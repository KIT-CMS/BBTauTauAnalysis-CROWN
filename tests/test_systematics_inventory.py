"""Contract tests for ``systematics_sm_2018.yaml`` and its validator script.

PyYAML is not guaranteed to be present in the plain ``python3`` environment
this repository's other tests run under (see e.g.
``tests/test_branch_contract_2018_v15.py``'s uproot guard for the established
pattern). Every test in this module that needs to parse the YAML or exercise
the validator is gated behind ``@unittest.skipUnless(_HAS_YAML, ...)`` so that
a plain ``python3 -m unittest`` run of the full suite still discovers this
module and skips cleanly instead of erroring; run it with a PyYAML-capable
interpreter (e.g. ``/work/sdaigler/forge/envs/fake_factors/bin/python``) to
actually exercise it. The NMSSM-isolation grep test has no YAML dependency and
always runs.

Building the SM configuration with ``shifts={"all"}`` (needed for the
validator's shift-coverage check) takes on the order of a minute, so the two
tests that need it share one ``setUpClass`` build via the validator's own
``build_sm_registered_shifts`` helper.
"""
import unittest
from pathlib import Path

try:
    import yaml

    _HAS_YAML = True
except ImportError:  # pragma: no cover - exercised only without PyYAML
    _HAS_YAML = False

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ANALYSIS_ROOT / "systematics_sm_2018.yaml"

EXECUTION_CLASSES = {
    "nominal_column",
    "crown_shift",
    "alternative_sample",
    "downstream",
}

# Minimum-content names required by the task spec (see task-12-brief.md):
# JES/JER incl. jesUncHEMIssue, tau/ele/mu ES+resolution, MET
# unclustered/recoil, pileup, trigger, lepton/tau ID/iso, UParT fixed-WP SF,
# LHE scales/PDF/alpha-s, parton-shower TuneCP5up, lumi + statistical,
# MC-efficiency statistics + phase-space transfer.
MINIMUM_CONTENT_NAMES = {
    "jes_regrouped_sources",
    "jer_uncertainty",
    "jes_hem_issue_2018",
    "tau_energy_scale_by_decay_mode",
    "lepton_to_tau_fake_energy_scale",
    "electron_energy_scale_and_resolution",
    "muon_momentum_scale",
    "met_unclustered_energy",
    "met_recoil_response_resolution",
    "pileup_reweighting",
    "lepton_id_iso_scale_factors",
    "single_electron_trigger_sf",
    "single_muon_trigger_sf",
    "tau_id_vs_jet",
    "tau_id_vs_electron",
    "tau_id_vs_muon",
    "upart_fixed_wp_btag_sf",
    "lhe_scale_weight_nominal",
    "lhe_pdf_alphas_weights",
    "parton_shower_tune_cp5_up",
    "luminosity_2018",
    "mc_statistical_uncertainty",
    "mc_efficiency_statistics",
    "phase_space_transfer_uncertainty",
}


@unittest.skipUnless(_HAS_YAML, "PyYAML not installed in this interpreter")
class SystematicsInventoryYamlTest(unittest.TestCase):
    """Schema round-trip + minimum-content checks on the raw YAML."""

    @classmethod
    def setUpClass(cls):
        with open(YAML_PATH) as handle:
            cls.data = yaml.safe_load(handle)
        cls.entries = cls.data["systematics"]
        cls.by_name = {entry["name"]: entry for entry in cls.entries}

    def test_yaml_round_trips(self):
        self.assertIsInstance(self.entries, list)
        self.assertGreater(len(self.entries), 0)

    def test_entry_names_are_unique(self):
        names = [entry["name"] for entry in self.entries]
        self.assertEqual(len(names), len(set(names)))

    def test_all_four_execution_classes_present(self):
        classes = {entry["execution_class"] for entry in self.entries}
        self.assertEqual(classes, EXECUTION_CLASSES)

    def test_schema_fields_present_on_every_entry(self):
        required = {
            "name",
            "execution_class",
            "affected_samples",
            "affected_channels",
            "source",
            "variation_keys",
            "correlation_policy",
            "production_status",
            "final_disposition",
        }
        for entry in self.entries:
            missing = required - set(entry)
            self.assertFalse(
                missing, f"{entry.get('name')}: missing fields {missing}"
            )

    def test_production_status_is_a_valid_enum_member(self):
        allowed = {"produced", "registered_not_produced", "planned"}
        for entry in self.entries:
            self.assertIn(entry["production_status"], allowed, entry["name"])

    def test_final_disposition_is_valid(self):
        for entry in self.entries:
            fd = entry["final_disposition"]
            self.assertTrue(
                fd in ("propagate", "pending_review") or fd.startswith("excluded:"),
                f"{entry['name']}: bad final_disposition {fd!r}",
            )

    def test_minimum_content_names_present(self):
        actual = set(self.by_name)
        missing = MINIMUM_CONTENT_NAMES - actual
        self.assertFalse(missing, f"missing minimum-content entries: {missing}")

    def test_jes_hem_issue_is_crown_shift_registered_not_produced(self):
        entry = self.by_name["jes_hem_issue_2018"]
        self.assertEqual(entry["execution_class"], "crown_shift")
        self.assertEqual(entry["production_status"], "registered_not_produced")
        self.assertIn("jesUncHEMIssue", entry["shift_name_patterns"])

    def test_upart_sf_is_nominal_column_with_dynamic_variation_keys(self):
        entry = self.by_name["upart_fixed_wp_btag_sf"]
        self.assertEqual(entry["execution_class"], "nominal_column")
        self.assertEqual(entry["variation_keys"], "pinned payload (dynamic)")

    def test_lhe_weights_are_nominal_column(self):
        for name in ("lhe_scale_weight_nominal", "lhe_pdf_alphas_weights"):
            self.assertEqual(self.by_name[name]["execution_class"], "nominal_column")

    def test_parton_shower_tune_is_alternative_sample(self):
        entry = self.by_name["parton_shower_tune_cp5_up"]
        self.assertEqual(entry["execution_class"], "alternative_sample")
        self.assertIn(
            "TTTo2L2Nu_TuneCP5up_13TeV-powheg-pythia8_RunIISummer20UL18NanoAODv15-150X",
            entry["source"],
        )

    def test_lumi_and_statistical_are_downstream(self):
        for name in ("luminosity_2018", "mc_statistical_uncertainty"):
            self.assertEqual(self.by_name[name]["execution_class"], "downstream")

    def test_mc_efficiency_and_phase_space_are_excluded_phase1(self):
        for name in ("mc_efficiency_statistics", "phase_space_transfer_uncertainty"):
            entry = self.by_name[name]
            self.assertEqual(entry["execution_class"], "downstream")
            self.assertEqual(
                entry["final_disposition"],
                "excluded: recorded Phase-1 approximation per design spec",
            )

    def test_pending_review_entries_exist_by_design(self):
        pending = [
            entry["name"]
            for entry in self.entries
            if entry["final_disposition"] == "pending_review"
        ]
        self.assertTrue(pending, "expected at least one pending_review entry")


@unittest.skipUnless(_HAS_YAML, "PyYAML not installed in this interpreter")
class ValidatorTest(unittest.TestCase):
    """Exercises scripts/validate_systematics_inventory.py against the shipped
    YAML and the real SM shifts=all registration.

    The SM shifts=all build (across the full MC sample census,
    ``SM_SHIFT_ENUMERATION_SAMPLES``) is slow-ish, so it is done exactly once
    here via the validator's own ``run()`` entry point for both the default
    and --final-inference tests (each call rebuilds it; this is accepted as
    the straightforward, dependency-free way to invoke the validator exactly
    as its CLI does).
    """

    @classmethod
    def setUpClass(cls):
        from analysis_configurations.bbtautau.scripts import (
            validate_systematics_inventory as validator,
        )

        cls.validator = validator
        cls.default_ok, cls.default_errors = validator.run(final_inference=False)
        cls.final_ok, cls.final_errors = validator.run(final_inference=True)

    def test_default_mode_passes_against_shipped_yaml(self):
        self.assertTrue(self.default_ok, self.default_errors)

    def test_final_inference_mode_fails_at_this_milestone(self):
        # pending_review entries exist by design at this milestone (see the
        # YAML file and progress notes); --final-inference must reject them.
        self.assertFalse(self.final_ok)
        self.assertTrue(self.final_errors)
        joined = " ".join(self.final_errors)
        self.assertIn("pending_review", joined)

    def test_cli_exit_codes_match_run(self):
        import subprocess
        import sys

        script = ANALYSIS_ROOT / "scripts" / "validate_systematics_inventory.py"
        default_proc = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True
        )
        self.assertEqual(default_proc.returncode, 0, default_proc.stdout)

        final_proc = subprocess.run(
            [sys.executable, str(script), "--final-inference"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(final_proc.returncode, 0)

    def test_enumeration_samples_are_exactly_the_mc_default_samples(self):
        # Task-12 fix: SM_SHIFT_ENUMERATION_SAMPLES must be the full MC
        # census (every sm_config.DEFAULT_SAMPLES entry except "data", which
        # registers no shifts), not a hand-picked subset.
        from analysis_configurations.bbtautau import sm_config

        expected = {sample for sample in sm_config.DEFAULT_SAMPLES if sample != "data"}
        actual = set(self.validator.SM_SHIFT_ENUMERATION_SAMPLES)
        self.assertEqual(actual, expected)
        self.assertNotIn("data", self.validator.SM_SHIFT_ENUMERATION_SAMPLES)
        # sanity: DEFAULT_SAMPLES actually contains "data" today, so the
        # exclusion above is exercising a real filter, not a no-op.
        self.assertIn("data", sm_config.DEFAULT_SAMPLES)


@unittest.skipUnless(_HAS_YAML, "PyYAML not installed in this interpreter")
class ShiftCoveragePatternInvariantsTest(unittest.TestCase):
    """Unit-level tests for check_shift_coverage's three invariants (uncovered
    / unused pattern / ambiguous coverage), isolated from the slow real
    SM-shift build via hand-built ``registered_shifts`` sets -- these do not
    need setUpClass's real ``run()`` build."""

    @classmethod
    def setUpClass(cls):
        from analysis_configurations.bbtautau.scripts import (
            validate_systematics_inventory as validator,
        )

        cls.validator = validator

    @staticmethod
    def _crown_shift_entry(name, patterns):
        return {
            "name": name,
            "execution_class": "crown_shift",
            "shift_name_patterns": patterns,
        }

    def test_unused_pattern_is_flagged(self):
        entries = [self._crown_shift_entry("a", ["fooUnc", "neverMatchesAnythingUnc"])]
        registered = {"fooUncUp", "fooUncDown"}
        errors = self.validator.check_shift_coverage(entries, registered)
        joined = " ".join(errors)
        self.assertIn("unused pattern", joined)
        self.assertIn("neverMatchesAnythingUnc", joined)

    def test_ambiguous_coverage_is_flagged(self):
        # "fooUncUp" is matched by both entry a's "fooUnc" and entry b's
        # "fooUncUp" -- two crown_shift entries claiming the same registered
        # shift name violates the single-owner rule.
        entries = [
            self._crown_shift_entry("a", ["fooUnc"]),
            self._crown_shift_entry("b", ["fooUncUp"]),
        ]
        registered = {"fooUncUp", "fooUncDown"}
        errors = self.validator.check_shift_coverage(entries, registered)
        joined = " ".join(errors)
        self.assertIn("ambiguous coverage", joined)
        self.assertIn("fooUncUp", joined)
        self.assertIn("'a'", joined)
        self.assertIn("'b'", joined)

    def test_clean_single_owner_coverage_passes(self):
        entries = [
            self._crown_shift_entry("a", ["fooUnc"]),
            self._crown_shift_entry("b", ["barUnc"]),
        ]
        registered = {"fooUncUp", "fooUncDown", "barUncUp", "barUncDown"}
        errors = self.validator.check_shift_coverage(entries, registered)
        self.assertEqual(errors, [])


@unittest.skipUnless(_HAS_YAML, "PyYAML not installed in this interpreter")
class SchemaShortCircuitTest(unittest.TestCase):
    """run() must short-circuit after check_schema failures with a clean,
    itemized report -- not crash with a KeyError from a later check that
    assumes required fields are present -- and check_final_inference_gate
    must independently tolerate schema-incomplete entries."""

    @classmethod
    def setUpClass(cls):
        from analysis_configurations.bbtautau.scripts import (
            validate_systematics_inventory as validator,
        )

        cls.validator = validator

    def test_run_reports_missing_field_without_crashing(self):
        import tempfile

        broken = {
            "systematics": [
                {
                    "name": "broken_entry",
                    "execution_class": "crown_shift",
                    # every other required field (affected_samples,
                    # affected_channels, source, variation_keys,
                    # correlation_policy, production_status,
                    # final_disposition) is missing on purpose.
                }
            ]
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as handle:
            yaml.safe_dump(broken, handle)
            path = Path(handle.name)
        try:
            # Must not raise (a pre-fix run() would KeyError inside
            # check_shift_coverage/check_final_inference_gate); must return a
            # clean, itemized failure instead.
            ok, errors = self.validator.run(final_inference=True, inventory_path=path)
        finally:
            path.unlink()

        # Not crashing is the point of this test: a pre-fix run() would raise
        # KeyError here (check_shift_coverage/check_final_inference_gate
        # index required fields directly). check_schema itself also reports
        # a knock-on "no entry present for execution_class(es)" error for
        # this single-entry fixture (the entry's fields are incomplete, so
        # it is skipped before its execution_class is recorded as seen) --
        # both are check_schema's own output, so the report stays itemized
        # and schema-only; no later check (coverage/dynamic-keys/final
        # inference) contributes anything past this point.
        self.assertFalse(ok)
        joined = " ".join(errors)
        self.assertIn("broken_entry", joined)
        self.assertIn("missing required field", joined)
        self.assertIn("no entry present for execution_class", joined)
        self.assertEqual(len(errors), 2, errors)

    def test_final_inference_gate_skips_schema_incomplete_entries(self):
        entries = [
            {"name": "incomplete_entry"},  # no final_disposition/production_status
            {
                "name": "complete_pending_entry",
                "final_disposition": "pending_review",
                "production_status": "planned",
            },
        ]
        errors = self.validator.check_final_inference_gate(entries)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("complete_pending_entry", errors[0])


class NMSSMIsolationTest(unittest.TestCase):
    """The validator/inventory must stay SM-only: no import or open of the
    YAML anywhere on the NMSSM path. Pure text-grep, no YAML dependency, so
    this always runs (even under plain python3 without PyYAML)."""

    def test_common_config_never_references_the_sm_inventory(self):
        text = (ANALYSIS_ROOT / "common_config.py").read_text()
        self.assertNotIn("systematics_sm_2018", text)
        self.assertNotIn("validate_systematics_inventory", text)

    def test_nmssm_config_never_references_the_sm_inventory(self):
        text = (ANALYSIS_ROOT / "nmssm_config.py").read_text()
        self.assertNotIn("systematics_sm_2018", text)
        self.assertNotIn("validate_systematics_inventory", text)


if __name__ == "__main__":
    unittest.main()
