#ifndef BBTAUTAU_ELECTRON_RECO_HXX
#define BBTAUTAU_ELECTRON_RECO_HXX

#include "ROOT/RDataFrame.hxx"
#include <string>

namespace correctionManager {
class CorrectionManager;
}

namespace xyh::scalefactor {
/**
 * @brief Electron reconstruction scale factor from the official EGM payload,
 * selecting the payload's pt category per electron.
 *
 * The EGM reconstruction efficiency is stored as separate "working points"
 * per pt range, each of which raises on a pt outside its range. Run 2 UL
 * payloads (2016preVFP to 2018) split at 20 GeV into `RecoBelow20` and
 * `RecoAbove20`; Run 3 payloads (2022 onwards) additionally split at 75 GeV
 * into `Reco20to75` and `RecoAbove75`. The 2023 payloads take phi as a
 * further input. The signature mirrors
 * `physicsobject::electron::scalefactor::Id` without the working-point
 * argument, so the call can move to a core function later.
 *
 * A pair rejected in a shifted column carries CROWN's default kinematics
 * (-10) and receives a weight of 1. Any other evaluation error stays visible.
 *
 * @param df input dataframe
 * @param manager correction manager that loads the scale factor file
 * @param output name of the output column with the reconstruction weight
 * @param pt name of the electron pt column
 * @param eta name of the electron eta column
 * @param phi name of the electron phi column (used for 2023 payloads only)
 * @param era era key of the payload, e.g. "2016preVFP" or "2022Re-recoBCD"
 * @param file path to the EGM electron correction file
 * @param correction correction set name, e.g. "UL-Electron-ID-SF"
 * @param variation "sf" for the nominal weight, "sfup"/"sfdown" for the
 * variations
 *
 * @return a new dataframe with the reconstruction weight column
 */
ROOT::RDF::RNode electron_reco(ROOT::RDF::RNode df,
                               correctionManager::CorrectionManager &manager,
                               const std::string &output,
                               const std::string &pt, const std::string &eta,
                               const std::string &phi, const std::string &era,
                               const std::string &file,
                               const std::string &correction,
                               const std::string &variation);
} // namespace xyh::scalefactor
#endif
