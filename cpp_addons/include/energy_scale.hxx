#ifndef BBTAUTAU_ENERGY_SCALE_HXX
#define BBTAUTAU_ENERGY_SCALE_HXX

#include "ROOT/RDataFrame.hxx"
#include <string>
#include <vector>

namespace xyh::energy_scale {
/**
 * @brief Scale the \f$p_T\f$ of the objects of a collection by a factor per
 * region of \f$|\eta|\f$: the energy scale variations of the light leptons
 * that belong to single scopes (muons in mt and em, electrons of the et
 * embedding).
 *
 * Region i starts at `abs_eta_edges[i]` and ends below `abs_eta_edges[i + 1]`;
 * the last region has no upper edge. Objects below the first edge keep their
 * \f$p_T\f$. A factor of exactly 1 leaves the \f$p_T\f$ of its region
 * untouched: with every factor at 1, the nominal, the output column is a copy
 * of the input column.
 *
 * @param df input dataframe
 * @param outputname name of the output column with the scaled \f$p_T\f$
 * @param pt name of the collection column with the \f$p_T\f$
 * @param eta name of the collection column with the pseudorapidity
 * @param abs_eta_edges ascending lower edges of the \f$|\eta|\f$ regions
 * @param factors one factor per region
 *
 * @return a new dataframe with the scaled \f$p_T\f$ column
 *
 * @throws std::invalid_argument unless there is one positive finite factor per
 * strictly ascending edge
 */
ROOT::RDF::RNode ScalePt(ROOT::RDF::RNode df, const std::string &outputname,
                         const std::string &pt, const std::string &eta,
                         const std::vector<float> &abs_eta_edges,
                         const std::vector<float> &factors);
} // namespace xyh::energy_scale
#endif
