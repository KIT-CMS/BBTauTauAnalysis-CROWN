#ifndef BBTAUTAU_KIT_TRIGGER_SF_HXX
#define BBTAUTAU_KIT_TRIGGER_SF_HXX

#include "ROOT/RDataFrame.hxx"
#include <string>

namespace correctionManager {
class CorrectionManager;
}

namespace xyh::scalefactor {
/**
 * @brief The pT at which a KIT trigger SF is evaluated: `max_pt` for a lepton
 * above it with |eta| below `max_pt_max_abs_eta`, the lepton pT otherwise.
 *
 * It keeps a defective high-pT bin of a payload out of the evaluation, which
 * then takes the bin below it. `max_pt_max_abs_eta` = 0 evaluates every lepton
 * at its pT.
 */
inline float evaluation_pt(const float &pt, const float &abs_eta,
                           const float &max_pt,
                           const float &max_pt_max_abs_eta) {
    return (abs_eta < max_pt_max_abs_eta && pt > max_pt) ? max_pt : pt;
}

/**
 * @brief Single-muon trigger scale factor of the Tau Embedding group (KIT)
 * payloads, evaluated like `embedding::muon::Scalefactor` (pT, |eta|, type,
 * times the extrapolation factor), but at `evaluation_pt`.
 *
 * @param df input dataframe
 * @param manager correction manager that loads the scale factor file
 * @param output name of the output column with the scale factor
 * @param pt name of the muon pt column
 * @param eta name of the muon eta column
 * @param file path to the KIT muon correction file
 * @param correction name of the trigger correction
 * @param type "mc" for simulated, "emb" for embedded events
 * @param extrapolation_factor factor multiplied to the scale factor
 * @param max_pt highest pT the correction is evaluated at
 * @param max_pt_max_abs_eta |eta| below which `max_pt` applies (0: nowhere)
 *
 * @return a new dataframe with the scale factor column
 */
ROOT::RDF::RNode
kit_muon_trigger(ROOT::RDF::RNode df,
                 correctionManager::CorrectionManager &manager,
                 const std::string &output, const std::string &pt,
                 const std::string &eta, const std::string &file,
                 const std::string &correction, const std::string &type,
                 const float &extrapolation_factor, const float &max_pt,
                 const float &max_pt_max_abs_eta);
} // namespace xyh::scalefactor
#endif
