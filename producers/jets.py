"""
Producers for AK4 jet energy scale and resolution corrections, object selections, overlap vetoes, and quantities to be stored.
"""

from ..quantities import output as q
from ..quantities import nanoAOD
from analysis_configurations.quantities import nanoAODv9_run2, nanoAODv12_run3
from code_generation.producer import Producer, ProducerGroup

from ._helpers import (
    type1_jet_collection_producer_factory,
    jerc_producer_factory,
    stepwise_jerc_producer_factory,
)
from ..helpers import era_producer_groups
from ..constants import GLOBAL_SCOPES, SCOPES, ERAS_RUN2


# Produce the jet ID column
# - For run 2, the jet ID can just be taken from the corresponding column in
#   nanoAOD.
# - For 2022 and 2023, the jet ID in nanoAOD v12 has a bug which must be
#   adressed.
# - For 2024, no jet ID column exists in nanoAOD v15 must be calculated using
#   a dedicated correction file.
JetID = {
    tuple(ERAS_RUN2): Producer(
        name="JetID",
        call="""
        event::quantity::Rename<ROOT::RVec<int>>(
            {df},
            {output},
            {input}
        )
        """,
        input=[nanoAODv9_run2.Jet_jetId],
        output=[q.Jet_ID],
        scopes=GLOBAL_SCOPES,
    ),
    ("2022preEE", "2022postEE", "2023preBPix", "2023postBPix"): Producer(
        name="JetID",
        call="""
        physicsobject::jet::quantities::CorrectJetIDRun3NanoV12(
            {df},
            {output},
            {input}
        )
        """,
        input=[
            nanoAOD.Jet_pt,
            nanoAOD.Jet_eta,
            nanoAODv12_run3.Jet_jetId,
            nanoAOD.Jet_neHEF,
            nanoAOD.Jet_neEmEF,
            nanoAOD.Jet_muEF,
            nanoAOD.Jet_chEmEF,
        ],
        output=[q.Jet_ID],
        scopes=GLOBAL_SCOPES,
    ),
    "2024": Producer(
        name="JetID",
        call="""
        physicsobject::jet::quantity::ID(
            {df},
            correctionManager,
            {output},
            {input},
            "{ak4jet_id_file}",
            "{ak4jet_id_name}"
        )
        """,
        input=[
            nanoAOD.Jet_eta,
            nanoAOD.Jet_chHEF,
            nanoAOD.Jet_neHEF,
            nanoAOD.Jet_chEmEF,
            nanoAOD.Jet_neEmEF,
            nanoAOD.Jet_muEF,
            nanoAOD.Jet_chMultiplicity,
            nanoAOD.Jet_neMultiplicity,
        ],
        output=[q.Jet_ID],
        scopes=GLOBAL_SCOPES,
    ),
}

# Seed for the random number generator for jet energy resolution smearing
JERSmearingSeed = Producer(
    name="JERSmearingSeed",
    call="""
    event::quantity::GenerateSeed(
        {df},
        {output},
        {input},
        {ak4jet_jer_master_seed}
    )
    """,
    input=[nanoAOD.luminosityBlock, nanoAOD.run, nanoAOD.event],
    output=[q.jet_seed],
    scopes=GLOBAL_SCOPES,
)


#
# JET ENERGY CALIBRATION
#

# Producer for raw jet pt before JES corrections
JetRawPt = Producer(
    name="JetRawPt",
    call="physicsobject::jet::jec::Raw({df}, {output}, {input})",
    input=[nanoAOD.Jet_pt, nanoAOD.Jet_rawFactor],
    output=[q.Jet_rawPt],
    scopes=GLOBAL_SCOPES,
)

# Producer for raw jet mass before JES corrections
JetRawMass = Producer(
    name="JetRawMass",
    call="physicsobject::jet::jec::Raw({df}, {output}, {input})",
    input=[nanoAOD.Jet_mass, nanoAOD.Jet_rawFactor],
    output=[q.Jet_rawMass],
    scopes=GLOBAL_SCOPES,
)

# Jet pt correction producers for AK4 jets on data and simulation
JetPtCorrectionData, JetPtCorrectionMC = stepwise_jerc_producer_factory(
    input={
        "jet_pt": nanoAOD.Jet_pt,
        "jet_eta": nanoAOD.Jet_eta,
        "jet_phi": nanoAOD.Jet_phi,
        "jet_mass": nanoAOD.Jet_mass,
        "jet_area": nanoAOD.Jet_area,
        "jet_raw_factor": nanoAOD.Jet_rawFactor,
        "jet_id": q.Jet_ID,
        "jet_seed": q.jet_seed,
        "genjet_pt": nanoAOD.GenJet_pt,
        "genjet_eta": nanoAOD.GenJet_eta,
        "genjet_phi": nanoAOD.GenJet_phi,
        "rho": nanoAOD.Rho_fixedGridRhoFastjetAll,
        "run": nanoAOD.run,
    },
    output={
        "jet_jec_result": q.Jet_jecResult,
        "jet_l1_pt": q.Jet_l1Pt,
        "jet_l2rel_pt": q.Jet_l2relPt,
        "jet_l2l3res_pt": q.Jet_l2l3resPt,
        "jet_corrected_pt": q.Jet_correctedPt,
    },
    scopes=GLOBAL_SCOPES,
    producer_prefix="Jet",
    config_parameter_prefix="ak4jet",
)

# Mass correction resulting from the JEC prodcedure
JetMassCorrection = Producer(
    name="JetMassCorrection",
    call="""
    physicsobject::jet::jec::MassCorrectionFromPt(
        {df},
        {output},
        {input}
    )
    """,
    input=[
        q.Jet_rawMass,
        q.Jet_rawPt,
        q.Jet_correctedPt,
    ],
    output=[q.Jet_correctedMass],
    scopes=GLOBAL_SCOPES,
)

# Producer group for jet energy calibration on data
JetEnergyCorrectionData = ProducerGroup(
    name="JECData",
    call=None,
    input=None,
    output=None,
    scopes=GLOBAL_SCOPES,
    subproducers=[
        JetRawPt,
        JetRawMass,
        JetPtCorrectionData,
        JetMassCorrection,
    ],
)

# Producer group for jet energy calibration on MC
JetEnergyCorrectionMC = ProducerGroup(
    name="JECSimulation",
    call=None,
    input=None,
    output=None,
    scopes=GLOBAL_SCOPES,
    subproducers=[
        JetRawPt,
        JetRawMass,
        JetPtCorrectionMC,
        JetMassCorrection,
    ],
)


#
# JETS AND JET ENERGY CALIBRATION FOR MET TYPE-I CORRECTIONS
#

# Dummy value or renaming of the EmEF column of CorrT1METJet collection
# - For 2022 and 2023, the EmEF column of the CorrT1METJet collection does not
#   exist. Dummy values of 0 are added, i.e., all CorrT1METJet objects are
#   passing the EmEF < 0.9 criterion.
# - For 2024, just rename the column.
CorrT1METJetEmEF = {
    tuple(ERAS_RUN2) + ("2022preEE", "2022postEE", "2023preBPix", "2023postBPix"): Producer(
        name="CorrT1METJetEmEFDummy",
        call="event::quantity::Define<float>({df}, {output}, {input}, 0.0)",
        input=[nanoAOD.nCorrT1METJet],
        output=[q.CorrT1METJet_EmEnergyFraction],
        scopes=GLOBAL_SCOPES,
    ),
    "2024": Producer(
        name="CorrT1METJetEmEFDummy",
        call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
        input=[nanoAOD.CorrT1METJet_EmEF],
        output=[q.CorrT1METJet_EmEnergyFraction],
        scopes=GLOBAL_SCOPES,
    ),
}

# Concatenate Jet and CorrT1METJet collections for MET type-I corrections
Type1JetCollection = type1_jet_collection_producer_factory(
    input={
        "jet_pt": nanoAOD.Jet_pt,
        "jet_eta": nanoAOD.Jet_eta,
        "jet_phi": nanoAOD.Jet_phi,
        "jet_id": q.Jet_ID,
        "jet_area": nanoAOD.Jet_area,
        "jet_raw_factor": nanoAOD.Jet_rawFactor,
        "jet_muon_subtr_factor": nanoAOD.Jet_muonSubtrFactor,
        "jet_ch_em_ef": nanoAOD.Jet_chEmEF,
        "jet_ne_em_ef": nanoAOD.Jet_neEmEF,
        "corrt1metjet_raw_pt": nanoAOD.CorrT1METJet_rawPt,
        "corrt1metjet_eta": nanoAOD.CorrT1METJet_eta,
        "corrt1metjet_phi": nanoAOD.CorrT1METJet_phi,
        "corrt1metjet_area": nanoAOD.CorrT1METJet_area,
        "corrt1metjet_muon_subtr_factor": nanoAOD.CorrT1METJet_muonSubtrFactor,
        "corrt1metjet_em_ef": q.CorrT1METJet_EmEnergyFraction,
        "n_corrt1metjet": nanoAOD.nCorrT1METJet,
    },
    output={
        "jet_raw_muon_subtr_pt": q.Jet_rawMuonSubtrPt,
        "jet_em_ef": q.Jet_EmEF,
        "corrt1metjet_raw_muon_subtr_pt": q.CorrT1METJet_rawMuonSubtrPt,
        "corrt1metjet_id": q.CorrT1METJet_ID,
        "t1jet_raw_muon_subtr_pt": q.Type1Jet_rawMuonSubtrPt,
        "t1jet_eta": q.Type1Jet_eta,
        "t1jet_phi": q.Type1Jet_phi,
        "t1jet_area": q.Type1Jet_area,
        "t1jet_id": q.Type1Jet_ID,
        "t1jet_em_ef": q.Type1Jet_EmEF,
    },
    scopes=GLOBAL_SCOPES,
    producer_prefix="Type1Jet",
)

# Jet pt correction producers for AK4 jets on data and simulation
Type1JetPtCorrectionData, Type1JetPtCorrectionMC = stepwise_jerc_producer_factory(
    input={
        "jet_pt": q.Type1Jet_rawMuonSubtrPt,
        "jet_eta": q.Type1Jet_eta,
        "jet_phi": q.Type1Jet_phi,
        "jet_area": q.Type1Jet_area,
        "jet_id": q.Type1Jet_ID,
        "genjet_pt": nanoAOD.GenJet_pt,
        "genjet_eta": nanoAOD.GenJet_eta,
        "genjet_phi": nanoAOD.GenJet_phi,
        "rho": nanoAOD.Rho_fixedGridRhoFastjetAll,
        "run": nanoAOD.run,
        "jet_seed": q.jet_seed,
    },
    output={
        "jet_jec_result": q.Type1Jet_jecResult,
        "jet_l1_pt": q.Type1Jet_l1Pt,
        "jet_l2rel_pt": q.Type1Jet_l2relPt,
        "jet_l2l3res_pt": q.Type1Jet_l2l3resPt,
        "jet_corrected_pt": q.Type1Jet_correctedPt,
    },
    scopes=GLOBAL_SCOPES,
    producer_prefix="Type1Jet",
    config_parameter_prefix="ak4jet",
)

# Producer group for type-I jet energy calibration on data
Type1JetEnergyCorrectionData = era_producer_groups( 
    "Type1JetEnergyCorrectionData",
    [
        CorrT1METJetEmEF,
        Type1JetCollection,
        Type1JetPtCorrectionData,
    ],
    GLOBAL_SCOPES,
)

# Producer group for type-I jet energy calibration on MC
Type1JetEnergyCorrectionMC = era_producer_groups( 
    "Type1JetEnergyCorrectionMC",
    [
        CorrT1METJetEmEF,
        Type1JetCollection,
        Type1JetPtCorrectionMC,
    ],
    GLOBAL_SCOPES,
)


#
# AK4 JET SELECTION
#

# Jet selection for run 2 (CHS jets)
GoodJetsWithPUID = Producer(
    name="GoodJetsWithPUID",
    call="xyh::object_selection::jet({df}, {output}, {input}, {ak4jet_min_pt}, {ak4jet_max_abs_eta}, {ak4jet_id_wp}, {ak4jet_apply_jet_horn_veto}, {ak4jet_puid_wp}, {ak4jet_puid_max_pt})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        q.Jet_ID,
        nanoAODv9_run2.Jet_puId,
    ],
    output=[q.good_jets_mask],
    scopes=GLOBAL_SCOPES,
)

# Jet selection for run 3 (PUPPI jets)
GoodJetsWithoutPUID = Producer(
    name="GoodJetsWithoutPUID",
    call="xyh::object_selection::jet({df}, {output}, {input}, {ak4jet_min_pt}, {ak4jet_max_abs_eta}, {ak4jet_id_wp}, {ak4jet_apply_jet_horn_veto})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        q.Jet_ID,
    ],
    output=[q.good_jets_mask],
    scopes=GLOBAL_SCOPES,
)

# Kinematic b jet selection for run 2 (CHS jets)
GoodBJetsBaseWithPUID = Producer(
    name="GoodBJetsBaseWithPUID",
    call="xyh::object_selection::jet({df}, {output}, {input}, {bjet_min_pt}, {bjet_max_abs_eta}, {ak4jet_id_wp}, {ak4jet_apply_jet_horn_veto}, {ak4jet_puid_wp}, {ak4jet_puid_max_pt})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        q.Jet_ID,
        nanoAODv9_run2.Jet_puId,
    ],
    output=[q.base_bjets_mask],
    scopes=GLOBAL_SCOPES,
)

# Kinematic b jet selection for run 3 (PUPPI jets)
GoodBJetsBaseWithoutPUID = Producer(
    name="GoodBJetsBaseWithoutPUID",
    call="xyh::object_selection::jet({df}, {output}, {input}, {bjet_min_pt}, {bjet_max_abs_eta}, {ak4jet_id_wp}, {ak4jet_apply_jet_horn_veto})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        q.Jet_ID,
    ],
    output=[q.base_bjets_mask],
    scopes=GLOBAL_SCOPES,
)

# Tag whether a jet is b-tagged.
# The NANOAOD column for the b tagging score is taken from the analysis
# configuration.
BTagCut = Producer(
    name="BTagCut",
    call="physicsobject::CutMin<float>({df}, {output}, \"{bjet_score_column}\", {bjet_min_score})",
    input=[],
    output=[q.Jet_is_btagged],
    scopes=GLOBAL_SCOPES,
)

# Full b jet selection for run 2, including the b tagging requirement (CHS jets)
GoodBJetsWithPUID = ProducerGroup(
    name="GoodBJetsWithPUID",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[],
    output=[q.good_bjets_mask],
    subproducers=[
        GoodBJetsBaseWithPUID,
        BTagCut,
    ],
    scopes=GLOBAL_SCOPES,
)

# Full b jet selection for run 3, including the b tagging requirement (PUPPI jets)
GoodBJetsWithoutPUID = ProducerGroup(
    name="GoodBJetsWithoutPUID",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[],
    output=[q.good_bjets_mask],
    subproducers=[
        GoodBJetsBaseWithoutPUID,
        BTagCut,
    ],
    scopes=GLOBAL_SCOPES,
)

# Producer group for jet and b jet selection in run 2 (CHS jets)
BaseJetSelectionWithPUID = ProducerGroup(
    name="GoodJetSelectionWithPUID",
    call=None,
    input=None,
    output=None,
    scopes=GLOBAL_SCOPES,
    subproducers=[
        GoodJetsWithPUID,
        GoodBJetsWithPUID,
    ],
)

# Producer group for jet and b jet selection in run 3 (PUPPI jets)
BaseJetSelectionWithoutPUID = ProducerGroup(
    name="GoodJetSelectionWithoutPUID",
    call=None,
    input=None,
    output=None,
    scopes=GLOBAL_SCOPES,
    subproducers=[
        GoodJetsWithoutPUID,
        GoodBJetsWithoutPUID,
    ],
)


#
# OVERLAP VETOES
#

# Check whether a jet is overlapping with the tight lepton candidates from resolved selection
VetoOverlappingJets = Producer(
    name="VetoOverlappingJets",
    call="physicsobject::jet::VetoOverlappingJets({df}, {output}, {input}, {ak4jet_veto_min_delta_r})",
    input=[
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.p4_1,
        q.p4_2,
    ],
    output=[q.jet_overlap_veto_mask],
    scopes=SCOPES,
)

# Create a mask that includes selected jets that do not overlap with the lepton candidates from the resolved selection
GoodJetsWithVeto = Producer(
    name="GoodJetsWithVeto",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[q.good_jets_mask, q.jet_overlap_veto_mask],
    output=[q.good_jets_with_veto_mask],
    scopes=SCOPES,
)

# Create a mask that includes selected b jets that do not overlap with the lepton candidates from the resolved selection
GoodBJetsWithVeto = Producer(
    name="GoodBJetsWithVeto",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[q.good_bjets_mask, q.jet_overlap_veto_mask],
    output=[q.good_bjets_with_veto_mask],
    scopes=SCOPES,
)

# Create a mask that merged the masks for the selected jets and b jets after overlap cleaning
GoodJetsOrBJetsWithVeto = Producer(
    name="GoodJetsOrBJetsWithVeto",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "any_of")',
    input=[q.good_jets_with_veto_mask, q.good_bjets_with_veto_mask],
    output=[],
    scopes=SCOPES,
)

# Final jet collection as list of indices of selected jets, ordered by pt for the resolved selection
JetCollection = ProducerGroup(
    name="JetCollection",
    call="physicsobject::OrderByPt({df}, {output}, {input})",
    input=[q.Jet_correctedPt],
    output=[q.good_jet_collection],
    scopes=SCOPES,
    subproducers=[GoodJetsOrBJetsWithVeto],
)

# Final b jet collection as list of indices of selected jets, ordered by pt for the resolved selection
BJetCollection = Producer(
    name="BJetCollection",
    call="physicsobject::OrderByPt({df}, {output}, {input})",
    input=[q.Jet_correctedPt, q.good_bjets_with_veto_mask],
    output=[q.good_bjet_collection],
    scopes=SCOPES,
)

# Producer group for the jet selection in the scopes after cleaning against leptons
JetSelection = ProducerGroup(
    name="JetSelection",
    call=None,
    input=[],
    output=[],
    scopes=SCOPES,
    subproducers=[
        VetoOverlappingJets,
        GoodJetsWithVeto,
        GoodBJetsWithVeto,
        JetCollection,
        BJetCollection,
    ],
)


#
# Number of jets (depending on the b jet tagger)
#

NumberOfJets = Producer(
    name="NumberOfJets",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_jet_collection],
    output=[q.n_jets],
    scopes=SCOPES,
)


#
# Quantities for the two leading jets
#

LVJet1 = Producer(
    name="LVJet1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_jet_collection,
    ],
    output=[q.jet_p4_1],
    scopes=SCOPES,
)

LVJet2 = Producer(
    name="LVJet2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_jet_collection,
    ],
    output=[q.jet_p4_2],
    scopes=SCOPES,
)

NumberOfJets = Producer(
    name="NumberOfJets",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_jet_collection],
    output=[q.n_jets],
    scopes=SCOPES,
)

NumberOfJets_boosted = Producer(
    name="NumberOfJets_boosted",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_jet_collection_boosted],
    output=[q.n_jets_boosted],
    scopes=SCOPES,
)

jpt_1 = Producer(
    name="jpt_1",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.jet_p4_1],
    output=[q.jpt_1],
    scopes=SCOPES,
)
jpt_2 = Producer(
    name="jpt_2",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.jet_p4_2],
    output=[q.jpt_2],
    scopes=SCOPES,
)
jeta_1 = Producer(
    name="jeta_1",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.jet_p4_1],
    output=[q.jeta_1],
    scopes=SCOPES,
)
jeta_2 = Producer(
    name="jeta_2",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.jet_p4_2],
    output=[q.jeta_2],
    scopes=SCOPES,
)
jphi_1 = Producer(
    name="jphi_1",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.jet_p4_1],
    output=[q.jphi_1],
    scopes=SCOPES,
)
jphi_2 = Producer(
    name="jphi_2",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.jet_p4_2],
    output=[q.jphi_2],
    scopes=SCOPES,
)
jtag_value_1 = Producer(
    name="jtag_value_1",
    call="event::quantity::Get<float>({df}, {output}, \"{bjet_score_column}\", {input}, 0)",
    input=[q.good_jet_collection],
    output=[q.jtag_value_1],
    scopes=SCOPES,
)
jtag_value_2 = Producer(
    name="jtag_value_2",
    call="event::quantity::Get<float>({df}, {output}, \"{bjet_score_column}\", {input}, 1)",
    input=[q.good_jet_collection],
    output=[q.jtag_value_2],
    scopes=SCOPES,
)
mjj = Producer(
    name="m_jj",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.jet_p4_1, q.jet_p4_2],
    output=[q.mjj],
    scopes=SCOPES,
)
BasicJetQuantities = ProducerGroup(
    name="BasicJetQuantities",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        LVJet1,
        LVJet2,
        NumberOfJets,
        jpt_1,
        jeta_1,
        jphi_1,
        jtag_value_1,
        jpt_2,
        jeta_2,
        jphi_2,
        jtag_value_2,
        mjj,
    ],
)

##########################
# Basic b-Jet Quantities
# nbtag, pt, eta, phi, b-tag value
##########################

LVBJet1 = Producer(
    name="LVBJet1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_bjet_collection,
    ],
    output=[q.bjet_p4_1],
    scopes=SCOPES,
)
LVBJet2 = Producer(
    name="LVBJet2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_bjet_collection,
    ],
    output=[q.bjet_p4_2],
    scopes=SCOPES,
)

NumberOfBJets = Producer(
    name="NumberOfBJets",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_bjet_collection],
    output=[q.n_bjets],
    scopes=SCOPES,
)

NumberOfBJets_boosted = Producer(
    name="NumberOfBJets_boosted",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_bjet_collection_boosted],
    output=[q.n_bjets_boosted],
    scopes=SCOPES,
)

# bpt_1 = Producer(
#     name="bpt_1",
#     call="lorentzvector::GetPt({df}, {output}, {input})",
#     input=[q.bjet_p4_1],
#     output=[q.bpt_1],
#     scopes=SCOPES,
# )
# bpt_2 = Producer(
#     name="bpt_2",
#     call="lorentzvector::GetPt({df}, {output}, {input})",
#     input=[q.bjet_p4_2],
#     output=[q.bpt_2],
#     scopes=SCOPES,
# )
# beta_1 = Producer(
#     name="beta_1",
#     call="lorentzvector::GetEta({df}, {output}, {input})",
#     input=[q.bjet_p4_1],
#     output=[q.beta_1],
#     scopes=SCOPES,
# )
# beta_2 = Producer(
#     name="beta_2",
#     call="lorentzvector::GetEta({df}, {output}, {input})",
#     input=[q.bjet_p4_2],
#     output=[q.beta_2],
#     scopes=SCOPES,
# )
# bphi_1 = Producer(
#     name="bphi_1",
#     call="lorentzvector::GetPhi({df}, {output}, {input})",
#     input=[q.bjet_p4_1],
#     output=[q.bphi_1],
#     scopes=SCOPES,
# )
# bphi_2 = Producer(
#     name="bphi_2",
#     call="lorentzvector::GetPhi({df}, {output}, {input})",
#     input=[q.bjet_p4_2],
#     output=[q.bphi_2],
#     scopes=SCOPES,
# )
# btag_value_deepjet_1 = Producer(
#     name="btag_value_deepjet_1",
#     call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
#     input=[nanoAOD.Jet_btagDeepFlavB, q.good_bjet_collection],
#     output=[q.btag_value_1],
#     scopes=SCOPES,
# )
# btag_value_deepjet_2 = Producer(
#     name="btag_value_deepjet_1",
#     call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
#     input=[nanoAOD.Jet_btagDeepFlavB, q.good_bjet_collection],
#     output=[q.btag_value_2],
#     scopes=SCOPES,
# )
# btag_value_pnet_1 = Producer(
#     name="btag_value_pnet_1",
#     call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
#     input=[nanoAOD.Jet_btagPNetB, q.good_bjet_collection],
#     output=[q.btag_value_1],
#     scopes=SCOPES,
# )
# btag_value_pnet_2 = Producer(
#     name="btag_value_pnet_2",
#     call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
#     input=[nanoAOD.Jet_btagPNetB, q.good_bjet_collection],
#     output=[q.btag_value_2],
#     scopes=SCOPES,
# )
# btag_value_upart_1 = Producer(
#     name="btag_value_upart_1",
#     call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
#     input=[nanoAOD.Jet_btagUParTAK4B, q.good_bjet_collection],
#     output=[q.btag_value_1],
#     scopes=SCOPES,
# )
# btag_value_pnet_2 = Producer(
#     name="btag_value_upart_2",
#     call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
#     input=[nanoAOD.Jet_btagUParTAK4B, q.good_bjet_collection],
#     output=[q.btag_value_2],
#     scopes=SCOPES,
# )
BasicBJetQuantities = ProducerGroup(
    name="BasicBJetQuantities",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        NumberOfBJets,
    ],
)
