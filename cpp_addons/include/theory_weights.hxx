#ifndef BBTAUTAU_THEORY_WEIGHTS_HXX
#define BBTAUTAU_THEORY_WEIGHTS_HXX

#include "ROOT/RDataFrame.hxx"
#include <string>
#include <vector>

namespace xyh::theory_weights {
/**
 * @brief A copy of a column of generator weights (`PSWeight`, `LHEPdfWeight`)
 * whose length is checked in every event.
 *
 * The producers behind it read the weights by index. NanoAOD files without
 * the variations carry a vector of another length (a single 1 for the parton
 * shower), and `event::reweighting::PartonShower` checks the length only when
 * it evaluates a variation, so that a nominal column would be written from
 * such a file without notice. Reading the weights through this column stops
 * the job in the first event with a length that is not listed.
 *
 * @param df input dataframe
 * @param outputname name of the output column, a copy of `weights`
 * @param weights name of the column with the weights
 * @param sizes the allowed lengths
 *
 * @return a new dataframe with the checked column
 *
 * @throws std::invalid_argument without a positive allowed length
 * @throws std::runtime_error in the event loop for a vector of another length
 */
ROOT::RDF::RNode CheckedSize(ROOT::RDF::RNode df, const std::string &outputname,
                             const std::string &weights,
                             const std::vector<int> &sizes);
} // namespace xyh::theory_weights
#endif
