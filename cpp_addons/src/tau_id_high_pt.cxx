#include "../include/tau_id_high_pt.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include <cmath>
#include <stdexcept>

namespace xyh::scalefactor {
const std::vector<std::string> &tau_id_vsjet_pt_binned_components() {
    static const std::vector<std::string> components{
        "stat_highpT_bin1", "stat_highpT_bin2", "syst_highpT",
        "syst_highpT_extrap"};
    return components;
}

ROOT::RDF::RNode tau_id_vsjet_pt_binned(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correction_manager,
    const std::string &outputname, const std::string &pt,
    const std::string &decay_mode, const std::string &gen_match,
    const std::string &sf_file, const std::string &sf_name,
    const std::string &id_vsjet_wp, const std::string &id_vse_wp,
    const std::string &member) {
    if (member != "nom" && member != "up" && member != "down") {
        throw std::invalid_argument(
            "xyh::scalefactor::tau_id_vsjet_pt_binned: member '" + member +
            "' must be nom, up or down");
    }
    auto evaluator = correction_manager.loadCorrection(sf_file, sf_name);
    const std::vector<std::string> expected{"pt", "dm",   "genmatch", "wp",
                                            "wp_VSe", "syst", "flag"};
    std::vector<std::string> inputs;
    for (const auto &input : evaluator->inputs()) {
        inputs.push_back(input.name());
    }
    if (inputs != expected) {
        throw std::invalid_argument(
            "xyh::scalefactor::tau_id_vsjet_pt_binned: " + sf_name + " of " +
            sf_file +
            " does not take the inputs pt, dm, genmatch, wp, wp_VSe, syst, "
            "flag");
    }
    const std::string flag = "pt";
    const auto components = tau_id_vsjet_pt_binned_components();
    auto sf_calculator = [evaluator, id_vsjet_wp, id_vse_wp, member, flag,
                          components](const float &pt, const int &decay_mode,
                                      const int &gen_match) {
        double sf = 1.;
        if (decay_mode != 0 && decay_mode != 1 && decay_mode != 10 &&
            decay_mode != 11) {
            return sf;
        }
        auto evaluate = [&](const std::string &syst) {
            return evaluator->evaluate({pt, decay_mode, gen_match, id_vsjet_wp,
                                        id_vse_wp, syst, flag});
        };
        sf = evaluate("nom");
        if (member == "nom") {
            return sf;
        }
        double sum = 0.;
        for (const auto &component : components) {
            const double difference = evaluate(component + "_" + member) - sf;
            sum += difference * difference;
        }
        return member == "up" ? sf + std::sqrt(sum) : sf - std::sqrt(sum);
    };
    return df.Define(outputname, sf_calculator, {pt, decay_mode, gen_match});
}
} // namespace xyh::scalefactor
