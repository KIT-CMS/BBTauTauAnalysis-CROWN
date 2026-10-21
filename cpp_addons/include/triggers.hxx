#ifndef GUARD_TRIGGERSEXT_H
#define GUARD_TRIGGERSEXT_H

#include "../../../../include/utility/utility.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <Math/Vector3D.h>
#include <Math/Vector4D.h>
#include <Math/VectorUtil.h>
#include <string>
#include <vector>

namespace trigger {

ROOT::RDF::RNode GenerateTriggerFlag(ROOT::RDF::RNode df,
                                     const std::string &triggerflag_name,
                                     const std::string &hltpath);

/**
 * @brief Quantity of the trigger object matched to a particle: among the
 * trigger objects with the given ID that carry all given filter bits and lie
 * within `max_delta_r` of the particle, the one nearest in \f$\Delta R\f$ wins
 * (the \f$\Delta R\f$ of the core `trigger::matchParticle`); its value of
 * `quantity` is written, `-1` if there is no such object.
 *
 * Used for the tau leg of the mu-tau monitoring paths in the tau-ID
 * measurement, e.g. `TrigObj_pt`, `TrigObj_l1pt` (`Float_t`) and
 * `TrigObj_l1iso` (`Int_t`).
 *
 * As in the core flags, the trigger object IDs are read as `UShort_t` and the
 * filter bits as `ULong64_t` (the NanoAOD v15 types; v9 columns are cast).
 *
 * @tparam T element type of the `quantity` column and type of the output
 * @param df input dataframe
 * @param outputname name of the output column
 * @param particle name of the column of the particle's Lorentz vector
 * @param triggerobject_eta name of the column of the trigger object
 * \f$\eta\f$ values
 * @param triggerobject_phi name of the column of the trigger object
 * \f$\phi\f$ values
 * @param triggerobject_id name of the column of the trigger object IDs
 * @param triggerobject_filterbit name of the column of the trigger object
 * filter bits
 * @param quantity name of the trigger-object column whose value is written
 * @param particle_id trigger object ID to match (e.g. 15 for taus)
 * @param bits filter bit positions that must all be set (0-63)
 * @param max_delta_r maximum \f$\Delta R\f$ between particle and trigger
 * object
 *
 * @return a dataframe with the new column
 */
template <typename T>
ROOT::RDF::RNode
MatchedObjectQuantity(ROOT::RDF::RNode df, const std::string &outputname,
                      const std::string &particle,
                      const std::string &triggerobject_eta,
                      const std::string &triggerobject_phi,
                      const std::string &triggerobject_id,
                      const std::string &triggerobject_filterbit,
                      const std::string &quantity, const int &particle_id,
                      const std::vector<int> &bits, const float &max_delta_r) {
    for (int bit : bits) {
        if (bit < 0 || bit > 63) {
            throw std::invalid_argument(
                "trigger::MatchedObjectQuantity: filter bit " +
                std::to_string(bit) + " outside 0-63 for " + outputname);
        }
    }
    auto [df1, id_column] =
        utility::Cast<ROOT::RVec<UShort_t>, ROOT::RVec<Int_t>>(
            df, triggerobject_id + "_v12", "ROOT::VecOps::RVec<UShort_t>",
            triggerobject_id);
    auto [df2, filterbit_column] =
        utility::Cast<ROOT::RVec<ULong64_t>, ROOT::RVec<Int_t>>(
            df1, triggerobject_filterbit + "_v15",
            "ROOT::VecOps::RVec<ULong64_t>", triggerobject_filterbit);
    ULong64_t mask = 0;
    for (int bit : bits) {
        mask |= (ULong64_t(1) << bit);
    }
    auto nearest = [particle_id, mask,
                    max_delta_r](const ROOT::Math::PtEtaPhiMVector &p4,
                                 const ROOT::RVec<float> &etas,
                                 const ROOT::RVec<float> &phis,
                                 const ROOT::RVec<UShort_t> &ids,
                                 const ROOT::RVec<ULong64_t> &filterbits,
                                 const ROOT::RVec<T> &values) {
        T result = T(-1);
        float best = max_delta_r;
        for (std::size_t i = 0; i < etas.size(); ++i) {
            if (int(ids[i]) != particle_id || (filterbits[i] & mask) != mask) {
                continue;
            }
            const auto object =
                ROOT::Math::RhoEtaPhiVectorF(0, etas[i], phis[i]);
            const float delta_r = ROOT::Math::VectorUtil::DeltaR(object, p4);
            if (delta_r < best) {
                best = delta_r;
                result = values[i];
            }
        }
        return result;
    };
    return df2.Define(outputname, nearest,
                      {particle, triggerobject_eta, triggerobject_phi,
                       id_column, filterbit_column, quantity});
}

} // namespace trigger

#endif // end GUARD_TRIGGERSEXT_H
