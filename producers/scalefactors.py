from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from code_generation.quantity import Quantity
from code_generation.producer import Producer, ProducerGroup
from code_generation.producer import ExtendedVectorProducer

from ..constants import ET_SCOPES, MT_SCOPES, TT_SCOPES, SL_SCOPES, ELECTRON_SCOPES, MUON_SCOPES, HAD_TAU_SCOPES, SCOPES


############################
# Muon ID, ISO SF
# The readout is done via correctionlib
############################

Muon_1_ID_SF = Producer(
    name="MuonID_SF",
    call="""physicsobject::muon::scalefactor::IsoAndID(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{muon_sf_file}", 
        "{muon_id_sf_name}", 
        "{muon_id_sf_variation}")
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.id_wgt_mu_1],
    scopes=["mt", "mm"],
)
Muon_1_Iso_SF = Producer(
    name="MuonIso_SF",
    call="""physicsobject::muon::scalefactor::IsoAndID(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{muon_sf_file}", 
        "{muon_iso_sf_name}", 
        "{muon_iso_sf_variation}")
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.iso_wgt_mu_1],
    scopes=["mt", "mm"],
)
Muon_2_ID_SF = Producer(
    name="MuonID_SF",
    call="""physicsobject::muon::scalefactor::IsoAndID(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{muon_sf_file}", 
        "{muon_id_sf_name}", 
        "{muon_id_sf_variation}")
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.id_wgt_mu_2],
    scopes=["em", "mm"],
)
Muon_2_Iso_SF = Producer(
    name="MuonIso_SF",
    call="""physicsobject::muon::scalefactor::IsoAndID(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{muon_sf_file}", 
        "{muon_iso_sf_name}", 
        "{muon_iso_sf_variation}")
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.iso_wgt_mu_2],
    scopes=["em", "mm"],
)
MuonIDIso_SF = ProducerGroup(
    name="MuonIDIso_SF",
    call=None,
    input=None,
    output=None,
    scopes=["mt", "em", "mm"],
    subproducers={
        "mt": [
            Muon_1_ID_SF,
            Muon_1_Iso_SF,
        ],
        "em": [
            Muon_2_ID_SF,
            Muon_2_Iso_SF,
        ],
        "mm": [
            Muon_1_ID_SF,
            Muon_1_Iso_SF,
            Muon_2_ID_SF,
            Muon_2_Iso_SF,
        ],
    },
)

Muon_1_Reco_SF_boosted = Producer(
    name="MuonReco_SF_boosted",
    call='scalefactor::muon::reco({df}, correctionManager, {input}, "{muon_reco_sf_variation}", {output}, "{muon_sf_file}", "{muon_reco_sf_name}")',
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.reco_wgt_mu_boosted_1],
    scopes=["mt"],
)
Muon_1_ID_SF_boosted = Producer(
    name="MuonID_SF_boosted",
    call="""physicsobject::muon::scalefactor::IsoAndID(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{muon_sf_file}", 
        "{muon_id_sf_name}", 
        "{muon_id_sf_variation}")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.id_wgt_mu_boosted_1],
    scopes=["mt"],
)
Muon_1_Iso_SF_boosted = Producer(
    name="MuonIso_SF_boosted",
    call="""physicsobject::muon::scalefactor::IsoAndID(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{muon_sf_file}", 
        "{muon_iso_sf_name}", 
        "{muon_iso_sf_variation}")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.iso_wgt_mu_boosted_1],
    scopes=["mt"],
)
Muon_SF_boosted = ProducerGroup(
    name="Muon_SF_boosted",
    call=None,
    input=None,
    output=None,
    scopes=["mt"],
    subproducers={
        "mt": [
            # Muon_1_Reco_SF_boosted,  does not exist in Run 3
            Muon_1_ID_SF_boosted,
            Muon_1_Iso_SF_boosted,
        ],
    },
)


#
# Tau ID scale factors
#

def _create_tau_id_vsjet_sf_producer(
    name: str,
    input: list[Quantity],
    output: str,
    scopes: list[str],
    vec_config: str,
):

    # define names of common parameters
    vsjet_wp = "vsjet_wp"
    tau_ides_sf_vsele_wp = "tau_ides_sf_vsele_wp"
    tau_id_sf_vsjet_sf_dependence = "tau_id_sf_vsjet_sf_dependence"

    call_fn = ""
    parameters = [
        "{df}", 
        "correctionManager",
        "{output}", 
        "{input}", 
        "\"{tau_ides_sf_file}\"",
        "\"{discriminator}\"", 
    ]
    call_fn = "physicsobject::tau::scalefactor::experimental::Id_vsJet"
    parameters.extend([
        f"\"{{{vsjet_wp}}}\"", 
        f"\"{{{tau_ides_sf_vsele_wp}}}\"", 
        f"\"{{{tau_id_sf_vsjet_sf_dependence}}}\"",
        "\"{tau_id_sf_vsjet_variation}\""
    ])

    return ExtendedVectorProducer(
        name=name,
        call=f"{call_fn}({', '.join(parameters)})",
        input=input,
        output=output,
        scopes=scopes,
        vec_config=vec_config,
    )


def _create_tau_id_vsele_sf_producer(
    name: str,
    input: list[Quantity],
    output: str,
    scopes: list[str],
    vec_config: str,
):
    return ExtendedVectorProducer(
        name=name,
        call="""
            physicsobject::tau::scalefactor::Id_vsEle(
                {df},
                correctionManager,
                {output},
                {input},
                "{tau_ides_sf_file}",
                "{discriminator}",
                "{vsele_wp}",
                "{era}",
                "{tau_id_sf_vsele_barrel_shift}",
                "{tau_id_sf_vsele_endcap_shift}"
            )
        """,
        input=input,
        output=output,
        scopes=scopes,
        vec_config=vec_config,
    )


def _create_tau_id_vsmu_sf_producer(
    name: str,
    input: list[Quantity],
    output: str,
    scopes: list[str],
    vec_config: str,
):
    return ExtendedVectorProducer(
        name=name,
        call="""physicsobject::tau::scalefactor::Id_vsMu(
            {df}, 
            correctionManager, 
            {output}, 
            {input}, 
            "{tau_ides_sf_file}", 
            "{discriminator}", 
            "{vsmu_wp}", 
            "{vsmu_vsele_wp}", 
            "{vsmu_vsjet_wp}", 
            "{era}", 
            "{tau_id_sf_vsmu_wheel1_shift}", 
            "{tau_id_sf_vsmu_wheel2_shift}", 
            "{tau_id_sf_vsmu_wheel3_shift}", 
            "{tau_id_sf_vsmu_wheel4_shift}", 
            "{tau_id_sf_vsmu_wheel5_shift}"
        )
        """,
        input=input,
        output=output,
        scopes=scopes,
        vec_config=vec_config,
    )

TauIDVsJetSF1 = _create_tau_id_vsjet_sf_producer(
    name="TauIDVsJetSF1",
    input=[q.pt_1, q.tau_decaymode_1, q.gen_match_1],
    output="tau1_output_name",
    scopes=TT_SCOPES,
    vec_config="vsjet_tau_id_sf",
)

TauIDVsJetSF2 = _create_tau_id_vsjet_sf_producer(
    name="TauIDVsJetSF2",
    input=[q.pt_2, q.tau_decaymode_2, q.gen_match_2],
    output="tau2_output_name",
    vec_config="vsjet_tau_id_sf",
    scopes=HAD_TAU_SCOPES,
)

# DeepTau ID vs. electrons scale factor for the first tau
TauIDVsEleSF1 = _create_tau_id_vsele_sf_producer(
    name="TauIDVsEleSF1",
    input=[q.eta_1, q.tau_decaymode_1, q.gen_match_1],
    output="tau1_output_name",
    scopes=TT_SCOPES,
    vec_config="vsele_tau_id_sf",
)

# DeepTau ID vs. electrons scale factor for the second tau
TauIDVsEleSF2 = _create_tau_id_vsele_sf_producer(
    name="TauIDVsEleSF2",
    input=[q.eta_2, q.tau_decaymode_2, q.gen_match_2],
    output="tau2_output_name",
    scopes=HAD_TAU_SCOPES,
    vec_config="vsele_tau_id_sf",
)

# DeepTau ID vs. muons scale factor for the first tau
TauIDVsMuSF1 = _create_tau_id_vsmu_sf_producer(
    name="TauIDVsMuSF1",
    input=[q.eta_1, q.gen_match_1],
    output="tau1_output_name",
    scopes=TT_SCOPES,
    vec_config="vsmu_tau_id_sf",
)

# DeepTau ID vs. muons scale factor for the second tau
TauIDVsMuSF2 = _create_tau_id_vsmu_sf_producer(
    name="TauIDVsMuSF2",
    input=[q.eta_2, q.gen_match_2],
    output="tau2_output_name",
    scopes=HAD_TAU_SCOPES,
    vec_config="vsmu_tau_id_sf",
)

# Producer group for all DeepTau ID scale factors
TauIDSF = ProducerGroup(
    name="TauIDSF",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers={
        "tt": [
            TauIDVsJetSF1,
            TauIDVsEleSF1,
            TauIDVsMuSF1,
            TauIDVsJetSF2,
            TauIDVsEleSF2,
            TauIDVsMuSF2,
        ],
        "mt": [
            TauIDVsJetSF2,
            TauIDVsEleSF2,
            TauIDVsMuSF2,
        ],
        "et": [
            TauIDVsJetSF2,
            TauIDVsEleSF2,
            TauIDVsMuSF2,
        ],
    },
)


#
# PRODUCERS FOR SCALE FACTORS OF BOOSTED HADRONIC TAUS (DEPRECATED)
#

Tau_1_oldIsoTauID_tt_SF = ExtendedVectorProducer(
    name="Tau_1_oldIsoTauID_tt_SF",
    call='scalefactor::tau::id_mva_vsJet_tt({df}, correctionManager, {input}, {vec_open}{boostedtau_dms}{vec_close}, "{iso_boostedtau_id_WP}", "{boostedtau_sf_iso_tauDM0}", "{boostedtau_sf_iso_tauDM1}", "{boostedtau_sf_iso_tauDM10}", "{boostedtau_sf_iso_tauDM11}", "{boostedtau_iso_sf_dependence}", "", {output}, "{boostedtau_sf_file}", "{boostedtau_id_discriminator}")',
    input=[q.boosted_pt_1, q.boosted_tau_decaymode_1, q.boosted_gen_match_1],
    output="boostedtau_1_iso_sf_outputname",
    scopes=["tt"],
    vec_config="iso_boostedtau_id",
)
Tau_1_antiEleTauID_SF = ExtendedVectorProducer(
    name="Tau_1_antiEleTauID_SF",
    call="""physicsobject::tau::scalefactor::Id_vsEle(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{era}",
        "{boostedtau_sf_file}", 
        "{boostedtau_id_discriminator}", 
        "{antiele_boostedtau_id_WP}", 
        "{boostedtau_sf_antiele_barrel}", 
        "{boostedtau_sf_antiele_endcap}")
        """,
    input=[q.boosted_eta_1, q.boosted_gen_match_1],
    output="boostedtau_1_antiele_sf_outputname",
    scopes=["tt"],
    vec_config="antiele_boostedtau_id",
)
Tau_1_antiMuTauID_SF = ExtendedVectorProducer(
    name="Tau_1_antiMuTauID_SF",
    call="""physicsobject::tau::scalefactor::Id_vsMu(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{boostedtau_sf_file}", 
        "{boostedtau_id_discriminator}", 
        "{antimu_boostedtau_id_WP}", 
        "{boostedtau_sf_antimu_wheel1}", 
        "{boostedtau_sf_antimu_wheel2}", 
        "{boostedtau_sf_antimu_wheel3}", 
        "{boostedtau_sf_antimu_wheel4}", 
        "{boostedtau_sf_antimu_wheel5}")
        """,
    input=[q.boosted_eta_1, q.boosted_gen_match_1],
    output="boostedtau_1_antimu_sf_outputname",
    scopes=["tt"],
    vec_config="antimu_boostedtau_id",
)
Tau_2_oldIsoTauID_tt_SF = ExtendedVectorProducer(
    name="Tau_2_oldIsoTauID_tt_SF",
    call='scalefactor::tau::id_mva_vsJet_tt({df}, correctionManager, {input}, {vec_open}{boostedtau_dms}{vec_close}, "{iso_boostedtau_id_WP}", "{boostedtau_sf_iso_tauDM0}", "{boostedtau_sf_iso_tauDM1}", "{boostedtau_sf_iso_tauDM10}", "{boostedtau_sf_iso_tauDM11}", "{boostedtau_iso_sf_dependence}", "", {output}, "{boostedtau_sf_file}", "{boostedtau_id_discriminator}")',
    input=[q.boosted_pt_2, q.boosted_tau_decaymode_2, q.boosted_gen_match_2],
    output="boostedtau_2_iso_sf_outputname",
    scopes=["tt"],
    vec_config="iso_boostedtau_id",
)
Tau_2_oldIsoTauID_lt_SF = ExtendedVectorProducer(
    name="Tau_2_oldIsoTauID_lt_SF",
    call='scalefactor::tau::id_mva_vsJet_lt({df}, correctionManager, {input}, {vec_open}{boostedtau_dms}{vec_close}, "{iso_boostedtau_id_WP}", "{boostedtau_sf_iso_tau30to35}", "{boostedtau_sf_iso_tau35to40}", "{boostedtau_sf_iso_tau40to500}", "{boostedtau_sf_iso_tau500to1000}", "{boostedtau_sf_iso_tau1000toinf}", "{boostedtau_iso_sf_dependence}", "", {output}, "{boostedtau_sf_file}", "{boostedtau_id_discriminator}")',
    input=[q.boosted_pt_2, q.boosted_tau_decaymode_2, q.boosted_gen_match_2],
    output="boostedtau_2_iso_sf_outputname",
    scopes=["et", "mt"],
    vec_config="iso_boostedtau_id",
)
Tau_2_antiEleTauID_SF = ExtendedVectorProducer(
    name="Tau_2_antiEleTauID_SF",
    call="""physicsobject::tau::scalefactor::Id_vsEle(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{era}",
        "{boostedtau_sf_file}", 
        "{boostedtau_id_discriminator}", 
        "{antiele_boostedtau_id_WP}", 
        "{boostedtau_sf_antiele_barrel}", 
        "{boostedtau_sf_antiele_endcap}")
        """,
    input=[q.boosted_eta_2, q.boosted_gen_match_2],
    output="boostedtau_2_antiele_sf_outputname",
    scopes=["et", "mt", "tt"],
    vec_config="antiele_boostedtau_id",
)
Tau_2_antiMuTauID_SF = ExtendedVectorProducer(
    name="Tau_2_antiMuTauID_SF",
    call="""physicsobject::tau::scalefactor::Id_vsMu(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{boostedtau_sf_file}", 
        "{boostedtau_id_discriminator}", 
        "{antimu_boostedtau_id_WP}", 
        "{boostedtau_sf_antimu_wheel1}", 
        "{boostedtau_sf_antimu_wheel2}", 
        "{boostedtau_sf_antimu_wheel3}", 
        "{boostedtau_sf_antimu_wheel4}", 
        "{boostedtau_sf_antimu_wheel5}")
        """,
    input=[q.boosted_eta_2, q.boosted_gen_match_2],
    output="boostedtau_2_antimu_sf_outputname",
    scopes=["et", "mt", "tt"],
    vec_config="antimu_boostedtau_id",
)
#BoostedTauID_SF = ProducerGroup(
#    name="BoostedTauID_SF",
#    call=None,
#    input=None,
#    output=None,
#    scopes=["tt", "mt", "et"],
#    subproducers={
#        "tt": [
#            Tau_1_VsJetTauID_SF,
#            Tau_1_VsEleTauID_SF,
#            Tau_1_VsMuTauID_SF,
#            Tau_2_oldIsoTauID_tt_SF,
#            Tau_2_antiEleTauID_SF,
#            Tau_2_antiMuTauID_SF,
#        ],
#        "mt": [
#            Tau_2_oldIsoTauID_lt_SF,
#            Tau_2_antiEleTauID_SF,
#            Tau_2_antiMuTauID_SF,
#        ],
#        "et": [
#            Tau_2_oldIsoTauID_lt_SF,
#            Tau_2_antiEleTauID_SF,
#            Tau_2_antiMuTauID_SF,
#        ],
#    },
#)

#########################
# Electron ID/ISO SF
#########################
Ele_1_Reco_SF = Producer(
    name="Ele_1_Reco_SF",
    call="""physicsobject::electron::scalefactor::Id(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{ele_sf_year_id}", 
        "{ele_reco_sf_name}", 
        "{ele_sf_file}", 
        "{ele_sf_cset_name}", 
        "{ele_reco_sf_variation}")
        """,
    input=[q.pt_1, q.eta_1, q.phi_1],
    output=[q.reco_wgt_ele_1],
    scopes=["em", "ee", "et"],
)
Ele_2_Reco_SF = Producer(
    name="Ele_2_Reco_SF",
    call="""physicsobject::electron::scalefactor::Id(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{ele_sf_year_id}", 
        "{ele_reco_sf_name}", 
        "{ele_sf_file}", 
        "{ele_sf_cset_name}", 
        "{ele_reco_sf_variation}")
        """,
    input=[q.pt_2, q.eta_2, q.phi_2],
    output=[q.reco_wgt_ele_2],
    scopes=["ee"],
)
Ele_1_IDWP90_SF = Producer(
    name="Ele_1_IDWP90_SF",
    call="""physicsobject::electron::scalefactor::Id(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{ele_sf_year_id}", 
        "{ele_id_sf_name}", 
        "{ele_sf_file}", 
        "{ele_sf_cset_name}", 
        "{ele_id_sf_variation}")
        """,
    input=[q.pt_1, q.eta_1, q.phi_1],
    output=[q.id_wgt_ele_1],
    scopes=["em", "ee", "et"],
)
Ele_2_IDWP90_SF = Producer(
    name="Ele_2_IDWP90_SF",
    call="""physicsobject::electron::scalefactor::Id(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{ele_sf_year_id}", 
        "{ele_id_sf_name}", 
        "{ele_sf_file}", 
        "{ele_sf_cset_name}", 
        "{ele_id_sf_variation}")
        """,
    input=[q.pt_2, q.eta_2, q.phi_2],
    output=[q.id_wgt_ele_2],
    scopes=["ee"],
)
EleID_SF = ProducerGroup(
    name="EleID_SF",
    call=None,
    input=None,
    output=None,
    scopes=["em", "ee", "et"],
    subproducers={
        "em": [
            #Ele_1_Reco_SF,  TODO a bit tedious to implement
            Ele_1_IDWP90_SF,
        ],
        "ee": [
            #Ele_1_Reco_SF,  TODO a bit tedious to implement
            #Ele_2_Reco_SF,  TODO a bit tedious to implement
            Ele_1_IDWP90_SF,
            Ele_2_IDWP90_SF,
        ],
        "et": [
            #Ele_1_Reco_SF,  TODO a bit tedious to implement
            Ele_1_IDWP90_SF,
        ],
    },
)
Ele_1_Reco_SF_boosted = Producer(
    name="Ele_1_Reco_SF_boosted",
    call="""physicsobject::electron::scalefactor::Id(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{ele_sf_year_id}", 
        "{ele_reco_sf_name}", 
        "{ele_sf_file}", 
        "{ele_sf_cset_name}", 
        "{ele_reco_sf_variation}")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1, q.boosted_phi_1],
    output=[q.reco_wgt_ele_boosted_1],
    scopes=["et"],
)
Ele_1_IDWP90_SF_boosted = Producer(
    name="Ele_1_IDWP90_SF_boosted",
    call="""physicsobject::electron::scalefactor::Id(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{ele_sf_year_id}", 
        "{ele_id_sf_name}", 
        "{ele_sf_file}", 
        "{ele_sf_cset_name}", 
        "{ele_id_sf_variation}")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1, q.boosted_phi_1],
    output=[q.id_wgt_ele_boosted_wp90nonIso_1],
    scopes=["et"],
)
EleID_SF_boosted = ProducerGroup(
    name="EleID_SF_boosted",
    call=None,
    input=None,
    output=None,
    scopes=["et"],
    subproducers={
        "et": [
            #Ele_1_Reco_SF_boosted,
            Ele_1_IDWP90_SF_boosted
        ],
    },
)

###################################
# Trigger Scalefactors coming from our measurements
###################################


#
# SINGLE ELECTRON TRIGGER SCALE FACTORS
#


# single electron trigger scale factor
SingleEleTriggerSF = ExtendedVectorProducer(
    name="SingleEleTriggerSF",
    call='physicsobject::electron::scalefactor::Trigger({df}, correctionManager, {output}, {input}, "{e_trigger_flag}", "{e_trigger_era}", "{e_trigger_path_id_name}", "{e_trigger_sf_file}", "{e_trigger_sf_name}", "{e_trigger_variation}")',
    input=[
        q.pt_1,
        q.eta_1,
    ],
    output="e_trigger_flagname",
    scopes=ELECTRON_SCOPES,
    vec_config="ele_trigger_sf",
)


#
# SINGLE MUON TRIGGER SCALE FACTORS
#


# single muon trigger scale factor
SingleMuTriggerSF = ExtendedVectorProducer(
    name="SingleMuTriggerSF",
    call='physicsobject::muon::scalefactor::Trigger({df}, correctionManager, {output}, {input}, "{m_trigger_flag}", "{muon_sf_file}", "{m_trigger_sf_name}", "{m_trigger_variation}")',
    input={
        "mt": [q.pt_1, q.eta_1],
        "mm": [q.pt_1, q.eta_1],
        "em": [q.pt_2, q.eta_2],
    },
    output="m_trigger_flagname",
    scopes=MUON_SCOPES,
    vec_config="mu_trigger_sf",
)


#
# DOUBLE MUON-TAU TRIGGER SCALE FACTORS
#


# muon leg scale factor
DoubleMuTauTriggerLeg1SF = ExtendedVectorProducer(
    name="DoubleMuTauTriggerLeg1SF",
    call='physicsobject::muon::scalefactor::Trigger({df}, correctionManager, {output}, {input}, "{mt_trigger_flag}", "{mt_trigger_leg1_sf_file}", "{mt_trigger_leg1_sf_name}", "{mt_trigger_leg1_variation}")',
    input=[
        q.pt_1,
        q.eta_1,
    ],
    output="mt_trigger_leg1_flagname",
    scopes=MT_SCOPES,
    vec_config="double_mutau_trigger_leg1_sf",
)

# tau leg scale factor (for the Medium DeepTau WP)
DoubleMuTauTriggerLeg2SF = ExtendedVectorProducer(
    name="GenerateMuTauCrossTriggerLeg2SF",
    call='physicsobject::tau::scalefactor::Trigger({df}, correctionManager, {output}, {input}, "{mt_trigger_flag}", "{tau_trigger_sf_file}", "tau_trigger", "{mt_trigger_leg2_sf_name}", "Medium", "sf", "{mt_trigger_leg2_variation}")',
    input=[
        q.pt_2,
        q.tau_decaymode_2,
    ],
    output="mt_trigger_leg2_flagname",
    scopes=MT_SCOPES,
    vec_config="double_mutau_trigger_leg2_sf",
)

# producer group containing the scale factors for both legs of the double muon-tau trigger
DoubleMuTauTriggerSF = ProducerGroup(
    name="DoubleMuTauTriggerSF",
    call=None,
    input=None,
    output=None,
    scopes=MT_SCOPES,
    subproducers=[
        DoubleMuTauTriggerLeg1SF,
        DoubleMuTauTriggerLeg2SF,
    ],
)


#
# DOUBLE ELECTRON-TAU TRIGGER SCALE FACTORS
#


# muon leg scale factor
DoubleEleTauTriggerLeg1SF = ExtendedVectorProducer(
    name="DoubleEleTauTriggerLeg1SF",
    call='physicsobject::electron::scalefactor::Trigger({df}, correctionManager, {output}, {input}, "{et_trigger_flag}", "{et_trigger_leg1_era}", "{et_trigger_leg1_path_id_name}", "{et_trigger_leg1_sf_file}", "{et_trigger_leg1_sf_name}", "{et_trigger_leg1_variation}")',
    input=[
        q.pt_1,
        q.eta_1,
    ],
    output="et_trigger_leg1_flagname",
    scopes=ET_SCOPES,
    vec_config="double_eletau_trigger_leg1_sf",
)

# tau leg scale factor (for the Medium DeepTau WP)
DoubleEleTauTriggerLeg2SF = ExtendedVectorProducer(
    name="DoubleEleTauTriggerLeg2SF",
    call='physicsobject::tau::scalefactor::Trigger({df}, correctionManager, {output}, {input}, "{et_trigger_flag}", "{tau_trigger_sf_file}", "tau_trigger", "{et_trigger_leg2_sf_name}", "Medium", "sf", "{et_trigger_leg2_variation}")',
    input=[
        q.pt_2,
        q.tau_decaymode_2,
    ],
    output="et_trigger_leg2_flagname",
    scopes=ET_SCOPES,
    vec_config="double_eletau_trigger_leg2_sf",
)

# producer group containing the scale factors for both legs of the double electron-tau trigger
DoubleEleTauTriggerSF = ProducerGroup(
    name="DoubleEleTauTriggerSF",
    call=None,
    input=None,
    output=None,
    scopes=ET_SCOPES,
    subproducers=[
        DoubleEleTauTriggerLeg1SF,
        DoubleEleTauTriggerLeg2SF,
    ],
)


#
# DOUBLE TAU-TAU TRIGGER SCALE FACTORS
#


# muon leg scale factor
TauTauTriggerLeg1SF = ExtendedVectorProducer(
    name="DoubleTauTauTriggerLeg1SF",
    call='physicsobject::tau::scalefactor::Trigger({df}, correctionManager, {output}, {input}, "{tt_trigger_flag}", "{tau_trigger_sf_file}", "tau_trigger", "{tt_trigger_leg1_sf_name}", "Medium", "sf", "{tt_trigger_leg1_variation}")',
    input=[
        q.pt_1,
        q.tau_decaymode_1,
    ],
    output="tt_trigger_leg1_flagname",
    scopes=TT_SCOPES,
    vec_config="double_tautau_trigger_leg1_sf",
)

# tau leg scale factor (for the Medium DeepTau WP)
TauTauTriggerLeg2SF = ExtendedVectorProducer(
    name="DoubleTauTauTriggerLeg2SF",
    call='physicsobject::tau::scalefactor::Trigger({df}, correctionManager, {output}, {input}, "{tt_trigger_flag}", "{tau_trigger_sf_file}", "tau_trigger", "{tt_trigger_leg2_sf_name}", "Medium", "sf", "{tt_trigger_leg2_variation}")',
    input=[
        q.pt_2,
        q.tau_decaymode_2,
    ],
    output="tt_trigger_leg2_flagname",
    scopes=TT_SCOPES,
    vec_config="double_tautau_trigger_leg2_sf",
)

# producer group containing the scale factors for both legs of the double electron-tau trigger
TauTauTriggerSF = ProducerGroup(
    name="DoubleTauTauTriggerSF",
    call=None,
    input=None,
    output=None,
    scopes=TT_SCOPES,
    subproducers=[
        TauTauTriggerLeg1SF,
        TauTauTriggerLeg2SF,
    ],
)


BoostedMTGenerateSingleMuonTriggerSF_MC = ExtendedVectorProducer(
    name="BoostedMTGenerateSingleMuonTriggerSF_MC",
    call='scalefactor::muon::trigger({df}, correctionManager, {input}, "{muon_trg_sf_variation}", {output}, "{muon_sf_file}", "{muon_trigger_sf_name}")',
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output="flagname",
    scopes=["mt"],
    vec_config="boosted_singlemuon_trigger_sf_mc",
)

ETGenerateSingleElectronTriggerSF_MC = ExtendedVectorProducer(
    name="ETGenerateSingleElectronTriggerSF_MC",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_electron_sf_file}", 
        "{mc_trigger_sf}", 
        "mc", 
        {mc_electron_trg_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output="flagname",
    scopes=["et", "ee"],
    vec_config="singlelectron_trigger_sf_mc",
)
BoostedETGenerateSingleElectronTriggerSF_MC = ExtendedVectorProducer(
    name="BoostedETGenerateSingleElectronTriggerSF_MC",
    call='scalefactor::electron::trigger({df}, correctionManager, {input}, "{ele_trg_sf_variation}", {output}, "{ele_trg_sf_file}", "{ele_trg_sf_name}")',
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output="flagname",
    scopes=["et"],
    vec_config="boosted_singleelectron_trigger_sf_mc",
)

TTGenerateDoubleTauTriggerSF_MC_1 = Producer(
    name="TTGenerateDoubleTauTriggerSF_MC_1",
    call="""physicsobject::tau::scalefactor::Trigger(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{tau_trigger_sf_file}", 
        "tau_trigger", 
        "{ditau_trigger_type}", 
        "{ditau_trigger_wp}", 
        "{ditau_trigger_corrtype}", 
        "{ditau_trigger_syst}")
        """,
    input=[q.pt_1, q.tau_decaymode_1],
    output=[q.trg_wgt_double_tau_1],
    scopes=["tt"],
)
TTGenerateDoubleTauTriggerSF_MC_2 = Producer(
    name="TTGenerateDoubleTauTriggerSF_MC_2",
    call="""physicsobject::tau::scalefactor::Trigger(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{tau_trigger_sf_file}", 
        "tau_trigger", 
        "{ditau_trigger_type}", 
        "{ditau_trigger_wp}", 
        "{ditau_trigger_corrtype}", 
        "{ditau_trigger_syst}")
        """,
    input=[q.pt_2, q.tau_decaymode_2],
    output=[q.trg_wgt_double_tau_2],
    scopes=["tt"],
)
TTGenerateDoubleTauTriggerSF_MC = ProducerGroup(
    name="TTGenerateDoubleTauTriggerSF_MC",
    call=None,
    input=None,
    output=None,
    scopes=["tt"],
    subproducers=[
        TTGenerateDoubleTauTriggerSF_MC_1,
        TTGenerateDoubleTauTriggerSF_MC_2,
    ],
)
BoostedTTGenerateFatjetTriggerSF_MC = Producer(
    name="BoostedTTGenerateFatjetTriggerSF_MC",
    call='scalefactor::fatjet::trigger({df}, correctionManager, {input}, {output}, "{fatjet_trigger_sf_file}", "{fatjet_trigger_sf_name}", "{fatjet_trigger_sf_syst}")',
    input=[q.fj_leading_pt, q.fj_leading_msoftdrop],
    output=[q.trg_wgt_fatjet],
    scopes=["tt"],
)

####################################
# Electron and Muon SFs coming from our measurements
####################################
TauEmbeddingMuonIDSF_1_MC = Producer(
    name="TauEmbeddingMuonIDSF_1_MC",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_muon_sf_file}", 
        "{mc_muon_id_sf}", 
        "mc", 
        {mc_muon_id_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.id_wgt_mu_1],
    scopes=["mt", "mm"],
)

TauEmbeddingMuonIDSF_2_MC = Producer(
    name="TauEmbeddingMuonIDSF_2_MC",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_muon_sf_file}", 
        "{mc_muon_id_sf}", 
        "mc", 
        {mc_muon_id_extrapolation})
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.id_wgt_mu_2],
    scopes=["mm", "em"],
)

TauEmbeddingMuonIsoSF_1_MC = Producer(
    name="TauEmbeddingMuonIsoSF_1_MC",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_muon_sf_file}", 
        "{mc_muon_iso_sf}", 
        "mc", 
        {mc_muon_iso_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.iso_wgt_mu_1],
    scopes=["mt", "mm"],
)

TauEmbeddingMuonIsoSF_2_MC = Producer(
    name="TauEmbeddingMuonIsoSF_2_MC",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_muon_sf_file}", 
        "{mc_muon_iso_sf}", 
        "mc", 
        {mc_muon_iso_extrapolation})
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.iso_wgt_mu_2],
    scopes=["mm", "em"],
)

TauEmbeddingBoostedMuonIDSF_1_MC = Producer(
    name="TauEmbeddingBoostedMuonIDSF_1_MC",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_muon_sf_file}", 
        "{mc_muon_id_sf}", 
        "mc")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.emb_id_wgt_mu_boosted_1],
    scopes=["mt", "mm"],
)
TauEmbeddingBoostedMuonIsoSF_1_MC = Producer(
    name="TauEmbeddingBoostedMuonIsoSF_1_MC",
    call="""embedding::muon::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_muon_sf_file}", 
        "{mc_muon_iso_sf}", 
        "mc")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.emb_iso_wgt_mu_boosted_1],
    scopes=["mt", "mm"],
)

# Electron ID/Iso/Trigger SFS

TauEmbeddingElectronIDSF_1_MC = Producer(
    name="TauEmbeddingElectronIDSF_1_MC",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_electron_sf_file}", 
        "{mc_electron_id_sf}", 
        "mc", 
        {mc_electron_id_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.id_wgt_ele_1],
    scopes=["et", "ee", "em"],
)

TauEmbeddingElectronIDSF_2_MC = Producer(
    name="TauEmbeddingElectronIDSF_2_MC",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_electron_sf_file}", 
        "{mc_electron_id_sf}", 
        "mc", 
        {mc_electron_id_extrapolation})
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.id_wgt_ele_2],
    scopes=["ee"],
)

TauEmbeddingElectronIsoSF_1_MC = Producer(
    name="TauEmbeddingElectronIsoSF_1_MC",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_electron_sf_file}", 
        "{mc_electron_iso_sf}", 
        "mc", 
        {mc_electron_iso_extrapolation})
        """,
    input=[q.pt_1, q.eta_1],
    output=[q.iso_wgt_ele_1],
    scopes=["et", "ee", "em"],
)

TauEmbeddingElectronIsoSF_2_MC = Producer(
    name="TauEmbeddingElectronIsoSF_2_MC",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_electron_sf_file}", 
        "{mc_electron_iso_sf}", 
        "mc", 
        {mc_electron_iso_extrapolation})
        """,
    input=[q.pt_2, q.eta_2],
    output=[q.iso_wgt_ele_2],
    scopes=["ee"],
)

TauEmbeddingBoostedElectronIDSF_1_MC = Producer(
    name="TauEmbeddingBoostedElectronIDSF_1_MC",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_electron_sf_file}", 
        "{mc_electron_id_sf}", 
        "mc")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.id_wgt_ele_boosted_1],
    scopes=["et", "ee", "em"],
)
TauEmbeddingBoostedElectronIsoSF_1_MC = Producer(
    name="TauEmbeddingBoostedElectronIsoSF_1_MC",
    call="""embedding::electron::Scalefactor(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{mc_electron_sf_file}", 
        "{mc_electron_iso_sf}", 
        "mc")
        """,
    input=[q.boosted_pt_1, q.boosted_eta_1],
    output=[q.iso_wgt_ele_boosted_1],
    scopes=["et", "ee", "em"],
)

#
# B JET ID
#

# B jet identification scale factor for DeepJet
BJetShapeDeepJet_SF = Producer(
    name="BJetShapeDeepJet_SF",
    call="""
    physicsobject::jet::scalefactor::BtaggingShape(
        {df},
        correctionManager,
        {output},
        {input},
        "{bjet_sf_file}",
        "{bjet_sf_name}",
        "{bjet_sf_variation}"
    )
    """,
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_btagDeepFlavB,
        nanoAOD.Jet_hadronFlavour,
        q.good_jets_mask,
        q.good_bjets_mask,
        q.jet_overlap_veto_mask,
    ],
    output=[q.id_wgt_bjet],
    scopes=SCOPES,
)

# B jet identification scale factor for ParticleNet
BJetShapePNet_SF = Producer(
    name="BJetShapePNet_SF",
    call="""
    physicsobject::jet::scalefactor::BtaggingShape(
        {df},
        correctionManager,
        {output},
        {input},
        "{bjet_sf_file}",
        "{bjet_sf_name}",
        "{bjet_sf_variation}"
    )
    """,
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_btagPNetB,
        nanoAOD.Jet_hadronFlavour,
        q.good_jets_mask,
        q.good_bjets_mask,
        q.jet_overlap_veto_mask,
    ],
    output=[q.id_wgt_bjet],
    scopes=SCOPES,
)

# B jet identification scale factor for UParT (multiple WP setup)
BJetWPUParT_SF = Producer(
    name="BJetWPUParT_SF",
    call="""
    physicsobject::jet::scalefactor::BtaggingMultipleWP(
        {df},
        correctionManager,
        {output},
        {input},
        "{bjet_sf_file}",
        "{bjet_sf_bc_name}",
        "{bjet_sf_light_name}",
        "{bjet_sf_wp_name}",
        "{bjet_eff_file}",
        "{bjet_eff_name}",
        "{bjet_eff_sample_type}",
        "{bjet_sf_variation_bc}",
        "{bjet_sf_variation_lf}"
    )
    """,
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_btagUParTAK4B,
        nanoAOD.Jet_hadronFlavour,
        q.good_jets_mask,
        q.good_bjets_mask,
        q.jet_overlap_veto_mask,
    ],
    output=[q.id_wgt_bjet],
    scopes=SCOPES,
)

btagging_SF_boosted = Producer(
    name="btagging_SF_boosted",
    call="""physicsobject::jet::scalefactor::BtaggingShape(
        {df}, 
        correctionManager, 
        {output}, 
        {input}, 
        "{btag_sf_file}", 
        "{btag_corr_algo}", 
        "{btag_sf_variation}")
        """,
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_btagDeepFlavB,
        nanoAOD.Jet_hadronFlavour,
        q.good_jets_mask,
        q.good_bjets_mask,
        q.jet_overlap_veto_mask_boosted,
    ],
    output=[q.btag_weight_boosted],
    scopes=["tt", "mt", "et", "mm", "em", "ee"],
)

#########################
# particleNet tagging SF
#########################
Xbb_tagging_SF = Producer(
    name="Xbb_tagging_SF",
    call='scalefactor::fatjet::pNetXbbSF({df}, correctionManager, {input}, "{pNetXbb_sf_variation}", {output}, "{pNetXbb_sf_file}")',
    input=[
        q.fj_Xbb_pt,
        q.fj_Xbb_nBhad,
        q.fj_Xbb_nChad,
    ],
    output=[q.pNet_Xbb_weight],
    scopes=["tt", "mt", "et", "mm", "em", "ee"],
)
Xbb_tagging_SF_boosted = Producer(
    name="Xbb_tagging_SF_boosted",
    call='scalefactor::fatjet::pNetXbbSF({df}, correctionManager, {input}, "{pNetXbb_sf_variation}", {output}, "{pNetXbb_sf_file}")',
    input=[
        q.fj_Xbb_pt_boosted,
        q.fj_Xbb_nBhad_boosted,
        q.fj_Xbb_nChad_boosted,
    ],
    output=[q.pNet_Xbb_weight_boosted],
    scopes=["tt", "mt", "et", "mm", "em", "ee"],
)
