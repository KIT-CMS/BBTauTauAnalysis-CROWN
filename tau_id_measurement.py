"""
Tau-ID SF and energy scale measurement for embedding (Run-2 eras; mt and mm).

The measurement keeps the SM selection and takes its corrections from jvoss's
measurement production SFs_EMB_Run2_04_08_26 (TauAnalysis config_run2_v15), the
precedent listed in the README section "Tau-ID measurement":

- the single-muon trigger of the era (TM_SINGLE_MUON_TRIGGERS) in data, MC and
  embedding, with the KIT trigger SFs of the Tau Embedding group
  (TM_KIT_TRIGGER_SFS; type "mc" in MC, "emb" in embedding): 2016 the IsoMu22
  family, 2017 IsoMu27, 2018 IsoMu24 || IsoMu27 as the precedent;
- the KIT muon ID and isolation SFs in MC, of both muons in mm;
- the MC tau energy scale of vsJet Loose and vsJet SFs for Medium and Tight;
- the L1 prefiring weight of MC (v7 spec E11, 2018 the muon part);
- the MC shifts of the analysis, except for the vsJet SF it measures and the POG
  muon SFs it replaces, plus the shifts of its KIT trigger SF and the prefiring
  weight (the exception of v7 spec E34: the measurement production keeps its MC
  shifts).

In mt it writes the columns of the efficiency measurement of the tau leg of the
di-tau trigger (v7 spec E33, docs v7_tt_emb_trigger 12.4): the monitoring-path flags
of the tau, the embedding di-tau filter flags and the matched trigger object
(tau_triggersetup.TAU_LEG_*).

The embedded events come from embedding_run2_v15 (mt: mu -> tau, mm: mu -> mu) with
uncorrected taus; ShapeSmith applies the energy scale grid downstream.
"""

from code_generation.configuration import Configuration
from code_generation.rules import AppendProducer, ReplaceProducer

from .constants import ERAS_RUN2, MM_SCOPES, MT_SCOPES
from .helpers import cpp_list
from .producers import event, scalefactors, triggers
from .quantities import output as q
from .tau_triggersetup import (
    KIT_SINGLE_LEPTON_MATCH_MAX_DELTA_R,
    KIT_SINGLE_MUON_TRIGGER_SFS,
    SINGLE_MUON_TRIGGERS,
    TAU_LEG,
    TAU_LEG_EMBEDDING_FILTERS,
    TAU_LEG_MONITOR_TRIGGERS,
    TAU_LEG_TRIGGER_OBJECT_BITS,
    single_lepton_triggers,
    tau_leg_flags,
)
from .variations.pileup_prefiring import COMMON_PREFIRING_ERAS, add_prefiring_shifts
from .variations.triggers import add_single_muon_trigger_extrapolation_shifts

MEASUREMENT_SCOPES = MT_SCOPES + MM_SCOPES
MC_SAMPLES = ("dyjets", "wjets", "ttbar", "singletop", "diboson")
NOT_MC = ["data", "embedding", "embedding_mc"]
# The single-muon triggers per era. 2016 and 2017 take the analysis triggers
# (tau_triggersetup.SINGLE_MUON_TRIGGERS, v7 spec E2, E3); 2018 those of the
# measurement production: IsoMu24 || IsoMu27, filter bit 3 (1mu), |eta| < 2.5. All
# are matched within the Delta R 0.1 of the KIT tag and probe (K8).
TM_SINGLE_MUON_TRIGGERS = {
    **{
        era: single_lepton_triggers(SINGLE_MUON_TRIGGERS, era, kit=True)
        for era in ("2016preVFP", "2016postVFP", "2017")
    },
    "2018": [
        {
            "flagname": flag,
            "hlt_path": hlt_path,
            "min_pt": min_pt,
            "max_abs_eta": 2.5,
            "filter_bit": 3,
            "particle_id": 13,
            "match_max_delta_r": KIT_SINGLE_LEPTON_MATCH_MAX_DELTA_R,
        }
        for flag, hlt_path, min_pt in [
            ("trg_single_mu24", "HLT_IsoMu24", 25.0),
            ("trg_single_mu27", "HLT_IsoMu27", 28.0),
        ]
    ],
}
# trigger SF column -> correction of the Tau Embedding group payload per era
TM_KIT_TRIGGER_SFS = {
    **{era: KIT_SINGLE_MUON_TRIGGER_SFS[era] for era in ("2016preVFP", "2016postVFP", "2017")},
    "2018": {
        "trg_wgt_single_mu24": "Trg_IsoMu24_pt_eta_bins",
        "trg_wgt_single_mu27": "Trg_IsoMu27_pt_eta_bins",
        "trg_wgt_single_mu24ormu27": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
    },
}
# MC is weighted with the L1 prefiring weight in every era (E11)
PREFIRING_ERAS = tuple(ERAS_RUN2)


def setup(configuration: Configuration, era: str, sample: str, scopes: list[str]):
    """Configure a measurement build of `sample` for `era` and `scopes`."""
    if era not in TM_SINGLE_MUON_TRIGGERS:
        raise ValueError(
            f"The tau-ID measurement exists for {sorted(TM_SINGLE_MUON_TRIGGERS)} only, "
            f"got era '{era}'."
        )
    unsupported = sorted(set(scopes) - set(MEASUREMENT_SCOPES))
    if unsupported:
        raise ValueError(
            f"The tau-ID measurement is built for {MEASUREMENT_SCOPES} only, got {unsupported}."
        )

    _add_muon_triggers(configuration, era)
    _add_tau_leg_trigger_columns(configuration, era)
    _add_mc_muon_scalefactors(configuration)
    _add_mc_tau_corrections(configuration)
    _add_prefiring(configuration, era, sample)
    _add_mc_shifts(configuration, era)


def _add_muon_triggers(configuration: Configuration, era: str):
    # The KIT SF producer of MC (scalefactors.KitSingleMuonTriggerSF) and its output
    # come from build_config (kit_single_lepton_triggers); the common rules remove
    # it from data and embedding, which embedding_run2_v15 gives the "emb" SFs.
    sfs = TM_KIT_TRIGGER_SFS[era]
    configuration.add_config_parameters(
        MEASUREMENT_SCOPES,
        {
            "mu_trigger": TM_SINGLE_MUON_TRIGGERS[era],
            "singlemuon_trigger_sf_mc": [
                {"flagname": flag, "mc_trigger_sf": sf, "mc_muon_trg_extrapolation": 1.0}
                for flag, sf in sfs.items()
            ],
            # in place of the analysis SFs of embedding_run2_v15
            "singlemuon_trigger_sf": [
                {"flagname": flag, "embedding_trigger_sf": sf, "muon_trg_extrapolation": 1.0}
                for flag, sf in sfs.items()
            ],
        },
    )


def _add_tau_leg_trigger_columns(configuration: Configuration, era: str):
    # v7_tt_emb_trigger 12.4: in mt for data, MC and embedding
    configuration.add_config_parameters(
        MT_SCOPES,
        {
            "tau_leg_monitor_trigger": tau_leg_flags(TAU_LEG_MONITOR_TRIGGERS[era]),
            "tau_leg_embedding_filter": tau_leg_flags(TAU_LEG_EMBEDDING_FILTERS[era]),
            "tau_leg_trigobj_particle_id": TAU_LEG["particle_id"],
            "tau_leg_trigobj_filter_bits": cpp_list(list(TAU_LEG_TRIGGER_OBJECT_BITS[era])),
            "tau_leg_trigobj_max_delta_r": TAU_LEG["match_max_delta_r"],
        },
    )
    producers = [
        triggers.MTTauLegMonitorTriggerFlags,
        triggers.MTTauLegEmbeddingFilterFlags,
        triggers.MTTauLegTriggerObject,
    ]
    configuration.add_producers(MT_SCOPES, producers)
    configuration.add_outputs(
        MT_SCOPES,
        [
            triggers.MTTauLegMonitorTriggerFlags.output_group,
            triggers.MTTauLegEmbeddingFilterFlags.output_group,
            q.trgobj_pt_2,
            q.trgobj_l1pt_2,
            q.trgobj_l1iso_2,
        ],
    )


def _add_mc_muon_scalefactors(configuration: Configuration):
    configuration.add_modification_rule(
        MEASUREMENT_SCOPES,
        ReplaceProducer(
            producers=[scalefactors.MuonIDIso_SF, scalefactors.TauEmbeddingMuonIDIsoSF_MC],
            exclude_samples=NOT_MC,
        ),
    )


def _add_mc_tau_corrections(configuration: Configuration):
    configuration.add_config_parameters(
        MT_SCOPES,
        {
            "tau_ides_sf_vsjet_wp": "Loose",
            "vsjet_tau_id_sf": [
                {
                    "discriminator": "DeepTau2018v2p5VSjet",
                    "tau1_output_name": f"id_wgt_tau_vsJet_{wp}_1",
                    "tau2_output_name": f"id_wgt_tau_vsJet_{wp}_2",
                    "vsjet_wp": wp,
                }
                for wp in ("Medium", "Tight")
            ],
        },
    )


def _add_prefiring(configuration: Configuration, era: str, sample: str):
    # L1PreFiringWeight_Nom on MC (E11); build_config adds the producer in
    # COMMON_PREFIRING_ERAS for every sample, the measurement adds it in the other
    # eras for MC.
    if era not in PREFIRING_ERAS or sample not in MC_SAMPLES:
        return
    if event.PrefireWeight not in configuration.producers["global"]:
        configuration.add_modification_rule(
            "global",
            AppendProducer(producers=[event.PrefireWeight], samples=list(MC_SAMPLES)),
        )
    configuration.add_outputs(MEASUREMENT_SCOPES, [q.prefireweight])


def _add_mc_shifts(configuration: Configuration, era: str):
    # the other MC shifts are the common ones of build_config; the KIT trigger SF
    # shift CMS_eff_m_trigger_<era> (x 1.02 / 0.98) in mt, where the measurement
    # has its trigger uncertainty
    add_single_muon_trigger_extrapolation_shifts(
        configuration, era, [scalefactors.KitSingleMuonTriggerSF], "mt"
    )
    # CMS_ecal_prefiring_<year>; build_config adds it in COMMON_PREFIRING_ERAS
    if era in PREFIRING_ERAS and era not in COMMON_PREFIRING_ERAS:
        add_prefiring_shifts(configuration, era)
