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

} // end namespace fakefactors
