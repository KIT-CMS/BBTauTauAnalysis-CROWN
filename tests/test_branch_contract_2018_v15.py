"""Network-marked branch-contract smoke test for the SM 2018 NanoAOD-v15 inputs.

Opens one registered HH (signal MC), one ttbar (background MC) and one Tau
(data) NanoAOD v15 file over xrootd and asserts the input-schema contract the
isolated SM 2018-v15 AK4-PUPPI jet path relies on:

* the AK4 PUPPI composition branches the reconstructed tight jet ID and the JEC
  factory read, plus the UParT b-tag branch, are present in every file;
* ``Jet_hadronFlavour`` is present in MC and absent in data;
* the legacy ``Jet_jetId`` / ``Jet_puId`` branches (dropped by v15 for the PUPPI
  collection) are absent everywhere;
* MC ``LHEScaleWeight`` has 9 entries per event (the SM profile keeps the
  standard 9-entry LHE producer for these samples).

The test is skipped unless ``TFF_NETWORK_TESTS`` is set (it needs xrootd and a
valid VOMS proxy). ``uproot`` is imported inside ``setUpClass`` so that the plain
``python3 -m unittest`` run used for the rest of the suite skips cleanly without
uproot installed; run it with the ``fake_factors`` interpreter, e.g.::

    export X509_USER_PROXY=/tmp/x509up_u$(id -u)
    TFF_NETWORK_TESTS=1 /work/sdaigler/forge/envs/fake_factors/bin/python \
        -m unittest \
        analysis_configurations.bbtautau.tests.test_branch_contract_2018_v15 -v
"""
import json
import os
import unittest
from pathlib import Path

SAMPLE_DB_2018 = Path(
    "/work/sdaigler/bbtautau/KingMaker/sample_database/nanoAOD_v15/2018"
)

# AK4 PUPPI composition branches read by the SM 2018-v15 jet path: the nine
# inputs of JetIDTight2018PuppiV15 plus the raw kinematics/area/rawFactor the
# JEC factory consumes.
JET_COMPOSITION_BRANCHES = {
    "Jet_pt",
    "Jet_eta",
    "Jet_phi",
    "Jet_mass",
    "Jet_area",
    "Jet_rawFactor",
    "Jet_neHEF",
    "Jet_neEmEF",
    "Jet_chHEF",
    "Jet_chEmEF",
    "Jet_muEF",
    "Jet_nConstituents",
    "Jet_chMultiplicity",
    "Jet_neMultiplicity",
}
UPART_BTAG_BRANCH = "Jet_btagUParTAK4B"
# Legacy branches v15 no longer ships for the (PUPPI) Jet collection.
LEGACY_JET_ID_BRANCHES = {"Jet_jetId", "Jet_puId"}


def _first_registered_file(type_dir, name_filter=None):
    """Return the first xrootd file URL from the first matching filelist JSON."""
    directory = SAMPLE_DB_2018 / type_dir
    candidates = sorted(directory.glob("*.json"))
    if name_filter is not None:
        candidates = [j for j in candidates if name_filter(j.name)]
    for json_path in candidates:
        meta = json.loads(json_path.read_text())
        filelist = meta.get("filelist") or []
        if filelist:
            return filelist[0]
    raise FileNotFoundError(
        f"No registered file found under {directory} (filter={name_filter})"
    )


@unittest.skipUnless(
    os.environ.get("TFF_NETWORK_TESTS"),
    "needs xrootd + VOMS proxy (set TFF_NETWORK_TESTS=1)",
)
class BranchContract2018V15Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import uproot  # imported here so the plain-python3 skip fires cleanly

        cls.uproot = uproot
        cls.urls = {
            "hh": _first_registered_file("hh2b2tau"),
            "ttbar": _first_registered_file(
                "ttbar", lambda n: "SemiLeptonic" in n
            ),
            "data": _first_registered_file(
                "data", lambda n: n.startswith("Tau_")
            ),
        }
        cls.events = {
            label: cls._open_events(url) for label, url in cls.urls.items()
        }
        cls.branches = {
            label: set(events.keys()) for label, events in cls.events.items()
        }

    @classmethod
    def _open_events(cls, url, retries=1):
        """Open the Events tree, retrying once on a transient xrootd failure."""
        last_error = None
        for _ in range(retries + 1):
            try:
                handle = cls.uproot.open(
                    url, timeout=120, num_workers=1
                )
                return handle["Events"]
            except Exception as error:  # noqa: BLE001 - xrootd can be flaky
                last_error = error
        raise last_error

    def test_composition_and_btag_present_everywhere(self):
        required = JET_COMPOSITION_BRANCHES | {UPART_BTAG_BRANCH}
        for label, branches in self.branches.items():
            missing = required - branches
            self.assertEqual(
                missing, set(), f"{label}: missing input branches {missing}"
            )

    def test_hadron_flavour_present_in_mc_absent_in_data(self):
        self.assertIn("Jet_hadronFlavour", self.branches["hh"])
        self.assertIn("Jet_hadronFlavour", self.branches["ttbar"])
        self.assertNotIn("Jet_hadronFlavour", self.branches["data"])

    def test_legacy_jet_id_branches_absent_everywhere(self):
        for label, branches in self.branches.items():
            present = LEGACY_JET_ID_BRANCHES & branches
            self.assertEqual(
                present, set(), f"{label}: unexpected legacy branches {present}"
            )

    def test_mc_lhe_scale_weight_has_nine_entries(self):
        for label in ("hh", "ttbar"):
            weights = self.events[label]["LHEScaleWeight"].array(entry_stop=1)
            self.assertEqual(
                len(weights[0]),
                9,
                f"{label}: expected 9 LHEScaleWeight entries",
            )


if __name__ == "__main__":
    unittest.main()
