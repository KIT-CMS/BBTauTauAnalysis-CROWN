import unittest

from analysis_configurations.bbtautau.variations.met import (
    add_unclustered_energy_shifts,
    add_recoil_calibration_shifts,
)


class CaptureConfiguration:
    """
    Helper class to capture configuration calls for testing.
    Mimics the Configuration interface needed for testing.
    """

    def __init__(self):
        self.shifts = []
        self.calls = []

    def add_shift(self, shift, exclude_samples=None, samples=None):
        self.shifts.append(
            {
                "shift": shift,
                "exclude_samples": exclude_samples,
                "samples": samples,
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


class AddUnclusteredEnergyShiftsTest(unittest.TestCase):
    """
    Unit tests for the
    `variations.met.add_unclustered_energy_shifts` function.
    """

    def test_unclustered_energy_adds_expected_shifts(self):
        """Test that unclustered energy shifts add the expected shifts."""

        # Create a configuration and add unclustered energy shifts
        configuration = CaptureConfiguration()
        add_unclustered_energy_shifts(
            configuration,
            "2024",
        )
        shift_names = [s["shift"].shiftname for s in configuration.shifts]

        # Validate that the expected shifts are available
        for direction in ["Up", "Down"]:
            shift_exp = f"CMS_scale_met_unclustered_energy_2024{direction}"
            self.assertIn(
                f"__{shift_exp}",
                shift_names,
                f"Expected shift {shift_exp} not found",
            )

    def test_excludes_samples_correctly(self):
        """Test that fixed WP shifts exclude data/embedding samples."""

        # Create a configuration and add fixed WP shifts
        configuration = CaptureConfiguration()
        add_unclustered_energy_shifts(
            configuration,
            "2024",
        )

        expected_exclude = ["data", "embedding", "embedding_mc"]
        for shift_info in configuration.shifts:
            self.assertEqual(
                shift_info["exclude_samples"],
                expected_exclude,
                f"exclude_samples mismatch for shift {shift_info["shift"].shiftname}",
            )

    def test_total_shift_count(self):
        """Test that function creates the expected number of shifts."""

        # Create a configuration and add shape shifts
        configuration = CaptureConfiguration()
        add_unclustered_energy_shifts(
            configuration,
            "2024",
        )

        # Expect one shift for each direction (Up, Down)
        expected_count = 2
        self.assertEqual(
            len(configuration.shifts),
            expected_count,
            f"Expected {expected_count} shifts, got {len(configuration.shifts)}",
        )


class AddRecoilCalibrationShiftsTest(unittest.TestCase):
    """
    Unit tests for the
    `variations.met.add_recoil_calibration_shifts` function.
    """

    def setUp(self):
        # Create a dummy producer for testing
        self.recoil_calibration_producer = DummyProducer(
            name="RecoilCalibrationProducer",
            scopes=["et", "mt", "tt", "em"],
        )

        # Example samples for testing
        self.samples = ["dyjets_amcatnlo", "wjets_amcatnlo", "ttbar_powheg"]

    def test_recoil_calibration_adds_expected_shifts(self):
        """Test that recoil calibration shifts add the expected shifts."""

        # Create a configuration and add recoil calibration shifts
        configuration = CaptureConfiguration()
        add_recoil_calibration_shifts(
            configuration,
            "2024",
            self.recoil_calibration_producer,
            self.samples,
        )
        shift_names = [s["shift"].shiftname for s in configuration.shifts]

        # Validate that the expected shifts are available
        shifts_expected = [
            f"CMS_{t}_met_RecoilCalibration_2024"
            for t in ["res"]
        ]

        # Validate that the expected shifts are available
        for shift_exp in shifts_expected:
            for direction in ["Up", "Down"]:
                self.assertIn(
                    f"__{shift_exp}{direction}",
                    shift_names,
                    f"Expected shift {shift_exp} not found",
                )

    def test_total_shift_count(self):
        """Test that function creates the expected number of shifts."""

        # Create a configuration and add shape shifts
        configuration = CaptureConfiguration()
        add_recoil_calibration_shifts(
            configuration,
            "2024",
            self.recoil_calibration_producer,
            self.samples,
        )

        # Expect resolution and response shift for each direction
        expected_count = 4
        self.assertEqual(
            len(configuration.shifts),
            expected_count,
            f"Expected {expected_count} shifts, got {len(configuration.shifts)}",
        )


if __name__ == "__main__":
    unittest.main()
