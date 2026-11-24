#include "../include/theory_weights.hxx"
#include "ROOT/RVec.hxx"
#include <algorithm>
#include <stdexcept>

namespace xyh::theory_weights {
ROOT::RDF::RNode CheckedSize(ROOT::RDF::RNode df, const std::string &outputname,
                             const std::string &weights,
                             const std::vector<int> &sizes) {
    if (sizes.empty() || std::any_of(sizes.begin(), sizes.end(),
                                     [](int size) { return size <= 0; })) {
        throw std::invalid_argument(
            "xyh::theory_weights::CheckedSize: needs the allowed lengths of " +
            weights + ", all positive");
    }
    std::string allowed;
    for (const int size : sizes) {
        allowed += (allowed.empty() ? "" : " or ") + std::to_string(size);
    }
    return df.Define(
        outputname,
        [sizes, weights, allowed](const ROOT::RVec<float> &values) {
            if (std::find(sizes.begin(), sizes.end(),
                          static_cast<int>(values.size())) == sizes.end()) {
                throw std::runtime_error(
                    "xyh::theory_weights::CheckedSize: " + weights + " has " +
                    std::to_string(values.size()) + " entries, expected " +
                    allowed);
            }
            return values;
        },
        {weights});
}
} // namespace xyh::theory_weights
