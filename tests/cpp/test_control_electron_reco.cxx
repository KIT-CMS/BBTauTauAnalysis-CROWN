#include "electron_reco.hxx"
#include "utility/CorrectionManager.hxx"
#include <cassert>
#include <cmath>
#include <string>

// Usage: <binary> <payload> <correction set> <era>
//
// The reconstruction weight must pick the official pt category of the era's
// payload per electron: Run 2 splits at 20 GeV (RecoBelow20 / RecoAbove20),
// Run 3 additionally at 75 GeV (Reco20to75 / RecoAbove75), and 2023 payloads
// take phi as a further input. Rejected pairs carry CROWN's default kinematics
// (-10) in shifted columns while the nominal pair is valid; the weight must be
// 1 there.
int main(int argc, char **argv) {
    assert(argc == 4);
    const std::string payload = argv[1];
    const std::string cset = argv[2];
    const std::string era = argv[3];
    const bool run3 = std::stoi(era.substr(0, 4)) > 2018;
    const bool with_phi = era.find("2023") != std::string::npos;

    correctionManager::CorrectionManager manager;
    auto correction = manager.loadCorrection(payload, cset);
    const float pts[] = {15.1f, 19.99f, 20.f, 30.f, 74.99f, 75.f, 150.f};
    const bool rejected_in_shift[] = {false, true, false, true, false, true, false};
    const int n = 7;
    const float eta = -1.2f;
    const float phi = 0.7f;
    ROOT::RDataFrame df(n);
    auto input =
        df.Define("pt", [pts](ULong64_t i) { return pts[i]; }, {"rdfentry_"})
            .Define("eta", [eta] { return eta; })
            .Define("phi", [phi] { return phi; })
            .Define("pt__shift", [pts, rejected_in_shift](ULong64_t i) { return rejected_in_shift[i] ? -10.f : pts[i]; }, {"rdfentry_"})
            .Define("eta__shift", [rejected_in_shift, eta](ULong64_t i) { return rejected_in_shift[i] ? -10.f : eta; }, {"rdfentry_"})
            .Define("phi__shift", [rejected_in_shift, phi](ULong64_t i) { return rejected_in_shift[i] ? -10.f : phi; }, {"rdfentry_"});
    auto nominal = xyh::scalefactor::electron_reco(
        input, manager, "reco", "pt", "eta", "phi", era, payload, cset, "sf");
    auto shifted = xyh::scalefactor::electron_reco(
        nominal, manager, "reco__shift", "pt__shift", "eta__shift", "phi__shift", era, payload, cset, "sf");
    auto values = shifted.Take<double>("reco");
    auto shifted_values = shifted.Take<double>("reco__shift");
    for (int i = 0; i < n; ++i) {
        std::string wp;
        if (pts[i] < 20.f) {
            wp = "RecoBelow20";
        } else if (!run3) {
            wp = "RecoAbove20";
        } else if (pts[i] < 75.f) {
            wp = "Reco20to75";
        } else {
            wp = "RecoAbove75";
        }
        std::vector<correction::Variable::Type> args = {era, "sf", wp, double(eta), double(pts[i])};
        if (with_phi) {
            args.push_back(double(phi));
        }
        const double expected = correction->evaluate(args);
        assert(std::abs(values->at(i) - expected) < 1e-12);
        const double expected_shift = rejected_in_shift[i] ? 1.0 : expected;
        assert(std::abs(shifted_values->at(i) - expected_shift) < 1e-12);
    }
    return 0;
}
