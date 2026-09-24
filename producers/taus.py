"""
Producers for hadronic tau energy scale corrections and object selections.
"""

from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from code_generation.producer import Producer, ProducerGroup
<<<<<<< Updated upstream
from ..constants import HAD_TAU_SCOPES, MT_SCOPES
from code_generation.helpers import defaults

=======
from ..constants import HAD_TAU_SCOPES
from code_generation.helpers import defaults
>>>>>>> Stashed changes

#
# ENERGY SCALE CORRECTIONS
#

# Hadronic tau pt correction for DeepTau v2.5
with defaults(output=[q.Tau_pt_corrected],
              scopes=HAD_TAU_SCOPES,
              input=[nanoAOD.Tau_pt, nanoAOD.Tau_eta, nanoAOD.Tau_decayMode, nanoAOD.Tau_genPartFlav]):
    TauPtCorrectionMC = Producer(
        name="TauPtCorrectionMC",
        call="""
            physicsobject::tau::PtCorrectionMC(
                {df},
                correctionManager,
                {output},
                {input},
                "{tau_ides_sf_file}",
                "{tau_ES_json_name}",
                "{tau_id_algorithm}",
                "{tau_ides_sf_vsjet_wp}",
                "{tau_ides_sf_vsele_wp}",
                {vec_open}{tight_tau_decay_modes}{vec_close},
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
<<<<<<< Updated upstream
        """
    )
=======
        """,
    )

>>>>>>> Stashed changes
    TauPtCorrection_emb_genTau_dm_binned = Producer(
        name="TauPtCorrection_emb_genTau_dm_binned",
        call='''physicsobject::tau::PtCorrectionMC_genuineTau_v15(
            {df},
            correctionManager,
            {output},
            {input},
            "{tau_emb_sf_file}",
            "{tau_emb_ES_json_name}",
            "{tau_id_algorithm}",
            "{tau_emb_ES_WP}",
            "{tau_ides_sf_vsele_wp}",
            "{tau_ES_shift_DM0}",
            "{tau_ES_shift_DM1}",
            "{tau_ES_shift_DM10}",
            "{tau_ES_shift_DM11}")''',
    )
    TauPtCorrection_emb_genTau_dm_pt_binned = Producer(
<<<<<<< Updated upstream
        name="TauPtCorrection_emb_genTau_dm_pt_binned",
        call='''physicsobject::tau::PtCorrectionMC_genuineTau_v15(
            {df},
            correctionManager,
            {output},
            {input},
            "{tau_emb_sf_file}",
            "{tau_emb_ES_json_name}",
            "{tau_id_algorithm}",
            "{tau_emb_ES_WP}",
            "{tau_ides_sf_vsele_wp}",
            "{tau_ES_shift_DM0_20to40}",
            "{tau_ES_shift_DM0_40toInf}",
            "{tau_ES_shift_DM1_20to40}",
            "{tau_ES_shift_DM1_40toInf}",
            "{tau_ES_shift_DM10_20to40}",
            "{tau_ES_shift_DM10_40toInf}",
            "{tau_ES_shift_DM11_20to40}",
            "{tau_ES_shift_DM11_40toInf}")''',
    )

=======
    name="TauPtCorrection_emb_genTau_dm_pt_binned",
    call='''physicsobject::tau::PtCorrectionMC_genuineTau_v15(
        {df},
        correctionManager,
        {output},
        {input},
        "{tau_emb_sf_file}",
        "{tau_emb_ES_json_name}",
        "{tau_id_algorithm}",
        "{tau_emb_ES_WP}",
        "{tau_ides_sf_vsele_wp}",
        "{tau_ES_shift_DM0_20to40}",
        "{tau_ES_shift_DM0_40toInf}",
        "{tau_ES_shift_DM1_20to40}",
        "{tau_ES_shift_DM1_40toInf}",
        "{tau_ES_shift_DM10_20to40}",
        "{tau_ES_shift_DM10_40toInf}",
        "{tau_ES_shift_DM11_20to40}",
        "{tau_ES_shift_DM11_40toInf}")''',
    )
>>>>>>> Stashed changes
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

# Producer to measure tau ES:
TauPtCorrection_byValue = Producer(
    name="TauPtCorrection_byValue",
    call='''embedding::tau::PtCorrection_byValue(
        {df},
        {output},
        {input},
        {shift_tau_ES_DM0_byValue},
        {shift_tau_ES_DM1_byValue},
        {shift_tau_ES_DM10_byValue},
        {shift_tau_ES_DM11_byValue})''',
        scopes=MT_SCOPES,
    input=[nanoAOD.Tau_pt, nanoAOD.Tau_decayMode],
    output=[q.Tau_pt_corrected],
)
with defaults(call=None, input=None, output=None, scopes=MT_SCOPES,):
    TauEnergyCorrection_Embedding_Measurement = ProducerGroup(
        subproducers=[
            TauPtCorrection_byValue,
            TauMassCorrection,
        ],
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
TauEnergyCorrection_Embedding_ES_dm_binned = ProducerGroup(
    name="TauEnergyCorrection_Embedding_ES_dm_binned",
        call=None,
        input=None,
        output=None,
        scopes=HAD_TAU_SCOPES,
    subproducers=[
        TauPtCorrection_emb_genTau_dm_binned,
        TauMassCorrection,
    ],
)
TauEnergyCorrection_Embedding_ES_dm_pt_binned = ProducerGroup(
    name="TauEnergyCorrection_Embedding_ES_dm_pt_binned",
            call=None,
            input=None,
            output=None,
            scopes=HAD_TAU_SCOPES,
    subproducers=[
        TauPtCorrection_emb_genTau_dm_pt_binned,
        TauMassCorrection,
    ],
)

TauEnergyCorrection_Embedding_ES_dm_binned = ProducerGroup(
    name="TauEnergyCorrection_Embedding_ES_dm_binned",
        call=None,
        input=None,
        output=None,
        scopes=HAD_TAU_SCOPES,
    subproducers=[
        TauPtCorrection_emb_genTau_dm_binned,
        TauMassCorrection,
    ],
)
TauEnergyCorrection_Embedding_ES_dm_pt_binned = ProducerGroup(
    name="TauEnergyCorrection_Embedding_ES_dm_pt_binned",
            call=None,
            input=None,
            output=None,
            scopes=HAD_TAU_SCOPES,
    subproducers=[
        TauPtCorrection_emb_genTau_dm_pt_binned,
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
MttCollApproximation = Producer(
    name="MttCollApproximation",
    call="quantities::CollinearApproxMtt({df}, {output}, {input})",
    input=[q.p4_1, q.p4_2, q.met_p4_recoilcorrected],
    output=[q.mtt_coll_approx],
    scopes=["et", "mt", "tt"],
)