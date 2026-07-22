"""SM HH -> bbtautau b-tagging efficiency ntuple entry point (2018, MC only).

Thin wrapper; the MC-only / probe-jet-collection behavior is filled in by a
later task behind the SM_BTAG_EFFICIENCY_PROFILE switches. In this task only
the era / mc_only gates at the top of common_config.build_config act on it.
"""
from code_generation.configuration import Configuration  # noqa: F401  (build-type dispatch)

from .analysis_profiles import SM_BTAG_EFFICIENCY_PROFILE
from . import common_config

AVAILABLE_ERAS = ["2018"]
DEFAULT_SAMPLES = [
    "hh2b2tau", "dyjets", "wjets", "ttbar", "singletop", "diboson",
    "electroweak_boson", "ggh_htautau", "vbf_htautau", "vbf_hbb", "rem_hbb",
    "rem_higgs", "rem_ttbar",
]
AVAILABLE_SAMPLES = list(DEFAULT_SAMPLES)


def build_config(era, sample, scopes, shifts, available_sample_types,
                 available_eras, available_scopes):
    return common_config.build_config(
        SM_BTAG_EFFICIENCY_PROFILE, era, sample, scopes, shifts,
        available_sample_types, available_eras, available_scopes,
    )
