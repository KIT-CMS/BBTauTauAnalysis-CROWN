// Test of xyh::energy_scale::ScalePt, the scope-level energy scale variation of
// the light leptons (v8 spec C32, C37).
//
// Usage: <binary> <n regions> <lower |eta| edges...> <n variations>
//                 <factors of variation 1...> <factors of variation 2...> ...
//
// The edges and the factors of every variation come from the configuration
// (nominal and each shift). The checks:
//  - with every factor at 1 the output is the input, bit for bit, also for
//    values that a multiplication by 1 would not reproduce (NaN payloads are
//    not compared, but denormals, infinities and negative zero are);
//  - a variation scales the pt of the objects of the regions with a factor
//    other than 1 by that factor and leaves every other object bit for bit;
//  - an object on an edge belongs to the region above it, objects above the
//    last edge to the last region, and objects below the first edge to none;
//  - malformed edges and factors are refused.

#include "energy_scale.hxx"

#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
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

bool same_bits(float a, float b) { return std::memcmp(&a, &b, sizeof(float)) == 0; }

ROOT::RVec<float> scaled(const ROOT::RVec<float> &pt, const ROOT::RVec<float> &eta,
                         const std::vector<float> &edges,
                         const std::vector<float> &factors) {
    ROOT::RDataFrame base(1);
    ROOT::RDF::RNode df = base.Define("pt", [pt] { return pt; })
                              .Define("eta", [eta] { return eta; });
    df = xyh::energy_scale::ScalePt(df, "out", "pt", "eta", edges, factors);
    return df.Take<ROOT::RVec<float>>("out")->at(0);
}

bool refused(const std::vector<float> &edges, const std::vector<float> &factors) {
    try {
        scaled({20.f}, {0.f}, edges, factors);
    } catch (const std::invalid_argument &) {
        return true;
    }
    return false;
}
} // namespace

int main(int argc, char **argv) {
    int arg = 1;
    auto next = [&]() {
        if (arg >= argc) {
            std::printf("too few arguments\n");
            std::exit(2);
        }
        return std::string(argv[arg++]);
    };
    const int n_regions = std::stoi(next());
    std::vector<float> edges;
    for (int i = 0; i < n_regions; ++i) {
        edges.push_back(std::stof(next()));
    }
    const int n_variations = std::stoi(next());
    std::vector<std::vector<float>> variations(n_variations);
    for (auto &factors : variations) {
        for (int i = 0; i < n_regions; ++i) {
            factors.push_back(std::stof(next()));
        }
    }

    // objects in the middle of every region, on every edge, just below every
    // edge, with both signs of eta, and far above the last edge
    ROOT::RVec<float> eta;
    for (int i = 0; i < n_regions; ++i) {
        const float low = edges[i];
        const float high = i + 1 < n_regions ? edges[i + 1] : edges[i] + 1.f;
        eta.push_back(0.5f * (low + high));
        eta.push_back(-0.5f * (low + high));
        eta.push_back(low);
        eta.push_back(-low);
        eta.push_back(std::nextafter(high, 0.f));
    }
    eta.push_back(edges.back() + 10.f);
    ROOT::RVec<float> pt;
    for (std::size_t i = 0; i < eta.size(); ++i) {
        pt.push_back(20.f + 7.3f * i);
    }
    auto region_of = [&](float value) {
        int region = -1;
        for (int i = 0; i < n_regions; ++i) {
            if (std::abs(value) >= edges[i]) {
                region = i;
            }
        }
        return region;
    };

    // nominal: every factor 1, on ordinary and on awkward values
    const std::vector<float> ones(n_regions, 1.f);
    ROOT::RVec<float> awkward{0.f, -0.f, 1e-42f, 3.4e38f,
                              std::numeric_limits<float>::infinity(), 33.333332f};
    ROOT::RVec<float> awkward_eta(awkward.size(), 0.5f * (edges[0] + 1.f));
    bool nominal_identical = true;
    const auto nominal = scaled(pt, eta, edges, ones);
    for (std::size_t i = 0; i < pt.size(); ++i) {
        nominal_identical = nominal_identical && same_bits(nominal[i], pt[i]);
    }
    const auto nominal_awkward = scaled(awkward, awkward_eta, edges, ones);
    for (std::size_t i = 0; i < awkward.size(); ++i) {
        nominal_identical =
            nominal_identical && same_bits(nominal_awkward[i], awkward[i]);
    }
    check(nominal.size() == pt.size() && nominal_identical,
          "with every factor at 1 the output is the input, bit for bit");

    // every variation of the configuration
    for (int v = 0; v < n_variations; ++v) {
        const auto &factors = variations[v];
        const auto out = scaled(pt, eta, edges, factors);
        bool ok = out.size() == pt.size();
        unsigned changed = 0;
        for (std::size_t i = 0; ok && i < pt.size(); ++i) {
            const int region = region_of(eta[i]);
            const float factor = region < 0 ? 1.f : factors[region];
            if (factor == 1.f) {
                ok = same_bits(out[i], pt[i]);
            } else {
                ok = out[i] == pt[i] * factor && out[i] != pt[i];
                ++changed;
            }
        }
        unsigned varied_regions = 0;
        for (float factor : factors) {
            varied_regions += factor != 1.f;
        }
        check(ok, "variation " + std::to_string(v) +
                      " scales the objects of its regions only");
        // five objects per region, and the one far above in the last region
        const unsigned expected =
            5 * varied_regions + (factors.back() != 1.f ? 1 : 0);
        check(varied_regions == 0 || changed == expected,
              "variation " + std::to_string(v) + " reaches every object of its regions");
    }

    // edges: below the first edge no region
    if (edges[0] > 0.f) {
        std::vector<float> all_up(n_regions, 1.1f);
        const auto out = scaled({50.f}, {0.5f * edges[0]}, edges, all_up);
        check(same_bits(out[0], 50.f), "objects below the first edge keep their pt");
    }
    check(refused({}, {}), "no region is refused");
    check(refused({0.f, 1.f}, {1.f}), "a missing factor is refused");
    check(refused({1.f, 0.5f}, {1.f, 1.f}), "descending edges are refused");
    check(refused({0.f, 0.f}, {1.f, 1.f}), "repeated edges are refused");
    check(refused({0.f}, {0.f}) && refused({0.f}, {-1.f}) &&
              refused({0.f}, {std::numeric_limits<float>::quiet_NaN()}),
          "factors that are not positive and finite are refused");
    return failures == 0 ? 0 : 1;
}
