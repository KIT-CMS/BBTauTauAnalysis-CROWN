#ifndef GUARDHEMVETO_CXX
#define GUARDHEMVETO_CXX

#include "../include/hem_veto.hxx"
#include "../../../../include/utility/utility.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <stdexcept>
#include <string>

// namespace xyh
namespace xyh {

// namespace vetoes
namespace vetoes {

/**
 * @brief Flag of the 2018 HEM 15/16 event veto (JME recipe for UL, CMS Talk
 * 38654 and 43448; v7 spec E29, C20).
 *
 * The flag is `true` if the event has a loose jet in the region of the failed
 * HCAL endcap modules (pT > `min_pt`, identification value >= `id_wp`,
 * `min_eta` < eta < `max_eta`, `min_phi` < phi < `max_phi`; all jets, before
 * the lepton cleaning) and belongs to the affected period: in data and
 * embedding (`by_run`) the runs from `first_run` on, in simulation a fraction
 * `affected_fraction` of the events, the luminosity fraction of these runs,
 * selected deterministically by run, luminosity block and event number.
 *
 * @param df The input data frame.
 * @param output The output flag column.
 * @param jet_pt The transverse momentum column of the jets.
 * @param jet_eta The pseudorapidity column of the jets.
 * @param jet_phi The azimuthal angle column of the jets.
 * @param jet_id The identification column of the jets (6: TightLeptonVeto).
 * @param run The run number column.
 * @param lumi The luminosity block column.
 * @param event The event number column.
 * @param by_run Whether the period is given by the run number (data,
 * embedding) or by the event fraction (simulation).
 * @param min_pt The minimum jet transverse momentum.
 * @param id_wp The minimum jet identification value.
 * @param min_eta The lower edge of the region in eta.
 * @param max_eta The upper edge of the region in eta.
 * @param min_phi The lower edge of the region in phi.
 * @param max_phi The upper edge of the region in phi.
 * @param first_run The first run of the affected period.
 * @param affected_fraction The luminosity fraction of the affected period.
 * @return A new data frame with the flag column.
 */
ROOT::RDF::RNode
hem_veto(ROOT::RDF::RNode df, const std::string &output,
         const std::string &jet_pt, const std::string &jet_eta,
         const std::string &jet_phi, const std::string &jet_id,
         const std::string &run, const std::string &lumi,
         const std::string &event, const bool &by_run, const float &min_pt,
         const int &id_wp, const float &min_eta, const float &max_eta,
         const float &min_phi, const float &max_phi, const int &first_run,
         const double &affected_fraction) {
    if (affected_fraction < 0.0 || affected_fraction > 1.0) {
        throw std::invalid_argument(
            "xyh::vetoes::hem_veto: the affected fraction must be in [0, 1], "
            "got " +
            std::to_string(affected_fraction));
    }
    // the jet ID is UChar_t in NanoAOD v12+, Int_t from the correctionlib ID
    auto [df1, jet_id_v12] =
        utility::Cast<ROOT::RVec<UChar_t>, ROOT::RVec<Int_t>>(
            df, jet_id + "_hem_v12", "ROOT::VecOps::RVec<UChar_t>", jet_id);
    const unsigned int first = static_cast<unsigned int>(first_run);

    auto flag = [by_run, min_pt, id_wp, min_eta, max_eta, min_phi, max_phi,
                 first, affected_fraction](
                    const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
                    const ROOT::RVec<float> &phi,
                    const ROOT::RVec<UChar_t> &id, const UInt_t &run_number,
                    const UInt_t &lumi_block, const ULong64_t &event_number) {
        if (!hem::affected_period(by_run, run_number, lumi_block, event_number,
                                  first, affected_fraction)) {
            return false;
        }
        for (std::size_t i = 0; i < pt.size(); ++i) {
            if (hem::jet_in_region(pt.at(i), eta.at(i), phi.at(i),
                                   static_cast<int>(id.at(i)), min_pt, id_wp,
                                   min_eta, max_eta, min_phi, max_phi)) {
                return true;
            }
        }
        return false;
    };

    return df1.Define(output, flag,
                      {jet_pt, jet_eta, jet_phi, jet_id_v12, run, lumi, event});
}

} // end namespace vetoes

} // end namespace xyh

#endif // end GUARDHEMVETO_CXX
