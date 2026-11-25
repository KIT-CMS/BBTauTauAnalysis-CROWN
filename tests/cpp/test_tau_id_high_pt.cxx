// Test of xyh::scalefactor::tau_id_vsjet_pt_binned, the columns of the
// pT-binned DeepTau vsJet scale factor (v8 spec C40, V35), on the pinned TAU
// payload of an era.
//
// Usage: <binary> <tau.json.gz> <correction> <vsJet WP> <vsEle WP>
//
// The checks, against direct evaluations of the correction:
//  - "nom" is the correction with flag "pt" at the tau, bit for bit, at every
//    pT: below 140 GeV the value of the lowest bin, constant in pT;
//  - "up"/"down" are nom +- the quadrature sum of the four components
//    stat_highpT_bin1, stat_highpT_bin2, syst_highpT, syst_highpT_extrap;
//  - without the extrapolation component that sum is the payload's own syst
//    "up"/"down" (to 1e-9), so the columns are never narrower than it, and
//    they are wider above 140 GeV, where the extrapolation term grows from
//    zero (by more than 1e-4 from 170 GeV on);
//  - every value is finite, positive and has down < nom < up for genuine
//    taus; for other generator matches all three are exactly 1, and for a leg
//    without a tau (decay mode -10, 2, 5) too;
//  - the nominal differs from the DM-binned scale factor (flag "dm");
//  - another member name, and a correction with other inputs, are refused.

#include "tau_id_high_pt.hxx"
#include "utility/CorrectionManager.hxx"

#include <ROOT/RDataFrame.hxx>
#include <cmath>
#include <correction.h>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
int failures = 0;

void check(bool condition, const std::string &what) {
    if (!condition) {
        std::printf("FAIL: %s\n", what.c_str());
        ++failures;
    }
}

bool same_bits(double a, double b) { return std::memcmp(&a, &b, sizeof(double)) == 0; }

struct Tau {
    float pt;
    int decay_mode, gen_match;
};
} // namespace

int main(int argc, char **argv) {
    if (argc != 5) {
        std::printf("usage: %s <tau.json.gz> <correction> <vsJet WP> <vsEle WP>\n", argv[0]);
        return 2;
    }
    const std::string payload = argv[1], name = argv[2], wp = argv[3], wp_vse = argv[4];
    std::vector<Tau> taus;
    for (int gen_match : {5, 0, 1, 2, 3, 4, 6}) {
        for (int decay_mode : {0, 1, 10, 11}) {
            for (float pt : {20.f, 25.f, 39.9f, 80.f, 139.9f, 140.f, 140.1f, 170.f, 199.9f, 200.f,
                             250.f, 300.f, 400.f, 700.f, 1500.f}) {
                taus.push_back({pt, decay_mode, gen_match});
            }
        }
    }
    const std::size_t n_valid = taus.size();
    // legs without a tau: the defaults of an event selected under a shift only,
    // and decay modes the scale factors do not cover
    for (int decay_mode : {-10, -1, 2, 5, 6}) {
        taus.push_back({-10.f, decay_mode, -10});
        taus.push_back({250.f, decay_mode, 5});
    }

    ROOT::RDataFrame base(taus.size());
    ROOT::RDF::RNode df =
        base.Define("pt", [taus](ULong64_t e) { return taus[e].pt; }, {"rdfentry_"})
            .Define("dm", [taus](ULong64_t e) { return taus[e].decay_mode; }, {"rdfentry_"})
            .Define("gm", [taus](ULong64_t e) { return taus[e].gen_match; }, {"rdfentry_"});
    correctionManager::CorrectionManager manager;
    const std::vector<std::string> members{"nom", "up", "down"};
    for (const auto &member : members) {
        df = xyh::scalefactor::tau_id_vsjet_pt_binned(df, manager, "sf_" + member, "pt", "dm",
                                                      "gm", payload, name, wp, wp_vse, member);
    }
    auto nom = df.Take<double>("sf_nom"), up = df.Take<double>("sf_up"),
         down = df.Take<double>("sf_down");

    auto correction = correction::CorrectionSet::from_file(payload)->at(name);
    auto direct = [&](const Tau &tau, const std::string &syst, const std::string &flag) {
        return correction->evaluate({tau.pt, tau.decay_mode, tau.gen_match, wp, wp_vse, syst, flag});
    };
    const auto &components = xyh::scalefactor::tau_id_vsjet_pt_binned_components();
    check(components.size() == 4, "four uncertainty components");

    bool nominal_ok = true, band_ok = true, payload_total_ok = true, finite = true,
         ordered = true, unity = true, constant_below = true;
    unsigned wider = 0, above = 0, differs_from_dm = 0, genuine = 0;
    double max_extra = 0., first_bin = -1.;
    for (std::size_t i = 0; i < n_valid; ++i) {
        const Tau &tau = taus[i];
        const double central = direct(tau, "nom", "pt");
        nominal_ok = nominal_ok && same_bits((*nom)[i], central);
        for (const std::string member : {"up", "down"}) {
            double all = 0., without_extrapolation = 0.;
            for (const auto &component : components) {
                const double difference = direct(tau, component + "_" + member, "pt") - central;
                all += difference * difference;
                if (component != "syst_highpT_extrap") {
                    without_extrapolation += difference * difference;
                }
            }
            const double sign = member == "up" ? 1. : -1.;
            const double value = member == "up" ? (*up)[i] : (*down)[i];
            band_ok = band_ok && same_bits(value, central + sign * std::sqrt(all));
            const double payload_total = direct(tau, member, "pt");
            payload_total_ok =
                payload_total_ok &&
                std::abs(central + sign * std::sqrt(without_extrapolation) - payload_total) < 1e-9;
            if (tau.gen_match == 5 && member == "up") {
                const double extra = value - payload_total;
                max_extra = std::max(max_extra, extra);
                // the term grows from 0 at 140 GeV: 3e-5 of the scale factor
                // per GeV, in quadrature with the 0.1 of the others
                if (tau.pt >= 170.f) {
                    ++above;
                    wider += extra > 1e-4;
                }
                band_ok = band_ok && extra > -1e-12;
            }
        }
        finite = finite && std::isfinite((*nom)[i]) && std::isfinite((*up)[i]) &&
                 std::isfinite((*down)[i]) && (*down)[i] > 0.;
        if (tau.gen_match == 5) {
            ++genuine;
            ordered = ordered && (*down)[i] < (*nom)[i] && (*nom)[i] < (*up)[i];
            differs_from_dm += central != direct(tau, "nom", "dm");
            if (tau.pt < 140.f) {
                if (first_bin < 0.) {
                    first_bin = central;
                }
                constant_below = constant_below && central == first_bin;
            }
        } else {
            unity = unity && (*nom)[i] == 1. && (*up)[i] == 1. && (*down)[i] == 1.;
        }
    }
    for (std::size_t i = n_valid; i < taus.size(); ++i) {
        unity = unity && (*nom)[i] == 1. && (*up)[i] == 1. && (*down)[i] == 1.;
    }
    std::printf("%u genuine taus: nominal below 140 GeV %.4f; %u of %u from 170 GeV on wider than the "
                "payload's total, by up to %.4f; %u differ from the DM-binned scale factor\n",
                genuine, first_bin, wider, above, max_extra, differs_from_dm);
    check(nominal_ok, "nom is the correction with flag pt, bit for bit");
    check(band_ok, "up and down are nom +- the quadrature sum of the four components");
    check(payload_total_ok,
          "the payload's up/down is the quadrature sum without the extrapolation component");
    check(finite, "every value is finite and positive");
    check(ordered, "down < nom < up for genuine taus at every pT");
    check(unity, "non-taus and legs without a tau have 1 in all three columns");
    check(constant_below, "below 140 GeV the nominal is the value of the lowest bin");
    check(above > 0 && wider == above,
          "from 170 GeV on the extrapolation component widens the band by more than 1e-4");
    check(differs_from_dm > genuine / 2, "the pT-binned set differs from the DM-binned one");

    bool refused = true;
    for (const std::string bad : {"nominal", "Up", "stat_highpT_bin1_up", ""}) {
        try {
            xyh::scalefactor::tau_id_vsjet_pt_binned(df, manager, "bad_" + bad, "pt", "dm", "gm",
                                                     payload, name, wp, wp_vse, bad);
            refused = false;
        } catch (const std::invalid_argument &) {
        }
    }
    check(refused, "other member names are refused");
    bool other_inputs_refused = false;
    try {
        // the energy scale correction takes other inputs
        xyh::scalefactor::tau_id_vsjet_pt_binned(df, manager, "other", "pt", "dm", "gm", payload,
                                                 "tau_energy_scale", wp, wp_vse, "nom");
    } catch (const std::invalid_argument &) {
        other_inputs_refused = true;
    }
    check(other_inputs_refused, "a correction with other inputs is refused");
    return failures == 0 ? 0 : 1;
}
