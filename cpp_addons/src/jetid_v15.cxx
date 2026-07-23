#ifndef GUARDJETIDV15_CXX
#define GUARDJETIDV15_CXX

#include "../include/jetid_v15.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <cmath>
#include <cstddef>

// namespace xyh
namespace xyh {

// namespace object_selection
namespace object_selection {

/**
 * @brief Recompute the pinned 2018 UL AK4 PUPPI tight jet ID
 * (`jetid_2018UL_puppi_tight_v1`) from NanoAOD v15 per-jet composition
 * branches.
 *
 * NanoAOD v15 drops the precomputed `Jet_jetId` bitmask that NanoAODv9
 * shipped, and the v15 `Jet` collection is AK4 PUPPI rather than the AK4 CHS
 * collection that bitmask was computed for. This function recomputes the
 * *tight* working point (CMSSW `RUN2ULPUPPI`/`TIGHT`) directly from the
 * per-jet composition branches, per the region-split criteria pinned in
 * `docs/jetid_2018UL_puppi_v15.md`:
 *  - |eta| <= 2.6 (central): `chHEF > 0`, `chMultiplicity > 0`,
 *    `nConstituents > 1`, `neEmEF < 0.9`, `neHEF < 0.9`.
 *  - 2.6 < |eta| <= 2.7 (transition): `neHEF < 0.9`, `neEmEF < 0.99`.
 *  - |eta| > 2.7: outside the region structure pinned in the doc (the
 *    primary source continues into "EC"/"FW" regions above 2.7, but they
 *    are out of scope for this analysis, whose b-jet/probe acceptance ends
 *    at |eta| < 2.4). The mask entry for such jets is 0 (fail).
 *
 * All cuts above are strict inequalities; a value exactly at a threshold
 * fails that cut (see the doc's "Region boundary convention" and
 * "cut_convention" sections).
 *
 * @param df The input data frame.
 * @param outputmask The output mask column.
 * @param jet_eta The jet pseudorapidity column.
 * @param jet_neHEF The jet neutral hadron energy fraction column.
 * @param jet_neEmEF The jet neutral electromagnetic energy fraction column.
 * @param jet_nConstituents The jet number-of-constituents column.
 * @param jet_chHEF The jet charged hadron energy fraction column.
 * @param jet_muEF The jet muon energy fraction column. Not used by the
 * *tight* (non-lepton-veto) working point computed here; kept as an input
 * for a future tightLepVeto extension of this producer.
 * @param jet_chEmEF The jet charged electromagnetic energy fraction column.
 * Not used by the *tight* working point computed here; kept as an input for
 * a future tightLepVeto extension of this producer.
 * @param jet_chMultiplicity The jet charged-particle multiplicity column.
 * @param jet_neMultiplicity The jet neutral-particle multiplicity column.
 * Not used by the *tight* working point in the region structure encoded
 * here; kept as an input for a possible future extension of this producer
 * into the |eta| > 3.0 forward region.
 * @return A new data frame with the selection mask column.
 */
ROOT::RDF::RNode tight_jet_id_2018_puppi_v15(
    ROOT::RDF::RNode df, const std::string &outputmask,
    const std::string &jet_eta, const std::string &jet_neHEF,
    const std::string &jet_neEmEF, const std::string &jet_nConstituents,
    const std::string &jet_chHEF, const std::string &jet_muEF,
    const std::string &jet_chEmEF, const std::string &jet_chMultiplicity,
    const std::string &jet_neMultiplicity) {
    auto compute_mask = [](const ROOT::RVec<float> &eta,
                           const ROOT::RVec<float> &neHEF,
                           const ROOT::RVec<float> &neEmEF,
                           const ROOT::RVec<UChar_t> &nConstituents,
                           const ROOT::RVec<float> &chHEF,
                           const ROOT::RVec<float> &muEF,
                           const ROOT::RVec<float> &chEmEF,
                           const ROOT::RVec<UChar_t> &chMultiplicity,
                           const ROOT::RVec<UChar_t> &neMultiplicity) {
        // muEF, chEmEF, and neMultiplicity are accepted for a future
        // tightLepVeto / forward-region extension of this producer (see
        // docs/jetid_2018UL_puppi_v15.md) but play no role in the *tight*
        // (non-lepton-veto) working point computed here.
        (void)muEF;
        (void)chEmEF;
        (void)neMultiplicity;

        // debug output for selection criteria and jet observables
        Logger::get("xyh::object_selection::tight_jet_id_2018_puppi_v15")
            ->debug("Recomputing 2018UL PUPPI tight jet ID ({})",
                    formula_version);
        Logger::get("xyh::object_selection::tight_jet_id_2018_puppi_v15")
            ->debug("    eta {}", eta);
        Logger::get("xyh::object_selection::tight_jet_id_2018_puppi_v15")
            ->debug("    neHEF {}", neHEF);
        Logger::get("xyh::object_selection::tight_jet_id_2018_puppi_v15")
            ->debug("    neEmEF {}", neEmEF);
        Logger::get("xyh::object_selection::tight_jet_id_2018_puppi_v15")
            ->debug("    nConstituents {}", nConstituents);
        Logger::get("xyh::object_selection::tight_jet_id_2018_puppi_v15")
            ->debug("    chHEF {}", chHEF);
        Logger::get("xyh::object_selection::tight_jet_id_2018_puppi_v15")
            ->debug("    chMultiplicity {}", chMultiplicity);

        size_t nJets = eta.size();
        ROOT::RVec<int> mask(nJets, 0);
        for (size_t i = 0; i < nJets; ++i) {
            float abs_eta = std::abs(eta.at(i));
            bool pass = false;

            if (abs_eta <= eta_central_max) {
                // central region: |eta| <= 2.6
                pass = (chHEF.at(i) > central_chHEF_min) &&
                       (static_cast<int>(chMultiplicity.at(i)) >
                        central_chMultiplicity_min) &&
                       (static_cast<int>(nConstituents.at(i)) >
                        central_nConstituents_min) &&
                       (neEmEF.at(i) < central_neEmEF_max) &&
                       (neHEF.at(i) < central_neHEF_max);
            } else if (abs_eta <= eta_transition_max) {
                // transition region: 2.6 < |eta| <= 2.7
                pass = (neHEF.at(i) < transition_neHEF_max) &&
                       (neEmEF.at(i) < transition_neEmEF_max);
            } else {
                // |eta| > 2.7: outside the region structure pinned in
                // docs/jetid_2018UL_puppi_v15.md; not the production
                // acceptance (|eta| < 2.4) for this analysis. The mask
                // entry is 0 (fail) by convention -- see the fixture's
                // "eta_beyond_2p7_unsupported_fails_by_convention" case
                // (expected_pass=null, i.e. out of scope, not validated).
                pass = false;
            }

            mask[i] = pass ? 1 : 0;
        }

        // debug output for the final selection mask
        Logger::get("xyh::object_selection::tight_jet_id_2018_puppi_v15")
            ->debug("    selection mask {}", mask);

        return mask;
    };

    return df.Define(outputmask, compute_mask,
                     {jet_eta, jet_neHEF, jet_neEmEF, jet_nConstituents,
                      jet_chHEF, jet_muEF, jet_chEmEF, jet_chMultiplicity,
                      jet_neMultiplicity});
}

} // end namespace object_selection

} // end namespace xyh

#endif // end GUARDJETIDV15_CXX
