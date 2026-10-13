"""SM tau-ID SF and ES measurement entry point (2018; mt and mm), see tau_id_measurement.py."""
from code_generation.configuration import Configuration  # noqa: F401  (build-type dispatch)

from .analysis_profiles import SM_TAU_ID_MEASUREMENT_PROFILE
from . import common_config
from .tau_id_measurement import MC_SAMPLES

AVAILABLE_ERAS = ["2018"]
AVAILABLE_SAMPLES = ["data", *MC_SAMPLES, "embedding"]


def build_config(era, sample, scopes, shifts, available_sample_types,
                 available_eras, available_scopes):
    return common_config.build_config(
        SM_TAU_ID_MEASUREMENT_PROFILE, era, sample, scopes, shifts,
        available_sample_types, available_eras, available_scopes,
    )
