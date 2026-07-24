"""Cross-parameter consistency of the b-tag flag, for every profile and era.

``jets.JetIsBTagged`` runs in the ``global`` scope as a member of the auxiliary
``Jet`` quantity group -- i.e. for every profile, MC and data -- and flags a jet
by loading a working-point-values correction from a payload:

    IsBTagged(Jet_bTagValue, {bjet_sf_file}, {bjet_sf_wp_name}, {bjet_btag_wp_name})

where ``Jet_bTagValue`` is a rename of ``{bjet_score_column}``. Four independent
config parameters therefore have to agree, and nothing in the framework checks
that they do: a wrong ``bjet_sf_wp_name`` throws in correctionlib at graph
construction (loud), but a working point taken from a *different tagger* than
the discriminant column silently mis-flags jets in the gap between the two
thresholds. Both failure modes have occurred:

* ``bjet_sf_wp_name`` was left as the placeholder ``"TO_ADD"`` for eight eras;
* the working-point payload and the discriminant column were staged under
  different profile gates, so a profile got a UParT working point against a
  DeepJet discriminant.

These tests pin all three invariants: no placeholder reaches the producer, the
discriminant and the working point name the same tagger, and the working point's
threshold equals the numeric ``bjet_min_score`` staged for the same era.
"""
import gzip
import json
import logging
import os
import unittest

from analysis_configurations.bbtautau import (
    nmssm_config,
    sm_btag_efficiency_config,
    sm_config,
)
from analysis_configurations.bbtautau.constants import ERAS, SCOPES
from analysis_configurations.bbtautau.tests.test_nmssm_characterization import (
    LEGACY_AVAILABLE_SAMPLES,
)

# Discriminant column -> the tagger it belongs to, and the prefix its
# working-point-values correction must carry inside the payload.
TAGGER_BY_SCORE_COLUMN = {
    "Jet_btagDeepFlavB": "deepJet",
    "Jet_btagPNetB": "particleNet",
    "Jet_btagUParTAK4B": "UParTAK4",
}

# (label, builder) for every entry point, built for the eras it supports.
def _build_nmssm(era):
    return nmssm_config.build_config(
        era, "ttbar", ["mt"], {"none"}, LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES
    )


def _build_sm(era):
    return sm_config.build_config(
        era, "ttbar", ["mt"], {"none"}, sm_config.AVAILABLE_SAMPLES, [era], SCOPES
    )


def _build_sm_btag_efficiency(era):
    return sm_btag_efficiency_config.build_config(
        era,
        "ttbar",
        ["mt"],
        {"none"},
        sm_btag_efficiency_config.AVAILABLE_SAMPLES,
        [era],
        SCOPES,
    )


CASES = (
    [("nmssm_config", era, _build_nmssm) for era in ERAS]
    + [("sm_config", "2018", _build_sm)]
    + [("sm_btag_efficiency_config", "2018", _build_sm_btag_efficiency)]
)


def btag_parameters(config):
    params = config.config_parameters["global"]["nominal"]
    return {
        key: params.get(key)
        for key in (
            "bjet_score_column",
            "bjet_min_score",
            "bjet_sf_file",
            "bjet_sf_wp_name",
            "bjet_btag_wp_name",
        )
    }


def working_point_threshold(payload_path, correction_name, working_point):
    """Medium-etc. threshold of ``correction_name`` in a correctionlib payload.

    Returns None when the payload cannot be read (no cvmfs on this host), so the
    caller can skip rather than fail.
    """
    try:
        with gzip.open(payload_path) as payload_file:
            payload = json.load(payload_file)
    except (OSError, ValueError):
        return None
    matching = [c for c in payload["corrections"] if c["name"] == correction_name]
    if not matching:
        return None
    node = matching[0]["data"]
    while isinstance(node, dict) and node.get("nodetype") == "category":
        content = {c["key"]: c["value"] for c in node["content"]}
        if working_point in content:
            node = content[working_point]
            break
        node = next(iter(content.values()))
    return node if isinstance(node, (int, float)) else None


class BtagFlagConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # build_config is chatty; the assertions below are what matters here
        logging.disable(logging.CRITICAL)
        cls.parameters = {}
        for label, era, build in CASES:
            cls.parameters[(label, era)] = btag_parameters(build(era))

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def test_no_placeholder_reaches_the_flag_producer(self):
        for case, params in self.parameters.items():
            with self.subTest(case=case):
                for key, value in params.items():
                    self.assertNotIn(
                        value,
                        ("TO_ADD", "DOES_NOT_EXIST", None),
                        f"{key} is unset/placeholder for {case}",
                    )

    def test_discriminant_and_working_point_are_the_same_tagger(self):
        for case, params in self.parameters.items():
            with self.subTest(case=case):
                tagger = TAGGER_BY_SCORE_COLUMN.get(params["bjet_score_column"])
                self.assertIsNotNone(
                    tagger, f"unknown b-tag discriminant {params['bjet_score_column']}"
                )
                self.assertTrue(
                    params["bjet_sf_wp_name"].startswith(tagger),
                    f"{case}: discriminant {params['bjet_score_column']} ({tagger}) is "
                    f"thresholded with {params['bjet_sf_wp_name']}",
                )

    def test_working_point_threshold_matches_numeric_min_score(self):
        checked = 0
        for case, params in self.parameters.items():
            with self.subTest(case=case):
                if not os.path.exists(params["bjet_sf_file"]):
                    continue
                threshold = working_point_threshold(
                    params["bjet_sf_file"],
                    params["bjet_sf_wp_name"],
                    params["bjet_btag_wp_name"],
                )
                if threshold is None:
                    continue
                checked += 1
                self.assertAlmostEqual(
                    threshold,
                    params["bjet_min_score"],
                    places=6,
                    msg=(
                        f"{case}: payload {params['bjet_sf_wp_name']} "
                        f"{params['bjet_btag_wp_name']} = {threshold} but "
                        f"bjet_min_score = {params['bjet_min_score']}"
                    ),
                )
        if not checked:
            self.skipTest("no b-tag payload readable on this host (no cvmfs?)")


if __name__ == "__main__":
    unittest.main()
