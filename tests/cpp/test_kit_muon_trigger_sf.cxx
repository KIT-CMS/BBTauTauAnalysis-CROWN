// Test of the KIT single-muon trigger SF of MC with the pT cap,
// xyh::scalefactor::kit_muon_trigger (v7 spec E5/C6), on the 2016preVFP payload
// whose bin pT >= 200 GeV, |eta| < 0.9 of type mc holds 2.756.
//
// Usage: <binary> <data/embedding/muon_2016preVFPUL.json.gz>

#include "kit_trigger_sf.hxx"
#include "utility/CorrectionManager.hxx"

#include <ROOT/RDataFrame.hxx>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

void check(bool ok, const std::string &name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << std::endl;
    if (!ok) {
        ++g_failures;
    }
}

struct Muon {
    float pt, eta;
};

std::vector<double> evaluate(const std::string &payload,
                             const std::vector<Muon> &muons,
                             float extrapolation, float max_pt,
                             float max_pt_max_abs_eta) {
    correctionManager::CorrectionManager manager;
    ROOT::RDataFrame df(muons.size());
    auto input =
        df.Define("pt", [muons](ULong64_t i) { return muons[i].pt; },
                  {"rdfentry_"})
            .Define("eta", [muons](ULong64_t i) { return muons[i].eta; },
                    {"rdfentry_"});
    return *xyh::scalefactor::kit_muon_trigger(
                input, manager, "sf", "pt", "eta", payload, "Trg_pt_eta_bins",
                "mc", extrapolation, max_pt, max_pt_max_abs_eta)
                .Take<double>("sf");
}

} // namespace

int main(int argc, char **argv) {
    if (argc != 2) {
        std::cerr << "usage: " << argv[0] << " <muon payload>" << std::endl;
        return 2;
    }
    const std::string payload = argv[1];
    correctionManager::CorrectionManager manager;
    auto direct = [&](double pt, double eta) {
        return manager.loadCorrection(payload, "Trg_pt_eta_bins")
            ->evaluate({pt, std::abs(eta), "mc"});
    };

    // the defect the cap is for
    check(direct(250.0, 0.5) > 2.7 && direct(150.0, 0.5) < 1.0,
          "payload: 2.756 above 200 GeV in the barrel, below 1 under it");

    const std::vector<Muon> muons = {
        {30.f, 0.5f},   {150.f, 0.5f},  {199.f, -0.3f}, {250.f, 0.5f},
        {250.f, -0.5f}, {900.f, 0.89f}, {250.f, 1.0f},  {250.f, -2.2f}};

    // no cap (the setting of every other era and correction)
    auto plain = evaluate(payload, muons, 1.0f, 1000.0f, 0.0f);
    bool same = true;
    for (std::size_t i = 0; i < muons.size(); ++i) {
        same &= std::abs(plain[i] - direct(muons[i].pt, muons[i].eta)) < 1e-12;
    }
    check(same, "without a cap: the payload value at the muon pT");

    // the 2016preVFP setting: 199.9 GeV below |eta| 0.9
    auto capped = evaluate(payload, muons, 1.0f, 199.9f, 0.9f);
    check(std::abs(capped[0] - direct(30.0, 0.5)) < 1e-12 &&
              std::abs(capped[1] - direct(150.0, 0.5)) < 1e-12 &&
              std::abs(capped[2] - direct(199.0, 0.3)) < 1e-12,
          "capped: unchanged below the cap");
    check(std::abs(capped[3] - direct(199.9, 0.5)) < 1e-12 &&
              std::abs(capped[4] - direct(199.9, 0.5)) < 1e-12 &&
              std::abs(capped[5] - direct(199.9, 0.89)) < 1e-12,
          "capped: the 100-200 GeV value above 200 GeV in the barrel");
    check(capped[3] > 0.9 && capped[3] < 0.95, "capped: 0.933 in the barrel");
    check(std::abs(capped[6] - direct(250.0, 1.0)) < 1e-12 &&
              std::abs(capped[7] - direct(250.0, 2.2)) < 1e-12,
          "capped: unchanged above 200 GeV outside |eta| 0.9");

    // the shift factor
    auto up = evaluate(payload, muons, 1.02f, 199.9f, 0.9f);
    bool scaled = true;
    for (std::size_t i = 0; i < muons.size(); ++i) {
        scaled &= std::abs(up[i] - 1.02f * capped[i]) < 1e-6;
    }
    check(scaled, "extrapolation factor scales the SF");

    bool threw = false;
    try {
        evaluate(payload, muons, 1.0f, 0.0f, 0.9f);
    } catch (const std::invalid_argument &) {
        threw = true;
    }
    check(threw, "max_pt <= 0 throws");

    std::cout << (g_failures == 0 ? "ALL PASS" : "FAILURES") << std::endl;
    return g_failures == 0 ? 0 : 1;
}
