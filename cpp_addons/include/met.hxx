#ifndef GUARDMETEXT_H
#define GUARDMETEXT_H

#include "ROOT/RDataFrame.hxx"

namespace met {

ROOT::RDF::RNode METType1Correction(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string raw_met, const std::string &t1jet_pt_l1corrected,
    const std::string &t1jet_pt_corrected, const std::string &t1jet_eta,
    const std::string &t1jet_phi, const std::string &t1jet_em_ef,
    const std::string &t1jet_muon_subtr_delta_phi,
    const float &t1jet_min_pt, const float &t1jet_max_abs_eta,
    const float &t1jet_max_em_ef);

}

#endif
