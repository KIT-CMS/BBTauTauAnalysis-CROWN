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

The single test below pins all three invariants at once, per era and profile:
no placeholder reaches the producer, the discriminant and the working point name
the same tagger, and the working point's threshold in the payload equals the
numeric ``bjet_min_score`` staged for that era (which is a hand-typed literal
for the legacy eras).
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
from analysis_configurations.bbtautau.constants import (
    ERAS,
    LEGACY_AVAILABLE_SAMPLES,
    SCOPES,
)

# Discriminant column -> the prefix its working-point-values correction must
# carry inside the payload.
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

# (label, module, eras) -- every entry point, over the eras it supports.
# nmssm_config defines neither AVAILABLE_SAMPLES nor AVAILABLE_ERAS; both SM
# wrappers define both, so the getattr fallbacks below cover all three.
ENTRY_POINTS = (
    ("nmssm_config", nmssm_config, ERAS),
    ("sm_config", sm_config, sm_config.AVAILABLE_ERAS),
    (
        "sm_btag_efficiency_config",
        sm_btag_efficiency_config,
        sm_btag_efficiency_config.AVAILABLE_ERAS,
    ),
)


def btag_parameters(module, era):
    config = module.build_config(
        era,
        "ttbar",
        ["mt"],
        {"none"},
        list(getattr(module, "AVAILABLE_SAMPLES", LEGACY_AVAILABLE_SAMPLES)),
        list(getattr(module, "AVAILABLE_ERAS", ERAS)),
        SCOPES,
    )
    params = config.config_parameters["global"]["nominal"]
    return {key: params.get(key) for key in PARAMETERS}


def working_point_threshold(payload_path, correction_name, working_point):
    """Threshold of ``working_point`` in ``correction_name`` of a payload.

    Returns None when the payload or correction cannot be read (no cvmfs on
    this host), so the caller can skip rather than fail.
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
        # build_config is chatty; the assertions below are what matters here.
        logging.disable(logging.CRITICAL)
        try:
            cls.parameters = {
                (label, era): btag_parameters(module, era)
                for label, module, eras in ENTRY_POINTS
                for era in eras
            }
        finally:
            logging.disable(logging.NOTSET)

    def test_btag_flag_parameters_are_consistent(self):
        checked_thresholds = 0
        for case, params in self.parameters.items():
            with self.subTest(case=case):
                for key, value in params.items():
                    self.assertNotIn(
                        value,
                        ("TO_ADD", "DOES_NOT_EXIST", None),
                        f"{key} is unset/placeholder for {case}",
                    )

                tagger = TAGGER_BY_SCORE_COLUMN.get(params["bjet_score_column"])
                self.assertIsNotNone(
                    tagger,
                    f"unknown b-tag discriminant {params['bjet_score_column']}",
                )
                self.assertTrue(
                    params["bjet_sf_wp_name"].startswith(tagger),
                    f"{case}: discriminant {params['bjet_score_column']} "
                    f"({tagger}) is thresholded with {params['bjet_sf_wp_name']}",
                )

                if not os.path.exists(params["bjet_sf_file"]):
                    continue
                threshold = working_point_threshold(
                    params["bjet_sf_file"],
                    params["bjet_sf_wp_name"],
                    params["bjet_btag_wp_name"],
                )
                if threshold is None:
                    continue
                checked_thresholds += 1
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
        if not checked_thresholds:
            self.skipTest("no b-tag payload readable on this host (no cvmfs?)")


if __name__ == "__main__":
    unittest.main()
