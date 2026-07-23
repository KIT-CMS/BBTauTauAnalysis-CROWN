"""Config-level contract for the isolated SM 2018-v15 AK4-PUPPI jet path.

Freezes the SM-only jet wiring introduced for NanoAOD v15: the reconstructed
2018 UL PUPPI tight jet-ID producer (replacing the v9 ``Jet_jetId`` rename),
no CHS pileup-jet-ID cut, the pinned AK4PFPuppi JEC/JER payload, and the
unchanged 2018 noise policy. The NMSSM 2018 path must stay on the legacy v9
AK4-CHS wiring (proven byte-identical by the characterization suite); the last
test guards that the v9 rename producer is still selected there.

Jet config parameters are registered in the ``global`` scope, and the expanded
configuration nests parameters under a ``nominal`` shift layer, so all lookups
below go through ``config_parameters["global"]["nominal"]``.
"""
import dataclasses
import tempfile
import unittest

from analysis_configurations.bbtautau import common_config, sm_config, nmssm_config
from analysis_configurations.bbtautau.analysis_profiles import SM_PROFILE
from analysis_configurations.bbtautau.constants import ERAS, SCOPES
from analysis_configurations.bbtautau.tests.fixtures.sm_btag_efficiency_payload import (
    write_passing_payload,
)
from analysis_configurations.bbtautau.tests.test_nmssm_characterization import (
    LEGACY_AVAILABLE_SAMPLES,
    producer_names,
)


def build_sm(sample, era="2018", scopes=("mt",)):
    return sm_config.build_config(
        era,
        sample,
        list(scopes),
        {"none"},
        sm_config.AVAILABLE_SAMPLES,
        ["2018"],
        SCOPES,
    )


class SMV15JetPathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # This class exercises the SM AK4-PUPPI jet path, not b-tagging, but
        # building ANY MC sample under SM_PROFILE now also requires the
        # strict validated-payload gate (Task 11) to pass, since
        # SM_PROFILE.require_validated_btag_payload=True. build_sm() above
        # uses the real (production) SM_PROFILE unmodified -- appropriate for
        # tests that specifically want that gate to fire (see
        # test_sm_main_config.py) -- so here a synthetic, PASSING payload is
        # supplied via a profile carrying a tempdir btag_payload_dir instead,
        # built directly through common_config.build_config.
        cls._payload_dir = tempfile.mkdtemp(prefix="sm_jet_path_btag_payload_")
        write_passing_payload(cls._payload_dir, scopes=("mt",))
        profile = dataclasses.replace(SM_PROFILE, btag_payload_dir=cls._payload_dir)
        cls.cfg = common_config.build_config(
            profile, "2018", "ttbar", ["mt"], {"none"},
            sm_config.AVAILABLE_SAMPLES, ["2018"], SCOPES,
        )
        cls.params = cls.cfg.config_parameters["global"]["nominal"]
        cls.global_producers = producer_names(cls.cfg, "global")

    def test_reconstructed_tight_id_replaces_v9_rename(self):
        self.assertIn("JetIDTight2018PuppiV15", self.global_producers)
        self.assertNotIn("JetID", self.global_producers)  # v9 rename producer

    def test_no_puid_cut(self):
        self.assertEqual(self.params["ak4jet_puid_max_pt"], 0.0)
        self.assertEqual(self.params["ak4jet_id_wp"], 1)

    def test_jec_is_v15_ak4pfpuppi(self):
        self.assertIn(
            "Run2-2018-UL-NanoAODv15", str(self.params["ak4jet_jec_file"])
        )
        self.assertIn(
            "AK4PFPuppi",
            str(self.params["ak4jet_jes_tag_mc"])
            + str(self.params["ak4jet_jec_algo"]),
        )

    def test_2018_noise_policy(self):
        self.assertEqual(self.params["ak4jet_apply_jet_horn_veto"], "true")
        self.assertNotIn("JetVetoMapVeto", self.global_producers)

    def test_nmssm_2018_jet_path_unchanged(self):
        cfg = nmssm_config.build_config(
            "2018",
            "ttbar",
            ["mt"],
            {"none"},
            LEGACY_AVAILABLE_SAMPLES,
            ERAS,
            SCOPES,
        )
        self.assertIn("JetID", producer_names(cfg, "global"))


if __name__ == "__main__":
    unittest.main()
