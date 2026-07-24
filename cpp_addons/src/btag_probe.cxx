#ifndef GUARDBTAGPROBE_CXX
#define GUARDBTAGPROBE_CXX

#include "../include/btag_probe.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "Math/Vector4D.h"
#include "Math/VectorUtil.h"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <cmath>
#include <cstddef>

// namespace xyh
namespace xyh {

// namespace btag_probe
namespace btag_probe {

/**
 * @brief Build the per-jet probe mask for the payload-independent b-tag
 * efficiency-measurement ntuple.
 *
 * A jet passes if its corrected pt is at least @p min_pt, its |eta| is below
 * @p max_abs_eta, the reconstructed tight jet-ID mask entry is nonzero, and
 * its deltaR against BOTH selected pair legs is at least @p min_delta_r. No
 * b-tag discriminator cut and no b-tag scale factor is applied. The mask is
 * built from the base jet collection, independently of the analysis b-jet
 * selection (see btag_probe.hxx).
 *
 * The pt cut is boundary-inclusive (``>=``), the |eta| cut is
 * boundary-exclusive (``<``), and the deltaR cut is boundary-inclusive
 * (``>=``).
 *
 * @param df The input data frame.
 * @param output The output per-jet mask column.
 * @param jet_pt The (nominal) corrected jet pt column.
 * @param jet_eta The jet pseudorapidity column.
 * @param jet_phi The jet azimuth column.
 * @param jet_id_mask The reconstructed tight jet-ID mask column.
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
                            const float max_abs_eta, const float min_delta_r) {
    auto compute_mask =
        [min_pt, max_abs_eta, min_delta_r](
            const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
            const ROOT::RVec<float> &phi, const ROOT::RVec<int> &id_mask,
            const ROOT::Math::PtEtaPhiMVector &leg1,
            const ROOT::Math::PtEtaPhiMVector &leg2) {
        // debug output for selection criteria and jet observables
        Logger::get("xyh::btag_probe::probe_mask")
            ->debug("Building probe-jet mask (min_pt {}, max_abs_eta {}, "
                    "min_delta_r {})",
                    min_pt, max_abs_eta, min_delta_r);
        Logger::get("xyh::btag_probe::probe_mask")->debug("    pt {}", pt);
        Logger::get("xyh::btag_probe::probe_mask")->debug("    eta {}", eta);
        Logger::get("xyh::btag_probe::probe_mask")
            ->debug("    jet ID mask {}", id_mask);

        const std::size_t nJets = pt.size();
        ROOT::RVec<int> mask(nJets, 0);
        for (std::size_t i = 0; i < nJets; ++i) {
            const ROOT::Math::PtEtaPhiMVector jet(pt.at(i), eta.at(i),
                                                  phi.at(i), 0.f);
            const bool pass =
                (pt.at(i) >= min_pt) &&
                (std::abs(eta.at(i)) < max_abs_eta) &&
                (id_mask.at(i) != 0) &&
                (ROOT::Math::VectorUtil::DeltaR(jet, leg1) >= min_delta_r) &&
                (ROOT::Math::VectorUtil::DeltaR(jet, leg2) >= min_delta_r);
            mask[i] = pass ? 1 : 0;
        }

        // debug output for the final selection mask
        Logger::get("xyh::btag_probe::probe_mask")
            ->debug("    probe mask {}", mask);

        return mask;
    };

    return df.Define(output, compute_mask,
                     {jet_pt, jet_eta, jet_phi, jet_id_mask, pair_p4_1,
                      pair_p4_2});
}

} // end namespace btag_probe

} // end namespace xyh

#endif // end GUARDBTAGPROBE_CXX
