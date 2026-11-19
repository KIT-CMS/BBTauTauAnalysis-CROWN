#include "../include/embedding_iso.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace xyh::scalefactor {
ROOT::RDF::RNode embedding_iso_binned(
    ROOT::RDF::RNode df, correctionManager::CorrectionManager &manager,
    const std::string &output, const std::string &pt, const std::string &eta,
    const std::string &iso, const std::string &file,
    const std::vector<float> &iso_edges,
    const std::vector<std::string> &corrections, const std::string &type,
    const float &extrapolation_factor, const bool use_abs_eta) {
    if (corrections.size() != iso_edges.size() + 1 ||
        !std::is_sorted(iso_edges.begin(), iso_edges.end())) {
        throw std::invalid_argument(
            "xyh::scalefactor::embedding_iso_binned: needs ascending iso edges "
            "and one correction more than edges");
    }
    std::vector<const correction::Correction *> evaluators;
    for (const auto &name : corrections) {
        evaluators.push_back(manager.loadCorrection(file, name));
    }
    return df.Define(
        output,
        [evaluators, iso_edges, type, extrapolation_factor,
         use_abs_eta](const float &pt, const float &eta, const float &iso) {
            const auto bin =
                std::upper_bound(iso_edges.begin(), iso_edges.end(), iso) -
                iso_edges.begin();
            const float eta_input = use_abs_eta ? std::abs(eta) : eta;
            return extrapolation_factor *
                   evaluators[bin]->evaluate({pt, eta_input, type});
        },
        {pt, eta, iso});
}
} // namespace xyh::scalefactor
