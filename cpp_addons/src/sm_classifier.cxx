#include "../include/sm_classifier.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <algorithm>
#include <cctype>
#include <stdexcept>
#include <string>
#include <vector>

namespace xyh {

namespace classifier {

ROOT::RDF::RNode SelectionFlag(ROOT::RDF::RNode df, const std::string &output,
                               const std::string &expression,
                               const std::vector<std::string> &columns) {
    std::string code;
    for (size_t i = 0; i < expression.size(); ++i) {
        if (expression[i] != '$') {
            code += expression[i];
            continue;
        }
        size_t end = i + 1;
        while (end < expression.size() && std::isdigit(expression[end])) {
            ++end;
        }
        if (end == i + 1) {
            throw std::invalid_argument("SelectionFlag: '$' without a column "
                                        "index in " +
                                        expression);
        }
        const auto index = std::stoul(expression.substr(i + 1, end - i - 1));
        if (index >= columns.size()) {
            throw std::out_of_range(
                "SelectionFlag: column $" + std::to_string(index) + " of " +
                std::to_string(columns.size()) + " in " + expression);
        }
        code += columns[index];
        i = end - 1;
    }
    Logger::get("xyh::classifier::SelectionFlag")
        ->debug("Define {} as {}", output, code);
    return df.Define(output, "static_cast<bool>(" + code + ")");
}

ROOT::RDF::RNode UnpackScores(ROOT::RDF::RNode df,
                              const std::vector<std::string> &outputs,
                              const std::string &scores,
                              const int &num_classes) {
    if (num_classes < 1 || outputs.size() < 2 + size_t(num_classes)) {
        throw std::invalid_argument(
            "UnpackScores: " + std::to_string(outputs.size()) +
            " output columns for " + std::to_string(num_classes) + " classes");
    }
    const size_t num_scores = outputs.size() - 2;
    auto check = [num_scores](const ROOT::RVec<float> &values) {
        if (values.size() != num_scores) {
            throw std::runtime_error(
                "UnpackScores: " + std::to_string(values.size()) +
                " scores, expected " + std::to_string(num_scores));
        }
    };
    auto predicted_class = [check,
                            num_classes](const ROOT::RVec<float> &values) {
        if (values.empty()) {
            return -1;
        }
        check(values);
        return static_cast<int>(
            std::max_element(values.begin(), values.begin() + num_classes) -
            values.begin());
    };
    auto predicted_max_value = [check,
                                num_classes](const ROOT::RVec<float> &values) {
        if (values.empty()) {
            return -1.f;
        }
        check(values);
        return *std::max_element(values.begin(), values.begin() + num_classes);
    };
    ROOT::RDF::RNode result =
        df.Define(outputs[0], predicted_class, {scores})
            .Define(outputs[1], predicted_max_value, {scores});
    for (size_t i = 0; i < num_scores; ++i) {
        result = result.Define(outputs[2 + i],
                               [i](const ROOT::RVec<float> &values) {
                                   return values.empty() ? -1.f : values[i];
                               },
                               {scores});
    }
    return result;
}

} // namespace classifier

} // namespace xyh
