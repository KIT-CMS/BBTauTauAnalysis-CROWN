#ifndef GUARDFAKEFACTORS_test_H
#define GUARDFAKEFACTORS_test_H

#include "ROOT/RDataFrame.hxx"
#include "correction.h"
#include "../../../../include/utility/CorrectionManager.hxx"

#include <string>
#include <vector>

namespace fakefactors {

ROOT::RDF::RNode build_model_input_column(
    ROOT::RDF::RNode df,
    const std::string &outputname,
    const std::vector<std::string> &input_columns
);

std::string joinAndReplace(const std::vector<std::string> &strings,
                           const std::string &delimiter);

namespace sm{

    struct NonClosureHandler {
        std::string prefix;
        const correction::CompoundCorrection *compound;
        std::vector<std::string> variables;

        NonClosureHandler(const std::string &proc, const std::string &file,
                          const correction::CompoundCorrection *c);

        float evaluate(const std::string &systematic,
                       std::vector<correction::Variable::Type> args);
    };

    ROOT::RDF::RNode
    raw_fakefactor_lt(
        ROOT::RDF::RNode df,
        correctionManager::CorrectionManager &correctionManager,
        const std::string &outputname,
        // ---
        const std::string &pt_2_input,
        // ---
        const std::string &qcd_ff_input,
        // const std::string &wjets_ff_input,
        const std::string &ttbar_ff_input,
        const std::string &fractions_input,
        // ---
        const std::string &fraction_variation,
        // ---
        const std::string &QCD_variation,
        // const std::string &Wjets_variation,
        const std::string &ttbar_variation,
        // ---
        const std::string &ff_file
    );

    ROOT::RDF::RNode
    fakefactor_lt(
        ROOT::RDF::RNode df, 
        correctionManager::CorrectionManager &correctionManager,
        const std::vector<std::string> &outputnames,
        // ---
        const std::string &pt_2_input,
        // ---
        const std::string &qcd_ff_input,
        // const std::string &wjets_ff_input,
        const std::string &ttbar_ff_input,
        // ---
        const std::string &fractions_input,
        // ---
        const std::string &qcd_DR_SR_input,
        // const std::string &wjets_DR_SR_input,
        // ---
        const std::string &qcd_non_closure_input,
        // const std::string &wjets_non_closure_input,
        const std::string &ttbar_non_closure_input,
        // ---
        const std::string &fraction_variation,
        const std::string &QCD_variation,
        // const std::string &Wjets_variation,
        const std::string &ttbar_variation,
        // ---
        const std::string &QCD_DR_SR_correction_variation,
        const std::string &QCD_non_closure_correction_variation,
        // ---
        // const std::string &Wjets_DR_SR_correction_variation,
        // const std::string &Wjets_non_closure_correction_variation,
        //
        const std::string &ttbar_non_closure_correction_variation,
        // ---
        const std::string &ff_file,
        const std::string &ff_corr_file,
        const bool split_info
    );

ROOT::RDF::RNode
raw_fakefactor_tt(ROOT::RDF::RNode df, correctionManager::CorrectionManager &correctionManager,
    const std::string &outputname,
    const int &tau_idx,
    // ---
    const std::string &pt_1,
    const std::string &pt_2,
    const std::string &m_vis,
    const std::string &njets,
    // ---
    const std::string &qcd_variation,
    const std::string &ttbar_variation,
    const std::string &fraction_variation,
    // ---
    const std::string &ff_file
    );

ROOT::RDF::RNode
fakefactor_tt(ROOT::RDF::RNode df, correctionManager::CorrectionManager &correctionManager,
    const std::string &outputname,
    const int &tau_idx,
    const std::string &decaymode_1,
    const std::string &decaymode_2,
    const std::string &tau_pt_1,
    const std::string &tau_pt_2,
    const std::string &met,
    const std::string &mt_tot,
    const std::string &pt_tt,
    const std::string &mass_1,
    const std::string &mass_2,
    const std::string &m_vis,
    const std::string &njets,
    const std::string &qcd_variation,
    const std::string &ttbar_variation,
    const std::string &fraction_variation,
    const std::string &qcd_non_closure_correction_variation,
    const std::string &qcd_DR_SR_correction_variation,
    const std::string &ttbar_non_closure_correction_variation,
    const std::string &ff_file, const std::string &ff_corr_file);


}  // namespace sm
} // namespace fakefactors
#endif /* GUARDFAKEFACTORS_test_H */
