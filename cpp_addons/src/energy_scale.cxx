#include "../include/energy_scale.hxx"
#include "ROOT/RVec.hxx"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace xyh::energy_scale {
ROOT::RDF::RNode ScalePt(ROOT::RDF::RNode df, const std::string &outputname,
                         const std::string &pt, const std::string &eta,
                         const std::vector<float> &abs_eta_edges,
                         const std::vector<float> &factors) {
    const bool ascending =
        std::adjacent_find(abs_eta_edges.begin(), abs_eta_edges.end(),
                           [](float lower, float upper) {
                               return !(lower < upper);
                           }) == abs_eta_edges.end();
    const bool valid_factors =
        std::all_of(factors.begin(), factors.end(), [](float factor) {
            return std::isfinite(factor) && factor > 0.f;
        });
    if (abs_eta_edges.empty() || factors.size() != abs_eta_edges.size() ||
        !ascending || !valid_factors) {
        throw std::invalid_argument(
            "xyh::energy_scale::ScalePt: needs strictly ascending |eta| edges "
            "and one positive finite factor per edge");
    }
    // The nominal: the input column, bit for bit
    if (std::all_of(factors.begin(), factors.end(),
                    [](float factor) { return factor == 1.f; })) {
        return df.Define(
            outputname, [](const ROOT::RVec<float> &pt) { return pt; }, {pt});
    }
    return df.Define(
        outputname,
        [abs_eta_edges, factors](const ROOT::RVec<float> &pt,
                                 const ROOT::RVec<float> &eta) {
            ROOT::RVec<float> scaled(pt);
            for (std::size_t i = 0; i < pt.size(); ++i) {
                // the region whose lower edge is the last one not above |eta|
                const auto upper =
                    std::upper_bound(abs_eta_edges.begin(), abs_eta_edges.end(),
                                     std::abs(eta[i]));
                if (upper == abs_eta_edges.begin()) {
                    continue;
                }
                const float factor =
                    factors[upper - abs_eta_edges.begin() - 1];
                if (factor != 1.f) {
                    scaled[i] = pt[i] * factor;
                }
            }
            return scaled;
        },
        {pt, eta});
}
} // namespace xyh::energy_scale
