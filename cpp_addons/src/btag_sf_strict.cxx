#ifndef GUARDBTAGSFSTRICT_CXX
#define GUARDBTAGSFSTRICT_CXX

#include "../include/btag_sf_strict.hxx"
#include "../../../../include/utility/CorrectionManager.hxx"
#include "../../../../include/utility/Logger.hxx"
#include "../../../../include/utility/utility.hxx"
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "correction.h"
#include <cmath>
#include <cstddef>
#include <exception>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// namespace xyh
namespace xyh {

// namespace scalefactor
namespace scalefactor {

// namespace btagging_strict
namespace btagging_strict {

namespace {

// Compose a compact per-jet kinematics string for the strict error messages.
std::string jet_kinematics(float pt, float eta, int flavor, float score) {
    std::ostringstream os;
    os << "pt=" << pt << " eta=" << eta << " flavor=" << flavor
       << " score=" << score;
    return os.str();
}

} // namespace

ROOT::RDF::RNode multi_wp_event_weight(
    ROOT::RDF::RNode df,
    correctionManager::CorrectionManager &correction_manager,
    const std::string &output, const std::string &jet_pt,
    const std::string &jet_eta, const std::string &jet_flavor,
    const std::string &jet_score, const std::string &jet_mask,
    const std::string &sf_file, const std::string &eff_file,
    const std::string &eff_sample_type, const std::string &variation_comb,
    const std::string &variation_light, const std::vector<float> &wp_values) {

    const std::string logger_name =
        "xyh::scalefactor::btagging_strict::multi_wp_event_weight";

    // The five WP thresholds must line up with the five fixed WP names.
    if (wp_values.size() != kWorkingPointsTightToLoose.size()) {
        throw std::runtime_error(
            logger_name + ": expected " +
            std::to_string(kWorkingPointsTightToLoose.size()) +
            " working-point thresholds (ordered tightest->loosest), got " +
            std::to_string(wp_values.size()));
    }

    Logger::get(logger_name)
        ->debug("strict UParTAK4 multi-WP event weight: comb variation {}, "
                "light variation {}, eff sample_type {}",
                variation_comb, variation_light, eff_sample_type);

    // Load the SF and efficiency evaluators once (shared through the manager).
    auto comb_evaluator =
        correction_manager.loadCorrection(sf_file, kCombCorrection);
    auto light_evaluator =
        correction_manager.loadCorrection(sf_file, kLightCorrection);
    auto eff_evaluator =
        correction_manager.loadCorrection(eff_file, kEfficiencyCorrection);

    // In nanoAODv12/v15 the jet hadron flavor is stored as UChar_t; the cast
    // keeps v9 (Int_t) inputs working, mirroring the core BtaggingMultipleWP.
    auto [df1, flavor_column] =
        utility::Cast<ROOT::RVec<UChar_t>, ROOT::RVec<Int_t>>(
            df, jet_flavor + "_upart_strict_v12",
            "ROOT::VecOps::RVec<UChar_t>", jet_flavor);

    const std::vector<float> thresholds = wp_values;

    auto event_weight =
        [comb_evaluator, light_evaluator, eff_evaluator, thresholds,
         variation_comb, variation_light, eff_sample_type,
         logger_name](const ROOT::RVec<float> &pts,
                      const ROOT::RVec<float> &etas,
                      const ROOT::RVec<UChar_t> &flavors_uc,
                      const ROOT::RVec<float> &scores,
                      const ROOT::RVec<int> &mask) {
            double weight = 1.0;
            auto flavors = static_cast<ROOT::RVec<int>>(flavors_uc);

            for (std::size_t i = 0; i < pts.size(); ++i) {
                if (!mask.at(i)) {
                    continue;
                }

                const float pt = pts.at(i);
                const float eta = etas.at(i);
                const int flavor = flavors.at(i);
                const float score = scores.at(i);
                const float abs_eta = std::abs(eta);
                const std::string kin = jet_kinematics(pt, eta, flavor, score);

                // Strict eta support: the pinned payload's abseta binning uses
                // flow=error at 2.4, so anything at or beyond 2.4 (or a
                // non-finite eta) has no defined correction.
                if (!std::isfinite(abs_eta) || abs_eta >= 2.4f) {
                    throw std::runtime_error(
                        logger_name +
                        ": jet outside the [0, 2.4) eta support of the "
                        "UParTAK4 b-tag corrections (" +
                        kin + ")");
                }

                // Dispatch to the per-flavor correction + variation.
                const correction::Correction *sf_evaluator = nullptr;
                std::string sf_variation;
                if (flavor == 5 || flavor == 4) {
                    sf_evaluator = comb_evaluator;
                    sf_variation = variation_comb;
                } else if (flavor == 0) {
                    sf_evaluator = light_evaluator;
                    sf_variation = variation_light;
                } else {
                    throw std::runtime_error(logger_name +
                                             ": unrecognized jet flavor (" +
                                             kin + ")");
                }

                // Evaluate a SF for a WP, rethrowing correctionlib failures
                // (e.g. an unknown variation key) with the jet kinematics.
                auto eval_sf = [&](const std::string &wp) -> double {
                    try {
                        return sf_evaluator->evaluate(
                            {sf_variation, wp, flavor,
                             static_cast<double>(abs_eta),
                             static_cast<double>(pt)});
                    } catch (const std::exception &error) {
                        throw std::runtime_error(
                            logger_name +
                            ": failed to evaluate b-tag SF (WP " + wp +
                            ", variation '" + sf_variation + "') for " + kin +
                            ": " + error.what());
                    }
                };

                // Evaluate + strictly validate a MC efficiency for a WP.
                auto eval_eff = [&](const std::string &wp) -> double {
                    double eff;
                    try {
                        eff = eff_evaluator->evaluate(
                            {eff_sample_type, wp, flavor,
                             static_cast<double>(abs_eta),
                             static_cast<double>(pt)});
                    } catch (const std::exception &error) {
                        throw std::runtime_error(
                            logger_name +
                            ": failed to evaluate b-tag efficiency (WP " + wp +
                            ", sample_type '" + eff_sample_type + "') for " +
                            kin + ": " + error.what());
                    }
                    if (!std::isfinite(eff) || eff <= 0.0 || eff > 1.0) {
                        throw std::runtime_error(
                            logger_name + ": invalid b-tag efficiency " +
                            std::to_string(eff) + " (WP " + wp +
                            ") must be finite and in (0, 1] for " + kin);
                    }
                    return eff;
                };

                // Tightest passed WP index (0 = tightest); == thresholds.size()
                // means the jet fails even the loosest WP.
                std::size_t passed = thresholds.size();
                for (std::size_t w = 0; w < thresholds.size(); ++w) {
                    if (score >= thresholds.at(w)) {
                        passed = w;
                        break;
                    }
                }

                double num = 0.0;
                double denom = 0.0;
                if (passed == 0) {
                    // Passes the tightest WP: jet_w = SF(tightest). The
                    // efficiency cancels but is validated so a broken payload
                    // is still caught.
                    const std::string &wp = kWorkingPointsTightToLoose.at(0);
                    const double eff = eval_eff(wp);
                    const double sf = eval_sf(wp);
                    num = sf * eff;
                    denom = eff;
                } else if (passed < thresholds.size()) {
                    // Passes `low` but not the next tighter WP `high`.
                    const std::string &low =
                        kWorkingPointsTightToLoose.at(passed);
                    const std::string &high =
                        kWorkingPointsTightToLoose.at(passed - 1);
                    const double eff_low = eval_eff(low);
                    const double eff_high = eval_eff(high);
                    denom = eff_low - eff_high;
                    if (denom <= 0.0) {
                        throw std::runtime_error(
                            logger_name +
                            ": non-monotonic b-tag efficiencies eff(" + low +
                            ")=" + std::to_string(eff_low) +
                            " must exceed eff(" + high +
                            ")=" + std::to_string(eff_high) + " for " + kin);
                    }
                    const double sf_low = eval_sf(low);
                    const double sf_high = eval_sf(high);
                    num = sf_low * eff_low - sf_high * eff_high;
                } else {
                    // Fails even the loosest WP.
                    const std::string &loosest =
                        kWorkingPointsTightToLoose.back();
                    const double eff = eval_eff(loosest);
                    denom = 1.0 - eff;
                    if (denom <= 0.0) {
                        throw std::runtime_error(
                            logger_name +
                            ": degenerate untagged probability 1 - eff(" +
                            loosest + ")=" + std::to_string(denom) +
                            " must be positive for " + kin);
                    }
                    const double sf = eval_sf(loosest);
                    num = 1.0 - sf * eff;
                }

                const double jet_w = num / denom;
                if (!std::isfinite(jet_w) || jet_w <= 0.0) {
                    throw std::runtime_error(
                        logger_name +
                        ": non-positive/non-finite jet contribution " +
                        std::to_string(jet_w) + " for " + kin);
                }

                weight *= jet_w;
            }

            Logger::get(logger_name)->debug("event b-tag weight {}", weight);
            return weight;
        };

    return df1.Define(output, event_weight,
                      {jet_pt, jet_eta, flavor_column, jet_score, jet_mask});
}

ROOT::RDF::RNode pt_clamped_njets(ROOT::RDF::RNode df, const std::string &output,
                                  const std::string &jet_pt,
                                  const std::string &jet_mask,
                                  const float pt_clamp_threshold) {
    auto count = [pt_clamp_threshold](const ROOT::RVec<float> &pts,
                                      const ROOT::RVec<int> &mask) {
        unsigned int n = 0;
        for (std::size_t i = 0; i < pts.size(); ++i) {
            if (mask.at(i) && pts.at(i) > pt_clamp_threshold) {
                ++n;
            }
        }
        return n;
    };
    return df.Define(output, count, {jet_pt, jet_mask});
}

} // end namespace btagging_strict

} // end namespace scalefactor

} // end namespace xyh

#endif // end GUARDBTAGSFSTRICT_CXX
