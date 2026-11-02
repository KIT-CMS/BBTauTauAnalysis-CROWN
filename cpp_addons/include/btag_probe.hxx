#ifndef GUARDBTAGPROBE_HXX
#define GUARDBTAGPROBE_HXX

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <string>
#include <type_traits>

// namespace xyh
namespace xyh {

// namespace btag_probe
namespace btag_probe {

// clang-format off
//
// Payload-independent UParT probe-jet collection.
// ------------------------------------------------------------------------
// The b-tag efficiency-measurement ntuple profile
// (``sm_btag_efficiency_config``) exports a *probe* jet collection with NO
// b-tag discriminator cut and NO b-tag scale factor applied, from which the
// b-tag efficiency (per hadron flavour, per UParTAK4 working point) is
// measured downstream in TauFakeFactors -- one row per probe jet.
//
// The probe mask itself is assembled on the Python side out of the existing
// core building blocks (``physicsobject::CombineMasks`` of the base b-jet mask
// and the lepton-overlap veto mask); this header only holds the helper that
// applies that mask to the exported per-probe-jet vectors. All exported
// vectors share the one mask, so they are equal in length by construction.
// clang-format on

/**
 * @brief Keep the elements of a per-jet vector selected by a mask, in input
 * order.
 *
 * The output length equals the number of nonzero mask entries, so applying the
 * same @p mask to several input columns yields aligned, equal-length outputs.
 *
 * @tparam TOut element type of the output vector
 * @tparam TIn element type of the input column (defaults to @p TOut); the
 *     distinct-type form is used for the hadron-flavour vector, whose NanoAOD
 *     v15 branch is stored as ``UChar_t`` but which is exported as ``int``
 *
 * @param df input dataframe
 * @param output name of the output (masked) vector column
 * @param input_column name of the input per-jet vector column
 * @param mask name of the per-jet mask column (nonzero = keep)
 * @return a new dataframe carrying the masked output vector column
 */
template <typename TOut, typename TIn = TOut>
ROOT::RDF::RNode masked_vector(ROOT::RDF::RNode df, const std::string &output,
                               const std::string &input_column,
                               const std::string &mask) {
    auto select = [](const ROOT::RVec<TIn> &values,
                     const ROOT::RVec<int> &jet_mask) {
        if constexpr (std::is_same_v<TOut, TIn>) {
            return values[jet_mask != 0];
        } else {
            return ROOT::VecOps::Map(
                values[jet_mask != 0],
                [](const TIn &value) { return static_cast<TOut>(value); });
        }
    };
    return df.Define(output, select, {input_column, mask});
}

} // end namespace btag_probe

} // end namespace xyh

#endif // end GUARDBTAGPROBE_HXX
