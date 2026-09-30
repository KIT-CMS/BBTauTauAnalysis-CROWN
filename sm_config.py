from code_generation.configuration import Configuration

from .analysis_profiles import SM_PROFILE
from . import common_config

AVAILABLE_ERAS = ["2018"]
# embedding: et, mt and tt only, see embedding_run2_v15.py and the README
# section "Tau embedding"
AVAILABLE_SAMPLES = [
    "hh2b2tau", "data", "dyjets", "wjets", "ttbar", "singletop", "diboson",
    "electroweak_boson", "ggh_htautau", "vbf_htautau", "vbf_hbb", "rem_hbb",
    "rem_higgs", "rem_ttbar", "embedding",
]

# Entry point for SM Analysis
def build_config(era, sample, scopes, shifts, available_sample_types,
                 available_eras, available_scopes):
    return common_config.build_config(
        SM_PROFILE, era, sample, scopes, shifts,
        available_sample_types, available_eras, available_scopes,
    )
