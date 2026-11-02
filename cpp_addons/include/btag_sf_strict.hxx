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
//   * Find the tightest working point the jet passes among the configured
//     UParTAK4 WPs `working_points`, ordered tightest -> loosest (v7: {T, M},
//     spec E14/C14), using the score thresholds read from the SF payload's
//     `UParTAK4_wp_values` correction (the same way the core
//     BtaggingMultipleWP does), so the thresholds can never drift from the
//     payload they belong to.
//   * Let eff(WP) be the MC tagging efficiency and SF(WP) the data/MC scale
//     factor for the jet flavor at that WP.
//   * The jet's tag category and its per-jet contribution jet_w = P_data/P_MC:
//       - passes the tightest WP: P_MC = eff(tightest),
//         P_data = SF(tightest)*eff(tightest)  => jet_w = SF(tightest).
//       - passes WP `low` but not the next tighter WP `high`:
//         P_MC   = eff(low) - eff(high),
//         P_data = SF(low)*eff(low) - SF(high)*eff(high)
//                                            => jet_w = P_data / P_MC;
//         if P_data < 0, jet_w = 1 (BTV fixedWP recommendation, "set these
//         intermediate factors to unity"; v7 spec K1), and the jet is counted
//         in the `unity_count_output` column.
//       - fails even the loosest WP: P_MC = 1 - eff(loosest),
//         P_data = 1 - SF(loosest)*eff(loosest)  => jet_w = P_data / P_MC.
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
// b/c jets below `bc_min_pt`, the lowest calibrated pT of `UParTAK4_comb`,
// take the SF at that pT with twice its deviation from central for the
// variations (BTV convention, CMSSW BTagCalibrationReader::eval_auto_bounds);
// the payload's pT flow would return the highest bin. Their efficiencies stay
// at the jet pT.
//
// STRICT throw conditions (all but the first two carry the offending jet's
// pt / eta / flavor / score in the std::runtime_error message):
//   * an empty or repeated working-point list (checked at Define time);
//   * `UParTAK4_wp_values` thresholds that are non-finite or not strictly
//     decreasing over the configured WP names, or a WP name the payload does
//     not have (checked once, at Define time);
//   * jet |eta| outside [0, 2.4) (the abseta support of the pinned payload,
//     whose abseta binning uses flow=error at 2.4);
//   * an efficiency that is non-finite, <= 0, or > 1;
//   * a non-monotonic efficiency pair (looser WP must have STRICTLY larger
//     efficiency than the tighter WP, i.e. the P_MC bin probability > 0);
//   * a jet flavor that is not one of {0, 4, 5};
//   * a jet contribution that is non-finite or <= 0 (except the negative
//     intermediate numerator above, which gives 1);
//   * any correctionlib evaluation failure (e.g. an unknown variation key for
//     the correction the jet is dispatched to) -- rethrown with kinematics.
//
// The UParTAK4 SF correction names and the efficiency correction name are
// pinned constants of this consumer (the interface carries the payload FILES,
// the efficiency sample-type category value, the working points and the two
// per-flavor variation keys).
// clang-format on

// Correction-set names inside the pinned UParTAK4 SF payload.
static const char *kCombCorrection = "UParTAK4_comb";   // b/c jets (flavor 5/4)
static const char *kLightCorrection = "UParTAK4_light"; // light jets (flavor 0)
static const char *kWpValuesCorrection = "UParTAK4_wp_values"; // WP thresholds

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
 * @param unity_count_output name of the output column counting the jets whose
 *     intermediate factor is set to 1 for a negative numerator (K1)
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
 * @param bc_min_pt lowest calibrated pT of the b/c-jet SFs
 * @param working_points UParTAK4 working-point names, tightest first; their
 *     score thresholds are read from the SF payload and must decrease strictly
 * @param variation_comb systematic key evaluated for b/c jets on UParTAK4_comb
 * @param variation_light systematic key evaluated for light jets on
 *     UParTAK4_light
 * @return a new dataframe carrying the event-weight and the count columns
 */
ROOT::RDF::RNode multi_wp_event_weight(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correction_manager,
    const std::string &output, const std::string &unity_count_output,
    const std::string &jet_pt, const std::string &jet_eta,
    const std::string &jet_flavor, const std::string &jet_score,
    const std::string &jet_mask, const std::string &sf_file,
    const std::string &eff_file, const std::string &eff_sample_type,
    const float &bc_min_pt, const std::vector<std::string> &working_points,
    const std::string &variation_comb, const std::string &variation_light);

} // end namespace btagging_strict

} // end namespace scalefactor

} // end namespace xyh

#endif // end GUARDBTAGSFSTRICT_HXX
