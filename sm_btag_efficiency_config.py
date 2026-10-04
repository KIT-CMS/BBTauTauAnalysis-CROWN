"""SM HH -> bbtautau b-tagging efficiency ntuple entry point (MC only)."""
from code_generation.configuration import Configuration  # noqa: F401  (build-type dispatch)

from .analysis_profiles import SM_BTAG_EFFICIENCY_PROFILE
from . import common_config

AVAILABLE_ERAS = ["2018"]
AVAILABLE_SAMPLES = [
    "hh2b2tau", "dyjets", "wjets", "ttbar", "singletop", "diboson",
    "electroweak_boson", "ggh_htautau", "vbf_htautau", "vbf_hbb", "rem_hbb",
    "rem_higgs", "rem_ttbar",
]

def build_config(era, sample, scopes, shifts, available_sample_types,
                 available_eras, available_scopes):
    return common_config.build_config(
        SM_BTAG_EFFICIENCY_PROFILE, era, sample, scopes, shifts,
        available_sample_types, available_eras, available_scopes,
    )
