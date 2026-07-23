#ifndef GUARDBTAGSFSTRICT_HXX
#define GUARDBTAGSFSTRICT_HXX

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <string>
#include <vector>

// The full correctionManager::CorrectionManager definition is pulled in by the
// .cxx (and is always present in generated CROWN code, where the core includes
// precede the addon headers). A forward declaration is enough for the function
// signatures here and avoids dragging correctionlib's correction.h into every
// translation unit that only needs the declarations.
namespace correctionManager {
class CorrectionManager;
} // namespace correctionManager

// namespace xyh
namespace xyh {

// namespace scalefactor
namespace scalefactor {

// namespace btagging_strict
namespace btagging_strict {

// clang-format off
//
// Strict fixed-multiple-working-point UParTAK4 b-tag EVENT reweighting
// --------------------------------------------------------------------
// This is the STRICT counterpart of the core algorithm
// physicsobject::jet::scalefactor::BtaggingMultipleWP (CROWN core
// src/jets.cxx). It implements the BTV fixed-WP event-reweighting method
// (https://btv-wiki.docs.cern.ch/PerformanceCalibration/fixedWPSFRecommendations/)
// with the SAME per-jet algebra, but it NEVER substitutes a silent 1.0 for a
// degenerate jet contribution. Where the core clamps a non-positive
// denominator or a non-positive jet contribution to 1.0 (core
// src/jets.cxx:2155-2172), this consumer throws std::runtime_error carrying
// the offending jet's pt / eta / flavor / score, so a broken efficiency
// payload becomes a loud build/run failure rather than a subtle physics bug.
//
// Per-jet method (jet selected by `jet_mask`; jets are expected to already be
// inside the b-tag acceptance, |eta| < 2.4 and pt > 20, cleaned of lepton
// overlaps -- the consumer enforces the eta support explicitly):
//   * Find the tightest working point the jet passes among the five fixed
//     UParTAK4 WPs, ordered tightest -> loosest {XXT, XT, T, M, L}, using the
//     score thresholds in `wp_values` (same tightest->loosest order).
//   * Let eff(WP) be the MC tagging efficiency and SF(WP) the data/MC scale
//     factor for the jet flavor at that WP.
//   * The jet's tag category and its per-jet contribution jet_w = P_data/P_MC:
//       - passes the tightest WP (XXT): P_MC = eff(XXT),
//         P_data = SF(XXT)*eff(XXT)         => jet_w = SF(XXT).
//       - passes WP `low` but not the next tighter WP `high`:
//         P_MC   = eff(low) - eff(high),
//         P_data = SF(low)*eff(low) - SF(high)*eff(high)
//                                            => jet_w = P_data / P_MC.
//       - fails even the loosest WP (L): P_MC = 1 - eff(L),
//         P_data = 1 - SF(L)*eff(L)         => jet_w = P_data / P_MC.
//   * The event weight is the product of jet_w over all selected jets, i.e.
//         weight = P_data(event) / P_MC(event)
//                = prod_j P_data(j) / prod_j P_MC(j).
//
// Per-correction variation dispatch: b/c jets (flavor 5/4) evaluate the
// `UParTAK4_comb` correction with `variation_comb`; light jets (flavor 0)
// evaluate `UParTAK4_light` with `variation_light`. The caller is expected to
// pass "central" on the side that does not carry a requested systematic
// component (a comb-only component keeps light central, and vice versa).
//
// STRICT throw conditions (each std::runtime_error message contains the jet
// pt / eta / flavor / score):
//   * jet |eta| outside [0, 2.4) (the abseta support of the pinned payload,
//     whose abseta binning uses flow=error at 2.4);
//   * an efficiency that is non-finite, <= 0, or > 1;
//   * a non-monotonic efficiency pair (looser WP must have STRICTLY larger
//     efficiency than the tighter WP, i.e. the P_MC bin probability > 0);
//   * a jet flavor that is not one of {0, 4, 5};
//   * a jet contribution that is non-finite or <= 0;
//   * any correctionlib evaluation failure (e.g. an unknown variation key for
//     the correction the jet is dispatched to) -- rethrown with kinematics.
//
// The UParTAK4 SF correction names, the efficiency correction name, and the
// five WP names are pinned constants of this consumer (the interface only
// carries the payload FILES, the efficiency sample-type category value, and
// the two per-flavor variation keys).
// clang-format on

// Fixed UParTAK4 working-point names, ordered tightest -> loosest. The
// `wp_values` argument of multi_wp_event_weight MUST be given in this exact
// order (as produced by btag_payloads.load_upart_wps on the Python side).
// clang-format off
static const std::vector<std::string> kWorkingPointsTightToLoose = {
    "XXT", "XT", "T", "M", "L"};
// clang-format on

// Correction-set names inside the pinned UParTAK4 SF payload.
static const char *kCombCorrection = "UParTAK4_comb";   // b/c jets (flavor 5/4)
static const char *kLightCorrection = "UParTAK4_light"; // light jets (flavor 0)

// Correction-set name inside the b-tag efficiency payload.
static const char *kEfficiencyCorrection = "btag_efficiency";

/**
 * @brief Strict fixed-multi-WP UParTAK4 b-tag event reweighting.
 *
 * See the block comment above for the algorithm and the exhaustive list of
 * throw conditions. Contrast with the core
 * physicsobject::jet::scalefactor::BtaggingMultipleWP, which silently
 * substitutes 1.0 for degenerate jet contributions.
 *
 * @param df input dataframe
 * @param correction_manager correction manager that loads (once) the SF and
 *     efficiency payloads
 * @param output name of the output event-weight column
 * @param jet_pt name of the per-jet transverse-momentum column
 * @param jet_eta name of the per-jet pseudorapidity column
 * @param jet_flavor name of the per-jet hadron-flavor column (0 / 4 / 5)
 * @param jet_score name of the per-jet UParTAK4 b-tag score column
 * @param jet_mask name of the per-jet selection mask column; only jets with a
 *     non-zero mask entry contribute (they are expected to already sit inside
 *     the b-tag acceptance)
 * @param sf_file path to the UParTAK4 scale-factor payload
 * @param eff_file path to the b-tag efficiency payload
 * @param eff_sample_type value of the efficiency payload's `sample_type`
 *     category for this sample
 * @param variation_comb systematic key evaluated for b/c jets on UParTAK4_comb
 * @param variation_light systematic key evaluated for light jets on
 *     UParTAK4_light
 * @param wp_values the five WP score thresholds, ordered tightest -> loosest
 *     to match kWorkingPointsTightToLoose
 * @return a new dataframe carrying the event-weight column
 */
ROOT::RDF::RNode multi_wp_event_weight(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correction_manager,
    const std::string &output, const std::string &jet_pt,
    const std::string &jet_eta, const std::string &jet_flavor,
    const std::string &jet_score, const std::string &jet_mask,
    const std::string &sf_file, const std::string &eff_file,
    const std::string &eff_sample_type, const std::string &variation_comb,
    const std::string &variation_light, const std::vector<float> &wp_values);

/**
 * @brief Diagnostic: per-event count of selected jets whose pt exceeds the
 * efficiency-payload pt-flow clamp threshold.
 *
 * The efficiency payload clamps pt above its top bin edge (flow=clamp), so a
 * jet with pt above the threshold is reweighted with the top-bin efficiency.
 * This diagnostic column records how many selected jets are affected, so the
 * clamping stays observable in the produced ntuple rather than silent.
 *
 * @param df input dataframe
 * @param output name of the output (unsigned) count column
 * @param jet_pt name of the per-jet transverse-momentum column
 * @param jet_mask name of the per-jet selection mask column
 * @param pt_clamp_threshold pt value above which the efficiency lookup clamps
 * @return a new dataframe carrying the count column
 */
ROOT::RDF::RNode pt_clamped_njets(ROOT::RDF::RNode df, const std::string &output,
                                  const std::string &jet_pt,
                                  const std::string &jet_mask,
                                  const float pt_clamp_threshold);

} // end namespace btagging_strict

} // end namespace scalefactor

} // end namespace xyh

#endif // end GUARDBTAGSFSTRICT_HXX
