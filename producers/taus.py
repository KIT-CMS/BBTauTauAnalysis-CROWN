"""
Producers for hadronic tau energy scale corrections and object selections.
"""

from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from code_generation.producer import Producer, ProducerGroup
from ..constants import HAD_TAU_SCOPES


#
# ENERGY SCALE CORRECTIONS
#

# Hadronic tau pt correction for DeepTau v2.5
TauPtCorrectionMC = Producer(
    name="TauPtCorrectionMC",
    call="""
        physicsobject::tau::experimental::PtCorrectionMC(
            {df},
            correctionManager,
            {output},
            {input},
            "{tau_ides_sf_file}",
            "{tau_ES_json_name}",
            "{tau_id_algorithm}",
            "{tau_ides_sf_vsjet_wp}",
            "{tau_ides_sf_vsele_wp}",
            "{tau_es_variation}"
        )
    """,
    input=[
        nanoAOD.Tau_pt,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_decayMode,
        nanoAOD.Tau_genPartFlav,
    ],
    output=[q.Tau_pt_corrected],
    scopes=HAD_TAU_SCOPES,
)

# Tau mass correction, derived from the change of the tau pt due to the 
# correction
TauMassCorrection = Producer(
    name="TauMassCorrection",
    call="physicsobject::MassCorrectionWithPt({df}, {output}, {input})",
    input=[
        nanoAOD.Tau_mass,
        nanoAOD.Tau_pt,
        q.Tau_pt_corrected,
    ],
    output=[q.Tau_mass_corrected],
    scopes=HAD_TAU_SCOPES,
)

# Rename the hadronic tau pt in data (no correction applied)
RenameTauPt = Producer(
    name="RenameTauPt",
    call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
    input=[nanoAOD.Tau_pt],
    output=[q.Tau_pt_corrected],
    scopes=HAD_TAU_SCOPES,
)

# Rename the hadronic tau mass in data (no correction applied)
RenameTauMass = Producer(
    name="RenameTauMass",
    call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
    input=[nanoAOD.Tau_mass],
    output=[q.Tau_mass_corrected],
    scopes=HAD_TAU_SCOPES,
)

# Producer group encapsulating all tau energy scale corrections in MC samples
TauEnergyCorrectionMC = ProducerGroup(
    name="TauEnergyCorrectionMC",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers=[
        TauPtCorrectionMC,
        TauMassCorrection,
    ],
)

# producer group encapsulating dummy tau energy scale corrections in data
TauEnergyCorrectionData = ProducerGroup(
    name="TauEnergyCorrectionData",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers=[
        RenameTauPt,
        RenameTauMass,
    ],
)


#
# RUN 2 TAU ENERGY CORRECTION PRODUCERS (DEPRECATED)
#

# Hadronic tau pt correction for DeepTau v2.1 (deprectated)
TauPtCorrectionMCDeepTau2p1 = Producer(
    name="TauPtCorrectionMCDeepTau2p1",
    call="""
        physicsobject::tau::PtCorrectionMC(
            {df},
            correctionManager,
            {output},
            {input},
            "{tau_ides_sf_file}",
            "{tau_ES_json_name}",
            "{tau_id_algorithm}",
            "{tau_elefake_es_DM0_barrel}",
            "{tau_elefake_es_DM1_barrel}",
            "{tau_elefake_es_DM0_endcap}",
            "{tau_elefake_es_DM1_endcap}",
            "{tau_mufake_es}",
            "{tau_ES_shift_DM0}",
            "{tau_ES_shift_DM1}",
            "{tau_ES_shift_DM10}",
            "{tau_ES_shift_DM11}"
        )
    """,
    input=[
        nanoAOD.Tau_pt,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_decayMode,
        nanoAOD.Tau_genPartFlav,
    ],
    output=[q.Tau_pt_corrected],
    scopes=HAD_TAU_SCOPES,
)

# pt correction for hadronic taus in embedding samples (deprecated)
TauPtCorrection_byValue = Producer(
    name="TauPtCorrection",
    call="embedding::tau::PtCorrection_byValue({df}, {output}, {input}, {tau_ES_shift_DM0}, {tau_ES_shift_DM1}, {tau_ES_shift_DM10}, {tau_ES_shift_DM11})",
    input=[
        nanoAOD.Tau_pt,
        nanoAOD.Tau_decayMode,
    ],
    output=[q.Tau_pt_corrected],
    scopes=HAD_TAU_SCOPES,
)

# pt correction for electrons that fake hadronic taus (deprecated)
TauPtCorrection_eleFake = Producer(
    name="TauPtCorrection_eleFake",
    call='physicsobject::tau::PtCorrectionMC_eleFake({df}, correctionManager, {output}, {input}, "{tau_ides_sf_file}", "{tau_ES_json_name}", "{tau_id_algorithm}", "{tau_elefake_es_DM0_barrel}", "{tau_elefake_es_DM1_barrel}", "{tau_elefake_es_DM0_endcap}", "{tau_elefake_es_DM1_endcap}")',
    input=[
        nanoAOD.Tau_pt,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_decayMode,
        nanoAOD.Tau_genPartFlav,
    ],
    output=[q.Tau_pt_ele_corrected],
    scopes=HAD_TAU_SCOPES,
)

# pt correction for muons that fake hadronic taus  (deprecated)
TauPtCorrection_muFake = Producer(
    name="TauPtCorrection_muFake",
    call='physicsobject::tau::PtCorrectionMC_muFake({df}, correctionManager, {output}, {input}, "{tau_ides_sf_file}", "{tau_ES_json_name}", "{tau_id_algorithm}", "{tau_mufake_es}")',
    input=[
        q.Tau_pt_ele_corrected,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_decayMode,
        nanoAOD.Tau_genPartFlav,
    ],
    output=[q.Tau_pt_ele_mu_corrected],
    scopes=HAD_TAU_SCOPES,
)

# pt correction for genuine hadronic taus  (deprecated)
TauPtCorrection_genTau = Producer(
    name="TauPtCorrection_genTau",
    call='physicsobject::tau::PtCorrectionMC_genuineTau({df}, correctionManager, {output}, {input}, "{tau_ides_sf_file}", "{tau_ES_json_name}", "{tau_id_algorithm}", "{tau_ES_shift_DM0}", "{tau_ES_shift_DM1}", "{tau_ES_shift_DM10}", "{tau_ES_shift_DM11}")',
    input=[
        q.Tau_pt_ele_mu_corrected,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_decayMode,
        nanoAOD.Tau_genPartFlav,
    ],
    output=[q.Tau_pt_corrected],
    scopes=HAD_TAU_SCOPES,
)


# producer group encapsulating tau pt corrections in embedding samples
# (deprecated)
TauEnergyCorrection_byValue = ProducerGroup(
    name="TauEnergyCorrection",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers=[
        TauPtCorrection_eleFake,
        TauPtCorrection_byValue,
        TauMassCorrection,
    ],
)

# producer group encapsulating all tau energy scale corrections in MC samples
#  (deprecated)
TauEnergyCorrection_MC = ProducerGroup(
    name="TauEnergyCorrectionMCRun2",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers=[
        TauPtCorrection_eleFake,
        TauPtCorrection_muFake,
        TauPtCorrection_genTau,
        TauMassCorrection,
    ],
)

# producer group encapsulating all tau energy scale corrections in embedding 
# samples (deprecated)
TauEnergyCorrection_Embedding = ProducerGroup(
    name="TauEnergyCorrection_Embedding",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers=[
        TauPtCorrection_byValue,
        TauMassCorrection,
    ],
)


#
# OBJECT SELECTION
#

# selection masks for tight hadronic taus (final state tau candidates)
GoodTaus = Producer(
    name="GoodTaus",
    call="xyh::object_selection::tau({df}, {output}, {input}, {tight_tau_min_pt}, {tight_tau_max_abs_eta}, {tight_tau_max_abs_dz}, {{{tight_tau_decay_modes}}}, {tight_tau_id_vs_jet_wp}, {tight_tau_id_vs_electron_wp}, {tight_tau_id_vs_muon_wp})",
    input=[
        q.Tau_pt_corrected,
        nanoAOD.Tau_eta,
        nanoAOD.Tau_dz,
        nanoAOD.Tau_decayMode,
        nanoAOD.Tau_idDeepTau2018v2p5VSjet,
        nanoAOD.Tau_idDeepTau2018v2p5VSe,
        nanoAOD.Tau_idDeepTau2018v2p5VSmu,
    ],
    output=[q.good_taus_mask],
    scopes=HAD_TAU_SCOPES,
)

# count number of selected hadronic taus
NumberOfGoodTaus = Producer(
    name="NumberOfGoodTaus",
    call="physicsobject::Count({df}, {output}, {input})",
    input=[q.good_taus_mask],
    output=[q.ntaus],
    scopes=HAD_TAU_SCOPES,
)
