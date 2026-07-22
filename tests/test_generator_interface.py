"""Tests for the generator interface: config-specific sample/era surfaces
resolved and enforced by generate.py (and generate_friends.py) BEFORE
build_config is ever invoked, plus the -DSAMPLES=all cmake expansion helper.
"""
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from analysis_configurations.bbtautau import generate, sm_config, nmssm_config
from analysis_configurations.bbtautau.constants import LEGACY_AVAILABLE_SAMPLES

CROWN_ROOT = Path(__file__).resolve().parents[3]


class GeneratorInterfaceTest(unittest.TestCase):
    def test_nmssm_falls_back_to_legacy_list(self):
        avail, default = generate.resolve_sample_surface(nmssm_config)
        self.assertEqual(avail, LEGACY_AVAILABLE_SAMPLES)
        self.assertEqual(default, LEGACY_AVAILABLE_SAMPLES)

    def test_sm_surface_includes_signal_and_excludes_forbidden(self):
        avail, default = generate.resolve_sample_surface(sm_config)
        self.assertIn("hh2b2tau", default)
        for forbidden in ("nmssm_Ybb", "nmssm_Ytautau", "ggZZ", "triboson"):
            self.assertNotIn(forbidden, avail)
        for commissioning_only in ("embedding", "embedding_mc"):
            self.assertIn(commissioning_only, avail)
            self.assertNotIn(commissioning_only, default)

    def test_sm_era_gate_fires_before_sample_expansion(self):
        # 2024 samples=all through an SM entry point must never reach NMSSM signals.
        with self.assertRaisesRegex(ValueError, "2018"):
            sm_config.build_config(
                "2024", "nmssm_Ybb", ["mt"], {"none"},
                LEGACY_AVAILABLE_SAMPLES, ["2024"], ["mt"],
            )

    def test_cmake_all_expansion_helper(self):
        out = subprocess.check_output(
            [sys.executable, str(CROWN_ROOT / "code_generation" / "expand_samples.py"),
             "--analysis", "bbtautau", "--config", "sm_config"],
            cwd=CROWN_ROOT, text=True, stderr=subprocess.DEVNULL,
        ).strip()
        self.assertEqual(out.split(","), sm_config.DEFAULT_SAMPLES)

    def test_cmake_all_expansion_errors_for_legacy_config(self):
        proc = subprocess.run(
            [sys.executable, str(CROWN_ROOT / "code_generation" / "expand_samples.py"),
             "--analysis", "bbtautau", "--config", "nmssm_config"],
            cwd=CROWN_ROOT, capture_output=True, text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("nmssm_config", proc.stderr)
        self.assertIn("SAMPLES=all is not supported", proc.stderr)

    def test_build_scripts_accept_optional_config_argument(self):
        for script in (CROWN_ROOT / "analysis_configurations/bbtautau/build_scripts").glob("test_build_*.sh"):
            text = script.read_text()
            self.assertIn('local config="${5:-nmssm_config}"', text, script.name)
            self.assertNotIn('local config="nmssm_config"', text, script.name)
            self.assertIn('$( [[ "${config}" != "nmssm_config" ]] && echo "_${config}" )', text, script.name)
            self.assertLess(text.index('local config="${5:-nmssm_config}"'), text.index('local crown_build_dir='), script.name)


class GenerateLevelGateTest(unittest.TestCase):
    """Exercises the SECOND, independent era/sample gate: the one inside
    generate.run() itself, which must fire before config.build_config() is
    ever called -- not just the profile gate inside common_config.build_config
    that test_sm_era_gate_fires_before_sample_expansion above already covers.
    """

    class _FakeArgs:
        config = "sm_config"
        era = "2024"
        sample = "hh2b2tau"
        scopes = ["mt"]
        shifts = ["none"]

    def test_generate_level_era_gate_fires_before_build_config_is_called(self):
        with mock.patch.object(
            sm_config, "build_config",
            side_effect=AssertionError("must not be called"),
        ):
            with self.assertRaisesRegex(ValueError, "2024"):
                generate.run(self._FakeArgs())

    def test_generate_level_sample_gate_fires_before_build_config_is_called(self):
        args = self._FakeArgs()
        args.era = "2018"
        args.sample = "nmssm_Ybb"  # not in sm_config's AVAILABLE_SAMPLES
        with mock.patch.object(
            sm_config, "build_config",
            side_effect=AssertionError("must not be called"),
        ):
            with self.assertRaisesRegex(ValueError, "nmssm_Ybb"):
                generate.run(args)


if __name__ == "__main__":
    unittest.main()
