from pathlib import Path
import unittest

from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup

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


def get_mock_producer(scopes=("global",), name="MockProducer"):
    """Create a mock producer for testing."""
    return Producer(
        name=name,
        call="mock_call",
        input=[],
        output=[],
        scopes=scopes,
    )


class JECVariationsTest(unittest.TestCase):
    def test_add_jec_shifts_creates_configuration(self):
        """Test that add_jec_shifts creates a valid configuration with shifts."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2018", jec_producers)

        # Should have multiple shifts (JES sources + JER)
        self.assertGreater(len(configuration.shifts), 0)

    def test_jer_uncertainty_shifts_are_added(self):
        """Test that JER up and down variations are added."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2018", jec_producers)

        shift_names = [
            shift_info["shift"].name for shift_info in configuration.shifts
        ]

        # Check for JER uncertainties
        jer_up_exists = any("jerUncUp" in name for name in shift_names)
        jer_down_exists = any("jerUncDown" in name for name in shift_names)

        self.assertTrue(jer_up_exists, "JER up variation not found")
        self.assertTrue(jer_down_exists, "JER down variation not found")

    def test_jes_sources_for_2018_include_hemissue(self):
        """Test that HEMIssue JES source is included for 2018 era."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2018", jec_producers)

        shift_names = [
            shift_info["shift"].name for shift_info in configuration.shifts
        ]

        # HEMIssue should only be present for 2018
        hem_up_exists = any("jesHEMIssueUp" in name for name in shift_names)
        hem_down_exists = any(
            "jesHEMIssueDown" in name for name in shift_names
        )

        self.assertTrue(hem_up_exists, "HEMIssue up variation not found for 2018")
        self.assertTrue(
            hem_down_exists, "HEMIssue down variation not found for 2018"
        )

    def test_jes_sources_for_run3_exclude_hemissue(self):
        """Test that HEMIssue JES source is excluded for Run 3 eras."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2022preEE", jec_producers)

        shift_names = [
            shift_info["shift"].name for shift_info in configuration.shifts
        ]

        # HEMIssue should NOT be present for Run 3
        hem_shifts = [name for name in shift_names if "HEMIssue" in name]

        self.assertEqual(
            len(hem_shifts),
            0,
            "HEMIssue should not be present for Run 3 eras",
        )

    def test_jes_shift_naming_convention(self):
        """Test that JES shifts follow the expected naming convention."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2018", jec_producers)

        shift_names = [
            shift_info["shift"].name for shift_info in configuration.shifts
        ]

        # Expected JES shift names (without HEMIssue for generic check)
        expected_patterns = [
            "jesAbsolute",
            "jesFlavorQCD",
            "jesBBEC1",
            "jesHF",
            "jesEC2",
            "jesRelativeBal",
        ]

        for pattern in expected_patterns:
            up_exists = any(pattern + "Up" in name for name in shift_names)
            down_exists = any(pattern + "Down" in name for name in shift_names)

            self.assertTrue(
                up_exists,
                f"Expected JES shift '{pattern}Up' not found",
            )
            self.assertTrue(
                down_exists,
                f"Expected JES shift '{pattern}Down' not found",
            )

    def test_era_specific_jes_sources_are_formatted(self):
        """Test that era-specific JES sources have the era substituted."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2022preEE", jec_producers)

        shift_names = [
            shift_info["shift"].name for shift_info in configuration.shifts
        ]

        # Check for era-specific shifts (should have era in the name removed)
        # Regrouped_Absolute_2022preEE -> jesAbsolute2022preEEUp/Down
        era_specific_patterns = [
            "jesAbsolute2022preEE",
            "jesBBEC12022preEE",
            "jesHF2022preEE",
            "jesEC22022preEE",
            "jesRelativeSample2022preEE",
        ]

        for pattern in era_specific_patterns:
            up_exists = any(pattern + "Up" in name for name in shift_names)
            down_exists = any(pattern + "Down" in name for name in shift_names)

            self.assertTrue(
                up_exists,
                f"Expected era-specific JES shift '{pattern}Up' not found",
            )
            self.assertTrue(
                down_exists,
                f"Expected era-specific JES shift '{pattern}Down' not found",
            )

    def test_exclude_samples_are_passed_correctly(self):
        """Test that exclude_samples are correctly passed to add_shift."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2018", jec_producers)

        # All shifts should exclude data, embedding, and embedding_mc samples
        expected_exclude = ["data", "embedding", "embedding_mc"]

        for shift_info in configuration.shifts:
            self.assertEqual(
                shift_info["exclude_samples"],
                expected_exclude,
                f"exclude_samples mismatch for shift {shift_info['shift'].name}",
            )

    def test_bjet_tagging_sf_producer_integration(self):
        """Test that bjet tagging SF producer is properly integrated."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer(scopes=("global",), name="JECProducer")]
        bjet_sf_producer = get_mock_producer(
            scopes=("btagging",), name="BJetSFProducer"
        )

        add_jec_shifts(configuration, "2018", jec_producers, bjet_sf_producer)

        # Check that shifts include bjet_sf_variation configuration
        has_bjet_config = False
        for shift_info in configuration.shifts:
            shift = shift_info["shift"]
            # Check if shift_config contains bjet_sf_variation
            for scope_config in shift.shift_config.values():
                if isinstance(scope_config, dict) and "bjet_sf_variation" in str(
                    scope_config
                ):
                    has_bjet_config = True
                    break

        self.assertTrue(
            has_bjet_config,
            "bjet tagging SF producer configuration not found in shifts",
        )

    def test_jec_producers_scope_consistency_check(self):
        """Test that inconsistent JEC producer scopes raise an error."""
        configuration = CaptureConfiguration()

        # Create producers with different scopes
        producer1 = get_mock_producer(scopes=("global",), name="Producer1")
        producer2 = get_mock_producer(scopes=("local",), name="Producer2")

        # Should raise ValueError due to inconsistent scopes
        with self.assertRaises(ValueError) as context:
            add_jec_shifts(configuration, "2018", [producer1, producer2])

        self.assertIn(
            "not consistent in their scope definition",
            str(context.exception),
        )

    def test_jes_source_format_string_validation(self):
        """Test that invalid format strings in JES sources raise an error."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        # Try to add a JES shift with invalid format string (contains invalid placeholder)
        with self.assertRaises(ValueError) as context:
            _add_jes_shift(
                configuration,
                "2018",
                "Regrouped_{invalid_placeholder}",  # Invalid placeholder
                jec_producers,
                jec_scopes=("global",),
            )

        self.assertIn(
            "Format string is only allowed to contain the 'era' placeholder",
            str(context.exception),
        )

    def test_shift_config_contains_expected_parameters(self):
        """Test that shift configurations contain expected parameters."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2018", jec_producers)

        for shift_info in configuration.shifts:
            shift = shift_info["shift"]

            # Each shift should have shift_config and producers
            self.assertTrue(hasattr(shift, "shift_config"))
            self.assertTrue(hasattr(shift, "producers"))

            # Check that shift_config is not empty
            self.assertGreater(len(shift.shift_config), 0)

    def test_all_jes_sources_are_added(self):
        """Test that all expected JES sources are present in the configuration."""
        configuration = CaptureConfiguration()
        jec_producers = [get_mock_producer()]

        add_jec_shifts(configuration, "2018", jec_producers)

        shift_names = [
            shift_info["shift"].name for shift_info in configuration.shifts
        ]

        # Count JES shifts (should have multiple sources * 2 directions)
        jes_shifts = [name for name in shift_names if name.startswith("jes")]

        # We expect at least these JES sources for 2018:
        # Absolute, Absolute_2018, FlavorQCD, BBEC1, BBEC1_2018,
        # HF, HF_2018, EC2, EC2_2018, RelativeBal, RelativeSample_2018,
        # HEMIssue (each with Up and Down = 12 * 2 = 24 minimum)
        self.assertGreaterEqual(
            len(jes_shifts),
            20,
            f"Expected at least 20 JES shifts, got {len(jes_shifts)}",
        )


if __name__ == "__main__":
    unittest.main()
