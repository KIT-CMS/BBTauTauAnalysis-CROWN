#include "embedding_iso.hxx"
#include "utility/CorrectionManager.hxx"
#include <cassert>
#include <cmath>
#include <string>
#include <vector>

// Usage: <binary> <muon payload> <electron payload>
//
// The iso-binned embedding SF must take the correction of the lepton's
// isolation bin (a value on an edge belongs to the upper bin) and keep the eta
// convention of the core embedding functions: |eta| for the muon payload, which
// clamps negative values into its first bin, and signed eta for the electron
// payload, which is binned from -2.5 to 2.5.

struct Lepton {
    float pt, eta, iso;
};

// Evaluate the addon on `leptons` and compare every value with a direct
// correctionlib evaluation of `expected_corrections`.
void check(const std::string &payload, const std::vector<float> &edges,
           const std::vector<std::string> &corrections, bool use_abs_eta,
           const std::vector<Lepton> &leptons,
           const std::vector<std::string> &expected_corrections) {
    correctionManager::CorrectionManager manager;
    const auto n = leptons.size();
    ROOT::RDataFrame df(n);
    auto input =
        df.Define("pt", [leptons](ULong64_t i) { return leptons[i].pt; }, {"rdfentry_"})
            .Define("eta", [leptons](ULong64_t i) { return leptons[i].eta; }, {"rdfentry_"})
            .Define("iso", [leptons](ULong64_t i) { return leptons[i].iso; }, {"rdfentry_"});
    auto values = xyh::scalefactor::embedding_iso_binned(
                      input, manager, "sf", "pt", "eta", "iso", payload, edges,
                      corrections, "emb", 1.0, use_abs_eta)
                      .Take<double>("sf");
    for (std::size_t i = 0; i < n; ++i) {
        const auto &lepton = leptons[i];
        const double eta = use_abs_eta ? std::abs(lepton.eta) : lepton.eta;
        const double expected =
            manager.loadCorrection(payload, expected_corrections[i])
                ->evaluate({double(lepton.pt), eta, "emb"});
        assert(std::abs(values->at(i) - expected) < 1e-12);
    }
}

int main(int argc, char **argv) {
    assert(argc == 3);
    const std::string muon = argv[1], electron = argv[2];

    const std::vector<std::string> muon_iso = {"Iso_pt_eta_bins", "AIso1_pt_eta_bins", "AIso2_pt_eta_bins"};
    check(muon, {0.15, 0.25}, muon_iso, true,
          {{35, 0.5, 0.10}, {35, 0.5, 0.15}, {35, 0.5, 0.20}, {35, 0.5, 0.25}, {35, 0.5, 0.40},
           {35, -1.5, 0.20}, {35, 1.5, 0.20}, {35, -2.2, 0.20}},
          {muon_iso[0], muon_iso[1], muon_iso[1], muon_iso[2], muon_iso[2],
           muon_iso[1], muon_iso[1], muon_iso[1]});

    const std::vector<std::string> electron_iso = {"Iso_pt_eta_bins", "AIso_pt_eta_bins"};
    check(electron, {0.15}, electron_iso, false,
          {{35, 0.5, 0.10}, {35, 0.5, 0.15}, {35, 0.5, 0.20}, {35, 0.5, 0.25}, {35, 0.5, 0.40},
           {35, -0.5, 0.20}, {30, -1.8, 0.20}, {30, 1.8, 0.20}},
          {electron_iso[0], electron_iso[1], electron_iso[1], electron_iso[1], electron_iso[1],
           electron_iso[1], electron_iso[1], electron_iso[1]});

    // the conventions matter: the electron payload is asymmetric in eta
    correctionManager::CorrectionManager manager;
    auto aiso = manager.loadCorrection(electron, "AIso_pt_eta_bins");
    assert(aiso->evaluate({35., -0.5, "emb"}) != aiso->evaluate({35., 0.5, "emb"}));
    return 0;
}
