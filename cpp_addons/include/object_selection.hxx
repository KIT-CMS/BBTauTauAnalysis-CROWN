#ifndef GUARDOBJECTSELECTION_HXX
#define GUARDOBJECTSELECTION_HXX

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <vector>

// namespace xyh
namespace xyh {

// namespace object_selection
namespace object_selection {

/**
 * @brief Create selection masks for jets.
 *
 * This inline function is intended to be used in `ROOT::RDataFrame::Define`
 * statements.
 *
 * The vectors `pt`, `eta`, and `id` contain the values of the jet observables
 * for each jet in the events. `min_pt`, `abs_max_eta`, and `id_wp` are the
 * parameters for the jet selection.
 *
 * @param pt The jet transverse momentum.
 * @param eta The jet pseudorapidity.
 * @param id The jet identification bitmask.
 * @param min_pt The minimum transverse momentum for selected jets.
 * @param abs_max_eta The maximum absolute pseudorapidity for selected jets.
 * @param id_wp The working point for the jet identification.
 * @param apply_jet_horn_veto Whether to apply the jet horn veto.
 *
 * @note The function does not apply pileup ID, as it is not present for PFPuppi
 * jets. If it should be applied, use the overloaded function with pileup ID.
 *
 * @note The jet horn veto removes jets in the pseudorapidity range \(2.5 <
 * |\eta| < 3.0\) with a transverse momentum \(p_T < 50\) GeV.
 */
inline auto select_jet(const ROOT::RVec<float> &pt,
                       const ROOT::RVec<float> &eta, const ROOT::RVec<int> &id,
                       const float &min_pt, const float &abs_max_eta,
                       const int &id_wp, const bool &apply_jet_horn_veto) {
    // jet horn veto: veto jets in 2.5 < eta < 3.0 with a pt smaller than 50 GeV
    // jets that have this flag set to "true" shall be ignored, i.e., selected
    // jets should have !jet_horn_veto
    auto jet_horn_veto = (abs(eta) > 2.5) && (abs(eta) < 3.0) && (pt < 50.0);

    // create the selection mask
    auto mask = ((pt > min_pt) && (abs(eta) < abs_max_eta) && (id >= id_wp) &&
                 !(apply_jet_horn_veto && jet_horn_veto));
    return mask;
}

/**
 * @brief Create selection masks for jets.
 *
 * This inline function is intended to be used in `ROOT::RDataFrame::Define`
 * statements.
 *
 * The vectors `pt`, `eta`, and `id` contain the values of the jet observables
 * for each jet in the events. `min_pt`, `abs_max_eta`, and `id_wp` are the
 * parameters for the jet selection.
 *
 * @param pt The jet transverse momentum.
 * @param eta The jet pseudorapidity.
 * @param id The jet identification bitmask.
 * @param puid The jet pileup identification bitmask.
 * @param min_pt The minimum transverse momentum for selected jets.
 * @param abs_max_eta The maximum absolute pseudorapidity for selected jets.
 * @param id_wp The working point for the jet identification.
 * @param apply_jet_horn_veto Whether to apply the jet horn veto.
 * @param puid_wp The working point for the jet pileup identification.
 * @param puid_max_pt The maximum transverse momentum for the pileup
 * identification.
 *
 * @note The function applies pileup ID.
 *       If it should not be applied, use the overloaded function with pileup
 * ID.
 *
 * @note The jet horn veto removes jets in the pseudorapidity range \(2.5 <
 * |\eta| < 3.0\) with a transverse momentum \(p_T < 50\) GeV.
 */
inline auto select_jet(const ROOT::RVec<float> &pt,
                       const ROOT::RVec<float> &eta, const ROOT::RVec<int> &id,
                       const ROOT::RVec<int> &puid, const float &min_pt,
                       const float &abs_max_eta, const int &id_wp,
                       const bool &apply_jet_horn_veto, const int &puid_wp,
                       const float &puid_max_pt) {
    // create  pileup ID mask
    auto puid_mask =
        (pt > puid_max_pt) || ((pt <= puid_max_pt) && (puid >= puid_wp));

    // evaluate jet selection with base function and add pileup ID mask
    auto mask = (select_jet(pt, eta, id, min_pt, abs_max_eta, id_wp,
                            apply_jet_horn_veto) &&
                 puid_mask);

    return mask;
}

// function xyh::object_selection::electron
ROOT::RDF::RNode
electron(ROOT::RDF::RNode df, const std::string &output_mask,
         const std::string &electron_pt, const std::string &electron_eta,
         const std::string &electron_iso, const std::string &electron_dxy,
         const std::string &electron_dz, const std::string &electron_id,
         const float &min_pt, const float &abs_max_eta, const float &max_iso,
         const float &max_dxy, const float &max_dz);

// function xyh::object_selection::muon
ROOT::RDF::RNode muon(ROOT::RDF::RNode df, const std::string &output_mask,
                      const std::string &muon_pt, const std::string &muon_eta,
                      const std::string &muon_iso, const std::string &muon_dxy,
                      const std::string &muon_dz, const std::string &muon_id,
                      const float &min_pt, const float &abs_max_eta,
                      const float &max_iso, const float &max_dxy,
                      const float &max_dz);

// function xyh::object_selection::tau
ROOT::RDF::RNode
tau(ROOT::RDF::RNode df, const std::string &output_mask,
    const std::string &tau_pt, const std::string &tau_eta,
    const std::string &tau_dz, const std::string &tau_decay_mode,
    const std::string &tau_id_vs_jet, const std::string &tau_id_vs_electron,
    const std::string &tau_id_vs_muon, const float &min_pt,
    const float &abs_max_eta, const float &max_dz,
    const std::vector<int> &decay_modes, const int &id_vs_jet_wp,
    const int &id_vs_electron_wp, const int &id_vs_muon_wp);

// function xyh::object_selection::jet (overloaded version without pileup ID)
ROOT::RDF::RNode jet(ROOT::RDF::RNode df, const std::string &output_mask,
                     const std::string &jet_pt, const std::string &jet_eta,
                     const std::string &jet_id, const float &min_pt,
                     const float &abs_max_eta, const int &id_wp,
                     const bool &apply_jet_horn_veto);

// function xyh::object_selection::jet (overloaded version with pileup ID)
ROOT::RDF::RNode jet(ROOT::RDF::RNode df, const std::string &output_mask,
                     const std::string &jet_pt, const std::string &jet_eta,
                     const std::string &jet_id, const std::string &jet_puid,
                     const float &min_pt, const float &abs_max_eta,
                     const int &id_wp, const bool &apply_jet_horn_veto,
                     const int &puid_wp, const float &puid_max_pt);

} // end namespace object_selection

} // end namespace xyh

#endif // end GUARDOBJECTSELECTION_HXX
