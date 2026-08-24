"""SM 2018-UL NanoAOD-v15 config contracts, and the NMSSM path they must not disturb.

Each test here guards a value that would otherwise regress silently into wrong
physics or a broken grid job:

* the truth-gen mothers the SM signal pair is built from (a lost
  ``SampleModifier`` key falls back to ``-1`` and yields garbage truth pairs);
* the pinned 2018-v15 UParTAK4 b-tag wiring -- discriminant column, acceptance,
  medium working point read from the payload, and the comb/light SF correction
  split (swapping the two applies heavy-flavour SFs to light jets);
* the per-variation weight columns, which must match exactly what
  ``btag_payloads.discover_upart_variations`` finds in the pinned payload;
* the five WP thresholds baked into the strict consumer's call (they cannot
  travel as a config parameter, so nothing else cross-checks them);
* the AK4-PUPPI jet-ID and electron-scale wiring that is SM-profile-only;
* the DY/W gen-boson + recoil treatment on the merged sample names;
* and, in ``NMSSMIsolationTest``, that none of the above leaked into NMSSM.

Parameter lookups follow ``config_parameters[scope]["nominal"]``: the b-tag
selection and jet parameters live in the ``global`` scope, the SF payload
parameters in the analysis scopes.
"""
import unittest

from analysis_configurations.bbtautau import btag_payloads
from analysis_configurations.bbtautau.tests.helpers import (
    all_producer_names,
    build_nmssm,
    build_sm,
    output_names,
    producer_names,
)

try:
    import yaml  # noqa: F401  -- only probed; the validator imports it itself

    _HAS_YAML = True
except ImportError:  # pragma: no cover
    _HAS_YAML = False


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
    keys = (variations["UParTAK4_comb"] | variations["UParTAK4_light"]) - {"central"}
    return {"btag_weight_upart"} | {f"btag_weight_upart_{key}" for key in keys}


class SMMainConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg_sig = build_sm("hh2b2tau")
        cls.cfg_tt = build_sm("ttbar")

    def test_truth_mothers_and_lhe_producer_for_sm_signal(self):
        params = self.cfg_sig.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bb_truegen_mother_pdgid"], 25)
        self.assertEqual(params["tautau_truegen_mother_pdgid"], 25)
        # SM keeps the standard 9-entry LHE producer for hh2b2tau.
        names = producer_names(self.cfg_sig, "global")
        self.assertIn("LHE_Scale_weight", names)
        self.assertNotIn("NMSSM_LHE_Scale_weight", names)

    def test_upart_btag_path_2018(self):
        params = self.cfg_tt.config_parameters["global"]["nominal"]
        self.assertEqual(params["bjet_max_abs_eta"], 2.4)
        self.assertIn("Jet_btagUParTAK4B", str(params["bjet_score_column"]))
        wps = btag_payloads.load_upart_wps(btag_payloads.PINNED_BTV_2018_V15)
        self.assertEqual(params["bjet_min_score"], wps["M"])

        # The heavy-flavour and light-flavour SF corrections must not be
        # swapped: that would apply comb SFs to light jets and vice versa.
        sf = self.cfg_tt.config_parameters["mt"]["nominal"]
        self.assertEqual(sf["bjet_sf_file"], btag_payloads.PINNED_BTV_2018_V15)
        self.assertEqual(sf["bjet_sf_bc_name"], "UParTAK4_comb")
        self.assertEqual(sf["bjet_sf_lf_name"], "UParTAK4_light")

    def test_upart_weight_variation_columns_match_discovery(self):
        outs = output_names(self.cfg_tt, "mt")
        actual = {o for o in outs if o.startswith("btag_weight_upart")}
        self.assertEqual(actual, _expected_upart_weight_columns())
        self.assertIn("btag_eff_pt_clamped_njets", outs)

    def test_upart_wp_thresholds_baked_into_consumer_call(self):
        # The five WP thresholds are baked (tightest -> loosest) into the
        # weight producers' calls via {vec_open}/{vec_close}, not a config
        # parameter (a std::vector<float> literal cannot survive CROWN's format
        # passes as a parameter value), so nothing else cross-checks them.
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

    def test_efficiency_lookup_keys_on_the_samples_own_name(self):
        # The SM path keys the efficiency lookup on the sample's OWN name (no
        # legacy hh2b2tau -> ggh_htautau aliasing), and reads the per-channel
        # payload shipped under the profile's payload directory.
        params = self.cfg_sig.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bjet_eff_sample_type"], "hh2b2tau")
        self.assertEqual(
            self.cfg_tt.config_parameters["mt"]["nominal"]["bjet_eff_sample_type"],
            "ttbar",
        )
        self.assertIn(
            "payloads/btagging_efficiencies/upart/2018/btag_efficiency_mt.json.gz",
            str(params["bjet_eff_file"]),
        )

    def test_sm_dyw_recoil_wiring(self):
        # The merged dyjets/wjets names get the gen-boson four-vector and the
        # intact recoil-correction group (MetScopes); everything else gets the
        # "no recoil correction" path (RenameMet). Zpt stays off for 2018.
        for sample in ("dyjets", "wjets"):
            with self.subTest(sample=sample):
                cfg = build_sm(sample)
                names = producer_names(cfg, "mt") | producer_names(cfg, "global")
                self.assertIn("GenBosonQuantities", names)
                self.assertIn("MetScopes", names)
                self.assertNotIn("RenameMet", names)
                self.assertNotIn("ZPtReweighting", names)

        names_tt = producer_names(self.cfg_tt, "mt") | producer_names(
            self.cfg_tt, "global"
        )
        self.assertIn("RenameMet", names_tt)
        self.assertNotIn("GenBosonQuantities", names_tt)
        self.assertNotIn("MetScopes", names_tt)

    def test_sm_v15_jet_and_electron_wiring(self):
        # SM-profile-only: the reconstructed 2018 UL PUPPI tight jet ID (a
        # member of AuxJetCollectionQuantities) replaces the v9 Jet_jetId
        # rename, and the electron scale comes from the pinned v15 EGM payload.
        nested = all_producer_names(self.cfg_tt, "global")
        top = producer_names(self.cfg_tt, "global")
        self.assertIn("AuxJetCollectionQuantities", top)
        self.assertIn("JetIDTight2018PuppiV15", nested)
        self.assertNotIn("JetID", nested)  # the v9 rename producer
        self.assertIn("ElectronPtCorrectionMCRun3", top)
        self.assertIn(
            "EGM/Run2-2018-UL-NanoAODv15/2025-12-05",
            str(self.cfg_tt.config_parameters["global"]["nominal"]["ele_es_file"]),
        )


class NMSSMIsolationTest(unittest.TestCase):
    """The SM 2018-v15 additions must not leak into the NMSSM path.

    ``nmssm_config.py`` and both SM entry points share ``common_config.py``, so
    every SM-only switch is profile-gated. These three tests build the NMSSM
    2018 configuration and assert the legacy surface is untouched.
    """

    @classmethod
    def setUpClass(cls):
        cls.cfg_signal = build_nmssm("nmssm_Ybb")
        cls.cfg_ttbar = build_nmssm("ttbar")

    def test_nmssm_crossed_truth_mothers(self):
        # Y -> bb (35) with H -> tautau (25) -- crossed relative to SM's 25/25.
        params = self.cfg_signal.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bb_truegen_mother_pdgid"], 35)
        self.assertEqual(params["tautau_truegen_mother_pdgid"], 25)
        self.assertEqual(params["bb_truegen_daughter_1_pdgid"], 5)
        self.assertEqual(params["tautau_truegen_daughter_1_pdgid"], 15)

    def test_nmssm_lhe_producer_dispatch(self):
        signal = producer_names(self.cfg_signal, "global")
        self.assertIn("NMSSM_LHE_Scale_weight", signal)
        self.assertNotIn("LHE_Scale_weight", signal)
        background = producer_names(self.cfg_ttbar, "global")
        self.assertIn("LHE_Scale_weight", background)
        self.assertNotIn("NMSSM_LHE_Scale_weight", background)

    def test_nmssm_2018_keeps_legacy_jet_and_btag_path(self):
        params = self.cfg_ttbar.config_parameters["global"]["nominal"]
        self.assertEqual(params["bjet_max_abs_eta"], 2.5)
        self.assertIn("Jet_btagDeepFlavB", str(params["bjet_score_column"]))
        self.assertEqual(params["ak4jet_id_wp"], 2)  # v9 Jet_jetId working point

        nested = all_producer_names(self.cfg_ttbar, "global")
        self.assertIn("JetID", nested)  # the v9 rename producer
        self.assertNotIn("JetIDTight2018PuppiV15", nested)

        mt = producer_names(self.cfg_ttbar, "mt")
        outs = output_names(self.cfg_ttbar, "mt")
        self.assertIn("BJetShapeDeepJet_SF", mt)
        self.assertNotIn("StrictUParTBtagWeight", mt)
        self.assertIn("id_wgt_bjet", outs)
        self.assertFalse(any(o.startswith("btag_weight_upart") for o in outs))


@unittest.skipUnless(_HAS_YAML, "PyYAML not installed in this interpreter")
class SMShiftInventoryTest(unittest.TestCase):
    """``systematics_sm_2018.yaml`` must account for every registered SM shift.

    ``scripts/validate_systematics_inventory.py`` builds the SM configuration
    with ``shifts={"all"}`` across the full MC sample census and checks that
    every registered ``crown_shift`` name is claimed by exactly one inventory
    entry, that no inventory pattern is unused, and that the dynamic UParTAK4
    variation keys expand against the pinned payload. Running it here is the
    only shifts=all build in the suite.
    """

    def test_shift_inventory_covers_every_registered_sm_shift(self):
        from analysis_configurations.bbtautau.scripts import (
            validate_systematics_inventory as validator,
        )

        ok, errors = validator.run(final_inference=False)
        self.assertTrue(ok, errors)


if __name__ == "__main__":
    unittest.main()
