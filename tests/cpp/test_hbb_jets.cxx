// Test of xyh::genmatching::JetsFromBosonDecay, the flag of the jets from
// H -> bb in the jet slots (v8 spec C25), on generator records with the
// features of the NanoAOD v15 HH samples.
//
// The checks:
//  - the last copies of the two b quarks of the Higgs boson decay flag the
//    nearest jet of the collection within Delta R < 0.4, in the order of the
//    collection; every other jet gets 0;
//  - a quark is matched to at most one jet, and two quarks can share one;
//  - a quark without a jet in the radius flags nothing, also if its nearest
//    jet is not in the collection;
//  - a copy with the partner quark as its mother (status 73 with two mothers)
//    still belongs to the decay;
//  - a b quark from gluon splitting, which NanoAOD links to the radiating
//    quark (a last copy that is not from the hard process), does not count,
//    nor does a hard-process b quark without the boson above it, nor the b
//    quarks of another boson;
//  - Delta phi wraps at +-pi; an empty collection gives an empty vector.

#include "hbb_jets.hxx"

#include <ROOT/RDataFrame.hxx>
#include <ROOT/RVec.hxx>
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

const UShort_t HARD = 1 << 8, LAST = 1 << 13, FIRST = 1 << 12;

struct Particle {
    int pdgid;
    UShort_t flags;
    Short_t mother;
    float eta, phi;
};
struct Jet {
    float eta, phi;
};

ROOT::RVec<int> flags(const std::vector<Particle> &particles, const std::vector<Jet> &jets,
                      const ROOT::RVec<int> &collection, int mother_pdgid = 25) {
    ROOT::RVec<int> pdgid;
    ROOT::RVec<UShort_t> statusflags;
    ROOT::RVec<Short_t> mother;
    ROOT::RVec<float> eta, phi, jet_eta, jet_phi;
    for (const auto &particle : particles) {
        pdgid.push_back(particle.pdgid);
        statusflags.push_back(particle.flags);
        mother.push_back(particle.mother);
        eta.push_back(particle.eta);
        phi.push_back(particle.phi);
    }
    for (const auto &jet : jets) {
        jet_eta.push_back(jet.eta);
        jet_phi.push_back(jet.phi);
    }
    ROOT::RDataFrame base(1);
    ROOT::RDF::RNode df = base.Define("pdgid", [pdgid] { return pdgid; })
                              .Define("flags", [statusflags] { return statusflags; })
                              .Define("mother", [mother] { return mother; })
                              .Define("eta", [eta] { return eta; })
                              .Define("phi", [phi] { return phi; })
                              .Define("jet_eta", [jet_eta] { return jet_eta; })
                              .Define("jet_phi", [jet_phi] { return jet_phi; })
                              .Define("jets", [collection] { return collection; });
    df = xyh::genmatching::JetsFromBosonDecay(df, "from_hbb", "pdgid", "flags", "mother", "eta",
                                              "phi", "jet_eta", "jet_phi", "jets", mother_pdgid,
                                              5, 0.4f);
    return df.Take<ROOT::RVec<int>>("from_hbb")->at(0);
}

bool equal(const ROOT::RVec<int> &a, const std::vector<int> &b) {
    return a.size() == b.size() && std::equal(a.begin(), a.end(), b.begin());
}
} // namespace

int main() {
    // gluons -> H H; H(1) -> b bbar, H(2) -> tau tau. The b quark radiates, its
    // last copy is 7; the anti-b quark has a copy with the b quark as mother.
    std::vector<Particle> event{
        {21, HARD, -1, 0.f, 0.f},                  // 0 incoming
        {25, HARD | LAST, 0, 0.5f, 1.0f},          // 1 H -> bb
        {25, HARD | LAST, 0, -0.5f, -2.0f},        // 2 H -> tautau
        {5, HARD | FIRST, 1, 1.0f, 0.5f},          // 3 b, first copy
        {-5, HARD | FIRST, 1, -1.0f, 3.0f},        // 4 bbar, first copy
        {15, HARD | FIRST | LAST, 2, 0.2f, -2.f},  // 5
        {-15, HARD | FIRST | LAST, 2, -0.9f, -2.f},// 6
        {5, HARD | LAST, 3, 1.1f, 0.6f},           // 7 b, last copy
        {-5, HARD, 3, -1.0f, 3.05f},               // 8 bbar copy, mother: the b quark
        {-5, HARD | LAST, 8, -1.05f, 3.1f},        // 9 bbar, last copy
        {-5, LAST, 3, 2.0f, -1.0f},                // 10 bbar from gluon splitting off the b
        {5, LAST, 3, 2.1f, -1.2f},                 // 11 b from gluon splitting off the b
        {5, HARD | FIRST | LAST, 0, -2.0f, 0.0f},  // 12 b of a real emission
    };
    // jets 0..5; the collection orders them by pT as 2, 0, 5, 3
    std::vector<Jet> jets{
        {1.15f, 0.65f},   // 0 at the b quark
        {-1.0f, -3.1f},   // 1 at the bbar quark across phi = pi, not in the collection
        {-1.2f, 3.0f},    // 2 at the bbar quark, a little further than jet 1
        {2.05f, -1.1f},   // 3 at the gluon splitting pair
        {0.2f, -2.f},     // 4 a tau, not in the collection
        {-2.0f, 0.05f},   // 5 at the real emission
    };
    check(equal(flags(event, jets, {2, 0, 5, 3}), {1, 1, 0, 0}),
          "the jets at the two quarks of the decay are flagged, in collection order; gluon "
          "splitting and real emission are not");
    check(equal(flags(event, jets, {2, 1, 0}), {0, 1, 1}),
          "a quark flags its nearest jet only (Delta phi wraps at pi)");
    check(equal(flags(event, jets, {3, 5, 4}), {0, 0, 0}),
          "quarks without a jet of the collection in the radius flag nothing");
    check(equal(flags(event, jets, {}), {}), "an empty collection gives an empty vector");
    // the radius: jet 2 is 0.18 from the bbar quark, a jet at 0.41 is outside
    {
        auto far = jets;
        far[2] = {-1.05f, 3.1f - 0.41f};
        check(equal(flags(event, far, {2, 0}), {0, 1}), "a jet at Delta R 0.41 is not matched");
        far[2] = {-1.05f, 3.1f - 0.39f};
        check(equal(flags(event, far, {2, 0}), {1, 1}), "a jet at Delta R 0.39 is matched");
    }
    // both quarks in one jet
    {
        auto merged = event;
        merged[9].eta = 1.0f;
        merged[9].phi = 0.7f;
        check(equal(flags(merged, jets, {2, 0, 3}), {0, 1, 0}), "two quarks can share a jet");
    }
    // the quarks of another boson do not count
    check(equal(flags(event, jets, {2, 0, 5, 3}, 23), {0, 0, 0, 0}),
          "the quarks must stem from the requested boson");
    // a last copy that is its own first copy (no radiation)
    {
        std::vector<Particle> simple{{25, HARD | LAST, -1, 0.f, 0.f},
                                     {5, HARD | FIRST | LAST, 0, 0.3f, 0.3f},
                                     {-5, HARD | FIRST | LAST, 0, -0.3f, -0.3f}};
        check(equal(flags(simple, {{0.3f, 0.3f}, {-0.3f, -0.3f}, {2.f, 2.f}}, {0, 1, 2}), {1, 1, 0}),
              "direct daughters that are last copies are matched");
    }
    bool refused = true;
    for (const auto &[mother, quark, radius] :
         {std::tuple{0, 5, 0.4f}, std::tuple{25, 0, 0.4f}, std::tuple{25, 5, 0.f}}) {
        try {
            ROOT::RDataFrame base(1);
            xyh::genmatching::JetsFromBosonDecay(base, "x", "a", "b", "c", "d", "e", "f", "g", "h",
                                                 mother, quark, radius);
            refused = false;
        } catch (const std::invalid_argument &) {
        }
    }
    check(refused, "non-positive pdgIds and radius are refused");
    return failures == 0 ? 0 : 1;
}
