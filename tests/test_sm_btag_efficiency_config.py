"""Contract of the payload-independent UParT probe-jet profile (2018 UL v15, MC only).

The output contract is cross-repo: TauFakeFactors' ``configs/btag_efficiency/2018/*``
reads the four probe columns by exactly these names and needs the nominal weight and
ditau columns for its own selection, while the analysis b-jet layer must be gone. The
other two tests are crash gates -- a data/embedding build must be refused rather than
produce a meaningless measurement, and ``{is_data}`` must resolve in every scope that
references it. The shared SM/NMSSM surface is pinned by ``test_sm_main_config.py``.
"""
import unittest

from analysis_configurations.bbtautau.tests.helpers import (
    build, find_producer, output_names, producer_names,
)

# The complete input contract of the downstream measurement, plus the nominal MC
# weights and reduced ditau+MET quantities its preselection needs.
REQUIRED_COLUMNS = (
    "btag_probe_jet_pt", "btag_probe_jet_eta",
    "btag_probe_jet_hadron_flavour", "btag_probe_jet_upart",
    "puweight", "lhe_scale_weight", "genWeight", "id_wgt_mu_1", "iso_wgt_mu_1",
    "SingleMuTriggerSF", "mt_1", "mt_2", "pt_tautau", "mt_tot", "m_vis",
)


class SMBtagEfficiencyConfigTest(unittest.TestCase):
    def test_probe_jet_ntuple_contract(self):
        config = build("sm_btag_efficiency_config", "ttbar")
        outs = output_names(config, "mt")
        for column in REQUIRED_COLUMNS:
            with self.subTest(column=column):
                self.assertIn(column, outs)

        # the probe collection is the base b-jet acceptance cleaned of lepton
        # overlaps, with no discriminator cut of its own
        mask = find_producer(config, "mt", "BtagProbeJetMask")
        self.assertIn("physicsobject::CombineMasks", mask.call)
        self.assertEqual(
            [q.get_leaf(shift="", scope="mt") for q in mask.get_inputs("mt")],
            ["base_bjets_mask", "jet_overlap_veto_mask"],
        )

        # the b-tag SF and the selected-bb-pair layer really are dropped
        self.assertNotIn("StrictUParTBtagWeight", producer_names(config, "mt"))
        for column in ("id_wgt_bjet", "n_bjets", "mass_tautaubb"):
            with self.subTest(column=column):
                self.assertNotIn(column, outs)
        self.assertFalse(
            any(o.startswith("btag_weight_upart") for o in outs),
            f"b-tag weight columns present: {sorted(outs)}",
        )

    def test_non_mc_builds_are_refused(self):
        for sample in ("data", "embedding", "embedding_mc"):
            with self.subTest(sample=sample):
                with self.assertRaises(ValueError) as ctx:
                    build("sm_btag_efficiency_config", sample)
                self.assertIn("MC only", str(ctx.exception))

    def test_sample_flags_present_in_every_scope(self):
        # boson_corrections.GenBosonP4/GenVisBosonP4 run in the analysis scopes
        # and reference {is_data}; without the flag code generation dies.
        for sample in ("dyjets", "wjets"):
            with self.subTest(sample=sample):
                config = build(
                    "sm_btag_efficiency_config", sample, scopes=("et", "mt", "tt")
                )
                for scope in ("global", "et", "mt", "tt"):
                    nominal = config.config_parameters[scope]["nominal"]
                    for flag in ("is_data", "is_embedding"):
                        self.assertIn(
                            flag, nominal,
                            f"{sample}: '{flag}' missing from scope '{scope}'",
                        )
                    self.assertEqual(nominal["is_data"], False)
                self.assertIn("GenBosonQuantities", producer_names(config, "mt"))


if __name__ == "__main__":
    unittest.main()
