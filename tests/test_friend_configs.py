"""Friend-tree entry points: dispatch marker, gates, and output contracts.

The SM friend entries (`sm_fastmtt.py`, `sm_kinfit_resolved.py`, `sm_ml.py`) are
thin wrappers around bodies shared with their NMSSM counterparts, so the two
things worth testing are the surfaces where a mistake is silent:

* ``FriendTreeConfiguration`` must be importable from every entry module --
  it is the marker ``generate_friends.run()`` dispatches on via
  ``inspect.getmembers``, and in ``nmssm_fastmtt.py`` it is otherwise-unused
  (``# noqa: F401``) code an automated import cleanup would happily delete;
* the era gate must fire inside ``generate_friends.run()`` -- i.e. from the
  module-level ``AVAILABLE_ERAS`` attribute, before ``build_config`` is called
  at all -- and ``sm_ml.py`` must stay gated shut while its payload directory
  does not exist;
* the emitted output leaves are the friend tree's entire interface. SM and
  NMSSM kinematic fits live in the same ``producers/hhkinfit.py`` and share
  three output ``Quantity`` objects, so an edit for the SM friend can silently
  rename or drop NMSSM branches.
"""
import inspect
import unittest
from pathlib import Path
from unittest import mock

from analysis_configurations.bbtautau import (
    generate_friends,
    nmssm_fastmtt,
    nmssm_kinfit_resolved,
    sm_fastmtt,
    sm_kinfit_resolved,
    sm_ml,
)
from analysis_configurations.bbtautau.constants import (
    ERAS,
    LEGACY_AVAILABLE_SAMPLES,
    SCOPES,
)
from analysis_configurations.bbtautau.tests.helpers import output_names

FIXTURES = Path(__file__).resolve().parent / "fixtures"
QUANTITIES_MAP_FASTMTT = str(FIXTURES / "fastmtt_quantities_map.json")
QUANTITIES_MAP_KINFIT = str(FIXTURES / "kinfit_quantities_map.json")

ENTRY_MODULES = (
    nmssm_fastmtt,
    sm_fastmtt,
    sm_kinfit_resolved,
    nmssm_kinfit_resolved,
    sm_ml,
)
SM_GATED_MODULES = ("sm_fastmtt", "sm_kinfit_resolved", "sm_ml")


class _FakeArgs:
    """The attribute surface ``generate_friends.run()`` reads before its gates."""

    def __init__(self, config, era):
        self.config = config
        self.era = era
        self.sample = "ttbar"
        self.scopes = ["mt"]
        self.shifts = ["none"]
        self.quantities_map = None
        self.logger = mock.Mock()


class FriendEntryPointTest(unittest.TestCase):
    def test_friend_entry_points_expose_friendtreeconfiguration(self):
        for module in ENTRY_MODULES:
            with self.subTest(module=module.__name__):
                members = [x[0] for x in inspect.getmembers(module, inspect.isclass)]
                self.assertIn("FriendTreeConfiguration", members)
                # Both markers present would make generate_friends.run() raise.
                self.assertNotIn("Configuration", members)

    def test_sm_friend_era_gates_fire_before_build_config(self):
        for name in SM_GATED_MODULES:
            module = globals()[name]
            with self.subTest(module=name):
                # (a) the gate is the first statement of build_config, so it
                # fires before quantities_map is ever touched.
                with self.assertRaisesRegex(ValueError, "2018"):
                    module.build_config(
                        "2024", "ttbar", ["mt"], {"none"},
                        LEGACY_AVAILABLE_SAMPLES, ["2024"], SCOPES, None,
                    )
                # (b) the independent generate_friends.run() gate, which reads
                # the module-level AVAILABLE_ERAS before dispatching at all.
                with mock.patch.object(
                    module, "build_config",
                    side_effect=AssertionError("must not be called"),
                ):
                    with self.assertRaisesRegex(ValueError, "2024"):
                        generate_friends.run(_FakeArgs(name, "2024"))

    def test_sm_ml_stays_gated_until_its_payload_is_installed(self):
        # payloads/ml/sm/2018/ does not exist, so the activation manifest is
        # missing and every 2018 build must refuse with an actionable error.
        with self.assertRaises(FileNotFoundError):
            sm_ml.build_config(
                "2018", "ttbar", ["mt"], {"none"},
                LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES, None,
            )


class FriendOutputContractTest(unittest.TestCase):
    def test_fastmtt_output_contract(self):
        # Both entries reach the one shared builder in fastmtt_common.py; the
        # SM entry cannot produce these four leaves unless its forwarding is
        # correct.
        expected = {"m_fastmtt", "pt_fastmtt", "eta_fastmtt", "phi_fastmtt"}
        for module in (nmssm_fastmtt, sm_fastmtt):
            with self.subTest(module=module.__name__):
                config = module.build_config(
                    "2018", "ttbar", ["mt"], {"none"},
                    LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES,
                    QUANTITIES_MAP_FASTMTT,
                )
                self.assertEqual(output_names(config, "mt"), expected)

    def test_kinfit_output_contracts(self):
        # The SM fixed-mass (125/125) fit exposes ONLY four leaves -- no mX/mY,
        # no YToBB/YToTauTau split -- while the NMSSM fit must keep all 18.
        sm = sm_kinfit_resolved.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES, QUANTITIES_MAP_KINFIT,
        )
        self.assertEqual(
            output_names(sm, "mt"),
            {"kinfit_convergence", "kinfit_chi2", "kinfit_prob", "kinfit_mHH"},
        )

        nmssm = nmssm_kinfit_resolved.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES, QUANTITIES_MAP_KINFIT,
        )
        self.assertEqual(
            output_names(nmssm, "mt"),
            {
                "kinfit_convergence_YToBB", "kinfit_mX_YToBB", "kinfit_mY_YToBB",
                "kinfit_mh_YToBB", "kinfit_chi2_YToBB", "kinfit_prob_YToBB",
                "kinfit_convergence_YToTauTau", "kinfit_mX_YToTauTau",
                "kinfit_mY_YToTauTau", "kinfit_mh_YToTauTau",
                "kinfit_chi2_YToTauTau", "kinfit_prob_YToTauTau",
                "kinfit_convergence", "kinfit_mX", "kinfit_mY", "kinfit_mh",
                "kinfit_chi2", "kinfit_prob",
            },
        )


if __name__ == "__main__":
    unittest.main()
