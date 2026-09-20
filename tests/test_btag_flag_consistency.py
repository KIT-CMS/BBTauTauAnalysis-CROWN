"""Cross-parameter consistency of the ``jets.JetIsBTagged`` flag, per era and profile.

``IsBTagged(Jet_bTagValue, {bjet_sf_file}, {bjet_sf_wp_name}, {bjet_btag_wp_name})``
thresholds a rename of ``{bjet_score_column}``, so four independent parameters must
agree and nothing in the framework checks that they do. A placeholder or a wrong
correction name throws loudly in correctionlib, but a working point taken from a
*different tagger* than the discriminant silently mis-flags jets; both have happened.
"""

import gzip
import json

import pytest

from analysis_configurations.bbtautau import btag_payloads
from analysis_configurations.bbtautau.constants import ERAS
from analysis_configurations.bbtautau.tests.helpers import build

# Discriminant column -> the prefix its working-point-values correction must carry.
TAGGER_BY_SCORE_COLUMN = {
    "Jet_btagDeepFlavB": "deepJet",
    "Jet_btagPNetB": "particleNet",
    "Jet_btagUParTAK4B": "UParTAK4",
}
PARAMETERS = (
    "bjet_score_column",
    "bjet_min_score",
    "bjet_sf_file",
    "bjet_sf_wp_name",
    "bjet_btag_wp_name",
)
# Every entry point over the eras it supports; nmssm_config accepts all of them.
CASES = [("nmssm_config", era) for era in ERAS] + [
    ("sm_config", "2018"),
    ("sm_btag_efficiency_config", "2018"),
]


def working_points(payload_path, correction_name):
    """``key`` -> threshold of a ``*_wp_values`` correction in a BTV payload."""
    if correction_name == btag_payloads.WP_VALUES_CORRECTION:
        return btag_payloads.load_upart_wps(payload_path)
    with gzip.open(payload_path, "rt") as handle:
        corrections = {c["name"]: c for c in json.load(handle)["corrections"]}
    return {
        item["key"]: item["value"]
        for item in corrections[correction_name]["data"]["content"]
    }


@pytest.mark.parametrize("module,era", CASES)
def test_btag_flag_parameters_are_consistent(module, era):
    nominal = build(module, "ttbar", era=era).config_parameters["global"]["nominal"]
    params = {key: nominal.get(key) for key in PARAMETERS}
    for key, value in params.items():
        assert value not in (
            "TO_ADD",
            "DOES_NOT_EXIST",
            None,
        ), f"{key} is unset for {module}/{era}"
    tagger = TAGGER_BY_SCORE_COLUMN[params["bjet_score_column"]]
    assert params["bjet_sf_wp_name"].startswith(
        tagger
    ), f"{module}/{era}: discriminant {params['bjet_score_column']} is thresholded with {params['bjet_sf_wp_name']}"
    wps = working_points(params["bjet_sf_file"], params["bjet_sf_wp_name"])
    assert wps[params["bjet_btag_wp_name"]] == pytest.approx(
        params["bjet_min_score"], abs=1e-6
    )
