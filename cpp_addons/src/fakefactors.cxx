#include "../../../../include/utility/CorrectionManager.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "ROOT/RDataFrame.hxx"
#include "correction.h"
#include <sstream>
#include <spdlog/fmt/ranges.h>


namespace fakefactors {

ROOT::RDF::RNode
BuildFloatVector(ROOT::RDF::RNode df, const std::string &output,
                 const std::vector<std::string> &input_columns) {

    // Set name of the logger for debug messages
    auto logger_name = "fakefactors::BuildFloatVector";
    Logger::get(logger_name)
        ->debug("Building input vector from columns {}",
                fmt::join(input_columns, ", "));

    // Build the expression to create a vector of variants with the input
    // columns, casting all to double for correctionlib evaluation
    std::string expression = "std::vector<float>{";
    for (size_t i = 0; i < input_columns.size(); ++i) {
        expression += "static_cast<float>(" + input_columns[i] + ")";
        if (i + 1 < input_columns.size()) {
            expression += ", ";
        }
    }
    expression += "}";

    // Debug message to show the JIT expression being defined for the column
    Logger::get(logger_name)
        ->debug("Define column with expression {}", expression);

    return df.Define(output, expression);
}

// ----------------------------------------------------------------------------
// Utility functions for correctionlib input vector creation, manipulation, and
// inspection
// ----------------------------------------------------------------------------

namespace util {

std::vector<correction::Variable::Type>
to_clib_input(const std::vector<float> &vector) {
    // Copy vector of doubles to expected correctionlib input
    return std::vector<correction::Variable::Type>(vector.begin(),
                                                   vector.end());
}

void prepend(std::vector<correction::Variable::Type> &vector,
             const correction::Variable::Type &value) {
    // Prepend a value to a correctionlib input vector
    vector.insert(vector.begin(), value);
}

void append(std::vector<correction::Variable::Type> &vector,
            const correction::Variable::Type &value) {
    // Append a value to a correctionlib input vector
    vector.insert(vector.end(), value);
}

const std::vector<correction::Variable::Type>
prepare_ff_input(const std::vector<float> &vector,
                 const std::string &variation) {
    // Convert vector of doubles to vector of correction::Variable::Type and
    // append the systematic variation
    auto input = to_clib_input(vector);
    append(input, variation);
    return input;
}

const std::vector<correction::Variable::Type>
prepare_fractions_input(const std::vector<float> &vector,
                        const std::string &process,
                        const std::string &variation) {
    // Convert vector of doubles to vector of correction::Variable::Type,
    // add process type, and append the systematic variation
    auto input = to_clib_input(vector);
    prepend(input, process);
    append(input, variation);
    return input;
}

std::string join(const std::vector<correction::Variable::Type> &vector) {
    // Join all elements of a correctionlib input vector to a string
    std::ostringstream os;
    bool first = true;
    for (const auto &v : vector) {
        if (!first)
            os << ", ";
        first = false;
        std::visit([&os](auto &&x) { os << x; }, v);
    }
    return os.str();
}

} // end namespace util

namespace xyh {

// ----------------------------------------------------------------------------
// Fake factor evaluation in the semileptonic channels
// ----------------------------------------------------------------------------

ROOT::RDF::RNode RawFakeFactorSemileptonic(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correctionManager,
    const std::string &outputname, const std::string &qcd_inputs,
    const std::string &tt_inputs, const std::string &fraction_inputs,
    const std::string &ff_file, const std::string &ff_qcd_name,
    const std::string &ff_tt_name, const std::string &ff_fraction_name,
    const std::string &ff_qcd_variation, const std::string &ff_tt_variation,
    const std::string &ff_fraction_variation) {
    // Define logger name and print general debug information
    auto logger_name = "fakefactors::xyh::RawFakeFactorSemileptonic";

    // Load the correction sets with fake factors and process fractions
    Logger::get(logger_name)
        ->debug("Loading correction sets for raw fake factor evaluation");
    auto qcd_cset = correctionManager.loadCorrection(ff_file, ff_qcd_name);
    auto tt_cset = correctionManager.loadCorrection(ff_file, ff_tt_name);
    auto fractions_cset =
        correctionManager.loadCorrection(ff_file, ff_fraction_name);

    auto raw_ff_semileptonic = [logger_name, qcd_cset, tt_cset, fractions_cset,
                                ff_qcd_name, ff_tt_name, ff_fraction_name,
                                ff_qcd_variation, ff_tt_variation,
                                ff_fraction_variation](
                                   const std::vector<float> &qcd_inputs,
                                   const std::vector<float> &tt_inputs,
                                   const std::vector<float> &fraction_inputs) {
        // Initial debug message at the start of the function
        Logger::get(logger_name)->debug("Run raw fake factor evaluation");

        // Debug messages for the systematic variations being applied
        Logger::get(logger_name)->debug("Variations for fake factors:");
        Logger::get(logger_name)
            ->debug("    {}: {}", ff_qcd_name, ff_qcd_variation);
        Logger::get(logger_name)
            ->debug("    {}: {}", ff_tt_name, ff_tt_variation);
        Logger::get(logger_name)
            ->debug("    {}: {}", ff_fraction_name, ff_fraction_variation);

        // Prepare the inputs for the correction set evaluation
        auto _qcd_inputs =
            fakefactors::util::prepare_ff_input(qcd_inputs, ff_qcd_variation);
        auto _tt_inputs =
            fakefactors::util::prepare_ff_input(tt_inputs, ff_tt_variation);
        auto _fraction_inputs_qcd = fakefactors::util::prepare_fractions_input(
            fraction_inputs, "QCD", ff_fraction_variation);
        auto _fraction_inputs_tt = fakefactors::util::prepare_fractions_input(
            fraction_inputs, "ttbar", ff_fraction_variation);

        // Debug messages for inputs to correction sets
        Logger::get(logger_name)
            ->debug("Evaluating fake factors and process fractions with "
                    "the following input vectors");
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_qcd_name,
                    fakefactors::util::join(_qcd_inputs));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_tt_name,
                    fakefactors::util::join(_tt_inputs));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_fraction_name,
                    fakefactors::util::join(_fraction_inputs_qcd));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_fraction_name,
                    fakefactors::util::join(_fraction_inputs_tt));

        // Get the fake factors and process fractions from the
        // correction sets
        float ff_qcd = qcd_cset->evaluate(_qcd_inputs);
        float ff_tt = tt_cset->evaluate(_tt_inputs);
        float frac_qcd = fractions_cset->evaluate(_fraction_inputs_qcd);
        float frac_tt = fractions_cset->evaluate(_fraction_inputs_tt);

        // Debug messages for fake factors and process fractions
        Logger::get(logger_name)->debug("Got results");
        Logger::get(logger_name)->debug("    cset {}: {}", ff_qcd_name, ff_qcd);
        Logger::get(logger_name)->debug("    cset {}: {}", ff_tt_name, ff_tt);
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_fraction_name, frac_qcd);
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_fraction_name, frac_tt);

        // Calculate the raw fake factor
        float ff =
            frac_qcd * std::max(ff_qcd, 0.f) + frac_tt * std::max(ff_tt, 0.f);
        Logger::get(logger_name)->debug("Calculated raw fake factor {}", ff);

        return ff;
    };

    return df.Define(outputname, raw_ff_semileptonic,
                     {qcd_inputs, tt_inputs, fraction_inputs});
}

ROOT::RDF::RNode FakeFactorSemileptonic(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correctionManager,
    const std::string &outputname, const std::string &qcd_inputs,
    const std::string &tt_inputs, const std::string &fraction_inputs,
    const std::string &qcd_corr_dr_sr_inputs,
    const std::string &qcd_corr_closure_inputs,
    const std::string &tt_corr_closure_inputs, const std::string &ff_file,
    const std::string &ff_qcd_name, const std::string &ff_tt_name,
    const std::string &ff_fraction_name, const std::string &corr_file,
    const std::string &corr_qcd_dr_sr_name,
    const std::string &corr_qcd_closure_name,
    const std::string &corr_tt_closure_name,
    const std::string &ff_qcd_variation, const std::string &ff_tt_variation,
    const std::string &ff_fraction_variation,
    const std::string &qcd_corr_dr_sr_variation,
    const std::string &qcd_corr_closure_variation,
    const std::string &tt_corr_closure_variation) {
    // Define logger name and print general debug information
    auto logger_name = "fakefactors::xyh::FakeFactorSemileptonic";

    // Load the correction sets with fake factors and process fractions, as
    // well as the compound fake factor corrections
    Logger::get(logger_name)
        ->debug("Loading correction sets for fake factor evaluation with "
                "corrections");
    auto qcd_cset = correctionManager.loadCorrection(ff_file, ff_qcd_name);
    auto tt_cset = correctionManager.loadCorrection(ff_file, ff_tt_name);
    auto fractions_cset =
        correctionManager.loadCorrection(ff_file, ff_fraction_name);
    auto qcd_corr_dr_sr_cset =
        correctionManager.loadCorrection(corr_file, corr_qcd_dr_sr_name);
    auto qcd_corr_closure_cset = correctionManager.loadCompoundCorrection(
        corr_file, corr_qcd_closure_name);
    auto tt_corr_closure_cset = correctionManager.loadCompoundCorrection(
        corr_file, corr_tt_closure_name);

    auto ff_semileptonic = [qcd_cset, tt_cset, fractions_cset,
                            qcd_corr_dr_sr_cset, qcd_corr_closure_cset,
                            tt_corr_closure_cset, logger_name, ff_qcd_name,
                            ff_tt_name, ff_fraction_name, corr_qcd_dr_sr_name,
                            corr_qcd_closure_name, corr_tt_closure_name,
                            ff_qcd_variation, ff_tt_variation,
                            ff_fraction_variation, qcd_corr_dr_sr_variation,
                            qcd_corr_closure_variation,
                            tt_corr_closure_variation](
                               const std::vector<float> &qcd_inputs,
                               const std::vector<float> &tt_inputs,
                               const std::vector<float> &fraction_inputs,
                               const std::vector<float> &qcd_corr_dr_sr_inputs,
                               const std::vector<float>
                                   &qcd_corr_closure_inputs,
                               const std::vector<float>
                                   &tt_corr_closure_inputs) {
        // Initial debug message at the start of the function
        Logger::get(logger_name)
            ->debug("Run fake factor evaluation with corrections");

        Logger::get(logger_name)->debug("Variations for fake factors:");
        Logger::get(logger_name)
            ->debug("    {}: {}", ff_qcd_name, ff_qcd_variation);
        Logger::get(logger_name)
            ->debug("    {}: {}", ff_tt_name, ff_tt_variation);
        Logger::get(logger_name)
            ->debug("    {}: {}", ff_fraction_name, ff_fraction_variation);
        Logger::get(logger_name)
            ->debug("    {}: {}", corr_qcd_dr_sr_name,
                    qcd_corr_dr_sr_variation);
        Logger::get(logger_name)
            ->debug("    {}: {}", corr_qcd_closure_name,
                    qcd_corr_closure_variation);
        Logger::get(logger_name)
            ->debug("    {}: {}", corr_tt_closure_name,
                    tt_corr_closure_variation);

        // Prepare inputs
        auto _qcd_inputs =
            fakefactors::util::prepare_ff_input(qcd_inputs, ff_qcd_variation);
        auto _tt_inputs =
            fakefactors::util::prepare_ff_input(tt_inputs, ff_tt_variation);
        auto _fraction_inputs_qcd = fakefactors::util::prepare_fractions_input(
            fraction_inputs, "QCD", ff_fraction_variation);
        auto _fraction_inputs_tt = fakefactors::util::prepare_fractions_input(
            fraction_inputs, "ttbar", ff_fraction_variation);
        auto _qcd_corr_dr_sr_inputs = fakefactors::util::prepare_ff_input(
            qcd_corr_dr_sr_inputs, qcd_corr_dr_sr_variation);
        auto _qcd_corr_closure_inputs = fakefactors::util::prepare_ff_input(
            qcd_corr_closure_inputs, qcd_corr_closure_variation);
        auto _tt_corr_closure_inputs = fakefactors::util::prepare_ff_input(
            tt_corr_closure_inputs, tt_corr_closure_variation);

        // Debug messages for inputs to correction sets
        Logger::get(logger_name)
            ->debug("Evaluating fake factors and process "
                    "fractions with "
                    "the following input vectors");
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_qcd_name,
                    fakefactors::util::join(_qcd_inputs));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_tt_name,
                    fakefactors::util::join(_tt_inputs));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_fraction_name,
                    fakefactors::util::join(_fraction_inputs_qcd));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_fraction_name,
                    fakefactors::util::join(_fraction_inputs_tt));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", corr_qcd_dr_sr_name,
                    fakefactors::util::join(_qcd_corr_dr_sr_inputs));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", corr_qcd_closure_name,
                    fakefactors::util::join(_qcd_corr_closure_inputs));
        Logger::get(logger_name)
            ->debug("    cset {}: {}", corr_tt_closure_name,
                    fakefactors::util::join(_tt_corr_closure_inputs));

        // Get the fake factors and process fractions from the
        // correction sets
        float ff_qcd = qcd_cset->evaluate(_qcd_inputs);
        float ff_tt = tt_cset->evaluate(_tt_inputs);
        float frac_qcd = fractions_cset->evaluate(_fraction_inputs_qcd);
        float frac_tt = fractions_cset->evaluate(_fraction_inputs_tt);

        // Get the corrections for the fake factors
        float corr_qcd_dr_sr =
            qcd_corr_dr_sr_cset->evaluate(_qcd_corr_dr_sr_inputs);
        float corr_qcd_closure =
            qcd_corr_closure_cset->evaluate(_qcd_corr_closure_inputs);
        float corr_tt_closure =
            tt_corr_closure_cset->evaluate(_tt_corr_closure_inputs);

        // Debug messages for fake factors, process fractions,
        // and corrections
        Logger::get(logger_name)->debug("Got results");
        Logger::get(logger_name)->debug("    cset {}: {}", ff_qcd_name, ff_qcd);
        Logger::get(logger_name)->debug("    cset {}: {}", ff_tt_name, ff_tt);
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_fraction_name, frac_qcd);
        Logger::get(logger_name)
            ->debug("    cset {}: {}", ff_fraction_name, frac_tt);
        Logger::get(logger_name)
            ->debug("    cset {}: {}", corr_qcd_dr_sr_name, corr_qcd_dr_sr);
        Logger::get(logger_name)
            ->debug("    cset {}: {}", corr_qcd_closure_name, corr_qcd_closure);
        Logger::get(logger_name)
            ->debug("    cset {}: {}", corr_tt_closure_name, corr_tt_closure);

        // Calculate the raw fake factor
        float ff =
            frac_qcd *
                std::max(ff_qcd * corr_qcd_dr_sr * corr_qcd_closure, 0.f) +
            frac_tt * std::max(ff_tt * corr_tt_closure, 0.f);
        Logger::get(logger_name)
            ->debug("Calculated fake factor with corrections {}", ff);

        return ff;
    };

    return df.Define(outputname, ff_semileptonic,
                     {qcd_inputs, tt_inputs, fraction_inputs,
                      qcd_corr_dr_sr_inputs, qcd_corr_closure_inputs,
                      tt_corr_closure_inputs});
}

} // namespace xyh

/**
 * @brief Function to calculate raw fake factors without corrections with
 * correctionlib for the semileptonic channels
 *
 * @param df the input dataframe
 * @param outputname name of the output column for the fake factor
 * @param tau_pt pt of the hadronic tau in the tau pair
 * @param njets number of good jets in the event
 * @param lep_mt transverse mass of the leptonic tau in the tau pair
 * @param nbtags number of good b-tagged jets in the event
 * @param qcd_variation name of the QCD FF uncertainty variation or nominal
 * @param wjets_variation name of the Wjets FF uncertainty variation or
 * nominal
 * @param ttbar_variation name of the ttbar FF uncertainty variation or
 * nominal
 * @param fraction_variation name of the process fraction uncertainty
 * variation or nominal
 * @param ff_file correctionlib json file with the fake factors
 * @returns a dataframe with the fake factors
 */
ROOT::RDF::RNode raw_fakefactor_lt(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &tau_pt, const std::string &njets,
    const std::string &lep_mt, const std::string &nbtags,
    const std::string &qcd_variation, const std::string &wjets_variation,
    const std::string &ttbar_variation, const std::string &fraction_variation,
    const std::string &ff_file) {
    Logger::get("RawFakeFactor")
        ->debug("Setting up functions for raw fake factor (without "
                "corrections) evaluation with correctionlib");
    Logger::get("RawFakeFactor")
        ->debug("QCD variation - Name {}", qcd_variation);
    Logger::get("RawFakeFactor")
        ->debug("Wjets variation - Name {}", wjets_variation);
    Logger::get("RawFakeFactor")
        ->debug("ttbar variation - Name {}", ttbar_variation);
    Logger::get("RawFakeFactor")
        ->debug("Fraction variation - Name {}", fraction_variation);
    auto qcd =
        correction::CorrectionSet::from_file(ff_file)->at("QCD_fake_factors");
    auto wjets =
        correction::CorrectionSet::from_file(ff_file)->at("Wjets_fake_factors");
    auto ttbar =
        correction::CorrectionSet::from_file(ff_file)->at("ttbar_fake_factors");
    auto fractions =
        correction::CorrectionSet::from_file(ff_file)->at("process_fractions");
    auto calc_fake_factor = [qcd_variation, wjets_variation, ttbar_variation,
                             fraction_variation, qcd, wjets, ttbar,
                             fractions](const float &pt_2, const int &njets,
                                        const float &mt_1, const int &nbtag) {
        float ff = 0.;
        if (pt_2 >= 0.) {
            Logger::get("RawFakeFactor")->debug("Tau pt - value {}", pt_2);
            Logger::get("RawFakeFactor")->debug("N jets - value {}", njets);

            float qcd_ff = qcd->evaluate({pt_2, (float)njets, qcd_variation});
            Logger::get("RawFakeFactor")->debug("QCD - value {}", qcd_ff);
            float wjets_ff =
                wjets->evaluate({pt_2, (float)njets, wjets_variation});
            Logger::get("RawFakeFactor")->debug("Wjets - value {}", wjets_ff);
            float ttbar_ff =
                ttbar->evaluate({pt_2, (float)njets, ttbar_variation});
            Logger::get("RawFakeFactor")->debug("ttbar - value {}", ttbar_ff);

            Logger::get("RawFakeFactor")->debug("Lep mt - value {}", mt_1);
            Logger::get("RawFakeFactor")->debug("N b-jets - value {}", nbtag);

            float qcd_frac = fractions->evaluate(
                {"QCD", mt_1, (float)nbtag, fraction_variation});
            Logger::get("RawFakeFactor")->debug("QCD - fraction {}", qcd_frac);
            float wjets_frac = fractions->evaluate(
                {"Wjets", mt_1, (float)nbtag, fraction_variation});
            Logger::get("RawFakeFactor")
                ->debug("Wjets - fraction {}", wjets_frac);
            float ttbar_frac = fractions->evaluate(
                {"ttbar", mt_1, (float)nbtag, fraction_variation});
            Logger::get("RawFakeFactor")
                ->debug("ttbar - fraction {}", ttbar_frac);

            ff = qcd_frac * std::max(qcd_ff, (float)0.) +
                 wjets_frac * std::max(wjets_ff, (float)0.) +
                 ttbar_frac * std::max(ttbar_ff, (float)0.);
        }

        Logger::get("RawFakeFactor")->debug("Event Fake Factor {}", ff);
        return ff;
    };
    auto df1 = df.Define(outputname, calc_fake_factor,
                         {tau_pt, njets, lep_mt, nbtags});
    return df1;
}

/**
 * @brief Function to calculate raw fake factors without corrections with
 * correctionlib for the semileptonic channels
 *
 * @param df the input dataframe
 * @param outputname name of the output column for the fake factor
 * @param tau_pt pt of the hadronic tau in the tau pair
 * @param njets number of good jets in the event
 * @param lep_mt transverse mass of the leptonic tau in the tau pair
 * @param nbtags number of good b-tagged jets in the event
 * @param qcd_variation name of the QCD FF uncertainty variation or nominal
 * @param wjets_variation name of the Wjets FF uncertainty variation or
 * nominal
 * @param ttbar_variation name of the ttbar FF uncertainty variation or
 * nominal
 * @param fraction_variation name of the process fraction uncertainty
 * variation or nominal
 * @param ff_file correctionlib json file with the fake factors
 * @returns a dataframe with the fake factors
 */
ROOT::RDF::RNode raw_fakefactor_nmssm_lt(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &tau_pt, const std::string &njets,
    const std::string &lep_mt, const std::string &nbtags,
    const std::string &qcd_variation, const std::string &wjets_variation,
    const std::string &ttbar_variation, const std::string &fraction_variation,
    const std::string &ff_file) {
    Logger::get("RawFakeFactor")
        ->debug("Setting up functions for raw fake factor (without "
                "corrections) evaluation with correctionlib");
    Logger::get("RawFakeFactor")
        ->debug("QCD variation - Name {}", qcd_variation);
    Logger::get("RawFakeFactor")
        ->debug("Wjets variation - Name {}", wjets_variation);
    Logger::get("RawFakeFactor")
        ->debug("ttbar variation - Name {}", ttbar_variation);
    Logger::get("RawFakeFactor")
        ->debug("Fraction variation - Name {}", fraction_variation);
    auto qcd =
        correction::CorrectionSet::from_file(ff_file)->at("QCD_fake_factors");
    auto wjets =
        correction::CorrectionSet::from_file(ff_file)->at("Wjets_fake_factors");
    auto ttbar =
        correction::CorrectionSet::from_file(ff_file)->at("ttbar_fake_factors");
    auto fractions =
        correction::CorrectionSet::from_file(ff_file)->at("process_fractions");
    auto calc_fake_factor = [qcd_variation, wjets_variation, ttbar_variation,
                             fraction_variation, qcd, wjets, ttbar,
                             fractions](const float &pt_2, const int &njets,
                                        const float &mt_1, const int &nbtag) {
        float ff = 0.;
        if (pt_2 >= 0.) {
            Logger::get("RawFakeFactor")->debug("Tau pt - value {}", pt_2);
            Logger::get("RawFakeFactor")->debug("N jets - value {}", njets);

            float qcd_ff = qcd->evaluate({pt_2, (float)njets, qcd_variation});
            Logger::get("RawFakeFactor")->debug("QCD - value {}", qcd_ff);
            float wjets_ff =
                wjets->evaluate({pt_2, (float)njets, wjets_variation});
            Logger::get("RawFakeFactor")->debug("Wjets - value {}", wjets_ff);
            float ttbar_ff =
                ttbar->evaluate({pt_2, (float)njets, ttbar_variation});
            Logger::get("RawFakeFactor")->debug("ttbar - value {}", ttbar_ff);

            Logger::get("RawFakeFactor")->debug("Lep mt - value {}", mt_1);
            Logger::get("RawFakeFactor")->debug("N b-jets - value {}", nbtag);

            float qcd_frac = fractions->evaluate(
                {"QCD", mt_1, (float)nbtag, fraction_variation});
            Logger::get("RawFakeFactor")->debug("QCD - fraction {}", qcd_frac);
            float wjets_frac = fractions->evaluate(
                {"Wjets", mt_1, (float)nbtag, fraction_variation});
            Logger::get("RawFakeFactor")
                ->debug("Wjets - fraction {}", wjets_frac);
            float ttbar_frac = fractions->evaluate(
                {"ttbar", mt_1, (float)nbtag, fraction_variation});
            Logger::get("RawFakeFactor")
                ->debug("ttbar - fraction {}", ttbar_frac);

            ff = qcd_frac * std::max(qcd_ff, (float)0.) +
                 wjets_frac * std::max(wjets_ff, (float)0.) +
                 ttbar_frac * std::max(ttbar_ff, (float)0.);
        }

        Logger::get("RawFakeFactor")->debug("Event Fake Factor {}", ff);
        return ff;
    };
    auto df1 = df.Define(outputname, calc_fake_factor,
                         {tau_pt, njets, lep_mt, nbtags});
    return df1;
}
/**
 * @brief Function to calculate raw fake factors without corrections with
 * correctionlib for the NMSSM Di-Higgs analysis for the full hadronic
 * channel
 *
 * @param df the dataframe to add the quantity to
 * @param outputname name of the output column for the fake factor
 * @param tau_idx index of the tau, leading/subleading
 * @param tau_pt_1 pt of the leading hadronic tau in the tau pair
 * @param tau_pt_2 pt of the subleading hadronic tau in the tau pair
 * @param njets number of good jets in the event
 * @param m_vis visible di-tau mass of the tau pair
 * @param nbtag number of good b-tagged jets in the event
 * @param qcd_variation name of the QCD FF uncertainty variation or nominal
 * @param ttbar_variation name of the ttbar FF uncertainty variation or
 * nominal
 * @param fraction_variation name of the process fraction uncertainty
 * variation or nominal
 * @param ff_file correctionlib json file with the fake factors
 * @returns a dataframe with the fake factors
 */
ROOT::RDF::RNode raw_fakefactor_nmssm_tt(
    ROOT::RDF::RNode df, const std::string &outputname, const int &tau_idx,
    const std::string &tau_pt_1, const std::string &tau_pt_2,
    const std::string &njets, const std::string &m_vis,
    const std::string &nbtag, const std::string &qcd_variation,
    const std::string &ttbar_variation, const std::string &fraction_variation,
    const std::string &ff_file) {

    Logger::get("RawFakeFactor")
        ->debug("Setting up functions for raw fake factor (without "
                "corrections) evaluation with correctionlib");
    Logger::get("RawFakeFactor")
        ->debug("QCD variation - Name {}", qcd_variation);
    Logger::get("RawFakeFactor")
        ->debug("ttbar variation - Name {}", ttbar_variation);
    Logger::get("RawFakeFactor")
        ->debug("Fraction variation - Name {}", fraction_variation);

    auto qcd =
        correction::CorrectionSet::from_file(ff_file)->at("QCD_fake_factors");
    auto qcd_subleading = correction::CorrectionSet::from_file(ff_file)->at(
        "QCD_subleading_fake_factors");
    auto ttbar =
        correction::CorrectionSet::from_file(ff_file)->at("ttbar_fake_factors");
    auto ttbar_subleading = correction::CorrectionSet::from_file(ff_file)->at(
        "ttbar_subleading_fake_factors");
    auto fractions =
        correction::CorrectionSet::from_file(ff_file)->at("process_fractions");
    auto fractions_subleading =
        correction::CorrectionSet::from_file(ff_file)->at(
            "process_fractions_subleading");

    auto calc_fake_factor = [tau_idx, qcd_variation, ttbar_variation,
                             fraction_variation, qcd, qcd_subleading, ttbar,
                             ttbar_subleading, fractions, fractions_subleading](
                                const float &pt_1, const float &pt_2,
                                const int &njets, const float &m_vis,
                                const int &nbtag) {
        float ff = 0.;
        if (pt_2 >= 0.) {
            Logger::get("RawFakeFactor")
                ->debug("Leading Tau pt - value {}", pt_1);
            Logger::get("RawFakeFactor")
                ->debug("Subleading Tau pt - value {}", pt_2);
            Logger::get("RawFakeFactor")->debug("N jets - value {}", njets);

            float qcd_ff = -1.;
            float ttbar_ff = -1.;
            float qcd_frac = -1.;
            float wjets_frac = -1.;
            float ttbar_frac = -1.;
            if (tau_idx == 0) {
                qcd_ff = qcd->evaluate({pt_1, (float)njets, qcd_variation});
                Logger::get("RawFakeFactor")->debug("QCD - value {}", qcd_ff);
                ttbar_ff =
                    ttbar->evaluate({pt_1, (float)njets, ttbar_variation});
                Logger::get("RawFakeFactor")
                    ->debug("ttbar - value {}", ttbar_ff);
                qcd_frac = fractions->evaluate(
                    {"QCD", m_vis, (float)nbtag, fraction_variation});
                Logger::get("RawFakeFactor")
                    ->debug("QCD - fraction {}", qcd_frac);
                wjets_frac = fractions->evaluate(
                    {"Wjets", m_vis, (float)nbtag, fraction_variation});
                Logger::get("RawFakeFactor")
                    ->debug("Wjets - fraction {}", wjets_frac);
                ttbar_frac = fractions->evaluate(
                    {"ttbar", m_vis, (float)nbtag, fraction_variation});
                Logger::get("RawFakeFactor")
                    ->debug("ttbar - fraction {}", ttbar_frac);

                ff = (qcd_frac + wjets_frac) * std::max(qcd_ff, (float)0.) +
                     ttbar_frac * std::max(ttbar_ff, (float)0.);
            } else if (tau_idx == 1) {
                qcd_ff = qcd_subleading->evaluate(
                    {pt_2, (float)njets, qcd_variation});
                Logger::get("RawFakeFactor")->debug("QCD - value {}", qcd_ff);
                ttbar_ff = ttbar_subleading->evaluate(
                    {pt_1, (float)njets, ttbar_variation});
                Logger::get("RawFakeFactor")
                    ->debug("ttbar - value {}", ttbar_ff);
                qcd_frac = fractions_subleading->evaluate(
                    {"QCD", m_vis, (float)nbtag, fraction_variation});
                Logger::get("RawFakeFactor")
                    ->debug("QCD - fraction {}", qcd_frac);
                wjets_frac = fractions_subleading->evaluate(
                    {"Wjets", m_vis, (float)nbtag, fraction_variation});
                Logger::get("RawFakeFactor")
                    ->debug("Wjets - fraction {}", wjets_frac);
                ttbar_frac = fractions_subleading->evaluate(
                    {"ttbar", m_vis, (float)nbtag, fraction_variation});
                Logger::get("RawFakeFactor")
                    ->debug("ttbar - fraction {}", ttbar_frac);

                ff = (qcd_frac + wjets_frac) * std::max(qcd_ff, (float)0.) +
                     ttbar_frac * std::max(ttbar_ff, (float)0.);
            }
        }

        Logger::get("RawFakeFactor")->debug("Event Fake Factor {}", ff);
        return ff;
    };
    auto df1 = df.Define(outputname, calc_fake_factor,
                         {tau_pt_1, tau_pt_2, njets, m_vis, nbtag});
    return df1;
}
/**
 * @brief Function to calculate fake factors with correctionlib for the
 * semileptonic channels
 *
 * @param df the input dataframe
 * @param outputname name of the output column for the fake factor
 * @param tau_pt pt of the hadronic tau in the tau pair
 * @param njets number of good jets in the event
 * @param lep_mt transverse mass of the leptonic tau in the tau pair
 * @param nbtags number of good b-tagged jets in the event
 * @param lep_pt pt of the leptonic tau in the tau pair
 * @param tau_mass mass of the hadronic tau in the tau pair
 * @param m_vis visible mass of the tau pair
 * @param qcd_variation name of the QCD FF uncertainty variation or nominal
 * @param wjets_variation name of the Wjets FF uncertainty variation or
 * nominal
 * @param ttbar_variation name of the ttbar FF uncertainty variation or
 * nominal
 * @param fraction_variation name of the process fraction uncertainty
 * variation or nominal
 * @param qcd_corr_leppt_variation name of the QCD lepton pt correction
 * uncertainty variation or nominal
 * @param qcd_corr_taumass_variation name of the QCD tau mass correction
 * uncertainty variation or nominal
 * @param qcd_corr_drsr_variation name of the QCD DR to SR correction
 * uncertainty variation or nominal
 * @param wjets_corr_leppt_variation name of the Wjets lepton pt correction
 * uncertainty variation or nominal
 * @param wjets_corr_taumass_variation name of the Wjets tau mass correction
 * uncertainty variation or nominal
 * @param wjets_corr_drsr_variation name of the Wjets DR to SR correction
 * uncertainty variation or nominal
 * @param ttbar_corr_leppt_variation name of the ttbar lepton pt correction
 * uncertainty variation or nominal
 * @param ttbar_corr_taumass_variation name of the ttbar tau mass correction
 * uncertainty variation or nominal
 * @param ff_file correctionlib json file with the fake factors
 * @param ff_corr_file correctionlib json file with corrections for the fake
 * factors
 * @returns a dataframe with the fake factors
 */
ROOT::RDF::RNode fakefactor_nmssm_lt(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &tau_pt, const std::string &njets,
    const std::string &lep_mt, const std::string &nbtags,
    const std::string &lep_pt, const std::string &tau_mass,
    const std::string &m_vis, const std::string &qcd_variation,
    const std::string &wjets_variation, const std::string &ttbar_variation,
    const std::string &fraction_variation,
    const std::string &qcd_corr_leppt_variation,
    const std::string &qcd_corr_taumass_variation,
    const std::string &qcd_corr_drsr_variation,
    const std::string &wjets_corr_leppt_variation,
    const std::string &wjets_corr_taumass_variation,
    const std::string &wjets_corr_drsr_variation,
    const std::string &ttbar_corr_leppt_variation,
    const std::string &ttbar_corr_taumass_variation, const std::string &ff_file,
    const std::string &ff_corr_file) {

    Logger::get("FakeFactor")
        ->debug("Setting up functions for fake factor evaluation with "
                "correctionlib");
    Logger::get("FakeFactor")->debug("QCD variation - Name {}", qcd_variation);
    Logger::get("FakeFactor")
        ->debug("Wjets variation - Name {}", wjets_variation);
    Logger::get("FakeFactor")
        ->debug("ttbar variation - Name {}", ttbar_variation);
    Logger::get("FakeFactor")
        ->debug("Fraction variation - Name {}", fraction_variation);
    Logger::get("FakeFactor")
        ->debug("QCD lep pt corr variation - Name {}",
                qcd_corr_leppt_variation);
    Logger::get("FakeFactor")
        ->debug("QCD tau mass corr variation - Name {}",
                qcd_corr_taumass_variation);
    Logger::get("FakeFactor")
        ->debug("QCD DRSR corr variation - Name {}", qcd_corr_drsr_variation);
    Logger::get("FakeFactor")
        ->debug("Wjets lep pt corr variation - Name {}",
                wjets_corr_leppt_variation);
    Logger::get("FakeFactor")
        ->debug("Wjets tau mass corr variation - Name {}",
                wjets_corr_taumass_variation);
    Logger::get("FakeFactor")
        ->debug("Wjets DRSR corr variation - Name {}",
                wjets_corr_drsr_variation);
    Logger::get("FakeFactor")
        ->debug("ttbar lep pt corr variation - Name {}",
                ttbar_corr_leppt_variation);
    Logger::get("FakeFactor")
        ->debug("ttbar tau mass corr variation - Name {}",
                ttbar_corr_taumass_variation);

    auto qcd =
        correction::CorrectionSet::from_file(ff_file)->at("QCD_fake_factors");
    auto wjets =
        correction::CorrectionSet::from_file(ff_file)->at("Wjets_fake_factors");
    auto ttbar =
        correction::CorrectionSet::from_file(ff_file)->at("ttbar_fake_factors");
    auto fractions =
        correction::CorrectionSet::from_file(ff_file)->at("process_fractions");

    auto qcd_lep_pt_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("QCD_non_closure_leading_lep_pt_correction");
    auto qcd_tau_mass_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("QCD_non_closure_subleading_lep_mass_correction");
    auto qcd_DR_SR = correction::CorrectionSet::from_file(ff_corr_file)
                         ->at("QCD_DR_SR_correction");
    auto wjets_lep_pt_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("Wjets_non_closure_leading_lep_pt_correction");
    auto wjets_tau_mass_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("Wjets_non_closure_subleading_lep_mass_correction");
    auto wjets_DR_SR = correction::CorrectionSet::from_file(ff_corr_file)
                           ->at("Wjets_DR_SR_correction");
    auto ttbar_lep_pt_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("ttbar_non_closure_leading_lep_pt_correction");
    auto ttbar_tau_mass_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("ttbar_non_closure_subleading_lep_mass_correction");
    auto calc_fake_factor = [qcd_variation, wjets_variation, ttbar_variation,
                             fraction_variation, qcd_corr_leppt_variation,
                             qcd_corr_taumass_variation,
                             qcd_corr_drsr_variation,
                             wjets_corr_leppt_variation,
                             wjets_corr_taumass_variation,
                             wjets_corr_drsr_variation,
                             ttbar_corr_leppt_variation,
                             ttbar_corr_taumass_variation, qcd, wjets, ttbar,
                             fractions, qcd_lep_pt_closure,
                             qcd_tau_mass_closure, qcd_DR_SR,
                             wjets_lep_pt_closure, wjets_tau_mass_closure,
                             wjets_DR_SR, ttbar_lep_pt_closure,
                             ttbar_tau_mass_closure](
                                const float &pt_2, const int &njets,
                                const float &mt_1, const int &nbtag,
                                const float &pt_1, const float &mass_2,
                                const float &m_vis) {
        float ff = 0.;
        if (pt_2 >= 0.) {
            Logger::get("FakeFactor")->debug("Tau pt - value {}", pt_2);
            Logger::get("FakeFactor")->debug("N jets - value {}", njets);

            float qcd_ff = qcd->evaluate({pt_2, (float)njets, qcd_variation});
            Logger::get("FakeFactor")->debug("QCD - value {}", qcd_ff);
            float wjets_ff =
                wjets->evaluate({pt_2, (float)njets, wjets_variation});
            Logger::get("FakeFactor")->debug("Wjets - value {}", wjets_ff);
            float ttbar_ff =
                ttbar->evaluate({pt_2, (float)njets, ttbar_variation});
            Logger::get("FakeFactor")->debug("ttbar - value {}", ttbar_ff);

            Logger::get("FakeFactor")->debug("Lep mt - value {}", mt_1);
            Logger::get("FakeFactor")->debug("N b-jets - value {}", nbtag);

            float qcd_frac = fractions->evaluate(
                {"QCD", mt_1, (float)nbtag, fraction_variation});
            Logger::get("FakeFactor")->debug("QCD - fraction {}", qcd_frac);
            float wjets_frac = fractions->evaluate(
                {"Wjets", mt_1, (float)nbtag, fraction_variation});
            Logger::get("FakeFactor")->debug("Wjets - fraction {}", wjets_frac);
            float ttbar_frac = fractions->evaluate(
                {"ttbar", mt_1, (float)nbtag, fraction_variation});
            Logger::get("FakeFactor")->debug("ttbar - fraction {}", ttbar_frac);

            Logger::get("FakeFactor")->debug("Lep pt - value {}", pt_1);
            Logger::get("FakeFactor")->debug("Tau mass - value {}", mass_2);
            Logger::get("FakeFactor")->debug("m_vis - value {}", m_vis);

            float qcd_lep_pt_corr =
                qcd_lep_pt_closure->evaluate({pt_1, qcd_corr_leppt_variation});
            Logger::get("FakeFactor")
                ->debug("QCD - lep pt correction {}", qcd_lep_pt_corr);
            float qcd_tau_mass_corr = qcd_tau_mass_closure->evaluate(
                {mass_2, qcd_corr_taumass_variation});
            Logger::get("FakeFactor")
                ->debug("QCD - tau mass correction {}", qcd_tau_mass_corr);
            float qcd_DR_SR_corr =
                qcd_DR_SR->evaluate({m_vis, qcd_corr_drsr_variation});
            Logger::get("FakeFactor")
                ->debug("QCD - DR to SR correction {}", qcd_DR_SR_corr);
            float wjets_lep_pt_corr = wjets_lep_pt_closure->evaluate(
                {pt_1, wjets_corr_leppt_variation});
            Logger::get("FakeFactor")
                ->debug("Wjets - lep pt correction {}", wjets_lep_pt_corr);
            float wjets_tau_mass_corr = wjets_tau_mass_closure->evaluate(
                {mass_2, wjets_corr_taumass_variation});
            Logger::get("FakeFactor")
                ->debug("Wjets - tau mass correction {}", wjets_tau_mass_corr);
            float wjets_DR_SR_corr =
                wjets_DR_SR->evaluate({m_vis, wjets_corr_drsr_variation});
            Logger::get("FakeFactor")
                ->debug("Wjets - DR to SR correction {}", wjets_DR_SR_corr);
            float ttbar_lep_pt_corr = ttbar_lep_pt_closure->evaluate(
                {pt_1, ttbar_corr_leppt_variation});
            Logger::get("FakeFactor")
                ->debug("ttbar - lep pt correction {}", ttbar_lep_pt_corr);
            float ttbar_tau_mass_corr = ttbar_tau_mass_closure->evaluate(
                {mass_2, ttbar_corr_taumass_variation});
            Logger::get("FakeFactor")
                ->debug("ttbar - tau mass correction {}", ttbar_tau_mass_corr);

            ff = qcd_frac * std::max(qcd_ff, (float)0.) * qcd_lep_pt_corr *
                     qcd_tau_mass_corr * qcd_DR_SR_corr +
                 wjets_frac * std::max(wjets_ff, (float)0.) *
                     wjets_lep_pt_corr * wjets_tau_mass_corr *
                     wjets_DR_SR_corr +
                 ttbar_frac * std::max(ttbar_ff, (float)0.) *
                     ttbar_lep_pt_corr * ttbar_tau_mass_corr;
        }

        Logger::get("FakeFactor")->debug("Event Fake Factor {}", ff);
        return ff;
    };
    auto df1 =
        df.Define(outputname, calc_fake_factor,
                  {tau_pt, njets, lep_mt, nbtags, lep_pt, tau_mass, m_vis});
    return df1;
}

/**
 * @brief Function to calculate fake factors with correctionlib for the
 * NMSSM Di-Higgs boosted analysis for the semileptonic channel
 *
 * @param df the dataframe to add the quantity to
 * @param outputname name of the output column for the fake factor
 * @param boosted_tau_pt pt of the hadronic tau in the boosted tau pair
 * @param njets number of good jets in the event
 * @param boosted_lep_mt transverse mass of the leptonic tau in the boosted
 * tau pair
 * @param nbtags number of good b-tagged jets in the event
 * @param boosted_lep_pt pt of the leptonic tau in the boosted tau pair
 * @param boosted_m_vis visible mass of the boosted tau pair
 * @param boosted_dR_ditau distance in eta-phi plane of the boosted tau pair
 * @param qcd_variation name of the QCD FF uncertainty variation or nominal
 * @param wjets_variation name of the Wjets FF uncertainty variation or
 * nominal
 * @param ttbar_variation name of the ttbar FF uncertainty variation or
 * nominal
 * @param fraction_variation name of the process fraction uncertainty
 * variation or nominal
 * @param qcd_corr_leppt_variation name of the QCD lepton pt correction
 * uncertainty variation or nominal
 * @param qcd_corr_lepmt_variation name of the QCD transverse mass
 * (lepton+MET) correction uncertainty variation or nominal
 * @param qcd_corr_drsr_variation name of the QCD DR to SR correction
 * uncertainty variation or nominal
 * @param wjets_corr_leppt_variation name of the Wjets lepton pt correction
 * uncertainty variation or nominal
 * @param wjets_corr_drsr_variation name of the Wjets DR to SR correction
 * uncertainty variation or nominal
 * @param ttbar_corr_leppt_variation name of the ttbar lepton pt correction
 * uncertainty variation or nominal
 * @param ff_file correctionlib json file with the fake factors
 * @param ff_corr_file correctionlib json file with corrections for the fake
 * factors
 * @returns a dataframe with the fake factors
 */
ROOT::RDF::RNode fakefactor_nmssm_boosted_lt(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &boosted_tau_pt, const std::string &njets,
    const std::string &boosted_lep_mt, const std::string &nbtags,
    const std::string &boosted_lep_pt, const std::string &boosted_m_vis,
    const std::string &boosted_dR_ditau, const std::string &qcd_variation,
    const std::string &wjets_variation, const std::string &ttbar_variation,
    const std::string &fraction_variation,
    const std::string &qcd_corr_leppt_variation,
    const std::string &qcd_corr_lepmt_variation,
    const std::string &qcd_corr_drsr_variation,
    const std::string &wjets_corr_leppt_variation,
    const std::string &wjets_corr_drsr_variation,
    const std::string &ttbar_corr_leppt_variation, const std::string &ff_file,
    const std::string &ff_corr_file) {

    Logger::get("FakeFactor")
        ->debug("Setting up functions for fake factor evaluation with "
                "correctionlib");
    Logger::get("FakeFactor")->debug("QCD variation - Name {}", qcd_variation);
    Logger::get("FakeFactor")
        ->debug("Wjets variation - Name {}", wjets_variation);
    Logger::get("FakeFactor")
        ->debug("ttbar variation - Name {}", ttbar_variation);
    Logger::get("FakeFactor")
        ->debug("Fraction variation - Name {}", fraction_variation);
    Logger::get("FakeFactor")
        ->debug("QCD lep pt corr variation - Name {}",
                qcd_corr_leppt_variation);
    Logger::get("FakeFactor")
        ->debug("QCD lep mt corr variation - Name {}",
                qcd_corr_lepmt_variation);
    Logger::get("FakeFactor")
        ->debug("QCD DRSR corr variation - Name {}", qcd_corr_drsr_variation);
    Logger::get("FakeFactor")
        ->debug("Wjets lep pt corr variation - Name {}",
                wjets_corr_leppt_variation);
    Logger::get("FakeFactor")
        ->debug("Wjets DRSR corr variation - Name {}",
                wjets_corr_drsr_variation);
    Logger::get("FakeFactor")
        ->debug("ttbar lep pt corr variation - Name {}",
                ttbar_corr_leppt_variation);
    auto qcd =
        correction::CorrectionSet::from_file(ff_file)->at("QCD_fake_factors");
    auto wjets =
        correction::CorrectionSet::from_file(ff_file)->at("Wjets_fake_factors");
    auto ttbar =
        correction::CorrectionSet::from_file(ff_file)->at("ttbar_fake_factors");
    auto fractions =
        correction::CorrectionSet::from_file(ff_file)->at("process_fractions");

    auto qcd_lep_pt_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("QCD_non_closure_leading_lep_pt_correction");
    auto qcd_lep_mt_closure = correction::CorrectionSet::from_file(ff_corr_file)
                                  ->at("QCD_non_closure_lep_mt_correction");
    auto qcd_DR_SR = correction::CorrectionSet::from_file(ff_corr_file)
                         ->at("QCD_DR_SR_correction");
    auto wjets_lep_pt_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("Wjets_non_closure_leading_lep_pt_correction");
    auto wjets_DR_SR = correction::CorrectionSet::from_file(ff_corr_file)
                           ->at("Wjets_DR_SR_correction");
    auto ttbar_lep_pt_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("ttbar_non_closure_leading_lep_pt_correction");
    // auto ttbar_m_vis_closure =
    //     correction::CorrectionSet::from_file(ff_corr_file)
    //         ->at("ttbar_non_closure_m_vis_correction");
    auto calc_fake_factor = [qcd_variation, wjets_variation, ttbar_variation,
                             fraction_variation, qcd_corr_leppt_variation,
                             qcd_corr_lepmt_variation, qcd_corr_drsr_variation,
                             wjets_corr_leppt_variation,
                             wjets_corr_drsr_variation,
                             ttbar_corr_leppt_variation, qcd, wjets, ttbar,
                             fractions, qcd_lep_pt_closure, qcd_lep_mt_closure,
                             qcd_DR_SR, wjets_lep_pt_closure, wjets_DR_SR,
                             ttbar_lep_pt_closure](
                                const float &boosted_pt_2, const int &njets,
                                const float &boosted_mt_1, const int &nbtag,
                                const float &boosted_pt_1,
                                const float &boosted_m_vis,
                                const float &boosted_dR_ditau) {
        float ff = 0.;
        if (boosted_pt_2 >= 0.) {
            Logger::get("FakeFactor")->debug("Tau pt - value {}", boosted_pt_2);
            Logger::get("FakeFactor")->debug("N jets - value {}", njets);

            float qcd_ff =
                qcd->evaluate({boosted_pt_2, (float)njets, qcd_variation});
            Logger::get("FakeFactor")->debug("QCD - value {}", qcd_ff);
            float wjets_ff =
                wjets->evaluate({boosted_pt_2, (float)njets, wjets_variation});
            Logger::get("FakeFactor")->debug("Wjets - value {}", wjets_ff);
            float ttbar_ff =
                ttbar->evaluate({boosted_pt_2, (float)njets, ttbar_variation});
            Logger::get("FakeFactor")->debug("ttbar - value {}", ttbar_ff);

            Logger::get("FakeFactor")->debug("Lep mt - value {}", boosted_mt_1);
            Logger::get("FakeFactor")->debug("N b-jets - value {}", nbtag);

            float qcd_frac = fractions->evaluate(
                {"QCD", boosted_mt_1, (float)nbtag, fraction_variation});
            Logger::get("FakeFactor")->debug("QCD - fraction {}", qcd_frac);
            float wjets_frac = fractions->evaluate(
                {"Wjets", boosted_mt_1, (float)nbtag, fraction_variation});
            Logger::get("FakeFactor")->debug("Wjets - fraction {}", wjets_frac);
            float ttbar_frac = fractions->evaluate(
                {"ttbar", boosted_mt_1, (float)nbtag, fraction_variation});
            Logger::get("FakeFactor")->debug("ttbar - fraction {}", ttbar_frac);

            Logger::get("FakeFactor")->debug("Lep pt - value {}", boosted_pt_1);
            Logger::get("FakeFactor")->debug("m_vis - value {}", boosted_m_vis);

            float qcd_lep_pt_corr = qcd_lep_pt_closure->evaluate(
                {boosted_pt_1, qcd_corr_leppt_variation});
            Logger::get("FakeFactor")
                ->debug("QCD - lep pt correction {}", qcd_lep_pt_corr);
            float qcd_lep_mt_corr = qcd_lep_mt_closure->evaluate(
                {boosted_mt_1, qcd_corr_lepmt_variation});
            Logger::get("FakeFactor")
                ->debug("QCD - lep mt correction {}", qcd_lep_mt_corr);
            float qcd_DR_SR_corr = qcd_DR_SR->evaluate(
                {boosted_dR_ditau, qcd_corr_drsr_variation});
            Logger::get("FakeFactor")
                ->debug("QCD - DR to SR correction {}", qcd_DR_SR_corr);
            float wjets_lep_pt_corr = wjets_lep_pt_closure->evaluate(
                {boosted_pt_1, wjets_corr_leppt_variation});
            Logger::get("FakeFactor")
                ->debug("Wjets - lep pt correction {}", wjets_lep_pt_corr);
            float wjets_DR_SR_corr = wjets_DR_SR->evaluate(
                {boosted_dR_ditau, wjets_corr_drsr_variation});
            Logger::get("FakeFactor")
                ->debug("Wjets - DR to SR correction {}", wjets_DR_SR_corr);
            float ttbar_lep_pt_corr = ttbar_lep_pt_closure->evaluate(
                {boosted_pt_1, ttbar_corr_leppt_variation});
            Logger::get("FakeFactor")
                ->debug("ttbar - lep pt correction {}", ttbar_lep_pt_corr);
            // float ttbar_m_vis_corr =
            //     ttbar_m_vis_closure->evaluate({boosted_m_vis,
            //     variation});
            // Logger::get("FakeFactor")
            //     ->debug("ttbar - m_vis correction {}", ttbar_m_vis_corr);

            ff = qcd_frac * std::max(qcd_ff, (float)0.) * qcd_lep_pt_corr *
                     qcd_lep_mt_corr * qcd_DR_SR_corr +
                 wjets_frac * std::max(wjets_ff, (float)0.) *
                     wjets_lep_pt_corr * wjets_DR_SR_corr +
                 ttbar_frac * std::max(ttbar_ff, (float)0.) * ttbar_lep_pt_corr;
        }

        Logger::get("FakeFactor")->debug("Event Fake Factor {}", ff);
        return ff;
    };
    auto df1 = df.Define(outputname, calc_fake_factor,
                         {boosted_tau_pt, njets, boosted_lep_mt, nbtags,
                          boosted_lep_pt, boosted_m_vis, boosted_dR_ditau});
    return df1;
}
/**
 * @brief Function to calculate fake factors with correctionlib
 *
 * @param df the dataframe to add the quantity to
 * @param outputname name of the output column for the fake factor
 * @param tau_idx index of the tau, leading/subleading
 * @param tau_pt_1 pt of the leading hadronic tau in the tau pair
 * @param tau_pt_2 pt of the subleading hadronic tau in the tau pair
 * @param njets number of good jets in the event
 * @param m_vis visible mass of the tau pair
 * @param nbtag number of good b-tagged jets in the event
 * @param tau_mass_1 mass of the leading hadronic tau in the tau pair
 * @param tau_mass_2 mass of the subleading hadronic tau in the tau pair
 * @param qcd_variation name of the QCD FF uncertainty variation or nominal
 * @param ttbar_variation name of the ttbar FF uncertainty variation or
 * nominal
 * @param fraction_variation name of the process fraction uncertainty
 * variation or nominal
 * @param qcd_corr_leppt_variation name of the QCD lepton pt correction
 * uncertainty variation or nominal
 * @param qcd_corr_taumass_variation name of the QCD lepton mass correction
 * uncertainty variation or nominal
 * @param qcd_corr_drsr_variation name of the QCD DR to SR correction
 * uncertainty variation or nominal
 * @param ttbar_corr_leppt_variation name of the ttbar lepton pt correction
 * uncertainty variation or nominal
 * @param ttbar_corr_taumass_variation name of the ttbar lepton mass
 * correction uncertainty variation or nominal
 * @param ff_file correctionlib json file with the fake factors
 * @param ff_corr_file correctionlib json file with corrections for the fake
 * factors
 * @returns a dataframe with the fake factors
 */
ROOT::RDF::RNode fakefactor_nmssm_tt(
    ROOT::RDF::RNode df, const std::string &outputname, const int &tau_idx,
    const std::string &tau_pt_1, const std::string &tau_pt_2,
    const std::string &njets, const std::string &m_vis,
    const std::string &nbtag, const std::string &tau_mass_1,
    const std::string &tau_mass_2, const std::string &qcd_variation,
    const std::string &ttbar_variation, const std::string &fraction_variation,
    const std::string &qcd_corr_leppt_variation,
    const std::string &qcd_corr_taumass_variation,
    const std::string &qcd_corr_drsr_variation,
    const std::string &ttbar_corr_leppt_variation,
    const std::string &ttbar_corr_taumass_variation, const std::string &ff_file,
    const std::string &ff_corr_file) {

    Logger::get("FakeFactor")
        ->debug("Setting up functions for fake factor evaluation with "
                "correctionlib");
    Logger::get("FakeFactor")->debug("QCD variation - Name {}", qcd_variation);
    Logger::get("FakeFactor")
        ->debug("ttbar variation - Name {}", ttbar_variation);
    Logger::get("FakeFactor")
        ->debug("Fraction variation - Name {}", fraction_variation);
    Logger::get("FakeFactor")
        ->debug("QCD lepton pt variation - Name {}", qcd_corr_leppt_variation);
    Logger::get("FakeFactor")
        ->debug("QCD lepton mass variation - Name {}",
                qcd_corr_taumass_variation);
    Logger::get("FakeFactor")
        ->debug("QCD DRSR variation - Name {}", qcd_corr_drsr_variation);
    Logger::get("FakeFactor")
        ->debug("ttbar lepton pt variation - Name {}",
                ttbar_corr_leppt_variation);
    Logger::get("FakeFactor")
        ->debug("ttbar lepton mass variation - Name {}",
                ttbar_corr_taumass_variation);

    auto qcd =
        correction::CorrectionSet::from_file(ff_file)->at("QCD_fake_factors");
    auto qcd_subleading = correction::CorrectionSet::from_file(ff_file)->at(
        "QCD_subleading_fake_factors");
    auto ttbar =
        correction::CorrectionSet::from_file(ff_file)->at("ttbar_fake_factors");
    auto ttbar_subleading = correction::CorrectionSet::from_file(ff_file)->at(
        "ttbar_subleading_fake_factors");
    auto fractions =
        correction::CorrectionSet::from_file(ff_file)->at("process_fractions");
    auto fractions_subleading =
        correction::CorrectionSet::from_file(ff_file)->at(
            "process_fractions_subleading");
    auto qcd_tau_pt_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("QCD_non_closure_subleading_lep_pt_correction");
    auto qcd_tau_mass_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("QCD_non_closure_leading_lep_mass_correction");
    auto qcd_DR_SR = correction::CorrectionSet::from_file(ff_corr_file)
                         ->at("QCD_DR_SR_correction");
    auto ttbar_tau_pt_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("ttbar_non_closure_subleading_lep_pt_correction");
    auto ttbar_tau_mass_closure =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("ttbar_non_closure_leading_lep_mass_correction");
    auto qcd_tau_pt_closure_subleading =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("QCD_subleading_non_closure_leading_lep_pt_correction");
    auto qcd_tau_mass_closure_subleading =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("QCD_subleading_non_closure_subleading_lep_mass_"
                 "correction");
    auto qcd_DR_SR_subleading =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("QCD_subleading_DR_SR_correction");
    auto ttbar_tau_pt_closure_subleading =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("ttbar_subleading_non_closure_leading_lep_pt_correction");
    auto ttbar_tau_mass_closure_subleading =
        correction::CorrectionSet::from_file(ff_corr_file)
            ->at("ttbar_subleading_non_closure_subleading_lep_mass_"
                 "correction");

    auto calc_fake_factor = [tau_idx, qcd_variation, ttbar_variation,
                             fraction_variation, qcd_corr_leppt_variation,
                             qcd_corr_taumass_variation,
                             qcd_corr_drsr_variation,
                             ttbar_corr_leppt_variation,
                             ttbar_corr_taumass_variation, qcd, ttbar,
                             fractions, qcd_tau_pt_closure,
                             qcd_tau_mass_closure, qcd_DR_SR,
                             ttbar_tau_pt_closure, ttbar_tau_mass_closure,
                             qcd_subleading, ttbar_subleading,
                             fractions_subleading,
                             qcd_tau_pt_closure_subleading,
                             qcd_tau_mass_closure_subleading,
                             qcd_DR_SR_subleading,
                             ttbar_tau_pt_closure_subleading,
                             ttbar_tau_mass_closure_subleading](
                                const float &pt_1, const float &pt_2,
                                const int &njets, const float &m_vis,
                                const int &nbtag, const float &mass_1,
                                const float &mass_2) {
        float ff = 0.;
        if (pt_2 >= 0.) {
            Logger::get("FakeFactor")->debug("Leading Tau pt - value {}", pt_1);
            Logger::get("FakeFactor")
                ->debug("Subleading Tau pt - value {}", pt_2);
            Logger::get("FakeFactor")->debug("m_vis - value {}", m_vis);
            Logger::get("FakeFactor")->debug("N jets - value {}", njets);
            Logger::get("FakeFactor")->debug("N btag - value {}", nbtag);
            Logger::get("FakeFactor")
                ->debug("Leading Tau mass - value {}", mass_1);
            Logger::get("FakeFactor")
                ->debug("Subleading Tau mass - value {}", mass_2);

            float qcd_ff = -1.;
            float ttbar_ff = -1.;
            float qcd_frac = -1.;
            float wjets_frac = -1.;
            float ttbar_frac = -1.;
            float qcd_tau_pt_corr = -1.;
            float qcd_tau_mass_corr = -1.;
            float qcd_DR_SR_corr = -1.;
            float ttbar_tau_pt_corr = -1.;
            float ttbar_tau_mass_corr = -1.;
            if (tau_idx == 0) {
                qcd_ff = qcd->evaluate({pt_1, (float)njets, qcd_variation});
                Logger::get("FakeFactor")->debug("QCD - value {}", qcd_ff);
                ttbar_ff =
                    ttbar->evaluate({pt_1, (float)njets, ttbar_variation});
                Logger::get("FakeFactor")->debug("ttbar - value {}", ttbar_ff);
                qcd_frac = fractions->evaluate(
                    {"QCD", m_vis, (float)nbtag, fraction_variation});
                Logger::get("FakeFactor")->debug("QCD - fraction {}", qcd_frac);
                wjets_frac = fractions->evaluate(
                    {"Wjets", m_vis, (float)nbtag, fraction_variation});
                Logger::get("FakeFactor")
                    ->debug("Wjets - fraction {}", wjets_frac);
                ttbar_frac = fractions->evaluate(
                    {"ttbar", m_vis, (float)nbtag, fraction_variation});
                Logger::get("FakeFactor")
                    ->debug("ttbar - fraction {}", ttbar_frac);

                qcd_tau_pt_corr = qcd_tau_pt_closure->evaluate(
                    {pt_2, qcd_corr_leppt_variation});
                Logger::get("FakeFactor")
                    ->debug("QCD - lep pt correction {}", qcd_tau_pt_corr);
                qcd_tau_mass_corr = qcd_tau_mass_closure->evaluate(
                    {mass_1, qcd_corr_taumass_variation});
                Logger::get("FakeFactor")
                    ->debug("QCD - lep mass correction {}", qcd_tau_mass_corr);
                qcd_DR_SR_corr =
                    qcd_DR_SR->evaluate({m_vis, qcd_corr_drsr_variation});
                Logger::get("FakeFactor")
                    ->debug("QCD - DR to SR correction {}", qcd_DR_SR_corr);
                ttbar_tau_pt_corr = ttbar_tau_pt_closure->evaluate(
                    {pt_2, ttbar_corr_leppt_variation});
                Logger::get("FakeFactor")
                    ->debug("ttbar - lep pt correction {}", ttbar_tau_pt_corr);
                ttbar_tau_mass_corr = ttbar_tau_mass_closure->evaluate(
                    {mass_1, ttbar_corr_taumass_variation});
                Logger::get("FakeFactor")
                    ->debug("ttbar - lep mass correction {}",
                            ttbar_tau_mass_corr);

                ff = (qcd_frac + wjets_frac) * std::max(qcd_ff, (float)0.) *
                         qcd_tau_pt_corr * qcd_tau_mass_corr * qcd_DR_SR_corr +
                     ttbar_frac * std::max(ttbar_ff, (float)0.) *
                         ttbar_tau_pt_corr * ttbar_tau_mass_corr;
            } else if (tau_idx == 1) {
                qcd_ff = qcd_subleading->evaluate(
                    {pt_2, (float)njets, qcd_variation});
                Logger::get("FakeFactor")->debug("QCD - value {}", qcd_ff);
                ttbar_ff = ttbar_subleading->evaluate(
                    {pt_2, (float)njets, ttbar_variation});
                Logger::get("FakeFactor")->debug("ttbar - value {}", ttbar_ff);
                qcd_frac = fractions_subleading->evaluate(
                    {"QCD", m_vis, (float)nbtag, fraction_variation});
                Logger::get("FakeFactor")->debug("QCD - fraction {}", qcd_frac);
                wjets_frac = fractions_subleading->evaluate(
                    {"Wjets", m_vis, (float)nbtag, fraction_variation});
                Logger::get("FakeFactor")
                    ->debug("Wjets - fraction {}", wjets_frac);
                ttbar_frac = fractions_subleading->evaluate(
                    {"ttbar", m_vis, (float)nbtag, fraction_variation});
                Logger::get("FakeFactor")
                    ->debug("ttbar - fraction {}", ttbar_frac);

                qcd_tau_pt_corr = qcd_tau_pt_closure_subleading->evaluate(
                    {pt_1, qcd_corr_leppt_variation});
                Logger::get("FakeFactor")
                    ->debug("QCD - lep pt correction {}", qcd_tau_pt_corr);
                qcd_tau_mass_corr = qcd_tau_mass_closure_subleading->evaluate(
                    {mass_2, qcd_corr_taumass_variation});
                Logger::get("FakeFactor")
                    ->debug("QCD - lep mass correction {}", qcd_tau_mass_corr);
                qcd_DR_SR_corr = qcd_DR_SR_subleading->evaluate(
                    {m_vis, qcd_corr_drsr_variation});
                Logger::get("FakeFactor")
                    ->debug("QCD - DR to SR correction {}", qcd_DR_SR_corr);
                ttbar_tau_pt_corr = ttbar_tau_pt_closure_subleading->evaluate(
                    {pt_1, ttbar_corr_leppt_variation});
                Logger::get("FakeFactor")
                    ->debug("ttbar - lep pt correction {}", ttbar_tau_pt_corr);
                ttbar_tau_mass_corr =
                    ttbar_tau_mass_closure_subleading->evaluate(
                        {mass_2, ttbar_corr_taumass_variation});
                Logger::get("FakeFactor")
                    ->debug("ttbar - lep mass correction {}",
                            ttbar_tau_mass_corr);

                ff = (qcd_frac + wjets_frac) * std::max(qcd_ff, (float)0.) *
                         qcd_tau_pt_corr * qcd_tau_mass_corr * qcd_DR_SR_corr +
                     ttbar_frac * std::max(ttbar_ff, (float)0.) *
                         ttbar_tau_pt_corr * ttbar_tau_mass_corr;
            }
        }

        Logger::get("FakeFactor")->debug("Event Fake Factor {}", ff);
        return ff;
    };
    auto df1 = df.Define(
        outputname, calc_fake_factor,
        {tau_pt_1, tau_pt_2, njets, m_vis, nbtag, tau_mass_1, tau_mass_2});
    return df1;
}

} // end namespace fakefactors
