import unittest

from analysis_configurations.bbtautau.analysis_profiles import (
    NMSSM_PROFILE, SM_PROFILE, SM_BTAG_EFFICIENCY_PROFILE,
)


class AnalysisProfileTest(unittest.TestCase):
    def test_profiles_are_immutable(self):
        with self.assertRaises(Exception):
            SM_PROFILE.name = "other"

    def test_sm_profiles_are_2018_only(self):
        self.assertEqual(SM_PROFILE.allowed_eras, ("2018",))
        self.assertEqual(SM_BTAG_EFFICIENCY_PROFILE.allowed_eras, ("2018",))
        self.assertIsNone(NMSSM_PROFILE.allowed_eras)

    def test_truth_mothers(self):
        self.assertEqual(SM_PROFILE.bb_truegen_mother_pdgid, {"hh2b2tau": 25})
        self.assertEqual(SM_PROFILE.tautau_truegen_mother_pdgid, {"hh2b2tau": 25})
        self.assertEqual(NMSSM_PROFILE.bb_truegen_mother_pdgid["nmssm_Ybb"], 35)

    def test_sm_keeps_standard_lhe_for_hh2b2tau(self):
        self.assertNotIn("hh2b2tau", SM_PROFILE.lhe_scale_weight_excluded_samples)
        self.assertIn("hh2b2tau", NMSSM_PROFILE.lhe_scale_weight_excluded_samples)
        self.assertEqual(SM_PROFILE.nmssm_lhe_scale_weight_samples, ())

    def test_efficiency_profile_is_payload_independent_mc_only(self):
        p = SM_BTAG_EFFICIENCY_PROFILE
        self.assertTrue(p.mc_only and p.enable_probe_jet_collection)
        self.assertFalse(p.enable_btag_sf)


if __name__ == "__main__":
    unittest.main()
