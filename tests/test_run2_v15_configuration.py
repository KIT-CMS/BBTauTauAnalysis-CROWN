from pathlib import Path
import unittest

from analysis_configurations.bbtautau.producers import taus
from analysis_configurations.bbtautau.tau_triggersetup import add_diTauTriggerSetup


CROWN_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = CROWN_ROOT / "analysis_configurations" / "bbtautau"
BUILD_SCRIPTS = [
    ANALYSIS_ROOT / "build_scripts" / "test_build_2018.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2022preEE.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2022postEE.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2023preBPix.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2023postBPix.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2024.sh",
]


class CaptureConfiguration:
    def __init__(self):
        self.calls = []

    def add_config_parameters(self, scopes, parameters):
        self.calls.append((scopes, parameters))


def get_double_eletau_trigger_modifier():
    configuration = CaptureConfiguration()
    add_diTauTriggerSetup(configuration)
    for _, parameters in configuration.calls:
        if "double_eletau_trigger" in parameters:
            return parameters["double_eletau_trigger"]
    raise AssertionError("double_eletau_trigger was not configured")


class Run2NanoAODv15ConfigurationTest(unittest.TestCase):
    def test_analysis_identity_is_bbtautau(self):
        generate = (ANALYSIS_ROOT / "generate.py").read_text()
        generate_friends = (ANALYSIS_ROOT / "generate_friends.py").read_text()
        init_script = (CROWN_ROOT / "init.sh").read_text()

        self.assertIn('analysis_name = "bbtautau"', generate)
        self.assertIn('analysis_name = "bbtautau"', generate_friends)
        for script in BUILD_SCRIPTS:
            self.assertIn('local analysis="bbtautau"', script.read_text())
        self.assertIn('bbtautau)', init_script)
        self.assertIn(
            'REPO="git@github.com:KIT-CMS/BBTauTauAnalysis-CROWN.git"',
            init_script,
        )

        checked_text = "\n".join(
            [generate, generate_friends, init_script]
            + [script.read_text() for script in BUILD_SCRIPTS]
        )
        self.assertNotIn("xyh_bbtautau", checked_text)

    def test_tau_pt_correction_matches_current_crown_signature(self):
        call = taus.TauPtCorrectionMC.call
        ordered_arguments = [
            '"{tau_id_algorithm}"',
            '"{tau_ides_sf_vsjet_wp}"',
            '"{tau_ides_sf_vsele_wp}"',
            "{vec_open}{tight_tau_decay_modes}{vec_close}",
            '"{tau_elefake_es_DM0_barrel}"',
            '"{tau_elefake_es_DM1_barrel}"',
            '"{tau_elefake_es_DM0_endcap}"',
            '"{tau_elefake_es_DM1_endcap}"',
            '"{tau_mufake_es}"',
            '"{tau_ES_shift_DM0}"',
            '"{tau_ES_shift_DM1}"',
            '"{tau_ES_shift_DM10}"',
            '"{tau_ES_shift_DM11}"',
        ]
        for argument in ordered_arguments:
            self.assertIn(argument, call)
        positions = [call.index(argument) for argument in ordered_arguments]
        self.assertEqual(positions, sorted(positions))

    def test_2018_double_eletau_trigger_arguments_are_mapped_correctly(self):
        modifier = get_double_eletau_trigger_modifier()
        expected = [
            {
                "flagname": "trg_cross_ele24tau30_hps",
                "hlt_path": "HLT_Ele24_eta2p1_WPTight_Gsf_LooseChargedIsoPFTauHPS30_eta2p1_CrossL1",
                "p1_min_pt": 25,
                "p1_max_abs_eta": 2.5,
                "p1_filter_bit": 1,
                "p1_particle_id": 11,
                "p2_min_pt": 32,
                "p2_max_abs_eta": 2.1,
                "p2_filter_bit": -1,
                "p2_particle_id": 15,
                "match_max_delta_r": 0.4,
            },
            {
                "flagname": "trg_cross_ele24tau30",
                "hlt_path": "HLT_Ele24_eta2p1_WPTight_Gsf_LooseChargedIsoPFTau30_eta2p1_CrossL1",
                "p1_min_pt": 25,
                "p1_max_abs_eta": 2.5,
                "p1_filter_bit": 1,
                "p1_particle_id": 11,
                "p2_min_pt": 32,
                "p2_max_abs_eta": 2.1,
                "p2_filter_bit": 4,
                "p2_particle_id": 15,
                "match_max_delta_r": 0.4,
            },
        ]
        self.assertEqual(modifier.modifier_dict["2018"], expected)

    def test_run3_double_eletau_trigger_arguments_are_preserved(self):
        modifier = get_double_eletau_trigger_modifier()
        expected = [
            {
                "flagname": "trg_double_ele24tau30",
                "hlt_path": "HLT_Ele24_eta2p1_WPTight_Gsf_LooseDeepTauPFTauHPS30_eta2p1_CrossL1",
                "p1_min_pt": 26.0,
                "p1_max_abs_eta": 2.1,
                "p1_filter_bit": -1,
                "p1_particle_id": 11,
                "p2_min_pt": 32.0,
                "p2_max_abs_eta": 2.1,
                "p2_filter_bit": -1,
                "p2_particle_id": 15,
                "match_max_delta_r": 0.4,
            }
        ]
        for era in [
            "2022preEE",
            "2022postEE",
            "2023preBPix",
            "2023postBPix",
            "2024",
        ]:
            self.assertEqual(modifier.modifier_dict[era], expected)


if __name__ == "__main__":
    unittest.main()
