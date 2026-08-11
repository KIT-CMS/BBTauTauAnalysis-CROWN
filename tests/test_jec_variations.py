from pathlib import Path
import unittest


from analysis_configurations.bbtautau.variations.jec import (
    add_jec_shifts,
    _add_jes_shift,
)


ANALYSIS_ROOT = Path(__file__).resolve().parent


class CaptureConfiguration:
    """
    Helper class to capture configuration calls for testing.
    Mimics the Configuration interface needed for testing.
    """

    def __init__(self):
        self.shifts = []
        self.calls = []

    def add_shift(self, shift, exclude_samples=None):
        self.shifts.append(
            {
                "shift": shift,
                "exclude_samples": exclude_samples,
            }
        )


class DummyProducer:

    def __init__(self, name, scopes):
        self.name = name
        self.scopes = scopes

        # Leave unneeded attributes empty
        self.call = None
        self.input = []
        self.output = []


class AddJECShiftsTest(unittest.TestCase):

    def setUp(self):
        # Set up dummy JEC producers for testing
        self.jec_producers = [
            DummyProducer(name="JECProducer1", scopes=["global",]),
            DummyProducer(name="JECProducer2", scopes=["global",]),
        ]

        # Set up dummy b jet tagging SF producer
        self.bjet_tagging_sf_producer = DummyProducer(
            name="BJetTaggingSFProducer",
            scopes=["et", "mt", "tt"],
        )

    def test_adds_expected_jes_and_jer_shifts(self):
        """Test that add_jec_shifts adds expected JES shifts."""

        # Create test config and add JEC shifts, get the shift names
        configuration = CaptureConfiguration()
        add_jec_shifts(
            configuration,
            "2024",
            self.jec_producers,
        )
        shift_names = [s["shift"].shiftname for s in configuration.shifts]

        # Check for expected JES sources (up and down, reduced scheme)
        names = [
            "FlavorQCD",
            "RelativeBal",
            "HF",
            "BBEC1",
            "EC2",
            "Absolute",
            "BBEC12024",
            "RelativeSample2024",
            "EC22024",
            "HF2024",
            "Absolute2024",
        ]
        expected_jes_sources = [
            f"jes{name}{direction}"
            for name in names
            for direction in ["Up", "Down"]
        ]

        # Check if all expected JES sources are present in the configuration
        # shifts
        for exp_name in expected_jes_sources:
            self.assertIn(
                f"__{exp_name}",
                shift_names,
                (
                    f"Expected JES source {exp_name} not found in "
                    + "configuration shifts"
                ),
            )

    def test_adds_expected_jer_shifts(self):
        """Test that add_jec_shifts adds expected JER shifts."""

        # Create test config and add JEC shifts
        configuration = CaptureConfiguration()
        add_jec_shifts(
            configuration,
            "2024",
            self.jec_producers,
        )
        shift_names = [s["shift"].shiftname for s in configuration.shifts]

        # Check if all expected JER sources are present in the configuration
        # shifts
        for direction in ["Up", "Down"]:
            self.assertIn(
                f"__jerUnc{direction}",
                shift_names,
                (
                    f"Expected JER source 'jerUnc{direction}' not found in "
                    + "configuration shifts"
                ),
            )

    def test_includes_hem_issue_in_2018(self):
        """
        Test that add_jec_shifts adds HEMIssue uncertainty in 2018.
        """

        # Create test config and add JEC shifts
        configuration = CaptureConfiguration()
        add_jec_shifts(
            configuration,
            "2018",
            self.jec_producers,
        )
        shift_names = [s["shift"].shiftname for s in configuration.shifts]

        # Check that HEM issue uncertainties have been added
        for direction in ["Up", "Down"]:
            self.assertIn(
                f"__jesHEMIssue{direction}",
                shift_names,
                (
                    f"Expected JES source jesHEMIssue{direction} not found in "
                    + "configuration shifts"
                ),
            )

    def test_excludes_hem_issue_in_not_2018(self):
        """
        Test that add_jec_shifts does not add HEMIssue uncertainty in eras
        other than 2018.
        """

        # Create test config and add JEC shifts
        configuration = CaptureConfiguration()
        add_jec_shifts(
            configuration,
            "2024",
            self.jec_producers,
        )
        shift_names = [s["shift"].shiftname for s in configuration.shifts]

        # Check that HEM issue uncertainties have been added
        for direction in ["Up", "Down"]:
            self.assertNotIn(
                f"__jesHEMIssue{direction}",
                shift_names,
                (
                    f"Unexpected JES source jesHEMIssue{direction} found in "
                    + "configuration shifts"
                ),
            )

    def test_excludes_samples_with_data(self):
        """Test that exclude_samples are correctly passed to add_shift."""

        # Create test config and add JEC shifts
        configuration = CaptureConfiguration()
        add_jec_shifts(
            configuration,
            "2024",
            self.jec_producers,
        )

        # All shifts should exclude data, embedding, and embedding_mc samples
        expected_exclude = ["data", "embedding", "embedding_mc"]

        # Check list of excluded samples for each shift
        for shift_info in configuration.shifts:
            self.assertEqual(
                shift_info["exclude_samples"],
                expected_exclude,
                (
                    "exclude_samples mismatch for shift "
                    + shift_info['shift'].shiftname
                ),
            )

    def test_absent_bjet_tagging_shifts(self):
        """
        Test that b jet tagging SF shifts are absent when
        `bjet_tagging_sf_producer` is not provided.
        """

        # Create test config and add JEC shifts
        configuration = CaptureConfiguration()
        add_jec_shifts(
            configuration,
            "2024",
            self.jec_producers,
        )

        # Check that shifts include bjet_sf_variation configuration
        has_bjet_config = False
        for shift_info in configuration.shifts:
            shift = shift_info["shift"]
            for scope_config in shift.shift_config.values():
                if "bjet_sf_variation" in scope_config:
                    has_bjet_config = True
                    break
        self.assertFalse(
            has_bjet_config,
            (
                "bjet tagging SF producer configuration found in shifts "
                + "although no producer has been provided",
            )
        )

    def test_present_bjet_tagging_shifts(self):
        """
        Test that b jet tagging SF are present in the shift configuration when
        `bjet_tagging_sf_producer` is provided.
        """

        # Create test config and add JEC shifts
        configuration = CaptureConfiguration()
        add_jec_shifts(
            configuration,
            "2024",
            self.jec_producers,
            bjet_tagging_sf_producer=self.bjet_tagging_sf_producer,
        )

        # Check that shifts include bjet_sf_variation configuration
        has_bjet_config = False
        for shift_info in configuration.shifts:
            shift = shift_info["shift"]
            for scope_config in shift.shift_config.values():
                if "bjet_sf_variation" in scope_config:
                    has_bjet_config = True
                    break
        self.assertTrue(
            has_bjet_config,
            "bjet tagging SF producer configuration not found in shifts",
        )

    def test_jec_producers_scope_consistency_check(self):
        """Test that inconsistent JEC producer scopes raise an error."""
        configuration = CaptureConfiguration()

        # Create test config and add JEC shifts
        jec_producers = self.jec_producers + [
            DummyProducer(name="JECProducer3", scopes=["et", "mt", "tt"])
        ]
        configuration = CaptureConfiguration()

        # Should raise ValueError due to inconsistent scopes
        with self.assertRaises(ValueError) as context:
            add_jec_shifts(configuration, "2024", jec_producers)

        # Check that the error message indicates inconsistent scope definitions
        self.assertIn(
            "not consistent in their scope definition",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
