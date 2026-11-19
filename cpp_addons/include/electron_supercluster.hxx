#ifndef GUARDELECTRONSUPERCLUSTER_HXX
#define GUARDELECTRONSUPERCLUSTER_HXX

#include "../../../../include/defaults.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <stdexcept>
#include <string>

// namespace xyh
namespace xyh {

// namespace electron
namespace electron {

/**
 * @brief Supercluster pseudorapidity of the electron at `position` of the pair,
 * eta + deltaEtaSC.
 *
 * The EGM electron ID and reconstruction scale factors are binned in the
 * supercluster eta (v7 spec K7, C22), whose bin edges at 1.444 and 1.566 the
 * electron eta can miss. An index outside the collection gives the default
 * float, like event::quantity::Get.
 *
 * @param df The input data frame.
 * @param output The output column.
 * @param eta The electron pseudorapidity column.
 * @param delta_eta_sc The column of the supercluster eta minus the electron
 * eta (Electron_deltaEtaSC).
 * @param pair The column of the pair indices.
 * @param position The position of the electron in the pair.
 * @return A new data frame with the supercluster eta column.
 */
inline ROOT::RDF::RNode
supercluster_eta(ROOT::RDF::RNode df, const std::string &output,
                 const std::string &eta, const std::string &delta_eta_sc,
                 const std::string &pair, const int &position) {
    return df.Define(
        output,
        [position](const ROOT::RVec<float> &electron_eta,
                   const ROOT::RVec<float> &electron_delta_eta_sc,
                   const ROOT::RVec<int> &indices) {
            try {
                const int index = indices.at(position);
                return electron_eta.at(index) +
                       electron_delta_eta_sc.at(index);
            } catch (const std::out_of_range &) {
                return default_value<float>();
            }
        },
        {eta, delta_eta_sc, pair});
}

} // end namespace electron

} // end namespace xyh

#endif // end GUARDELECTRONSUPERCLUSTER_HXX
