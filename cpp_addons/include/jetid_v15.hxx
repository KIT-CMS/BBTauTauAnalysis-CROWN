#ifndef GUARDJETIDV15_HXX
#define GUARDJETIDV15_HXX

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <string>

// namespace xyh
namespace xyh {

// namespace object_selection
namespace object_selection {

// clang-format off
//
// Pinned formula constants: reconstructed 2018 UL AK4 PUPPI TIGHT jet ID
// ------------------------------------------------------------------------
// NanoAOD v15 drops the precomputed `Jet_jetId` branch that NanoAODv9
// shipped. The v15 `Jet` collection is AK4 PUPPI (JEC payload AK4PFPuppi),
// not the AK4 CHS collection the old bitmask was computed for, so this
// analysis recomputes the *tight* working point (CMSSW enum
// `RUN2ULPUPPI`/`TIGHT`) event-by-event from the per-jet composition
// branches that v15 does ship.
//
// The formula, its region structure, boundary-inclusive conventions, and
// primary/cross-check sources are pinned in
// `docs/jetid_2018UL_puppi_v15.md`; the machine-readable boundary fixture
// is `tests/fixtures/jetid_2018UL_puppi_tight_v1.json`. Do NOT change any
// value below without bumping `formula_version` and updating both the doc
// and the fixture together.
//
// @note These constants are for the 2017/2018 UL PUPPI **tight** working
// point only -- NOT tightLepVeto, NOT 2016 UL (`RUN2UL16PUPPI`), and NOT
// AK4 CHS (`RUN2ULCHS`).
// @note Jets with |eta| > 2.7 are outside the region structure encoded
// here (the primary source continues into "EC"/"FW" regions above 2.7,
// but those are out of scope for this analysis: production b-jet/probe
// acceptance ends at |eta| < 2.4 anyway).
// `tight_jet_id_2018_puppi_v15` returns a mask entry of 0 (fail) for any
// jet with |eta| > eta_transition_max.
// clang-format on

// Version tag for the pinned formula; must equal
// tests/fixtures/jetid_2018UL_puppi_tight_v1.json's "formula_version".
constexpr const char *formula_version = "jetid_2018UL_puppi_tight_v1";

// Region boundaries. Both upper edges are inclusive; the central region has
// no lower edge, the transition region's lower edge (2.6) is exclusive.
constexpr float eta_central_max = 2.6f;    // |eta| <= 2.6      -> central region
constexpr float eta_transition_max = 2.7f; // 2.6 < |eta| <= 2.7 -> transition region

// Central region (|eta| <= 2.6) cuts -- all strict inequalities.
constexpr float central_neHEF_max = 0.9f;
constexpr float central_neEmEF_max = 0.9f;
constexpr int central_nConstituents_min = 1;  // nConstituents > 1
constexpr float central_chHEF_min = 0.0f;     // chHEF > 0
constexpr int central_chMultiplicity_min = 0; // chMultiplicity > 0

// Transition region (2.6 < |eta| <= 2.7) cuts -- all strict inequalities.
constexpr float transition_neHEF_max = 0.9f;
constexpr float transition_neEmEF_max = 0.99f;

/**
 * @brief Recompute the pinned 2018 UL AK4 PUPPI tight jet ID
 * (`jetid_2018UL_puppi_tight_v1`) from NanoAOD v15 per-jet composition
 * branches, and store the result as a per-jet `int` mask column (1 = pass,
 * 0 = fail).
 *
 * See the constants block above and `docs/jetid_2018UL_puppi_v15.md` for
 * the pinned criteria table, sources, and boundary conventions.
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
 * for a future tightLepVeto extension of this producer (see the doc).
 * @param jet_chEmEF The jet charged electromagnetic energy fraction column.
 * Not used by the *tight* working point computed here; kept as an input for
 * a future tightLepVeto extension of this producer (see the doc).
 * @param jet_chMultiplicity The jet charged-particle multiplicity column.
 * @param jet_neMultiplicity The jet neutral-particle multiplicity column.
 * Not used by the *tight* working point in the region structure encoded
 * here (only relevant for the |eta| > 3.0 forward region, which is out of
 * scope for this analysis); kept as an input for a possible future
 * extension of this producer into that region.
 * @return A new data frame with the selection mask column.
 */
ROOT::RDF::RNode tight_jet_id_2018_puppi_v15(
    ROOT::RDF::RNode df, const std::string &outputmask,
    const std::string &jet_eta, const std::string &jet_neHEF,
    const std::string &jet_neEmEF, const std::string &jet_nConstituents,
    const std::string &jet_chHEF, const std::string &jet_muEF,
    const std::string &jet_chEmEF, const std::string &jet_chMultiplicity,
    const std::string &jet_neMultiplicity);

} // end namespace object_selection

} // end namespace xyh

#endif // end GUARDJETIDV15_HXX
