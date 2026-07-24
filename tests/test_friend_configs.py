"""Tests for the shared FastMTT friend-tree builder (`fastmtt_common.py`)
and its thin entry points (`nmssm_fastmtt.py`, `sm_fastmtt.py`).

Covers: both entries import and expose FriendTreeConfiguration (the marker
generate_friends.py dispatches on); both delegate to fastmtt_common instead
of redefining the producer/output wiring; the SM entry's 2018-only era
surface is enforced by two independent gates; and a minimal end-to-end
build proves the moved-verbatim body still produces the unchanged FastMTT
outputs.
"""
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from analysis_configurations.bbtautau import (
    fastmtt_common,
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

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
QUANTITIES_MAP = str(Path(__file__).resolve().parent / "fixtures" / "fastmtt_quantities_map.json")
QUANTITIES_MAP_KINFIT = str(
    Path(__file__).resolve().parent / "fixtures" / "kinfit_quantities_map.json"
)


class FastMTTEntryPointImportTest(unittest.TestCase):
    """Both thin entries import cleanly and expose FriendTreeConfiguration,
    the marker generate_friends.run() looks for (via inspect.getmembers) to
    dispatch a config module to the friend-tree code path.
    """

    def test_nmssm_fastmtt_exposes_friendtreeconfiguration(self):
        members = [x[0] for x in inspect.getmembers(nmssm_fastmtt, inspect.isclass)]
        self.assertIn("FriendTreeConfiguration", members)
        self.assertNotIn("Configuration", members)

    def test_sm_fastmtt_exposes_friendtreeconfiguration(self):
        members = [x[0] for x in inspect.getmembers(sm_fastmtt, inspect.isclass)]
        self.assertIn("FriendTreeConfiguration", members)
        self.assertNotIn("Configuration", members)


class FastMTTDelegationTest(unittest.TestCase):
    """Both thin entries delegate to fastmtt_common; neither redefines the
    FastMTT producer/output wiring itself.
    """

    def test_nmssm_fastmtt_reexports_the_shared_builder_directly(self):
        # nmssm_fastmtt.build_config IS fastmtt_common.build_fastmtt_config
        # -- the same function object, not a wrapper -- since the NMSSM
        # entry needs no extra gating.
        self.assertIs(nmssm_fastmtt.build_config, fastmtt_common.build_fastmtt_config)

    def test_sm_fastmtt_forwards_to_the_shared_builder_unchanged(self):
        # sm_fastmtt.build_config cannot be a direct re-export like the
        # NMSSM entry (it wraps the era gate below), so delegation is
        # verified by replacing fastmtt_common.build_fastmtt_config with a
        # stand-in and checking it receives exactly the arguments
        # sm_fastmtt.build_config was called with, and that its return
        # value is passed straight back through.
        sentinel = object()
        with mock.patch.object(
            fastmtt_common, "build_fastmtt_config", return_value=sentinel
        ) as mocked:
            result = sm_fastmtt.build_config(
                "2018", "ttbar", ["mt"], {"none"},
                LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES, "some_map.json",
            )
        mocked.assert_called_once_with(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES, "some_map.json",
        )
        self.assertIs(result, sentinel)

    def test_thin_entries_contain_no_producer_wiring(self):
        # Source-level guard: neither thin file may reference the FastMTT
        # producer module or its outputs directly -- that wiring lives
        # exclusively in fastmtt_common.py now.
        for module_name in ("nmssm_fastmtt", "sm_fastmtt"):
            text = (ANALYSIS_ROOT / f"{module_name}.py").read_text()
            self.assertNotIn("pairquantities", text, module_name)
            self.assertNotIn("FastMTTQuantities", text, module_name)
            self.assertIn("fastmtt_common", text, module_name)


class SMFastMTTEraGateTest(unittest.TestCase):
    """The SM friend build surface is 2018-only, enforced by two
    independent gates (see the sm_fastmtt.py module docstring): the
    generate-time AVAILABLE_ERAS gate in generate_friends.py, and an
    explicit check as the first statement of sm_fastmtt.build_config.
    """

    def test_module_level_gate_lists_2018_only(self):
        self.assertEqual(sm_fastmtt.AVAILABLE_ERAS, ["2018"])

    def test_build_config_rejects_era_2024(self):
        # The gate is the first statement in build_config, so it fires
        # before quantities_map is ever touched -- no fixture required,
        # and quantities_map=None is safe to pass here.
        with self.assertRaisesRegex(ValueError, "2018"):
            sm_fastmtt.build_config(
                "2024", "ttbar", ["mt"], {"none"},
                LEGACY_AVAILABLE_SAMPLES, ["2024"], SCOPES, None,
            )

    def test_generate_friends_level_gate_fires_before_build_config(self):
        # Mirrors GenerateLevelGateTest in test_generator_interface.py: the
        # generate_friends.run() gate (module-level AVAILABLE_ERAS, checked
        # before build_config is invoked) is independent of the gate inside
        # build_config exercised above.
        class _FakeArgs:
            config = "sm_fastmtt"
            era = "2024"
            sample = "ttbar"
            scopes = ["mt"]
            shifts = ["none"]
            logger = mock.Mock()

        with mock.patch.object(
            sm_fastmtt, "build_config",
            side_effect=AssertionError("must not be called"),
        ):
            with self.assertRaisesRegex(ValueError, "2024"):
                generate_friends.run(_FakeArgs())


class FastMTTFullBuildTest(unittest.TestCase):
    """A minimal end-to-end build for both entries against a synthetic
    quantities-map fixture, proving the moved-verbatim body still produces
    the unchanged FastMTT outputs (not just the delegation plumbing above).
    """

    @staticmethod
    def _output_names(config, scope):
        return {q.get_leaf(shift="", scope=scope) for q in config.outputs[scope]}

    def test_nmssm_fastmtt_full_build_outputs_are_unchanged(self):
        config = nmssm_fastmtt.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES, QUANTITIES_MAP,
        )
        self.assertEqual(
            self._output_names(config, "mt"),
            {"m_fastmtt", "pt_fastmtt", "eta_fastmtt", "phi_fastmtt"},
        )

    def test_sm_fastmtt_full_build_matches_nmssm_fastmtt(self):
        config = sm_fastmtt.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES, QUANTITIES_MAP,
        )
        self.assertEqual(
            self._output_names(config, "mt"),
            {"m_fastmtt", "pt_fastmtt", "eta_fastmtt", "phi_fastmtt"},
        )


class SMKinFitResolvedConfigTest(unittest.TestCase):
    """The SM fixed-mass (125/125) HH kinematic-fit friend
    (`sm_kinfit_resolved.py`) reuses the same vendored fit engine as the
    NMSSM kinematic fit, but exposes ONLY the four SM-named outputs (no
    mX/mY, no YToBB/YToTauTau split, no boosted variant), and its friend
    build surface is 2018-only.
    """

    @staticmethod
    def _output_names(config, scope):
        return {q.get_leaf(shift="", scope=scope) for q in config.outputs[scope]}

    def test_exposes_friendtreeconfiguration(self):
        # The marker generate_friends.run() dispatches on.
        members = [
            x[0] for x in inspect.getmembers(sm_kinfit_resolved, inspect.isclass)
        ]
        self.assertIn("FriendTreeConfiguration", members)
        self.assertNotIn("Configuration", members)

    def test_module_level_gate_lists_2018_only(self):
        self.assertEqual(sm_kinfit_resolved.AVAILABLE_ERAS, ["2018"])

    def test_build_config_rejects_era_2024(self):
        # The gate is the first statement in build_config, so it fires before
        # quantities_map is ever touched -- quantities_map=None is safe here.
        with self.assertRaisesRegex(ValueError, "2018"):
            sm_kinfit_resolved.build_config(
                "2024", "ttbar", ["mt"], {"none"},
                LEGACY_AVAILABLE_SAMPLES, ["2024"], SCOPES, None,
            )

    def test_output_set_is_exactly_the_four_sm_outputs(self):
        config = sm_kinfit_resolved.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES, QUANTITIES_MAP_KINFIT,
        )
        self.assertEqual(
            self._output_names(config, "mt"),
            {"kinfit_convergence", "kinfit_chi2", "kinfit_prob", "kinfit_mHH"},
        )

    def test_generated_outputs_have_no_nmssm_only_substrings(self):
        config = sm_kinfit_resolved.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES, QUANTITIES_MAP_KINFIT,
        )
        names = self._output_names(config, "mt")
        for forbidden in ("mX", "mY", "YToBB", "YToTauTau", "boosted"):
            for name in names:
                self.assertNotIn(forbidden, name, f"{forbidden} in {name}")


class NMSSMKinFitResolvedUnchangedTest(unittest.TestCase):
    """Guard that adding the SM kinematic-fit friend did not disturb the
    NMSSM kinematic-fit friend (`nmssm_kinfit_resolved.py`): it still imports,
    still exposes FriendTreeConfiguration, and still produces its full,
    unchanged set of YToBB / YToTauTau / best-hypothesis outputs.
    """

    @staticmethod
    def _output_names(config, scope):
        return {q.get_leaf(shift="", scope=scope) for q in config.outputs[scope]}

    def test_exposes_friendtreeconfiguration(self):
        members = [
            x[0] for x in inspect.getmembers(nmssm_kinfit_resolved, inspect.isclass)
        ]
        self.assertIn("FriendTreeConfiguration", members)
        self.assertNotIn("Configuration", members)

    def test_output_set_is_unchanged(self):
        config = nmssm_kinfit_resolved.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES, QUANTITIES_MAP_KINFIT,
        )
        self.assertEqual(
            self._output_names(config, "mt"),
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


class SMMLGateTest(unittest.TestCase):
    """The gated SM (non-resonant) ML friend stub (`sm_ml.py`, Task 22).

    Currently `payloads/ml/sm/2018/` does not exist at all, so
    `build_config` must always raise `FileNotFoundError` naming the
    activation-manifest path and the Phase-1 status -- see the module
    docstring for the full manifest schema. Only the era gate (checked
    first, matching the sm_fastmtt.py/sm_kinfit_resolved.py pattern) can
    fire before that.
    """

    def test_import_succeeds_and_exposes_friendtreeconfiguration(self):
        # The marker generate_friends.run() dispatches on (via
        # inspect.getmembers), imported cleanly with no side effects.
        members = [x[0] for x in inspect.getmembers(sm_ml, inspect.isclass)]
        self.assertIn("FriendTreeConfiguration", members)
        self.assertNotIn("Configuration", members)

    def test_module_level_gate_lists_2018_only(self):
        self.assertEqual(sm_ml.AVAILABLE_ERAS, ["2018"])

    def test_build_config_rejects_era_2024_before_manifest_check(self):
        # The era gate is the first statement in build_config -- it must
        # fire (as ValueError, NOT FileNotFoundError) before the manifest
        # is ever looked at, so this needs no fixture at all.
        with self.assertRaises(ValueError) as ctx:
            sm_ml.build_config(
                "2024", "ttbar", ["mt"], {"none"},
                LEGACY_AVAILABLE_SAMPLES, ["2024"], SCOPES, None,
            )
        self.assertNotIsInstance(ctx.exception, FileNotFoundError)
        self.assertIn("2018", str(ctx.exception))

    def test_build_config_raises_file_not_found_with_actionable_message(self):
        # payloads/ml/sm/2018/ does not exist -- the real ACTIVATION_MANIFEST
        # path is untouched, so this exercises the actual Phase-1 gate.
        with self.assertRaisesRegex(FileNotFoundError, "activation"):
            sm_ml.build_config(
                "2018", "ttbar", ["mt"], {"none"},
                LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES, None,
            )
        with self.assertRaisesRegex(FileNotFoundError, "gated"):
            sm_ml.build_config(
                "2018", "ttbar", ["mt"], {"none"},
                LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES, None,
            )

    def test_source_contains_no_forbidden_tokens(self):
        # Source-level guard: no resonance-mass conditioning, no boosted
        # (fatjet) inputs, no reference to the other analysis's ML payload
        # path -- SM ML is non-resonant and currently resolved-only.
        text = (ANALYSIS_ROOT / "sm_ml.py").read_text()
        for forbidden in ("massX", "massY", "fatjet", "pnn_mass", "nmssm"):
            self.assertNotIn(forbidden, text, forbidden)

    def test_synthetic_complete_manifest_proceeds_past_the_gate(self):
        # A self-contained synthetic manifest + dummy model/transformation
        # files, with ACTIVATION_MANIFEST monkeypatched to point at it,
        # proves the gate itself accepts a well-formed, complete manifest:
        # build_config must get PAST the FileNotFoundError gate. What
        # happens next is honest, pinned, and documented in sm_ml.py's
        # module docstring: no SM ONNX inference producer is implemented
        # yet, so build_config raises NotImplementedError (or, on an
        # interpreter without PyYAML, ImportError while parsing the
        # manifest) -- either way, NOT the Phase-1 FileNotFoundError gate.
        payload_dir = tempfile.mkdtemp(prefix="sm_ml_gate_")
        model_file = "mt_model.onnx"
        transformation_file = "mt_transform.json"
        (Path(payload_dir) / model_file).write_bytes(b"dummy-onnx-bytes")
        (Path(payload_dir) / transformation_file).write_text("{}")
        manifest_path = Path(payload_dir) / "activation.yaml"
        manifest_path.write_text(
            "channels:\n"
            "  mt:\n"
            f"    model_file: {model_file}\n"
            f"    transformation_file: {transformation_file}\n"
            "    fold_count: 2\n"
            '    event_to_fold_rule: "event % fold_count"\n'
        )

        with mock.patch.object(sm_ml, "ACTIVATION_MANIFEST", str(manifest_path)):
            with self.assertRaises(Exception) as ctx:
                sm_ml.build_config(
                    "2018", "ttbar", ["mt"], {"none"},
                    LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES, None,
                )

        self.assertNotIsInstance(ctx.exception, FileNotFoundError)
        self.assertIsInstance(ctx.exception, (NotImplementedError, ImportError))


if __name__ == "__main__":
    unittest.main()
