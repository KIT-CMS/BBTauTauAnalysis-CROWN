#ifndef GUARDHEMVETO_HXX
#define GUARDHEMVETO_HXX

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include <string>

// namespace xyh
namespace xyh {

// namespace vetoes
namespace vetoes {

// HEM 15/16 event veto of 2018 (JME recipe for UL, v7 spec E29): the pieces of
// xyh::vetoes::hem_veto, inline so that the C++ test can check them directly.
namespace hem {

/**
 * @brief Whether a jet is a loose jet in the HEM 15/16 region: pT above
 * `min_pt`, identification value at least `id_wp` (6: TightLeptonVeto), and
 * strictly inside `min_eta < eta < max_eta`, `min_phi < phi < max_phi`.
 */
inline bool jet_in_region(const float &pt, const float &eta, const float &phi,
                          const int &id, const float &min_pt, const int &id_wp,
                          const float &min_eta, const float &max_eta,
                          const float &min_phi, const float &max_phi) {
    return pt > min_pt && id >= id_wp && eta > min_eta && eta < max_eta &&
           phi > min_phi && phi < max_phi;
}

/**
 * @brief Deterministic number in [0, 1) of a simulated event, from its run,
 * luminosity block and event number (splitmix64), so that the same event
 * number in different generator jobs falls on independent numbers.
 */
inline double event_uniform(const unsigned int &run, const unsigned int &lumi,
                            const unsigned long long &event) {
    auto mix = [](unsigned long long x) {
        x += 0x9E3779B97F4A7C15ULL;
        x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
        x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
        return x ^ (x >> 31);
    };
    const unsigned long long hash =
        mix(event ^ mix((static_cast<unsigned long long>(run) << 32) ^ lumi));
    return static_cast<double>(hash >> 11) * 0x1.0p-53;
}

/**
 * @brief Whether an event belongs to the period with the HEM 15/16 failure:
 * data and embedding from run `first_run` on (`by_run`), simulation with the
 * probability `affected_fraction`, the luminosity fraction of that period.
 */
inline bool affected_period(const bool &by_run, const unsigned int &run,
                            const unsigned int &lumi,
                            const unsigned long long &event,
                            const unsigned int &first_run,
                            const double &affected_fraction) {
    if (by_run) {
        return run >= first_run;
    }
    return event_uniform(run, lumi, event) < affected_fraction;
}

} // end namespace hem

// function xyh::vetoes::hem_veto
ROOT::RDF::RNode
hem_veto(ROOT::RDF::RNode df, const std::string &output,
         const std::string &jet_pt, const std::string &jet_eta,
         const std::string &jet_phi, const std::string &jet_id,
         const std::string &run, const std::string &lumi,
         const std::string &event, const bool &by_run, const float &min_pt,
         const int &id_wp, const float &min_eta, const float &max_eta,
         const float &min_phi, const float &max_phi, const int &first_run,
         const double &affected_fraction);

} // end namespace vetoes

} // end namespace xyh

#endif // end GUARDHEMVETO_HXX
