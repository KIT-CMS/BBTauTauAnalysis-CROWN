"""SM 2018-UL NanoAOD-v15 config contracts, and the NMSSM path they must not disturb.

Each assertion pins a value that would otherwise regress silently into wrong
physics or a broken grid job: the truth-gen mothers and LHE dispatch per sample,
the pinned UParTAK4 b-tag and v15 jet/electron wiring, the per-variation weight
columns and the scopes they run in, the DY/W recoil treatment, and the era/sample
gates. Parameter lookups follow ``config_parameters[scope]["nominal"]``.
"""
import importlib
import unittest
from unittest import mock

from analysis_configurations.bbtautau import btag_payloads, generate
from analysis_configurations.bbtautau.tests.helpers import (
    FakeArgs, build, find_producer, output_names, producer_names,
)

try:
    import yaml  # noqa: F401  -- only probed; the validator imports it itself
except ImportError:  # pragma: no cover
    yaml = None

ALL_SCOPES = ("et", "mt", "tt", "em", "ee", "mm")
HAD_TAU_SCOPES, FULLY_LEPTONIC_SCOPES = ("et", "mt", "tt"), ("em", "ee", "mm")
LHE_PRODUCERS = {"LHE_Scale_weight", "NMSSM_LHE_Scale_weight"}

# module, sample, bb mother pdgid, tautau mother pdgid, the only LHE producer
# that may be scheduled. A lost SampleModifier key falls back to -1 and yields
# garbage truth pairs, so the background default is pinned as well.
TRUTH_CASES = (
    ("sm_config", "hh2b2tau", 25, 25, "LHE_Scale_weight"),
    ("nmssm_config", "nmssm_Ybb", 35, 25, "NMSSM_LHE_Scale_weight"),
    ("nmssm_config", "nmssm_Ytautau", 25, 35, "NMSSM_LHE_Scale_weight"),
    ("nmssm_config", "ttbar", -1, -1, "LHE_Scale_weight"),
)


class SMMainConfigTest(unittest.TestCase):
    def test_truth_mothers_and_lhe_dispatch(self):
        for module_name, sample, bb, tautau, lhe in TRUTH_CASES:
            with self.subTest(module=module_name, sample=sample):
                config = build(module_name, sample)
                params = config.config_parameters["mt"]["nominal"]
                self.assertEqual(params["bb_truegen_mother_pdgid"], bb)
                self.assertEqual(params["tautau_truegen_mother_pdgid"], tautau)
                self.assertEqual(params["bb_truegen_daughter_1_pdgid"], 5)
                self.assertEqual(params["tautau_truegen_daughter_1_pdgid"], 15)
                self.assertEqual(producer_names(config, "global") & LHE_PRODUCERS, {lhe})

    def test_upart_btag_and_v15_input_wiring(self):
        config = build("sm_config", "ttbar", scopes=ALL_SCOPES)
        params = config.config_parameters["global"]["nominal"]
        payload = btag_payloads.btv_upart_payload("2018")
        self.assertEqual(params["bjet_max_abs_eta"], 2.4)
        self.assertEqual(params["bjet_score_column"], "Jet_btagUParTAK4B")
        wps = btag_payloads.load_upart_wps(payload)
        self.assertEqual(params["bjet_min_score"], wps["M"])

        sf = config.config_parameters["mt"]["nominal"]
        self.assertEqual(sf["bjet_sf_file"], payload)
        # swapping these applies heavy-flavour SFs to light jets and vice versa
        self.assertEqual(sf["bjet_sf_bc_name"], "UParTAK4_comb")
        self.assertEqual(sf["bjet_sf_lf_name"], "UParTAK4_light")

        # the efficiency lookup keys on the sample's OWN name (no legacy
        # hh2b2tau -> ggh_htautau alias) and reads the per-channel payload
        signal = build("sm_config", "hh2b2tau").config_parameters["mt"]["nominal"]
        self.assertEqual(sf["bjet_eff_sample_type"], "ttbar")
        self.assertEqual(signal["bjet_eff_sample_type"], "hh2b2tau")
        self.assertEqual(
            sf["bjet_eff_file"],
            "payloads/btagging_efficiencies/upart/2018/btag_efficiency_mt.json.gz",
        )

        self.assertIn("AuxJetCollectionQuantities", producer_names(config, "global"))
        # the correctionlib jet ID, not the v9 Jet_jetId rename; and the
        # Run-3-style electron scale+smear group, not the Run-2 rename (both era
        # variants of these two producers share one name)
        jet_id = find_producer(config, "global", "JetID").call
        ele_pt = find_producer(config, "global", "ElectronPtCorrectionMC").call
        self.assertIn("physicsobject::jet::quantity::ID", jet_id)
        self.assertIn("physicsobject::electron::PtCorrectionMC", ele_pt)

        # the Run-3 EGM Electron-HLT-SF correction does not exist for 2018 UL,
        # so the et scope evaluates TauAnalysis' Trg32_Iso_pt_eta_bins instead
        et = producer_names(config, "et")
        self.assertIn("ETGenerateSingleElectronTriggerSF_MC", et)
        self.assertNotIn("SingleEleTriggerSF", et)

        # the payload pin is keyed per era and fails loudly for an unpinned one
        with self.assertRaises(KeyError):
            btag_payloads.btv_upart_payload("2022preEE")

    def test_upart_weight_variation_columns_match_discovery(self):
        variations = btag_payloads.discover_upart_variations(
            btag_payloads.btv_upart_payload("2018")
        )
        keys = (variations["UParTAK4_comb"] | variations["UParTAK4_light"]) - {"central"}
        expected = {"btag_weight_upart"} | {f"btag_weight_upart_{k}" for k in keys}
        self.assertEqual(len(expected), 83)

        config = build("sm_config", "ttbar", scopes=ALL_SCOPES)
        for scope in HAD_TAU_SCOPES:
            with self.subTest(scope=scope):
                outs = output_names(config, scope)
                self.assertEqual(
                    {o for o in outs if o.startswith("btag_weight_upart")}, expected
                )
        for scope in FULLY_LEPTONIC_SCOPES:
            with self.subTest(scope=scope):
                outs = output_names(config, scope)
                self.assertFalse(any(o.startswith("btag_weight_upart") for o in outs))
                self.assertNotIn("StrictUParTBtagWeight", producer_names(config, scope))

    def test_sm_dyw_recoil_wiring(self):
        # the merged dyjets/wjets names get the gen-boson four-vector and the
        # intact recoil-correction group; everything else takes RenameMet
        for sample in ("dyjets", "wjets"):
            with self.subTest(sample=sample):
                config = build("sm_config", sample)
                names = producer_names(config, "mt") | producer_names(config, "global")
                self.assertIn("GenBosonQuantities", names)
                self.assertIn("MetScopes", names)
                self.assertNotIn("RenameMet", names)

        ttbar = build("sm_config", "ttbar", scopes=ALL_SCOPES)
        names = producer_names(ttbar, "mt") | producer_names(ttbar, "global")
        self.assertIn("RenameMet", names)
        self.assertNotIn("GenBosonQuantities", names)
        self.assertNotIn("MetScopes", names)


class SMEntryPointGatingTest(unittest.TestCase):
    # module, era, sample, text the raised ValueError must name
    GATED = (
        ("sm_btag_efficiency_config", "2017", "ttbar", "does not support era '2017'"),
        ("sm_btag_efficiency_config", "2018", "data", "does not accept sample 'data'"),
        ("sm_config", "2022postEE", "ttbar", "does not support era '2022postEE'"),
    )

    def test_module_level_gates_fire_before_build_config(self):
        """``generate.run`` rejects an unsupported era/sample without building."""
        for module_name, era, sample, expected in self.GATED:
            with self.subTest(module=module_name, era=era, sample=sample):
                module = importlib.import_module(
                    f"analysis_configurations.bbtautau.{module_name}"
                )
                with mock.patch.object(
                    module, "build_config",
                    side_effect=AssertionError("must not be called"),
                ):
                    with self.assertRaisesRegex(ValueError, expected):
                        generate.run(FakeArgs(module_name, era, sample))


class NMSSMIsolationTest(unittest.TestCase):
    def test_nmssm_2018_keeps_legacy_jet_and_btag_path(self):
        """Every SM-only v15 switch is profile-gated, so NMSSM 2018 is untouched."""
        config = build("nmssm_config", "ttbar")
        params = config.config_parameters["global"]["nominal"]
        self.assertEqual(params["bjet_max_abs_eta"], 2.5)
        self.assertEqual(params["bjet_score_column"], "Jet_btagDeepFlavB")
        self.assertEqual(params["ak4jet_id_wp"], 2)
        self.assertEqual(params["ak4jet_id_file"], "DOES_NOT_EXIST")
        jet_id = find_producer(config, "global", "JetID").call
        self.assertIn("event::quantity::Rename", jet_id)

        mt, outs = producer_names(config, "mt"), output_names(config, "mt")
        self.assertIn("BJetShapeDeepJet_SF", mt)
        self.assertNotIn("StrictUParTBtagWeight", mt)
        self.assertIn("id_wgt_bjet", outs)
        self.assertFalse(any(o.startswith("btag_weight_upart") for o in outs))


@unittest.skipUnless(yaml, "PyYAML not installed in this interpreter")
class SMShiftInventoryTest(unittest.TestCase):
    def test_shift_inventory_covers_every_registered_sm_shift(self):
        """``systematics_sm_2018.yaml`` must account for every registered SM shift.

        The validator builds the SM configuration with ``shifts={"all"}`` over the
        full MC sample census and checks that every registered ``crown_shift`` is
        claimed by exactly one inventory entry, that no pattern is unused, and that
        the dynamic UParTAK4 variation keys expand against the pinned payload.
        """
        from analysis_configurations.bbtautau.scripts import (
            validate_systematics_inventory as validator,
        )
        ok, errors = validator.run(final_inference=False)
        self.assertTrue(ok, errors)


if __name__ == "__main__":
    unittest.main()
