#ifndef BBTAUTAU_EMBEDDING_ISO_HXX
#define BBTAUTAU_EMBEDDING_ISO_HXX

#include "ROOT/RDataFrame.hxx"
#include <string>
#include <vector>

namespace correctionManager {
class CorrectionManager;
}

namespace xyh::scalefactor {
/**
 * @brief Lepton isolation scale factor of the Tau Embedding group payloads,
 * taken from the correction of the lepton's isolation bin.
 *
 * The payloads hold one correction per isolation region, e.g. `Iso_pt_eta_bins`
 * below 0.15 and `AIso1_pt_eta_bins`/`AIso2_pt_eta_bins` above. Bin i of
 * `iso_edges` uses correction i; a value on an edge falls into the upper bin,
 * so the bin below the first edge matches a `iso < edge` selection. Apart from
 * the bin choice, the evaluation is that of `embedding::muon::Scalefactor`
 * (|eta|, `use_abs_eta = true`) and `embedding::electron::Scalefactor` (signed
 * eta, `use_abs_eta = false`), whose payloads bin eta differently.
 *
 * @param df input dataframe
 * @param manager correction manager that loads the scale factor file
 * @param output name of the output column with the scale factor
 * @param pt name of the lepton pt column
 * @param eta name of the lepton eta column
 * @param iso name of the lepton relative isolation column
 * @param file path to the embedding lepton correction file
 * @param iso_edges ascending isolation edges between the bins
 * @param corrections one correction name per bin, one more than edges
 * @param type "emb" for embedded, "mc" for simulated events
 * @param extrapolation_factor factor multiplied to the scale factor
 * @param use_abs_eta evaluate with |eta| (muons) instead of eta (electrons)
 *
 * @return a new dataframe with the scale factor column
 */
ROOT::RDF::RNode embedding_iso_binned(
    ROOT::RDF::RNode df, correctionManager::CorrectionManager &manager,
    const std::string &output, const std::string &pt, const std::string &eta,
    const std::string &iso, const std::string &file,
    const std::vector<float> &iso_edges,
    const std::vector<std::string> &corrections, const std::string &type,
    const float &extrapolation_factor, const bool use_abs_eta);
} // namespace xyh::scalefactor
#endif
