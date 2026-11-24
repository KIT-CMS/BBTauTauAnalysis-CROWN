// Test of xyh::scalefactor::tau_trigger_per_decay_mode, the tau trigger scale
// factor with variations per decay mode (v8 spec C39), on the pinned TAU
// payload of an era.
//
// Usage: <binary> <tau.json.gz> <correction> <trigger name> <working point>
//
// The checks, against direct evaluations of the correction:
//  - "nom", "up" and "down" give what physicsobject::tau::scalefactor::Trigger
//    gives: 1 without the trigger flag, with a negative pt or where the
//    correction throws (below its lowest pt edge), else the correction at
//    (pt, decay mode), bit for bit;
//  - "<up|down>_dm<DM>" gives the varied value for taus of decay mode DM and
//    the nominal value for every other tau, so that the four variations of a
//    direction together reproduce the coherent variation;
//  - the varied value differs from the nominal one where the trigger fired
//    and the correction has a value;
//  - other variation names are refused.

#include "tau_trigger_sf.hxx"
#include "utility/CorrectionManager.hxx"

#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
#include <correction.h>
#include <cstdio>
#include <cstring>
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

struct Tau {
    float pt;
    int decay_mode;
    bool flag;
};
} // namespace

int main(int argc, char **argv) {
    if (argc != 5) {
        std::printf("usage: %s <tau.json.gz> <correction> <trigger> <wp>\n", argv[0]);
        return 2;
    }
    const std::string payload = argv[1], name = argv[2], trigger = argv[3],
                      wp = argv[4];
    const std::vector<int> decay_modes{0, 1, 10, 11};
    std::vector<Tau> taus;
    for (int decay_mode : decay_modes) {
        for (float pt : {20.f, 36.f, 41.5f, 55.f, 80.f, 150.f, 400.f}) {
            taus.push_back({pt, decay_mode, true});
        }
        taus.push_back({60.f, decay_mode, false});
        taus.push_back({-10.f, decay_mode, true});
    }

    ROOT::RDataFrame base(taus.size());
    ROOT::RDF::RNode df =
        base.Define("pt", [taus](ULong64_t e) { return taus[e].pt; }, {"rdfentry_"})
            .Define("dm", [taus](ULong64_t e) { return taus[e].decay_mode; },
                    {"rdfentry_"})
            .Define("flag", [taus](ULong64_t e) { return taus[e].flag; },
                    {"rdfentry_"});
    correctionManager::CorrectionManager manager;
    std::vector<std::string> variations{"nom", "up", "down"};
    for (const std::string direction : {"up", "down"}) {
        for (int decay_mode : decay_modes) {
            variations.push_back(direction + "_dm" + std::to_string(decay_mode));
        }
    }
    for (const auto &variation : variations) {
        df = xyh::scalefactor::tau_trigger_per_decay_mode(
            df, manager, "sf_" + variation, "pt", "dm", "flag", payload, name,
            trigger, wp, "sf", variation);
    }
    std::vector<ROOT::RDF::RResultPtr<std::vector<float>>> results;
    for (const auto &variation : variations) {
        results.push_back(df.Take<float>("sf_" + variation));
    }

    auto correction = correction::CorrectionSet::from_file(payload)->at(name);
    // the correction at a tau, and whether it has a value there
    auto defined = [&](const Tau &tau) {
        try {
            correction->evaluate({tau.pt, tau.decay_mode, trigger, wp,
                                  std::string("sf"), std::string("nom")});
        } catch (const std::runtime_error &) {
            return false;
        }
        return true;
    };
    auto direct = [&](const Tau &tau, const std::string &syst) {
        if (!(tau.pt >= 0.) || !tau.flag || !defined(tau)) {
            return 1.f;
        }
        return static_cast<float>(correction->evaluate(
            {tau.pt, tau.decay_mode, trigger, wp, std::string("sf"), syst}));
    };
    unsigned varied = 0, fired = 0, undefined = 0;
    for (const auto &tau : taus) {
        undefined += tau.flag && tau.pt >= 0. && !defined(tau);
    }
    for (std::size_t v = 0; v < variations.size(); ++v) {
        const std::string &variation = variations[v];
        const auto separator = variation.find("_dm");
        const std::string direction = variation.substr(0, separator);
        const int varied_dm = separator == std::string::npos
                                  ? -1
                                  : std::stoi(variation.substr(separator + 3));
        bool ok = true;
        for (std::size_t i = 0; i < taus.size(); ++i) {
            const bool in_scope = varied_dm < 0 || taus[i].decay_mode == varied_dm;
            const float expected = direct(taus[i], in_scope ? direction : "nom");
            ok = ok && same_bits((*results[v])[i], expected);
            if (direction != "nom" && varied_dm >= 0 && in_scope &&
                taus[i].flag && taus[i].pt >= 0. && defined(taus[i])) {
                ++fired;
                varied += (*results[v])[i] != direct(taus[i], "nom");
            }
        }
        check(ok, "variation " + variation + " is the correction at the tau, "
                                             "varied for its decay mode only");
    }
    std::printf("%u taus below the pt range of the correction, %u of %u varied "
                "scale factors differ from the nominal\n",
                undefined, varied, fired);
    // at least the five pt values from 41.5 GeV on per decay mode and direction
    check(fired >= 2 * 4 * 5 && varied == fired,
          "a variation of a decay mode changes the scale factor of its taus");

    bool refused = true;
    for (const std::string bad : {"up_dm2", "up_dm", "nominal", "upward", "up_dm0_pt20"}) {
        try {
            xyh::scalefactor::tau_trigger_per_decay_mode(
                df, manager, "bad_" + bad, "pt", "dm", "flag", payload, name,
                trigger, wp, "sf", bad);
            refused = false;
        } catch (const std::invalid_argument &) {
        }
    }
    check(refused, "other variation names are refused");
    return failures == 0 ? 0 : 1;
}
