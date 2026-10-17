// Test of the electron SFs at the supercluster eta (v7 spec K7, C22): the pair
// electron's supercluster eta xyh::electron::supercluster_eta (eta +
// deltaEtaSC) feeds the core ID SF (physicsobject::electron::scalefactor::Id)
// and the reconstruction weight (xyh::scalefactor::electron_reco) of the
// official EGM payload. An electron with eta just below the barrel edge 1.444
// and supercluster eta just above it takes the SF of the bin above, and so at
// the endcap edge 1.566.
//
// Usage: test_electron_supercluster_eta <EGM electron.json.gz> <correction>
//        <year id> <ID working point>

#include "electron_reco.hxx"
#include "electron_supercluster.hxx"

#include "utility/CorrectionManager.hxx"

#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
#include <cmath>
#include <iostream>
#include <string>
#include <vector>

namespace physicsobject {
namespace electron {
namespace scalefactor {
// the core function (src/electrons.cxx)
ROOT::RDF::RNode Id(ROOT::RDF::RNode df,
                    correctionManager::CorrectionManager &correction_manager,
                    const std::string &outputname, const std::string &pt,
                    const std::string &eta, const std::string &phi,
                    const std::string &era, const std::string &wp,
                    const std::string &sf_file, const std::string &sf_name,
                    const std::string &variation);
} // namespace scalefactor
} // namespace electron
} // namespace physicsobject

namespace {

int g_failures = 0;

void check(bool ok, const std::string &name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << std::endl;
    if (!ok) {
        ++g_failures;
    }
}

// electron (eta, deltaEtaSC) cases: second electron of the pair at index 2
struct Case {
    float eta, delta_eta_sc;
};
const std::vector<Case> kCases = {
    {1.440f, 0.008f},   // barrel by eta, gap bin by supercluster eta
    {1.448f, -0.008f},  // the reverse
    {1.560f, 0.010f},   // gap bin by eta, endcap by supercluster eta
    {-1.440f, -0.008f}, // negative side
    {0.500f, 0.010f},   // far from an edge
};
constexpr float kPt = 40.f, kPhi = 0.3f;

} // namespace

int main(int argc, char **argv) {
    if (argc != 5) {
        std::cerr << "usage: " << argv[0]
                  << " <payload> <correction> <year id> <ID WP>" << std::endl;
        return 2;
    }
    const std::string payload = argv[1], cset = argv[2], year = argv[3],
                      wp = argv[4];
    correctionManager::CorrectionManager mgr;
    auto evaluator = mgr.loadCorrection(payload, cset);

    ROOT::RDataFrame df(kCases.size());
    ROOT::RDF::RNode node =
        df.Define("Electron_eta",
                  [](ULong64_t e) {
                      return ROOT::RVec<float>{0.1f, -0.2f, kCases.at(e).eta};
                  },
                  {"rdfentry_"})
            .Define("Electron_deltaEtaSC",
                    [](ULong64_t e) {
                        return ROOT::RVec<float>{0.0f, 0.0f,
                                                 kCases.at(e).delta_eta_sc};
                    },
                    {"rdfentry_"})
            .Define("dileptonpair", []() { return ROOT::RVec<int>{0, 2}; })
            .Define("dileptonpair_bad", []() { return ROOT::RVec<int>{0, 7}; })
            .Define("pt_2", []() { return kPt; })
            .Define("phi_2", []() { return kPhi; })
            .Define("eta_2",
                    [](ULong64_t e) { return kCases.at(e).eta; },
                    {"rdfentry_"});
    node = xyh::electron::supercluster_eta(node, "sc_eta_2", "Electron_eta",
                                           "Electron_deltaEtaSC",
                                           "dileptonpair", 1);
    node = xyh::electron::supercluster_eta(node, "sc_eta_bad", "Electron_eta",
                                           "Electron_deltaEtaSC",
                                           "dileptonpair_bad", 1);
    node = physicsobject::electron::scalefactor::Id(
        node, mgr, "id_wgt_ele_2", "pt_2", "sc_eta_2", "phi_2", year, wp,
        payload, cset, "sf");
    node = xyh::scalefactor::electron_reco(node, mgr, "reco_wgt_ele_2", "pt_2",
                                           "sc_eta_2", "phi_2", year, payload,
                                           cset, "sf");
    auto sc_eta = node.Take<float>("sc_eta_2");
    auto bad = node.Take<float>("sc_eta_bad");
    auto id = node.Take<double>("id_wgt_ele_2");
    auto reco = node.Take<double>("reco_wgt_ele_2");

    const std::string reco_key = "RecoAbove20"; // pT 40 GeV
    for (std::size_t i = 0; i < kCases.size(); ++i) {
        const float expected_sc = kCases[i].eta + kCases[i].delta_eta_sc;
        const std::string label = "eta " + std::to_string(kCases[i].eta) +
                                  ", eta_SC " + std::to_string(expected_sc);
        check(sc_eta->at(i) == expected_sc, label + ": supercluster eta");
        const double id_sc = evaluator->evaluate(
            {year, "sf", wp, static_cast<double>(expected_sc), double(kPt)});
        const double id_eta = evaluator->evaluate(
            {year, "sf", wp, static_cast<double>(kCases[i].eta), double(kPt)});
        const double reco_sc = evaluator->evaluate(
            {year, "sf", reco_key, static_cast<double>(expected_sc), double(kPt)});
        check(id->at(i) == id_sc, label + ": ID SF at the supercluster eta");
        check(reco->at(i) == reco_sc,
              label + ": reco SF at the supercluster eta");
        // the electrons that straddle an edge take another SF than at their eta
        if (i < 4) {
            check(id_sc != id_eta, label + ": the edge changes the ID SF");
        }
    }
    check(bad->at(0) == -10.f, "an index outside the collection gives the default");

    if (g_failures > 0) {
        std::cerr << g_failures << " case(s) FAILED" << std::endl;
        return 1;
    }
    std::cout << "All supercluster eta cases PASSED." << std::endl;
    return 0;
}
