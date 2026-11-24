// Test of the parton shower weight (v8 spec C23): xyh::theory_weights::CheckedSize,
// which stops on a weight vector of another length, in front of the core
// event::reweighting::PartonShower, whose index per variation it pins.
//
// The Run-2 v15 NanoAOD files carry PSWeight = [ISR scale 2, FSR scale 2,
// ISR scale 0.5, FSR scale 0.5]. The checks:
//  - CheckedSize returns its input unchanged for an allowed length and throws
//    in the event loop for every other length, also where the weight read
//    from it is the nominal one (which the core function returns without
//    looking at the vector);
//  - PartonShower(isr, fsr) reads entry 0 for (2, 1), 1 for (1, 2), 2 for
//    (0.5, 1), 3 for (1, 0.5) and returns 1 for (1, 1): the shifts ps_isrUp,
//    ps_fsrUp, ps_isrDown and ps_fsrDown of the configuration;
//  - CheckedSize refuses an empty or non-positive list of lengths.

#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>

#include "utility/CorrectionManager.hxx"
// the core header (the addons have a reweighting.hxx of their own); it relies
// on the includes above
#include "../../../../include/reweighting.hxx"
#include "theory_weights.hxx"

#include <cstdio>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
int failures = 0;

void check(bool condition, const std::string &what) {
    if (!condition) {
        std::printf("FAIL: %s\n", what.c_str());
        ++failures;
    }
}

// one event with the weights `weights`: the value of the parton shower weight
// for (isr, fsr), read through CheckedSize with the allowed lengths `sizes`
float ps_weight(const ROOT::RVec<float> &weights, float isr, float fsr,
                const std::vector<int> &sizes) {
    ROOT::RDataFrame base(1);
    ROOT::RDF::RNode df = base.Define("PSWeight", [weights] { return weights; });
    df = xyh::theory_weights::CheckedSize(df, "PSWeight_checked", "PSWeight", sizes);
    df = event::reweighting::PartonShower(df, "ps_weight", "PSWeight_checked", isr, fsr);
    return df.Take<float>("ps_weight")->at(0);
}

bool throws_in_the_loop(const ROOT::RVec<float> &weights, float isr, float fsr,
                        const std::vector<int> &sizes) {
    try {
        ps_weight(weights, isr, fsr, sizes);
    } catch (const std::runtime_error &error) {
        return std::string(error.what()).find("CheckedSize") != std::string::npos;
    }
    return false;
}
} // namespace

int main() {
    const ROOT::RVec<float> weights{10.f, 20.f, 30.f, 40.f};
    check(ps_weight(weights, 1.f, 1.f, {4}) == 1.f, "the nominal weight is 1");
    check(ps_weight(weights, 2.f, 1.f, {4}) == 10.f, "ISR scale 2 reads entry 0");
    check(ps_weight(weights, 1.f, 2.f, {4}) == 20.f, "FSR scale 2 reads entry 1");
    check(ps_weight(weights, 0.5f, 1.f, {4}) == 30.f, "ISR scale 0.5 reads entry 2");
    check(ps_weight(weights, 1.f, 0.5f, {4}) == 40.f, "FSR scale 0.5 reads entry 3");

    // the copy is the input
    {
        ROOT::RDataFrame base(1);
        ROOT::RDF::RNode df = base.Define("w", [weights] { return weights; });
        df = xyh::theory_weights::CheckedSize(df, "checked", "w", {101, 4});
        const auto copy = df.Take<ROOT::RVec<float>>("checked")->at(0);
        check(copy.size() == 4 && ROOT::VecOps::All(copy == weights),
              "the checked column is a copy of the weights");
    }

    // other lengths stop the job, under a variation and in the nominal
    for (const std::size_t size : {0u, 1u, 2u, 3u, 5u, 8u, 44u, 46u}) {
        const ROOT::RVec<float> other(size, 1.f);
        check(throws_in_the_loop(other, 1.f, 1.f, {4}),
              "the nominal stops on " + std::to_string(size) + " weights");
        check(throws_in_the_loop(other, 2.f, 1.f, {4}),
              "a variation stops on " + std::to_string(size) + " weights");
    }
    // the lengths of the PDF weights of the signal samples
    for (const std::size_t size : {101u, 103u}) {
        check(!throws_in_the_loop(ROOT::RVec<float>(size, 1.f), 1.f, 1.f, {101, 103}),
              std::to_string(size) + " entries pass a check for 101 or 103");
    }
    for (const std::size_t size : {1u, 9u, 100u, 102u, 104u}) {
        check(throws_in_the_loop(ROOT::RVec<float>(size, 1.f), 1.f, 1.f, {101, 103}),
              std::to_string(size) + " entries fail a check for 101 or 103");
    }

    bool refused = true;
    for (const std::vector<int> &sizes :
         {std::vector<int>{}, std::vector<int>{0}, std::vector<int>{4, -1}}) {
        try {
            ROOT::RDataFrame base(1);
            ROOT::RDF::RNode df = base.Define("w", [weights] { return weights; });
            xyh::theory_weights::CheckedSize(df, "checked", "w", sizes);
            refused = false;
        } catch (const std::invalid_argument &) {
        }
    }
    check(refused, "an empty or non-positive list of lengths is refused");
    return failures == 0 ? 0 : 1;
}
