from pathlib import Path
import unittest
from itertools import product
import os
import re
import sys

from analysis_configurations.bbtautau.nmssm_config import build_config
from analysis_configurations.bbtautau.constants import ERAS_RUN3, SCOPES


CROWN_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(CROWN_ROOT)
ANALYSIS_ROOT = CROWN_ROOT / "analysis_configurations" / "bbtautau"
BUILD_SCRIPTS = [
    ANALYSIS_ROOT / "build_scripts" / "test_build_2018.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2022preEE.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2022postEE.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2023preBPix.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2023postBPix.sh",
    ANALYSIS_ROOT / "build_scripts" / "test_build_2024.sh",
]


def collect_correction_files(configuration):
    correction_files = []
    for parameters in configuration.config_parameters.values():
        for value in parameters["nominal"].values():
            if isinstance(value, str) and value.startswith("/cvmfs"):
                correction_files.append(value)
    return correction_files


def get_correction_version(correction_file):
    return os.path.basename(os.path.dirname(correction_file))

def get_latest_correction_version(correction_file):
    changes_file = os.path.join(
        os.path.dirname(os.path.dirname(correction_file)),
        "latest",
        "changes.md",
    )
    with open(changes_file, "r") as f:
        content = f.read()
    m = re.search(r"^## Changes:\s(.+)\s\(", content)
    if m is None:
        raise ValueError(f"Could not extract latest version from {changes_file}")
    return m.group(1)


class CorrectionVersionTest(unittest.TestCase):

    def setUp(self):
        eras = ["2018"] + ERAS_RUN3
        available_scopes = SCOPES
        samples = [
            "data",
            "ttbar",
            "dyjets_amcatnlo",
            "nmssm_Ybb",
            "nmssm_Ytautau",
        ]
        available_samples = [
            "ggh_htautau",
            "ggh_hbb",
            "vbf_htautau",
            "vbf_hbb",
            "rem_htautau",
            "rem_hbb",
            "rem_hww",
            "rem_hzz",
            "rem_higgs",
            "higgs",
            "hh4b",
            "hh2b2tau",
            "hh4v",
            "embedding",
            "embedding_mc",
            "singletop",
            "ttbar",
            "rem_ttbar",
            "diboson",
            "dyjets",
            "dyjets_madgraph",
            "dyjets_amcatnlo",
            "dyjets_amcatnlo_ll",
            "dyjets_amcatnlo_tt",
            "dyjets_powheg",
            "wjets",
            "wjets_madgraph",
            "wjets_amcatnlo",
            "data",
            "electroweak_boson",
            "nmssm_Ybb",
            "nmssm_Ytautau",
        ]
        configurations = {
            build_config(
                era,
                sample,
                available_scopes,
                ["none"],
                available_samples,
                eras,
                available_scopes,
            )
            for era, sample in product(eras, samples)
        }
        self.correction_files = set()
        for configuration in configurations:
            self.correction_files |= set(collect_correction_files(configuration))

    def test_correction_version(self):
        for correction_file in self.correction_files:
            with self.subTest(correction_file=correction_file):
                self.assertEqual(
                    get_correction_version(correction_file),
                    get_latest_correction_version(correction_file),
                )


if __name__ == "__main__":
    unittest.main()
