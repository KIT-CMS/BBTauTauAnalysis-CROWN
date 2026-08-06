#include "../include/jets.hxx"
#include "../../../../include/defaults.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "../../../../include/utility/utility.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "TRandom3.h"
#include "correction.h"
#include <Math/Vector3D.h>
#include <Math/Vector4D.h>
#include <Math/VectorUtil.h>
#include <algorithm>

namespace physicsobject {

namespace jet {

namespace jec {

const correction::Correction *load_nominal_jes_correction(
    correctionManager::CorrectionManager &correction_manager,
    const std::string &jec_file, const std::string &jes_tag,
    const std::string &type_tag, const std::string &jes_level,
    const std::string &jec_algo) {
    return correction_manager.loadCorrection(
        jec_file, jes_tag + "_" + type_tag + "_" + jes_level + "_" + jec_algo);
}

const correction::Correction *load_shifted_jes_correction(
    correctionManager::CorrectionManager &correction_manager,
    const std::string &jec_file, const std::string &jer_tag,
    const std::string &type_tag, const std::string &jes_shift,
    const std::string &jec_algo) {
    return correction_manager.loadCorrection(
        jec_file, jer_tag + "_" + type_tag + "_" + jes_shift + "_" + jec_algo);
}

const correction::Correction *
load_jer_correction(correctionManager::CorrectionManager &correction_manager,
                    const std::string &jec_file, const std::string &jer_tag,
                    const std::string &type_tag,
                    const std::string &jer_parameter,
                    const std::string &jec_algo) {
    return correction_manager.loadCorrection(
        jec_file,
        jer_tag + "_" + type_tag + "_" + jer_parameter + "_" + jec_algo);
}

float apply_jes_l1(const float &jet_pt, const float &jet_eta,
                   const float &jet_area, const float &rho,
                   const correction::Correction *jes_l1_evaluator) {
    // Calculate L1FastJet-corrected pt
    return jet_pt *
           jes_l1_evaluator->evaluate({jet_area, jet_eta, jet_pt, rho});
}

float apply_jes_l2rel(const float &jet_pt, const float &jet_eta,
                      const float &jet_phi, const std::string &era,
                      const correction::Correction *jes_l2rel_evaluator) {
    // Calculate the L2rel-corrected pt
    float pt_corrected;
    if (std::stoi(era.substr(0, 4)) <= 2022 || era == "2023preBPix") {
        // For era <= 2023preBPix, phi is not an input argument
        pt_corrected =
            jet_pt * jes_l2rel_evaluator->evaluate({jet_eta, jet_pt});
    } else {
        // For era >= 2023postBPix, phi is an input argument
        pt_corrected =
            jet_pt * jes_l2rel_evaluator->evaluate({jet_eta, jet_phi, jet_pt});
    }
    return pt_corrected;
}

float apply_jes_l2l3res(const float &jet_pt, const float &jet_eta,
                        const float &run, const std::string &era,
                        const correction::Correction *jes_l2l3res_evaluator) {
    // Calculate the L2L3res-corrected pt
    return jet_pt * jes_l2l3res_evaluator->evaluate({run, jet_eta, jet_pt});
}

float apply_jes_shifts(
    const float &jet_pt, const float &jet_eta, const float &jet_phi,
    const UChar_t &jet_id, const std::vector<std::string> &jes_shift_sources,
    const int &jes_shift_factor,
    const std::vector<correction::Correction *> &jes_shift_evaluators) {
    float jet_pt_corr;
    if (jes_shift_sources.at(0) == "HEMIssue") {
        // To assign an uncertainty to the HEM issue, the jet pt needs to be
        // manually scaled in a specific phase space region.
        float sf = 1.0;
        if (jes_shift_factor == -1 && jet_pt > 15.0 && jet_phi > -1.57 &&
            jet_phi < -0.87 && jet_id == 2) {
            if (jet_eta > -2.5 && jet_eta < -1.3) {
                sf = 0.8;
            } else if (jet_eta > -3.0 && jet_eta <= -2.5) {
                sf = 0.65;
            }
        }
        jet_pt_corr = sf * jet_pt;
    } else {
        // Calculate the relative difference to the nominal corrected pt.
        // If multiple sources are combined, the squared sum of the
        // differences is computed.
        float delta_squared = 0.;
        for (const auto &evaluator : jes_shift_evaluators) {
            delta_squared +=
                std::pow(evaluator->evaluate({jet_eta, jet_pt}), 2);
        }

        jet_pt_corr =
            jet_pt * (1 + jes_shift_factor * std::sqrt(delta_squared));
    }
    return jet_pt_corr;
}

float apply_jer(const float &jet_pt, const float &jet_eta, const float &jet_phi,
                const float &rho, const ROOT::RVec<float> &genjet_pt,
                const ROOT::RVec<float> &genjet_eta,
                const ROOT::RVec<float> &genjet_phi,
                const correction::Correction *jer_resolution_evaluator,
                const correction::Correction *jer_scalefactor_evaluator,
                const correction::Correction *jer_scalefactor_uncertainty_evaluator,
                const std::string &jer_shift, const float &jet_radius,
                const std::string &era, TRandom3 randgen) {
    // Get the JER MC resolution and data-MC scale factor for the smearing
    auto resol = jer_resolution_evaluator->evaluate({jet_eta, jet_pt, rho});
    auto sf = 1.0;
    if (std::stoi(era.substr(0, 4)) <= 2018) { // with run 2 inputs
        sf = jer_scalefactor_evaluator->evaluate({jet_eta, jer_shift});
    } else {
        sf = jer_scalefactor_evaluator->evaluate({ // with run 3 inputs
                                                  jet_eta, jet_pt});
        if (jer_shift == "up" || jer_shift == "down") {
            auto sf_unc = jer_scalefactor_uncertainty_evaluator->evaluate({jet_eta, jet_pt});
            if (jer_shift == "up") {
                sf *= 1 + sf_unc;
            }
            else if (jer_shift == "down") {
                sf *= 1 - sf_unc;
            }
        }
    }

    // Match the jet to a generator-level jet
    float min_delta_r = 0;
    float gen_pt = -10.0;
    for (int i = 0; i < genjet_pt.size(); ++i) {
        float delta_r = ROOT::VecOps::DeltaR(jet_eta, jet_phi, genjet_eta[i],
                                             genjet_phi[i]);
        if (delta_r > min_delta_r) {
            continue;
        }
        if (delta_r < (jet_radius / 2.) &&
            std::abs(jet_pt - genjet_pt[i]) < (3.0 * resol * jet_pt)) {
            min_delta_r = delta_r;
            gen_pt = genjet_pt[i];
        }
    }

    // Smear the JER by either using the rescaling or the random smearing
    // method
    float delta_jer = 0.0;
    if (gen_pt >= 0.0) {
        delta_jer = (sf - 1.0) * (jet_pt - gen_pt) / jet_pt;
    } else {
        // Jet horn mitigation for run 3
        // If no generator-level jet is found for a reconstructed jet in
        // 2.5 < eta < 3.0, no smearing shall be applied.
        if (std::stoi(era.substr(0, 4)) > 2022 && abs(jet_eta) > 2.5 &&
            abs(jet_eta) < 3.0) {
            delta_jer = 0.0;
        } else {
            delta_jer = randgen.Gaus(0, resol) *
                        (std::sqrt(std::max(std::pow(sf, 2) - 1.0, 0.0)));
        }
    }

    return jet_pt * std::max(0.f, 1.f + delta_jer);
}

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
    ) {
    // Apply the consecutive steps of the jet energy calibration
    auto jet_pt_l1 =
        apply_jes_l1(jet_pt, jet_eta, jet_area, rho, jes_l1_evaluator);
    auto jet_pt_l2rel =
        apply_jes_l2rel(jet_pt_l1, jet_eta, jet_phi, era, jes_l2rel_evaluator);
    auto jet_pt_syst = apply_jes_shifts(jet_pt_l2rel, jet_eta, jet_phi, jet_id,
                                        jes_shift_sources, jes_shift_factor,
                                        jes_shift_evaluators);
    auto jet_pt_jer = apply_jer(
        jet_pt_syst, jet_eta, jet_phi, rho, genjet_pt, genjet_eta, genjet_phi,
        jer_resolution_evaluator, jer_scalefactor_evaluator, jer_scalefactor_uncertainty_evaluator, jer_shift,
        jet_radius, era, randgen);

    // Create the JECResult which also contains intermediate results of the
    // calibration
    auto result = physicsobject::jet::jec::JECResult{
        jet_pt_l1, jet_pt_l2rel,
        jet_pt_l2rel, // not applied to MC, so this is just the correction after
                      // L2rel
        jet_pt_syst, jet_pt_jer};

    return result;
}

JECResult apply_jes_shifts_and_jer_mc(
    const float &jet_pt, const float &jet_eta, const float &jet_phi,
    const UChar_t &jet_id, const float &rho, const ROOT::RVec<float> &genjet_pt,
    const ROOT::RVec<float> &genjet_eta, const ROOT::RVec<float> &genjet_phi,
    const std::vector<std::string> &jes_shift_sources,
    const int &jes_shift_factor, const std::string &jer_shift,
    const float &jet_radius, const std::string &era, TRandom3 randgen,
    const std::vector<correction::Correction *> &jes_shift_evaluators,
    const correction::Correction *jer_resolution_evaluator,
    const correction::Correction *jer_scalefactor_evaluator, const correction::Correction* jer_scalefactor_uncertainty_evaluator) {
    // Apply the jet energy scale shifts and the resolution smearing
    auto jet_pt_syst =
        apply_jes_shifts(jet_pt, jet_eta, jet_phi, jet_id, jes_shift_sources,
                         jes_shift_factor, jes_shift_evaluators);
    auto jet_pt_jer = apply_jer(
        jet_pt_syst, jet_eta, jet_phi, rho, genjet_pt, genjet_eta, genjet_phi,
        jer_resolution_evaluator, jer_scalefactor_evaluator, jer_scalefactor_uncertainty_evaluator, jer_shift,
        jet_radius, era, randgen);

    // Create the JECResult which also contains intermediate results of the
    // calibration
    auto result = JECResult{jet_pt, // the input is the already JES-corrected pt
                            jet_pt, // the input is the already JES-corrected pt
                            jet_pt, // the input is the already JES-corrected pt
                            jet_pt_syst, jet_pt_jer};

    return result;
}

JECResult apply_full_jec_data(
    const float &jet_pt, const float &jet_eta, const float &jet_phi,
    const float &jet_area, const float &rho, const unsigned int &run,
    const std::string &era, const correction::Correction *jes_l1_evaluator,
    const correction::Correction *jes_l2rel_evaluator,
    const correction::Correction *jes_l2l3res_evaluator) {
    // Apply the consecutive steps of the jet energy calibration
    auto jet_pt_l1 =
        apply_jes_l1(jet_pt, jet_eta, jet_area, rho, jes_l1_evaluator);
    auto jet_pt_l2rel =
        apply_jes_l2rel(jet_pt_l1, jet_eta, jet_phi, era, jes_l2rel_evaluator);
    auto jet_pt_l2l3res =
        apply_jes_l2l3res(jet_pt_l2rel, jet_eta, static_cast<float>(run), era,
                          jes_l2l3res_evaluator);

    // Create the JECResult which also contains intermediate results of the
    // calibration
    auto result = JECResult{
        jet_pt_l1, jet_pt_l2rel, jet_pt_l2l3res,
        jet_pt_l2l3res, // not applied to data, so this is just the correction
                        // after L2L3res
        jet_pt_l2l3res  // no JER smearing applied to data, so this is just the
                        // correction after L2L3res
    };

    return result;
}

ROOT::RDF::RNode Raw(ROOT::RDF::RNode df, const std::string &outputname,
                     const std::string &jet_quantity,
                     const std::string &jet_raw_factor) {
    // Event-level lambda that computes the jet pt before JEC for each jet in
    // the event
    auto func = [](const ROOT::RVec<float> &jet_quantity,
                   const ROOT::RVec<float> &jet_raw_factor) {
        return jet_quantity * (1 - jet_raw_factor);
    };

    return df.Define(outputname, func, {jet_quantity, jet_raw_factor});
}

ROOT::RDF::RNode RawMuonSubtr(ROOT::RDF::RNode df,
                              const std::string &outputname,
                              const std::string &jet_quantity,
                              const std::string &jet_raw_factor,
                              const std::string &jet_muon_subtr_factor) {
    // Event-level lambda that computes the jet pt before JEC and with
    // subtracting the muon component for each jet in the event
    auto callable = [](const ROOT::RVec<float> &jet_quantity,
                       const ROOT::RVec<float> &jet_raw_factor,
                       const ROOT::RVec<float> &jet_muon_subtr_factor) {
        return jet_quantity * (1 - jet_raw_factor) *
               (1 - jet_muon_subtr_factor);
    };

    return df.Define(outputname, callable,
                     {jet_quantity, jet_raw_factor, jet_muon_subtr_factor});
}

ROOT::RDF::RNode RawMuonSubtr(ROOT::RDF::RNode df,
                              const std::string &outputname,
                              const std::string &jet_quantity,
                              const std::string &jet_muon_subtr_factor) {
    // Event-level lambda that computes the jet pt before JEC and with
    // subtracting the muon component for each jet in the event
    auto callable = [](const ROOT::RVec<float> &jet_quantity,
                       const ROOT::RVec<float> &jet_muon_subtr_factor) {
        return jet_quantity * (1 - jet_muon_subtr_factor);
    };

    return df.Define(outputname, callable,
                     {jet_quantity, jet_muon_subtr_factor});
}

/**
 * Compute the regressed jet pt using the UParT/ParticleNet regression factors.
 * 
 * The regressed jet pt is computed, based on the raw jet \$p_{\text{T}}\$,
 * according to
 * https://cms-jerc.web.cern.ch/JES/#remarks-on-getting-rawpt-and-mass-for-regular-pnet-and-upart-jets.
 *
 * @param df The input dataframe.
 * @param outputname The name of the output column for the regressed jet pt or
       mass.
 * @param jet_quantity_raw The name of the input column for the raw jet pt or
 *     mass.
 * @param jet_reg_factor The name of the input column for the regression factor.
 * @param jet_reg_factor_with_neutrino The name of the input column for the
 *     regression factor including neutrinos (only applied to b-tagged jets).
 * @param jet_is_btagged The name of the input column indicating whether the jet
 *     is b-tagged.
 * @param algo The regression algorithm to use ("UParTAK4" or "PNet"). The
 *     formula for calculating the regressed p_T differs for these two
 *     algorithms.
 * @return A dataframe with a new column of regressed jet pt or mass.
 */
ROOT::RDF::RNode Regressed(ROOT::RDF::RNode df, const std::string &outputname,
                     const std::string &jet_quantity_raw,
                    const std::string &jet_reg_factor,
                     const std::string &jet_reg_factor_with_neutrino,
                    const std::string &jet_is_btagged,
                    const std::string &algo
                ) {

    if (algo != "UParTAK4" and algo != "PNet") {
        Logger::get("jet::jec::Regressed")->error("Invalid regression algorithm specified: {}. Possible values are 'UParTAK4' and 'PNet'.", algo);
        throw std::runtime_error("Invalid regression algorithm specified");
    }
    
    auto func = [algo] (
        const ROOT::RVec<float> &jet_quantity_raw,
        const ROOT::RVec<float> &jet_reg_factor,
        const ROOT::RVec<float> &jet_reg_factor_with_neutrino,
        const ROOT::RVec<int> &jet_is_btagged
    ) {
        return ROOT::VecOps::Map(
            jet_quantity_raw,
            jet_reg_factor,
            jet_reg_factor_with_neutrino,
            jet_is_btagged,
            [algo] (
                const float &jet_quantity_raw,
                const float &jet_reg_factor,
                const float &jet_reg_factor_with_neutrino,
                const int &jet_is_btagged
            ) {
                float jet_quantity_regressed;
                if (jet_is_btagged) {
                    if (algo == "PNet") {
                        jet_quantity_regressed = jet_quantity_raw * jet_reg_factor * jet_reg_factor_with_neutrino;
                    } else if (algo == "UParTAK4") {
                        jet_quantity_regressed = jet_quantity_raw * jet_reg_factor_with_neutrino;
                    }
                } else {
                    jet_quantity_regressed = jet_quantity_raw * jet_reg_factor;
                }
                return jet_quantity_regressed;
            }
        );
    };

    return df.Define(
        outputname,
        func,
        {
            jet_quantity_raw,
            jet_reg_factor,
            jet_reg_factor_with_neutrino,
            jet_is_btagged
        }
    );
}


/**
 * @brief This function applies the full jet energy calibration (JEC) procedure
 * to MC according to the recommendations of the JME POG. The corrections are
 * implemented as a multi-step procedure, where the corrected jet \f$p_T\f$ of
 * the previous step serves as input for the next step.
 *
 * The jet energy scale (JES) in simulation is corrected in two steps
 * ([JES recipe](https://cms-jerc.web.cern.ch/JES/)):
 * - `L1FastJet`: Correction for the offset of the energy measurement due to
 *   pileup.
 * - `L2Relative`: Correction to bring the response of reconstructed-level jets
 *   relative to particle-level jets to 1.
 * These steps are only processed by this function if the parameter
 * `reapply_jes` is set to `true`. Otherwise, make sure that the `jet_pt_raw`
 * function contains the already JES-corrected jet \f$p_T\f$ values, e.g., from
 * the input NANOAOD file.
 *
 * Systematic shifts encoding different sources of uncertainties are
 * applied on top of the outcome of these corrections. Recommendations for the
 * uncertainty scheme to use can be found in the
 * [JES uncertainty
 * recipe](https://cms-jerc.web.cern.ch/JECUncertaintySources/).
 *
 * On top of the outcome of the previous steps, a jet energy resolution smearing
 * is performed, details can be found in the
 * [JER recipe](https://cms-jerc.web.cern.ch/JER/). This function uses the
 * hybrid method to smear the resolution of reconstructed jets in simulation.
 * The JER corrections are also associated with systematic uncertainties.
 *
 * The corrections are provided as JSON files provided by the JME POG. The
 * most recent recommendations on the use of these files can be found in
 * the
 * [JERC
 * documentation](https://cms-jerc.web.cern.ch/Recommendations/#jet-energy-scale).
 * Specifications of the data format for corresponding eras can be found in the
 * [CMS analysis corrections
 * documentation](https://cms-analysis-corrections.docs.cern.ch/corrections/JME/).
 *
 * @param df input dataframe
 * @param correction_manager correction manager responsible for loading the jet
 * energy correction file
 * @param output_jec_result name of the output column for storing a `JECResult`
 * object containing intermediate results of the calibration of the jet
 * \f$p_T\f$
 * @param output_l1 name of the output column for corrected jet \f$p_T\f$ after
 * the `L1FastJet` correction level
 * @param output_l2rel name of the output column for corrected jet \f$p_T\f$
 * after the `L2Relative` correction level
 * @param output_l2l3res name of the output column for corrected jet \f$p_T\f$
 * after the `L2L3Residual` correction level
 * @param output_full name of the output column for corrected jet \f$p_T\f$
 * after the full procedure
 * @param jet_pt_raw collection column of raw jet \f$p_T\f$ before the
 * calibration; if `reapply_jes` is set to `true`, this column is interpreted as
 * the already JES-corrected jet \f$p_T\f$.
 * @param jet_eta collection column of jet \f$\eta\f$
 * @param jet_phi collection column of jet \f$\phi\f$
 * @param jet_area collection column of area that the clustered object covers in
 * \f$\eta\f$-\f$\phi\f$ plane
 * @param jet_id collection column of jet ID
 * @param genjet_pt collection column of particle-level jet \f$p_T\f$
 * @param genjet_eta collection column of particle-level jet \f$\eta\f$
 * @param genjet_phi collection column of particle-level jet \f$\phi\f$
 * @param rho column containing the average event energy density
 * @param jer_seed column with eventwise seed value for the random number
 * generator that is used for the jet energy resolution smearing
 * @param jec_file path to the JEC correction file
 * @param jec_algo name of the jet reconstruction algorithm (e.g., "AK4PFchs" or
 * "AK8PFPuppi")
 * @param jes_tag tag of the JES correction campaign (e.g., "Summer19UL18_V5")
 * @param jer_tag tag of the JER correction campaign (e.g., "Summer19UL18_JRV2")
 * @param jes_shift_sources list of JES shift sources for the systematic shift
 * to be applied
 * @param jes_shift_factor factor of the JES shift variation (0 = nominal, +/-1
 * = up/down)
 * @param jer_shift name of the JER shift variation ("nom", "up", or "down")
 * @param reapply_jes flag to reapply the jet energy calibration, otherwise
 * `jet_pt_raw` is taken as the already JES-corrected \f$p_T\f$
 * @param era string defining the currently processed era, needed due to
 * different kind of recommendations from JME POG for different eras
 *
 * @return A dataframe with a new column of corrected jet \f$p_T\f$'s
 */
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
               const bool &reapply_jes, const std::string &era) {
    // In nanoAODv12 the type of jet/fatjet ID was changed to UChar_t
    // For v9 compatibility a type casting is applied
    auto [df1, jet_id_v12] =
        utility::Cast<ROOT::RVec<UChar_t>, ROOT::RVec<Int_t>>(
            df, jet_id + "_v12", "ROOT::VecOps::RVec<UChar_t>", jet_id);

    // Identify jet radius from algorithm
    float jet_radius = 0.4;
    if (jec_algo.find("AK8") != std::string::npos) {
        jet_radius = 0.8;
    }

    // Set the type tag to "MC"
    const std::string type_tag = "MC";

    // Load the nominal jet energy scale evaluators
    auto jes_l1_evaluator = load_nominal_jes_correction(
        correction_manager, jec_file, jes_tag, type_tag, "L1FastJet", jec_algo);
    auto jes_l2rel_evaluator =
        load_nominal_jes_correction(correction_manager, jec_file, jes_tag,
                                    type_tag, "L2Relative", jec_algo);

    // Load the jet energy scale variation evaluators
    std::vector<correction::Correction *> jes_shift_evaluators;
    for (const auto &source : jes_shift_sources) {
        if (source != "" && source != "HEMIssue") {
            auto evaluator = const_cast<correction::Correction *>(
                load_shifted_jes_correction(correction_manager, jec_file,
                                            jes_tag, type_tag, source,
                                            jec_algo));
            jes_shift_evaluators.push_back(evaluator);
        }
    }

    // Load the jet energy resolution evaluators
    auto jer_resolution_evaluator =
        load_jer_correction(correction_manager, jec_file, jer_tag, type_tag,
                            "PtResolution", jec_algo);
    auto jer_scalefactor_evaluator =
        load_jer_correction(correction_manager, jec_file, jer_tag, type_tag,
                            "ScaleFactor", jec_algo);
    auto jer_scalefactor_uncertainty_evaluator =
        load_jer_correction(correction_manager, jec_file, jer_tag, type_tag,
                            "SFUncertainty", jec_algo);

    // Function to retrieve the JEC result with intermediate steps
    auto func_jec_result = [jes_shift_sources, jes_shift_factor, jer_shift,
                            jet_radius, reapply_jes, era, jes_l1_evaluator,
                            jes_l2rel_evaluator, jes_shift_evaluators,
                            jer_resolution_evaluator,
                            jer_scalefactor_evaluator,
                            jer_scalefactor_uncertainty_evaluator
    ](
                               const ROOT::RVec<float> &jet_pt_raw,
                               const ROOT::RVec<float> &jet_eta,
                               const ROOT::RVec<float> &jet_phi,
                               const ROOT::RVec<UChar_t> &jet_id,
                               const ROOT::RVec<float> &jet_area,
                               const ROOT::RVec<float> &genjet_pt,
                               const ROOT::RVec<float> &genjet_eta,
                               const ROOT::RVec<float> &genjet_phi,
                               const float &rho, const unsigned int &seed) {
        // Random value generator for jet energy resolution smearing
        TRandom3 randgen = TRandom3(seed);

        ROOT::RVec<JECResult> jet_jec_result;
        if (reapply_jes) {
            // Apply the jet energy scale and resolution corrections to MC
            // events. This is done by using the corresponding helper function
            // for single jets and wrap it with ROOT::VecOps::Map to retrieve
            // the calibrated momenta for the full collection.
            jet_jec_result = ROOT::VecOps::Map(
                jet_pt_raw, jet_eta, jet_phi, jet_id, jet_area,
                [rho, genjet_pt, genjet_eta, genjet_phi, jes_shift_sources,
                 jes_shift_factor, jer_shift, jet_radius, era, randgen,
                 jes_l1_evaluator, jes_l2rel_evaluator, jes_shift_evaluators,
                 jer_resolution_evaluator, jer_scalefactor_evaluator, jer_scalefactor_uncertainty_evaluator](
                    const float &jet_pt, const float &jet_eta,
                    const float &jet_phi, const float &jet_id,
                    const float &jet_area) {
                    return apply_full_jec_mc(
                        jet_pt, jet_eta, jet_phi, jet_id, jet_area, rho,
                        genjet_pt, genjet_eta, genjet_phi, jes_shift_sources,
                        jes_shift_factor, jer_shift, jet_radius, era, randgen,
                        jes_l1_evaluator, jes_l2rel_evaluator,
                        jes_shift_evaluators, jer_resolution_evaluator,
                        jer_scalefactor_evaluator, jer_scalefactor_uncertainty_evaluator);
                });
        } else {
            // The jet_pt_raw is already the jet energy scale-corrected pt.
            // Only shifts and and resolution corrections need to be applied
            // on top of it. This is done by using the corresponding helper
            // function for single jets and wrap it with ROOT::VecOps::Map to
            // retrieve the calibrated momenta for the full collection.
            jet_jec_result = ROOT::VecOps::Map(
                jet_pt_raw, jet_eta, jet_phi, jet_id, jet_area,
                [rho, genjet_pt, genjet_eta, genjet_phi, jes_shift_sources,
                 jes_shift_factor, jer_shift, jet_radius, era, randgen,
                 jes_shift_evaluators, jer_resolution_evaluator,
                 jer_scalefactor_evaluator, jer_scalefactor_uncertainty_evaluator](
                    const float &jet_pt, const float &jet_eta,
                    const float &jet_phi, const float &jet_id,
                    const float &jet_area) {
                    return apply_jes_shifts_and_jer_mc(
                        jet_pt, jet_eta, jet_phi, jet_id, rho, genjet_pt,
                        genjet_eta, genjet_phi, jes_shift_sources,
                        jes_shift_factor, jer_shift, jet_radius, era, randgen,
                        jes_shift_evaluators, jer_resolution_evaluator,
                        jer_scalefactor_evaluator, jer_scalefactor_uncertainty_evaluator);
                });
        }
        return jet_jec_result;
    };

    // Function to store the L1FastJet step outcome in a column
    auto func_pt_l1 = [](const ROOT::RVec<JECResult> &jec_result) {
        // Retrieve the result from the JECResult struct eventwise and wrap
        // with ROOT::VecOps::Map to get the result collection.
        auto jet_pt_l1 =
            ROOT::VecOps::Map(jec_result, [](const JECResult &jec_result) {
                return jec_result.jet_pt_l1;
            });
        return jet_pt_l1;
    };

    // Function to store the L2Rel step outcome in a column
    auto func_pt_l2rel = [](const ROOT::RVec<JECResult> &jec_result) {
        // Retrieve the result from the JECResult struct eventwise and wrap
        // with ROOT::VecOps::Map to get the result collection.
        auto jet_pt_l2rel =
            ROOT::VecOps::Map(jec_result, [](const JECResult &jec_result) {
                return jec_result.jet_pt_l2rel;
            });
        return jet_pt_l2rel;
    };

    // Function to store the L2L3Residual step outcome in a column
    auto func_pt_l2l3res = [](const ROOT::RVec<JECResult> &jec_result) {
        // Retrieve the result from the JECResult struct eventwise and wrap
        // with ROOT::VecOps::Map to get the result collection.
        auto jet_pt_l2l3res =
            ROOT::VecOps::Map(jec_result, [](const JECResult &jec_result) {
                return jec_result.jet_pt_l2l3res;
            });
        return jet_pt_l2l3res;
    };

    // Function to store the full procedure outcome in a column
    auto func_pt_full = [](const ROOT::RVec<JECResult> &jec_result) {
        // Retrieve the result from the JECResult struct eventwise and wrap
        // with ROOT::VecOps::Map to get the result collection.
        auto jet_pt_final =
            ROOT::VecOps::Map(jec_result, [](const JECResult &jec_result) {
                return jec_result.jet_pt_corr;
            });
        return jet_pt_final;
    };

    // Store the JECResult
    auto df2 = df1.Define(output_jec_result, func_jec_result,
                          {jet_pt_raw, jet_eta, jet_phi, jet_id_v12, jet_area,
                           genjet_pt, genjet_eta, genjet_phi, rho, jer_seed});

    // Store the L1FastJet-corrected pt
    auto df3 = df2.Define(output_l1, func_pt_l1, {output_jec_result});

    // Store the L2Relative-corrected pt
    auto df4 = df3.Define(output_l2rel, func_pt_l2rel, {output_jec_result});

    // Store the L2L3Residual-corrected pt
    auto df5 = df4.Define(output_l2l3res, func_pt_l2l3res, {output_jec_result});

    // Store the corrected pt after the full JEC procedure
    auto df6 = df5.Define(output_full, func_pt_full, {output_jec_result});

    return df6;
}

/**
 * @brief This function applies the full jet energy calibration (JEC) procedure
 * to data according to the recommendations of the JME POG. The corrections are
 * implemented as a multi-step procedure, where the corrected jet \f$p_T\f$ of
 * the previous step serves as input for the next step.
 *
 * The jet energy scale (JES) in simulation is corrected in two steps
 * ([JES recipe](https://cms-jerc.web.cern.ch/JES/)):
 * - `L1FastJet`: Correction for the offset of the energy measurement due to
 *   pileup.
 * - `L2Relative`: Correction to bring the response of reconstructed-level jets
 *   relative to particle-level jets to 1.
 * - `L2L3Residual`: Relative (\f$\eta\f$-dependent) and absolute
 *   (\f$p_T\f$-dependent) corrections to the jet \f$p_T\f to correct for
 *   residual differences between data and simulation, introduced in the
 *   `L2Relative` step.
 * These steps are only processed by this function if the parameter
 * `reapply_jes` is set to `true`. Otherwise, make sure that the `jet_pt_raw`
 * function contains the already JES-corrected jet \f$p_T\f$ values, e.g., from
 * the input NANOAOD file.
 *
 * The corrections are provided as JSON files provided by the JME POG. The
 * most recent recommendations on the use of these files can be found in
 * the
 * [JERC
 * documentation](https://cms-jerc.web.cern.ch/Recommendations/#jet-energy-scale).
 * Specifications of the data format for corresponding eras can be found in the
 * [CMS analysis corrections
 * documentation](https://cms-analysis-corrections.docs.cern.ch/corrections/JME/).
 *
 * @param df input dataframe
 * @param correction_manager correction manager responsible for loading the jet
 * energy correction file
 * @param output_jec_result name of the output column for storing a `JECResult`
 * object containing intermediate results of the calibration of the jet
 * \f$p_T\f$
 * @param output_l1 name of the output column for corrected jet \f$p_T\f$ after
 * the `L1FastJet` correction level
 * @param output_l2rel name of the output column for corrected jet \f$p_T\f$
 * after the `L2Relative` correction level
 * @param output_l2l3res name of the output column for corrected jet \f$p_T\f$
 * after the `L2L3Residual` correction level
 * @param output_full name of the output column for corrected jet \f$p_T\f$
 * after the full procedure
 * @param jet_pt_raw collection column of raw jet \f$p_T\f$ before the
 * calibration; if `reapply_jes` is set to `true`, this column is interpreted as
 * the already JES-corrected jet \f$p_T\f$.
 * @param jet_eta collection column of jet \f$\eta\f$
 * @param jet_phi collection column of jet \f$\phi\f$
 * @param jet_area collection column of area that the clustered object covers in
 * \f$\eta\f$-\f$\phi\f$ plane
 * @param rho column containing the average event energy density
 * @param run run index of the event
 * @param jec_file path to the JEC correction file
 * @param jec_algo name of the jet reconstruction algorithm (e.g., "AK4PFchs" or
 * "AK8PFPuppi")
 * @param jes_tag tag of the JES correction campaign (e.g., "Summer19UL18_V5")
 * @param jer_shift name of the JER shift variation ("nom", "up", or "down")
 * @param reapply_jes flag to reapply the jet energy calibration, otherwise
 * `jet_pt_raw` is taken as the already JES-corrected \f$p_T\f$
 * @param era string defining the currently processed era, needed due to
 * different kind of recommendations from JME POG for different eras
 *
 * @return A dataframe with a new column of corrected jet \f$p_T\f$'s
 */
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
                 const bool &reapply_jes, const std::string &era) {
    // Identify jet radius from algorithm
    float jet_radius = 0.4;
    if (jec_algo.find("AK8") != std::string::npos) {
        jet_radius = 0.8;
    }

    // Set the type tag to "DATA"
    const std::string type_tag = "DATA";

    // Load the nominal jet energy scale evaluators
    auto jes_l1_evaluator = load_nominal_jes_correction(
        correction_manager, jec_file, jes_tag, type_tag, "L1FastJet", jec_algo);
    auto jes_l2rel_evaluator =
        load_nominal_jes_correction(correction_manager, jec_file, jes_tag,
                                    type_tag, "L2Relative", jec_algo);
    auto jes_l2l3res_evaluator =
        load_nominal_jes_correction(correction_manager, jec_file, jes_tag,
                                    type_tag, "L2L3Residual", jec_algo);

    // Function to retrieve the JEC result with intermediate steps
    auto func_jec_result =
        [era, reapply_jes, jes_l1_evaluator, jes_l2rel_evaluator,
         jes_l2l3res_evaluator](const ROOT::RVec<float> &jet_pt_raw,
                                const ROOT::RVec<float> &jet_eta,
                                const ROOT::RVec<float> &jet_phi,
                                const ROOT::RVec<float> &jet_area,
                                const float &rho, const unsigned int &run) {
            ROOT::RVec<JECResult> jet_jec_result;
            if (reapply_jes) {
                // Apply the jet energy scale corrections to data. This is done
                // by using the corresponding helper function for single jets
                // and wrap it with ROOT::VecOps::Map to retrieve the calibrated
                // momenta for the full collection.
                jet_jec_result = ROOT::VecOps::Map(
                    jet_pt_raw, jet_eta, jet_phi, jet_area,
                    [rho, run, era, jes_l1_evaluator, jes_l2rel_evaluator,
                     jes_l2l3res_evaluator](
                        const float &jet_pt, const float &jet_eta,
                        const float &jet_phi, const float &jet_area) {
                        return apply_full_jec_data(
                            jet_pt, jet_eta, jet_phi, jet_area, rho, run, era,
                            jes_l1_evaluator, jes_l2rel_evaluator,
                            jes_l2l3res_evaluator);
                    });
            } else {
                // Nothing needs to be done here as the input jet_pt_raw is
                // interpreted as the already corrected jet pt.
                // ROOT::VecOps::Map is used to create dummy JECResult objects
                // in order to allow consistent processing with the other branch
                // of this if else query.
                jet_jec_result =
                    ROOT::VecOps::Map(jet_pt_raw, [](const float &jet_pt) {
                        return JECResult{
                            jet_pt, // the input is the already JES-corrected pt
                            jet_pt, // the input is the already JES-corrected pt
                            jet_pt, // the input is the already JES-corrected pt
                            jet_pt, // the input is the already JES-corrected pt
                            jet_pt, // the input is the already JES-corrected pt
                        };
                    });
            }

            return jet_jec_result;
        };

    // Function to store the L1FastJet step outcome in a column
    auto func_pt_l1 = [](const ROOT::RVec<JECResult> &jec_result) {
        // Retrieve the result from the JECResult struct eventwise and wrap
        // with ROOT::VecOps::Map to get the result collection.
        auto jet_pt_l1 =
            ROOT::VecOps::Map(jec_result, [](const JECResult &jec_result) {
                return jec_result.jet_pt_l1;
            });
        return jet_pt_l1;
    };

    // Function to store the L2Rel step outcome in a column
    auto func_pt_l2rel = [](const ROOT::RVec<JECResult> &jec_result) {
        // Retrieve the result from the JECResult struct eventwise and wrap
        // with ROOT::VecOps::Map to get the result collection.
        auto jet_pt_l2rel =
            ROOT::VecOps::Map(jec_result, [](const JECResult &jec_result) {
                return jec_result.jet_pt_l2rel;
            });
        return jet_pt_l2rel;
    };

    // Function to store the L2L3Residual step outcome in a column
    auto func_pt_l2l3res = [](const ROOT::RVec<JECResult> &jec_result) {
        // Retrieve the result from the JECResult struct eventwise and wrap
        // with ROOT::VecOps::Map to get the result collection.
        auto jet_pt_l2l3res =
            ROOT::VecOps::Map(jec_result, [](const JECResult &jec_result) {
                return jec_result.jet_pt_l2l3res;
            });
        return jet_pt_l2l3res;
    };

    // Function to store the full procedure outcome in a column
    auto func_pt_full = [](const ROOT::RVec<JECResult> &jec_result) {
        // Retrieve the result from the JECResult struct eventwise and wrap
        // with ROOT::VecOps::Map to get the result collection.
        auto jet_pt_final =
            ROOT::VecOps::Map(jec_result, [](const JECResult &jec_result) {
                return jec_result.jet_pt_corr;
            });
        return jet_pt_final;
    };

    // Store the JECResult
    auto df1 = df.Define(output_jec_result, func_jec_result,
                         {jet_pt_raw, jet_eta, jet_phi, jet_area, rho, run});

    // Store the L1FastJet-corrected pt
    auto df2 = df1.Define(output_l1, func_pt_l1, {output_jec_result});

    // Store the L2Relative-corrected pt
    auto df3 = df2.Define(output_l2rel, func_pt_l2rel, {output_jec_result});

    // Store the L2L3Residual-corrected pt
    auto df4 = df3.Define(output_l2l3res, func_pt_l2l3res, {output_jec_result});

    // Store the corrected pt after the full JEC procedure
    auto df5 = df4.Define(output_full, func_pt_full, {output_jec_result});

    return df5;
}

/**
 * @brief This function modifies the mass of objects in an event using the
 * formula \f[ M_{\text{corrected},i} = M_{\text{raw},i} \times
 * \frac{p_{T,\text{corrected},i}}{p_{T,\text{raw},i}} \f] for each object of an
 * object collection in the event. The correction is applied element-wise to the
 * mass vector and is needed as part of for example energy scale corrections
 * that were before to the transverse momenta.
 *
 * @param df input dataframe
 * @param outputname name of the output column storing the corrected masses
 * @param raw_mass name of the column containing raw object masses
 * @param raw_pt name of the column containing raw object transverse momenta
 * @param corrected_pt name of the column containing corrected transverse
 * momenta
 *
 * @return a dataframe with a new column
 */
ROOT::RDF::RNode MassCorrectionFromPt(ROOT::RDF::RNode df,
                                      const std::string &outputname,
                                      const std::string &jet_mass_raw,
                                      const std::string &jet_pt_raw,
                                      const std::string &jet_pt_corrected) {
    // Function to align the jet mass to the corrected jet pt
    auto func = [](const ROOT::RVec<float> &jet_mass_raw,
                   const ROOT::RVec<float> &jet_pt_raw,
                   const ROOT::RVec<float> &jet_pt_corrected) {
        return jet_mass_raw * jet_pt_corrected / jet_pt_raw;
    };

    auto df1 = df.Define(outputname, func,
                         {jet_mass_raw, jet_pt_raw, jet_pt_corrected});
    return df1;
}

} // end namespace jec

namespace quantities {

/**
 * Evaluate the tightest b jet working point that a jet passes.
 *
 * @param df input dataframe
 * @param correction_manager correction manager responsible for loading the b
 * jet tagging score working point definitions
 * @param outputname name of the output column storing the tightest WP passed
 * @param btag_value name of the column containing the b jet tagging score
 * @param sf_file path to the b jet tagging score working point definition file
 * @param sf_wp_name name of the working point definition set in the correction
 *     file
 * @return a dataframe with the new column
 */
ROOT::RDF::RNode TightestWPPassed(
           ROOT::RDF::RNode df,
           correctionManager::CorrectionManager &correction_manager,
           const std::string &outputname, const std::string &btag_value,
           const std::string &sf_file, const std::string &sf_wp_name
) {
    // Get evaluator for WP definitions from correctionlib file
    auto wp_evaluator = correction_manager.loadCorrection(sf_file, sf_wp_name);

    // Sort the working points in descending order to find the tightest WP passed
    auto wp_names = std::vector<std::string>({"L", "M", "T", "XT", "XXT"});
    auto wp_cuts = std::vector<float>(wp_names.size());
    for (auto &wp_name : wp_names) {
        wp_cuts.push_back(wp_evaluator->evaluate({wp_name}));
    }

    auto func = [wp_cuts, wp_names] (ROOT::RVec<float> &btag_value) {
        return ROOT::VecOps::Map(
            btag_value,
            [wp_cuts, wp_names] (const float &btag_value) {
                std::string tightest_wp = "U";
                for (size_t i = 0; i < wp_cuts.size(); ++i) {
                    if (btag_value > wp_cuts[i]) {
                        // If the jet passes the current WP, store it as the
                        // tightest WP passed
                        tightest_wp = wp_names[i];
                    } else {
                        break; // Since wp_cuts are sorted in ascending order
                    }
                }
                Logger::get("jet::quantities::TightestWPPassed")
                    ->debug("Evaluated tightest WP for btag value {} to {}",
                            btag_value,
                            tightest_wp);
                return tightest_wp;
            }
        );
    };

    return df.Define(
        outputname,
        func,
        {
            btag_value
        }
    );
}

/**
 * Evaluate whether a b jet passes a given tagger working point.
 *
 * @param df input dataframe
 * @param correction_manager correction manager responsible for loading the b
 * jet tagging score working point definitions
 * @param outputname name of the output column storing the tightest WP passed
 * @param btag_value name of the column containing the b jet tagging score
 * @param sf_file path to the b jet tagging score working point definition file
 * @param sf_wp_name name of the working point definition set in the correction
 *     file
 * @param btag_wp_name name of the working point to evaluate
 * @return a dataframe with the new column
 */
ROOT::RDF::RNode IsBTagged(
           ROOT::RDF::RNode df,
           correctionManager::CorrectionManager &correction_manager,
           const std::string &outputname, const std::string &btag_value,
           const std::string &sf_file, const std::string &sf_wp_name,
           const std::string &btag_wp_name
) {
    // Set the logger name for better readability in debug messages
    const std::string logger_name = "jet::quantities::IsBTagged";

    // Debug messages for loading corrections
    Logger::get(logger_name)
        ->debug(
            "Evaluate b jet tagging scores with respect to fixed WP {}",
            btag_wp_name
        );
    Logger::get(logger_name)->debug("working point cset name {}", sf_wp_name);

    // Get evaluator for WP definitions from correctionlib file
    auto wp_evaluator = correction_manager.loadCorrection(sf_file, sf_wp_name);

    // Get the b jet tagging score to cut on for the given working point
    float btag_wp_cut = wp_evaluator->evaluate({btag_wp_name});

    auto func = [btag_wp_cut] (ROOT::RVec<float> &btag_value) {
        return ROOT::VecOps::Map(
            btag_value,
            [btag_wp_cut] (const float &score) { return static_cast<int>(score > btag_wp_cut); }
        );
    };

    return df.Define(
        outputname,
        func,
        {
            btag_value
        }
    );
}

/**
 * @brief Patch for wrong Jet ID values in Run3 NanoAOD v12 samples.
 *
 * The implementation follows the recipe by the [JME
 * POG](https://twiki.cern.ch/twiki/bin/view/CMS/JetID13p6TeV#nanoAOD_Flags).
 *
 * @param df the input dataframe
 * @param outputname the name of the produced column
 * @param jet_pt name of the column with jet pt values
 * @param jet_eta name of the column with jet eta values
 * @param jet_id name of the column with (broken) jet ID values
 * @param jet_ne_hef name of the column with neutral hadron energy fraction
 * @param jet_ne_em_ef name of the column with neutral EM energy fraction
 * @param jet_mu_ef name of the column with muon energy fraction
 * @param jet_ch_em_ef name of the column with charged EM energy fraction
 *
 * @return a dataframe with the new column
 */
ROOT::RDF::RNode CorrectJetIDRun3NanoV12(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &jet_pt, const std::string &jet_eta,
    const std::string &jet_id, const std::string &jet_ne_hef,
    const std::string &jet_ne_em_ef, const std::string &jet_mu_ef,
    const std::string &jet_ch_em_ef) {

    // we do not need to ensure the correct casting for NanoAOD v9 samples here
    // as this fix applies to NanoAOD v12 samples only

    auto correction = [](const ROOT::RVec<float> &jet_pt,
                         const ROOT::RVec<float> &jet_eta,
                         const ROOT::RVec<UChar_t> &jet_id_v12,
                         const ROOT::RVec<float> &jet_ne_hef,
                         const ROOT::RVec<float> &jet_ne_em_ef,
                         const ROOT::RVec<float> &jet_mu_ef,
                         const ROOT::RVec<float> &jet_ch_em_ef) {
        // cast jet_id to integer
        auto jet_id = static_cast<ROOT::RVec<int>>(jet_id_v12);

        // apply the JME POG recipe
        auto jet_id_corrected = ROOT::RVec<int>(jet_id.size(), 0);
        for (int i = 0; i < jet_pt.size(); ++i) {
            // evaluate if the jet passes the tight WP
            bool pass_tight = false;
            if (abs(jet_eta.at(i)) <= 2.7) {
                pass_tight = jet_id.at(i) & (1 << 1);
            } else if (abs(jet_eta.at(i)) > 2.7 && abs(jet_eta.at(i)) <= 3.0) {
                pass_tight =
                    (jet_id.at(i) & (1 << 1)) && (jet_ne_hef.at(i) < 0.99);
            } else if (abs(jet_eta.at(i)) > 3.0) {
                pass_tight =
                    (jet_id.at(i) & (1 << 1)) && (jet_ne_em_ef.at(i) < 0.4);
            }

            // evaluate if the jet passes the tight WP and fulfills the lepton
            // veto
            bool pass_tight_lep_veto = false;
            if (abs(jet_eta.at(i)) <= 2.7) {
                pass_tight_lep_veto = pass_tight && (jet_mu_ef.at(i) < 0.8) &&
                                      (jet_ch_em_ef.at(i) < 0.8);
            } else {
                pass_tight_lep_veto = pass_tight;
            }

            // return value of the working point that is passed
            // - 0 == fail
            // - 2 == pass tight & fail tightlepveto
            // - 6 == pass tight & pass tightlepveto
            if (pass_tight && !pass_tight_lep_veto) {
                jet_id_corrected[i] = 2;
            } else if (pass_tight && pass_tight_lep_veto) {
                jet_id_corrected[i] = 6;
            } else {
                jet_id_corrected[i] = 0;
            }
        }

        // convert the data type to default in NanoAOD v12 (UChar_t)
        auto jet_id_corrected_v12 =
            static_cast<ROOT::RVec<Int_t>>(jet_id_corrected);

        return jet_id_corrected_v12;
    };

    // redefine the data type of the Jet ID mask
    return df.Define(outputname, correction,
                     {jet_pt, jet_eta, jet_id, jet_ne_hef, jet_ne_em_ef,
                      jet_mu_ef, jet_ch_em_ef});
}

ROOT::RDF::RNode JetPtPNetRegression(ROOT::RDF::RNode df,
                                     const std::string &outputname,
                                     const std::string &jet_pt_nanoaod,
                                     const std::string &jet_raw_factor,
                                     const std::string &jet_pnet_reg_pt_factor,
                                     const std::string &jet_collection_index) {
    auto correction = [](const ROOT::RVec<float> &jet_pt_nanoaod,
                         const ROOT::RVec<float> &jet_raw_factor,
                         const ROOT::RVec<float> &jet_pnet_reg_pt_factor,
                         const ROOT::RVec<int> &jet_collection_index) {
        // Jet_rawFactor is 1 - (raw pt)/(corrected pt) (from NANOAOD
        // documentation) Calculate raw pt before JEC
        auto jet_pt_raw = ROOT::VecOps::Take(
            jet_pt_nanoaod * (1 - jet_raw_factor), jet_collection_index);
        auto jet_pt_pnet =
            jet_pt_raw *
            ROOT::VecOps::Take(jet_pnet_reg_pt_factor, jet_collection_index);

        return jet_pt_pnet;
    };

    return df.Define(outputname, correction,
                     {jet_pt_nanoaod, jet_raw_factor, jet_pnet_reg_pt_factor,
                      jet_collection_index});
}

ROOT::RDF::RNode JetPtPNetRegressionWithNeutrino(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &jet_pt_nanoaod, const std::string &jet_raw_factor,
    const std::string &jet_pnet_reg_pt_factor,
    const std::string &jet_pnet_reg_pt_neutrino_factor,
    const std::string &jet_collection_index) {
    auto correction =
        [](const ROOT::RVec<float> &jet_pt_nanoaod,
           const ROOT::RVec<float> &jet_raw_factor,
           const ROOT::RVec<float> &jet_pnet_reg_pt_factor,
           const ROOT::RVec<float> &jet_pnet_reg_pt_neutrino_factor,
           const ROOT::RVec<int> &jet_collection_index) {
            // Jet_rawFactor is 1 - (raw pt)/(corrected pt) (from NANOAOD
            // documentation) Calculate raw pt before JEC
            auto jet_pt_raw = ROOT::VecOps::Take(
                jet_pt_nanoaod * (1 - jet_raw_factor), jet_collection_index);
            auto jet_pt_pnet_neutrino =
                jet_pt_raw *
                ROOT::VecOps::Take(jet_pnet_reg_pt_factor *
                                       jet_pnet_reg_pt_neutrino_factor,
                                   jet_collection_index);

            return jet_pt_pnet_neutrino;
        };

    return df.Define(outputname, correction,
                     {jet_pt_nanoaod, jet_raw_factor, jet_pnet_reg_pt_factor,
                      jet_pnet_reg_pt_neutrino_factor, jet_collection_index});
}

} // namespace quantities

} // namespace jet

} // namespace physicsobject
