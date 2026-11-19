// Test of fakefactors::xyh::FakeFactor, the fake factor of a tau leg summed over
// the processes of its payload (v7 spec C15), on real and synthetic payloads.
//
// Usage: test_fake_factor_sum <plan file>
//
// The plan (written by tests/test_cpp_runtime.py from ff_payloads.read_legs)
// lists the legs: files, fractions, the fake factor of each process, the
// corrections, candidate values of every input and the syst keys the friend
// shifts. For every leg, random events draw each input from its candidates, and
// the raw and the corrected fake factor are evaluated nominal and with every
// syst key, each key on its own as in the friend:
//   - legs marked "reference" (QCD + ttbar) must give the frozen two-process
//     functions (reference/fakefactors_two_process.hxx, the friend before C15)
//     bit for bit;
//   - every leg must give sum_p f_p * max(FF_p * prod C, 0), evaluated here in
//     double precision, within 1e-5, and every process must contribute;
//   - every leg must give that sum in the float arithmetic of the friend (every
//     value rounded to float, the corrections applied in their order, the
//     terms summed in payload order) bit for bit, which fixes the values of the
//     QCD + W + ttbar legs as the reference fixes those of the two-process ones.
//
// Build it with -ffp-contract=off: the friend is built with ROOT's
// -march=nocona, which has no fused multiply-add, and a reference fused by the
// compiler differs from the friend in the last bit.

#include "fakefactors.hxx"
#include "reference/fakefactors_two_process.hxx"

#include "utility/CorrectionManager.hxx"

#include <ROOT/RDataFrame.hxx>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr ULong64_t kEvents = 2000;

struct Leg {
    std::string label;
    bool reference = false;
    std::string ff_file, corr_file, fraction;
    std::vector<std::string> processes, ff_names;
    std::vector<std::string> corr_processes, corr_names;
    std::vector<int> corr_compound;
    // slot (0 fractions, 1..P fake factors, then corrections) -> input -> values
    std::vector<std::vector<std::vector<float>>> candidates;
    std::vector<std::pair<std::size_t, std::string>> variations;

    std::size_t n_slots() const {
        return 1 + processes.size() + corr_names.size();
    }
};

std::vector<Leg> read_plan(const std::string &path) {
    std::ifstream file(path);
    if (!file) {
        throw std::runtime_error("cannot read the plan " + path);
    }
    std::vector<Leg> legs;
    std::string line;
    while (std::getline(file, line)) {
        std::istringstream in(line);
        std::string tag;
        in >> tag;
        if (tag.empty()) {
            continue;
        }
        if (tag == "leg") {
            legs.emplace_back();
            int reference;
            in >> legs.back().label >> reference;
            legs.back().reference = reference;
            continue;
        }
        Leg &leg = legs.back();
        if (tag == "ff_file") {
            in >> leg.ff_file;
        } else if (tag == "corr_file") {
            in >> leg.corr_file;
        } else if (tag == "fraction") {
            in >> leg.fraction;
        } else if (tag == "process") {
            std::string process, name;
            in >> process >> name;
            leg.processes.push_back(process);
            leg.ff_names.push_back(name);
        } else if (tag == "correction") {
            std::string process, name;
            int compound;
            in >> process >> name >> compound;
            leg.corr_processes.push_back(process);
            leg.corr_names.push_back(name);
            leg.corr_compound.push_back(compound);
        } else if (tag == "values") {
            std::size_t slot, n;
            in >> slot >> n;
            std::vector<float> values(n);
            for (auto &value : values) {
                in >> value;
            }
            if (leg.candidates.size() <= slot) {
                leg.candidates.resize(slot + 1);
            }
            leg.candidates[slot].push_back(values);
        } else if (tag == "variation") {
            std::size_t slot;
            std::string key;
            in >> slot >> key;
            leg.variations.emplace_back(slot, key);
        } else {
            throw std::runtime_error("unknown plan line: " + line);
        }
    }
    return legs;
}

std::string column(std::size_t slot) { return "in_" + std::to_string(slot); }

bool same_bits(float a, float b) {
    std::uint32_t x, y;
    std::memcpy(&x, &a, sizeof x);
    std::memcpy(&y, &b, sizeof y);
    return x == y;
}

using Inputs = std::vector<correction::Variable::Type>;

Inputs with_syst(const std::vector<float> &values, const std::string &syst) {
    Inputs result(values.begin(), values.end());
    result.push_back(syst);
    return result;
}

// The expected fake factor in precision T: double for the formula, float for
// the arithmetic of the friend (every value rounded to float, the corrections
// applied in their order, the terms summed in payload order); `terms` gets the
// term of each process
template <typename T>
T expected(correctionManager::CorrectionManager &mgr, const Leg &leg,
           const std::vector<std::vector<float>> &inputs,
           const std::vector<std::string> &syst, bool corrected,
           std::vector<T> &terms) {
    const std::size_t n_p = leg.processes.size();
    auto fractions = mgr.loadCorrection(leg.ff_file, leg.fraction);
    std::vector<T> products(n_p);
    for (std::size_t p = 0; p < n_p; ++p) {
        products[p] = mgr.loadCorrection(leg.ff_file, leg.ff_names[p])
                          ->evaluate(with_syst(inputs[1 + p], syst[1 + p]));
    }
    for (std::size_t c = 0; corrected && c < leg.corr_names.size(); ++c) {
        const auto values = with_syst(inputs[1 + n_p + c], syst[1 + n_p + c]);
        const T correction =
            leg.corr_compound[c]
                ? mgr.loadCompoundCorrection(leg.corr_file, leg.corr_names[c])
                      ->evaluate(values)
                : mgr.loadCorrection(leg.corr_file, leg.corr_names[c])
                      ->evaluate(values);
        for (std::size_t p = 0; p < n_p; ++p) {
            if (leg.processes[p] == leg.corr_processes[c]) {
                products[p] *= correction;
            }
        }
    }
    T sum = 0;
    terms.assign(n_p, T(0));
    for (std::size_t p = 0; p < n_p; ++p) {
        Inputs values = with_syst(inputs[0], syst[0]);
        values.insert(values.begin(), leg.processes[p]);
        const T fraction = fractions->evaluate(values);
        terms[p] = fraction * std::max(products[p], T(0));
        sum = p == 0 ? terms[p] : sum + terms[p];
    }
    return sum;
}

int test_leg(correctionManager::CorrectionManager &mgr, const Leg &leg) {
    const std::size_t n_p = leg.processes.size();
    const std::size_t n_c = leg.corr_names.size();
    if (leg.candidates.size() != leg.n_slots()) {
        std::cerr << leg.label << ": values for " << leg.candidates.size()
                  << " of " << leg.n_slots() << " slots" << std::endl;
        return 1;
    }

    // random events: every input drawn from its candidates
    ROOT::RDataFrame df(kEvents);
    ROOT::RDF::RNode node = df;
    for (std::size_t slot = 0; slot < leg.n_slots(); ++slot) {
        const auto candidates = leg.candidates[slot];
        node = node.Define(
            column(slot),
            [candidates, slot](ULong64_t entry) {
                std::mt19937_64 rng(entry * 1000003ULL + slot * 7919ULL + 17ULL);
                std::vector<float> values;
                for (const auto &options : candidates) {
                    std::uniform_int_distribution<std::size_t> pick(
                        0, options.size() - 1);
                    values.push_back(options[pick(rng)]);
                }
                return values;
            },
            {"rdfentry_"});
    }
    std::vector<std::string> all_inputs, raw_inputs;
    for (std::size_t slot = 0; slot < leg.n_slots(); ++slot) {
        all_inputs.push_back(column(slot));
        if (slot <= n_p) {
            raw_inputs.push_back(column(slot));
        }
    }
    std::vector<ROOT::RDF::RResultPtr<std::vector<std::vector<float>>>> inputs;
    for (std::size_t slot = 0; slot < leg.n_slots(); ++slot) {
        inputs.push_back(node.Take<std::vector<float>>(column(slot)));
    }

    // nominal, then every syst key on its own
    std::vector<std::vector<std::string>> configurations(
        1, std::vector<std::string>(leg.n_slots(), "nominal"));
    for (const auto &[slot, key] : leg.variations) {
        configurations.push_back(
            std::vector<std::string>(leg.n_slots(), "nominal"));
        configurations.back().at(slot) = key;
    }

    using Values = ROOT::RDF::RResultPtr<std::vector<float>>;
    std::vector<Values> new_raw, new_corrected, ref_raw, ref_corrected;
    for (std::size_t k = 0; k < configurations.size(); ++k) {
        const auto &syst = configurations[k];
        const std::vector<std::string> ff_syst(syst.begin() + 1,
                                               syst.begin() + 1 + n_p);
        const std::vector<std::string> corr_syst(syst.begin() + 1 + n_p,
                                                 syst.end());
        const std::string suffix = "_" + std::to_string(k);
        node = fakefactors::xyh::FakeFactor(
            node, mgr, "new_raw" + suffix, raw_inputs, leg.processes,
            leg.ff_file, leg.ff_names, leg.fraction, "", {}, {}, {}, ff_syst,
            syst[0], {});
        node = fakefactors::xyh::FakeFactor(
            node, mgr, "new_corrected" + suffix, all_inputs, leg.processes,
            leg.ff_file, leg.ff_names, leg.fraction, leg.corr_file,
            leg.corr_names, leg.corr_processes, leg.corr_compound, ff_syst,
            syst[0], corr_syst);
        new_raw.push_back(node.Take<float>("new_raw" + suffix));
        new_corrected.push_back(node.Take<float>("new_corrected" + suffix));
        if (leg.reference) {
            node = fakefactors_reference::xyh::RawFakeFactorSemileptonic(
                node, mgr, "ref_raw" + suffix, column(1), column(2), column(0),
                leg.ff_file, leg.ff_names[0], leg.ff_names[1], leg.fraction,
                syst[1], syst[2], syst[0]);
            node = fakefactors_reference::xyh::FakeFactorSemileptonic(
                node, mgr, "ref_corrected" + suffix, column(1), column(2),
                column(0), column(3), column(4), column(5), leg.ff_file,
                leg.ff_names[0], leg.ff_names[1], leg.fraction, leg.corr_file,
                leg.corr_names[0], leg.corr_names[1], leg.corr_names[2],
                syst[1], syst[2], syst[0], syst[3], syst[4], syst[5]);
            ref_raw.push_back(node.Take<float>("ref_raw" + suffix));
            ref_corrected.push_back(node.Take<float>("ref_corrected" + suffix));
        }
    }

    // the reference legs have the layout of the two-process functions
    if (leg.reference &&
        (leg.processes != std::vector<std::string>{"QCD", "ttbar"} ||
         leg.corr_processes != std::vector<std::string>{"QCD", "QCD", "ttbar"} ||
         leg.corr_compound != std::vector<int>{0, 1, 1})) {
        std::cerr << leg.label << ": not the two-process layout" << std::endl;
        return 1;
    }

    std::size_t bit_mismatches = 0, float_mismatches = 0, value_mismatches = 0,
                nonzero = 0, compared = 0;
    std::vector<std::size_t> contributions(n_p, 0);
    for (std::size_t k = 0; k < configurations.size(); ++k) {
        for (ULong64_t e = 0; e < kEvents; ++e) {
            const float raw = new_raw[k]->at(e);
            const float corrected = new_corrected[k]->at(e);
            if (leg.reference) {
                bit_mismatches += !same_bits(raw, ref_raw[k]->at(e));
                bit_mismatches += !same_bits(corrected, ref_corrected[k]->at(e));
                compared += 2;
            }
            std::vector<std::vector<float>> values;
            for (auto &input : inputs) {
                values.push_back(input->at(e));
            }
            std::vector<double> raw_terms, corrected_terms;
            const double expected_raw =
                expected(mgr, leg, values, configurations[k], false, raw_terms);
            const double expected_corrected = expected(
                mgr, leg, values, configurations[k], true, corrected_terms);
            std::vector<float> float_terms;
            float_mismatches += !same_bits(
                raw, expected(mgr, leg, values, configurations[k], false,
                              float_terms));
            float_mismatches += !same_bits(
                corrected, expected(mgr, leg, values, configurations[k], true,
                                    float_terms));
            for (const auto &[got, want] :
                 {std::pair<double, double>{raw, expected_raw},
                  std::pair<double, double>{corrected, expected_corrected}}) {
                if (std::abs(got - want) >
                    1e-5 * std::max(1.0, std::abs(want))) {
                    if (value_mismatches < 5) {
                        std::cerr << leg.label << " configuration " << k
                                  << " event " << e << ": " << got << " != "
                                  << want << std::endl;
                    }
                    ++value_mismatches;
                }
            }
            nonzero += corrected != 0.f;
            for (std::size_t p = 0; p < n_p; ++p) {
                contributions[p] += corrected_terms[p] > 0.0;
            }
        }
    }

    bool every_process = true;
    std::string terms;
    for (std::size_t p = 0; p < n_p; ++p) {
        every_process = every_process && contributions[p] > 0;
        terms += " " + leg.processes[p] + " " + std::to_string(contributions[p]);
    }
    const bool ok = bit_mismatches == 0 && float_mismatches == 0 &&
                    value_mismatches == 0 && nonzero > 0 && every_process;
    std::cout << (ok ? "PASS " : "FAIL ") << leg.label << ": "
              << configurations.size() << " configurations x " << kEvents
              << " events, processes " << n_p << ", corrections " << n_c
              << ", " << compared << " values against the reference ("
              << bit_mismatches << " differ in a bit), " << float_mismatches
              << " differ in a bit from the float sum, " << value_mismatches
              << " off the formula, " << nonzero << " non-zero; terms > 0:"
              << terms << std::endl;
    return ok ? 0 : 1;
}

} // namespace

int main(int argc, char **argv) {
    if (argc != 2) {
        std::cerr << "usage: " << argv[0] << " <plan file>" << std::endl;
        return 2;
    }
    correctionManager::CorrectionManager mgr;
    int failures = 0;
    const auto legs = read_plan(argv[1]);
    for (const auto &leg : legs) {
        failures += test_leg(mgr, leg);
    }
    if (legs.empty()) {
        std::cerr << "no legs in the plan" << std::endl;
        return 1;
    }
    return failures == 0 ? 0 : 1;
}
