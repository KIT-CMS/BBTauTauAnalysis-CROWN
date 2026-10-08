#ifndef GUARDOBJECTSELECTION_CXX
#define GUARDOBJECTSELECTION_CXX

#include "../include/object_selection.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "../../../../include/utility/utility.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <vector>

// namespace xyh
namespace xyh {

// namespace object_selection
namespace object_selection {

/**
 * @brief Create a selection mask for electrons.
 *
 * The selection criteria include kinematic, impact parameter, isolation, and
 * identification requirements. The function creates a new column with a boolean
 * value for each electron, indicating whether it passes the selection criteria.
 * The electron identification value is a boolean for the respective working
 * point (works with MVA-based ID).
 *
 * @param df The input data frame.
 * @param output_mask The output mask column.
 * @param electron_pt The tranverse momentum column.
 * @param electron_eta The pseudorapidity column.
 * @param electron_iso The relative isolation column.
 * @param electron_dxy The impact parameter (xy plane) column.
 * @param electron_dz The impact parameter (z direction) column.
 * @param electron_id The identification column. The column should contain flags
 * whether the electron passes or fails the identification at the considered
 * working point.
 * @param min_pt The minimum transverse momentum for selected electrons.
 * @param abs_max_eta Maximum absolute pseudorapidity for selected electrons.
 * @param max_iso Maximum isolation value for selected electrons.
 * @param max_dxy Maximum impact parameter value (xy plane) for selected
 * electrons.
 * @param max_dz Maximum impact parameter value (z direction) for selected
 * electrons.
 * @return A new data frame with the selection mask column.
 */
ROOT::RDF::RNode
electron(ROOT::RDF::RNode df, const std::string &output_mask,
         const std::string &electron_pt, const std::string &electron_eta,
         const std::string &electron_iso, const std::string &electron_dxy,
         const std::string &electron_dz, const std::string &electron_id,
         const float &min_pt, const float &abs_max_eta, const float &max_iso,
         const float &max_dxy, const float &max_dz) {
    auto select = [min_pt, abs_max_eta, max_iso, max_dxy, max_dz, electron_id](
                      const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
                      const ROOT::RVec<float> &iso,
                      const ROOT::RVec<float> &dxy, const ROOT::RVec<float> &dz,
                      const ROOT::RVec<bool> &id) {
        // debug output for selection criteria and electron observables
        Logger::get("xyh::object_selection::electron")
            ->debug("Create selection masks for electrons");
        Logger::get("xyh::object_selection::electron")
            ->debug("    min_pt {}, abs_max_eta {}, max_iso {}, max_dxy {}, "
                    "max_dz {}",
                    min_pt, abs_max_eta, max_iso, max_dxy, max_dz);
        Logger::get("xyh::object_selection::electron")
            ->debug("    electron_id {}", electron_id);
        Logger::get("xyh::object_selection::electron")->debug("    pt {}", pt);
        Logger::get("xyh::object_selection::electron")
            ->debug("    eta {}", eta);
        Logger::get("xyh::object_selection::electron")
            ->debug("    iso {}", iso);
        Logger::get("xyh::object_selection::electron")
            ->debug("    dxy {}", dxy);
        Logger::get("xyh::object_selection::electron")->debug("    dz {}", dz);
        Logger::get("xyh::object_selection::electron")->debug("    id {}", id);

        // create the selection mask
        auto mask =
            ((pt > min_pt) && (ROOT::VecOps::abs(eta) < abs_max_eta) && (iso < max_iso) &&
             (ROOT::VecOps::abs(dxy) < max_dxy) && (abs(dz) < max_dz) && (id));

        // debug output for the final selection mask
        Logger::get("xyh::object_selection::electron")
            ->debug("    selection mask {}", mask);

        return mask;
    };

    return df.Define(output_mask, select,
                     {electron_pt, electron_eta, electron_iso, electron_dxy,
                      electron_dz, electron_id});
}

/**
 * @brief Create a selection mask for muons.
 *
 * The selection criteria include kinematic, impact parameter, isolation, and
 * identification requirements. The function creates a new column with a boolean
 * value for each muon, indicating whether it passes the selection criteria. The
 * muon identification value is a boolean for the respective working point.
 *
 * @param df The input data frame.
 * @param output_mask The output mask column.
 * @param muon_pt The tranverse momentum column.
 * @param muon_eta The pseudorapidity column.
 * @param muon_iso The relative isolation column.
 * @param muon_dxy The impact parameter (xy plane) column.
 * @param muon_dz The impact parameter (z direction) column.
 * @param muon_id The identification column. The column should contain flags
 * whether the muon passes or fails the identification at the considered working
 * point.
 * @param min_pt The minimum transverse momentum for selected muons.
 * @param abs_max_eta Maximum absolute pseudorapidity for selected muons.
 * @param max_iso Maximum isolation value for selected muons.
 * @param max_dxy Maximum impact parameter value (xy plane) for selected muons.
 * @param max_dz Maximum impact parameter value (z direction) for selected
 * muons.
 * @return A new data frame with the selection mask column.
 */
ROOT::RDF::RNode muon(ROOT::RDF::RNode df, const std::string &output_mask,
                      const std::string &muon_pt, const std::string &muon_eta,
                      const std::string &muon_iso, const std::string &muon_dxy,
                      const std::string &muon_dz, const std::string &muon_id,
                      const float &min_pt, const float &abs_max_eta,
                      const float &max_iso, const float &max_dxy,
                      const float &max_dz) {
    auto select = [min_pt, abs_max_eta, max_iso, max_dxy, max_dz, muon_id](
                      const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
                      const ROOT::RVec<float> &iso,
                      const ROOT::RVec<float> &dxy, const ROOT::RVec<float> &dz,
                      const ROOT::RVec<bool> &id) {
        // debug output for selection criteria and muon observables
        Logger::get("xyh::object_selection::muon")
            ->debug("Create selection masks for muons");
        Logger::get("xyh::object_selection::muon")
            ->debug("    min_pt {}, abs_max_eta {}, max_iso {}, max_dxy {}, "
                    "max_dz {}",
                    min_pt, abs_max_eta, max_iso, max_dxy, max_dz, muon_id);
        Logger::get("xyh::object_selection::muon")
            ->debug("    muon_id {}", muon_id);
        Logger::get("xyh::object_selection::muon")->debug("    pt {}", pt);
        Logger::get("xyh::object_selection::muon")->debug("    eta {}", eta);
        Logger::get("xyh::object_selection::muon")->debug("    iso {}", iso);
        Logger::get("xyh::object_selection::muon")->debug("    dxy {}", dxy);
        Logger::get("xyh::object_selection::muon")->debug("    dz {}", dz);
        Logger::get("xyh::object_selection::muon")->debug("    id {}", id);

        // create the selection mask
        auto mask =
            ((pt > min_pt) && (ROOT::VecOps::abs(eta) < abs_max_eta) && (iso < max_iso) &&
             (ROOT::VecOps::abs(dxy) < max_dxy) && (ROOT::VecOps::abs(dz) < max_dz) && (id));

        // debug output for the final selection mask
        Logger::get("xyh::object_selection::muon")
            ->debug("    selection mask {}", mask);

        return mask;
    };

    return df.Define(output_mask, select,
                     {muon_pt, muon_eta, muon_iso, muon_dxy, muon_dz, muon_id});
}

/**
 * @brief Create a selection mask for tight taus, based on various criteria.
 *
 * The selection criteria include kinematic, impact parameter, isolation, and
 * identification requirements. The function creates a new column with a boolean
 * value for each tau, indicating whether it passes the selection criteria. The
 * three identification variables for the taus are integers, indicating the
 * loosest working point that the tau passes.
 *
 * @param df The input data frame.
 * @param output_mask The output mask column.
 * @param tau_pt The taus' tranverse momenta.
 * @param tau_eta The taus' pseudorapidities.
 * @param tau_dz The taus' impact parameter values (z direction).
 * @param tau_decay_mode The taus' decay mode flags.
 * @param tau_id_vs_electron The tau vs electrons discriminators' flags. The
 * column should contain integers for the loosest working point that the tau
 * passes.
 * @param tau_id_vs_muon The tau vs muons discriminators' flags. The column
 * should contain integers for the loosest working point that the tau passes.
 * @param tau_id_vs_jet The tau vs jets discriminators' flags. The column should
 * contain integers for the loosest working point that the tau passes.
 * @param min_pt Minimum transverse momentum for the taus.
 * @param abs_max_eta Maximum absolute pseudorapidity for the taus.
 * @param decay_modes Tau decay mode flags.
 * @param max_dz Maximum impact parameter value (z direction) for the taus.
 * @param id_vs_electron_wp The working point for the tau vs electrons
 * identification.
 * @param id_vs_muon_wp The working point for the tau vs muons identification.
 * @param id_vs_jet_wp The working point for the tau vs jets identification.
 */
ROOT::RDF::RNode
tau(ROOT::RDF::RNode df, const std::string &output_mask,
    const std::string &tau_pt, const std::string &tau_eta,
    const std::string &tau_dz, const std::string &tau_decay_mode,
    const std::string &tau_id_vs_jet, const std::string &tau_id_vs_electron,
    const std::string &tau_id_vs_muon, const float &min_pt,
    const float &abs_max_eta, const float &max_dz,
    const std::vector<int> &decay_modes, const int &id_vs_jet_wp,
    const int &id_vs_electron_wp, const int &id_vs_muon_wp) {
    auto select = [min_pt, abs_max_eta, decay_modes, max_dz, id_vs_electron_wp,
                   id_vs_muon_wp, id_vs_jet_wp, tau_id_vs_jet,
                   tau_id_vs_electron, tau_id_vs_muon](
                      const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
                      const ROOT::RVec<float> &dz,
                      const ROOT::RVec<UChar_t> &decay_mode_v12,
                      const ROOT::RVec<UChar_t> &id_vs_jet,
                      const ROOT::RVec<UChar_t> &id_vs_electron,
                      const ROOT::RVec<UChar_t> &id_vs_muon) {
        // convert decay mode column to integer
        ROOT::RVec<int> decay_mode =
            static_cast<ROOT::RVec<int>>(decay_mode_v12);

        // debug output for selection criteria and tau observables
        Logger::get("xyh::object_selection::tau")
            ->debug("Create selection masks for hadronic taus");
        // Logger::get("xyh::object_selection::tau")->debug("    min_pt {},
        // abs_max_eta {}, decay_modes {}, max_dz {}, id_vs_jet_wp {},
        // id_vs_electron_wp {}, id_vs_muon_wp {}", min_pt, abs_max_eta,
        // decay_modes, max_dz, id_vs_jet_wp, id_vs_electron_wp, id_vs_muon_wp);
        Logger::get("xyh::object_selection::tau")
            ->debug("    tau_id_vs_jet {}, tau_id_vs_electron {}, "
                    "tau_id_vs_muon {}",
                    tau_id_vs_jet, tau_id_vs_electron, tau_id_vs_muon);
        Logger::get("xyh::object_selection::tau")->debug("    pt {}", pt);
        Logger::get("xyh::object_selection::tau")->debug("    eta {}", eta);
        Logger::get("xyh::object_selection::tau")->debug("    dz {}", dz);
        Logger::get("xyh::object_selection::tau")
            ->debug("    decay_mode {}", decay_mode);
        Logger::get("xyh::object_selection::tau")
            ->debug("    id_vs_jet {}", id_vs_jet);
        Logger::get("xyh::object_selection::tau")
            ->debug("    id_vs_electron {}", id_vs_electron);
        Logger::get("xyh::object_selection::tau")
            ->debug("    id_vs_muon {}", id_vs_muon);

        // construct a decay mode mask
        auto decay_mode_mask =
            ROOT::VecOps::RVec<bool>(decay_mode.size(), false);
        for (const auto &mode : decay_modes) {
            decay_mode_mask |= (decay_mode == mode);
        }

        // create the selection mask
        auto mask =
            ((pt > min_pt) && (ROOT::VecOps::abs(eta) < abs_max_eta) && (ROOT::VecOps::abs(dz) < max_dz) &&
             decay_mode_mask && (id_vs_jet >= id_vs_jet_wp) &&
             (id_vs_electron >= id_vs_electron_wp) &&
             (id_vs_muon >= id_vs_muon_wp));

        // debug output for the final selection mask
        Logger::get("xyh::object_selection::tau")
            ->debug("    selection mask {}", mask);

        return mask;
    };

    return df.Define(output_mask, select,
                     {tau_pt, tau_eta, tau_dz, tau_decay_mode, tau_id_vs_jet,
                      tau_id_vs_electron, tau_id_vs_muon});
}

/**
 * @brief Create a selection mask for jets, based on various criteria, without
 * pileup ID.
 *
 * The selection criteria include kinematic and identification requirements.
 * The function creates a new column with a boolean value for each jet,
 * indicating whether it passes the selection criteria. The identification
 * variable for the jets is a bitmask. Bit 0 corresponds to a jet that passes
 * the loose jet ID. Bit 1 corresponds to a jet that passes the tight jet ID.
 * Bit 2 corresponds to a jet that passes the tight jet ID and the tight lepton
 * veto.
 *
 * @param df The input data frame.
 * @param output_mask The output mask column.
 * @param jet_pt The tranverse momentum column.
 * @param jet_eta The pseudorapidity column.
 * @param jet_id The jet identification bitmask column.
 * @param min_pt The minimum transverse momentum for selected jets.
 * @param abs_max_eta The maximum absolute pseudorapidity for selected jets.
 * @param id_wp The working point for the jet identification.
 * @param apply_jet_horn_veto Whether to apply the jet horn veto.
 * @return A new data frame with the selection mask column.
 *
 * @note The function does not apply pileup ID, as it is not present for PFPuppi
 * jets. If it should be applied, use the overloaded function with pileup ID.
 *
 * @note The jet horn veto removes jets in the pseudorapidity range \(2.5 <
 * |\eta| < 3.0\) with a transverse momentum \(p_T < 50\) GeV.
 */
ROOT::RDF::RNode jet(ROOT::RDF::RNode df, const std::string &output_mask,
                     const std::string &jet_pt, const std::string &jet_eta,
                     const std::string &jet_id, const float &min_pt,
                     const float &abs_max_eta, const int &id_wp,
                     const bool &apply_jet_horn_veto) {
    // In nanoAODv12 the type of jet/fatjet ID was changed to UChar_t
    // For v9 compatibility a type casting is applied
    auto [df1, jet_id_v12] =
        utility::Cast<ROOT::RVec<UChar_t>, ROOT::RVec<Int_t>>(
            df, jet_id + "_v12", "ROOT::VecOps::RVec<UChar_t>", jet_id);

    auto select = [min_pt, abs_max_eta, id_wp, apply_jet_horn_veto](
                      const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
                      const ROOT::RVec<UChar_t> &id) {
        // debug output for selection criteria and jet observables
        Logger::get("xyh::object_selection::jet")
            ->debug("Create selection masks for jets");
        Logger::get("xyh::object_selection::jet")
            ->debug("    min_pt {}, abs_max_eta {}, id_wp {}", min_pt,
                    abs_max_eta, id_wp);
        Logger::get("xyh::object_selection::jet")->debug("    pt {}", pt);
        Logger::get("xyh::object_selection::jet")->debug("    eta {}", eta);
        Logger::get("xyh::object_selection::jet")->debug("    id {}", id);

        // create the selection mask
        auto mask = xyh::object_selection::select_jet(
            pt, eta, id, min_pt, abs_max_eta, id_wp, apply_jet_horn_veto);

        // debug output for the final selection mask
        Logger::get("xyh::object_selection::jet")
            ->debug("    selection mask {}", mask);

        return mask;
    };

    return df1.Define(output_mask, select, {jet_pt, jet_eta, jet_id_v12});
}

/**
 * @brief Create a selection mask for jets, based on various criteria, with
 * pileup ID.
 *
 * The selection criteria include kinematic and identification requirements.
 * The function creates a new column with a boolean value for each jet,
 * indicating whether it passes the selection criteria. The identification
 * variable for the jets is a bitmask. Bit 0 corresponds to a jet that passes
 * the loose jet ID. Bit 1 corresponds to a jet that passes the tight jet ID.
 * Bit 2 corresponds to a jet that passes the tight jet ID and the tight lepton
 * veto.
 *
 * @param df The input data frame.
 * @param output_mask The output mask column.
 * @param jet_pt The tranverse momentum column.
 * @param jet_eta The pseudorapidity column.
 * @param jet_id The jet identification bitmask column.
 * @param min_pt The minimum transverse momentum for selected jets.
 * @param abs_max_eta The maximum absolute pseudorapidity for selected jets.
 * @param id_wp The working point for the jet identification.
 * @param apply_jet_horn_veto Whether to apply the jet horn veto.
 * @param puid_wp The working point for the jet pileup identification.
 * @param puid_max_pt The maximum transverse momentum for the pileup
 * identification.
 * @return A new data frame with the selection mask column.
 *
 * @note The function applies pileup ID.
 *       If it should not be applied, use the overloaded function with pileup
 * ID.
 *
 * @note The jet horn veto removes jets in the pseudorapidity range \(2.5 <
 * |\eta| < 3.0\) with a transverse momentum \(p_T < 50\) GeV.
 */
ROOT::RDF::RNode jet(ROOT::RDF::RNode df, const std::string &output_mask,
                     const std::string &jet_pt, const std::string &jet_eta,
                     const std::string &jet_id, const std::string &jet_puid,
                     const float &min_pt, const float &abs_max_eta,
                     const int &id_wp, const bool &apply_jet_horn_veto,
                     const int &puid_wp, const float &puid_max_pt) {
    // In nanoAODv12 the type of jet/fatjet ID was changed to UChar_t
    // For v9 compatibility a type casting is applied
    auto [df1, jet_id_v12] =
        utility::Cast<ROOT::RVec<UChar_t>, ROOT::RVec<Int_t>>(
            df, jet_id + "_v12", "ROOT::VecOps::RVec<UChar_t>", jet_id);

    auto select = [min_pt, abs_max_eta, id_wp, puid_wp, puid_max_pt,
                   apply_jet_horn_veto](const ROOT::RVec<float> &pt,
                                        const ROOT::RVec<float> &eta,
                                        const ROOT::RVec<UChar_t> &id,
                                        const ROOT::RVec<UChar_t> &puid) {
        // debug output for selection criteria and jet observables
        Logger::get("xyh::object_selection::jet")
            ->debug("Create selection masks for jets");
        Logger::get("xyh::object_selection::jet")
            ->debug("    min_pt {}, abs_max_eta {}, id_wp {}, puid_wp {}, "
                    "puid_max_pt {}",
                    min_pt, abs_max_eta, id_wp, puid_wp, puid_max_pt);
        Logger::get("xyh::object_selection::jet")->debug("    pt {}", pt);
        Logger::get("xyh::object_selection::jet")->debug("    eta {}", eta);
        Logger::get("xyh::object_selection::jet")->debug("    id {}", id);
        Logger::get("xyh::object_selection::jet")->debug("    puid {}", puid);

        // create the selection mask
        auto mask = xyh::object_selection::select_jet(
            pt, eta, id, puid, min_pt, abs_max_eta, id_wp, apply_jet_horn_veto,
            puid_wp, puid_max_pt);

        // debug output for the final selection mask
        Logger::get("xyh::object_selection::jet")
            ->debug("    selection mask {}", mask);

        return mask;
    };

    return df1.Define(output_mask, select,
                      {jet_pt, jet_eta, jet_id_v12, jet_puid});
}

} // end namespace object_selection

} // end namespace xyh

#endif // end GUARDOBJECTSELECTION_CXX
