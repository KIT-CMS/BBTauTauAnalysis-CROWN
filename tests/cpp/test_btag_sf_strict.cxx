// Fixture-driven test for
// xyh::scalefactor::btagging_strict::multi_wp_event_weight (+ pt_clamped_njets).
//
// A standalone (non-CROWN-generated) executable that drives the strict
// UParTAK4 fixed-multi-WP b-tag event-weight consumer against synthetic
// correctionlib fixtures (tests/fixtures/btag_sf_strict_{sf,eff}.json,
// produced by tests/fixtures/make_btag_sf_strict_fixtures.py) and, for the
// pt-flow case, against the REAL pinned SF payload on cvmfs.
//
// Cases (see the brief):
//   (a) nominal weight reproduces a hand-computed value;
//   (b) efficiency <= 0 -> throws;
//   (c) non-monotonic efficiencies -> throws;
//   (d) comb-only variation (up_hf) changes b/c jets, leaves light central
//       (mixed-flavor event);
//   (e) unsupported variation key -> throws;
//   (f) real pinned SF payload pt-flow: comb central is finite and
//       pt-flow-extrapolated at the {25, 29.9, 30, 31, 299.9, 300, 300.1, 350}
//       boundaries;
//   (g) jet passing the TIGHTEST WP (XXT) -> jet_w == SF(XXT), the eff-cancel
//       branch of the algebra;
//   (h) jet failing ALL WPs (score below the loosest, L) -> jet_w ==
//       (1 - SF(L)*eff(L)) / (1 - eff(L)), the untagged-probability branch.
//
// Run via: bash tests/cpp/run_btag_sf_test.sh (inside the CROWN container --
// see that script for the compile command and the cvmfs bind).

#include "btag_sf_strict.hxx"

#include "utility/CorrectionManager.hxx"

#include "correction.h"

#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
#include <cmath>
#include <cstddef>
#include <exception>
#include <functional>
#include <iostream>
#include <string>
#include <vector>

#ifndef BTAG_FIXTURE_SF
#define BTAG_FIXTURE_SF "tests/fixtures/btag_sf_strict_sf.json"
#endif
#ifndef BTAG_FIXTURE_EFF
#define BTAG_FIXTURE_EFF "tests/fixtures/btag_sf_strict_eff.json"
#endif
#ifndef BTAG_REAL_SF
#define BTAG_REAL_SF                                                           \
    "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/"                            \
    "Run2-2018-UL-NanoAODv15/2026-06-18/btagging.json.gz"
#endif

namespace {

int g_failures = 0;

// Relative-tolerance float comparison for the hand-computed algebra.
bool approx_equal(double a, double b, double tol = 1e-6) {
    if (a == b) {
        return true;
    }
    double denom = std::abs(a) + std::abs(b);
    if (denom == 0.0) {
        return true;
    }
    return std::abs(a - b) / denom < tol;
}

void check(bool ok, const std::string &name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << std::endl;
    if (!ok) {
        ++g_failures;
    }
}

template <typename T>
ROOT::RVec<T> mkvec(const std::vector<T> &values) {
    ROOT::RVec<T> out;
    for (const auto &value : values) {
        out.push_back(value);
    }
    return out;
}

// Synthetic WP thresholds, tightest -> loosest {XXT, XT, T, M, L}. Match the
// synthetic UParTAK4_wp_values in the fixture SF file.
const std::vector<float> kSynthWpValues = {0.9f, 0.7f, 0.5f, 0.3f, 0.1f};

// Run the strict consumer on a single (possibly multi-jet) event and return
// the event weight. May throw (the strict consumer rejects degenerate input).
double run_weight(correctionManager::CorrectionManager &mgr,
                  const std::vector<float> &pt, const std::vector<float> &eta,
                  const std::vector<int> &flavor,
                  const std::vector<float> &score, const std::vector<int> &mask,
                  const std::string &eff_sample_type,
                  const std::string &variation_comb,
                  const std::string &variation_light) {
    ROOT::RDataFrame df(1);
    auto defined =
        df.Define("Jet_pt", [pt]() { return mkvec(pt); })
            .Define("Jet_eta", [eta]() { return mkvec(eta); })
            .Define("Jet_flavor", [flavor]() { return mkvec(flavor); })
            .Define("Jet_score", [score]() { return mkvec(score); })
            .Define("Jet_mask", [mask]() { return mkvec(mask); });
    ROOT::RDF::RNode node = defined;
    auto out = xyh::scalefactor::btagging_strict::multi_wp_event_weight(
        node, mgr, "btag_weight_upart", "Jet_pt", "Jet_eta", "Jet_flavor",
        "Jet_score", "Jet_mask", BTAG_FIXTURE_SF, BTAG_FIXTURE_EFF,
        eff_sample_type, variation_comb, variation_light, kSynthWpValues);
    return out.Take<double>("btag_weight_upart").GetValue().at(0);
}

bool throws(const std::function<void()> &fn) {
    try {
        fn();
        return false;
    } catch (const std::exception &) {
        return true;
    }
}

} // namespace

int main() {
    correctionManager::CorrectionManager mgr;

    // ------------------------------------------------------------------
    // (a) Nominal weight reproduces a hand-computed value.
    //
    // A single b-jet (flavor 5) with score 0.4 passes WP M (0.4 >= 0.3) but
    // not WP T (0.4 < 0.5), so it lands in the M/T bin:
    //     jet_w = (SF(M)*eff(M) - SF(T)*eff(T)) / (eff(M) - eff(T))
    // With the fixture "valid" efficiencies (flavor 5): eff(M)=0.60, eff(T)=0.40
    // and central comb SFs (flavor 5): SF(M)=0.95, SF(T)=0.90:
    //     jet_w = (0.95*0.60 - 0.90*0.40) / (0.60 - 0.40)
    //           = (0.57 - 0.36) / 0.20 = 0.21 / 0.20 = 1.05
    // ------------------------------------------------------------------
    {
        double w = run_weight(mgr, {50.0f}, {1.0f}, {5}, {0.4f}, {1}, "valid",
                              "central", "central");
        check(approx_equal(w, 1.05), "(a) nominal weight == hand-computed 1.05");
    }

    // ------------------------------------------------------------------
    // (b) An efficiency <= 0 must throw (no silent 1.0 substitution). The
    // "zero" regime sets flavor-5 eff(M) = 0.
    // ------------------------------------------------------------------
    {
        bool did_throw = throws([&]() {
            run_weight(mgr, {50.0f}, {1.0f}, {5}, {0.4f}, {1}, "zero",
                       "central", "central");
        });
        check(did_throw, "(b) efficiency <= 0 throws");
    }

    // ------------------------------------------------------------------
    // (c) Non-monotonic efficiencies must throw. The "nonmono" regime sets
    // flavor-5 eff(M)=0.30 < eff(T)=0.50, so the M/T bin has a non-positive
    // denominator.
    // ------------------------------------------------------------------
    {
        bool did_throw = throws([&]() {
            run_weight(mgr, {50.0f}, {1.0f}, {5}, {0.4f}, {1}, "nonmono",
                       "central", "central");
        });
        check(did_throw, "(c) non-monotonic efficiency throws");
    }

    // ------------------------------------------------------------------
    // (d) A comb-only component (up_hf) changes b/c jets while leaving light
    // jets central. Mixed event: one b-jet (flavor 5, score 0.4) and one light
    // jet (flavor 0, score 0.15). Dispatch: variation_comb="up_hf",
    // variation_light="central".
    //   * The (up_hf,central)/(central,central) ratio of the MIXED weight must
    //     equal that of the b-only weight -> the light factor is identical in
    //     both (unaffected by the comb-only component).
    //   * The b-only ratio must differ from 1 -> the b-jet actually changed.
    //   * The light-only weight is identical under (up_hf,central) and
    //     (central,central) -> light stays central.
    // ------------------------------------------------------------------
    {
        double w_mixed_cc = run_weight(mgr, {50.0f, 60.0f}, {1.0f, 1.2f},
                                       {5, 0}, {0.4f, 0.15f}, {1, 1}, "valid",
                                       "central", "central");
        double w_mixed_uc = run_weight(mgr, {50.0f, 60.0f}, {1.0f, 1.2f},
                                       {5, 0}, {0.4f, 0.15f}, {1, 1}, "valid",
                                       "up_hf", "central");
        double w_bonly_cc = run_weight(mgr, {50.0f}, {1.0f}, {5}, {0.4f}, {1},
                                       "valid", "central", "central");
        double w_bonly_uc = run_weight(mgr, {50.0f}, {1.0f}, {5}, {0.4f}, {1},
                                       "valid", "up_hf", "central");
        double w_lonly_cc = run_weight(mgr, {60.0f}, {1.2f}, {0}, {0.15f}, {1},
                                       "valid", "central", "central");
        double w_lonly_uc = run_weight(mgr, {60.0f}, {1.2f}, {0}, {0.15f}, {1},
                                       "valid", "up_hf", "central");
        double ratio_mixed = w_mixed_uc / w_mixed_cc;
        double ratio_bonly = w_bonly_uc / w_bonly_cc;
        check(approx_equal(ratio_mixed, ratio_bonly),
              "(d) mixed-event variation ratio is entirely from the b-jet");
        check(!approx_equal(ratio_bonly, 1.0),
              "(d) comb-only component changes the b-jet weight");
        check(approx_equal(w_lonly_uc, w_lonly_cc),
              "(d) light jet stays central under a comb-only component");
    }

    // ------------------------------------------------------------------
    // (e) An unsupported variation key must throw (the fixture comb systematic
    // category has no default, so correctionlib raises; the consumer rethrows
    // with the jet kinematics).
    // ------------------------------------------------------------------
    {
        bool did_throw = throws([&]() {
            run_weight(mgr, {50.0f}, {1.0f}, {5}, {0.4f}, {1}, "valid",
                       "up_DOES_NOT_EXIST", "central");
        });
        check(did_throw, "(e) unsupported variation key throws");
    }

    // ------------------------------------------------------------------
    // (f) Real pinned SF payload pt-flow. UParTAK4_comb central for flavor 5
    // has pt bin edges [30, 50, 70, 100, 140, 200, 300] and a single constant
    // flow value that equals the top pt bin (clamp-to-top-bin convention): so
    // pt < 30 and pt >= 300 both return that flow/top-bin value, while pt in
    // [30, 300) returns the measured bin values.
    //   * all boundary evaluations are finite;
    //   * pt=25 (flow) differs from pt=31 (first real bin);
    //   * pt=29.9 (flow) differs from pt=30 (first real bin);
    //   * the SF varies across the measured range (first bin != last bin);
    //   * pt=299.9 (top bin) == pt=300.1 (flow clamp) == pt=300 == pt=350.
    // ------------------------------------------------------------------
    {
        try {
            const correction::Correction *comb =
                mgr.loadCorrection(BTAG_REAL_SF, "UParTAK4_comb");
            auto sf = [&](double pt) {
                return comb->evaluate(
                    {std::string("central"), std::string("M"), 5, 1.0, pt});
            };
            double sf25 = sf(25.0), sf299 = sf(29.9), sf30 = sf(30.0),
                   sf31 = sf(31.0), sf2999 = sf(299.9), sf300 = sf(300.0),
                   sf3001 = sf(300.1), sf350 = sf(350.0);
            bool all_finite = std::isfinite(sf25) && std::isfinite(sf299) &&
                              std::isfinite(sf30) && std::isfinite(sf31) &&
                              std::isfinite(sf2999) && std::isfinite(sf300) &&
                              std::isfinite(sf3001) && std::isfinite(sf350);
            check(all_finite, "(f) real payload boundary SFs are finite");
            check(!approx_equal(sf25, sf31),
                  "(f) pt=25 (flow) differs from pt=31 (first bin)");
            check(!approx_equal(sf299, sf30),
                  "(f) pt=29.9 (flow) differs from pt=30 (first bin)");
            check(!approx_equal(sf31, sf2999),
                  "(f) SF varies across the measured pt range (first vs last "
                  "bin)");
            check(approx_equal(sf2999, sf3001) &&
                      approx_equal(sf3001, sf300) &&
                      approx_equal(sf3001, sf350),
                  "(f) pt >= top edge clamps to the top-bin value (flow)");
        } catch (const std::exception &error) {
            check(false, std::string("(f) real payload eval threw: ") +
                             error.what());
        }
    }

    // ------------------------------------------------------------------
    // (g) Jet passing the TIGHTEST WP (XXT). thresholds (kSynthWpValues,
    // tightest -> loosest) are {XXT:0.9, XT:0.7, T:0.5, M:0.3, L:0.1}; a
    // score of 0.95 >= 0.9 passes XXT, so `passed == 0` and the algebra
    // collapses to jet_w = (SF(XXT)*eff(XXT)) / eff(XXT) = SF(XXT) (the
    // efficiency cancels but is still evaluated/validated).
    // Flavor 5, "valid" regime, central comb SF/eff (from
    // make_btag_sf_strict_fixtures.py):
    //   SF(XXT) = COMB_BASE[5]["XXT"] + delta["central"] = 0.80 + 0 = 0.80
    //   eff(XXT) = EFF_VALID[5]["XXT"] = 0.10 (> 0, so no throw)
    //   jet_w = SF(XXT) = 0.80
    // ------------------------------------------------------------------
    {
        double w = run_weight(mgr, {50.0f}, {1.0f}, {5}, {0.95f}, {1}, "valid",
                              "central", "central");
        check(approx_equal(w, 0.80),
              "(g) tightest-WP pass reproduces hand-computed SF(XXT) == 0.80");
    }

    // ------------------------------------------------------------------
    // (h) Jet failing ALL WPs: score 0.05 < loosest threshold L (0.1), so
    // `passed == thresholds.size()` and the algebra uses the
    // untagged-probability branch:
    //     jet_w = (1 - SF(L)*eff(L)) / (1 - eff(L))
    // Flavor 5, "valid" regime, central comb SF/eff:
    //   SF(L) = COMB_BASE[5]["L"] + delta["central"] = 0.98 + 0 = 0.98
    //   eff(L) = EFF_VALID[5]["L"] = 0.80
    //   jet_w = (1 - 0.98*0.80) / (1 - 0.80)
    //         = (1 - 0.784) / 0.20 = 0.216 / 0.20 = 1.08
    // ------------------------------------------------------------------
    {
        double w = run_weight(mgr, {50.0f}, {1.0f}, {5}, {0.05f}, {1}, "valid",
                              "central", "central");
        check(approx_equal(w, 1.08),
              "(h) fails-all-WPs reproduces hand-computed "
              "(1-SF(L)*eff(L))/(1-eff(L)) == 1.08");
    }

    // ------------------------------------------------------------------
    // pt-clamp diagnostic: only selected jets with pt above the threshold are
    // counted.
    // ------------------------------------------------------------------
    {
        ROOT::RDataFrame df(1);
        auto defined =
            df.Define("Jet_pt",
                      []() {
                          return ROOT::RVec<float>{25.0f, 1500.0f, 2000.0f};
                      })
                .Define("Jet_mask",
                        []() { return ROOT::RVec<int>{1, 1, 0}; });
        ROOT::RDF::RNode node = defined;
        auto out = xyh::scalefactor::btagging_strict::pt_clamped_njets(
            node, "btag_eff_pt_clamped_njets", "Jet_pt", "Jet_mask", 1000.0f);
        unsigned int n =
            out.Take<unsigned int>("btag_eff_pt_clamped_njets").GetValue().at(0);
        // pt=1500 selected & > 1000 -> counted; pt=25 selected but < 1000;
        // pt=2000 > 1000 but not selected. Expect exactly 1.
        check(n == 1u, "(clamp) counts only selected jets with pt > threshold");
    }

    if (g_failures > 0) {
        std::cerr << g_failures << " case(s) FAILED" << std::endl;
        return 1;
    }
    std::cout << "All strict UParTAK4 b-tag cases PASSED." << std::endl;
    return 0;
}
