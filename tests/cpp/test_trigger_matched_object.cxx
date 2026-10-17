// trigger::MatchedObjectQuantity (cpp_addons/include/triggers.hxx), the
// trigger-object columns trgobj_pt_2, trgobj_l1pt_2 and trgobj_l1iso_2 of the
// tau-ID measurement.
//
// The input is a TTree with the NanoAOD v15 types (TrigObj_id UShort_t,
// TrigObj_filterBits ULong64_t, TrigObj_l1iso Int_t), one event per case:
//   0  two objects pass, the farther one first: the nearest in Delta R wins
//   1  the only object is outside Delta R 0.4: -1
//   2  one object lacks one of the bits, one is a muon: -1
//   3  the bits are set among bits above 31 (bit 40) and the embedding bit 23:
//      matched, with the 64-bit filter bits of v15
//   4  no trigger object: -1
// A second call requires bit 40 alone, which only event 3 carries.

#include "triggers.hxx"

#include <Math/Vector4D.h>
#include <ROOT/RDataFrame.hxx>
#include <TTree.h>

#include <cmath>
#include <cstdio>
#include <vector>

struct Object {
    float pt, eta, phi, l1pt;
    UShort_t id;
    ULong64_t bits;
    Int_t l1iso;
};

struct Event {
    float eta, phi;
    std::vector<Object> objects;
    float expected_pt, expected_l1pt;
    int expected_l1iso;
    float expected_pt_bit40;
};

constexpr ULong64_t bit(int n) { return ULong64_t(1) << n; }

int main() {
    const ULong64_t leg = bit(9) | bit(17);
    const std::vector<Event> events = {
        {0.5f, 1.0f,
         {{41.f, 0.70f, 1.0f, 36.f, 15, leg, 1},
          {42.f, 0.55f, 1.0f, 37.f, 15, leg | bit(2), 3}},
         42.f, 37.f, 3, -1.f},
        {0.5f, 1.0f, {{43.f, 0.5f, 1.45f, 38.f, 15, leg, 1}}, -1.f, -1.f, -1, -1.f},
        {0.5f, 1.0f,
         {{44.f, 0.5f, 1.0f, 39.f, 15, bit(9), 1},
          {45.f, 0.5f, 1.0f, 40.f, 13, leg, 1}},
         -1.f, -1.f, -1, -1.f},
        {-1.2f, -2.0f, {{46.f, -1.2f, -2.05f, 41.f, 15, leg | bit(23) | bit(40), 2}}, 46.f, 41.f, 2, 46.f},
        {0.0f, 0.0f, {}, -1.f, -1.f, -1, -1.f},
    };

    TTree tree("Events", "Events");
    tree.SetDirectory(nullptr);
    float eta, phi;
    UInt_t n;
    const int max_objects = 4;
    Float_t pts[max_objects], etas[max_objects], phis[max_objects], l1pts[max_objects];
    UShort_t ids[max_objects];
    ULong64_t filterbits[max_objects];
    Int_t l1isos[max_objects];
    tree.Branch("eta", &eta, "eta/F");
    tree.Branch("phi", &phi, "phi/F");
    tree.Branch("nTrigObj", &n, "nTrigObj/i");
    tree.Branch("TrigObj_pt", pts, "TrigObj_pt[nTrigObj]/F");
    tree.Branch("TrigObj_eta", etas, "TrigObj_eta[nTrigObj]/F");
    tree.Branch("TrigObj_phi", phis, "TrigObj_phi[nTrigObj]/F");
    tree.Branch("TrigObj_l1pt", l1pts, "TrigObj_l1pt[nTrigObj]/F");
    tree.Branch("TrigObj_id", ids, "TrigObj_id[nTrigObj]/s");
    tree.Branch("TrigObj_filterBits", filterbits, "TrigObj_filterBits[nTrigObj]/l");
    tree.Branch("TrigObj_l1iso", l1isos, "TrigObj_l1iso[nTrigObj]/I");
    for (const auto &event : events) {
        eta = event.eta;
        phi = event.phi;
        n = event.objects.size();
        for (UInt_t i = 0; i < n; ++i) {
            const auto &o = event.objects[i];
            pts[i] = o.pt;
            etas[i] = o.eta;
            phis[i] = o.phi;
            l1pts[i] = o.l1pt;
            ids[i] = o.id;
            filterbits[i] = o.bits;
            l1isos[i] = o.l1iso;
        }
        tree.Fill();
    }

    ROOT::RDataFrame frame(tree);
    ROOT::RDF::RNode df = frame.Define(
        "p4_2",
        [](float eta, float phi) { return ROOT::Math::PtEtaPhiMVector(40.f, eta, phi, 1.777f); },
        {"eta", "phi"});
    const std::vector<int> monitor_bits = {9, 17};
    df = trigger::MatchedObjectQuantity<Float_t>(
        df, "trgobj_pt_2", "p4_2", "TrigObj_eta", "TrigObj_phi", "TrigObj_id",
        "TrigObj_filterBits", "TrigObj_pt", 15, monitor_bits, 0.4);
    df = trigger::MatchedObjectQuantity<Float_t>(
        df, "trgobj_l1pt_2", "p4_2", "TrigObj_eta", "TrigObj_phi", "TrigObj_id",
        "TrigObj_filterBits", "TrigObj_l1pt", 15, monitor_bits, 0.4);
    df = trigger::MatchedObjectQuantity<Int_t>(
        df, "trgobj_l1iso_2", "p4_2", "TrigObj_eta", "TrigObj_phi", "TrigObj_id",
        "TrigObj_filterBits", "TrigObj_l1iso", 15, monitor_bits, 0.4);
    df = trigger::MatchedObjectQuantity<Float_t>(
        df, "trgobj_pt_bit40", "p4_2", "TrigObj_eta", "TrigObj_phi", "TrigObj_id",
        "TrigObj_filterBits", "TrigObj_pt", 15, {40}, 0.4);

    auto pt = df.Take<Float_t>("trgobj_pt_2");
    auto l1pt = df.Take<Float_t>("trgobj_l1pt_2");
    auto l1iso = df.Take<Int_t>("trgobj_l1iso_2");
    auto pt_bit40 = df.Take<Float_t>("trgobj_pt_bit40");
    int failures = 0;
    for (std::size_t i = 0; i < events.size(); ++i) {
        const auto &e = events[i];
        if (pt->at(i) != e.expected_pt || l1pt->at(i) != e.expected_l1pt ||
            l1iso->at(i) != e.expected_l1iso || pt_bit40->at(i) != e.expected_pt_bit40) {
            std::printf("event %zu: pt %g (%g), l1pt %g (%g), l1iso %d (%d), pt bit 40 %g (%g)\n",
                        i, pt->at(i), e.expected_pt, l1pt->at(i), e.expected_l1pt,
                        l1iso->at(i), e.expected_l1iso, pt_bit40->at(i), e.expected_pt_bit40);
            ++failures;
        }
    }

    // a bit outside the 64-bit word is a configuration error
    bool thrown = false;
    try {
        trigger::MatchedObjectQuantity<Float_t>(
            df, "bad", "p4_2", "TrigObj_eta", "TrigObj_phi", "TrigObj_id",
            "TrigObj_filterBits", "TrigObj_pt", 15, {64}, 0.4);
    } catch (const std::invalid_argument &) {
        thrown = true;
    }
    if (!thrown) {
        std::printf("bit 64 accepted\n");
        ++failures;
    }
    return failures == 0 ? 0 : 1;
}
