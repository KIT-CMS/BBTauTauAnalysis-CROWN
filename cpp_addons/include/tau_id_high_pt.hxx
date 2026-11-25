#ifndef BBTAUTAU_TAU_ID_HIGH_PT_HXX
#define BBTAUTAU_TAU_ID_HIGH_PT_HXX

#include "ROOT/RDataFrame.hxx"
#include <string>
#include <vector>

namespace correctionManager {
class CorrectionManager;
}

namespace xyh::scalefactor {
/// The uncertainty components of the pT-binned DeepTau vsJet scale factor in
/// the TAU payload (syst keys `<component>_up`, `<component>_down`).
const std::vector<std::string> &tau_id_vsjet_pt_binned_components();

/**
 * @brief The DeepTau vsJet scale factor of the pT-binned set of the TAU
 * payload (flag "pt"), which the TAU POG recommends for hadronic taus above
 * 140 GeV, and its total uncertainty (v8 spec C40, V35).
 *
 * The correction is evaluated like the DM-binned one of
 * `physicsobject::tau::scalefactor::experimental::Id_vsJet`: at (pt, decay
 * mode, gen match, vsJet WP, vsEle WP, syst, "pt"), and 1 for a decay mode
 * other than 0, 1, 10 and 11 (an empty leg). The payload returns 1 for
 * everything but genuine hadronic taus (gen match 5) and, with this flag, the
 * value of its lowest bin (140 to 200 GeV) for every pT below 140 GeV: the
 * column is defined at every pT but is the recommended scale factor above
 * 140 GeV only.
 *
 * `member` selects the value:
 *  - "nom": the nominal scale factor (syst "nom");
 *  - "up", "down": nom +- the quadrature sum of the differences to nom of
 *    every component of `tau_id_vsjet_pt_binned_components()` in that
 *    direction: the statistical uncertainties of the two pT bins, the
 *    systematic uncertainty and the uncertainty of the extrapolation to
 *    higher pT. The payload's own syst "up"/"down" is the same sum without the
 *    extrapolation component.
 *
 * @param df input dataframe
 * @param correction_manager correction manager that loads the scale factor
 * file
 * @param outputname name of the output column with the scale factor
 * @param pt name of the column with the tau \f$p_T\f$
 * @param decay_mode name of the column with the tau decay mode
 * @param gen_match name of the column with the generator match of the tau
 * @param sf_file path to the file with the tau scale factors
 * @param sf_name name of the vsJet correction in the file
 * @param id_vsjet_wp working point of the vsJet ID
 * @param id_vse_wp working point of the vsEle ID
 * @param member "nom", "up" or "down"
 *
 * @return a new dataframe with the scale factor column
 *
 * @throws std::invalid_argument for another member, or if the correction does
 * not take the seven inputs pt, dm, genmatch, wp, wp_VSe, syst, flag
 */
ROOT::RDF::RNode tau_id_vsjet_pt_binned(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correction_manager,
    const std::string &outputname, const std::string &pt,
    const std::string &decay_mode, const std::string &gen_match,
    const std::string &sf_file, const std::string &sf_name,
    const std::string &id_vsjet_wp, const std::string &id_vse_wp,
    const std::string &member);
} // namespace xyh::scalefactor
#endif
