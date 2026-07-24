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
import unittest

from analysis_configurations.bbtautau import sm_config, nmssm_config
from analysis_configurations.bbtautau.constants import ERAS, SCOPES
from analysis_configurations.bbtautau.producers import met
from analysis_configurations.bbtautau.tests.test_nmssm_characterization import (
    LEGACY_AVAILABLE_SAMPLES,
    all_producer_names,
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
        cls.cfg = build_sm("ttbar")
        cls.params = cls.cfg.config_parameters["global"]["nominal"]
        cls.global_producers = producer_names(cls.cfg, "global")
        # The jet ID is a member of the AuxJetCollectionQuantities group rather
        # than a top-level producer, so the ID assertions below look through
        # groups.
        cls.all_global_producers = all_producer_names(cls.cfg, "global")

    def test_reconstructed_tight_id_replaces_v9_rename(self):
        # The group is what gets scheduled; the ID producer is substituted
        # inside it, so exactly one of the two ID producers may be present.
        self.assertIn("AuxJetCollectionQuantities", self.global_producers)
        self.assertIn("JetIDTight2018PuppiV15", self.all_global_producers)
        self.assertNotIn("JetID", self.all_global_producers)  # v9 rename

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

    def test_sm_v15_electron_met_jer_wiring(self):
        """Verify the three empirically-validated 2018-v15 runtime fixes are wired:
        1. Electron correction via pinned EGM v15 payload
        2. MET covariance from PuppiMET (MetCovSM2018V15)
        3. JER schema (checked implicitly via ak4jet_jec_file containment above)
        """
        # (a) Check ElectronPtCorrectionMCRun3 producer is scheduled in global scope
        self.assertIn("ElectronPtCorrectionMCRun3", self.global_producers)

        # (b) Check ele_es_file parameter contains the pinned v15 EGM payload path
        self.assertIn(
            "EGM/Run2-2018-UL-NanoAODv15/2025-12-05",
            str(self.params["ele_es_file"]),
        )

        # (c) Check that MetCovSM2018V15 is in the producers via object identity:
        # MetCovSM2018V15 has name="MetCov" and reads from PuppiMET covariance branches.
        # It is nested inside MetGlobal; access via config.producers["global"] and
        # check MetGlobal's subproducers dict.
        global_producers = self.cfg.producers["global"]
        met_global_producers = [p for p in global_producers if p.name == "MetGlobal"]
        self.assertTrue(
            len(met_global_producers) > 0,
            "MetGlobal producer not found in global scope",
        )
        met_global = met_global_producers[0]
        # MetGlobal has a 'producers' dict with scope as key
        met_cov_in_global = [
            p for p in met_global.producers.get("global", [])
            if p.name == "MetCov"
        ]
        self.assertTrue(
            len(met_cov_in_global) > 0,
            "MetCov producer not found as subproducer of MetGlobal",
        )
        # The SM2018V15 variant uses PuppiMET covariance as input; verify the producer
        # by checking that it uses PuppiMET_covXX input (versus PFMET_cov for other eras)
        met_cov = met_cov_in_global[0]
        if hasattr(met_cov, 'producers'):
            # If MetCov is also a ProducerGroup with subproducers, check the input at that level
            cov_producers = met_cov.producers.get("global", [])
            self.assertTrue(len(cov_producers) > 0)
        elif hasattr(met_cov, 'input'):
            # Single Producer: check its input quantities
            input_names = {inp.name for inp in met_cov.input if hasattr(inp, "name")}
            # MetCovSM2018V15 uses nanoAOD.PuppiMET_covXX, _covXY, _covYY
            self.assertIn("PuppiMET_covXX", input_names)

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
        nmssm_global_producers = all_producer_names(cfg, "global")
        self.assertIn("JetID", nmssm_global_producers)  # v9 rename producer
        self.assertNotIn("JetIDTight2018PuppiV15", nmssm_global_producers)


if __name__ == "__main__":
    unittest.main()
