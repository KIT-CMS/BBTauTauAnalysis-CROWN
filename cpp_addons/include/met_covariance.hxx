#ifndef GUARDMETCOVARIANCE_HXX
#define GUARDMETCOVARIANCE_HXX

#include "ROOT/RDataFrame.hxx"
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

// namespace xyh
namespace xyh {

// namespace met_covariance
namespace met_covariance {

/**
 * @brief Whether a MET covariance matrix ((xx, xy), (xy, yy)) is usable: finite,
 * positive definite, and with both variances at most `sum_et`^2.
 *
 * The bound is physical: the variance of a MET component is a sum of squared
 * object resolutions, none of which exceeds the object's pT, so it cannot exceed
 * (sum of pT)^2 = sumEt^2. The Run-2 NanoAOD-v15 PuppiMET covariance breaks it in
 * about 1 % of the 2016 events (NaN, non-positive determinants, values up to
 * 1e14 GeV^2), never in 2017 or 2018.
 */
inline bool is_valid(const float &xx, const float &xy, const float &yy,
                     const float &sum_et) {
    if (!(std::isfinite(xx) && std::isfinite(xy) && std::isfinite(yy) &&
          std::isfinite(sum_et))) {
        return false;
    }
    const double bound = static_cast<double>(sum_et) * sum_et;
    const double det = static_cast<double>(xx) * yy -
                       static_cast<double>(xy) * xy;
    return xx > 0.0f && yy > 0.0f && det > 0.0 && xx <= bound && yy <= bound;
}

/// A covariance matrix and where it comes from
struct Covariance {
    float xx;
    float xy;
    float yy;
    // 0: primary, 1: fallback, 2: diagonal at the sumEt^2 bound
    int source;
};

/**
 * @brief The primary covariance if it is valid, else the fallback covariance if
 * that one is, else a diagonal covariance at the larger sumEt^2 bound of the two
 * (or 1e6 GeV^2 without a finite positive sumEt), which leaves the MET
 * unconstrained.
 */
inline Covariance select(const float &xx, const float &xy, const float &yy,
                         const float &sum_et, const float &fallback_xx,
                         const float &fallback_xy, const float &fallback_yy,
                         const float &fallback_sum_et) {
    if (is_valid(xx, xy, yy, sum_et)) {
        return {xx, xy, yy, 0};
    }
    if (is_valid(fallback_xx, fallback_xy, fallback_yy, fallback_sum_et)) {
        return {fallback_xx, fallback_xy, fallback_yy, 1};
    }
    float variance = 0.0f;
    for (const float value : {sum_et, fallback_sum_et}) {
        if (std::isfinite(value) && value > 0.0f) {
            variance = std::max(variance, value * value);
        }
    }
    if (!(std::isfinite(variance) && variance > 0.0f)) {
        variance = 1.0e6f;
    }
    return {variance, 0.0f, variance, 2};
}

// function xyh::met_covariance::Checked
ROOT::RDF::RNode Checked(ROOT::RDF::RNode df,
                         const std::vector<std::string> &outputs,
                         const std::string &xx, const std::string &xy,
                         const std::string &yy, const std::string &sum_et,
                         const std::string &fallback_xx,
                         const std::string &fallback_xy,
                         const std::string &fallback_yy,
                         const std::string &fallback_sum_et);

} // end namespace met_covariance

} // end namespace xyh

#endif // end GUARDMETCOVARIANCE_HXX
