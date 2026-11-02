#include "../include/pog_muon_trigger_sf.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include <stdexcept>

namespace xyh::scalefactor {
ROOT::RDF::RNode
pog_muon_trigger(ROOT::RDF::RNode df,
                 correctionManager::CorrectionManager &manager,
                 const std::string &output, const std::string &pt,
                 const std::string &eta, const std::string &file,
                 const std::string &correction, const std::string &variation,
                 const float &extrapolation_factor, const double &min_pt,
                 const double &max_abs_eta) {
    if (!(min_pt > 0.0) || !(max_abs_eta > 0.0)) {
        throw std::invalid_argument(
            "xyh::scalefactor::pog_muon_trigger: needs min_pt > 0 and "
            "max_abs_eta > 0");
    }
    const auto evaluator = manager.loadCorrection(file, correction);
    // the range in double, as the payload edges (a float 2.4 lies above 2.4)
    return df.Define(
        output,
        [evaluator, variation, extrapolation_factor, min_pt,
         max_abs_eta](const float &pt, const float &eta) {
            const auto [at_pt, at_abs_eta] =
                pog_muon_trigger_point(pt, eta, min_pt, max_abs_eta);
            return extrapolation_factor *
                   evaluator->evaluate({at_abs_eta, at_pt, variation});
        },
        {pt, eta});
}
} // namespace xyh::scalefactor
