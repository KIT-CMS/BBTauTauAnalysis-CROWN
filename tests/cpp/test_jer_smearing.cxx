#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "correction.h"
#include "jets.hxx"
#include "utility/CorrectionManager.hxx"
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

// Usage: <binary> <jet_jerc payload of 2018-UL-NanoAODv15> <reapply_jes: 0|1>
//
// Drives physicsobject::jet::jec::PtCorrectionMC through RDataFrame with the
// official JER payload, in the production mode (reapply_jes = 1) or on
// already JES-corrected input (0). Jet 0 sits at |eta - phi| = 2.3, so that a
// swapped eta/phi in the distance cannot match it by chance. Its gen jets are,
// in this order: one at dR = 0.1 that passes the 3 sigma pt window, one at
// dR = 0.001 that fails it, one at dR = 0.014 and one at dR = 0.05 that pass,
// so that taking the first or the last passing gen jet, or the closest one
// before the pt window, all give a different pt. Jets 1 and 2 have no gen
// jet. The hybrid method must
//  - scale jet 0 deterministically with the closest passing gen jet,
//    pt' = pt + (sf - 1) * (pt - pt_gen), with pt the JER input pt;
//  - smear jets 1 and 2 with independent standard-normal numbers z;
//  - give jets 1 and 2 the same z whether or not jet 0 is matched, and in the
//    nominal and the JER-up variation.
// Here z = (pt' / pt - 1) / (sigma * sqrt(sf^2 - 1)). The HEM variation must
// scale jets that pass the tight jet ID (ID 2 or 6) in the HEM region.
namespace {
int failures = 0;

void check(bool condition, const char *what) {
    if (!condition) {
        std::printf("FAIL: %s\n", what);
        ++failures;
    }
}
} // namespace

int main(int argc, char **argv) {
    if (argc != 3) {
        std::printf("usage: %s <payload> <reapply_jes: 0|1>\n", argv[0]);
        return 2;
    }
    const std::string payload = argv[1];
    const bool reapply_jes = std::string(argv[2]) == "1";
    const std::string jer_tag = "Summer19UL18_JRV3";
    const std::string jes_tag = "Summer20UL18NanoV15_V1";
    const std::string algo = "AK4PFPuppi";
    const unsigned n = 20000;
    const float rho = 20.f;
    const ROOT::RVec<float> pt{60.f, 80.f, 50.f}, eta{0.3f, 0.5f, -1.2f},
        phi{-2.0f, 0.0f, 2.5f};
    const float matched_gen_pt = 55.f;

    ROOT::RDataFrame base(n);
    ROOT::RDF::RNode df =
        base.Define("pt", [pt] { return pt; })
            .Define("eta", [eta] { return eta; })
            .Define("phi", [phi] { return phi; })
            .Define("area", [] { return ROOT::RVec<float>(3, 0.5f); })
            // NanoAOD v9 type, cast to UChar_t by PtCorrectionMC
            .Define("id", [] { return ROOT::RVec<int>(3, 6); })
            .Define(
                "gen_pt",
                [matched_gen_pt] {
                    return ROOT::RVec<float>{59.f, 15.f, matched_gen_pt, 57.f};
                })
            .Define("gen_eta",
                    [] {
                        return ROOT::RVec<float>{0.4f, 0.3f, 0.31f, 0.35f};
                    })
            .Define("gen_phi",
                    [] {
                        return ROOT::RVec<float>{-2.0f, -2.001f, -1.99f, -2.0f};
                    })
            .Define("no_gen", [] { return ROOT::RVec<float>{}; })
            .Define("rho", [rho] { return rho; })
            .Define("seed",
                    [](ULong64_t entry) {
                        return static_cast<unsigned int>(1234567u +
                                                         2654435761u * entry);
                    },
                    {"rdfentry_"});

    correctionManager::CorrectionManager manager;
    auto correct = [&](ROOT::RDF::RNode node, const std::string &name,
                       bool with_gen, const std::string &jer_shift) {
        const std::string gen = with_gen ? "gen_" : "no_gen";
        return physicsobject::jet::jec::PtCorrectionMC(
            node, manager, name + "_jec", name + "_l1", name + "_l2rel",
            name + "_l2l3res", name, "pt", "eta", "phi", "area", "id",
            with_gen ? "gen_pt" : "no_gen", with_gen ? "gen_eta" : "no_gen",
            with_gen ? "gen_phi" : "no_gen", "rho", "seed", payload, algo,
            jes_tag, jer_tag, {""}, 0, jer_shift, reapply_jes, "2018");
    };
    df = correct(df, "nominal", true, "nom");
    df = correct(df, "unmatched", false, "nom");
    df = correct(df, "jer_up", true, "up");

    // Without JES shifts the JER input is the L2Relative-level pt, which is
    // the input pt itself if the JES is not reapplied
    auto input = df.Take<ROOT::RVec<float>>("nominal_l2rel");
    auto nominal = df.Take<ROOT::RVec<float>>("nominal");
    auto unmatched = df.Take<ROOT::RVec<float>>("unmatched");
    auto jer_up = df.Take<ROOT::RVec<float>>("jer_up");

    const ROOT::RVec<float> jer_pt = input->at(0);
    auto cset = correction::CorrectionSet::from_file(payload);
    auto resolution = cset->at(jer_tag + "_MC_PtResolution_" + algo);
    auto scalefactor = cset->at(jer_tag + "_MC_ScaleFactor_" + algo);
    auto uncertainty = cset->at(jer_tag + "_MC_SFUncertainty_" + algo);
    double sigma[3], sf[3], sf_up[3];
    for (int i = 0; i < 3; ++i) {
        sigma[i] = resolution->evaluate({eta[i], jer_pt[i], rho});
        sf[i] = scalefactor->evaluate({eta[i], jer_pt[i]});
        sf_up[i] = sf[i] * (1. + uncertainty->evaluate({eta[i], jer_pt[i]}));
    }

    const double hybrid =
        jer_pt[0] + (sf[0] - 1.) * (jer_pt[0] - matched_gen_pt);
    auto z = [&](float corrected, int i, const double *factors) {
        return (corrected / jer_pt[i] - 1.) /
               (sigma[i] * std::sqrt(factors[i] * factors[i] - 1.));
    };
    double max_input = 0., max_hybrid = 0., max_order = 0., max_variation = 0.;
    double s1 = 0., s2 = 0., s11 = 0., s22 = 0., s12 = 0.;
    for (unsigned e = 0; e < n; ++e) {
        const auto &p = (*nominal)[e];
        for (int i = 0; i < 3; ++i) {
            max_input = std::max(max_input,
                                 double(std::abs((*input)[e][i] - jer_pt[i])));
        }
        max_hybrid = std::max(max_hybrid, std::abs(p[0] - hybrid));
        const double z1 = z(p[1], 1, sf), z2 = z(p[2], 2, sf);
        for (int i = 1; i < 3; ++i) {
            max_order = std::max(max_order,
                                 double(std::abs(p[i] - (*unmatched)[e][i])));
            max_variation =
                std::max(max_variation, std::abs(z((*jer_up)[e][i], i, sf_up) -
                                                 z(p[i], i, sf)));
        }
        s1 += z1;
        s2 += z2;
        s11 += z1 * z1;
        s22 += z2 * z2;
        s12 += z1 * z2;
    }
    const double m1 = s1 / n, m2 = s2 / n;
    const double sd1 = std::sqrt(s11 / n - m1 * m1);
    const double sd2 = std::sqrt(s22 / n - m2 * m2);
    const double corr = (s12 / n - m1 * m2) / (sd1 * sd2);
    std::printf("reapply_jes=%d, JER input pt (%.3f, %.3f, %.3f)\n",
                reapply_jes, jer_pt[0], jer_pt[1], jer_pt[2]);
    std::printf("matched jet: max |pt' - %.4f| = %.2e GeV\n", hybrid,
                max_hybrid);
    std::printf("unmatched jets: mean %.4f %.4f, std %.4f %.4f, corr %.4f\n",
                m1, m2, sd1, sd2, corr);
    std::printf("max |dpt| with/without gen match of jet 0: %.2e GeV, "
                "max |dz| nominal vs JER up: %.2e\n",
                max_order, max_variation);

    // HEM variation: only the down shift scales, by 0.8 for -2.5 < eta < -1.3
    // and by 0.65 for -3.0 < eta <= -2.5, within -1.57 < phi < -0.87
    using physicsobject::jet::jec::apply_jes_shifts;
    const std::vector<std::string> hem{"HEMIssue"};
    const std::vector<correction::Correction *> none;
    const bool hem_ok =
        std::abs(apply_jes_shifts(50.f, -2.0f, -1.2f, 6, hem, -1, none) -
                 40.f) < 1e-4 &&
        std::abs(apply_jes_shifts(50.f, -2.7f, -1.2f, 6, hem, -1, none) -
                 32.5f) < 1e-4 &&
        std::abs(apply_jes_shifts(50.f, -2.0f, -1.2f, 2, hem, -1, none) -
                 40.f) < 1e-4 &&
        apply_jes_shifts(50.f, -2.0f, -1.2f, 0, hem, -1, none) == 50.f &&
        apply_jes_shifts(50.f, -2.0f, 0.5f, 6, hem, -1, none) == 50.f &&
        apply_jes_shifts(50.f, -2.0f, -1.2f, 6, hem, 1, none) == 50.f;

    // 20000 events: the statistical uncertainty is 0.007 on the mean and on
    // corr and 0.005 on the standard deviation, all tolerances exceed 4 sigma
    check(max_input == 0., "the JER input pt is the same in every event");
    check(max_hybrid < 1e-3,
          "matched jet is scaled with the closest passing gen jet");
    check(std::abs(m1) < 0.03 && std::abs(m2) < 0.03, "z has mean 0");
    check(std::abs(sd1 - 1.) < 0.03 && std::abs(sd2 - 1.) < 0.03,
          "z has standard deviation 1");
    check(std::abs(corr) < 0.03, "unmatched jets draw independent numbers");
    check(max_order == 0., "draws do not depend on the matching of other jets");
    check(max_variation < 1e-4, "JER up reuses the nominal numbers");
    check(hem_ok, "HEM down shift scales tight-ID jets in the HEM region");
    return failures == 0 ? 0 : 1;
}
