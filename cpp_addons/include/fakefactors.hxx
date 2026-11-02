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

/**
 * @brief Fake factor of one tau leg, summed over the processes of the payload
 * (v7 spec C15):
 *
 *     FF = sum_p f_p * max(FF_p * prod_{c of p} C_c, 0),
 *
 * with the fractions f_p of `fraction_name` (process category `processes[p]`),
 * the fake factors FF_p of `ff_names[p]` and the corrections C_c of
 * `corr_names` that belong to process `corr_processes[c]`, applied in their
 * order; `corr_compound[c]` marks a compound correction. Without corrections
 * it is the raw fake factor. The processes are {QCD, ttbar} or {QCD, Wjets,
 * ttbar}; the float arithmetic is the one of the former two-process function,
 * so a two-process payload gives the same values bit for bit.
 *
 * @param df input dataframe
 * @param correctionManager correction manager
 * @param outputname name of the fake-factor column
 * @param inputs the input-vector columns (fakefactors::BuildFloatVector): the
 * fractions, then the fake factor of each process, then each correction
 * @param processes process categories of the fractions, in summation order
 * @param ff_file file of the fake factors and fractions
 * @param ff_names fake-factor correction of each process
 * @param fraction_name fraction correction
 * @param corr_file file of the corrections
 * @param corr_names the corrections
 * @param corr_processes the process each correction belongs to
 * @param corr_compound 1 for a compound correction, 0 otherwise
 * @param ff_variations syst key of each fake factor
 * @param fraction_variation syst key of the fractions
 * @param corr_variations syst key of each correction
 * @return a dataframe with the fake-factor column
 */
ROOT::RDF::RNode FakeFactor(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correctionManager,
    const std::string &outputname, const std::vector<std::string> &inputs,
    const std::vector<std::string> &processes, const std::string &ff_file,
    const std::vector<std::string> &ff_names, const std::string &fraction_name,
    const std::string &corr_file, const std::vector<std::string> &corr_names,
    const std::vector<std::string> &corr_processes,
    const std::vector<int> &corr_compound,
    const std::vector<std::string> &ff_variations,
    const std::string &fraction_variation,
    const std::vector<std::string> &corr_variations);

} // end namespace xyh

} // namespace fakefactors
#endif /* GUARDFAKEFACTORS_H */
