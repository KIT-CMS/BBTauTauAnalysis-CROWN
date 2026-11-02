// Regression test for the CROWN core producer quantities::FastMtt, which the
// FastMTT friends (nmssm_fastmtt / sm_fastmtt) call.
//
// For every final state the producer has to hand FastMTT the decay type of
// each leg: a light lepton is a leptonic tau decay (two neutrinos), a tau_h a
// hadronic one (one neutrino). The test runs the producer on a one-event
// ROOT::RDataFrame and compares its result with a direct FastMTT call using
// the expected decay types. As a guard that the kinematics can tell the two
// apart, the expected leptonic result must also differ from the one obtained
// when both legs are treated as hadronic.

#include <Math/Vector4D.h>
#include <ROOT/RDataFrame.hxx>
#include <TMatrixD.h>

#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

#include "SVFit/FastMTT.hxx"
#include "SVFit/MeasuredTauLepton.hxx"
#include "quantities.hxx"

using fastmtt::MeasuredTauLepton;

struct Leg {
    int type;
    float pt, eta, phi, mass;
    int decay_mode;
};

const float met = 35.f, metphi = -1.5f, cov00 = 400.f, cov01 = 30.f,
            cov11 = 380.f;

double direct_fastmtt(const Leg &leg_1, const Leg &leg_2) {
    TMatrixD cov(2, 2);
    cov[0][0] = cov00;
    cov[0][1] = cov01;
    cov[1][0] = cov01;
    cov[1][1] = cov11;
    ROOT::Math::PtEtaPhiMVector met_p4(met, 0., metphi, 0.);
    std::vector<MeasuredTauLepton> legs;
    for (const Leg &leg : {leg_1, leg_2})
        legs.emplace_back(leg.type, leg.pt, leg.eta, leg.phi, leg.mass,
                          leg.decay_mode);
    FastMTT algo;
    return algo.run(legs, met_p4.X(), met_p4.Y(), cov).M();
}

double producer_fastmtt(const Leg &leg_1, const Leg &leg_2,
                        const std::string &finalstate) {
    ROOT::RDataFrame df(1);
    auto df1 = df.Define("pt_1", [&] { return leg_1.pt; })
                   .Define("pt_2", [&] { return leg_2.pt; })
                   .Define("eta_1", [&] { return leg_1.eta; })
                   .Define("eta_2", [&] { return leg_2.eta; })
                   .Define("phi_1", [&] { return leg_1.phi; })
                   .Define("phi_2", [&] { return leg_2.phi; })
                   .Define("mass_1", [&] { return leg_1.mass; })
                   .Define("mass_2", [&] { return leg_2.mass; })
                   .Define("met", [] { return met; })
                   .Define("metphi", [] { return metphi; })
                   .Define("metcov00", [] { return cov00; })
                   .Define("metcov01", [] { return cov01; })
                   .Define("metcov11", [] { return cov11; })
                   .Define("tau_decaymode_1", [&] { return leg_1.decay_mode; })
                   .Define("tau_decaymode_2", [&] { return leg_2.decay_mode; });
    auto df2 = quantities::FastMtt(
        df1, "p4_fastmtt", "pt_1", "pt_2", "eta_1", "eta_2", "phi_1", "phi_2",
        "mass_1", "mass_2", "met", "metphi", "metcov00", "metcov01", "metcov11",
        "tau_decaymode_1", "tau_decaymode_2", finalstate);
    return df2.Take<ROOT::Math::PtEtaPhiMVector>("p4_fastmtt")->at(0).M();
}

int main() {
    const int had = MeasuredTauLepton::kTauToHadDecay;
    const Leg muon{
        MeasuredTauLepton::kTauToMuDecay, 40.f, 0.5f, 0.3f, 0.1057f, -1};
    const Leg electron{
        MeasuredTauLepton::kTauToElecDecay, 38.f, 0.5f, 0.3f, 0.000511f, -1};
    const Leg tau_1{had, 55.f, 0.5f, 0.3f, 0.9f, 10};
    const Leg tau_2{had, 45.f, -0.3f, 2.9f, 0.8f, 1};
    const Leg muon_2{
        MeasuredTauLepton::kTauToMuDecay, 30.f, -0.3f, 2.9f, 0.1057f, -1};
    struct Case {
        std::string finalstate;
        Leg leg_1, leg_2;
    };
    const std::vector<Case> cases = {
        {"mt", muon, tau_2},
        {"et", electron, tau_2},
        {"em", electron, muon_2},
        {"tt", tau_1, tau_2},
    };

    int failures = 0;
    for (const Case &c : cases) {
        const double expected = direct_fastmtt(c.leg_1, c.leg_2);
        const double produced =
            producer_fastmtt(c.leg_1, c.leg_2, c.finalstate);
        Leg had_1 = c.leg_1, had_2 = c.leg_2;
        had_1.type = had_2.type = had;
        const double all_hadronic = direct_fastmtt(had_1, had_2);
        const bool leptonic = c.leg_1.type != had || c.leg_2.type != had;
        std::printf("%s: producer %.4f  expected %.4f  all-hadronic %.4f\n",
                    c.finalstate.c_str(), produced, expected, all_hadronic);
        if (leptonic && std::abs(expected / all_hadronic - 1.) < 0.01) {
            std::printf("  FAIL: kinematics do not separate the decay types\n");
            ++failures;
        }
        if (std::abs(produced - expected) > 1e-6 * expected) {
            std::printf("  FAIL: producer does not use the expected decay "
                        "types\n");
            ++failures;
        }
    }
    return failures == 0 ? 0 : 1;
}
