from code_generation.producer import Producer, ProducerGroup, ExtendedVectorProducer
from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD

"""
EmbeddingGenWeight = Producer(
    name="EmbeddingGenWeight",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD.genWeight],
    output=[q.emb_genweight],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)

TauEmbeddingInitialMETEt = Producer(
    name="TauEmbeddingInitialMETEt",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_initialMETEt],
    output=[q.emb_initialMETEt],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingInitialMETphi = Producer(
    name="TauEmbeddingInitialMETphi",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_initialMETphi],
    output=[q.emb_initialMETphi],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingInitialPuppiMETEt = Producer(
    name="TauEmbeddingInitialPuppiMETEt",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_initialPuppiMETEt],
    output=[q.emb_initialPuppiMETEt],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingInitialPuppiMETphi = Producer(
    name="TauEmbeddingInitialPuppiMETphi",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_initialPuppiMETphi],
    output=[q.emb_initialPuppiMETphi],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingIsMediumLeadingMuon = Producer(
    name="TauEmbeddingIsMediumLeadingMuon",
    call="event::quantity::Rename<Bool_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_isMediumLeadingMuon],
    output=[q.emb_isMediumLeadingMuon],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingIsMediumTrailingMuon = Producer(
    name="TauEmbeddingIsMediumTrailingMuon",
    call="event::quantity::Rename<Bool_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_isMediumTrailingMuon],
    output=[q.emb_isMediumTrailingMuon],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingIsTightLeadingMuon = Producer(
    name="TauEmbeddingIsTightLeadingMuon",
    call="event::quantity::Rename<Bool_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_isTightLeadingMuon],
    output=[q.emb_isTightLeadingMuon],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingIsTightTrailingMuon = Producer(
    name="TauEmbeddingIsTightTrailingMuon",
    call="event::quantity::Rename<Bool_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_isTightTrailingMuon],
    output=[q.emb_isTightTrailingMuon],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingnInitialPairCandidates = Producer(
    name="TauEmbeddingInitialPairCandidates",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_InitialPairCandidates],
    output=[q.emb_InitialPairCandidates],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingSelectionOldMass = Producer(
    name="TauEmbeddingSelectionOldMass",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_SelectionOldMass],
    output=[q.emb_SelectionOldMass],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingSelectionNewMass = Producer(
    name="TauEmbeddingSelectionNewMass",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD.TauEmbedding_SelectionNewMass],
    output=[q.emb_SelectionNewMass],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)

EmbeddingQuantities = ProducerGroup(
    name="EmbeddingQuantities",
    call=None,
    input=None,
    output=None,
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
    subproducers=[
        EmbeddingGenWeight,
        TauEmbeddingInitialMETEt,
        TauEmbeddingInitialMETphi,
        TauEmbeddingInitialPuppiMETEt,
        TauEmbeddingInitialPuppiMETphi,
        TauEmbeddingIsMediumLeadingMuon,
        TauEmbeddingIsMediumTrailingMuon,
        TauEmbeddingIsTightLeadingMuon,
        TauEmbeddingIsTightTrailingMuon,
        TauEmbeddingnInitialPairCandidates,
        TauEmbeddingSelectionOldMass,
        TauEmbeddingSelectionNewMass,
    ],
)
"""


# Selection scalefactor

TauEmbeddingTriggerSelectionSF = Producer(
    name="TauEmbeddingTriggerSelectionSF",
    call="""embedding::scalefactor::selectionTrigger(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_selection_sf_file}", 
        "{embedding_selection_trigger_sf}")
        """,
    input=[q.gen_pt_1, q.gen_eta_1, q.gen_pt_2, q.gen_eta_2],
    output=[q.emb_triggersel_wgt],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)
TauEmbeddingIDSelectionSF_1 = Producer(
    name="TauEmbeddingIDSelectionSF_1",
    call="""embedding::scalefactor::SelectionId(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_selection_sf_file}", 
        "{embedding_selection_id_sf}")
        """,
    input=[q.gen_pt_1, q.gen_eta_1],
    output=[q.emb_idsel_wgt_1],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)

TauEmbeddingIDSelectionSF_2 = Producer(
    name="TauEmbeddingIDSelectionSF_2",
    call="""embedding::scalefactor::SelectionId(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_selection_sf_file}", 
        "{embedding_selection_id_sf}")
        """,
    input=[q.gen_pt_2, q.gen_eta_2],
    output=[q.emb_idsel_wgt_2],
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
)

TauEmbeddingSelectionSF = ProducerGroup(
    name="TauEmbeddingSelectionSF",
    call=None,
    input=None,
    output=None,
    scopes=["et", "mt", "tt", "em", "mm", "ee"],
    subproducers=[
        TauEmbeddingTriggerSelectionSF,
        TauEmbeddingIDSelectionSF_1,
        TauEmbeddingIDSelectionSF_2,
    ],
)

# Muon ID/Iso/Trigger SFS

TauEmbeddingMuonIDSF_1 = Producer(
    name="TauEmbeddingMuonIDSF_1",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_muon_sf_file}", 
        "{embedding_muon_id_sf}", 
        "emb", 
        {embedding_muon_id_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.id_wgt_mu_1],
    scopes=["mt", "mm"],
)

TauEmbeddingMuonIDSF_2 = Producer(
    name="TauEmbeddingMuonIDSF_2",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_muon_sf_file}", 
        "{embedding_muon_id_sf}", 
        "emb", 
        {embedding_muon_id_extrapolation})
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.id_wgt_mu_2],
    scopes=["mm", "em"],
)

TauEmbeddingMuonIsoSF_1 = Producer(
    name="TauEmbeddingMuonIsoSF_1",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_muon_sf_file}", 
        "{embedding_muon_iso_sf}", 
        "emb", 
        {embedding_muon_iso_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.iso_wgt_mu_1],
    scopes=["mt", "mm"],
)

TauEmbeddingMuonIsoSF_2 = Producer(
    name="TauEmbeddingMuonIsoSF_2",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_muon_sf_file}", 
        "{embedding_muon_iso_sf}", 
        "emb", 
        {embedding_muon_iso_extrapolation})
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.iso_wgt_mu_2],
    scopes=["mm", "em"],
)

TauEmbeddingBoostedMuonIDSF_1 = Producer(
    name="TauEmbeddingBoostedMuonIDSF_1",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_muon_sf_file}", 
        "{embedding_muon_id_sf}", 
        "emb"
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.emb_id_wgt_mu_boosted_1],
    scopes=["mt", "mm"],
)
TauEmbeddingBoostedMuonIsoSF_1 = Producer(
    name="TauEmbeddingBoostedMuonIsoSF_1",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_muon_sf_file}", 
        "{embedding_muon_iso_sf}", 
        "emb"
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.emb_iso_wgt_mu_boosted_1],
    scopes=["mt", "mm"],
)

MTGenerateSingleMuonTriggerSF = ExtendedVectorProducer(
    name="MTGenerateSingleMuonTriggerSF",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_muon_sf_file}", 
        "{embedding_trigger_sf}", 
        "emb", 
        {muon_trg_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output="flagname",
    scopes=["mt", "mm"],
    vec_config="singlemuon_trigger_sf",
)

# Electron ID/Iso/Trigger SFS

TauEmbeddingElectronIDSF_1 = Producer(
    name="TauEmbeddingElectronIDSF_1",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_electron_sf_file}", 
        "{embedding_electron_id_sf}", 
        "emb", 
        {embedding_electron_id_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.id_wgt_ele_1],
    scopes=["et", "ee", "em"],
)

TauEmbeddingElectronIDSF_2 = Producer(
    name="TauEmbeddingElectronIDSF_2",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_electron_sf_file}", 
        "{embedding_electron_id_sf}", 
        "emb", 
        {embedding_electron_id_extrapolation})
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.id_wgt_ele_2],
    scopes=["ee"],
)

TauEmbeddingElectronIsoSF_1 = Producer(
    name="TauEmbeddingElectronIsoSF_1",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_electron_sf_file}", 
        "{embedding_electron_iso_sf}", 
        "emb", 
        {embedding_electron_iso_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.iso_wgt_ele_1],
    scopes=["et", "ee", "em"],
)

TauEmbeddingElectronIsoSF_2 = Producer(
    name="TauEmbeddingElectronIsoSF_2",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_electron_sf_file}", 
        "{embedding_electron_iso_sf}", 
        "emb", 
        {embedding_electron_iso_extrapolation})
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.iso_wgt_ele_2],
    scopes=["ee"],
)

TauEmbeddingBoostedElectronIDSF_1 = Producer(
    name="TauEmbeddingBoostedElectronIDSF_1",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_electron_sf_file}", 
        "{embedding_electron_id_sf}", 
        "emb")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.id_wgt_ele_boosted_1],
    scopes=["et", "ee", "em"],
)
TauEmbeddingBoostedElectronIsoSF_1 = Producer(
    name="TauEmbeddingBoostedElectronIsoSF_1",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_electron_sf_file}", 
        "{embedding_electron_iso_sf}", 
        "emb")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.iso_wgt_ele_boosted_1],
    scopes=["et", "ee", "em"],
)

ETGenerateSingleElectronTriggerSF = ExtendedVectorProducer(
    name="ETGenerateSingleElectronTriggerSF",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{embedding_electron_sf_file}", 
        "{embedding_trigger_sf}", 
        "emb", 
        {electron_trg_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output="flagname",
    scopes=["et", "ee"],
    vec_config="singlelectron_trigger_sf",
)

# Di-tau trigger SFs
TTGenerateDoubleTauTriggerSF_1 = Producer(
    name="TTGenerateDoubleTauTriggerSF_1",
    call="""physicsobject::tau::scalefactor::Trigger(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{emb_ditau_trigger_file}", 
        "tauTriggerSF", 
        "{ditau_trigger_type}", 
        "{ditau_trigger_wp}", 
        "{ditau_trigger_corrtype}", 
        "{ditau_trigger_syst}")
        """,
    input=[q.pt_1, q.tau_decaymode_1],
    output=[q.trg_wgt_double_tau_1],
    scopes=["tt"],
)
TTGenerateDoubleTauTriggerSF_2 = Producer(
    name="TTGenerateDoubleTauTriggerSF_2",
    call="""physicsobject::tau::scalefactor::Trigger(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{emb_ditau_trigger_file}", 
        "tauTriggerSF", 
        "{ditau_trigger_type}", 
        "{ditau_trigger_wp}", 
        "{ditau_trigger_corrtype}", 
        "{ditau_trigger_syst}")
        """,
    input=[q.pt_2, q.tau_decaymode_2],
    output=[q.trg_wgt_double_tau_2],
    scopes=["tt"],
)
TTGenerateDoubleTauTriggerSF = ProducerGroup(
    name="TTGenerateDoubleTauTriggerSF",
    call=None,
    input=None,
    output=None,
    scopes=["tt"],
    subproducers=[
        TTGenerateDoubleTauTriggerSF_1,
        TTGenerateDoubleTauTriggerSF_2,
    ],
)

###############################
# Tau ID/Iso/Trigger SFS
###############################

Tau_2_VsJetTauID_lt_SF = ExtendedVectorProducer(
    name="Tau_2_VsJetTauID_lt_SF",
    call="""embedding::tau::scalefactor::Id_vsJet(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{tau_emb_sf_file}", 
        "{tau_emb_id_sf_correctionset}", 
        {vec_open}{tight_tau_dms}{vec_close}, 
        "{vsjet_tau_id_WP}", 
        "{tau_emb_vsele_WP_for_vsjet_sf}", 
        "{tau_emb_vsjet_sf_dependence}", 
        "{tau_emb_sf_vsjet_tauDM0_pt20to40}",
        "{tau_emb_sf_vsjet_tauDM0_pt40toInf}",
        "{tau_emb_sf_vsjet_tauDM1_pt20to40}",
        "{tau_emb_sf_vsjet_tauDM1_pt40toInf}",
        "{tau_emb_sf_vsjet_tauDM10_pt20to40}",
        "{tau_emb_sf_vsjet_tauDM10_pt40toInf}",
        "{tau_emb_sf_vsjet_tauDM11_pt20to40}",
        "{tau_emb_sf_vsjet_tauDM11_pt40toInf}")
        """,
    input=[q.pt_2, q.tau_decaymode_2, q.gen_match_2],
    output="tau_2_vsjet_sf_outputname",
    scopes=["et", "mt"],
    vec_config="vsjet_tau_id_sf_embedding",
)

Tau_1_VsJetTauID_tt_SF = ExtendedVectorProducer(
    name="Tau_1_VsJetTauID_tt_SF",
    call="""physicsobject::tau::scalefactor::Id_vsJet(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{tau_emb_sf_file}", 
        "{tau_emb_id_sf_correctionset}", 
        "{vsjet_tau_id_WP}", 
        "{tau_emb_vsele_WP_for_vsjet_sf}", 
        "{tau_emb_vsjet_sf_dependence}", 
        "{tau_emb_sf_vsjet_tauDM0}", 
        "{tau_emb_sf_vsjet_tauDM1}", 
        "{tau_emb_sf_vsjet_tauDM10}", 
        "{tau_emb_sf_vsjet_tauDM11}")
        """,
    input=[q.pt_1, q.tau_decaymode_1, q.gen_match_1],
    output="tau_1_vsjet_sf_outputname",
    scopes=["tt"],
    vec_config="vsjet_tau_id_sf_embedding",
)

Tau_2_VsJetTauID_tt_SF = ExtendedVectorProducer(
    name="Tau_2_VsJetTauID_tt_SF",
    call="""physicsobject::tau::scalefactor::Id_vsJet(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{tau_emb_sf_file}", 
        "{tau_emb_id_sf_correctionset}", 
        "{vsjet_tau_id_WP}", 
        "{tau_emb_vsele_WP_for_vsjet_sf}", 
        "{tau_emb_vsjet_sf_dependence}", 
        "{tau_emb_sf_vsjet_tauDM0}", 
        "{tau_emb_sf_vsjet_tauDM1}", 
        "{tau_emb_sf_vsjet_tauDM10}", 
        "{tau_emb_sf_vsjet_tauDM11}")
        """,
    input=[q.pt_2, q.tau_decaymode_2, q.gen_match_2],
    output="tau_2_vsjet_sf_outputname",
    scopes=["tt"],
    vec_config="vsjet_tau_id_sf_embedding",
)