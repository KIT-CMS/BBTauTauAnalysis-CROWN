"""NMSSM X -> YH -> bbtautau entry point (thin wrapper, unchanged physics)."""
from code_generation.configuration import Configuration  # noqa: F401  (build-type dispatch)

from .analysis_profiles import NMSSM_PROFILE
from . import common_config


def build_config(era, sample, scopes, shifts, available_sample_types,
                 available_eras, available_scopes):
    return common_config.build_config(
        NMSSM_PROFILE, era, sample, scopes, shifts,
        available_sample_types, available_eras, available_scopes,
    )
