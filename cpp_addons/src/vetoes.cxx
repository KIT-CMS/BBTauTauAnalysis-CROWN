#ifndef GUARDVETOES_CXX
#define GUARDVETOES_CXX

#include "../include/vetoes.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "../../../../include/utility/utility.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <vector>
#include <cmath>

// namespace xyh
namespace xyh {

// namespace vetoes
namespace vetoes {

/**
 * @brief Create a veto flag mask for a di-electron system in the event.
 *
 * The selection criteria for considered electrons include kinematic, impact
 * parameter, isolation, and identification requirements. An event is vetoed if
 * at least one pair of selected electrons has a larger eta-phi separation than
 * `min_delta_r` and if the electrons have opposite charge. For events that are
 * vetoed, a value of `true` is stored in the new column, otherwise `false`. The
 * electron identification value is a integer indicating the loosest working
 * point that the electron passes (works with cut-based ID).
 *
 * @param df The input data frame.
 * @param output_mask The output mask column.
 * @param electron_pt The tranverse momentum column.
 * @param electron_eta The pseudorapidity column.
 * @param electron_phi The azimuthal angle column.
 * @param electron_iso The relative isolation column.
 * @param electron_dxy The impact parameter (xy plane) column.
 * @param electron_dz The impact parameter (z direction) column.
 * @param electron_id The identification column. The column should contain
 * interger values indicating the loosest working point that the electron
 * passes.
 * @param electron_charge The charge column.
 * @param min_pt The minimum transverse momentum for selected electrons.
 * @param abs_max_eta Maximum absolute pseudorapidity for selected electrons.
 * @param max_iso Maximum isolation value for selected electrons.
 * @param max_dxy Maximum impact parameter value (xy plane) for selected
 * electrons.
 * @param max_dz Maximum impact parameter value (z direction) for selected
 * electrons.
 * @param id_wp The working point for the electron identification.
 * @param min_delta_r The minimum eta-phi separation of two electrons.
 * @return A new data frame with the veto column.
 */
ROOT::RDF::RNode
dielectron(ROOT::RDF::RNode df, const std::string &output_mask,
           const std::string &electron_pt, const std::string &electron_eta,
           const std::string &electron_phi, const std::string &electron_iso,
           const std::string &electron_dxy, const std::string &electron_dz,
           const std::string &electron_id, const std::string &electron_charge,
           const float &min_pt, const float &abs_max_eta, const float &max_iso,
           const float &max_dxy, const float &max_dz, const int &id_wp,
           const float &min_delta_r) {
    auto select = [min_pt, abs_max_eta, max_iso, max_dxy, max_dz, id_wp,
                   min_delta_r, electron_id](
                      const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
                      const ROOT::RVec<float> &phi,
                      const ROOT::RVec<float> &iso,
                      const ROOT::RVec<float> &dxy, const ROOT::RVec<float> &dz,
                      const ROOT::RVec<UChar_t> &id_v12,
                      const ROOT::RVec<int> &charge) {
        // convert ID column to integer
        ROOT::RVec<int> id = static_cast<ROOT::RVec<int>>(id_v12);

        // debug output for selection criteria and electron observables
        Logger::get("xyh::vetoes::dielectron")
            ->debug("Create selection masks for electrons");
        Logger::get("xyh::vetoes::dielectron")
            ->debug(
                "    min_pt {}, abs_max_eta {}, max_iso {}, max_dxy {}, max_dz "
                "{}, id_wp {}, min_delta_r {}",
                min_pt, abs_max_eta, max_iso, max_dxy, max_dz, id_wp,
                min_delta_r);
        Logger::get("xyh::vetoes::dielectron")
            ->debug("    electron_id {}", electron_id);
        Logger::get("xyh::vetoes::dielectron")->debug("    pt {}", pt);
        Logger::get("xyh::vetoes::dielectron")->debug("    eta {}", eta);
        Logger::get("xyh::vetoes::dielectron")->debug("    phi {}", phi);
        Logger::get("xyh::vetoes::dielectron")->debug("    iso {}", iso);
        Logger::get("xyh::vetoes::dielectron")->debug("    dxy {}", dxy);
        Logger::get("xyh::vetoes::dielectron")->debug("    dz {}", dz);
        Logger::get("xyh::vetoes::dielectron")->debug("    id {}", id);
        Logger::get("xyh::vetoes::dielectron")->debug("    charge {}", charge);

        // create the index list of selected electron candidates
        auto object_index = ROOT::VecOps::Nonzero(
            (pt > min_pt) && (std::abs(eta) < abs_max_eta) && (iso < max_iso) &&
            (std::abs(dxy) < max_dxy) && (std::abs(dz) < max_dz) && (id >= id_wp));

        // evaluate conditions for di-electron veto
        auto has_dielectron =
            xyh::vetoes::dilepton_veto(object_index, eta, phi, charge,
                                       min_delta_r, "xyh::vetoes::dielectron");

        // debug output for the final selection mask
        Logger::get("xyh::vetoes::dielectron")
            ->debug("    veto value is {}", has_dielectron);

        return has_dielectron;
    };

    return df.Define(output_mask, select,
                     {electron_pt, electron_eta, electron_phi, electron_iso,
                      electron_dxy, electron_dz, electron_id, electron_charge});
}

/**
 * @brief Create a veto flag mask for a di-muon system in the event.
 *
 * The selection criteria for considered muons include kinematic, impact
 * parameter, isolation, and identification requirements. An event is vetoed if
 * at least one pair of selected muons has a larger eta-phi separation than
 * `min_delta_r` and if the muons have opposite charge. For events that are
 * vetoed, a value of `true` is stored in the new column, otherwise `false`. For
 * the muon identification, the flags for particle-flow candidate, global, and
 * tracker identification are combined.
 *
 * @param df The input data frame.
 * @param output_mask The output mask column.
 * @param muon_pt The tranverse momentum column.
 * @param muon_eta The pseudorapidity column.
 * @param muon_phi The azimuthal angle column.
 * @param muon_iso The relative isolation column.
 * @param muon_dxy The impact parameter (xy plane) column.
 * @param muon_dz The impact parameter (z direction) column.
 * @param muon_is_pf_cand Column with flag whether the muon is a particle-flow
 * candidate.
 * @param muon_is_tracker Column with flag whether the muon is tracker.
 * @param muon_is_global Column with flag whether the muon is global.
 * @param muon_charge The charge column.
 * @param min_pt The minimum transverse momentum for selected muons.
 * @param abs_max_eta Maximum absolute pseudorapidity for selected muons.
 * @param max_iso Maximum isolation value for selected muons.
 * @param max_dxy Maximum impact parameter value (xy plane) for selected muons.
 * @param max_dz Maximum impact parameter value (z direction) for selected
 * muons.
 * @param min_delta_r The minimum eta-phi separation of two muons.
 * @return A new data frame with the veto column.
 */
ROOT::RDF::RNode
dimuon(ROOT::RDF::RNode df, const std::string &output_mask,
       const std::string &muon_pt, const std::string &muon_eta,
       const std::string &muon_phi, const std::string &muon_iso,
       const std::string &muon_dxy, const std::string &muon_dz,
       const std::string &muon_is_pf_cand, const std::string &muon_is_tracker,
       const std::string &muon_is_global, const std::string &muon_charge,
       const float &min_pt, const float &abs_max_eta, const float &max_iso,
       const float &max_dxy, const float &max_dz, const float &min_delta_r) {
    auto select = [min_pt, abs_max_eta, max_iso, max_dxy, max_dz, min_delta_r,
                   muon_is_pf_cand, muon_is_tracker, muon_is_global](
                      const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
                      const ROOT::RVec<float> &phi,
                      const ROOT::RVec<float> &iso,
                      const ROOT::RVec<float> &dxy, const ROOT::RVec<float> &dz,
                      const ROOT::RVec<bool> &is_pf_cand,
                      const ROOT::RVec<bool> &is_tracker,
                      const ROOT::RVec<bool> &is_global,
                      const ROOT::RVec<int> &charge) {
        // debug output for selection criteria and electron observables
        Logger::get("xyh::vetoes::dimuon")
            ->debug("Create selection masks for muons");
        Logger::get("xyh::vetoes::dimuon")
            ->debug(
                "    min_pt {}, abs_max_eta {}, max_iso {}, max_dxy {}, max_dz "
                "{}, min_delta_r {}",
                min_pt, abs_max_eta, max_iso, max_dxy, max_dz, min_delta_r);
        Logger::get("xyh::vetoes::dimuon")
            ->debug("    muon_id {} && {} && {}", muon_is_pf_cand,
                    muon_is_tracker, muon_is_global);
        Logger::get("xyh::vetoes::dimuon")->debug("    pt {}", pt);
        Logger::get("xyh::vetoes::dimuon")->debug("    eta {}", eta);
        Logger::get("xyh::vetoes::dimuon")->debug("    phi {}", phi);
        Logger::get("xyh::vetoes::dimuon")->debug("    iso {}", iso);
        Logger::get("xyh::vetoes::dimuon")->debug("    dxy {}", dxy);
        Logger::get("xyh::vetoes::dimuon")->debug("    dz {}", dz);
        Logger::get("xyh::vetoes::dimuon")
            ->debug("    is_pf_cand {}", is_pf_cand);
        Logger::get("xyh::vetoes::dimuon")
            ->debug("    is_tracker {}", is_tracker);
        Logger::get("xyh::vetoes::dimuon")
            ->debug("    is_global {}", is_global);
        Logger::get("xyh::vetoes::dimuon")->debug("    charge {}", charge);

        // create the index list of selected muon candidates
        auto object_index = ROOT::VecOps::Nonzero(
            (pt > min_pt) && (std::abs(eta) < abs_max_eta) && (iso < max_iso) &&
            (std::abs(dxy) < max_dxy) && (std::abs(dz) < max_dz) &&
            (is_pf_cand && is_tracker && is_global));

        // evaluate conditions for di-muon veto
        auto has_dimuon = xyh::vetoes::dilepton_veto(
            object_index, eta, phi, charge, min_delta_r, "xyh::vetoes::dimuon");

        // debug output for the final selection mask
        Logger::get("xyh::vetoes::dimuon")
            ->debug("    veto value is {}", has_dimuon);

        return has_dimuon;
    };

    return df.Define(output_mask, select,
                     {muon_pt, muon_eta, muon_phi, muon_iso, muon_dxy, muon_dz,
                      muon_is_pf_cand, muon_is_tracker, muon_is_global,
                      muon_charge});
}

/**
 * @brief Create a veto flag for events with jets in regions, which are known to
 * produce wrong measurements. The function checks for jets which pass the base
 * selection criteria if they are in a eta-phi region with "hot" and/or "cold"
 * towers. Events with any jet in such a region are vetoed in data and
 * simulation. If the event is vetoed, a value of `true` is stored in the new
 * column, otherwise `false`. The locations are provided by a `correctionlib`
 * file and depend on the data-taking era. This procedure follows the official
 * [JME POG
 * recommendations](https://cms-jerc.web.cern.ch/Recommendations/#jet-veto-maps).
 *
 * The documentation of the `correctionlib` files for the respective eras can be
 * found here:
 * -
 * [2022preEE](https://cms-nanoaod-integration.web.cern.ch/commonJSONSFs/summaries/JME_2022_Summer22_jetvetomaps.html)
 * -
 * [2022postEE](https://cms-nanoaod-integration.web.cern.ch/commonJSONSFs/summaries/JME_2022_Summer22EE_jetvetomaps.html)
 * -
 * [2023preBPix](https://cms-nanoaod-integration.web.cern.ch/commonJSONSFs/summaries/JME_2023_Summer23_jetvetomaps.html)
 * -
 * [2023postBPix](https://cms-nanoaod-integration.web.cern.ch/commonJSONSFs/summaries/JME_2023_Summer23BPix_jetvetomaps.html)
 *
 * @param df The input data frame.
 * @param correctionManager The CorrectionManager object
 * @param output_mask The output mask column.
 * @param jet_pt The tranverse momentum column of the jets.
 * @param jet_eta The pseudorapidity column of the jets.
 * @param jet_phi The azimuthal angle column of the jets.
 * @param jet_id The jet identification bitmask column of the jets.
 * @param jet_ch_em_ef The charged electromagnetic energy fraction column of the
 * jets.
 * @param jet_n_em_ef The neutral electromagnetic energy fraction column of the
 * jets.
 * @param jet_vetomap_file The file path to the correctionlib jet veto map.
 * @param jet_vetomap_name The name of the correction to access jet veto map.
 * @param jet_vetomap_type The jet veto map type; for analyses, this name should
 * be `"jetvetomap"`.
 * @param min_pt The minimum transverse momentum for selected jets.
 * @param id_wp The working point for the jet identification.
 * @param max_em_frac The maximum charged and neutral electromagnetic energy
 * fraction for selected jets.
 *
 * @return A new data frame with the selection mask column.
 *
 * @note The veto map selection is mandatory for Run 3 analyses and can also be
 * applied to Run 2 analyses.
 */
ROOT::RDF::RNode
jet_vetomap(ROOT::RDF::RNode df,
            correctionManager::CorrectionManager &correctionManager,
            const std::string &output_mask, const std::string &jet_pt,
            const std::string &jet_eta, const std::string &jet_phi,
            const std::string &jet_id, const std::string &jet_ch_em_ef,
            const std::string &jet_n_em_ef, const std::string &jet_vetomap_file,
            const std::string &jet_vetomap_name,
            const std::string &jet_vetomap_type, const float &min_pt,
            const int &id_wp, const float &max_em_frac) {
    // In nanoAODv12 the type of jet/fatjet ID was changed to UChar_t
    // For v9 compatibility a type casting is applied
    auto [df1, jet_id_v12] =
        utility::Cast<ROOT::RVec<UChar_t>, ROOT::RVec<Int_t>>(
            df, jet_id + "_v12", "ROOT::VecOps::RVec<UChar_t>", jet_id);

    // load the veto map evaluator
    auto evaluator =
        correctionManager.loadCorrection(jet_vetomap_file, jet_vetomap_name);

    auto select = [evaluator, min_pt, id_wp, max_em_frac,
                   jet_vetomap_type](const ROOT::RVec<float> &jet_pt,
                                     const ROOT::RVec<float> &jet_eta,
                                     const ROOT::RVec<float> &jet_phi,
                                     const ROOT::RVec<UChar_t> &jet_id,
                                     const ROOT::RVec<float> &jet_ch_em_ef,
                                     const ROOT::RVec<float> &jet_n_em_ef) {
        // debug output for selection criteria and jet observables
        Logger::get("xyh::vetoes::jet_vetomap")
            ->debug("Create selection masks for jets");
        Logger::get("xyh::vetoes::jet_vetomap")
            ->debug("    min_pt {}, id_wp {}, max_em_fraction {}", min_pt,
                    id_wp, max_em_frac);
        Logger::get("xyh::vetoes::jet_vetomap")->debug("    pt {}", jet_pt);
        Logger::get("xyh::vetoes::jet_vetomap")->debug("    eta {}", jet_eta);
        Logger::get("xyh::vetoes::jet_vetomap")->debug("    phi {}", jet_phi);
        Logger::get("xyh::vetoes::jet_vetomap")->debug("    id {}", jet_id);
        Logger::get("xyh::vetoes::jet_vetomap")
            ->debug("    ch_em_ef {}", jet_ch_em_ef);
        Logger::get("xyh::vetoes::jet_vetomap")
            ->debug("    n_em_ef {}", jet_n_em_ef);

        // create the index of selected jets
        auto jet_index =
            ROOT::VecOps::Nonzero((jet_pt > min_pt) && (jet_id >= id_wp) &&
                                  ((jet_ch_em_ef + jet_n_em_ef) < max_em_frac));

        // create container with indices for vetoed jets
        auto jet_index_vetoed = ROOT::RVec<int>(0);

        for (const auto &i : jet_index) {
            // evaluate the jet veto map value
            auto jet_vetoed = evaluator->evaluate(
                {jet_vetomap_type, jet_eta.at(i), jet_phi.at(i)});

            // if the jet is vetoed, add it to the vetoed jet index
            if (jet_vetoed) {
                jet_index_vetoed.push_back(i);
            };
        }

        // check if any jet has been vetoed
        bool event_veto = false;
        if (!jet_index_vetoed.empty()) {
            event_veto = true;
        }

        // debug output for vetoes
        Logger::get("xyh::vetoes::jet_vetomap")->debug("Vetoes");
        Logger::get("xyh::vetoes::jet_vetomap")
            ->debug("    jet_index_vetoed {}", jet_index_vetoed);
        Logger::get("xyh::vetoes::jet_vetomap")
            ->debug("    event_veto {}", event_veto);

        return event_veto;
    };

    return df1.Define(
        output_mask, select,
        {jet_pt, jet_eta, jet_phi, jet_id_v12, jet_ch_em_ef, jet_n_em_ef});
}

} // end namespace vetoes

} // end namespace xyh

#endif // end GUARDVETOES_CXX
