from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from code_generation.producer import Producer, Filter

from ..constants import (
    ET_SCOPES,
    MT_SCOPES,
    TT_SCOPES,
    EE_SCOPES,
    MM_SCOPES,
    EM_SCOPES,
    HAD_TAU_SCOPES,
    ELECTRON_SCOPES,
    SCOPES,
)
    


####################
# Set of producers used for contruction of MT good pairs and the coressponding lorentz vectors
####################

MTPairSelection = Producer(
    name="MTPairSelection",
    call="ditau_pairselection::mutau::PairSelection({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        q.Tau_pt_corrected,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_phi,
        q.Tau_mass_corrected,
        nanoAOD.Tau_rawDeepTau2018v2p5VSjet,
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        nanoAOD.Muon_pfRelIso04_all,
        q.good_muons_mask,
        q.good_taus_mask,
    ],
    output=[q.dileptonpair],
    scopes=MT_SCOPES,
)
boostedMTPairSelection = Producer(
    name="boostedMTPairSelection",
    call="boosted_ditau_pairselection::mutau::PairSelection({df}, {input_vec}, {output}, {boosted_pairselection_min_dR}, {boosted_pairselection_max_dR})",
    input=[
        q.boostedTau_pt_corrected,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_phi,
        q.boostedTau_mass_corrected,
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.good_muons_mask,
        q.good_boostedtaus_mask,
    ],
    output=[q.boosteddileptonpair],
    scopes=MT_SCOPES,
)

GoodMTPairFlag = Producer(
    name="GoodMTPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.dileptonpair],
    output=[],
    scopes=MT_SCOPES,
)
GoodBoostedMTPairFlag = Producer(
    name="GoodboostedMTPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.boosteddileptonpair],
    output=[],
    scopes=MT_SCOPES,
)

GoodMTPairFilter = Filter(
    name="GoodMTPairFilter",
    call='event::filter::Flags({df}, "GoodMuTauPairs", {input}, "any_of")',
    input=[],
    scopes=MT_SCOPES,
    subproducers=[
        GoodMTPairFlag,
        # GoodBoostedMTPairFlag,
    ],
)

MuMuPairSelection = Producer(
    name="MuMuPairSelection",
    call="ditau_pairselection::mumu::PairSelection({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.good_muons_mask,
    ],
    output=[q.dileptonpair],
    scopes=MM_SCOPES,
)
MuMuPairSelectionOSPreferred = Producer(
    name="MuMuPairSelectionOSPreferred",
    call="ditau_pairselection::mumu::PairSelectionOSPreferred({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        nanoAOD.Muon_charge,
        q.good_muons_mask,
    ],
    output=[q.dileptonpair],
    scopes=MM_SCOPES,
)
ZMuMuPairSelection = Producer(
    name="ZMuMuPairSelection",
    call="ditau_pairselection::mumu::ZBosonPairSelection({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.good_muons_mask,
    ],
    output=[q.dileptonpair],
    scopes=MM_SCOPES,
)
ZMuMuPairSelectionOSPreferred = Producer(
    name="ZMuMuPairSelectionOSPrefered",
    call="ditau_pairselection::mumu::ZBosonPairSelectionOSPreferred({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        nanoAOD.Muon_charge,
        q.good_muons_mask,
    ],
    output=[q.dileptonpair],
    scopes=MM_SCOPES,
)
GoodMuMuPairFlag = Producer(
    name="GoodMuMuPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.dileptonpair],
    output=[],
    scopes=MM_SCOPES,
)

GoodMuMuPairFilter = Filter(
    name="GoodMuMuPairFilter",
    call='event::filter::Flags({df}, "GoodMuMuPairs", {input}, "any_of")',
    input=[],
    scopes=MM_SCOPES,
    subproducers=[GoodMuMuPairFlag],
)

ElElPairSelection = Producer(
    name="ElElPairSelection",
    call="pairselection::elel::PairSelection({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.good_electrons_mask,
    ],
    output=[q.dileptonpair],
    scopes=EE_SCOPES,
)
ZElElPairSelection = Producer(
    name="ZElElPairSelection",
    call="ditau_pairselection::elel::ZBosonPairSelection({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.good_electrons_mask,
    ],
    output=[q.dileptonpair],
    scopes=EE_SCOPES,
)

GoodElElPairFlag = Producer(
    name="GoodElElPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.dileptonpair],
    output=[],
    scopes=EE_SCOPES,
)

GoodElElPairFilter = Filter(
    name="GoodElElPairFilter",
    call='event::filter::Flags({df}, "GoodElElPairs", {input}, "any_of")',
    input=[],
    scopes=EE_SCOPES,
    subproducers=[GoodElElPairFlag],
)

ETPairSelection = Producer(
    name="ETPairSelection",
    call="ditau_pairselection::eltau::PairSelection({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        q.Tau_pt_corrected,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_phi,
        nanoAOD.Tau_mass,
        nanoAOD.Tau_rawDeepTau2018v2p5VSjet,
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        nanoAOD.Electron_pfRelIso03_all,
        q.good_electrons_mask,
        q.good_taus_mask,
    ],
    output=[q.dileptonpair],
    scopes=ET_SCOPES,
)
boostedETPairSelection = Producer(
    name="boostedETPairSelection",
    call="boosted_ditau_pairselection::eltau::PairSelection({df}, {input_vec}, {output}, {boosted_pairselection_min_dR}, {boosted_pairselection_max_dR})",
    input=[
        q.boostedTau_pt_corrected,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_phi,
        q.boostedTau_mass_corrected,
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.good_electrons_mask,
        q.good_boostedtaus_mask,
    ],
    output=[q.boosteddileptonpair],
    scopes=ET_SCOPES,
)

GoodETPairFlag = Producer(
    name="GoodETPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.dileptonpair],
    output=[],
    scopes=ET_SCOPES,
)
GoodBoostedETPairFlag = Producer(
    name="GoodboostedETPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.boosteddileptonpair],
    output=[],
    scopes=ET_SCOPES,
)

GoodETPairFilter = Filter(
    name="GoodETPairFilter",
    call='event::filter::Flags({df}, "GoodElTauPairs", {input}, "any_of")',
    input=[],
    scopes=ET_SCOPES,
    subproducers=[
        GoodETPairFlag,
        # GoodBoostedETPairFlag,
    ],
)

####################
## TauTau Pair Selection
####################
TTPairSelection = Producer(
    name="TTPairSelection",
    call="ditau_pairselection::tautau::PairSelection({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        q.Tau_pt_corrected,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_phi,
        q.Tau_mass_corrected,
        nanoAOD.Tau_rawDeepTau2018v2p5VSjet,
        q.good_taus_mask,
    ],
    output=[q.dileptonpair],
    scopes=TT_SCOPES,
)
boostedTTPairSelection = Producer(
    name="boostedTTPairSelection",
    call="boosted_ditau_pairselection::tautau::PairSelection({df}, {input_vec}, {output}, {boosted_pairselection_min_dR}, {boosted_pairselection_max_dR})",
    input=[
        q.boostedTau_pt_corrected,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_phi,
        q.boostedTau_mass_corrected,
        q.good_boostedtaus_mask,
    ],
    output=[q.boosteddileptonpair],
    scopes=TT_SCOPES,
)

GoodTTPairFlag = Producer(
    name="GoodTTPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.dileptonpair],
    output=[],
    scopes=TT_SCOPES,
)
GoodBoostedTTPairFlag = Producer(
    name="GoodTTPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.boosteddileptonpair],
    output=[],
    scopes=TT_SCOPES,
)

GoodTTPairFilter = Filter(
    name="GoodTTPairFilter",
    call='event::filter::Flags({df}, "GoodTauTauPairs", {input}, "any_of")',
    input=[],
    scopes=TT_SCOPES,
    subproducers=[
        GoodTTPairFlag,
        # GoodBoostedTTPairFlag,
    ],
)
####################
## ElMu Pair Selection
####################

EMPairSelection = Producer(
    name="EMPairSelection",
    call="ditau_pairselection::elmu::PairSelection({df}, {input_vec}, {output}, {pairselection_min_dR})",
    input=[
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        nanoAOD.Electron_pfRelIso03_all,
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        nanoAOD.Muon_pfRelIso04_all,
        q.good_electrons_mask,
        q.good_muons_mask,
    ],
    output=[q.dileptonpair],
    scopes=EM_SCOPES,
)

GoodEMPairFlag = Producer(
    name="GoodEMPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.dileptonpair],
    output=[],
    scopes=EM_SCOPES,
)

GoodEMPairFilter = Filter(
    name="GoodEMPairFilter",
    call='event::filter::Flags({df}, "GoodElMuPairs", {input}, "any_of")',
    input=[],
    scopes=EM_SCOPES,
    subproducers=[GoodEMPairFlag],
)

####################
## BB Pair Selection
####################

BBPairSelection = Producer(
    name="BBPairSelection",
    call="bb_pairselection::PairSelection({df}, {input_vec}, \"{bjet_score_column}\", {output}, {bb_pairselection_min_dR}, {bjet_min_score})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_bjet_collection,
        q.good_jet_collection,
    ],
    output=[q.dibjetpair],
    scopes=SCOPES,
)
BBPairSelection_boosted = Producer(
    name="BBPairSelection_boosted",
    call="bb_pairselection::PairSelection({df}, {input_vec}, \"{bjet_score_column}\", {output}, {bb_pairselection_min_dR}, {bjet_min_score})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_bjet_collection_boosted,
        q.good_jet_collection_boosted,
    ],
    output=[q.dibjetpair_boosted],
    scopes=SCOPES,
)
GoodBBPairFlag = Producer(
    name="GoodBBPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.dibjetpair],
    output=[],
    scopes=SCOPES,
)
GoodBBPairFlag_boosted = Producer(
    name="GoodBBPairFlag",
    call="ditau_pairselection::flagGoodPairs({df}, {output}, {input})",
    input=[q.dibjetpair_boosted],
    output=[],
    scopes=SCOPES,
)
GoodBBPairFilter = Filter(
    name="GoodBBPairFilter",
    call='event::filter::Flags({df}, "GoodBBPairs", {input}, "any_of")',
    input=[],
    scopes=SCOPES,
    subproducers=[GoodBBPairFlag, GoodBBPairFlag_boosted],
)

####################
## TauTau pair 4-vectors
####################

LVMu1 = Producer(
    name="LVMu1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.dileptonpair,
    ],
    output=[q.p4_1],
    scopes=MT_SCOPES + MM_SCOPES,
)
LVMu2 = Producer(
    name="LVMu2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.dileptonpair,
    ],
    output=[q.p4_2],
    scopes=MM_SCOPES + EM_SCOPES,
)
LVEl1 = Producer(
    name="LVEl1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.dileptonpair,
    ],
    output=[q.p4_1],
    scopes=ELECTRON_SCOPES,
)
LVEl2 = Producer(
    name="LVEl2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.dileptonpair,
    ],
    output=[q.p4_2],
    scopes=EE_SCOPES,
)
LVTau1 = Producer(
    name="LVTau1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Tau_pt_corrected,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_phi,
        q.Tau_mass_corrected,
        q.dileptonpair,
    ],
    output=[q.p4_1],
    scopes=TT_SCOPES,
)
LVTau2 = Producer(
    name="LVTau2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Tau_pt_corrected,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_phi,
        q.Tau_mass_corrected,
        q.dileptonpair,
    ],
    output=[q.p4_2],
    scopes=HAD_TAU_SCOPES,
)
## uncorrected versions of all particles, used for MET propagation
LVMu1Uncorrected = Producer(
    name="LVMu1Uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.dileptonpair,
    ],
    output=[q.p4_1_uncorrected],
    scopes=MT_SCOPES + MM_SCOPES,
)
LVMu2Uncorrected = Producer(
    name="LVMu2Uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.dileptonpair,
    ],
    output=[q.p4_2_uncorrected],
    scopes=MM_SCOPES + EM_SCOPES,
)
LVEl1Uncorrected = Producer(
    name="LVEl1Uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.dileptonpair,
    ],
    output=[q.p4_1_uncorrected],
    scopes=ELECTRON_SCOPES,
)
LVEl2Uncorrected = Producer(
    name="LVEl2Uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.dileptonpair,
    ],
    output=[q.p4_2_uncorrected],
    scopes=EE_SCOPES,
)
LVTau1Uncorrected = Producer(
    name="LVTau1Uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.Tau_pt,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_phi,
        nanoAOD.Tau_mass,
        q.dileptonpair,
    ],
    output=[q.p4_1_uncorrected],
    scopes=TT_SCOPES,
)
LVTau2Uncorrected = Producer(
    name="LVTau2Uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.Tau_pt,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_phi,
        nanoAOD.Tau_mass,
        q.dileptonpair,
    ],
    output=[q.p4_2_uncorrected],
    scopes=HAD_TAU_SCOPES,
)

####################
## Additional hadronic taus
####################

additionalBoostedTau = Producer(
    name="additionalBoostedTau",
    call="ditau_pairselection::findAdditionalTau({df}, {input}, {output})",
    input=[
        q.good_boostedtaus_mask,
        q.boosteddileptonpair,
    ],
    output=[q.additional_boostedtau],
    scopes=HAD_TAU_SCOPES,
)
LVaddBoostedTau = Producer(
    name="LVaddBoostedTau",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.boostedTau_pt_corrected,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_phi,
        q.boostedTau_mass_corrected,
        q.additional_boostedtau,
    ],
    output=[q.boosted_p4_add],
    scopes=HAD_TAU_SCOPES,
)

####################
## BB pair Lorentzvectors
####################

LVbjet1 = Producer(
    name="LVbjet1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.dibjetpair,
    ],
    output=[q.bpair_p4_1],
    scopes=SCOPES,
)
LVbjet2 = Producer(
    name="LVbjet2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.dibjetpair,
    ],
    output=[q.bpair_p4_2],
    scopes=SCOPES,
)
LVbjet1_boosted = Producer(
    name="LVbjet1_boosted",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.dibjetpair_boosted,
    ],
    output=[q.bpair_p4_1_boosted],
    scopes=SCOPES,
)
LVbjet2_boosted = Producer(
    name="LVbjet2_boosted",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.dibjetpair_boosted,
    ],
    output=[q.bpair_p4_2_boosted],
    scopes=SCOPES,
)
