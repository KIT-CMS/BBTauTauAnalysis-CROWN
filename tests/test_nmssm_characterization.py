"""Characterization of the NMSSM configuration surface.

These tests freeze behavior that the SM/NMSSM common-core refactor must not
change: sample surface, truth mothers, LHE producer dispatch, b-tag path,
key outputs, and registered shifts.
"""
import unittest
from pathlib import Path

from analysis_configurations.bbtautau import nmssm_config
from analysis_configurations.bbtautau.constants import ERAS, SCOPES

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]

LEGACY_AVAILABLE_SAMPLES = [
    "ggh_htautau", "ggh_hbb", "vbf_htautau", "vbf_hbb", "rem_htautau",
    "rem_hbb", "rem_hww", "rem_hzz", "rem_higgs", "hh4b", "hh2b2tau",
    "hh4v", "embedding", "embedding_mc", "singletop", "ttbar", "rem_ttbar",
    "diboson", "dyjets", "dyjets_madgraph", "dyjets_amcatnlo",
    "dyjets_amcatnlo_ll", "dyjets_amcatnlo_tt", "dyjets_powheg", "wjets",
    "wjets_madgraph", "wjets_amcatnlo", "data", "electroweak_boson",
    "nmssm_Ybb", "nmssm_Ytautau",
]


def build_nmssm(sample, era="2018", scopes=("mt",), shifts=("none",)):
    return nmssm_config.build_config(
        era, sample, list(scopes), {s.lower() for s in shifts},
        LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES,
    )


def producer_names(config, scope):
    return {p.name for p in config.producers[scope]}


def output_names(config, scope):
    return {q.get_leaf(shift="", scope=scope) for q in config.outputs[scope]}


class NMSSMCharacterizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg_signal = build_nmssm("nmssm_Ybb")
        cls.cfg_ttbar = build_nmssm("ttbar")
        cls.cfg_data = build_nmssm("data")

    def test_legacy_sample_surface_is_unchanged(self):
        # The legacy list lives in generate.py before Task 4 and moves to
        # constants.py afterwards; the characterization anchors the SURFACE,
        # not the file.
        text = (ANALYSIS_ROOT / "generate.py").read_text() + (
            ANALYSIS_ROOT / "constants.py"
        ).read_text()
        for sample in LEGACY_AVAILABLE_SAMPLES:
            self.assertIn(f'"{sample}"', text)

    def test_truth_mother_pdgids(self):
        params = self.cfg_signal.config_parameters["mt"]["nominal"]
        self.assertEqual(params["bb_truegen_mother_pdgid"], 35)
        self.assertEqual(params["tautau_truegen_mother_pdgid"], 25)
        self.assertEqual(params["bb_truegen_daughter_1_pdgid"], 5)
        self.assertEqual(params["tautau_truegen_daughter_1_pdgid"], 15)

    def test_nmssm_signal_uses_special_lhe_producer(self):
        names = producer_names(self.cfg_signal, "global")
        self.assertIn("NMSSM_LHE_Scale_weight", names)
        self.assertNotIn("LHE_Scale_weight", names)

    def test_ttbar_uses_standard_lhe_producer(self):
        names = producer_names(self.cfg_ttbar, "global")
        self.assertIn("LHE_Scale_weight", names)
        self.assertNotIn("NMSSM_LHE_Scale_weight", names)

    def test_2018_btag_path(self):
        params = self.cfg_ttbar.config_parameters["global"]["nominal"]
        self.assertEqual(params["bjet_max_abs_eta"], 2.5)
        self.assertIn("Jet_btagDeepFlavB", str(params["bjet_score_column"]))

    def test_mass_tautaubb_is_an_output(self):
        self.assertIn("mass_tautaubb", output_names(self.cfg_ttbar, "mt"))

    def test_registered_shift_names_2018_signal(self):
        # Shift *registration* can only be observed by actually selecting
        # shifts at build time: with the class-level default shifts="none",
        # Configuration._is_valid_shift() rejects every shift, so add_shift()
        # never records anything in self.shifts, regardless of what the
        # config defines. Build a dedicated shifts="all" config here to
        # characterize which shift names the framework registers for the
        # 2018 NMSSM signal sample.
        cfg_signal_all_shifts = build_nmssm("nmssm_Ybb", shifts=("all",))
        shifts = set(cfg_signal_all_shifts.shifts["mt"])
        for expected in ("muRWeightUp", "muRWeightDown", "muFWeightUp",
                         "muFWeightDown", "jesUncHEMIssueUp", "jesUncHEMIssueDown"):
            self.assertTrue(any(expected in s for s in shifts),
                            f"{expected} not registered; got {sorted(shifts)[:20]}...")


if __name__ == "__main__":
    unittest.main()
