"""Contract for scripts/export_sm_selection_contract.py.

Pins the SM selection contract exported for TauFakeFactors parity: the
per-channel trigger flags / offline pt, light-lepton and tau kinematics,
tau-ID working points, probe-jet acceptance and analysis-baseline cuts, plus
the deterministic ``contract_sha256`` (recomputed the same way on the
TauFakeFactors side). The contract is built from SM_BTAG_EFFICIENCY_PROFILE,
which carries the same object/trigger/tau definitions as SM_PROFILE but does
not apply b-tag scale factors.
"""
import unittest

from analysis_configurations.bbtautau.scripts import export_sm_selection_contract as export


class ExportSelectionContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = export.build_contract()

    def test_top_level_metadata(self):
        self.assertEqual(self.contract["era"], "2018")
        self.assertEqual(self.contract["profile"], "sm_btag_efficiency")
        self.assertEqual(self.contract["source_config"], "sm_btag_efficiency_config")
        self.assertEqual(set(self.contract["channels"]), {"et", "mt", "tt"})

    def test_et_channel_baseline(self):
        et = self.contract["channels"]["et"]
        self.assertEqual(et["trigger"]["flags"], ["trg_single_ele32"])
        self.assertEqual(et["trigger"]["lepton_min_pt"], 34.0)
        self.assertEqual(et["lepton"]["kind"], "electron")
        self.assertEqual(et["lepton"]["min_pt"], 20.0)
        self.assertEqual(et["lepton"]["max_iso"], 0.15)
        self.assertEqual(et["tau"]["decay_modes"], [0, 1, 10, 11])
        self.assertEqual(et["tau"]["vs_jet_wp"], "Medium")
        self.assertEqual(et["tau"]["vs_ele_wp"], "Tight")
        self.assertEqual(et["tau"]["vs_mu_wp"], "VLoose")
        self.assertEqual(et["transverse_mass_max"], 50.0)
        self.assertEqual(et["charge_requirement"], "opposite_sign")
        self.assertEqual(et["probe_jet"], {"min_pt": 20.0, "max_abs_eta": 2.4})
        self.assertIn("dilepton_veto", et["vetoes"])

    def test_mt_channel_baseline(self):
        mt = self.contract["channels"]["mt"]
        self.assertEqual(mt["trigger"]["flags"], ["trg_single_mu24"])
        self.assertEqual(mt["trigger"]["lepton_min_pt"], 26.0)
        self.assertEqual(mt["lepton"]["kind"], "muon")
        self.assertEqual(mt["tau"]["vs_ele_wp"], "VVLoose")
        self.assertEqual(mt["tau"]["vs_mu_wp"], "Tight")

    def test_tt_channel_baseline(self):
        tt = self.contract["channels"]["tt"]
        self.assertEqual(tt["trigger"]["flags"], ["trg_double_tau35_mediumiso"])
        self.assertEqual(tt["trigger"]["tau_min_pt"], 40.0)
        self.assertEqual(tt["tau"]["vs_ele_wp"], "VVLoose")
        self.assertEqual(tt["tau"]["vs_mu_wp"], "VLoose")
        # tau-tau carries no di-lepton veto column
        self.assertNotIn("dilepton_veto", tt["vetoes"])
        self.assertNotIn("transverse_mass_max", tt)
        self.assertNotIn("lepton", tt)

    def test_contract_sha256_is_deterministic(self):
        first = export.contract_sha256(self.contract)
        second = export.contract_sha256(export.build_contract())
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")

    def test_contract_sha256_excludes_itself(self):
        # Adding the checksum field must not change the digest (it is excluded).
        with_field = dict(self.contract)
        with_field["contract_sha256"] = "deadbeef"
        self.assertEqual(
            export.contract_sha256(with_field), export.contract_sha256(self.contract)
        )


if __name__ == "__main__":
    unittest.main()
