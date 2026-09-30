from ..quantities import output as q
from ..quantities import nanoAOD, nanoAOD_run2
from code_generation.producer import (
    BaseFilter,
    Filter,
    Producer,
    ProducerGroup,
    VectorProducer,
)
from .electrons import DiElectronVeto
from .muons import DiMuonVeto

####################
# Set of general producers for event quantities
####################

RunLumiEventFilter = VectorProducer(
    name="RunLumiEventFilter",
    call='event::filter::Quantity<{RunLumiEventFilter_Quantity_Types}>({df}, "RunLumiEventFilter", "{RunLumiEventFilter_Quantities}", {vec_open}{RunLumiEventFilter_Selections}{vec_close})',
    input=[],
    output=None,
    scopes=["global"],
    vec_configs=[
        "RunLumiEventFilter_Quantities",
        "RunLumiEventFilter_Quantity_Types",
        "RunLumiEventFilter_Selections",
    ],
)

JSONFilter = BaseFilter(
    name="JSONFilter",
    call='event::filter::GoldenJSON({df}, correctionManager, "GoldenJSONFilter", {input}, "{golden_json_file}")',
    input=[nanoAOD.run, nanoAOD.luminosityBlock],
    scopes=["global"],
)

PrefireWeight = Producer(
    name="PrefireWeight",
    call="event::quantity::Rename<Float_t>({df}, {output}, {input})",
    input=[nanoAOD_run2.L1PreFiringWeight_Nom],
    output=[q.prefireweight],
    scopes=["global"],
)

is_data = Producer(
    name="isData",
    input=[],
    call="event::quantity::Define({df}, {output}, {is_data})",
    output=[q.is_data],
    scopes=["global"],
)

is_embedding = Producer(
    name="is_embedding",
    call="event::quantity::Define({df}, {output}, {is_embedding})",
    input=[],
    output=[q.is_embedding],
    scopes=["global"],
)

is_mc = Producer(
    name="is_mc",
    call="event::quantity::Define({df}, {output}, {is_mc})",
    input=[],
    output=[q.is_mc],
    scopes=["global"],
)

SampleFlags = ProducerGroup(
    name="SampleFlags",
    call=None,
    input=None,
    output=None,
    scopes=["global"],
    subproducers=[
        is_data,
        is_embedding,
        is_mc,
    ],
)

MetFilter = VectorProducer(
    name="MetFilter",
    call='event::filter::Flag({df}, "{met_filters}", "{met_filters}")',
    input=[],
    output=None,
    scopes=["global"],
    vec_configs=["met_filters"],
)

Lumi = Producer(
    name="Lumi",
    call="event::quantity::Rename<UInt_t>({df}, {output}, {input})",
    input=[nanoAOD.luminosityBlock],
    output=[q.lumi],
    scopes=["global"],
)

npartons = Producer(
    name="npartons",
    call="event::quantity::Rename<UChar_t>({df}, {output}, {input})",
    input=[nanoAOD.LHE_Njets],
    output=[q.npartons],
    scopes=["global"],
)

PUweights = Producer(
    name="PUweights",
    call="""event::reweighting::Pileup(
        {df},
        correctionManager,
        {output},
        {input},
        "{PU_reweighting_file}",
        "{PU_reweighting_era}",
        "{PU_reweighting_variation}")
        """,
    input=[nanoAOD.Pileup_nTrueInt],
    output=[q.puweight],
    scopes=["global"],
)

ZPtMassReweighting = Producer(
    name="ZPtMassReweighting",
    call='event::reweighting::ZPtMass({df}, {output}, {input}, "{zptmass_file}", "{zptmass_functor}", "{zptmass_arguments}")',
    input=[
        q.recoil_genboson_p4,
    ],
    output=[q.ZPtMassReweightWeight],
    scopes=["global", "em", "et", "mt", "tt", "mm", "ee"],
)

TopPtReweighting = Producer(
    name="TopPtReweighting",
    call="event::reweighting::TopPt({df}, {output}, {input})",
    input=[
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_pt,
    ],
    output=[q.topPtReweightWeight],
    scopes=["global", "em", "et", "mt", "tt", "mm", "ee"],
)

DiLeptonVeto = ProducerGroup(
    name="DiLeptonVeto",
    call='event::CombineFlags({df}, {output}, {input}, "any_of")',
    input=[],
    output=[q.dilepton_veto],
    scopes=["global"],
    subproducers=[DiElectronVeto, DiMuonVeto],
)

JetVetoMapVeto = Producer(
    name="JetVetoMapVeto",
    call="""
    xyh::vetoes::jet_vetomap(
        {df},
        correctionManager,
        {output},
        {input},
        "{jet_veto_map_file}",
        "{jet_veto_map_name}",
        "{jet_veto_map_type}",
        {jet_veto_min_pt},
        {jet_veto_id_wp},
        {jet_veto_max_em_frac}
    )
    """,
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_ID,
        nanoAOD.Jet_chEmEF,
        nanoAOD.Jet_neEmEF,
    ],
    output=[q.jet_vetomap_veto],
    scopes=["global"],
)

GGH_NNLO_Reweighting = Producer(
    name="GGH_NNLO_Reweighting",
    call='htxs::ggHNNLOWeights({df}, {output}, "{ggHNNLOweightsRootfile}", "{ggH_generator}", {input})',
    input=[nanoAOD.HTXS_Higgs_pt, nanoAOD.HTXS_njets30],
    output=[q.ggh_NNLO_weight],
    scopes=["global", "em", "et", "mt", "tt", "mm", "ee"],
)

GGH_WG1_Uncertainties = Producer(
    name="GGH_WG1_Uncertainties",
    call="htxs::ggH_WG1_uncertainties({df}, {output_vec}, {input})",
    input=[
        nanoAOD.HTXS_stage_1_pTjet30,
        nanoAOD.HTXS_Higgs_pt,
        nanoAOD.HTXS_njets30,
    ],  # using non-updated stage1 flag required by the used macro
    output=[
        q.THU_ggH_Mu,
        q.THU_ggH_Res,
        q.THU_ggH_Mig01,
        q.THU_ggH_Mig12,
        q.THU_ggH_VBF2j,
        q.THU_ggH_VBF3j,
        q.THU_ggH_PT60,
        q.THU_ggH_PT120,
        q.THU_ggH_qmtop,
    ],
    scopes=["global", "em", "et", "mt", "tt", "mm", "ee"],
)

QQH_WG1_Uncertainties = Producer(
    name="QQH_WG1_Uncertainties",
    call="htxs::qqH_WG1_uncertainties({df}, {output_vec}, {input})",
    input=[
        nanoAOD.HTXS_stage1_1_fine_cat_pTjet30GeV
    ],  # using fine stage1.1 flag required by the used macro
    output=[
        q.THU_qqH_TOT,
        q.THU_qqH_PTH200,
        q.THU_qqH_Mjj60,
        q.THU_qqH_Mjj120,
        q.THU_qqH_Mjj350,
        q.THU_qqH_Mjj700,
        q.THU_qqH_Mjj1000,
        q.THU_qqH_Mjj1500,
        q.THU_qqH_25,
        q.THU_qqH_JET01,
    ],
    scopes=["global", "em", "et", "mt", "tt", "mm", "ee"],
)
LHE_Scale_weight = Producer(
    name="LHE_Scale_weight",
    call="event::reweighting::LHEscale({df}, {output}, {input}, {muR}, {muF})",
    input=[nanoAOD.LHEScaleWeight],
    output=[q.lhe_scale_weight],
    scopes=["global"],  #, "em", "et", "mt", "tt", "mm", "ee"],
)
LHEDrellYanDecayFlavor = Producer(
    name="LHEDrellYanDecayFlavor",
    call="genparticles::drell_yan::DecayFlavor({df}, {output}, {input})",
    input=[nanoAOD.LHEPart_pdgId, nanoAOD.LHEPart_status],
    output=[],
    scopes=["global"],
)

LHEDrellYanEMuFilter = Filter(
    name="LHEDrellYanEMuFilter",
    call="event::filter::Quantity<int>({df}, \"drell_yan_e_mu\", {input}, {vec_open}{dy_filter_flavors}{vec_close})",
    input=[],
    scopes=["global"],
    subproducers=[
        LHEDrellYanDecayFlavor,
    ]
)

NMSSM_LHE_Scale_weight = Producer(
    name="NMSSM_LHE_Scale_weight",
    call="event::reweighting::NMSSMLHEScaleWeights({df}, {output}, {input}, {muR}, {muF})",
    input=[nanoAOD.LHEScaleWeight],
    output=[q.lhe_scale_weight],
    scopes=["global", "em", "et", "mt", "tt", "mm", "ee"],
)
