#include "../include/hbb_jets.hxx"
#include "ROOT/RVec.hxx"
#include <cmath>
#include <stdexcept>

namespace xyh::genmatching {
ROOT::RDF::RNode JetsFromBosonDecay(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &genpart_pdgid, const std::string &genpart_statusflags,
    const std::string &genpart_mother, const std::string &genpart_eta,
    const std::string &genpart_phi, const std::string &jet_eta,
    const std::string &jet_phi, const std::string &jet_collection,
    const int mother_pdgid, const int quark_pdgid, const float max_delta_r) {
    if (mother_pdgid <= 0 || quark_pdgid <= 0 || !(max_delta_r > 0.f)) {
        throw std::invalid_argument(
            "xyh::genmatching::JetsFromBosonDecay: needs positive pdgIds and "
            "a positive matching radius");
    }
    // status flags: fromHardProcess (bit 8) and isLastCopy (bit 13)
    const int from_hard_process_last_copy = (1 << 8) | (1 << 13);
    auto flag_jets = [mother_pdgid, quark_pdgid, max_delta_r,
                      from_hard_process_last_copy](
                         const ROOT::RVec<int> &pdgid,
                         const ROOT::RVec<UShort_t> &statusflags,
                         const ROOT::RVec<Short_t> &mother,
                         const ROOT::RVec<float> &genpart_eta,
                         const ROOT::RVec<float> &genpart_phi,
                         const ROOT::RVec<float> &jet_eta,
                         const ROOT::RVec<float> &jet_phi,
                         const ROOT::RVec<int> &jets) {
        ROOT::RVec<int> flags(jets.size(), 0);
        const int n_particles = pdgid.size();
        for (int particle = 0; particle < n_particles; ++particle) {
            if (std::abs(pdgid[particle]) != quark_pdgid ||
                (statusflags[particle] & from_hard_process_last_copy) !=
                    from_hard_process_last_copy) {
                continue;
            }
            // up the quarks of the chain to its first copy; the index of a
            // mother is below that of its daughter, so the walk ends
            int first_copy = particle;
            while (mother[first_copy] >= 0 &&
                   mother[first_copy] < first_copy &&
                   std::abs(pdgid[mother[first_copy]]) == quark_pdgid) {
                first_copy = mother[first_copy];
            }
            const int boson = mother[first_copy];
            if (boson < 0 || boson >= n_particles ||
                std::abs(pdgid[boson]) != mother_pdgid) {
                continue;
            }
            // the nearest jet of the collection within the radius
            int nearest = -1;
            float nearest_delta_r = max_delta_r;
            for (std::size_t position = 0; position < jets.size();
                 ++position) {
                const int jet = jets[position];
                const float delta_eta = jet_eta[jet] - genpart_eta[particle];
                const float delta_phi = std::remainder(
                    jet_phi[jet] - genpart_phi[particle], 2.f * (float)M_PI);
                const float delta_r = std::hypot(delta_eta, delta_phi);
                if (delta_r < nearest_delta_r) {
                    nearest = position;
                    nearest_delta_r = delta_r;
                }
            }
            if (nearest >= 0) {
                flags[nearest] = 1;
            }
        }
        return flags;
    };
    return df.Define(outputname, flag_jets,
                     {genpart_pdgid, genpart_statusflags, genpart_mother,
                      genpart_eta, genpart_phi, jet_eta, jet_phi,
                      jet_collection});
}
} // namespace xyh::genmatching
