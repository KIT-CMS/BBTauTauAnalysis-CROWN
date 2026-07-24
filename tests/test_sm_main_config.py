"""SM main-config contract for the 2018 UL NanoAOD v15 UParT path.

* hh2b2tau truth mothers are 25/25 (both bb and tautau come from a SM Higgs);
* the standard ``LHE_Scale_weight`` producer is kept for the SM signal (the
  NMSSM-specific producer is not used);
* the pinned 2018-v15 UParTAK4 b-tag parameters (score column, medium WP,
  SF payload / correction names) replace the legacy Run-2 DeepJet wiring;
* working points and systematic variations are read from the pinned payload;
* the merged ``dyjets`` / ``wjets`` sample-type names (the SM surface carries no
  per-generator subtypes) receive the gen-boson + recoil treatment the legacy
  2018 subtypes get, while Zpt stays off for 2018 (Run-3-only producer).

Parameter lookups follow the characterization-suite accessor pattern
(``config_parameters[scope]["nominal"]``). The b-tag selection parameters are
registered in the ``global`` scope; the SF payload parameters in the analysis
scopes.
"""
import dataclasses
import gzip
import json
import os
import tempfile
import unittest

from analysis_configurations.bbtautau import (
    btag_payloads,
    common_config,
    nmssm_config,
    sm_btag_efficiency_config,
    sm_config,
)
from analysis_configurations.bbtautau.analysis_profiles import SM_PROFILE
from analysis_configurations.bbtautau.constants import ERAS, SCOPES
from analysis_configurations.bbtautau.tests.test_sm_v15_jet_path import build_sm
from analysis_configurations.bbtautau.tests.test_nmssm_characterization import (
    LEGACY_AVAILABLE_SAMPLES,
    producer_names,
    output_names,
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
        cls.cfg_sig = build_sm("hh2b2tau")
        cls.cfg_tt = build_sm("ttbar")

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
        wps = btag_payloads.load_upart_wps(btag_payloads.PINNED_BTV_2018_V15)
        self.assertEqual(params["bjet_min_score"], wps["M"])

    def test_upart_sf_payload_parameters(self):
        params = self.cfg_tt.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bjet_sf_file"], btag_payloads.PINNED_BTV_2018_V15)
        self.assertEqual(params["bjet_sf_name"], "UParTAK4_comb")
        self.assertEqual(params["bjet_sf_bc_name"], "UParTAK4_comb")
        self.assertEqual(params["bjet_sf_lf_name"], "UParTAK4_light")
        self.assertEqual(params["bjet_sf_wp_name"], "UParTAK4_wp_values")

    def test_mass_tautaubb_still_output(self):
        self.assertIn("mass_tautaubb", output_names(self.cfg_tt, "mt"))

    def test_wp_loader_reads_values_from_selected_payload(self):
        expected = {"L": 0.01, "M": 0.12, "T": 0.53, "XT": 0.71, "XXT": 0.97}
        payload = {
            "corrections": [
                {
                    "name": "UParTAK4_wp_values",
                    "data": {
                        "content": [
                            {"key": key, "value": value}
                            for key, value in expected.items()
                        ]
                    },
                }
            ]
        }
        payload_path = os.path.join(
            tempfile.mkdtemp(prefix="upart_wp_payload_"), "btagging.json.gz"
        )
        with gzip.open(payload_path, "wt") as handle:
            json.dump(payload, handle)

        self.assertEqual(btag_payloads.load_upart_wps(payload_path), expected)

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
        names = _all_producers(build_sm("dyjets"))
        # Gen-boson four-vector + the intact recoil-correction group (MetScopes),
        # matching the treatment the legacy 2018 DY subtypes get. RenameMet (the
        # "no recoil correction" path) must NOT be scheduled.
        self.assertIn("GenBosonQuantities", names)
        self.assertIn("MetScopes", names)
        self.assertNotIn("RenameMet", names)

    def test_sm_wjets_gets_gen_boson_and_recoil(self):
        names = _all_producers(build_sm("wjets"))
        self.assertIn("GenBosonQuantities", names)
        self.assertIn("MetScopes", names)
        self.assertNotIn("RenameMet", names)

    def test_sm_zpt_producer_off_for_2018(self):
        # ZPtReweighting is Run-3-only (z_pt_reweighting_producers == [] and
        # zpt_weight_file == DOES_NOT_EXIST for 2018): no Zpt producer is
        # scheduled for either DY or W, mirroring the legacy 2018 subtypes.
        for sample in ("dyjets", "wjets"):
            self.assertNotIn(
                "ZPtReweighting", _all_producers(build_sm(sample))
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
        wps = btag_payloads.load_upart_wps(btag_payloads.PINNED_BTV_2018_V15)
        for wp in ("XXT", "XT", "T", "M", "L"):
            self.assertIn(f"{wps[wp]}f", call)

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


class EfficiencyPayloadPathTest(unittest.TestCase):
    def test_efficiency_payload_path_is_forwarded_without_prevalidation(self):
        payload_dir = os.path.join(
            tempfile.mkdtemp(prefix="sm_efficiency_path_"), "not-installed"
        )
        profile = dataclasses.replace(SM_PROFILE, btag_payload_dir=payload_dir)
        cfg = common_config.build_config(
            profile, "2018", "ttbar", ["mt"], {"none"},
            sm_config.AVAILABLE_SAMPLES, ["2018"], SCOPES,
        )

        params = cfg.config_parameters["mt"]["nominal"]
        self.assertEqual(
            params["bjet_eff_file"],
            os.path.join(payload_dir, "btag_efficiency_mt.json.gz"),
        )


class LegacyEfficiencyAliasTest(unittest.TestCase):
    """Contract for the explicit legacy efficiency sample-type alias."""

    def test_alias_activates_only_for_explicit_opt_in(self):
        profile = dataclasses.replace(
            SM_PROFILE,
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
        # An alias that does not target the supported legacy sample stays
        # inactive.
        profile = dataclasses.replace(
            SM_PROFILE,
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


if __name__ == "__main__":
    unittest.main()
