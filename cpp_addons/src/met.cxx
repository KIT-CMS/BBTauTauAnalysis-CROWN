#include "../include/met.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <Math/Vector3D.h>
#include <Math/Vector4D.h>
#include <Math/VectorUtil.h>
#include <cmath>

namespace met {

ROOT::RDF::RNode
METType1Correction(ROOT::RDF::RNode df, const std::string &outputname,
                const std::string raw_met,
                const std::string &t1jet_pt_l1corrected,
                const std::string &t1jet_pt_corrected,
                const std::string &t1jet_eta, const std::string &t1jet_phi,
                const std::string &t1jet_em_ef, const std::string &t1jet_muon_subtr_delta_phi, const float &t1jet_min_pt,
                const float &t1jet_max_abs_eta, const float &t1jet_max_em_ef) {

    auto type1_corr_func = [t1jet_min_pt, t1jet_max_abs_eta, t1jet_max_em_ef](
                               const ROOT::Math::PtEtaPhiMVector &raw_met,
                               const ROOT::RVec<float> &t1jet_pt_l1corrected,
                               const ROOT::RVec<float> &t1jet_pt_corrected,
                               const ROOT::RVec<float> &t1jet_eta,
                               const ROOT::RVec<float> &t1jet_phi,
                               const ROOT::RVec<float> &t1jet_em_ef,
                               const ROOT::RVec<float> &t1jet_muon_subtr_delta_phi
    ) {
        // Add phi correction
        auto t1jet_phi_corrected = t1jet_phi + t1jet_muon_subtr_delta_phi;

        // Select jets for the type-I correction
        auto jet_index =
            ROOT::VecOps::Nonzero(t1jet_pt_corrected >= t1jet_min_pt &&
                                  std::abs(t1jet_eta) <= t1jet_max_abs_eta &&
                                  t1jet_em_ef <= t1jet_max_em_ef);

        // Calculate the difference vector between the fully corrected and
        // the L1-corrected transverse momentum vectors with all selected
        // jets
        float met_x = raw_met.Pt() * std::cos(raw_met.Phi());
        float met_y = raw_met.Pt() * std::sin(raw_met.Phi());
        for (const auto &i : jet_index) {
            met_x -= (t1jet_pt_corrected[i] - t1jet_pt_l1corrected[i]) *
                     std::cos(t1jet_phi_corrected[i]);
            met_y -= (t1jet_pt_corrected[i] - t1jet_pt_l1corrected[i]) *
                     std::sin(t1jet_phi_corrected[i]);
        }

        return ROOT::Math::PtEtaPhiMVector(
            std::sqrt(met_x * met_x + met_y * met_y), 0.0,
            std::atan2(met_y, met_x), std::sqrt(met_x * met_x + met_y * met_y));
    };

    return df.Define(outputname, type1_corr_func,
                     {raw_met, t1jet_pt_l1corrected, t1jet_pt_corrected,
                      t1jet_eta, t1jet_phi, t1jet_em_ef, t1jet_muon_subtr_delta_phi});
}

} // namespace met
