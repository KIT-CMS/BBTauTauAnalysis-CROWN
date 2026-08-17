"""SM non-resonant HH -> bbtautau entry point (2018 UL NanoAOD v15, UParT)."""
from code_generation.configuration import Configuration  # noqa: F401  (build-type dispatch)

from .analysis_profiles import SM_PROFILE
from . import common_config

AVAILABLE_ERAS = ["2018"]
DEFAULT_SAMPLES = [
    "hh2b2tau", "data", "dyjets", "wjets", "ttbar", "singletop", "diboson",
    "electroweak_boson", "ggh_htautau", "vbf_htautau", "vbf_hbb", "rem_hbb",
    "rem_higgs", "rem_ttbar",
]
# embedding/embedding_mc stay available for explicitly named commissioning
# builds only; they are never part of DEFAULT_SAMPLES (Phase-1 exclusion).
AVAILABLE_SAMPLES = DEFAULT_SAMPLES + ["embedding", "embedding_mc"]


def build_config(era, sample, scopes, shifts, available_sample_types,
                 available_eras, available_scopes):
    return common_config.build_config(
        SM_PROFILE, era, sample, scopes, shifts,
        available_sample_types, available_eras, available_scopes,
    )
