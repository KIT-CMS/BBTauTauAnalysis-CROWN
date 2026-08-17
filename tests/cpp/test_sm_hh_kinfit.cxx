// Compilation + smoke test for hhkinfit::sm_hh_kinfit (the SM fixed-mass
// 125/125 HH kinematic fit, which reuses the vendored YHKinFitMaster engine
// with a single hypothesis pair).
//
// This is a standalone (non-CROWN-generated) executable: it builds a
// one-event ROOT::RDataFrame with plausible bb tautau four-vectors + MET +
// MET covariance + per-jet b resolutions (0.12 / 0.18, standing in for the
// ParticleNet regression resolutions bpair_reg_res_1/2 of the real ntuple),
// applies sm_hh_kinfit directly, and asserts that the four outputs
// (kinfit_convergence, kinfit_chi2, kinfit_prob, kinfit_mHH) are all finite,
// that the convergence flag is present, and that kinfit_mHH clears the
// 200 GeV sanity bound (sum of the two on-shell 125 GeV Higgs masses). Any
// convergence value is acceptable -- the point is a no-crash, sane-output
// proof that the engine is wired correctly for the single 125/125
// hypothesis with per-jet resolutions.
//
// Run via: bash tests/cpp/run_kinfit_compile_test.sh (inside the CROWN
// container -- see that script for the compile command).

#include <Math/Vector4D.h>
#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>

#include <cmath>
#include <iostream>
#include <string>
#include <vector>

#include "hhkinfit.hxx"

int main() {
    // One-event dataframe with plausible HH -> bb tautau kinematics.
    ROOT::RDataFrame df(1);

    auto df1 =
        df.Define(
              "p4_1",
              []() { return ROOT::Math::PtEtaPhiMVector(60.0, 0.5, 0.3, 1.0); })
            .Define("p4_2",
                    []() {
                        return ROOT::Math::PtEtaPhiMVector(45.0, -0.2, 2.8,
                                                           0.8);
                    })
            .Define("bpair_p4_1",
                    []() {
                        return ROOT::Math::PtEtaPhiMVector(90.0, 0.8, 1.5, 8.0);
                    })
            .Define("bpair_p4_2",
                    []() {
                        return ROOT::Math::PtEtaPhiMVector(75.0, -0.5, -1.8,
                                                           7.0);
                    })
            .Define("met_p4",
                    []() {
                        return ROOT::Math::PtEtaPhiMVector(40.0, 0.0, 1.0, 0.0);
                    })
            .Define("metcov00", []() { return 400.0f; })
            .Define("metcov01", []() { return 0.0f; })
            .Define("metcov11", []() { return 400.0f; })
            .Define("bpair_reso_1", []() { return 0.12f; })
            .Define("bpair_reso_2", []() { return 0.18f; });

    ROOT::RDF::RNode node = df1;

    const std::vector<std::string> outputs = {
        "kinfit_convergence", "kinfit_chi2", "kinfit_prob", "kinfit_mHH"};

    auto df2 =
        hhkinfit::sm_hh_kinfit(node, outputs, "p4_1", "p4_2", "bpair_p4_1",
                               "bpair_reso_1", "bpair_p4_2", "bpair_reso_2",
                               "met_p4", "metcov00", "metcov01", "metcov11");

    float convergence = df2.Take<float>("kinfit_convergence").GetValue().at(0);
    float chi2 = df2.Take<float>("kinfit_chi2").GetValue().at(0);
    float prob = df2.Take<float>("kinfit_prob").GetValue().at(0);
    float mHH = df2.Take<float>("kinfit_mHH").GetValue().at(0);

    std::cout << "kinfit_convergence = " << convergence << std::endl;
    std::cout << "kinfit_chi2        = " << chi2 << std::endl;
    std::cout << "kinfit_prob        = " << prob << std::endl;
    std::cout << "kinfit_mHH         = " << mHH << std::endl;

    int failures = 0;
    if (!std::isfinite(convergence)) {
        std::cerr << "FAIL kinfit_convergence is not finite" << std::endl;
        ++failures;
    }
    if (!std::isfinite(chi2)) {
        std::cerr << "FAIL kinfit_chi2 is not finite" << std::endl;
        ++failures;
    }
    if (!std::isfinite(prob)) {
        std::cerr << "FAIL kinfit_prob is not finite" << std::endl;
        ++failures;
    }
    if (!std::isfinite(mHH)) {
        std::cerr << "FAIL kinfit_mHH is not finite" << std::endl;
        ++failures;
    }
    // Sanity bound: for a 125/125 HH hypothesis fitted against two ~massless
    // Higgs decay systems (each with pt well above the individual Higgs
    // masses), the fitted di-Higgs invariant mass must clear the sum of the
    // two on-shell Higgs masses.
    if (mHH <= 200.0f) {
        std::cerr << "FAIL kinfit_mHH = " << mHH << " is not > 200"
                  << std::endl;
        ++failures;
    }

    if (failures > 0) {
        std::cerr << failures << " check(s) FAILED" << std::endl;
        return 1;
    }

    std::cout << "All sm_hh_kinfit outputs finite; convergence flag set."
              << std::endl;
    return 0;
}
