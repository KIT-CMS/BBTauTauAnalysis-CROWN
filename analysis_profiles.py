"""Immutable analysis profiles consumed by common_config.build_config."""
from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple


@dataclass(frozen=True)
class AnalysisProfile:
    name: str
    # None = all eras allowed (NMSSM); SM profiles are 2018-only.
    allowed_eras: Optional[Tuple[str, ...]]
    signal_samples: Tuple[str, ...]
    # SampleModifier mappings sample -> mother pdgid (default -1).
    bb_truegen_mother_pdgid: Mapping[str, int]
    tautau_truegen_mother_pdgid: Mapping[str, int]
    # Samples for which the STANDARD LHE_Scale_weight producer is removed.
    lhe_scale_weight_excluded_samples: Tuple[str, ...]
    # Samples for which the special NMSSM producer replaces the standard one.
    nmssm_lhe_scale_weight_samples: Tuple[str, ...]
    # Read Run-2 eras from NanoAOD v15 instead of the legacy v9: AK4-PUPPI jets
    # with correctionlib jet ID and v15 JEC/JER, Run-3-style EGM scale+smear,
    # PuppiMET covariance. Not era-specific -- every Run-2 era is meant to move
    # to v15; the per-era payloads are resolved in common_config/btag_payloads.
    use_run2_v15_inputs: bool
    # SM-only b-jet acceptance override; None keeps the era default.
    bjet_max_abs_eta_override: Optional[float]
    # "upart" switches branch/WPs/SF payloads to the UParTAK4 tagger (BTV
    # payload pinned per era in btag_payloads.BTV_UPART_PAYLOADS); None = legacy.
    btag_algorithm: Optional[str]
    # Efficiency payload directory; may contain an "{era}" placeholder.
    btag_payload_dir: Optional[str]
    # Explicit opt-in legacy efficiency alias, e.g. {"hh2b2tau": "ggh_htautau"}.
    legacy_btag_efficiency_alias: Optional[Mapping[str, str]] = None
    # Efficiency-ntuple profile switches.
    mc_only: bool = False
    enable_btag_sf: bool = True
    enable_probe_jet_collection: bool = False


NMSSM_PROFILE = AnalysisProfile(
    name="nmssm",
    allowed_eras=None,
    signal_samples=("nmssm_Ybb", "nmssm_Ytautau"),
    bb_truegen_mother_pdgid={"nmssm_Ybb": 35, "nmssm_Ytautau": 25},
    tautau_truegen_mother_pdgid={"nmssm_Ybb": 25, "nmssm_Ytautau": 35},
    lhe_scale_weight_excluded_samples=(
        "data", "embedding", "embedding_mc", "diboson", "hh2b2tau",
    ),
    nmssm_lhe_scale_weight_samples=("nmssm_Ybb", "nmssm_Ytautau"),
    use_run2_v15_inputs=False,
    bjet_max_abs_eta_override=None,
    btag_algorithm=None,
    btag_payload_dir=None,
)

SM_PROFILE = AnalysisProfile(
    name="sm",
    allowed_eras=("2018",),
    signal_samples=("hh2b2tau",),
    bb_truegen_mother_pdgid={"hh2b2tau": 25},
    tautau_truegen_mother_pdgid={"hh2b2tau": 25},
    # SM keeps the standard LHE producer for hh2b2tau (verified: 9-entry
    # LHEScaleWeight present in the registered v15 HH input).
    lhe_scale_weight_excluded_samples=("data", "embedding", "embedding_mc", "diboson"),
    nmssm_lhe_scale_weight_samples=(),
    use_run2_v15_inputs=True,
    bjet_max_abs_eta_override=2.4,
    btag_algorithm="upart",
    btag_payload_dir="payloads/btagging_efficiencies/upart/{era}",
)

SM_BTAG_EFFICIENCY_PROFILE = AnalysisProfile(
    name="sm_btag_efficiency",
    allowed_eras=("2018",),
    signal_samples=("hh2b2tau",),
    bb_truegen_mother_pdgid={"hh2b2tau": 25},
    tautau_truegen_mother_pdgid={"hh2b2tau": 25},
    lhe_scale_weight_excluded_samples=("data", "embedding", "embedding_mc", "diboson"),
    nmssm_lhe_scale_weight_samples=(),
    use_run2_v15_inputs=True,
    bjet_max_abs_eta_override=2.4,
    btag_algorithm="upart",
    btag_payload_dir=None,
    mc_only=True,
    enable_btag_sf=False,
    enable_probe_jet_collection=True,
)
