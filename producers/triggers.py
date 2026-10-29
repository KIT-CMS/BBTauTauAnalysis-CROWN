from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from code_generation.producer import ExtendedVectorProducer

from ..constants import ET_SCOPES, MT_SCOPES, TT_SCOPES, EM_SCOPES, ELECTRON_SCOPES, MUON_SCOPES


# Common trigger-object inputs, needed by most of the trigger producers
_TRIGOBJ_INPUTS = [
    nanoAOD.TrigObj_pt,
    nanoAOD.TrigObj_eta,
    nanoAOD.TrigObj_phi,
    nanoAOD.TrigObj_id,
    nanoAOD.TrigObj_filterBits,
]


# -----------------------------------------------------------------------------
# Single-electron and electron-tau cross triggers
# -----------------------------------------------------------------------------

# Single-electron trigger flags, including trigger object matching
SingleEleTriggerFlags = ExtendedVectorProducer(
    name="SingleEleTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {min_pt}, {max_abs_eta}, {particle_id}, {vec_open}{filter_bit}{vec_close}, {match_max_delta_r})',
    input=[q.p4_1] + _TRIGOBJ_INPUTS,
    output="flagname",
    scopes=ELECTRON_SCOPES,
    vec_config="ele_trigger",
)

# Electron-tau cross trigger flags, including trigger object matching
EleTauTriggerFlags = ExtendedVectorProducer(
    name="EleTauTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_min_pt}, {p2_min_pt}, {p1_max_abs_eta}, {p2_max_abs_eta}, {p1_particle_id}, {p2_particle_id}, {vec_open}{p1_filter_bit}{vec_close}, {vec_open}{p2_filter_bit}{vec_close}, {match_max_delta_r})',
    input=[q.p4_1, q.p4_2] + _TRIGOBJ_INPUTS,
    output="flagname",
    scopes=ET_SCOPES,
    vec_config="eletau_trigger",
)


# -----------------------------------------------------------------------------
# Single-muon and muon-tau cross triggers
# -----------------------------------------------------------------------------

# Single-muon trigger flags, including trigger object matching
SingleMuTriggerFlags = ExtendedVectorProducer(
    name="SingleMuTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {min_pt}, {max_abs_eta}, {particle_id}, {vec_open}{filter_bit}{vec_close}, {match_max_delta_r})',
    input={
        "mt": [q.p4_1] + _TRIGOBJ_INPUTS,
        "mm": [q.p4_1] + _TRIGOBJ_INPUTS,
        "em": [q.p4_2] + _TRIGOBJ_INPUTS,
    },
    output="flagname",
    scopes=MUON_SCOPES,
    vec_config="mu_trigger",
)

# double muon-tau trigger flags, including trigger object matching
MuTauTriggerFlags = ExtendedVectorProducer(
    name="MuTauTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_min_pt}, {p2_min_pt}, {p1_max_abs_eta}, {p2_max_abs_eta}, {p1_particle_id}, {p2_particle_id}, {vec_open}{p1_filter_bit}{vec_close}, {vec_open}{p2_filter_bit}{vec_close}, {match_max_delta_r})',
    input=[q.p4_1, q.p4_2] + _TRIGOBJ_INPUTS,
    output="flagname",
    scopes=MT_SCOPES,
    vec_config="mutau_trigger",
)


# -----------------------------------------------------------------------------
# Tau-tau and tau-tau+jet triggers
# -----------------------------------------------------------------------------

# Double-tau trigger flags, including trigger object matching
TauTauTriggerFlags = ExtendedVectorProducer(
    name="TauTauTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_min_pt}, {p2_min_pt}, {p1_max_abs_eta}, {p2_max_abs_eta}, {p1_particle_id}, {p2_particle_id}, {vec_open}{p1_filter_bit}{vec_close}, {vec_open}{p2_filter_bit}{vec_close}, {match_max_delta_r})',
    input=[q.p4_1, q.p4_2] + _TRIGOBJ_INPUTS,
    output="flagname",
    scopes=TT_SCOPES,
    vec_config="tautau_trigger",
)

# double tau-tau + jet trigger flags, including trigger object matching
TauTauJetTriggerFlags = ExtendedVectorProducer(
    name="TauTauJetTriggerFlags",
    call='trigger::experimental::ObjectFlag({df}, {output}, {input_vec}, "{hlt_path}", {vec_open}{p1_min_pt}, {p2_min_pt}, {p3_min_pt}{vec_close}, {vec_open}{p1_max_abs_eta}, {p2_max_abs_eta}, {p3_max_abs_eta}{vec_close}, {vec_open}{p1_particle_id}, {p2_particle_id}, {p3_particle_id}{vec_close}, {vec_open}{vec_open}{p1_filter_bit}{vec_close}, {vec_open}{p2_filter_bit}{vec_close}, {vec_open}{p3_filter_bit}{vec_close}{vec_close}, {match_max_delta_r})',
    input=[q.p4_1, q.p4_2, q.jet_p4_1] + _TRIGOBJ_INPUTS,
    output="flagname",
    scopes=TT_SCOPES,
    vec_config="tautaujet_trigger",
)


####################
# Set of producers used for trigger flags, these are currently UNUSED
# TODO document and refactor this part
####################


MuMuGenerateSingleMuonTriggerFlags = ExtendedVectorProducer(
    name="MuMuGenerateSingleMuonTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.p4_1,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["mm"],
    vec_config="singlemuon_trigger",
)
ElElGenerateSingleElectronTriggerFlags = ExtendedVectorProducer(
    name="ElElGenerateSingleElectronTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.p4_1,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["ee"],
    vec_config="singleelectron_trigger",
)
ElElGenerateDoubleMuonTriggerFlags = ExtendedVectorProducer(
    name="ElElGenerateDoubleMuonTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_ptcut}, {p2_ptcut}, {p1_etacut}, {p2_etacut}, {p1_trigger_particle_id}, {p2_trigger_particle_id}, {p1_filterbit}, {p2_filterbit}, {max_deltaR_triggermatch})',
    input=[
        q.p4_1,
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["ee"],
    vec_config="doubleelectron_trigger",
)
MuMuGenerateDoubleMuonTriggerFlags = ExtendedVectorProducer(
    name="MuMuGenerateDoubleMuonTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_ptcut}, {p2_ptcut}, {p1_etacut}, {p2_etacut}, {p1_trigger_particle_id}, {p2_trigger_particle_id}, {p1_filterbit}, {p2_filterbit}, {max_deltaR_triggermatch})',
    input=[
        q.p4_1,
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["mm"],
    vec_config="doublemuon_trigger",
)

BoostedMTGenerateSingleMuonTriggerFlags = ExtendedVectorProducer(
    name="BoostedMTGenerateSingleMuonTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.boosted_p4_1,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["mt"],
    vec_config="boosted_singlemuon_trigger",
)
ETGenerateSingleElectronTriggerFlags = ExtendedVectorProducer(
    name="ETGenerateSingleElectronTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.p4_1,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["et"],
    vec_config="singleelectron_trigger",
)
BoostedETGenerateSingleElectronTriggerFlags = ExtendedVectorProducer(
    name="BoostedETGenerateSingleElectronTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.boosted_p4_1,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["et"],
    vec_config="boosted_singleelectron_trigger",
)
EMGenerateSingleElectronTriggerFlags = ExtendedVectorProducer(
    name="EMGenerateSingleElectronTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.p4_1,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["em"],
    vec_config="singleelectron_trigger",
)
GenerateSingleLeadingTauTriggerFlags = ExtendedVectorProducer(
    name="GenerateSingleLeadingTauTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.p4_1,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["tt"],
    vec_config="singletau_trigger_leading",
)
BoostedTTTriggerFlags = ExtendedVectorProducer(
    name="BoostedTTTriggerFlags",
    call='trigger::GenerateTriggerFlag({df}, {output}, "{hlt_path}")',
    input=[],
    output="flagname",
    scopes=["tt"],
    vec_config="boosted_ditau_trigger",
)
GenerateSingleTrailingTauTriggerFlags = ExtendedVectorProducer(
    name="GenerateSingleTrailingTauTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["et", "mt", "tt"],
    vec_config="singletau_trigger_trailing",
)
EMGenerateSingleMuonTriggerFlags = ExtendedVectorProducer(
    name="EMGenerateSingleMuonTriggerFlags",
    call='trigger::SingleObjectFlag({df}, {output}, {input}, "{hlt_path}", {ptcut}, {etacut}, {trigger_particle_id}, {filterbit}, {max_deltaR_triggermatch} )',
    input=[
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["em"],
    vec_config="singlemoun_trigger",
)
MTGenerateCrossTriggerFlags = ExtendedVectorProducer(
    name="GenerateCrossTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_ptcut}, {p2_ptcut}, {p1_etacut}, {p2_etacut}, {p1_trigger_particle_id}, {p2_trigger_particle_id}, {p1_filterbit}, {p2_filterbit}, {max_deltaR_triggermatch})',
    input=[
        q.p4_1,
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["mt"],
    vec_config="mutau_cross_trigger",
)
ETGenerateCrossTriggerFlags = ExtendedVectorProducer(
    name="GenerateCrossTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_ptcut}, {p2_ptcut}, {p1_etacut}, {p2_etacut}, {p1_trigger_particle_id}, {p2_trigger_particle_id}, {p1_filterbit}, {p2_filterbit}, {max_deltaR_triggermatch})',
    input=[
        q.p4_1,
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["et"],
    vec_config="eltau_cross_trigger",
)
TTGenerateDoubleTriggerFlags = ExtendedVectorProducer(
    name="TTGenerateDoubleTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_ptcut}, {p2_ptcut}, {p1_etacut}, {p2_etacut}, {p1_trigger_particle_id}, {p2_trigger_particle_id}, {p1_filterbit}, {p2_filterbit}, {max_deltaR_triggermatch})',
    input=[
        q.p4_1,
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["tt"],
    vec_config="doubletau_trigger",
)
EMGenerateCrossTriggerFlags = ExtendedVectorProducer(
    name="EMGenerateCrossTriggerFlags",
    call='trigger::DoubleObjectFlag({df}, {output}, {input}, "{hlt_path}", {p1_ptcut}, {p2_ptcut}, {p1_etacut}, {p2_etacut}, {p1_trigger_particle_id}, {p2_trigger_particle_id}, {p1_filterbit}, {p2_filterbit}, {max_deltaR_triggermatch})',
    input=[
        q.p4_1,
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["em"],
    vec_config="elmu_cross_trigger",
)


TTGenerateDoubleTriggerFlagsEmbedding = ExtendedVectorProducer(
    name="TTGenerateDoubleTriggerFlagsEmbedding",
    call="trigger::DoubleObjectFlag({df}, {output}, {input}, {p1_ptcut}, {p2_ptcut}, {p1_etacut}, {p2_etacut}, {p1_trigger_particle_id}, {p2_trigger_particle_id}, {p1_filterbit}, {p2_filterbit}, {max_deltaR_triggermatch})",
    input=[
        q.p4_1,
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["tt"],
    vec_config="doubletau_trigger_embedding",
)

MTGenerateCrossTriggerFlagsEmbedding = ExtendedVectorProducer(
    name="MTGenerateCrossTriggerFlagsEmbedding",
    call="trigger::DoubleObjectFlag({df}, {output}, {input}, {p1_ptcut}, {p2_ptcut}, {p1_etacut}, {p2_etacut}, {p1_trigger_particle_id}, {p2_trigger_particle_id}, {p1_filterbit}, {p2_filterbit}, {max_deltaR_triggermatch})",
    input=[
        q.p4_1,
        q.p4_2,
        nanoAOD.TrigObj_pt,
        nanoAOD.TrigObj_eta,
        nanoAOD.TrigObj_phi,
        nanoAOD.TrigObj_id,
        nanoAOD.TrigObj_filterBits,
    ],
    output="flagname",
    scopes=["mt"],
    vec_config="mutau_cross_trigger_embedding",
)
