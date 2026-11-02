#ifndef GUARDMETCOVARIANCE_CXX
#define GUARDMETCOVARIANCE_CXX

#include "../include/met_covariance.hxx"
#include "ROOT/RDataFrame.hxx"
#include <stdexcept>
#include <string>
#include <vector>

// namespace xyh
namespace xyh {

// namespace met_covariance
namespace met_covariance {

/**
 * @brief The MET covariance matrix elements with a validity check and a
 * fallback, and a column that records which matrix was taken.
 *
 * The primary covariance (xx, xy, yy) is taken if it is finite, positive
 * definite and both variances are at most sumEt^2 (`is_valid`); otherwise the
 * fallback covariance if that one passes the same check; otherwise a diagonal
 * matrix at the sumEt^2 bound (no MET constraint). On the Run-2 NanoAOD-v15
 * inputs the primary is the PuppiMET covariance and the fallback the PF MET
 * covariance, which the Run-2 NanoAOD v9/v12 configurations used for all events.
 *
 * @param df The input data frame.
 * @param outputs The output columns: the elements 00, 01, 10, 11 (float) and
 * the source of the matrix (int; 0 primary, 1 fallback, 2 diagonal).
 * @param xx The xx element column of the primary covariance.
 * @param xy The xy element column of the primary covariance.
 * @param yy The yy element column of the primary covariance.
 * @param sum_et The scalar transverse energy sum of the primary MET.
 * @param fallback_xx The xx element column of the fallback covariance.
 * @param fallback_xy The xy element column of the fallback covariance.
 * @param fallback_yy The yy element column of the fallback covariance.
 * @param fallback_sum_et The scalar transverse energy sum of the fallback MET.
 * @return A new data frame with the five columns.
 */
ROOT::RDF::RNode Checked(ROOT::RDF::RNode df,
                         const std::vector<std::string> &outputs,
                         const std::string &xx, const std::string &xy,
                         const std::string &yy, const std::string &sum_et,
                         const std::string &fallback_xx,
                         const std::string &fallback_xy,
                         const std::string &fallback_yy,
                         const std::string &fallback_sum_et) {
    if (outputs.size() != 5) {
        throw std::invalid_argument(
            "xyh::met_covariance::Checked: expected the outputs 00, 01, 10, "
            "11 and the source, got " +
            std::to_string(outputs.size()) + " names");
    }
    const std::vector<std::string> inputs = {
        xx, xy, yy, sum_et, fallback_xx, fallback_xy, fallback_yy,
        fallback_sum_et};
    auto element = [](const int index) {
        return [index](const float &xx, const float &xy, const float &yy,
                       const float &sum_et, const float &fallback_xx,
                       const float &fallback_xy, const float &fallback_yy,
                       const float &fallback_sum_et) {
            const Covariance cov =
                select(xx, xy, yy, sum_et, fallback_xx, fallback_xy,
                       fallback_yy, fallback_sum_et);
            return index == 0 ? cov.xx : index == 3 ? cov.yy : cov.xy;
        };
    };
    auto source = [](const float &xx, const float &xy, const float &yy,
                     const float &sum_et, const float &fallback_xx,
                     const float &fallback_xy, const float &fallback_yy,
                     const float &fallback_sum_et) {
        return select(xx, xy, yy, sum_et, fallback_xx, fallback_xy,
                      fallback_yy, fallback_sum_et)
            .source;
    };
    return df.Define(outputs.at(0), element(0), inputs)
        .Define(outputs.at(1), element(1), inputs)
        .Define(outputs.at(2), element(2), inputs)
        .Define(outputs.at(3), element(3), inputs)
        .Define(outputs.at(4), source, inputs);
}

} // end namespace met_covariance

} // end namespace xyh

#endif // end GUARDMETCOVARIANCE_CXX
