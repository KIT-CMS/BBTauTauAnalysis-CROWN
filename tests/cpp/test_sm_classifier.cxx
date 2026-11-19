// Test of the NN classifier friend sm_nn_classifier (nn spec 3.3, 3.4) with
// the toy models of tests/fixtures/nn_classifier
// (make_nn_classifier_fixtures.py): every event is scored by the model of its
// residue event % n, on unsigned 64-bit event numbers beyond 2^24, 2^31, 2^32
// and 2^63 (the thesis friend converted to float and int); n = 2 and n = 4,
// probabilities, logits (softmax in C++) and a binary head; outside the gate
// every output is -1; dynamic dimensions, wrong shapes, inputs of another
// length and non-finite inputs throw; the gate flag substitutes its columns;
// the constants of a manifest (era_index and channel_index of a model of all
// eras and scopes) enter the input vector at their position, as the friend
// generates it (event::quantity::Define<float>, fakefactors::BuildFloatVector).
// Prints the latency per event of the batch-1 evaluation.
//
// Usage: test_sm_classifier <tests/fixtures/nn_classifier>

// the event.hxx of the CROWN core, not the one of the addons
#include "../../../../include/event.hxx"
#include "fakefactors.hxx"
#include "sm_classifier.hxx"

#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

std::string scientific(double value) {
    std::ostringstream stream;
    stream << std::scientific << std::setprecision(2) << value;
    return stream.str();
}

void check(bool ok, const std::string &name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << std::endl;
    if (!ok) {
        ++g_failures;
    }
}

using Rows = std::vector<std::vector<float>>;

Rows read_rows(const std::string &path) {
    Rows rows;
    std::ifstream file(path);
    if (!file) {
        throw std::runtime_error("cannot read " + path);
    }
    std::string line;
    while (std::getline(file, line)) {
        std::istringstream stream(line);
        std::vector<float> row;
        float value;
        while (stream >> value) {
            row.push_back(value);
        }
        if (!row.empty()) {
            rows.push_back(row);
        }
    }
    return rows;
}

struct Family {
    std::string name;
    int folds, num_inputs, num_classes, num_outputs;
    bool softmax;
    std::vector<std::string> files;
    Rows inputs;
    std::vector<Rows> outputs; // per residue, after the softmax of logits
};

Family load(const std::string &directory, const std::string &name, int folds,
            int num_classes, int num_outputs, bool softmax) {
    Family family{name,    folds, 0,  num_classes, num_outputs,
                  softmax, {},    {}, {}};
    const auto base = directory + "/" + name + "/";
    family.inputs = read_rows(base + "inputs.txt");
    family.num_inputs = family.inputs.at(0).size();
    for (int r = 0; r < folds; ++r) {
        family.files.push_back(base + "model_k" + std::to_string(folds) + "_r" +
                               std::to_string(r) + ".onnx");
        auto rows = read_rows(base + "outputs_r" + std::to_string(r) + ".txt");
        if (softmax) {
            for (auto &row : rows) {
                double largest = *std::max_element(row.begin(), row.end());
                double norm = 0;
                for (auto value : row) {
                    norm += std::exp(double(value) - largest);
                }
                for (auto &value : row) {
                    value = std::exp(double(value) - largest) / norm;
                }
            }
        }
        family.outputs.push_back(rows);
    }
    return family;
}

// event numbers at the edges where a conversion to float (2^24), int (2^31),
// 32 bits (2^32) or a signed 64-bit type (2^63) would change the residue, and
// enough of them to use every row and residue
std::vector<ULong64_t> event_numbers(size_t count) {
    std::vector<ULong64_t> events = {0,
                                     1,
                                     2,
                                     3,
                                     (1ULL << 24) + 1,
                                     (1ULL << 24) + 3,
                                     (1ULL << 31) + 1,
                                     (1ULL << 31) + 2,
                                     (1ULL << 31) + 3,
                                     (1ULL << 32) + 1,
                                     (1ULL << 32) + 2,
                                     5970000001ULL,
                                     (1ULL << 63) + 1,
                                     (1ULL << 63) + 2,
                                     std::numeric_limits<ULong64_t>::max(),
                                     std::numeric_limits<ULong64_t>::max() - 1};
    for (ULong64_t event = 4000000000ULL; events.size() < count; event += 7) {
        events.push_back(event);
    }
    return events;
}

const std::vector<std::string> kOutputs = {"predicted_class",
                                           "predicted_max_value"};

std::vector<std::string> output_columns(const Family &family) {
    auto columns = kOutputs;
    for (int i = 0; i < family.num_outputs; ++i) {
        columns.push_back("score_" + std::to_string(i));
    }
    return columns;
}

ROOT::RDF::RNode frame(const std::vector<ULong64_t> &events, const Rows &rows,
                       const std::function<bool(ULong64_t)> &gate) {
    return ROOT::RDataFrame(events.size())
        .Define("event", [events](ULong64_t entry) { return events[entry]; },
                {"rdfentry_"})
        .Define("inputs",
                [rows](ULong64_t entry) { return rows[entry % rows.size()]; },
                {"rdfentry_"})
        .Define("gate", gate, {"rdfentry_"});
}

void test_residues(OnnxSessionManager &manager, const Family &family) {
    const auto events = event_numbers(4 * family.inputs.size());
    auto gate = [](ULong64_t entry) { return entry % 5 != 4; };
    auto scored = xyh::classifier::EvaluateFolds(
        frame(events, family.inputs, gate), manager, "scores", "inputs",
        "event", "gate", family.files, family.num_inputs, family.num_classes,
        family.num_outputs, family.softmax);
    const auto columns = output_columns(family);
    auto unpacked = xyh::classifier::UnpackScores(scored, columns, "scores",
                                                  family.num_classes);
    auto scores = unpacked.Take<ROOT::RVec<float>>("scores");
    auto classes = unpacked.Take<int>("predicted_class");
    auto maxima = unpacked.Take<float>("predicted_max_value");
    std::vector<ROOT::RDF::RResultPtr<std::vector<float>>> flat;
    for (size_t i = 2; i < columns.size(); ++i) {
        flat.push_back(unpacked.Take<float>(columns[i]));
    }
    double closure = 0, separation = std::numeric_limits<double>::max();
    bool own_model = true, unpacking = true, outside = true;
    std::vector<int> used(family.folds, 0);
    for (size_t entry = 0; entry < events.size(); ++entry) {
        const auto &s = scores->at(entry);
        if (!gate(entry)) {
            outside = outside && s.empty() && classes->at(entry) == -1 &&
                      maxima->at(entry) == -1.f;
            for (auto &column : flat) {
                outside = outside && column->at(entry) == -1.f;
            }
            continue;
        }
        const auto row = entry % family.inputs.size();
        const int residue = events[entry] % ULong64_t(family.folds);
        ++used[residue];
        if (s.size() != size_t(family.num_outputs)) {
            own_model = false;
            continue;
        }
        for (int r = 0; r < family.folds; ++r) {
            double difference = 0;
            for (int i = 0; i < family.num_outputs; ++i) {
                difference = std::max(
                    difference,
                    std::abs(double(s[i]) - family.outputs[r].at(row).at(i)));
            }
            if (r == residue) {
                closure = std::max(closure, difference);
            } else {
                separation = std::min(separation, difference);
            }
        }
        const auto best =
            std::max_element(s.begin(), s.begin() + family.num_classes);
        unpacking = unpacking && classes->at(entry) == best - s.begin() &&
                    maxima->at(entry) == *best;
        for (int i = 0; i < family.num_outputs; ++i) {
            unpacking = unpacking && flat[i]->at(entry) == s[i];
        }
    }
    const auto label =
        family.name + " (n = " + std::to_string(family.folds) + "): ";
    check(own_model && closure <= 1e-6,
          label + "each event scored by the model of event % n, max |diff| " +
              scientific(closure));
    check(separation > 1e-4,
          label + "the models of the other residues differ by > " +
              scientific(separation));
    check(std::all_of(used.begin(), used.end(), [](int n) { return n > 0; }),
          label + "every residue is used");
    check(unpacking, label + "class, maximum and scores unpacked");
    check(outside, label + "outside the gate: no scores, -1 everywhere");
}

bool throws(const std::function<void()> &call) {
    try {
        call();
    } catch (const std::exception &error) {
        std::cout << "     (" << error.what() << ")" << std::endl;
        return true;
    }
    return false;
}

void test_errors(OnnxSessionManager &manager, const Family &family,
                 const Family &dynamic) {
    const auto events = event_numbers(8);
    auto all = [](ULong64_t) { return true; };
    auto evaluate = [&](const Family &f, const Rows &rows, int num_inputs,
                        int num_classes, int num_outputs,
                        std::vector<std::string> files) {
        auto df = xyh::classifier::EvaluateFolds(
            frame(events, rows, all), manager, "scores", "inputs", "event",
            "gate", files, num_inputs, num_classes, num_outputs, f.softmax);
        df.Take<ROOT::RVec<float>>("scores").GetValue(); // runs the scores
    };
    const auto n = family.num_inputs, c = family.num_classes;
    check(throws([&] {
              evaluate(dynamic, dynamic.inputs, dynamic.num_inputs,
                       dynamic.num_classes, dynamic.num_outputs, dynamic.files);
          }),
          "a dynamic dimension throws");
    check(throws([&] {
              evaluate(family, family.inputs, n - 1, c, c, family.files);
          }),
          "an input dimension other than the model's throws");
    check(throws([&] {
              evaluate(family, family.inputs, n, c - 1, c - 1, family.files);
          }),
          "an output dimension other than the model's throws");
    check(throws([&] {
              evaluate(family, family.inputs, n, c, c + 2, family.files);
          }),
          "more than C + 1 outputs throw");
    check(throws([&] {
              evaluate(family, family.inputs, n, c, c, {family.files[0]});
          }),
          "a single model throws");
    Rows shorter = family.inputs;
    for (auto &row : shorter) {
        row.pop_back();
    }
    check(throws([&] { evaluate(family, shorter, n, c, c, family.files); }),
          "an input vector of another length throws");
    Rows nan = family.inputs;
    nan[1][3] = std::numeric_limits<float>::quiet_NaN();
    check(throws([&] { evaluate(family, nan, n, c, c, family.files); }),
          "a NaN input throws");
}

void test_selection_flag() {
    const std::vector<float> pt = {20.f, 35.f, 50.f, 50.f};
    const std::vector<float> eta = {0.f, -1.f, 2.2f, -2.0f};
    auto df =
        ROOT::RDF::RNode(ROOT::RDataFrame(pt.size()))
            .Define("pt_1", [pt](ULong64_t e) { return pt[e]; }, {"rdfentry_"})
            .Define("eta_1__shift", [eta](ULong64_t e) { return eta[e]; },
                    {"rdfentry_"});
    auto flagged = xyh::classifier::SelectionFlag(
        df, "gate", "(($0 > 30) && (std::abs($1) < 2.1)) || ($0 > 1000)",
        {"pt_1", "eta_1__shift"});
    const auto values = flagged.Take<bool>("gate").GetValue();
    check(values == std::vector<bool>{false, true, false, true},
          "gate flag: $i reads columns[i], std::abs on signed eta");
    check(throws([&] {
              xyh::classifier::SelectionFlag(df, "g", "$2 > 0", {"pt_1"});
          }),
          "gate flag: a column index beyond the list throws");
    check(throws([&] {
              xyh::classifier::SelectionFlag(df, "g", "$ > 0", {"pt_1"});
          }),
          "gate flag: '$' without an index throws");
}

// The toy family k2_constants (families.json): the inputs in the order of the
// manifest, two of them constants whose values are in every row of inputs.txt.
const std::vector<std::string> kConstantInputs = {
    "pt_1", "era_index", "m_vis", "channel_index", "pt_2", "n_jets"};
const std::map<std::string, float> kConstants = {{"era_index", 3.f},
                                                 {"channel_index", 1.f}};

// Scores of `family` with the input vector built by the friend's producers:
// one float column per constant, the others read from columns, the vector in
// the order of `order` (the manifest's, or another one for the control).
std::vector<ROOT::RVec<float>> constant_scores(
    OnnxSessionManager &manager, const Family &family,
    const std::vector<ULong64_t> &events, const std::vector<std::string> &order,
    std::string *column_type = nullptr) {
    const auto rows = family.inputs;
    ROOT::RDF::RNode df = ROOT::RDataFrame(events.size())
                              .Define("event",
                                      [events](ULong64_t entry) {
                                          return events[entry];
                                      },
                                      {"rdfentry_"})
                              .Define("gate", [] { return true; });
    std::vector<std::string> columns;
    for (size_t i = 0; i < kConstantInputs.size(); ++i) {
        const auto &name = kConstantInputs[i];
        if (kConstants.count(name)) {
            df = event::quantity::Define<float>(df, "nn_constant_" + name,
                                               kConstants.at(name));
            continue;
        }
        df = df.Define(name,
                       [rows, i](ULong64_t entry) {
                           return rows[entry % rows.size()][i];
                       },
                       {"rdfentry_"});
    }
    for (const auto &name : order) {
        columns.push_back(kConstants.count(name) ? "nn_constant_" + name
                                                 : name);
    }
    if (column_type != nullptr) {
        *column_type = df.GetColumnType("nn_constant_era_index");
    }
    df = fakefactors::BuildFloatVector(df, "inputs", columns);
    auto scored = xyh::classifier::EvaluateFolds(
        df, manager, "scores", "inputs", "event", "gate", family.files,
        family.num_inputs, family.num_classes, family.num_outputs,
        family.softmax);
    return scored.Take<ROOT::RVec<float>>("scores").GetValue();
}

void test_constants(OnnxSessionManager &manager, const Family &family) {
    const auto events = event_numbers(2 * family.inputs.size());
    std::string column_type;
    const auto scores =
        constant_scores(manager, family, events, kConstantInputs, &column_type);
    // the control: the constants after the columns instead of at their position
    std::vector<std::string> appended;
    for (const auto &name : kConstantInputs) {
        if (!kConstants.count(name)) {
            appended.push_back(name);
        }
    }
    for (const auto &[name, value] : kConstants) {
        appended.push_back(name);
    }
    const auto misplaced = constant_scores(manager, family, events, appended);
    double closure = 0, separation = std::numeric_limits<double>::max();
    for (size_t entry = 0; entry < events.size(); ++entry) {
        const auto residue = events[entry] % family.folds;
        const auto &row =
            family.outputs[residue].at(entry % family.inputs.size());
        double difference = 0, moved = 0;
        for (int i = 0; i < family.num_outputs; ++i) {
            difference = std::max(difference,
                                  std::abs(double(scores[entry][i]) - row[i]));
            moved = std::max(moved, std::abs(double(misplaced[entry][i]) -
                                             scores[entry][i]));
        }
        closure = std::max(closure, difference);
        separation = std::min(separation, moved);
    }
    check(closure <= 1e-6,
          "constants: the input vector of columns and constants in the order "
          "of the manifest reproduces onnxruntime, max |diff| " +
              scientific(closure));
    check(separation > 1e-5, "constants: at other positions the scores "
                             "differ on every event, by > " +
                                 scientific(separation));
    check(column_type == "float",
          "constants: defined as float columns (" + column_type + ")");
}

void latency(OnnxSessionManager &manager, const Family &family) {
    const auto events = event_numbers(200000);
    auto scored = xyh::classifier::EvaluateFolds(
        frame(events, family.inputs, [](ULong64_t) { return true; }), manager,
        "scores", "inputs", "event", "gate", family.files, family.num_inputs,
        family.num_classes, family.num_outputs, family.softmax);
    auto sum = scored.Define("first", "scores[0]").Sum<float>("first");
    const auto start = std::chrono::steady_clock::now();
    sum.GetValue();
    const double us = std::chrono::duration<double, std::micro>(
                          std::chrono::steady_clock::now() - start)
                          .count() /
                      events.size();
    std::cout << "LATENCY " << family.name << " " << us
              << " us/event (RDataFrame, 1 thread, " << events.size()
              << " events, input vector and gate included)" << std::endl;
}

} // namespace

int main(int argc, char **argv) {
    if (argc != 2) {
        std::cerr << "usage: " << argv[0] << " <fixtures/nn_classifier>"
                  << std::endl;
        return 2;
    }
    const std::string directory = argv[1];
    OnnxSessionManager manager;
    const auto k2 = load(directory, "k2", 2, 5, 5, false);
    const auto k4 = load(directory, "k4", 4, 5, 6, false);
    const auto logits = load(directory, "k2_logits", 2, 3, 3, true);
    const auto dynamic = load(directory, "dynamic", 2, 2, 2, false);
    const auto constants = load(directory, "k2_constants", 2, 5, 5, false);
    test_residues(manager, k2);
    test_residues(manager, k4);
    test_residues(manager, logits);
    test_errors(manager, k2, dynamic);
    test_selection_flag();
    test_constants(manager, constants);
    latency(manager, k2);
    latency(manager, k4);
    std::cout << (g_failures == 0 ? "ALL PASSED" : "FAILURES: ") << " "
              << g_failures << std::endl;
    return g_failures == 0 ? 0 : 1;
}
