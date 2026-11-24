#ifndef BBTAUTAU_TAU_TRIGGER_SF_HXX
#define BBTAUTAU_TAU_TRIGGER_SF_HXX

#include "ROOT/RDataFrame.hxx"
#include <string>

namespace correctionManager {
class CorrectionManager;
}

namespace xyh::scalefactor {
/**
 * @brief Scale factor of a tau trigger leg with variations per decay mode.
 *
 * The evaluation is that of `physicsobject::tau::scalefactor::Trigger` with a
 * trigger flag: 1 without the flag or for a negative \f$p_T\f$, else the
 * correction at the \f$p_T\f$ and decay mode of the tau (decay modes other
 * than 0, 1, 10 and 11 as -1), and 1 if the correction throws. The payload
 * takes the decay mode but has one up and one down variation, so the
 * variation of one decay mode is formed here: `<up|down>_dm<DM>` evaluates the
 * taus of decay mode DM (0, 1, 10 or 11) with the variation and every other
 * tau with "nom". "nom", "up" and "down" are passed on for every tau.
 *
 * @param df input dataframe
 * @param correction_manager correction manager that loads the scale factor
 * file
 * @param outputname name of the output column with the scale factor
 * @param pt name of the column with the tau \f$p_T\f$
 * @param decay_mode name of the column with the tau decay mode
 * @param trigger_flag name of the column with the trigger flag
 * @param sf_file path to the file with the tau scale factors
 * @param sf_name name of the correction in the file
 * @param trigger_name name of the trigger, e.g. "ditau"
 * @param wp working point of the vsJet ID
 * @param corr_type "sf", "eff_data" or "eff_mc"
 * @param variation "nom", "up", "down" or `<up|down>_dm<DM>`
 *
 * @return a new dataframe with the scale factor column
 *
 * @throws std::invalid_argument for a variation of another form
 */
ROOT::RDF::RNode tau_trigger_per_decay_mode(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correction_manager,
    const std::string &outputname, const std::string &pt,
    const std::string &decay_mode, const std::string &trigger_flag,
    const std::string &sf_file, const std::string &sf_name,
    const std::string &trigger_name, const std::string &wp,
    const std::string &corr_type, const std::string &variation);
} // namespace xyh::scalefactor
#endif
