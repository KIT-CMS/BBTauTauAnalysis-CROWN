#ifndef GUARDJETSEXT_H
#define GUARDJETSEXT_H

#include "../../../../include/defaults.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "TRandom3.h"
#include "correction.h"

namespace physicsobject {

namespace jet {

namespace jec {

typedef struct jec_result_t {
    float jet_pt_l1;
    float jet_pt_l2rel;
    float jet_pt_l2l3res;
    float jet_pt_syst;
    float jet_pt_corr;
} JECResult;
const correction::Correction *load_nominal_jes_correction(
    correctionManager::CorrectionManager &correction_manager,
    const std::string &jec_file, const std::string &jes_tag,
    const std::string &type_tag, const std::string &jes_level,
    const std::string &jec_algo);
const correction::Correction *load_shifted_jes_correction(
    correctionManager::CorrectionManager &correction_manager,
    const std::string &jec_file, const std::string &jer_tag,
    const std::string &type_tag, const std::string &jes_shift,
    const std::string &jec_algo);
const correction::Correction *
load_jer_correction(correctionManager::CorrectionManager &correction_manager,
                    const std::string &jec_file, const std::string &jer_tag,
                    const std::string &type_tag,
                    const std::string &jer_parameter,
                    const std::string &jec_algo);
float apply_jes_l1(const float &jet_pt, const float &jet_eta,
                   const float &jet_area, const float &rho,
                   const correction::Correction *jes_l1_evaluator);
float apply_jes_l2rel(const float &jet_pt, const float &jet_eta,
                      const float &jet_phi, const std::string &era,
                      const correction::Correction *jes_l2rel_evaluator);
float apply_jes_l2l3res(const float &jet_pt, const float &jet_eta,
                        const float &run, const std::string &era,
                        const correction::Correction *jes_l2l3res_evaluator);
float apply_jes_shifts(
    const float &jet_pt, const float &jet_eta, const float &jet_phi,
    const UChar_t &jet_id, const std::vector<std::string> &jes_shift_sources,
    const int &jes_shift_factor,
    const std::vector<correction::Correction *> &jes_shift_evaluators);
float apply_jer(const float &jet_pt, const float &jet_eta, const float &jet_phi,
                const float &rho, const ROOT::RVec<float> &genjet_pt,
                const ROOT::RVec<float> &genjet_eta,
                const ROOT::RVec<float> &genjet_phi,
                const correction::Correction *jer_resolution_evaluator,
                const correction::Correction *jer_scalefactor_evaluator,
                const correction::Correction *jer_scalefactor_uncertainty_evaluator,
                const std::string &jer_shift, const float &jet_radius,
                const std::string &era, TRandom3 randgen);
JECResult apply_full_jec_mc(
    const float &jet_pt, const float &jet_eta, const float &jet_phi,
    const UChar_t &jet_id, const float &jet_area, const float &rho,
    const ROOT::RVec<float> &genjet_pt, const ROOT::RVec<float> &genjet_eta,
    const ROOT::RVec<float> &genjet_phi,
    const std::vector<std::string> &jes_shift_sources,
    const int &jes_shift_factor, const std::string &jer_shift,
    const float &jet_radius, const std::string &era, TRandom3 randgen,
    const correction::Correction *jes_l1_evaluator,
    const correction::Correction *jes_l2rel_evaluator,
    const std::vector<correction::Correction *> &jes_shift_evaluators,
    const correction::Correction *jer_resolution_evaluator,
    const correction::Correction *jer_scalefactor_evaluator,
    const correction::Correction *jer_scalefactor_uncertainty_evaluator
    );
JECResult apply_jes_shifts_and_jer_mc(
    const float &jet_pt, const float &jet_eta, const float &jet_phi,
    const UChar_t &jet_id, const float &rho, const ROOT::RVec<float> &genjet_pt,
    const ROOT::RVec<float> &genjet_eta, const ROOT::RVec<float> &genjet_phi,
    const std::vector<std::string> &jes_shift_sources,
    const int &jes_shift_factor, const std::string &jer_shift,
    const float &jet_radius, const std::string &era, TRandom3 randgen,
    const std::vector<correction::Correction *> &jes_shift_evaluators,
    const correction::Correction *jer_resolution_evaluator,
    const correction::Correction *jer_scalefactor_evaluator,
    const correction::Correction *jer_scalefactor_uncertainty_evaluator
    );
JECResult
apply_full_jec_data(const float &jet_pt, const float &jet_eta,
                    const float &jet_phi, const float &jet_area,
                    const float &rho,
                    const correction::Correction *jes_l1_evaluator,
                    const correction::Correction *jes_l2rel_evaluator,
                    const correction::Correction *jes_l2l3res_evaluator);
ROOT::RDF::RNode Raw(ROOT::RDF::RNode df, const std::string &outputname,
                     const std::string &jet_quantity,
                     const std::string &jet_raw_factor);
ROOT::RDF::RNode RawMuonSubtr(ROOT::RDF::RNode df,
                              const std::string &outputname,
                              const std::string &jet_quantity,
                              const std::string &jet_raw_factor,
                              const std::string &jet_muon_subtr_factor);
ROOT::RDF::RNode RawMuonSubtr(ROOT::RDF::RNode df,
                              const std::string &outputname,
                              const std::string &jet_quantity,
                              const std::string &jet_muon_subtr_factor);
ROOT::RDF::RNode
PtCorrectionMC(ROOT::RDF::RNode df,
               correctionManager::CorrectionManager &correction_manager,
               const std::string &output_jec_result,
               const std::string &output_l1, const std::string &output_l2rel,
               const std::string &output_l2l3res,
               const std::string &output_full, const std::string &jet_pt_raw,
               const std::string &jet_eta, const std::string &jet_phi,
               const std::string &jet_area, const std::string &jet_id,
               const std::string &genjet_pt, const std::string &genjet_eta,
               const std::string &genjet_phi, const std::string &rho,
               const std::string &jer_seed, const std::string &jec_file,
               const std::string &jec_algo, const std::string &jes_tag,
               const std::string &jer_tag,
               const std::vector<std::string> &jes_shift_sources,
               const int &jes_shift_factor, const std::string &jer_shift,
               const bool &reapply_jes, const std::string &era);
ROOT::RDF::RNode
PtCorrectionData(ROOT::RDF::RNode df,
                 correctionManager::CorrectionManager &correction_manager,
                 const std::string &output_jec_result,
                 const std::string &output_l1, const std::string &output_l2rel,
                 const std::string &output_l2l3res,
                 const std::string &output_full, const std::string &jet_pt_raw,
                 const std::string &jet_eta, const std::string &jet_phi,
                 const std::string &jet_area, const std::string &rho,
                 const std::string &run, const std::string &jec_file,
                 const std::string &jec_algo, const std::string &jes_tag,
                 const bool &reapply_jes, const std::string &era);
ROOT::RDF::RNode MassCorrectionFromPt(ROOT::RDF::RNode df,
                                      const std::string &outputname,
                                      const std::string &jet_mass_raw,
                                      const std::string &jet_pt_raw,
                                      const std::string &jet_pt_corrected);

} // namespace jec

namespace quantities {

/**
 * @brief Get the value of a generator-level quantity of a jet.
 *
 * The reconstructed jet under consideration is chosen by providing its
 * position within a list of indices. Then, the `Jet_genJetIdx` or
 * `FatJet_genJetAK8Idx` of that jet is used to find the associated
 * generator-level jet, from which the requested quantity value is taken.
 *
 * @param df the input dataframe
 * @param output_name the name of the produced column
 * @param genjet_idx index column that holds the index of the associated
 * generator-level jet
 * @param gen_quantity name of the quantity of the generator-level jet
 * @param index_vector name of the column containing index values
 * @param position position within the index vector used to retrieve the index
 *
 * @return a dataframe with the new column
 */
template <typename T>
ROOT::RDF::RNode
GetGenJetQuantity(ROOT::RDF::RNode df, const std::string &output_name,
                  const std::string &genjet_idx,
                  const std::string &gen_quantity,
                  const std::string &index_vector, const int &position) {

    auto get_gen_quantity = [position](const ROOT::RVec<Short_t> &genjet_idx,
                                       const ROOT::RVec<T> &gen_quantity,
                                       const ROOT::RVec<int> &index_vector) {
        // Define the result with the default value, which is returned when
        // accessing the entries in the vectors fails
        T result = default_value<T>();

        // Get the index to access in the fatjet list
        if (position >= 0 && position < index_vector.size()) {
            auto index = index_vector.at(position);
            if (index >= 0 && index < genjet_idx.size()) {
                auto gen_index = genjet_idx.at(index);
                result = gen_quantity.at(gen_index);
            }
        } else {
            Logger::get("event::quantity::Get")
                ->debug("Index not found, returning dummy value!");
        }

        return result;
    };

    return df.Define(output_name, get_gen_quantity,
                     {genjet_idx, gen_quantity, index_vector});
}

ROOT::RDF::RNode CorrectJetIDRun3NanoV12(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &jet_pt, const std::string &jet_eta,
    const std::string &jet_id, const std::string &jet_ne_hef,
    const std::string &jet_ne_em_ef, const std::string &jet_mu_ef,
    const std::string &jet_ch_em_ef);
ROOT::RDF::RNode TightestWPPassed(
           ROOT::RDF::RNode df,
           correctionManager::CorrectionManager &correction_manager,
           const std::string &outputname, const std::string &btag_value,
           const std::string &sf_file, const std::string &sf_wp_name
);

ROOT::RDF::RNode JetPtPNetRegression(ROOT::RDF::RNode df,
                                     const std::string &outputname,
                                     const std::string &jet_pt_nanoaod,
                                     const std::string &jet_raw_factor,
                                     const std::string &jet_pnet_reg_pt_factor,
                                     const std::string &jet_collection_index);

ROOT::RDF::RNode JetPtPNetRegressionWithNeutrino(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &jet_pt_nanoaod, const std::string &jet_raw_factor,
    const std::string &jet_pnet_reg_pt_factor,
    const std::string &jet_pnet_reg_pt_neutrino_factor,
    const std::string &jet_collection_index);

} // namespace quantities

} // namespace jet

} // namespace physicsobject

#endif
