#include "../include/tau_trigger_sf.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include <regex>
#include <stdexcept>

namespace xyh::scalefactor {
ROOT::RDF::RNode tau_trigger_per_decay_mode(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correction_manager,
    const std::string &outputname, const std::string &pt,
    const std::string &decay_mode, const std::string &trigger_flag,
    const std::string &sf_file, const std::string &sf_name,
    const std::string &trigger_name, const std::string &wp,
    const std::string &corr_type, const std::string &variation) {
    // The variation of the payload and the decay mode it is restricted to
    // (-1: every tau)
    std::string direction = variation;
    int varied_decay_mode = -1;
    static const std::regex pattern("(up|down)_dm(0|1|10|11)");
    std::smatch match;
    if (std::regex_match(variation, match, pattern)) {
        direction = match[1].str();
        varied_decay_mode = std::stoi(match[2].str());
    } else if (variation != "nom" && variation != "up" && variation != "down") {
        throw std::invalid_argument(
            "xyh::scalefactor::tau_trigger_per_decay_mode: variation '" +
            variation + "' must be nom, up, down or <up|down>_dm<0|1|10|11>");
    }
    auto evaluator = correction_manager.loadCorrection(sf_file, sf_name);
    auto sf_calculator = [evaluator, trigger_name, wp, corr_type, direction,
                          varied_decay_mode](const float &pt,
                                             const int &decay_mode,
                                             const bool &trigger_flag) {
        float sf = 1.;
        try {
            if (pt >= 0. && trigger_flag) {
                const std::string syst =
                    varied_decay_mode < 0 || decay_mode == varied_decay_mode
                        ? direction
                        : "nom";
                if (decay_mode == 0 || decay_mode == 1 || decay_mode == 10 ||
                    decay_mode == 11) {
                    sf = evaluator->evaluate(
                        {pt, decay_mode, trigger_name, wp, corr_type, syst});
                } else {
                    sf = evaluator->evaluate(
                        {pt, -1, trigger_name, wp, corr_type, syst});
                }
            }
        } catch (const std::runtime_error &e) {
            // as the core function: no scale factor where the correction has
            // none
        }
        return sf;
    };
    return df.Define(outputname, sf_calculator,
                     {pt, decay_mode, trigger_flag});
}
} // namespace xyh::scalefactor
