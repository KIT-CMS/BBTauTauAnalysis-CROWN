"""Cross-parameter consistency of the ``jets.JetIsBTagged`` flag, per era and profile.

``IsBTagged(Jet_bTagValue, {bjet_sf_file}, {bjet_sf_wp_name}, {bjet_btag_wp_name})``
thresholds a rename of ``{bjet_score_column}``, so four independent parameters must
agree and nothing in the framework checks that they do. A placeholder or a wrong
correction name throws loudly in correctionlib, but a working point taken from a
*different tagger* than the discriminant silently mis-flags jets; both have happened.
"""
import gzip
import json
import unittest

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
    "bjet_score_column", "bjet_min_score", "bjet_sf_file",
    "bjet_sf_wp_name", "bjet_btag_wp_name",
)

# Every entry point over the eras it supports; nmssm_config defines no
# AVAILABLE_ERAS and therefore accepts all of them.
CASES = tuple(("nmssm_config", era) for era in ERAS) + (
    ("sm_config", "2018"), ("sm_btag_efficiency_config", "2018"),
)


def working_points(payload_path, correction_name):
    """``key`` -> threshold of a ``*_wp_values`` correction in a BTV payload."""
    if correction_name == btag_payloads.WP_VALUES_CORRECTION:
        return btag_payloads.load_upart_wps(payload_path)
    with gzip.open(payload_path, "rt") as handle:
        corrections = {c["name"]: c for c in json.load(handle)["corrections"]}
    content = corrections[correction_name]["data"]["content"]
    return {item["key"]: item["value"] for item in content}


class BtagFlagConsistencyTest(unittest.TestCase):
    def test_btag_flag_parameters_are_consistent(self):
        for module_name, era in CASES:
            with self.subTest(module=module_name, era=era):
                nominal = build(module_name, "ttbar", era=era).config_parameters[
                    "global"
                ]["nominal"]
                params = {key: nominal.get(key) for key in PARAMETERS}
                case = f"{module_name}/{era}"
                for key, value in params.items():
                    self.assertNotIn(
                        value, ("TO_ADD", "DOES_NOT_EXIST", None),
                        f"{key} is unset/placeholder for {case}",
                    )
                tagger = TAGGER_BY_SCORE_COLUMN.get(params["bjet_score_column"])
                self.assertIsNotNone(
                    tagger, f"unknown b-tag discriminant {params['bjet_score_column']}"
                )
                self.assertTrue(
                    params["bjet_sf_wp_name"].startswith(tagger),
                    f"{case}: discriminant {params['bjet_score_column']} ({tagger}) "
                    f"is thresholded with {params['bjet_sf_wp_name']}",
                )
                wps = working_points(params["bjet_sf_file"], params["bjet_sf_wp_name"])
                self.assertAlmostEqual(
                    wps[params["bjet_btag_wp_name"]], params["bjet_min_score"], places=6,
                    msg=f"{case}: payload {params['bjet_sf_wp_name']} "
                        f"{params['bjet_btag_wp_name']} != bjet_min_score",
                )


if __name__ == "__main__":
    unittest.main()
