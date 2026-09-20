from code_generation.configuration import Configuration

from .analysis_profiles import NMSSM_PROFILE
from . import common_config

### Entry point for NMSSM Analysis
def build_config(era, sample, scopes, shifts, available_sample_types,
                 available_eras, available_scopes):
    return common_config.build_config(
        NMSSM_PROFILE, era, sample, scopes, shifts,
        available_sample_types, available_eras, available_scopes,
    )
