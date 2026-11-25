#ifndef BBTAUTAU_HBB_JETS_HXX
#define BBTAUTAU_HBB_JETS_HXX

#include "ROOT/RDataFrame.hxx"
#include <string>

namespace xyh::genmatching {
/**
 * @brief Flag the jets of a collection that stem from the decay of a boson to
 * a quark pair, H -> bb: the label of the auxiliary head of the NN stage B
 * (nn spec 5.11, v8 spec C25).
 *
 * The quarks are the generator particles with `|pdgId| == quark_pdgid` that
 * are the last copy of a particle of the hard process (status flags
 * `isLastCopy`, bit 13, and `fromHardProcess`, bit 8) and whose chain of
 * mothers with `|pdgId| == quark_pdgid` ends at a boson with
 * `|pdgId| == mother_pdgid`. NanoAOD keeps these last copies and links every
 * particle to its nearest stored ancestor, which makes the two conditions
 * necessary: a quark from gluon splitting in the shower of the decay is linked
 * to the quark that radiated the gluon (it is a last copy, but not from the
 * hard process), and a copy with two mothers (status 73) names the partner
 * quark of the decay as its mother, so that the chain passes through quarks
 * of both signs. A b quark of the hard process that does not stem from the
 * boson, such as a real emission, has no boson at the end of its chain. On
 * 20 000 events each of the 2018 powheg (kl = 1) and madgraph (node_SM) HH
 * samples, every event has exactly two such quarks.
 *
 * Every quark is matched to at most one jet, the nearest jet of the
 * collection within `Delta R < max_delta_r`; the matched jets get 1, every
 * other jet 0. Two quarks can share a jet. The output has one entry per jet
 * of the collection, in its order.
 *
 * The column types are those of NanoAOD v12 and later (`GenPart_statusFlags`
 * UShort_t, `GenPart_genPartIdxMother` Short_t).
 *
 * @param df input dataframe
 * @param outputname name of the output column, `ROOT::RVec<int>`
 * @param genpart_pdgid name of the column with the pdgId of the generator
 * particles
 * @param genpart_statusflags name of the column with their status flags
 * @param genpart_mother name of the column with the index of their mother
 * @param genpart_eta name of the column with their pseudorapidity
 * @param genpart_phi name of the column with their azimuthal angle
 * @param jet_eta name of the column with the pseudorapidity of the jets
 * @param jet_phi name of the column with the azimuthal angle of the jets
 * @param jet_collection name of the column with the indices of the jets of
 * the collection
 * @param mother_pdgid pdgId of the boson, e.g. 25
 * @param quark_pdgid pdgId of the quarks, e.g. 5
 * @param max_delta_r matching radius
 *
 * @return a new dataframe with the flag column
 *
 * @throws std::invalid_argument unless the pdgIds and the radius are positive
 */
ROOT::RDF::RNode JetsFromBosonDecay(
    ROOT::RDF::RNode df, const std::string &outputname,
    const std::string &genpart_pdgid, const std::string &genpart_statusflags,
    const std::string &genpart_mother, const std::string &genpart_eta,
    const std::string &genpart_phi, const std::string &jet_eta,
    const std::string &jet_phi, const std::string &jet_collection,
    const int mother_pdgid, const int quark_pdgid, const float max_delta_r);
} // namespace xyh::genmatching
#endif
