#include "../include/kit_trigger_sf.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include <cmath>
#include <stdexcept>

namespace xyh::scalefactor {
ROOT::RDF::RNode
kit_muon_trigger(ROOT::RDF::RNode df,
                 correctionManager::CorrectionManager &manager,
                 const std::string &output, const std::string &pt,
                 const std::string &eta, const std::string &file,
                 const std::string &correction, const std::string &type,
                 const float &extrapolation_factor, const float &max_pt,
                 const float &max_pt_max_abs_eta) {
    if (!(max_pt > 0.0f) || max_pt_max_abs_eta < 0.0f) {
        throw std::invalid_argument(
            "xyh::scalefactor::kit_muon_trigger: needs max_pt > 0 and "
            "max_pt_max_abs_eta >= 0");
    }
    const auto evaluator = manager.loadCorrection(file, correction);
    return df.Define(
        output,
        [evaluator, type, extrapolation_factor, max_pt,
         max_pt_max_abs_eta](const float &pt, const float &eta) {
            const float abs_eta = std::abs(eta);
            return extrapolation_factor *
                   evaluator->evaluate(
                       {evaluation_pt(pt, abs_eta, max_pt, max_pt_max_abs_eta),
                        abs_eta, type});
        },
        {pt, eta});
}
} // namespace xyh::scalefactor
