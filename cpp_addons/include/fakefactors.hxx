#ifndef GUARDFAKEFACTORS_H
#define GUARDFAKEFACTORS_H

#include "../../../../include/utility/CorrectionManager.hxx"
#include "ROOT/RDataFrame.hxx"
#include "correction.h"

namespace fakefactors {

ROOT::RDF::RNode
BuildFloatVector(ROOT::RDF::RNode df, const std::string &output,
                 const std::vector<std::string> &input_columns);

namespace util {

std::vector<correction::Variable::Type>
to_clib_input(const std::vector<float> &vector);

void prepend(std::vector<correction::Variable::Type> &vector,
             const correction::Variable::Type &value);

void append(std::vector<correction::Variable::Type> &vector,
            const correction::Variable::Type &value);

const std::vector<correction::Variable::Type>
prepare_ff_input(const std::vector<float> &vector,
                 const std::string &variation);

const std::vector<correction::Variable::Type>
prepare_fractions_input(const std::vector<float> &vector,
                        const std::string &process,
                        const std::string &variation);

std::string join(const std::vector<correction::Variable::Type> &vector);

} // end namespace util

namespace xyh {

ROOT::RDF::RNode RawFakeFactorSemileptonic(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correctionManager,
    const std::string &outputname, const std::string &qcd_inputs,
    const std::string &tt_inputs, const std::string &fraction_inputs,
    const std::string &ff_file, const std::string &ff_qcd_name,
    const std::string &ff_tt_name, const std::string &ff_fraction_name,
    const std::string &ff_qcd_variation, const std::string &ff_tt_variation,
    const std::string &ff_fraction_variation);

ROOT::RDF::RNode FakeFactorSemileptonic(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correctionManager,
    const std::string &outputname, const std::string &qcd_inputs,
    const std::string &tt_inputs, const std::string &fraction_inputs,
    const std::string &qcd_corr_dr_sr_inputs,
    const std::string &qcd_corr_closure_inputs,
    const std::string &tt_corr_closure_inputs, const std::string &ff_file,
    const std::string &ff_qcd_name, const std::string &ff_tt_name,
    const std::string &ff_fraction_name, const std::string &corr_file,
    const std::string &corr_qcd_dr_sr_name,
    const std::string &corr_qcd_closure_name,
    const std::string &corr_tt_closure_name,
    const std::string &ff_qcd_variation, const std::string &ff_tt_variation,
    const std::string &ff_fraction_variation,
    const std::string &qcd_corr_dr_sr_variation,
    const std::string &qcd_corr_closure_variation,
    const std::string &tt_corr_closure_variation);
} // end namespace xyh

} // namespace fakefactors
#endif /* GUARDFAKEFACTORS_H */
