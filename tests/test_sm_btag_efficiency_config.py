"""Contract for the payload-independent UParT probe-jet ntuple profile
(``sm_btag_efficiency_config``, 2018 UL NanoAOD v15, MC only).

Pins the behavior of ``SM_BTAG_EFFICIENCY_PROFILE``:

* it exports the four payload-independent probe-jet vectors (corrected pt,
  eta, hadron flavour, UParTAK4 B score);
* it strips the whole analysis b-jet layer -- the b-tag SF weight producer
  (+ ``id_wgt_bjet``), the b-tagged event filter, the selected bb pair
  (four-vectors, di-b-jet kinematics, gen-matched di-b-jet quantities), the
  b-jet multiplicity, and the tautau+bb combined quantities -- while keeping
  the shared object / trigger / tau-pair / JEC / JER surface and the nominal
  MC event weights;
* it is MC only (a ``data``/``embedding`` build raises) and 2018 only (any
  other era raises);
* crucially, it builds with its OWN (MC-only) ``AVAILABLE_SAMPLES`` as the
  sample-type universe -- the pre-existing unconditional ``data``/``embedding``
  rules and JER/JES shifts degrade gracefully on the reduced surface.

The NMSSM/SM-main byte-identity of the shared config is pinned by the
characterization suite (``test_nmssm_characterization``) and
``test_sm_main_config``; here we only assert the efficiency profile's own
surface.
"""
from copy import deepcopy
import unittest

from analysis_configurations.bbtautau import sm_btag_efficiency_config
from analysis_configurations.bbtautau.constants import SCOPES


def _build(sample, era="2018", scopes=("mt",), available=None):
    return sm_btag_efficiency_config.build_config(
        era,
        sample,
        list(scopes),
        {"none"},
        list(available) if available is not None
        else list(sm_btag_efficiency_config.AVAILABLE_SAMPLES),
        [era],
        SCOPES,
    )


def _top_level_producer_names(config, scope):
    return {p.name for p in config.producers[scope]}


def _all_producer_names(config, scope):
    """Top-level producers plus one level of unpacked subproducers."""
    names = set()
    for producer in config.producers[scope]:
        names.add(producer.name)
        subproducers = getattr(producer, "producers", None)
        if isinstance(subproducers, dict):
            for sub in subproducers.get(scope, []):
                names.add(sub.name)
    return names


def _output_names(config, scope):
    return {q.get_leaf(shift="", scope=scope) for q in config.outputs[scope]}


def _generated_calls(config, scope, producer_name):
    """Generate calls on a copy so dynamic output groups stay test-local."""
    producer = deepcopy(
        next(p for p in config.producers[scope] if p.name == producer_name)
    )
    producer.output_group.shifts = {}
    producer.output_group.ignored_shifts = {}
    producer.output_group.quantities = []
    parameters = deepcopy(config.config_parameters[scope])
    return producer.writecalls(parameters, scope)


class SMBtagEfficiencyConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Built with the profile's OWN (MC-only) AVAILABLE_SAMPLES as the
        # sample universe -- this is the sample-surface fix in action.
        cls.cfg = _build("ttbar")
        cls.outs = _output_names(cls.cfg, "mt")
        cls.top = _top_level_producer_names(cls.cfg, "mt") | _top_level_producer_names(
            cls.cfg, "global"
        )
        cls.allp = _all_producer_names(cls.cfg, "mt") | _all_producer_names(
            cls.cfg, "global"
        )

    # -- probe-jet vectors -----------------------------------------------------

    def test_four_probe_outputs_present(self):
        for column in (
            "btag_probe_jet_pt",
            "btag_probe_jet_eta",
            "btag_probe_jet_hadron_flavour",
            "btag_probe_jet_upart",
        ):
            self.assertIn(column, self.outs)

    def test_probe_producer_group_scheduled(self):
        self.assertIn("BtagProbeJetVectors", self.top)
        self.assertIn("BtagProbeJetMask", self.allp)

    # -- b-tag / bb-pair layer fully stripped ----------------------------------

    def test_no_bbpair_producer_scheduled(self):
        offenders = {n for n in self.allp if "BBPair" in n}
        self.assertEqual(offenders, set(), f"bb-pair producers scheduled: {offenders}")

    def test_no_goodbbpairfilter_scheduled(self):
        self.assertNotIn("GoodBBPairFilter", self.allp)

    def test_no_btag_sf_producer_scheduled(self):
        for name in (
            "BJetShapeDeepJet_SF",
            "BJetShapePNet_SF",
            "BJetWPUParT_SF",
            "StrictUParTBtagWeight",
        ):
            self.assertNotIn(name, self.allp)

    def test_no_upart_weight_producer_scheduled(self):
        # No UParT-based b-tag SF / event-weight consumer. The probe-jet UParT
        # *score* writer (BtagProbeJetUParT) is the exported measurement input,
        # not a b-tag weight, so it is explicitly allowed.
        offenders = {
            n for n in self.allp if "UParT" in n and not n.startswith("BtagProbe")
        }
        self.assertEqual(
            offenders, set(), f"UParT-weight producers scheduled: {offenders}"
        )

    def test_no_btag_weight_or_bjet_outputs(self):
        self.assertNotIn("id_wgt_bjet", self.outs)
        self.assertNotIn("n_bjets", self.outs)
        self.assertFalse(
            any(o.startswith("btag_weight_upart") for o in self.outs),
            f"btag weight columns present: {sorted(self.outs)}",
        )

    def test_no_bbpair_or_tautaubb_outputs(self):
        for prefix in ("bpair", "genjet"):
            offenders = {o for o in self.outs if o.startswith(prefix)}
            self.assertEqual(offenders, set(), f"{prefix} outputs present: {offenders}")
        self.assertNotIn("mass_tautaubb", self.outs)
        self.assertNotIn("pt_tautaubb", self.outs)

    # -- kept surface (object / tau-pair / JEC / weights) ----------------------

    def test_nominal_weight_inputs_still_output(self):
        # pileup / LHE-scale / genWeight-derived nominal weights and the muon
        # ID+iso+trigger scale factors survive (only the b-tag SF is dropped).
        for column in (
            "puweight",
            "lhe_scale_weight",
            "genWeight",
            "id_wgt_mu_1",
            "iso_wgt_mu_1",
        ):
            self.assertIn(column, self.outs)
        self.assertIn("SingleMuTriggerSF", self.outs)

    def test_shared_object_and_taupair_surface_kept(self):
        # JEC/JER + jet selection + tau ID SF + the reduced ditau+MET group.
        # renamed upstream: JECSimulation -> JetEnergyCorrectionMC
        self.assertIn("JetEnergyCorrectionMC", self.top)
        self.assertIn("JetSelection", self.top)
        self.assertIn("TauIDSF", self.top)
        self.assertIn("DiTauPairMETQuantitiesNoBB", self.top)
        # nominal ditau+MET quantities survive; only tautau+bb is dropped.
        for column in ("mt_1", "mt_2", "pt_tautau", "mt_tot", "m_vis"):
            self.assertIn(column, self.outs)

    # -- MC-only / 2018-only gates ---------------------------------------------

    def test_data_build_raises_mc_only(self):
        with self.assertRaises(ValueError) as ctx:
            _build("data", available=list(sm_btag_efficiency_config.AVAILABLE_SAMPLES)
                   + ["data"])
        self.assertIn("MC only", str(ctx.exception))

    def test_embedding_build_raises_mc_only(self):
        with self.assertRaises(ValueError):
            _build(
                "embedding",
                available=list(sm_btag_efficiency_config.AVAILABLE_SAMPLES)
                + ["embedding"],
            )

    def test_era_2024_raises(self):
        with self.assertRaises(ValueError) as ctx:
            _build("ttbar", era="2024")
        self.assertIn("2018", str(ctx.exception))

    # -- sample-surface fix ----------------------------------------------------

    def test_builds_with_own_available_samples_universe(self):
        # The profile's own AVAILABLE_SAMPLES carries no data/embedding; the
        # unconditional data/embedding rules and JER/JES shifts must degrade
        # gracefully (this is exactly the universe setUpClass built with).
        cfg = _build("ttbar", available=sm_btag_efficiency_config.AVAILABLE_SAMPLES)
        self.assertIsNotNone(cfg)
        self.assertNotIn(
            "data", sm_btag_efficiency_config.AVAILABLE_SAMPLES
        )

    def test_probe_selection_parameters_staged(self):
        params = self.cfg.config_parameters["mt"]["nominal"]
        self.assertEqual(params["btag_probe_min_pt"], 20.0)
        self.assertEqual(params["btag_probe_max_abs_eta"], 2.4)
        self.assertEqual(params["btag_probe_min_delta_r"], 0.4)


class SMBtagEfficiencyDYWGenBosonScopeContractTest(unittest.TestCase):
    """Regression: DY/W gen-boson producers must have ``is_data`` in their scope.

    ``boson_corrections.GenBosonP4``/``GenVisBosonP4`` run in the analysis
    SCOPES (et/mt/tt/...) and their call templates reference ``{is_data}``. The
    framework's ``_set_sample_parameters`` only auto-injects ``is_${sampletype}``
    for types present in ``available_sample_types``; the MC-only efficiency
    profile drops ``data``/``embedding`` from its surface, so those flags are
    NOT auto-created and must be added manually to every scope in
    ``common_config.build_config`` -- not just the global scope. If they are
    added to the global scope only (the pre-fix bug), code generation for the
    DY/W executables fails with ``KeyError: 'is_data'`` when it tries to fill
    the ``{is_data}`` placeholder of a gen-boson producer in an analysis scope.

    This test pins the invariant with a fast proxy of the code-generation step:
    for every scope where a gen-boson producer is scheduled, ``is_data`` (and
    ``is_embedding``/``is_mc``) must be present in that scope's nominal config
    parameters.
    """

    GEN_BOSON_PRODUCERS = {"GenBosonQuantities", "GenBosonP4", "GenVisBosonP4"}

    def _scoped_gen_boson_scopes(self, cfg, scopes):
        """Return the subset of ``scopes`` where a gen-boson producer runs."""
        hit = []
        for scope in scopes:
            names = {p.name for p in cfg.producers.get(scope, [])}
            if names & self.GEN_BOSON_PRODUCERS:
                hit.append(scope)
        return hit

    def test_gen_boson_scheduled_for_dyw_in_analysis_scopes(self):
        for sample in ("dyjets", "wjets"):
            cfg = _build(sample, scopes=("et", "mt", "tt"))
            hit = self._scoped_gen_boson_scopes(cfg, ("et", "mt", "tt"))
            self.assertEqual(
                sorted(hit),
                ["et", "mt", "tt"],
                f"{sample}: gen-boson producers not scheduled in all analysis "
                f"scopes (got {sorted(hit)})",
            )

    def test_is_data_present_in_every_gen_boson_scope(self):
        for sample in ("dyjets", "wjets"):
            cfg = _build(sample, scopes=("et", "mt", "tt"))
            for scope in self._scoped_gen_boson_scopes(cfg, ("et", "mt", "tt")):
                nominal = cfg.config_parameters[scope]["nominal"]
                for flag in ("is_data", "is_embedding", "is_mc"):
                    self.assertIn(
                        flag,
                        nominal,
                        f"{sample}: '{flag}' missing from scope '{scope}' where a "
                        f"gen-boson producer (referencing '{{is_data}}') runs -- "
                        f"code generation would KeyError on it",
                    )

    def test_sample_flags_present_in_all_built_scopes(self):
        # The manual injection targets every configured scope, not just global.
        cfg = _build("dyjets", scopes=("et", "mt", "tt"))
        for scope in ("global", "et", "mt", "tt"):
            nominal = cfg.config_parameters[scope]["nominal"]
            self.assertIn("is_data", nominal)
            self.assertEqual(nominal["is_data"], False)
            self.assertEqual(nominal["is_mc"], True)


class SMBtagEfficiencyElectronTriggerSFTest(unittest.TestCase):
    """Run-2 2018 MC uses the TauAnalysis electron-trigger SF measurement.

    The Run-3 EGM ``Electron-HLT-SF`` correction is absent from the Run-2 UL
    ``electron.json.gz`` payload. TauAnalysis instead evaluates
    ``Trg32_Iso_pt_eta_bins`` from ``data/embedding/electron_2018UL.json.gz``
    for ordinary MC. Both SM profiles and NMSSM must use that producer in the
    2018 et scope and expose its ``trg_wgt_single_ele32`` column.
    """

    def test_efficiency_profile_et_uses_tau_analysis_ele32_sf(self):
        cfg = _build("ttbar", scopes=("et", "mt", "tt"))
        et = {p.name for p in cfg.producers["et"]}
        self.assertIn("ETGenerateSingleElectronTriggerSF_MC", et)
        self.assertNotIn("SingleEleTriggerSF", et)
        self.assertNotIn("SingleEleTriggerSFUnity", et)
        calls = _generated_calls(cfg, "et", "ETGenerateSingleElectronTriggerSF_MC")
        self.assertEqual(len(calls), 1)
        self.assertIn('"trg_wgt_single_ele32"', calls[0])
        self.assertIn('"data/embedding/electron_2018UL.json.gz"', calls[0])
        self.assertIn('"Trg32_Iso_pt_eta_bins"', calls[0])
        self.assertNotIn("trg_wgt_single_ele30", calls[0])

    def test_nmssm_2018_et_uses_tau_analysis_ele32_sf(self):
        from analysis_configurations.bbtautau import nmssm_config
        from analysis_configurations.bbtautau.constants import ERAS

        legacy = [
            "ggh_htautau", "ggh_hbb", "vbf_htautau", "vbf_hbb", "rem_htautau",
            "rem_hbb", "rem_hww", "rem_hzz", "rem_higgs", "hh4b", "hh2b2tau",
            "hh4v", "embedding", "embedding_mc", "singletop", "ttbar",
            "rem_ttbar", "diboson", "dyjets", "dyjets_madgraph",
            "dyjets_amcatnlo", "dyjets_amcatnlo_ll", "dyjets_amcatnlo_tt",
            "dyjets_powheg", "wjets", "wjets_madgraph", "wjets_amcatnlo",
            "data", "electroweak_boson", "nmssm_Ybb", "nmssm_Ytautau",
        ]
        cfg = nmssm_config.build_config(
            "2018", "ttbar", ["et"], {"none"}, legacy, ERAS, SCOPES,
        )
        et = {p.name for p in cfg.producers["et"]}
        self.assertIn("ETGenerateSingleElectronTriggerSF_MC", et)
        self.assertNotIn("SingleEleTriggerSF", et)
        self.assertNotIn("SingleEleTriggerSFUnity", et)
        self.assertEqual(
            cfg.config_parameters["et"]["nominal"]["singlelectron_trigger_sf_mc"],
            [
                {
                    "flagname": "trg_wgt_single_ele32",
                    "mc_trigger_sf": "Trg32_Iso_pt_eta_bins",
                    "mc_electron_trg_extrapolation": 1.0,
                }
            ],
        )

    def test_nmssm_2018_registers_tau_analysis_ele32_sf_shifts(self):
        from analysis_configurations.bbtautau import nmssm_config
        from analysis_configurations.bbtautau.constants import ERAS

        legacy = [
            "ggh_htautau", "ggh_hbb", "vbf_htautau", "vbf_hbb", "rem_htautau",
            "rem_hbb", "rem_hww", "rem_hzz", "rem_higgs", "hh4b", "hh2b2tau",
            "hh4v", "embedding", "embedding_mc", "singletop", "ttbar",
            "rem_ttbar", "diboson", "dyjets", "dyjets_madgraph",
            "dyjets_amcatnlo", "dyjets_amcatnlo_ll", "dyjets_amcatnlo_tt",
            "dyjets_powheg", "wjets", "wjets_madgraph", "wjets_amcatnlo",
            "data", "electroweak_boson", "nmssm_Ybb", "nmssm_Ytautau",
        ]
        cfg = nmssm_config.build_config(
            "2018", "ttbar", ["et"], {"all"}, legacy, ERAS, SCOPES,
        )
        shifts = set(cfg.shifts["et"])
        self.assertTrue(any("singleElectronTriggerSFUp" in shift for shift in shifts))
        self.assertTrue(any("singleElectronTriggerSFDown" in shift for shift in shifts))


if __name__ == "__main__":
    unittest.main()
