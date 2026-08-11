import unittest
from itertools import product
import os
import re

from analysis_configurations.bbtautau.nmssm_config import build_config
from analysis_configurations.bbtautau.constants import ERAS_RUN2, ERAS_RUN3, SCOPES


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
    correction_versions = []
    for correction_version in os.listdir(
        os.path.dirname(os.path.dirname(correction_file)),
    ):
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", correction_version)
        if m is None:
            continue
        correction_versions.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    newest_correction = sorted(correction_versions)[-1]
    return f"{newest_correction[0]:04d}-{newest_correction[1]:02d}-{newest_correction[2]:02d}"


class CorrectionVersionTest(unittest.TestCase):

    def setUp(self):
        eras = ERAS_RUN2 + ERAS_RUN3
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
