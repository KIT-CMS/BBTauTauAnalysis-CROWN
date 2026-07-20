from pathlib import Path
import unittest


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


if __name__ == "__main__":
    unittest.main()
