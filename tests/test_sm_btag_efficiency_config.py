"""Contract for the payload-independent UParT probe-jet ntuple profile
(``sm_btag_efficiency_config``, 2018 UL NanoAOD v15, MC only).

The four kept surface tests are cross-repo contracts: TauFakeFactors'
``configs/btag_efficiency/2018/*`` reads the four probe columns by exactly
these names, applies the probe acceptance to the same numbers, and needs the
nominal weight and ditau columns for its own selection. The remaining two are
crash gates -- a ``data``/``embedding`` build must be refused rather than
produce a meaningless measurement, and the sample flags must exist in every
scope where a producer references ``{is_data}``, or code generation dies with a
``KeyError``.

The shared configuration surface (SM b-tag path, NMSSM isolation) is pinned by
``test_sm_main_config.py``; here we only assert the efficiency profile's own.
"""
import unittest

from analysis_configurations.bbtautau import sm_btag_efficiency_config
from analysis_configurations.bbtautau.tests.helpers import (
    build_sm_btag_eff,
    output_names,
    producer_names,
)


class SMBtagEfficiencyConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Built with the profile's OWN (MC-only) AVAILABLE_SAMPLES as the
        # sample universe: the pre-existing unconditional data/embedding rules
        # and the JER/JES shifts must degrade gracefully on that reduced
        # surface.
        cls.cfg = build_sm_btag_eff("ttbar")
        cls.outs = output_names(cls.cfg, "mt")

    def test_four_probe_outputs_present(self):
        # The complete input contract of the downstream TauFakeFactors
        # measurement (jet_pt/eta/flavor/btag_column in its config).
        for column in (
            "btag_probe_jet_pt",
            "btag_probe_jet_eta",
            "btag_probe_jet_hadron_flavour",
            "btag_probe_jet_upart",
        ):
            self.assertIn(column, self.outs)

    def test_probe_selection_parameters_staged(self):
        params = self.cfg.config_parameters["mt"]["nominal"]
        self.assertEqual(params["btag_probe_min_pt"], 20.0)
        self.assertEqual(params["btag_probe_max_abs_eta"], 2.4)
        self.assertEqual(params["btag_probe_min_delta_r"], 0.4)

    def test_columns_the_downstream_preselection_needs(self):
        # Nominal MC event weights and the reduced ditau+MET quantities survive
        # (only the b-tag SF and the tautau+bb layer are dropped).
        for column in (
            "puweight",
            "lhe_scale_weight",
            "genWeight",
            "id_wgt_mu_1",
            "iso_wgt_mu_1",
            "SingleMuTriggerSF",
            "mt_1",
            "mt_2",
            "pt_tautau",
            "mt_tot",
            "m_vis",
        ):
            self.assertIn(column, self.outs)
        # ... and the b-tag weight / bb-pair layer really is gone.
        self.assertNotIn("id_wgt_bjet", self.outs)
        self.assertNotIn("n_bjets", self.outs)
        self.assertNotIn("mass_tautaubb", self.outs)
        self.assertFalse(
            any(o.startswith("btag_weight_upart") for o in self.outs),
            f"b-tag weight columns present: {sorted(self.outs)}",
        )

    def test_non_mc_builds_are_refused(self):
        for sample in ("data", "embedding", "embedding_mc"):
            with self.subTest(sample=sample):
                with self.assertRaises(ValueError) as ctx:
                    build_sm_btag_eff(
                        sample,
                        available=list(sm_btag_efficiency_config.AVAILABLE_SAMPLES)
                        + [sample],
                    )
                self.assertIn("MC only", str(ctx.exception))

    def test_sample_flags_present_in_every_scope(self):
        # ``boson_corrections.GenBosonP4``/``GenVisBosonP4`` run in the analysis
        # scopes and their call templates reference ``{is_data}``. The
        # framework only auto-injects ``is_${sampletype}`` for types present in
        # ``available_sample_types``, and this MC-only profile drops
        # data/embedding from its surface -- so the flags must be added
        # manually to EVERY configured scope, not just the global one. Adding
        # them to global only (the pre-fix bug) makes code generation for the
        # DY/W executables fail with ``KeyError: 'is_data'``.
        for sample in ("dyjets", "wjets"):
            with self.subTest(sample=sample):
                cfg = build_sm_btag_eff(sample, scopes=("et", "mt", "tt"))
                for scope in ("global", "et", "mt", "tt"):
                    nominal = cfg.config_parameters[scope]["nominal"]
                    for flag in ("is_data", "is_embedding", "is_mc"):
                        self.assertIn(
                            flag,
                            nominal,
                            f"{sample}: '{flag}' missing from scope '{scope}'",
                        )
                    self.assertEqual(nominal["is_data"], False)
                    self.assertEqual(nominal["is_mc"], True)
                self.assertIn("GenBosonQuantities", producer_names(cfg, "mt"))

    def test_et_uses_the_tau_analysis_ele32_trigger_sf(self):
        # The Run-3 EGM ``Electron-HLT-SF`` correction is absent from the Run-2
        # UL ``electron.json.gz`` payload, so 2018 MC evaluates TauAnalysis'
        # ``Trg32_Iso_pt_eta_bins`` from ``electron_2018UL.json.gz`` instead.
        cfg = build_sm_btag_eff("ttbar", scopes=("et",))
        et = producer_names(cfg, "et")
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


if __name__ == "__main__":
    unittest.main()
