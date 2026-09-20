#include "../include/electron_reco.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include <algorithm>
#include <cctype>
#include <stdexcept>

namespace xyh::scalefactor {
namespace {
/// Data-taking year encoded in the leading four digits of an EGM era key.
int payload_year(const std::string &era) {
    if (era.size() < 4 ||
        !std::all_of(era.begin(), era.begin() + 4,
                     [](unsigned char c) { return std::isdigit(c); })) {
        throw std::invalid_argument(
            "xyh::scalefactor::electron_reco: era key '" + era +
            "' does not start with a four-digit year");
    }
    return std::stoi(era.substr(0, 4));
}

/// The EGM reconstruction category covering `pt` for the payload layout.
std::string reco_category(float pt, bool run2_layout) {
    if (pt < 20.f) {
        return "RecoBelow20";
    }
    if (run2_layout) {
        return "RecoAbove20";
    }
    return pt < 75.f ? "Reco20to75" : "RecoAbove75";
}
} // namespace

ROOT::RDF::RNode electron_reco(ROOT::RDF::RNode df,
                               correctionManager::CorrectionManager &manager,
                               const std::string &output,
                               const std::string &pt, const std::string &eta,
                               const std::string &phi, const std::string &era,
                               const std::string &file,
                               const std::string &correction,
                               const std::string &variation) {
    const bool run2_layout = payload_year(era) <= 2018;
    // Same era special case as physicsobject::electron::scalefactor::Id: the
    // 2023 payloads take phi as an additional input.
    const bool with_phi = era.find("2023") != std::string::npos;
    auto evaluator = manager.loadCorrection(file, correction);
    return df.Define(
        output,
        [evaluator, era, variation, run2_layout, with_phi](
            float pt, float eta, float phi) {
            if (pt < 0.f) {
                return 1.0;
            }
            const std::string category = reco_category(pt, run2_layout);
            if (with_phi) {
                return evaluator->evaluate({era, variation, category,
                                            double(eta), double(pt),
                                            double(phi)});
            }
            return evaluator->evaluate(
                {era, variation, category, double(eta), double(pt)});
        },
        {pt, eta, phi});
}
} // namespace xyh::scalefactor
