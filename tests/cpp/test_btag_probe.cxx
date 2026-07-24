// Boundary + writer test for the payload-independent UParT probe-jet
// collection (xyh::btag_probe).
//
// This is a standalone (non-CROWN-generated) executable. For probe_mask it
// builds a single-jet ROOT::RDataFrame per boundary case and asserts the
// mask entry; for masked_vector it builds a multi-jet frame with a known
// mask and asserts the length + content of the selected output (for both a
// float vector and an int vector read from a UChar_t branch, i.e. the
// hadron-flavour path).
//
// Run via: bash tests/cpp/run_btag_probe_test.sh (from anywhere, inside the
// CROWN container -- see that script for the compile command).

#include "btag_probe.hxx"

#include <Math/Vector4D.h>
#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <string>

namespace {

int g_failures = 0;

// Probe selection thresholds mirrored from the config
// (btag_probe_min_pt / btag_probe_max_abs_eta / btag_probe_min_delta_r).
constexpr float kMinPt = 20.0f;
constexpr float kMaxAbsEta = 2.4f;
constexpr float kMinDeltaR = 0.4f;

// Evaluate probe_mask for a single jet against two pair legs (given as
// eta/phi; pt/mass are irrelevant for the deltaR the mask uses).
int evaluate_probe(float jet_pt, float jet_eta, float jet_phi, int jet_id,
                   float leg1_eta, float leg1_phi, float leg2_eta,
                   float leg2_phi) {
    ROOT::RDataFrame df(1);
    auto df1 =
        df.Define("Jet_pt", [=]() { return ROOT::RVec<float>{jet_pt}; })
            .Define("Jet_eta", [=]() { return ROOT::RVec<float>{jet_eta}; })
            .Define("Jet_phi", [=]() { return ROOT::RVec<float>{jet_phi}; })
            .Define("Jet_ID", [=]() { return ROOT::RVec<int>{jet_id}; })
            .Define("p4_1",
                    [=]() {
                        return ROOT::Math::PtEtaPhiMVector(50.0f, leg1_eta,
                                                           leg1_phi, 1.0f);
                    })
            .Define("p4_2", [=]() {
                return ROOT::Math::PtEtaPhiMVector(50.0f, leg2_eta, leg2_phi,
                                                   1.0f);
            });

    ROOT::RDF::RNode node = df1;
    auto df2 = xyh::btag_probe::probe_mask(
        node, "mask", "Jet_pt", "Jet_eta", "Jet_phi", "Jet_ID", "p4_1", "p4_2",
        kMinPt, kMaxAbsEta, kMinDeltaR);
    auto masks = df2.Take<ROOT::RVec<int>>("mask").GetValue();
    return masks.at(0).at(0);
}

void check_probe(const std::string &name, int actual, int expected) {
    const bool ok = (actual == expected);
    std::cout << (ok ? "PASS " : "FAIL ") << name << " expected=" << expected
              << " actual=" << actual << std::endl;
    if (!ok) {
        ++g_failures;
    }
}

void check_int(const std::string &name, long actual, long expected) {
    const bool ok = (actual == expected);
    std::cout << (ok ? "PASS " : "FAIL ") << name << " expected=" << expected
              << " actual=" << actual << std::endl;
    if (!ok) {
        ++g_failures;
    }
}

// Far-away legs (deltaR from any |eta| < 2.4 jet at phi=0 is large), used for
// the pt / eta boundary cases so only the varied criterion decides.
constexpr float kFarEta = 4.0f;
constexpr float kFarPhi = 3.0f;

void test_pt_boundary() {
    // pt == 20 passes (inclusive), pt == 19.99 fails.
    check_probe("pt_20_passes",
                evaluate_probe(20.0f, 0.0f, 0.0f, 1, kFarEta, kFarPhi, kFarEta,
                               kFarPhi),
                1);
    check_probe("pt_19p99_fails",
                evaluate_probe(19.99f, 0.0f, 0.0f, 1, kFarEta, kFarPhi, kFarEta,
                               kFarPhi),
                0);
}

void test_eta_boundary() {
    // |eta| == 2.399 passes, |eta| == 2.4 fails (exclusive).
    check_probe("abs_eta_2p399_passes",
                evaluate_probe(30.0f, 2.399f, 0.0f, 1, kFarEta, kFarPhi,
                               kFarEta, kFarPhi),
                1);
    check_probe("abs_eta_2p4_fails",
                evaluate_probe(30.0f, 2.4f, 0.0f, 1, kFarEta, kFarPhi, kFarEta,
                               kFarPhi),
                0);
    // negative-eta side of the same boundary.
    check_probe("abs_eta_neg2p399_passes",
                evaluate_probe(30.0f, -2.399f, 0.0f, 1, kFarEta, kFarPhi,
                               kFarEta, kFarPhi),
                1);
}

void test_jet_id() {
    // A failing jet-ID mask entry rejects the jet regardless of kinematics.
    check_probe("jet_id_fail_rejects",
                evaluate_probe(30.0f, 0.0f, 0.0f, 0, kFarEta, kFarPhi, kFarEta,
                               kFarPhi),
                0);
}

void test_delta_r_boundary() {
    // Jet at (eta=0, phi=0); a leg at (eta=dr, phi=0) is exactly deltaR=dr
    // away. deltaR == 0.4 passes (inclusive), 0.399 fails. The other leg is
    // kept far away so it never decides.
    check_probe("delta_r_0p4_passes",
                evaluate_probe(30.0f, 0.0f, 0.0f, 1, 0.4f, 0.0f, kFarEta,
                               kFarPhi),
                1);
    check_probe("delta_r_0p399_fails",
                evaluate_probe(30.0f, 0.0f, 0.0f, 1, 0.399f, 0.0f, kFarEta,
                               kFarPhi),
                0);
    // deltaR failure against the SECOND leg must also reject.
    check_probe("delta_r_0p399_second_leg_fails",
                evaluate_probe(30.0f, 0.0f, 0.0f, 1, kFarEta, kFarPhi, 0.399f,
                               0.0f),
                0);
}

void test_masked_vector_float() {
    // mask = {1, 0, 1, 1} over a float vector -> keep entries 0, 2, 3.
    ROOT::RDataFrame df(1);
    auto df1 =
        df.Define("values",
                  []() {
                      return ROOT::RVec<float>{10.5f, 20.5f, 30.5f, 40.5f};
                  })
            .Define("mask",
                    []() { return ROOT::RVec<int>{1, 0, 1, 1}; });
    ROOT::RDF::RNode node = df1;
    auto df2 = xyh::btag_probe::masked_vector<float>(node, "out", "values",
                                                     "mask");
    auto out = df2.Take<ROOT::RVec<float>>("out").GetValue().at(0);
    check_int("masked_vector_float_length", static_cast<long>(out.size()), 3);
    const bool content_ok = (out.size() == 3) && (out[0] == 10.5f) &&
                            (out[1] == 30.5f) && (out[2] == 40.5f);
    check_int("masked_vector_float_content", content_ok ? 1 : 0, 1);
}

void test_masked_vector_int_from_uchar() {
    // hadron-flavour path: input branch stored as UChar_t, exported as int.
    // mask = {0, 1, 1, 0, 1} -> keep entries 1, 2, 4 (values 4, 5, 0).
    ROOT::RDataFrame df(1);
    auto df1 =
        df.Define("flavours",
                  []() {
                      return ROOT::RVec<UChar_t>{
                          static_cast<UChar_t>(5), static_cast<UChar_t>(4),
                          static_cast<UChar_t>(5), static_cast<UChar_t>(0),
                          static_cast<UChar_t>(0)};
                  })
            .Define("mask",
                    []() { return ROOT::RVec<int>{0, 1, 1, 0, 1}; });
    ROOT::RDF::RNode node = df1;
    auto df2 = xyh::btag_probe::masked_vector<int, UChar_t>(node, "out",
                                                            "flavours", "mask");
    auto out = df2.Take<ROOT::RVec<int>>("out").GetValue().at(0);
    check_int("masked_vector_int_length", static_cast<long>(out.size()), 3);
    const bool content_ok = (out.size() == 3) && (out[0] == 4) &&
                            (out[1] == 5) && (out[2] == 0);
    check_int("masked_vector_int_content", content_ok ? 1 : 0, 1);
}

void test_masked_vector_empty() {
    // all-zero mask -> empty output (equal-length-by-construction corner).
    ROOT::RDataFrame df(1);
    auto df1 =
        df.Define("values", []() { return ROOT::RVec<float>{1.0f, 2.0f}; })
            .Define("mask", []() { return ROOT::RVec<int>{0, 0}; });
    ROOT::RDF::RNode node = df1;
    auto df2 = xyh::btag_probe::masked_vector<float>(node, "out", "values",
                                                     "mask");
    auto out = df2.Take<ROOT::RVec<float>>("out").GetValue().at(0);
    check_int("masked_vector_empty_length", static_cast<long>(out.size()), 0);
}

} // namespace

int main() {
    test_pt_boundary();
    test_eta_boundary();
    test_jet_id();
    test_delta_r_boundary();
    test_masked_vector_float();
    test_masked_vector_int_from_uchar();
    test_masked_vector_empty();

    if (g_failures > 0) {
        std::cerr << g_failures << " case(s) FAILED" << std::endl;
        return 1;
    }
    std::cout << "All btag_probe boundary/writer cases PASSED." << std::endl;
    return 0;
}
