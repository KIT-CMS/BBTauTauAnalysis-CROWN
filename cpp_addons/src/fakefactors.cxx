#include "../../../../include/utility/CorrectionManager.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "ROOT/RDataFrame.hxx"
#include "correction.h"
#include <algorithm>
#include <functional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
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
// Fake factor of one tau leg, summed over the processes of the payload
// ----------------------------------------------------------------------------

ROOT::RDF::RNode FakeFactor(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correctionManager,
    const std::string &outputname, const std::vector<std::string> &inputs,
    const std::vector<std::string> &processes, const std::string &ff_file,
    const std::vector<std::string> &ff_names, const std::string &fraction_name,
    const std::string &corr_file, const std::vector<std::string> &corr_names,
    const std::vector<std::string> &corr_processes,
    const std::vector<int> &corr_compound,
    const std::vector<std::string> &ff_variations,
    const std::string &fraction_variation,
    const std::vector<std::string> &corr_variations) {
    const std::string logger_name = "fakefactors::xyh::FakeFactor";
    const std::size_t n_processes = processes.size();
    const std::size_t n_corrections = corr_names.size();

    // The layout: one fake factor per process, one process per correction,
    // and the inputs of the fractions, the fake factors and the corrections.
    if (n_processes == 0 || ff_names.size() != n_processes ||
        ff_variations.size() != n_processes) {
        throw std::invalid_argument(
            logger_name + ": " + outputname + " needs one fake factor and one "
            "variation per process, got " + std::to_string(n_processes) +
            " processes, " + std::to_string(ff_names.size()) +
            " fake factors and " + std::to_string(ff_variations.size()) +
            " variations");
    }
    if (corr_processes.size() != n_corrections ||
        corr_compound.size() != n_corrections ||
        corr_variations.size() != n_corrections) {
        throw std::invalid_argument(
            logger_name + ": " + outputname + " needs a process, a kind and a "
            "variation for each of its " + std::to_string(n_corrections) +
            " corrections");
    }
    if (inputs.size() != 1 + n_processes + n_corrections) {
        throw std::invalid_argument(
            logger_name + ": " + outputname + " needs " +
            std::to_string(1 + n_processes + n_corrections) +
            " input columns, got " + std::to_string(inputs.size()));
    }
    std::vector<std::size_t> corr_process_index;
    for (const auto &process : corr_processes) {
        const auto found =
            std::find(processes.begin(), processes.end(), process);
        if (found == processes.end()) {
            throw std::invalid_argument(logger_name + ": a correction of " +
                                        outputname + " belongs to process " +
                                        process + ", which is not summed");
        }
        corr_process_index.push_back(found - processes.begin());
    }

    // Load the correction sets once
    Logger::get(logger_name)
        ->debug("Loading the fake factors of {} and {} corrections for {}",
                fmt::join(processes, ", "), n_corrections, outputname);
    auto fractions_cset =
        correctionManager.loadCorrection(ff_file, fraction_name);
    std::vector<const correction::Correction *> ff_csets;
    for (const auto &name : ff_names) {
        ff_csets.push_back(correctionManager.loadCorrection(ff_file, name));
    }
    using Inputs = std::vector<correction::Variable::Type>;
    std::vector<std::function<double(const Inputs &)>> corr_evaluators;
    for (std::size_t c = 0; c < n_corrections; ++c) {
        if (corr_compound.at(c)) {
            auto cset = correctionManager.loadCompoundCorrection(
                corr_file, corr_names.at(c));
            corr_evaluators.push_back(
                [cset](const Inputs &values) { return cset->evaluate(values); });
        } else {
            auto cset =
                correctionManager.loadCorrection(corr_file, corr_names.at(c));
            corr_evaluators.push_back(
                [cset](const Inputs &values) { return cset->evaluate(values); });
        }
    }

    // All input vectors in one column, in the order of `inputs`
    using Packed = std::vector<std::vector<float>>;
    std::string packed = outputname + "_ff_inputs_0";
    auto df1 = df.Define(
        packed, [](const std::vector<float> &values) { return Packed{values}; },
        {inputs.at(0)});
    for (std::size_t i = 1; i < inputs.size(); ++i) {
        const std::string next = outputname + "_ff_inputs_" + std::to_string(i);
        df1 = df1.Define(
            next,
            [](const Packed &previous, const std::vector<float> &values) {
                Packed result = previous;
                result.push_back(values);
                return result;
            },
            {packed, inputs.at(i)});
        packed = next;
    }

    auto fake_factor = [logger_name, processes, fractions_cset, ff_csets,
                        corr_evaluators, corr_process_index, ff_variations,
                        fraction_variation, corr_variations, n_processes,
                        n_corrections](const Packed &values) {
        // fake factor of each process times its corrections, in float as the
        // former two-process function
        std::vector<float> products(n_processes);
        for (std::size_t p = 0; p < n_processes; ++p) {
            products[p] = ff_csets[p]->evaluate(fakefactors::util::prepare_ff_input(
                values[1 + p], ff_variations[p]));
        }
        for (std::size_t c = 0; c < n_corrections; ++c) {
            const float correction =
                corr_evaluators[c](fakefactors::util::prepare_ff_input(
                    values[1 + n_processes + c], corr_variations[c]));
            products[corr_process_index[c]] *= correction;
        }
        // sum over the processes, weighted with their fractions
        float ff = 0.f;
        for (std::size_t p = 0; p < n_processes; ++p) {
            const float fraction = fractions_cset->evaluate(
                fakefactors::util::prepare_fractions_input(
                    values[0], processes[p], fraction_variation));
            const float term = fraction * std::max(products[p], 0.f);
            Logger::get(logger_name)
                ->debug("    {}: fraction {}, fake factor {}", processes[p],
                        fraction, products[p]);
            ff = p == 0 ? term : ff + term;
        }
        Logger::get(logger_name)->debug("Calculated fake factor {}", ff);
        return ff;
    };

    return df1.Define(outputname, fake_factor, {packed});
}

} // namespace xyh

} // end namespace fakefactors
