// Test of the checked MET covariance xyh::met_covariance::Checked (the Run-2
// NanoAOD-v15 PuppiMET covariance with the PF MET covariance as fallback): the
// validity check (finite, positive definite, variances at most sumEt^2), the
// fallback order, the diagonal last resort, and the columns on an RDataFrame
// with the v15 column types.

#include "met_covariance.hxx"

#include <ROOT/RDataFrame.hxx>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

void check(bool ok, const std::string &name) {
    std::cout << (ok ? "PASS " : "FAIL ") << name << std::endl;
    if (!ok) {
        ++g_failures;
    }
}

using xyh::met_covariance::is_valid;
using xyh::met_covariance::select;

constexpr float kNaN = std::numeric_limits<float>::quiet_NaN();
constexpr float kInf = std::numeric_limits<float>::infinity();

struct Event {
    float xx, xy, yy, sum_et, pf_xx, pf_xy, pf_yy, pf_sum_et;
};

} // namespace

int main() {
    // validity check
    check(is_valid(400.f, 50.f, 300.f, 500.f), "regular matrix is valid");
    check(is_valid(250000.f, 0.f, 250000.f, 500.f),
          "variances equal to sumEt^2 are valid");
    check(!is_valid(250001.f, 0.f, 100.f, 500.f), "xx above sumEt^2 is invalid");
    check(!is_valid(100.f, 0.f, 250001.f, 500.f), "yy above sumEt^2 is invalid");
    check(!is_valid(kNaN, 0.f, 100.f, 500.f), "NaN element is invalid");
    check(!is_valid(100.f, kInf, 100.f, 500.f), "infinite element is invalid");
    check(!is_valid(100.f, 0.f, 100.f, kNaN), "NaN sumEt is invalid");
    check(!is_valid(100.f, 100.f, 100.f, 500.f), "zero determinant is invalid");
    check(!is_valid(100.f, 150.f, 100.f, 500.f),
          "negative determinant is invalid");
    check(!is_valid(-100.f, 0.f, -100.f, 500.f),
          "negative definite (positive determinant) is invalid");
    check(!is_valid(0.f, 0.f, 100.f, 500.f), "zero variance is invalid");
    // a 2016 value of the v15 files
    check(!is_valid(6.6e14f, 1.0e3f, 2.0e3f, 300.f), "1e14 GeV^2 is invalid");

    // fallback order
    auto primary = select(400.f, 50.f, 300.f, 500.f, 900.f, 10.f, 800.f, 600.f);
    check(primary.source == 0 && primary.xx == 400.f && primary.xy == 50.f &&
              primary.yy == 300.f,
          "valid primary is kept");
    auto fallback = select(kNaN, 50.f, 300.f, 500.f, 900.f, 10.f, 800.f, 600.f);
    check(fallback.source == 1 && fallback.xx == 900.f && fallback.xy == 10.f &&
              fallback.yy == 800.f,
          "invalid primary takes the fallback");
    auto diagonal =
        select(kNaN, 0.f, 300.f, 500.f, 900.f, 900.f, 900.f, 600.f);
    check(diagonal.source == 2 && diagonal.xx == 360000.f &&
              diagonal.xy == 0.f && diagonal.yy == 360000.f,
          "both invalid: diagonal at the larger sumEt^2");
    auto constant = select(kNaN, 0.f, 300.f, kNaN, kNaN, 0.f, 1.f, -1.f);
    check(constant.source == 2 && constant.xx == 1.0e6f && constant.yy == 1.0e6f,
          "both invalid without a sumEt: diagonal 1e6 GeV^2");

    // columns on an RDataFrame
    const std::vector<Event> events = {
        {400.f, 50.f, 300.f, 500.f, 900.f, 10.f, 800.f, 600.f},
        {7.7e9f, 2.0e3f, 3.0e3f, 250.f, 900.f, 10.f, 800.f, 600.f},
        {100.f, 150.f, 100.f, 500.f, 900.f, 10.f, 800.f, 600.f},
    };
    ROOT::RDataFrame df(events.size());
    auto column = [&events](float Event::*member) {
        return [&events, member](ULong64_t entry) {
            return events.at(entry).*member;
        };
    };
    auto node = df.Define("PuppiMET_covXX", column(&Event::xx), {"rdfentry_"})
                    .Define("PuppiMET_covXY", column(&Event::xy), {"rdfentry_"})
                    .Define("PuppiMET_covYY", column(&Event::yy), {"rdfentry_"})
                    .Define("PuppiMET_sumEt", column(&Event::sum_et),
                            {"rdfentry_"})
                    .Define("PFMET_covXX", column(&Event::pf_xx), {"rdfentry_"})
                    .Define("PFMET_covXY", column(&Event::pf_xy), {"rdfentry_"})
                    .Define("PFMET_covYY", column(&Event::pf_yy), {"rdfentry_"})
                    .Define("PFMET_sumEt", column(&Event::pf_sum_et),
                            {"rdfentry_"});
    auto result = xyh::met_covariance::Checked(
        node, {"metcov00", "metcov01", "metcov10", "metcov11", "metcov_source"},
        "PuppiMET_covXX", "PuppiMET_covXY", "PuppiMET_covYY", "PuppiMET_sumEt",
        "PFMET_covXX", "PFMET_covXY", "PFMET_covYY", "PFMET_sumEt");
    auto c00 = result.Take<float>("metcov00");
    auto c01 = result.Take<float>("metcov01");
    auto c10 = result.Take<float>("metcov10");
    auto c11 = result.Take<float>("metcov11");
    auto source = result.Take<int>("metcov_source");
    check(*source == std::vector<int>({0, 1, 1}), "source column 0, 1, 1");
    check(*c00 == std::vector<float>({400.f, 900.f, 900.f}), "metcov00");
    check(*c01 == std::vector<float>({50.f, 10.f, 10.f}) && *c10 == *c01,
          "metcov01 = metcov10");
    check(*c11 == std::vector<float>({300.f, 800.f, 800.f}), "metcov11");

    bool threw = false;
    try {
        xyh::met_covariance::Checked(node, {"a", "b"}, "PuppiMET_covXX",
                                     "PuppiMET_covXY", "PuppiMET_covYY",
                                     "PuppiMET_sumEt", "PFMET_covXX",
                                     "PFMET_covXY", "PFMET_covYY", "PFMET_sumEt");
    } catch (const std::invalid_argument &) {
        threw = true;
    }
    check(threw, "wrong number of outputs throws");

    std::cout << (g_failures == 0 ? "ALL PASS" : "FAILURES") << std::endl;
    return g_failures == 0 ? 0 : 1;
}
