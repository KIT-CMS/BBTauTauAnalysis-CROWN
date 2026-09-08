"""Friend-tree entry points: dispatch marker, era gate, and output contracts.

The SM friend entries are thin re-exports of bodies shared with their NMSSM
counterparts, so what is worth testing are the surfaces where a mistake is silent:
the ``FriendTreeConfiguration`` marker ``generate_friends.run()`` dispatches on
(otherwise-unused ``# noqa: F401`` code an import cleanup would delete), the era
gate that must fire before ``build_config``, and the emitted leaves -- the friend
tree's entire interface, shared between the SM and NMSSM fits.
"""
import inspect
import unittest
from pathlib import Path
from unittest import mock

from analysis_configurations.bbtautau import (
    generate_friends, nmssm_fastmtt, nmssm_kinfit_resolved, sm_fastmtt,
    sm_kinfit_resolved,
)
from analysis_configurations.bbtautau.constants import ERAS, LEGACY_AVAILABLE_SAMPLES, SCOPES
from analysis_configurations.bbtautau.tests.helpers import FakeArgs, output_names

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MAP_FASTMTT = str(FIXTURES / "fastmtt_quantities_map.json")
MAP_KINFIT = str(FIXTURES / "kinfit_quantities_map.json")

ENTRY_MODULES = (nmssm_fastmtt, sm_fastmtt, sm_kinfit_resolved, nmssm_kinfit_resolved)
SM_GATED_MODULES = {"sm_fastmtt": sm_fastmtt, "sm_kinfit_resolved": sm_kinfit_resolved}

FASTMTT_LEAVES = {"m_fastmtt", "pt_fastmtt", "eta_fastmtt", "phi_fastmtt"}
# The SM fixed-mass (125/125) fit exposes ONLY these four -- no mX/mY, no
# YToBB/YToTauTau split -- while the NMSSM fit must keep all 18.
SM_KINFIT_LEAVES = {"kinfit_convergence", "kinfit_chi2", "kinfit_prob", "kinfit_mHH"}
NMSSM_KINFIT_LEAVES = {
    "kinfit_convergence_YToBB", "kinfit_mX_YToBB", "kinfit_mY_YToBB",
    "kinfit_mh_YToBB", "kinfit_chi2_YToBB", "kinfit_prob_YToBB",
    "kinfit_convergence_YToTauTau", "kinfit_mX_YToTauTau", "kinfit_mY_YToTauTau",
    "kinfit_mh_YToTauTau", "kinfit_chi2_YToTauTau", "kinfit_prob_YToTauTau",
    "kinfit_convergence", "kinfit_mX", "kinfit_mY", "kinfit_mh",
    "kinfit_chi2", "kinfit_prob",
}
OUTPUT_CONTRACTS = (
    (nmssm_fastmtt, MAP_FASTMTT, FASTMTT_LEAVES),
    (sm_fastmtt, MAP_FASTMTT, FASTMTT_LEAVES),
    (sm_kinfit_resolved, MAP_KINFIT, SM_KINFIT_LEAVES),
    (nmssm_kinfit_resolved, MAP_KINFIT, NMSSM_KINFIT_LEAVES),
)


class FriendEntryPointTest(unittest.TestCase):
    def test_friend_entry_points_expose_friendtreeconfiguration(self):
        for module in ENTRY_MODULES:
            with self.subTest(module=module.__name__):
                members = [x[0] for x in inspect.getmembers(module, inspect.isclass)]
                self.assertIn("FriendTreeConfiguration", members)
                # both markers present would make generate_friends.run() raise
                self.assertNotIn("Configuration", members)

    def test_sm_friend_era_gates_fire_before_build_config(self):
        for name, module in SM_GATED_MODULES.items():
            with self.subTest(module=name):
                with mock.patch.object(
                    module, "build_config",
                    side_effect=AssertionError("must not be called"),
                ):
                    with self.assertRaisesRegex(ValueError, "2024"):
                        generate_friends.run(FakeArgs(name, "2024"))

    def test_friend_output_contracts(self):
        for module, quantities_map, expected in OUTPUT_CONTRACTS:
            with self.subTest(module=module.__name__):
                config = module.build_config(
                    "2018", "ttbar", ["mt"], {"none"}, LEGACY_AVAILABLE_SAMPLES,
                    list(getattr(module, "AVAILABLE_ERAS", ERAS)), SCOPES,
                    quantities_map,
                )
                self.assertEqual(output_names(config, "mt"), expected)


if __name__ == "__main__":
    unittest.main()
