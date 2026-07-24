#ifndef GUARDBTAGPROBE_HXX
#define GUARDBTAGPROBE_HXX

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <cstddef>
#include <string>

// namespace xyh
namespace xyh {

// namespace btag_probe
namespace btag_probe {

// clang-format off
//
// Payload-independent UParT probe-jet collection.
// ------------------------------------------------------------------------
// The b-tag efficiency-measurement ntuple profile
// (``sm_btag_efficiency_config``) does not run the analysis b-jet selection
// or apply any b-tag scale factor. Instead it exports a *probe* jet
// collection selected purely on kinematics + reconstructed jet ID, from
// which the b-tag efficiency (per hadron flavour, per UParTAK4 working
// point) is measured downstream in TauFakeFactors -- one row per probe jet,
// with NO discriminator cut applied here (the denominator must be the full
// jet population, not the b-tagged subset, otherwise the 20-30 GeV region is
// biased by the analysis b-jet pt threshold).
//
// The probe mask is built from the base jet collection (corrected pt, jet
// eta, and the reconstructed tight jet-ID mask), NOT from the analysis
// b-jet-selected mask, so it is independent of the analysis b-jet
// acceptance. The four exported per-probe-jet vectors (corrected pt, eta,
// hadron flavour, UParTAK4 B score) share this one mask, so they are equal
// in length by construction.
// clang-format on

/**
 * @brief Build the per-jet probe mask (1 = probe, 0 = not a probe) for the
 * payload-independent b-tag efficiency-measurement ntuple.
 *
 * A jet is a probe if ALL of the following hold:
 *  - corrected pt >= @p min_pt;
 *  - |eta| < @p max_abs_eta;
 *  - the reconstructed tight jet-ID mask entry is nonzero (pass);
 *  - deltaR >= @p min_delta_r against BOTH selected pair legs
 *    (@p pair_p4_1 and @p pair_p4_2).
 *
 * No b-tag discriminator cut and no b-tag scale factor is applied -- the
 * probe collection is deliberately independent of the analysis b-jet
 * collection (see the file-level note).
 *
 * @param df The input data frame.
 * @param output The output per-jet mask column (RVec<int>, 1 = probe).
 * @param jet_pt The (nominal) corrected jet pt column (RVec<float>).
 * @param jet_eta The jet pseudorapidity column (RVec<float>).
 * @param jet_phi The jet azimuth column (RVec<float>), used for deltaR.
 * @param jet_id_mask The reconstructed tight jet-ID mask column (RVec<int>).
 * @param pair_p4_1 The first selected pair leg four-vector column.
 * @param pair_p4_2 The second selected pair leg four-vector column.
 * @param min_pt The minimum corrected pt (inclusive).
 * @param max_abs_eta The maximum |eta| (exclusive).
 * @param min_delta_r The minimum deltaR against each pair leg (inclusive).
 * @return A new data frame with the probe mask column.
 */
ROOT::RDF::RNode probe_mask(ROOT::RDF::RNode df, const std::string &output,
                            const std::string &jet_pt,
                            const std::string &jet_eta,
                            const std::string &jet_phi,
                            const std::string &jet_id_mask,
                            const std::string &pair_p4_1,
                            const std::string &pair_p4_2, const float min_pt,
                            const float max_abs_eta, const float min_delta_r);

/**
 * @brief Write the elements of an input per-jet vector selected by a mask to
 * a new (shorter) output vector, in input order.
 *
 * The output length equals the number of nonzero mask entries. Applying the
 * same @p mask to several input columns yields equal-length outputs by
 * construction, which is how the four probe-jet vectors stay aligned.
 *
 * @tparam TOut The element type of the output vector.
 * @tparam TIn The element type of the input column (defaults to @p TOut).
 * Each kept element is ``static_cast<TOut>``. The distinct-type form is used
 * for the hadron-flavour vector, whose NanoAOD v15 branch is stored as
 * ``UChar_t`` but is exported as ``int``.
 *
 * @param df The input data frame.
 * @param output The output (masked) vector column.
 * @param input_column The input per-jet vector column.
 * @param mask The per-jet mask column (RVec<int>, nonzero = keep).
 * @return A new data frame with the masked output vector column.
 */
template <typename TOut, typename TIn = TOut>
ROOT::RDF::RNode masked_vector(ROOT::RDF::RNode df, const std::string &output,
                               const std::string &input_column,
                               const std::string &mask) {
    auto select = [](const ROOT::RVec<TIn> &values,
                     const ROOT::RVec<int> &jet_mask) {
        ROOT::RVec<TOut> selected;
        const std::size_t n = values.size();
        selected.reserve(n);
        for (std::size_t i = 0; i < n; ++i) {
            if (i < jet_mask.size() && jet_mask[i] != 0) {
                selected.push_back(static_cast<TOut>(values[i]));
            }
        }
        return selected;
    };
    return df.Define(output, select, {input_column, mask});
}

} // end namespace btag_probe

} // end namespace xyh

#endif // end GUARDBTAGPROBE_HXX
