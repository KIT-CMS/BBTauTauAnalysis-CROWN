import unittest

from analysis_configurations.bbtautau.variations.bjet_tagging import (
    add_bjet_tagging_fixed_wp_shifts,
    add_bjet_tagging_shape_shifts,
)


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
    """Dummy producer class to simulate a producer for testing purposes."""

    def __init__(self, name, scopes):
        self.name = name
        self.scopes = scopes

        # Leave unneeded attributes empty
        self.call = None
        self.input = []
        self.output = []


class AddBJetTaggingFixedWPShiftsTest(unittest.TestCase):
    """
    Unit tests for the
    `variations.bjet_tagging.add_bjet_tagging_fixed_wp_shifts` function.
    """

    def setUp(self):
        # Set up dummy producers for testing
        self.fixed_wp_producer = DummyProducer(
            name="BJetWPUParT_SF",
            scopes=["et", "mt", "tt"],
        )

    def test_fixed_wp_adds_expected_shifts(self):
        """Test that fixed WP shifts add correlated bc uncertainties."""

        # Create a configuration and add fixed WP shifts
        configuration = CaptureConfiguration()
        add_bjet_tagging_fixed_wp_shifts(
            configuration,
            "2024",
            self.fixed_wp_producer,
        )
        shift_names = [s["shift"].shiftname for s in configuration.shifts]

        # List expected shifts
        shifts_expected = [
            f"{name}{direction}"
            for name in [
                "btagBCCorrelated",
                "btagLFCorrelated",
                "btagBC2024",
                "btagLF2024",
            ]
            for direction in ["Up", "Down"]
        ]

        # Check for correlated bc shifts (up and down)
        for shift_exp in shifts_expected:
            self.assertIn(
                f"__{shift_exp}",
                shift_names,
                f"Expected b jet tagging shift {shift_exp} not found",
            )

    def test_fixed_wp_excludes_samples_correctly(self):
        """Test that fixed WP shifts exclude data/embedding samples."""

        # Create a configuration and add fixed WP shifts
        configuration = CaptureConfiguration()
        add_bjet_tagging_fixed_wp_shifts(
            configuration,
            "2024",
            self.fixed_wp_producer,
        )

        expected_exclude = ["data", "embedding", "embedding_mc"]
        for shift_info in configuration.shifts:
            self.assertEqual(
                shift_info["exclude_samples"],
                expected_exclude,
                f"exclude_samples mismatch for shift {shift_info["shift"].shiftname}",
            )

    def test_shape_total_shift_count(self):
        """Test that WP-based shifts create the expected number of shifts."""

        # Create a configuration and add shape shifts
        configuration = CaptureConfiguration()
        add_bjet_tagging_fixed_wp_shifts(
            configuration,
            "2024",
            self.fixed_wp_producer,
        )

        # Expect (BC, LF) x (correlated, uncorrelated)
        # Total: 4 shifts, each with up and down variations
        expected_count = 8
        self.assertEqual(
            len(configuration.shifts),
            expected_count,
            f"Expected {expected_count} shifts, got {len(configuration.shifts)}",
        )


class AddBJetTaggingShapeShiftsTest(unittest.TestCase):
    """
    Unit tests for the
    `variations.bjet_tagging.add_bjet_tagging_shape_shifts` function.
    """

    def setUp(self):
        # Set up dummy producers for testing
        self.shape_producer = DummyProducer(
            name="BJetShapePNet_SF",
            scopes=["et", "mt", "tt"],
        )

    def test_shape_adds_expected_shifts(self):
        """Test that shape shifts add hf uncertainties."""

        # Create a configuration and add shape shifts
        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            self.shape_producer,
        )
        shift_names = [s["shift"].shiftname for s in configuration.shifts]

        # List expected shifts
        shifts_expected = [
            f"{name}{direction}"
            for name in [
                "btagHf",
                "btagLf",
                "btagHfstats1",
                "btagHfstats2",
                "btagLfstats1",
                "btagLfstats2",
                "btagCferr1",
                "btagCferr2",
                "btagCferr1",
                "btagCferr2",
            ]
            for direction in ["Up", "Down"]
        ]

        # Check for correlated bc shifts (up and down)
        for shift_exp in shifts_expected:
            self.assertIn(
                f"__{shift_exp}",
                shift_names,
                f"Expected b jet tagging shift {shift_exp} not found",
            )

    def test_shape_excludes_samples_correctly(self):
        """Test that shape shifts exclude data/embedding samples."""

        # Create a configuration and add shape shifts
        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            self.shape_producer,
        )

        # Check that all shifts have the expected exclude_samples list
        expected_exclude = sorted(["data", "embedding", "embedding_mc"])
        for shift_info in configuration.shifts:
            self.assertEqual(
                sorted(shift_info["exclude_samples"]),
                expected_exclude,
                f"exclude_samples mismatch for shift {shift_info["shift"].shiftname}",
            )

    def test_shape_total_shift_count(self):
        """Test that shape shifts create the expected number of shifts."""

        # Create a configuration and add shape shifts
        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            self.shape_producer,
        )

        # Expect
        # - 1 x HF, 1 x LF
        # - 2 x HFSTAT, 2 x LFSTAT
        # - 2 x CFERR
        # Total: 8 shifts, each with up and down variations
        expected_count = 16
        self.assertEqual(
            len(configuration.shifts),
            expected_count,
            f"Expected {expected_count} shifts, got {len(configuration.shifts)}",
        )


if __name__ == "__main__":
    unittest.main()
