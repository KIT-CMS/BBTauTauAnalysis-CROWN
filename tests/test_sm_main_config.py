"""SM main-config contract.

Pins the SM (non-resonant HH -> bbtautau) configuration surface introduced for
the 2018 UL NanoAOD v15 UParT path:

* hh2b2tau truth mothers are 25/25 (both bb and tautau come from a SM Higgs);
* the standard ``LHE_Scale_weight`` producer is kept for the SM signal (the
  NMSSM-specific producer is not used);
* the pinned 2018-v15 UParTAK4 b-tag parameters (score column, medium WP,
  SF payload / correction names) replace the legacy Run-2 DeepJet wiring;
* the pinned-payload helpers read + validate the frozen working points and the
  per-correction systematic variations;
* the merged ``dyjets`` / ``wjets`` sample-type names (the SM surface carries no
  per-generator subtypes) receive the gen-boson + recoil treatment the legacy
  2018 subtypes get, while Zpt stays off for 2018 (Run-3-only producer).

Parameter lookups follow the characterization-suite accessor pattern
(``config_parameters[scope]["nominal"]``). The b-tag selection parameters are
registered in the ``global`` scope; the SF payload parameters in the analysis
scopes.

Since Task 11, ``SM_PROFILE.require_validated_btag_payload=True`` means every
MC build now also has to pass the strict validated-payload gate
(``btag_payloads.require_validated_payload``, called from
``common_config.build_config`` before any producer is scheduled) -- and the
real production payload (``payloads/btagging_efficiencies/upart_nanoaodv15/2018``)
has not been installed yet. ``build_sm()`` (imported from
``test_sm_v15_jet_path``) therefore only builds successfully for
sample=="data"/"embedding*" (which never reach the gate) or era!=2018. Every
other test in this module that needs a *successful* MC build goes through
``build_sm_valid_payload`` instead, which points a
``dataclasses.replace``d copy of ``SM_PROFILE`` at a synthetic, PASSING
payload fixture (``tests/fixtures/sm_btag_efficiency_payload.py``) built once
for the module. The gate-failure/gate-bypass/alias-contradiction contract
itself is pinned directly against the pristine, unpatched profile below.
"""
import dataclasses
import json
import os
import tempfile
import unittest
from unittest import mock

from analysis_configurations.bbtautau import (
    btag_payloads,
    common_config,
    nmssm_config,
    sm_btag_efficiency_config,
    sm_config,
)
from analysis_configurations.bbtautau.analysis_profiles import SM_PROFILE
from analysis_configurations.bbtautau.constants import ERAS, SCOPES
from analysis_configurations.bbtautau.tests.fixtures.sm_btag_efficiency_payload import (
    write_passing_payload,
)
from analysis_configurations.bbtautau.tests.test_sm_v15_jet_path import build_sm
from analysis_configurations.bbtautau.tests.test_nmssm_characterization import (
    LEGACY_AVAILABLE_SAMPLES,
    producer_names,
    output_names,
)

# A single synthetic, PASSING efficiency payload shared by every test in this
# module that needs an SM MC build to actually succeed (see module docstring).
_VALID_PAYLOAD_DIR = tempfile.mkdtemp(prefix="sm_main_config_btag_payload_")
write_passing_payload(_VALID_PAYLOAD_DIR, scopes=("et", "mt", "tt"))


def build_sm_valid_payload(sample, era="2018", scopes=("mt",)):
    """Build through SM_PROFILE with btag_payload_dir replaced by a synthetic,
    PASSING payload fixture, so the validated-payload gate is satisfied.

    Everything else about the profile (require_validated_btag_payload=True,
    btag_2018_algorithm, etc.) is untouched -- only the directory the gate
    reads from is redirected to the fixture, exactly the
    ``dataclasses.replace`` pattern the gate's own tests use below.
    """
    profile = dataclasses.replace(SM_PROFILE, btag_payload_dir=_VALID_PAYLOAD_DIR)
    return common_config.build_config(
        profile, era, sample, list(scopes), {"none"},
        sm_config.AVAILABLE_SAMPLES, ["2018"], SCOPES,
    )


def _all_producers(config):
    return producer_names(config, "mt") | producer_names(config, "global")


def _expected_upart_weight_columns():
    """Independently derive the expected UParTAK4 weight column names.

    One nominal column plus, for every non-``central`` systematic key present
    in either the comb or the light correction, one ``btag_weight_upart_<key>``
    column (each correction ships symmetric up/down keys, so this reproduces
    the per-component up/down dispatch the producer emits).
    """
    variations = btag_payloads.discover_upart_variations(
        btag_payloads.PINNED_BTV_2018_V15
    )
    keys = (variations["UParTAK4_comb"] | variations["UParTAK4_light"]) - {
        "central"
    }
    return {"btag_weight_upart"} | {f"btag_weight_upart_{key}" for key in keys}


class SMMainConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg_sig = build_sm_valid_payload("hh2b2tau")
        cls.cfg_tt = build_sm_valid_payload("ttbar")

    def test_truth_mothers_are_25_for_sm_signal(self):
        params = self.cfg_sig.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bb_truegen_mother_pdgid"], 25)
        self.assertEqual(params["tautau_truegen_mother_pdgid"], 25)

    def test_sm_signal_uses_standard_lhe_producer(self):
        names = producer_names(self.cfg_sig, "global")
        self.assertIn("LHE_Scale_weight", names)
        self.assertNotIn("NMSSM_LHE_Scale_weight", names)

    def test_upart_btag_path_2018(self):
        params = self.cfg_tt.config_parameters["global"]["nominal"]
        self.assertEqual(params["bjet_max_abs_eta"], 2.4)
        self.assertIn("Jet_btagUParTAK4B", str(params["bjet_score_column"]))
        self.assertAlmostEqual(params["bjet_min_score"], 0.161)

    def test_upart_sf_payload_parameters(self):
        params = self.cfg_tt.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bjet_sf_file"], btag_payloads.PINNED_BTV_2018_V15)
        self.assertEqual(params["bjet_sf_name"], "UParTAK4_comb")
        self.assertEqual(params["bjet_sf_bc_name"], "UParTAK4_comb")
        self.assertEqual(params["bjet_sf_lf_name"], "UParTAK4_light")
        self.assertEqual(params["bjet_sf_wp_name"], "UParTAK4_wp_values")

    def test_mass_tautaubb_still_output(self):
        self.assertIn("mass_tautaubb", output_names(self.cfg_tt, "mt"))

    def test_pinned_wp_loader_validates(self):
        wps = btag_payloads.load_upart_wps(btag_payloads.PINNED_BTV_2018_V15)
        self.assertEqual(
            wps,
            {"L": 0.0308, "M": 0.161, "T": 0.5405, "XT": 0.6992, "XXT": 0.9655},
        )

    def test_variation_discovery_is_per_correction(self):
        var = btag_payloads.discover_upart_variations(
            btag_payloads.PINNED_BTV_2018_V15
        )
        self.assertEqual(
            len([v for v in var["UParTAK4_comb"] if v.startswith("up")]), 41
        )
        self.assertEqual(
            sorted(v for v in var["UParTAK4_light"] if v.startswith("up")),
            ["up", "up_correlated", "up_uncorrelated"],
        )

    # -- DY/W merged-group wiring (SM surface uses merged dyjets/wjets) --------

    def test_sm_dyjets_gets_gen_boson_and_recoil(self):
        names = _all_producers(build_sm_valid_payload("dyjets"))
        # Gen-boson four-vector + the intact recoil-correction group (MetScopes),
        # matching the treatment the legacy 2018 DY subtypes get. RenameMet (the
        # "no recoil correction" path) must NOT be scheduled.
        self.assertIn("GenBosonQuantities", names)
        self.assertIn("MetScopes", names)
        self.assertNotIn("RenameMet", names)

    def test_sm_wjets_gets_gen_boson_and_recoil(self):
        names = _all_producers(build_sm_valid_payload("wjets"))
        self.assertIn("GenBosonQuantities", names)
        self.assertIn("MetScopes", names)
        self.assertNotIn("RenameMet", names)

    def test_sm_zpt_producer_off_for_2018(self):
        # ZPtReweighting is Run-3-only (z_pt_reweighting_producers == [] and
        # zpt_weight_file == DOES_NOT_EXIST for 2018): no Zpt producer is
        # scheduled for either DY or W, mirroring the legacy 2018 subtypes.
        for sample in ("dyjets", "wjets"):
            self.assertNotIn(
                "ZPtReweighting", _all_producers(build_sm_valid_payload(sample))
            )

    def test_sm_non_dyw_sample_gets_rename_met(self):
        names = _all_producers(self.cfg_tt)
        self.assertIn("RenameMet", names)
        self.assertNotIn("GenBosonQuantities", names)
        self.assertNotIn("MetScopes", names)

    # -- Strict UParTAK4 multi-WP event-weight consumer (SM path) --------------

    def test_strict_upart_producer_scheduled_for_sm(self):
        self.assertIn(
            "StrictUParTBtagWeight", producer_names(self.cfg_tt, "mt")
        )

    def test_deepjet_shape_producer_not_scheduled_for_sm(self):
        names = producer_names(self.cfg_tt, "mt")
        self.assertNotIn("BJetShapeDeepJet_SF", names)
        self.assertNotIn("BJetWPUParT_SF", names)

    def test_legacy_id_wgt_bjet_dropped_for_sm(self):
        # The DeepJet-shape producer (which produced id_wgt_bjet) is gone; the
        # strict UParT columns replace it, so id_wgt_bjet is no longer written.
        self.assertNotIn("id_wgt_bjet", output_names(self.cfg_tt, "mt"))

    def test_upart_weight_variation_columns_match_discovery(self):
        actual = {
            o
            for o in output_names(self.cfg_tt, "mt")
            if o.startswith("btag_weight_upart")
        }
        self.assertEqual(actual, _expected_upart_weight_columns())

    def test_clamp_diagnostic_in_outputs(self):
        self.assertIn(
            "btag_eff_pt_clamped_njets", output_names(self.cfg_tt, "mt")
        )

    def test_efficiency_sample_type_is_identity_for_hh2b2tau(self):
        # The SM path keys the efficiency lookup on the sample's OWN name (no
        # legacy hh2b2tau -> ggh_htautau aliasing).
        params = self.cfg_sig.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bjet_eff_sample_type"], "hh2b2tau")
        self.assertEqual(
            self.cfg_tt.config_parameters["mt"]["nominal"]["bjet_eff_sample_type"],
            "ttbar",
        )

    def test_upart_consumer_parameters(self):
        params = self.cfg_tt.config_parameters["mt"]["nominal"]
        self.assertIn(
            "btag_efficiency_mt.json.gz", str(params["bjet_eff_file"])
        )
        self.assertEqual(params["bjet_eff_pt_clamp"], 1000.0)

    def test_upart_wp_thresholds_baked_into_consumer_call(self):
        # The five WP thresholds are baked (tightest -> loosest) into the
        # weight producers' calls via {vec_open}/{vec_close}, not a config
        # parameter (a std::vector<float> literal cannot survive CROWN's format
        # passes as a parameter value).
        subproducers = {
            p.name: p
            for group in self.cfg_tt.producers["mt"]
            if group.name == "StrictUParTBtagWeight"
            for p in group.producers["mt"]
        }
        call = subproducers["StrictUParTBtagWeightNominal"].call
        self.assertIn("{vec_open}", call)
        self.assertIn("{vec_close}", call)
        for threshold in ("0.9655f", "0.6992f", "0.5405f", "0.161f", "0.0308f"):
            self.assertIn(threshold, call)

    def test_nmssm_btag_scheduling_unchanged(self):
        # Guards that the SM producer swap does not leak into NMSSM: NMSSM keeps
        # the DeepJet-shape producer + id_wgt_bjet and never sees the strict
        # consumer or its columns.
        cfg = nmssm_config.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES,
        )
        names = producer_names(cfg, "mt")
        outs = output_names(cfg, "mt")
        self.assertIn("BJetShapeDeepJet_SF", names)
        self.assertNotIn("StrictUParTBtagWeight", names)
        self.assertIn("id_wgt_bjet", outs)
        self.assertFalse(any(o.startswith("btag_weight_upart") for o in outs))

    def test_efficiency_profile_schedules_no_btag_sf(self):
        # SM_BTAG_EFFICIENCY_PROFILE pins btag_2018_algorithm=="upart_2018_v15"
        # (same as SM_PROFILE) but has enable_btag_sf=False and
        # btag_payload_dir=None: it must never take the strict-UParT-consumer
        # branch, since an efficiency-measurement profile must not apply b-tag
        # SFs, and its {bjet_eff_file} parameter is never staged (that only
        # happens when btag_payload_dir is set) -- scheduling the consumer
        # would reference an unresolved config parameter. Available sample
        # types use LEGACY_AVAILABLE_SAMPLES (not the profile's own, MC-only
        # AVAILABLE_SAMPLES) because unrelated unconditional rules elsewhere in
        # build_config require "data"/"embedding"/"embedding_mc" to be present
        # in the available-sample-types universe regardless of this profile's
        # restricted sample surface.
        cfg = sm_btag_efficiency_config.build_config(
            "2018", "ttbar", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES,
        )
        names = producer_names(cfg, "mt") | producer_names(cfg, "global")
        outs = output_names(cfg, "mt")
        self.assertFalse(
            any("UParT" in name for name in names),
            f"strict UParT consumer scheduled on the efficiency profile: {names}",
        )
        self.assertNotIn("StrictUParTBtagWeight", names)
        self.assertFalse(any(o.startswith("btag_weight_upart") for o in outs))


# -- Strict validated-payload gate (Task 11) -------------------------------


class ValidatedPayloadGateTest(unittest.TestCase):
    """The build_config-level gate: btag_payloads.require_validated_payload,
    called only when _use_strict_upart_btag(profile, era) and
    profile.require_validated_btag_payload and is_mc.
    """

    def test_missing_validated_payload_raises_with_actionable_message(self):
        # build_sm() uses the pristine, unpatched SM_PROFILE, whose
        # btag_payload_dir ("payloads/btagging_efficiencies/upart_nanoaodv15/2018")
        # has no provenance.json installed yet -- the real production chain
        # (sm_btag_efficiency_config -> TauFakeFactors -> install) has not
        # run. hh2b2tau is MC, so the gate must fire before any producer is
        # scheduled.
        with self.assertRaises(FileNotFoundError) as ctx:
            build_sm("hh2b2tau")
        message = str(ctx.exception)
        self.assertIn("upart_nanoaodv15/2018", message)
        self.assertIn("provenance.json", message)
        # actionable: names the production chain that creates the payload.
        self.assertIn("sm_btag_efficiency_config", message)
        self.assertIn("TauFakeFactors", message)
        self.assertIn("install", message)

    def test_missing_validated_payload_raises_for_ttbar_too(self):
        # Not signal-specific: ANY MC sample under the production profile
        # must hit the gate.
        with self.assertRaises(FileNotFoundError):
            build_sm("ttbar")

    def test_validated_payload_gate_passes_with_synthetic_fixture(self):
        # (b) A dedicated, self-contained synthetic payload+provenance
        # (independent of the module-shared _VALID_PAYLOAD_DIR) proves the
        # gate accepts a well-formed passing payload, and that the build
        # keys the efficiency lookup on hh2b2tau's OWN name (identity, NOT
        # the legacy hh2b2tau -> ggh_htautau aliasing).
        payload_dir = tempfile.mkdtemp(prefix="sm_gate_pass_")
        write_passing_payload(payload_dir, scopes=("mt",))
        profile = dataclasses.replace(SM_PROFILE, btag_payload_dir=payload_dir)
        cfg = common_config.build_config(
            profile, "2018", "hh2b2tau", ["mt"], {"none"},
            sm_config.AVAILABLE_SAMPLES, ["2018"], SCOPES,
        )
        params = cfg.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bjet_eff_sample_type"], "hh2b2tau")
        self.assertIn("StrictUParTBtagWeight", producer_names(cfg, "mt"))

    def test_data_build_succeeds_without_validated_payload(self):
        # (c) data builds evaluate no MC b-tag efficiency SF at all
        # (is_mc=False), so the gate must not even attempt to resolve the
        # (still-absent) production payload directory.
        cfg = build_sm("data")
        params = cfg.config_parameters["global"]["nominal"]
        self.assertTrue(params["is_data"])
        self.assertFalse(params["is_mc"])

    def test_embedding_mc_bypasses_payload_gate(self):
        # Fix (code review): "embedding_mc" was, before the fix, treated as
        # is_mc==True by the gate's own `is_mc` check (`is_mc = sample not in
        # ["data", "embedding"]` -- global NMSSM semantics, deliberately left
        # untouched), so it incorrectly required the (here absent) real
        # production payload just like a genuine MC sample. Like "embedding",
        # embedding_mc jobs never evaluate a b-tag MC efficiency SF and must
        # not require the payload to exist on disk either. The gate condition
        # is now `requires_btag_payload = is_mc and sample != "embedding_mc"`.
        #
        # Full end-to-end build success for "embedding"/"embedding_mc" is
        # currently blocked by a SEPARATE, unrelated, pre-existing bug deeper
        # in setup_embedding() (tau_embedding_settings.py references several
        # producers -- e.g. scalefactors.Tau_2_VsJetTauID_lt_SF,
        # scalefactors.Tau_1_VsJetTauID_SF, scalefactors.Tau_2_VsJetTauID_tt_SF
        # -- that no longer exist in producers/scalefactors.py) -- out of
        # scope for this fix (it predates it and is independent of the gate).
        # This test therefore isolates the gate itself via mock: if it fired,
        # btag_payloads.require_validated_payload would be called (and would
        # raise FileNotFoundError, since SM_PROFILE's real production payload
        # directory is not installed); asserting it is never called proves
        # the bypass, independent of the later, unrelated AttributeError.
        with mock.patch.object(
            btag_payloads, "require_validated_payload"
        ) as mocked_gate:
            try:
                build_sm("embedding_mc")
            except AttributeError:
                pass  # pre-existing, unrelated setup_embedding breakage (see above)
            mocked_gate.assert_not_called()

    def test_non_strict_profile_never_requires_payload(self):
        # SM_BTAG_EFFICIENCY_PROFILE has require_validated_btag_payload=False
        # (and enable_btag_sf=False, so _use_strict_upart_btag is False
        # too): the gate must be skipped even though its own
        # btag_payload_dir is None (which would otherwise make the gate
        # raise via resolve_payload_dir).
        cfg = sm_btag_efficiency_config.build_config(
            "2018", "hh2b2tau", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ["2018"], SCOPES,
        )
        self.assertIsNotNone(cfg)

    def test_nmssm_never_requires_payload(self):
        # NMSSM_PROFILE.require_validated_btag_payload is False and
        # btag_2018_algorithm is None: never reaches the gate.
        cfg = nmssm_config.build_config(
            "2018", "hh4b", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES,
        )
        self.assertIsNotNone(cfg)


class LegacyEfficiencyAliasTest(unittest.TestCase):
    """AnalysisProfile.legacy_btag_efficiency_alias: accepted ONLY under the
    explicit, non-production opt-in conditions; contradictory with the
    validated-payload gate.
    """

    def test_alias_contradiction_raises(self):
        # (d) SM_PROFILE uses the dedicated production payload path
        # (require_validated_btag_payload=True): setting a non-empty alias
        # on top of it is a contradiction, caught at build time -- it must
        # NOT silently activate (nor silently fall back to identity).
        profile = dataclasses.replace(
            SM_PROFILE,
            legacy_btag_efficiency_alias={"hh2b2tau": "ggh_htautau"},
        )
        with self.assertRaises(ValueError) as ctx:
            common_config.build_config(
                profile, "2018", "ttbar", ["mt"], {"none"},
                sm_config.AVAILABLE_SAMPLES, ["2018"], SCOPES,
            )
        message = str(ctx.exception)
        self.assertIn("legacy_btag_efficiency_alias", message)
        self.assertIn("require_validated_btag_payload", message)

    def test_alias_activates_only_for_explicit_non_production_opt_in(self):
        # ALL conditions met: upart_2018_v15, the alias maps hh2b2tau onto
        # "ggh_htautau", require_validated_btag_payload=False (NOT the
        # production path), and the alias is explicitly set (never
        # auto-activated).
        profile = dataclasses.replace(
            SM_PROFILE,
            require_validated_btag_payload=False,
            legacy_btag_efficiency_alias={"hh2b2tau": "ggh_htautau"},
        )
        cfg = common_config.build_config(
            profile, "2018", "hh2b2tau", ["mt"], {"none"},
            sm_config.AVAILABLE_SAMPLES, ["2018"], SCOPES,
        )
        params = cfg.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bjet_eff_sample_type"], "ggh_htautau")

    def test_alias_activation_logs_warning_and_records_parameter(self):
        # Fix (code review): activating the legacy alias must not be silent.
        # It must (a) log a WARNING naming the active sample -> target
        # mapping, and (b) be written into the configuration itself (as the
        # `legacy_btag_efficiency_alias_active` global-scope parameter) so it
        # also surfaces in the generated configuration report/parameters, not
        # only in the build log. Reuses the same profile fixture as
        # test_alias_activates_only_for_explicit_non_production_opt_in above.
        profile = dataclasses.replace(
            SM_PROFILE,
            require_validated_btag_payload=False,
            legacy_btag_efficiency_alias={"hh2b2tau": "ggh_htautau"},
        )
        with self.assertLogs(
            "analysis_configurations.bbtautau.common_config", level="WARNING"
        ) as logs:
            cfg = common_config.build_config(
                profile, "2018", "hh2b2tau", ["mt"], {"none"},
                sm_config.AVAILABLE_SAMPLES, ["2018"], SCOPES,
            )
        self.assertTrue(
            any("LEGACY B-TAG EFFICIENCY ALIAS ACTIVE" in msg for msg in logs.output)
        )
        self.assertTrue(
            any("hh2b2tau -> ggh_htautau" in msg for msg in logs.output)
        )
        params = cfg.config_parameters["global"]["nominal"]
        self.assertEqual(
            params["legacy_btag_efficiency_alias_active"], "hh2b2tau->ggh_htautau"
        )

    def test_alias_stays_inactive_without_explicit_ggh_htautau_target(self):
        # Non-empty alias, non-production path, but it doesn't map anything
        # onto "ggh_htautau" (the specific legacy target this escape hatch
        # exists for): stays identity.
        profile = dataclasses.replace(
            SM_PROFILE,
            require_validated_btag_payload=False,
            legacy_btag_efficiency_alias={"ttbar": "rem_ttbar"},
        )
        cfg = common_config.build_config(
            profile, "2018", "hh2b2tau", ["mt"], {"none"},
            sm_config.AVAILABLE_SAMPLES, ["2018"], SCOPES,
        )
        params = cfg.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bjet_eff_sample_type"], "hh2b2tau")
        # No activation -> no report annotation either.
        self.assertNotIn(
            "legacy_btag_efficiency_alias_active",
            cfg.config_parameters["global"]["nominal"],
        )

    def test_alias_never_activates_for_nmssm(self):
        # NMSSM_PROFILE.legacy_btag_efficiency_alias is None and
        # btag_2018_algorithm is None: the alias-resolution branch is not
        # even reachable (use_sm_2018_v15 is False), so NMSSM's own,
        # unrelated hh2b2tau -> ggh_htautau SampleModifier (the *legacy*
        # sample_types dict at ~L1777) is untouched by this task.
        cfg = nmssm_config.build_config(
            "2018", "hh2b2tau", ["mt"], {"none"},
            LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES,
        )
        params = cfg.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bjet_eff_sample_type"], "ggh_htautau")


class RequireValidatedPayloadUnitTest(unittest.TestCase):
    """Direct unit tests of btag_payloads.require_validated_payload, pinning
    its FileNotFoundError/ValueError contract independent of build_config.
    """

    def setUp(self):
        self.payload_dir = tempfile.mkdtemp(prefix="require_validated_payload_")

    def test_returns_parsed_provenance_on_success(self):
        write_passing_payload(self.payload_dir, scopes=("et", "mt", "tt"))
        provenance = btag_payloads.require_validated_payload(
            self.payload_dir, ["et", "mt", "tt"],
            btag_payloads.SM_BTAG_EFFICIENCY_CATEGORIES,
        )
        self.assertEqual(provenance["validation_status"], "passed")
        self.assertEqual(
            set(provenance["manifest"]),
            {f"btag_efficiency_{s}.json.gz" for s in ("et", "mt", "tt")},
        )

    def test_missing_provenance_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            btag_payloads.require_validated_payload(
                self.payload_dir, ["mt"], btag_payloads.SM_BTAG_EFFICIENCY_CATEGORIES,
            )

    def test_missing_scope_file_raises_file_not_found(self):
        write_passing_payload(self.payload_dir, scopes=("mt",))
        with self.assertRaises(FileNotFoundError):
            btag_payloads.require_validated_payload(
                self.payload_dir, ["mt", "tt"],
                btag_payloads.SM_BTAG_EFFICIENCY_CATEGORIES,
            )

    def test_failed_validation_status_raises_value_error(self):
        write_passing_payload(self.payload_dir, scopes=("mt",))
        provenance_path = os.path.join(self.payload_dir, "provenance.json")
        with open(provenance_path) as handle:
            provenance = json.load(handle)
        provenance["validation_status"] = "failed"
        with open(provenance_path, "w") as handle:
            json.dump(provenance, handle)
        with self.assertRaisesRegex(ValueError, "validation_status"):
            btag_payloads.require_validated_payload(
                self.payload_dir, ["mt"], btag_payloads.SM_BTAG_EFFICIENCY_CATEGORIES,
            )

    def test_checksum_mismatch_raises_value_error(self):
        write_passing_payload(self.payload_dir, scopes=("mt",))
        with open(
            os.path.join(self.payload_dir, "btag_efficiency_mt.json.gz"), "ab"
        ) as handle:
            handle.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "checksum"):
            btag_payloads.require_validated_payload(
                self.payload_dir, ["mt"], btag_payloads.SM_BTAG_EFFICIENCY_CATEGORIES,
            )

    def test_missing_category_raises_value_error(self):
        write_passing_payload(
            self.payload_dir, scopes=("mt",), categories=["hh2b2tau", "dyjets"],
        )
        with self.assertRaisesRegex(ValueError, "missing expected sample_type"):
            btag_payloads.require_validated_payload(
                self.payload_dir, ["mt"], btag_payloads.SM_BTAG_EFFICIENCY_CATEGORIES,
            )


if __name__ == "__main__":
    unittest.main()
