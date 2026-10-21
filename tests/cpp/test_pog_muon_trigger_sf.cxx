// Test of the POG single-muon trigger SF of MC, xyh::scalefactor::pog_muon_trigger
// (v7 decision 2026-10-18, replacing the KIT SF of E5 in MC), on a Run-2 UL
// muon_Z payload whose binning ends with flow "error": inside the range the
// payload value at the muon, below the lowest pT edge and at |eta| >= 2.4 the
// value at the clamped point instead of an exception.
//
// Usage: <binary> <muon_Z.json.gz> <correction> <min_pt> <max_abs_eta>

#include "pog_muon_trigger_sf.hxx"
#include "utility/CorrectionManager.hxx"

#include <ROOT/RDataFrame.hxx>
#include <cmath>
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

struct Muon {
    float pt, eta;
};

std::vector<double> evaluate(const std::string &payload,
                             const std::string &correction,
                             const std::vector<Muon> &muons,
                             const std::string &variation, float extrapolation,
                             double min_pt, double max_abs_eta) {
    correctionManager::CorrectionManager manager;
    ROOT::RDataFrame df(muons.size());
    auto input =
        df.Define("pt", [muons](ULong64_t i) { return muons[i].pt; },
                  {"rdfentry_"})
            .Define("eta", [muons](ULong64_t i) { return muons[i].eta; },
                    {"rdfentry_"});
    return *xyh::scalefactor::pog_muon_trigger(
                input, manager, "sf", "pt", "eta", payload, correction,
                variation, extrapolation, min_pt, max_abs_eta)
                .Take<double>("sf");
}

} // namespace

int main(int argc, char **argv) {
    if (argc != 5) {
        std::cerr << "usage: " << argv[0]
                  << " <muon_Z payload> <correction> <min_pt> <max_abs_eta>"
                  << std::endl;
        return 2;
    }
    const std::string payload = argv[1];
    const std::string correction = argv[2];
    const double min_pt = std::stod(argv[3]);
    const double max_abs_eta = std::stod(argv[4]);
    correctionManager::CorrectionManager manager;
    const auto sf = manager.loadCorrection(payload, correction);
    auto direct = [&](double pt, double eta, const std::string &variation) {
        return sf->evaluate({eta, pt, variation});
    };
    auto throws = [&](double pt, double eta) {
        try {
            direct(pt, eta, "nominal");
        } catch (const std::exception &) {
            return true;
        }
        return false;
    };

    // the range the clamp is for: the payload throws outside it
    check(throws(min_pt - 0.5, 0.5) && throws(40.0, max_abs_eta) &&
              throws(40.0, -max_abs_eta - 0.1) && !throws(min_pt, 0.5) &&
              !throws(40.0, -2.39) && !throws(5000.0, 1.0),
          "payload: errors below min_pt and from |eta| max_abs_eta on");

    const std::vector<Muon> inside = {
        {static_cast<float>(min_pt) + 0.5f, 0.3f},
        {35.f, -1.0f},
        {45.f, 1.5f},
        {150.f, -2.3f},
        {800.f, 0.95f}};
    auto values = evaluate(payload, correction, inside, "nominal", 1.0f,
                           min_pt, max_abs_eta);
    bool same = true;
    for (std::size_t i = 0; i < inside.size(); ++i) {
        same &= std::abs(values[i] - direct(inside[i].pt, inside[i].eta,
                                            "nominal")) < 1e-12;
    }
    check(same, "inside the range: the payload value at the muon");

    const std::vector<Muon> outside = {
        {static_cast<float>(min_pt) - 2.0f, 0.5f},  // 2016: 24 GeV (IsoMu22)
        {static_cast<float>(min_pt) - 0.01f, -1.6f},
        {-10.f, 0.5f},                              // default value
        {40.f, static_cast<float>(max_abs_eta)},    // on the edge
        {40.f, -2.45f},
        {static_cast<float>(min_pt) - 1.0f, 2.47f}};
    auto clamped = evaluate(payload, correction, outside, "nominal", 1.0f,
                            min_pt, max_abs_eta);
    const double below_edge = std::nextafter(max_abs_eta, 0.0);
    check(std::abs(clamped[0] - direct(min_pt, 0.5, "nominal")) < 1e-12 &&
              std::abs(clamped[1] - direct(min_pt, 1.6, "nominal")) < 1e-12 &&
              std::abs(clamped[2] - direct(min_pt, 0.5, "nominal")) < 1e-12,
          "below min_pt: the value of the lowest pT bin");
    check(std::abs(clamped[3] - direct(40.0, below_edge, "nominal")) < 1e-12 &&
              std::abs(clamped[4] - direct(40.0, below_edge, "nominal")) <
                  1e-12 &&
              std::abs(clamped[5] - direct(min_pt, below_edge, "nominal")) <
                  1e-12,
          "from |eta| max_abs_eta on: the value of the last |eta| bin");
    check(std::abs(clamped[3] - direct(40.0, 2.3, "nominal")) < 1e-12,
          "the last |eta| bin is 2.1-2.4");

    auto up = evaluate(payload, correction, outside, "nominal", 1.02f, min_pt,
                       max_abs_eta);
    bool scaled = true;
    for (std::size_t i = 0; i < outside.size(); ++i) {
        scaled &= std::abs(up[i] - 1.02f * clamped[i]) < 1e-6;
    }
    check(scaled, "extrapolation factor scales the SF");

    auto systup = evaluate(payload, correction, inside, "systup", 1.0f, min_pt,
                           max_abs_eta);
    check(std::abs(systup[1] - direct(35.0, -1.0, "systup")) < 1e-12 &&
              systup[1] > values[1],
          "the variation reaches the payload");

    bool threw = false;
    try {
        evaluate(payload, correction, inside, "nominal", 1.0f, 0.0,
                 max_abs_eta);
    } catch (const std::invalid_argument &) {
        threw = true;
    }
    check(threw, "min_pt <= 0 throws");

    std::cout << (g_failures == 0 ? "ALL PASS" : "FAILURES") << std::endl;
    return g_failures == 0 ? 0 : 1;
}
