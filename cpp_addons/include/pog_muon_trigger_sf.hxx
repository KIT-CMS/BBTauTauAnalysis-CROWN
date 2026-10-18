#ifndef BBTAUTAU_POG_MUON_TRIGGER_SF_HXX
#define BBTAUTAU_POG_MUON_TRIGGER_SF_HXX

#include "ROOT/RDataFrame.hxx"
#include <algorithm>
#include <cmath>
#include <string>
#include <utility>

namespace correctionManager {
class CorrectionManager;
}

namespace xyh::scalefactor {
/**
 * @brief The (pT, |eta|) at which a POG (MUO) single-muon trigger SF is
 * evaluated: the pT raised to `min_pt`, the lowest edge of the payload, and
 * |eta| lowered to just below `max_abs_eta`, its highest edge.
 *
 * The Run-2 UL muon_Z payloads end at their edges with flow "error"
 * (pT >= 26 GeV, 29 GeV for 2017 IsoMu27; |eta| < 2.4), while the analysis
 * triggers start below them (2016 IsoMu22 family: 24 GeV, 2018 tau-ID
 * measurement IsoMu24: 25 GeV). A muon below the range takes the SF of the
 * lowest pT bin.
 */
inline std::pair<double, double>
pog_muon_trigger_point(const float &pt, const float &eta, const double &min_pt,
                       const double &max_abs_eta) {
    return {std::max(static_cast<double>(pt), min_pt),
            std::min(std::abs(static_cast<double>(eta)),
                     std::nextafter(max_abs_eta, 0.0))};
}

/**
 * @brief Single-muon trigger scale factor of MC from a POG (MUO) correctionlib
 * payload (muon_Z.json.gz, inputs eta, pt, scale_factors), evaluated at every
 * muon pT (the trigger flags select downstream) at `pog_muon_trigger_point`,
 * times the extrapolation factor (the shift CMS_eff_m_trigger_<era> scales it by
 * 1.02 / 0.98).
 *
 * @param df input dataframe
 * @param manager correction manager that loads the scale factor file
 * @param output name of the output column with the scale factor
 * @param pt name of the muon pt column
 * @param eta name of the muon eta column
 * @param file path to the POG muon correction file
 * @param correction name of the trigger correction, e.g.
 * "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"
 * @param variation "nominal", "systup" or "systdown"
 * @param extrapolation_factor factor multiplied to the scale factor
 * @param min_pt lowest pT of the payload (its first edge)
 * @param max_abs_eta highest |eta| of the payload (its last edge)
 *
 * @return a new dataframe with the scale factor column
 */
ROOT::RDF::RNode
pog_muon_trigger(ROOT::RDF::RNode df,
                 correctionManager::CorrectionManager &manager,
                 const std::string &output, const std::string &pt,
                 const std::string &eta, const std::string &file,
                 const std::string &correction, const std::string &variation,
                 const float &extrapolation_factor, const double &min_pt,
                 const double &max_abs_eta);
} // namespace xyh::scalefactor
#endif
