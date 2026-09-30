"""
Tau-ID SF and energy scale measurement for embedding (2018; mt and mm).

The measurement keeps the SM selection and takes its corrections from jvoss's
measurement production SFs_EMB_Run2_04_08_26 (TauAnalysis config_run2_v15), the
precedent listed in the README section "Tau-ID measurement":

- the trigger IsoMu24 || IsoMu27 in data, MC and embedding, with the KIT trigger
  SFs of the Tau Embedding group (type "mc" in MC, "emb" in embedding);
- the KIT muon ID and isolation SFs in MC, of both muons in mm;
- the MC tau energy scale of vsJet Loose and vsJet SFs for Medium and Tight;
- the MC shifts of the analysis, except for the vsJet SF it measures and the POG
  muon SFs it replaces, and the shift of its KIT trigger SF.

The embedded events come from embedding_run2_v15 (mt: mu -> tau, mm: mu -> mu) with
uncorrected taus; ShapeSmith applies the energy scale grid downstream.
"""

from code_generation.configuration import Configuration
from code_generation.rules import ReplaceProducer

from .constants import MM_SCOPES, MT_SCOPES
from .producers import scalefactors
from .variations.triggers import add_single_muon_trigger_extrapolation_shifts

MEASUREMENT_SCOPES = MT_SCOPES + MM_SCOPES
MC_SAMPLES = ("dyjets", "wjets", "ttbar", "singletop", "diboson")
NOT_MC = ["data", "embedding", "embedding_mc"]
# trigger flags as in the measurement production: filter bit 3 (1mu), |eta| < 2.5
SINGLE_MUON_TRIGGERS = [
    {
        "flagname": flag,
        "hlt_path": hlt_path,
        "min_pt": min_pt,
        "max_abs_eta": 2.5,
        "filter_bit": 3,
        "particle_id": 13,
        "match_max_delta_r": 0.4,
    }
    for flag, hlt_path, min_pt in [
        ("trg_single_mu24", "HLT_IsoMu24", 25.0),
        ("trg_single_mu27", "HLT_IsoMu27", 28.0),
    ]
]
# trigger SF column -> correction of the Tau Embedding group payload
TRIGGER_SFS = {
    "trg_wgt_single_mu24": "Trg_IsoMu24_pt_eta_bins",
    "trg_wgt_single_mu27": "Trg_IsoMu27_pt_eta_bins",
    "trg_wgt_single_mu24ormu27": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
}


def setup(configuration: Configuration, era: str, sample: str, scopes: list[str]):
    """Configure a measurement build of `sample` for `era` and `scopes`."""
    if era != "2018":
        raise ValueError(f"The tau-ID measurement exists for 2018 only, got era '{era}'.")
    unsupported = sorted(set(scopes) - set(MEASUREMENT_SCOPES))
    if unsupported:
        raise ValueError(
            f"The tau-ID measurement is built for {MEASUREMENT_SCOPES} only, got {unsupported}."
        )

    _add_muon_triggers(configuration, sample)
    _add_mc_muon_scalefactors(configuration)
    _add_mc_tau_corrections(configuration)
    _add_mc_shifts(configuration, era)


def _mc_trigger_sfs(extrapolation: float) -> list[dict]:
    return [
        {"flagname": flag, "mc_trigger_sf": sf, "mc_muon_trg_extrapolation": extrapolation}
        for flag, sf in TRIGGER_SFS.items()
    ]


def _add_muon_triggers(configuration: Configuration, sample: str):
    configuration.add_config_parameters(
        MEASUREMENT_SCOPES,
        {
            "mu_trigger": SINGLE_MUON_TRIGGERS,
            "singlemuon_trigger_sf_mc": _mc_trigger_sfs(1.0),
            # in place of the IsoMu24-only embedding SF of embedding_run2_v15
            "singlemuon_trigger_sf": [
                {"flagname": flag, "embedding_trigger_sf": sf, "muon_trg_extrapolation": 1.0}
                for flag, sf in TRIGGER_SFS.items()
            ],
        },
    )
    # the common rules remove the POG trigger SF from data and embedding
    configuration.add_modification_rule(
        MEASUREMENT_SCOPES,
        ReplaceProducer(
            producers=[
                scalefactors.SingleMuTriggerSF,
                scalefactors.MTGenerateSingleMuonTriggerSF_MC,
            ],
            exclude_samples=NOT_MC,
        ),
    )
    if sample in MC_SAMPLES:
        configuration.add_outputs(
            MEASUREMENT_SCOPES, scalefactors.MTGenerateSingleMuonTriggerSF_MC.output_group
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


def _add_mc_shifts(configuration: Configuration, era: str):
    # the other MC shifts are the common ones of build_config
    add_single_muon_trigger_extrapolation_shifts(
        configuration, era, [scalefactors.MTGenerateSingleMuonTriggerSF_MC], "mt"
    )
