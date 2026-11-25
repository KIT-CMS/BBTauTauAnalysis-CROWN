#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "correction.h"
#include "jets.hxx"
#include "utility/CorrectionManager.hxx"
#include <cmath>
#include <limits>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <vector>

// Usage: <binary> <jet_jerc payload of the era's UL-NanoAODv15> <reapply_jes: 0|1>
//                 <JER tag> <JES tag> <era> <six JER region selections>
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
//
// The JER variations restricted to a region (v8 spec C33) are driven with the
// six selections of the configuration (variations.jec.JER_REGIONS, in the
// order of the JERC table) on a second set of jets that populates every
// region, matched and unmatched. A regional variation must give the jets of
// its region the pt of the inclusive variation and every other jet the nominal
// pt, both bit for bit: the region is decided by the nominal smeared pt (as in
// the split JER of nanoAOD-tools), and the random numbers are those of the
// nominal.
namespace {
int failures = 0;

void check(bool condition, const char *what) {
    if (!condition) {
        std::printf("FAIL: %s\n", what);
        ++failures;
    }
}

// The JERC regions of the resolution uncertainty, in the order of the table
int jerc_region(float eta, float pt) {
    const float abs_eta = std::abs(eta);
    if (abs_eta < 1.93f) {
        return 0;
    }
    if (abs_eta < 2.5f) {
        return 1;
    }
    if (abs_eta < 3.0f) {
        return pt < 50.f ? 2 : 3;
    }
    return pt < 50.f ? 4 : 5;
}

bool throws(const std::string &jer_shift) {
    try {
        physicsobject::jet::jec::parse_jer_variation(jer_shift);
    } catch (const std::invalid_argument &) {
        return true;
    }
    return false;
}
} // namespace

int main(int argc, char **argv) {
    if (argc != 12) {
        std::printf("usage: %s <payload> <reapply_jes: 0|1> <JER tag> <JES tag> "
                    "<era> <six JER region selections>\n",
                    argv[0]);
        return 2;
    }
    const std::vector<std::string> regions(argv + 6, argv + 12);
    const std::string payload = argv[1];
    const bool reapply_jes = std::string(argv[2]) == "1";
    const std::string jer_tag = argv[3];
    const std::string jes_tag = argv[4];
    const std::string era = argv[5];
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
            jes_tag, jer_tag, "nominal", 0, jer_shift, reapply_jes, era);
    };
    df = correct(df, "nominal", true, "nom");
    df = correct(df, "unmatched", false, "nom");
    df = correct(df, "jer_up", true, "up");
    // the JES-only pt that carries the jet energy scale to the MET of the
    // recoil-corrected samples
    df = physicsobject::jet::jec::ScaledPt(df, "nominal_scaled", "nominal_jec");
    df = physicsobject::jet::jec::ScaledPt(df, "jer_up_scaled", "jer_up_jec");

    // Without JES shifts the JER input is the L2Relative-level pt, which is
    // the input pt itself if the JES is not reapplied
    auto input = df.Take<ROOT::RVec<float>>("nominal_l2rel");
    auto nominal = df.Take<ROOT::RVec<float>>("nominal");
    auto unmatched = df.Take<ROOT::RVec<float>>("unmatched");
    auto jer_up = df.Take<ROOT::RVec<float>>("jer_up");
    auto scaled = df.Take<ROOT::RVec<float>>("nominal_scaled");
    auto scaled_up = df.Take<ROOT::RVec<float>>("jer_up_scaled");

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
    double max_scaled = 0., max_scaled_up = 0.;
    unsigned smeared_differs = 0;
    for (unsigned e = 0; e < n; ++e) {
        const auto &p = (*nominal)[e];
        for (int i = 0; i < 3; ++i) {
            max_scaled = std::max(
                max_scaled, double(std::abs((*scaled)[e][i] - (*input)[e][i])));
            max_scaled_up =
                std::max(max_scaled_up,
                         double(std::abs((*scaled_up)[e][i] - (*scaled)[e][i])));
        }
        smeared_differs += (*scaled)[e][1] != p[1];
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
    const std::string hem{"HEMIssue"};
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

    // --- JER variations restricted to a region ---------------------------------
    using physicsobject::jet::jec::parse_jer_variation;
    const float inf = std::numeric_limits<float>::infinity();
    const auto all_jets = parse_jer_variation("up");
    const auto endcap_low = parse_jer_variation("down_abseta2p5to3_pt0to50");
    const auto forward_high = parse_jer_variation("up_abseta3toInf_pt50toInf");
    check(parse_jer_variation("nom").direction == "nom" &&
              !parse_jer_variation("nom").regional &&
              all_jets.direction == "up" && !all_jets.regional &&
              all_jets.varies(4.9f, 1e4f) && all_jets.varies(0.f, 0.f),
          "a variation without region varies every jet");
    check(endcap_low.direction == "down" && endcap_low.regional &&
              endcap_low.min_abs_eta == 2.5f && endcap_low.max_abs_eta == 3.f &&
              endcap_low.min_pt == 0.f && endcap_low.max_pt == 50.f,
          "the region of a variation is parsed");
    check(forward_high.regional && forward_high.min_abs_eta == 3.f &&
              forward_high.max_abs_eta == inf && forward_high.min_pt == 50.f &&
              forward_high.max_pt == inf,
          "Inf opens a region upwards");
    check(endcap_low.varies(-2.7f, 49.99f) && endcap_low.varies(2.5f, 20.f) &&
              !endcap_low.varies(2.7f, 50.f) && !endcap_low.varies(3.0f, 20.f) &&
              !endcap_low.varies(2.49f, 20.f),
          "a region includes its lower edges and excludes its upper edges");
    check(throws("up_abseta") && throws("up_abseta3to2") &&
              throws("up_abseta0to1_pt50to50") && throws("left_abseta0to1") &&
              throws("up_abseta0to1_pt") && throws("up_abseta0.5to1"),
          "malformed regions are refused");

    // jets in every region, also where the re-applied JES raises the pt (jets 3
    // and 5 stay below 50 GeV); jets 0, 2, 4 and 6 have a gen jet nearby. Jets
    // 7 to 14 lie beyond |eta| 2.5 with a pt of 30 to 51 GeV, so that with and
    // without the re-applied JES some of them are smeared across 50 GeV
    const ROOT::RVec<float> r_pt{60.f, 40.f, 60.f, 20.f, 90.f, 25.f, 90.f, 49.f,
                                 51.f, 30.f, 36.f, 42.f, 30.f, 36.f, 42.f},
        r_eta{0.3f, -1.2f, 2.2f,   -2.7f, 2.8f,  3.5f,  -4.0f, 2.7f,
              -3.2f, 2.7f, 2.75f, 2.65f, -3.2f, -3.3f, -3.1f},
        r_phi{-2.0f, 0.0f, 2.5f,  1.0f, -1.0f, 0.5f, -0.5f, 2.0f,
              -2.6f, 3.0f, -3.0f, 1.5f, -1.5f, 2.9f, 0.2f};
    ROOT::RDataFrame region_base(n);
    ROOT::RDF::RNode rdf =
        region_base.Define("pt", [r_pt] { return r_pt; })
            .Define("eta", [r_eta] { return r_eta; })
            .Define("phi", [r_phi] { return r_phi; })
            .Define("area",
                    [r_pt] { return ROOT::RVec<float>(r_pt.size(), 0.5f); })
            .Define("id", [r_pt] { return ROOT::RVec<int>(r_pt.size(), 6); })
            .Define("gen_pt",
                    [r_pt] {
                        return ROOT::RVec<float>{0.95f * r_pt[0], 0.95f * r_pt[2],
                                                 0.95f * r_pt[4],
                                                 0.95f * r_pt[6]};
                    })
            .Define("gen_eta",
                    [r_eta] {
                        return ROOT::RVec<float>{r_eta[0], r_eta[2], r_eta[4],
                                                 r_eta[6]};
                    })
            .Define("gen_phi",
                    [r_phi] {
                        return ROOT::RVec<float>{r_phi[0], r_phi[2], r_phi[4],
                                                 r_phi[6]};
                    })
            .Define("no_gen", [] { return ROOT::RVec<float>{}; })
            .Define("rho", [rho] { return rho; })
            .Define("seed",
                    [](ULong64_t entry) {
                        return static_cast<unsigned int>(7654321u +
                                                         2654435761u * entry);
                    },
                    {"rdfentry_"});
    rdf = correct(rdf, "nominal", true, "nom");
    const std::vector<std::string> directions{"up", "down"};
    for (const auto &direction : directions) {
        rdf = correct(rdf, direction, true, direction);
        for (std::size_t r = 0; r < regions.size(); ++r) {
            rdf = correct(rdf, direction + std::to_string(r), true,
                          direction + "_" + regions[r]);
        }
    }
    auto r_input = rdf.Take<ROOT::RVec<float>>("nominal_l2rel");
    auto r_nominal = rdf.Take<ROOT::RVec<float>>("nominal");
    std::vector<ROOT::RDF::RResultPtr<std::vector<ROOT::RVec<float>>>>
        r_inclusive, r_regional;
    for (const auto &direction : directions) {
        r_inclusive.push_back(rdf.Take<ROOT::RVec<float>>(direction));
        for (std::size_t r = 0; r < regions.size(); ++r) {
            r_regional.push_back(
                rdf.Take<ROOT::RVec<float>>(direction + std::to_string(r)));
        }
    }
    // the region of each jet from its nominal smeared pt, event by event:
    // jets 7 and 8 start next to 50 GeV and are smeared across it
    std::vector<unsigned> jets_in_region(regions.size(), 0),
        varied_in_region(regions.size(), 0);
    unsigned region_mismatches = 0, smeared_across_50 = 0;
    for (unsigned e = 0; e < n; ++e) {
        for (std::size_t j = 0; j < r_pt.size(); ++j) {
            const float before = (*r_input)[e][j], nom = (*r_nominal)[e][j];
            const int jet_region = jerc_region(r_eta[j], nom);
            ++jets_in_region[jet_region];
            smeared_across_50 += std::abs(r_eta[j]) >= 2.5f &&
                                 (before < 50.f) != (nom < 50.f);
            for (std::size_t d = 0; d < directions.size(); ++d) {
                const float inclusive = (*r_inclusive[d])[e][j];
                varied_in_region[jet_region] += inclusive != nom;
                for (std::size_t r = 0; r < regions.size(); ++r) {
                    const float regional =
                        (*r_regional[d * regions.size() + r])[e][j];
                    const float expected =
                        jet_region == static_cast<int>(r) ? inclusive : nom;
                    region_mismatches += regional != expected;
                }
            }
        }
    }
    bool regions_populated = true, regions_varied = true;
    for (std::size_t r = 0; r < regions.size(); ++r) {
        regions_populated = regions_populated && jets_in_region[r] > n / 2;
        regions_varied = regions_varied && varied_in_region[r] > n / 2;
    }
    std::printf("JER regions: jets per region %u %u %u %u %u %u, %u jets "
                "smeared across 50 GeV, %u mismatches\n",
                jets_in_region[0], jets_in_region[1], jets_in_region[2],
                jets_in_region[3], jets_in_region[4], jets_in_region[5],
                smeared_across_50, region_mismatches);
    check(regions.size() == 6 && regions_populated,
          "the test jets populate the six JER regions");
    check(regions_varied, "the inclusive JER variation changes jets of every region");
    check(smeared_across_50 > 0,
          "jets beyond |eta| 2.5 are smeared across the 50 GeV edge, so that the "
          "nominal pt and the pt before the smearing give different regions");
    check(region_mismatches == 0,
          "a regional JER variation varies the jets of its region only, like "
          "the inclusive variation");

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
    check(max_scaled == 0., "the scaled pt is the pt before the JER smearing");
    check(max_scaled_up == 0., "the JER variation leaves the scaled pt alone");
    check(smeared_differs > n / 2, "the smeared pt differs from the scaled pt");
    return failures == 0 ? 0 : 1;
}
