// Test of the 2018 HEM 15/16 event flag xyh::vetoes::hem_veto (v7 spec E29, C20):
// the region edges in eta, phi and pT, the TightLeptonVeto ID, the first affected
// run, the deterministic luminosity fraction of simulated events, and the flag
// on an RDataFrame with the v15 column types.

#include "hem_veto.hxx"

#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
#include <cmath>
#include <functional>
#include <iostream>
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

// the configuration of common_config.add_hem_veto_config
constexpr float kMinPt = 15.0f, kMinEta = -3.0f, kMaxEta = -1.3f,
                kMinPhi = -1.57f, kMaxPhi = -0.87f;
constexpr int kIdWp = 6;
constexpr unsigned int kFirstRun = 319077;
constexpr double kFraction = 0.647719;

bool in_region(float pt, float eta, float phi, int id) {
    return xyh::vetoes::hem::jet_in_region(pt, eta, phi, id, kMinPt, kIdWp,
                                           kMinEta, kMaxEta, kMinPhi, kMaxPhi);
}

struct Event {
    unsigned int run;
    unsigned int lumi;
    unsigned long long event;
    std::vector<float> pt, eta, phi;
    std::vector<int> id;
};

std::vector<bool> flags(const std::vector<Event> &events, bool by_run,
                        double fraction) {
    ROOT::RDataFrame df(events.size());
    auto at = [events](ULong64_t entry) { return events.at(entry); };
    auto node =
        df.Define("Jet_correctedPt",
                  [at](ULong64_t e) { return ROOT::RVec<float>(at(e).pt); },
                  {"rdfentry_"})
            .Define("Jet_eta",
                    [at](ULong64_t e) { return ROOT::RVec<float>(at(e).eta); },
                    {"rdfentry_"})
            .Define("Jet_phi",
                    [at](ULong64_t e) { return ROOT::RVec<float>(at(e).phi); },
                    {"rdfentry_"})
            .Define("Jet_ID",
                    [at](ULong64_t e) { return ROOT::RVec<int>(at(e).id); },
                    {"rdfentry_"})
            .Define("run", [at](ULong64_t e) { return UInt_t(at(e).run); },
                    {"rdfentry_"})
            .Define("luminosityBlock",
                    [at](ULong64_t e) { return UInt_t(at(e).lumi); },
                    {"rdfentry_"})
            .Define("event",
                    [at](ULong64_t e) { return ULong64_t(at(e).event); },
                    {"rdfentry_"});
    auto flagged = xyh::vetoes::hem_veto(
        node, "hem_veto", "Jet_correctedPt", "Jet_eta", "Jet_phi", "Jet_ID",
        "run", "luminosityBlock", "event", by_run, kMinPt, kIdWp, kMinEta,
        kMaxEta, kMinPhi, kMaxPhi, kFirstRun, fraction);
    auto values = flagged.Take<bool>("hem_veto").GetValue();
    return std::vector<bool>(values.begin(), values.end());
}

} // namespace

int main() {
    // --- region of a loose jet ------------------------------------------------
    check(in_region(30.f, -2.0f, -1.2f, 6), "jet in the region is flagged");
    check(!in_region(15.0f, -2.0f, -1.2f, 6) && in_region(15.01f, -2.0f, -1.2f, 6),
          "pT edge 15 GeV (above only)");
    check(!in_region(30.f, -2.0f, -1.2f, 2) && !in_region(30.f, -2.0f, -1.2f, 0),
          "TightLeptonVeto ID required (2: tight only)");
    check(!in_region(30.f, -3.0f, -1.2f, 6) && in_region(30.f, -2.999f, -1.2f, 6),
          "eta edge -3.0 (inside only)");
    check(!in_region(30.f, -1.3f, -1.2f, 6) && in_region(30.f, -1.301f, -1.2f, 6),
          "eta edge -1.3 (inside only)");
    check(!in_region(30.f, 2.0f, -1.2f, 6), "positive eta is not flagged");
    check(!in_region(30.f, -2.0f, -1.57f, 6) &&
              in_region(30.f, -2.0f, -1.569f, 6),
          "phi edge -1.57 (inside only)");
    check(!in_region(30.f, -2.0f, -0.87f, 6) &&
              in_region(30.f, -2.0f, -0.871f, 6),
          "phi edge -0.87 (inside only)");
    check(!in_region(30.f, -2.0f, 1.2f, 6), "positive phi is not flagged");

    // --- affected period --------------------------------------------------------
    using xyh::vetoes::hem::affected_period;
    check(!affected_period(true, 319076, 1, 1, kFirstRun, kFraction) &&
              affected_period(true, 319077, 1, 1, kFirstRun, kFraction) &&
              affected_period(true, 325000, 1, 1, kFirstRun, kFraction),
          "data and embedding: runs from 319077 on");
    std::size_t affected = 0, total = 0, sequential = 0, differs = 0;
    for (unsigned int lumi = 1; lumi <= 200; ++lumi) {
        for (unsigned long long event = 1; event <= 5000; ++event) {
            const bool a = affected_period(false, 1, lumi, event, kFirstRun,
                                           kFraction);
            affected += a;
            ++total;
            differs += a != affected_period(false, 1, lumi + 1000, event,
                                            kFirstRun, kFraction);
        }
    }
    for (unsigned long long event = 1; event <= 2000; ++event) {
        sequential += affected_period(false, 1, 7, event, kFirstRun, kFraction);
    }
    const double share = double(affected) / total;
    check(std::abs(share - kFraction) < 0.002,
          "MC: the luminosity fraction of the events (" +
              std::to_string(share) + ")");
    check(std::abs(sequential / 2000.0 - kFraction) < 0.04,
          "MC: also for the consecutive event numbers of one block");
    check(differs > total / 3,
          "MC: equal event numbers of other blocks fall independently");
    check(affected_period(false, 1, 3, 42, kFirstRun, kFraction) ==
              affected_period(false, 1, 3, 42, kFirstRun, kFraction),
          "MC: deterministic");
    bool extremes = true;
    for (unsigned long long event = 1; event <= 1000; ++event) {
        extremes = extremes &&
                   !affected_period(false, 1, 1, event, kFirstRun, 0.0) &&
                   affected_period(false, 1, 1, event, kFirstRun, 1.0);
    }
    check(extremes, "MC: fraction 0 never, 1 always");
    const double u = xyh::vetoes::hem::event_uniform(4294967295u, 4294967295u,
                                                     ~0ULL);
    check(u >= 0.0 && u < 1.0, "MC: the event number maps into [0, 1)");

    // --- the flag on a data frame ----------------------------------------------
    const std::vector<Event> events = {
        {319077, 1, 1, {30.f}, {-2.0f}, {-1.2f}, {6}},          // in region
        {319076, 1, 2, {30.f}, {-2.0f}, {-1.2f}, {6}},          // before
        {320000, 1, 3, {30.f}, {-1.2f}, {-1.2f}, {6}},          // eta outside
        {320000, 1, 4, {30.f}, {-2.0f}, {-1.2f}, {2}},          // tight only
        {320000, 1, 5, {40.f, 20.f}, {0.5f, -2.5f}, {0.f, -1.0f}, {6, 6}},
        {320000, 1, 6, {}, {}, {}, {}},                          // no jets
        {320000, 1, 7, {10.f}, {-2.0f}, {-1.2f}, {6}},          // below 15 GeV
    };
    const std::vector<bool> data = {true, false, false, false, true, false, false};
    check(flags(events, true, kFraction) == data,
          "data frame: data and embedding by run");
    const std::vector<bool> all = {true, true, false, false, true, false, false};
    check(flags(events, false, 1.0) == all, "data frame: MC, fraction 1");
    check(flags(events, false, 0.0) == std::vector<bool>(events.size(), false),
          "data frame: MC, fraction 0");
    bool threw = false;
    try {
        flags(events, false, 1.5);
    } catch (const std::invalid_argument &) {
        threw = true;
    }
    check(threw, "a fraction outside [0, 1] throws");

    if (g_failures > 0) {
        std::cerr << g_failures << " case(s) FAILED" << std::endl;
        return 1;
    }
    std::cout << "All HEM veto cases PASSED." << std::endl;
    return 0;
}
