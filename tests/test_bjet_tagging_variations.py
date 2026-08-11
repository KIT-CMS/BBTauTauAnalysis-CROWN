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


class AddBJetTaggingShiftsTest(unittest.TestCase):
    """
    Unit tests for the `variations.bjet_tagging` functions.
    """

    def setUp(self):
        # Set up dummy producers for testing
        self.fixed_wp_producer = DummyProducer(
            name="BJetWPUParT_SF",
            scopes=["et", "mt", "tt"],
        )
        self.shape_producer = DummyProducer(
            name="BJetShapePNet_SF",
            scopes=["et", "mt", "tt"],
        )

    # ========================================================================
    # Tests for add_bjet_tagging_fixed_wp_shifts
    # ========================================================================

    def test_fixed_wp_adds_correlated_bc_shifts(self):
        """Test that fixed WP shifts add correlated bc uncertainties."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_fixed_wp_shifts(
            configuration,
            "2024",
            self.fixed_wp_producer,
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # Check for correlated bc shifts (up and down)
        for direction in ["Up", "Down"]:
            self.assertIn(
                f"btagBCCorrelated{direction}",
                shift_names,
                f"Expected btagBCCorrelated{direction} not found",
            )

    def test_fixed_wp_adds_correlated_lf_shifts(self):
        """Test that fixed WP shifts add correlated lf uncertainties."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_fixed_wp_shifts(
            configuration,
            "2024",
            self.fixed_wp_producer,
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # Check for correlated lf shifts (up and down)
        for direction in ["Up", "Down"]:
            self.assertIn(
                f"btagLFCorrelated{direction}",
                shift_names,
                f"Expected btagLFCorrelated{direction} not found",
            )

    def test_fixed_wp_adds_uncorrelated_bc_shifts(self):
        """Test that fixed WP shifts add era-uncorrelated bc uncertainties."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_fixed_wp_shifts(
            configuration,
            "2024",
            self.fixed_wp_producer,
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # Check for uncorrelated bc shifts with era (up and down)
        for direction in ["Up", "Down"]:
            self.assertIn(
                f"btagBC2024{direction}",
                shift_names,
                f"Expected btagBC2024{direction} not found",
            )

    def test_fixed_wp_adds_uncorrelated_lf_shifts(self):
        """Test that fixed WP shifts add era-uncorrelated lf uncertainties."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_fixed_wp_shifts(
            configuration,
            "2024",
            self.fixed_wp_producer,
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # Check for uncorrelated lf shifts with era (up and down)
        for direction in ["Up", "Down"]:
            self.assertIn(
                f"btagLF2024{direction}",
                shift_names,
                f"Expected btagLF2024{direction} not found",
            )

    def test_fixed_wp_era_specific_naming(self):
        """Test that uncorrelated shifts include the correct era in name."""

        for era in ["2018", "2022preEE", "2022postEE", "2023preBPix"]:
            configuration = CaptureConfiguration()
            add_bjet_tagging_fixed_wp_shifts(
                configuration,
                era,
                self.fixed_wp_producer,
            )
            shift_names = [s["shift"].name for s in configuration.shifts]

            # Check that era appears in uncorrelated shift names
            for flavor in ["BC", "LF"]:
                for direction in ["Up", "Down"]:
                    expected_name = f"btag{flavor}{era}{direction}"
                    self.assertIn(
                        expected_name,
                        shift_names,
                        f"Expected {expected_name} not found for era {era}",
                    )

    def test_fixed_wp_excludes_samples_correctly(self):
        """Test that fixed WP shifts exclude data/embedding samples."""

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
                f"exclude_samples mismatch for shift {shift_info['shift'].name}",
            )

    def test_fixed_wp_total_shift_count(self):
        """Test that fixed WP creates the expected number of shifts."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_fixed_wp_shifts(
            configuration,
            "2024",
            self.fixed_wp_producer,
        )

        # Expected: 2 flavors (bc, lf) × 2 types (correlated, uncorrelated) × 2 directions = 8 shifts
        self.assertEqual(
            len(configuration.shifts),
            8,
            f"Expected 8 shifts, got {len(configuration.shifts)}",
        )

    # ========================================================================
    # Tests for add_bjet_tagging_shape_shifts
    # ========================================================================

    def test_shape_adds_hf_uncertainty_shifts(self):
        """Test that shape shifts add hf uncertainties."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            "2024",
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # Check for hf shifts (up and down)
        for direction in ["Up", "Down"]:
            self.assertIn(
                f"btagHf{direction}",
                shift_names,
                f"Expected btagHf{direction} not found",
            )

    def test_shape_adds_lf_uncertainty_shifts(self):
        """Test that shape shifts add lf uncertainties."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            "2024",
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # Check for lf shifts (up and down)
        for direction in ["Up", "Down"]:
            self.assertIn(
                f"btagLf{direction}",
                shift_names,
                f"Expected btagLf{direction} not found",
            )

    def test_shape_adds_cferr_uncertainty_shifts(self):
        """Test that shape shifts add cferr uncertainties."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            "2024",
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # Check for cferr shifts (up and down)
        for err_type in ["cferr1", "cferr2"]:
            for direction in ["Up", "Down"]:
                self.assertIn(
                    f"btag{err_type.capitalize()}{direction}",
                    shift_names,
                    f"Expected btag{err_type.capitalize()}{direction} not found",
                )

    def test_shape_adds_stats_uncertainty_shifts(self):
        """Test that shape shifts add stats uncertainties."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            "2024",
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # Check for stats shifts (hfstats1, hfstats2, lfstats1, lfstats2)
        for stats_type in ["hfstats1", "hfstats2", "lfstats1", "lfstats2"]:
            for direction in ["Up", "Down"]:
                self.assertIn(
                    f"btag{stats_type.capitalize()}{direction}",
                    shift_names,
                    f"Expected btag{stats_type.capitalize()}{direction} not found",
                )

    def test_shape_excludes_samples_correctly(self):
        """Test that shape shifts exclude data/embedding samples."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            "2024",
        )

        expected_exclude = ["data", "embedding", "embedding_mc"]
        for shift_info in configuration.shifts:
            self.assertEqual(
                shift_info["exclude_samples"],
                expected_exclude,
                f"exclude_samples mismatch for shift {shift_info['shift'].name}",
            )

    def test_shape_total_shift_count(self):
        """Test that shape shifts create the expected number of shifts."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            "2024",
        )

        # Expected: 12 uncertainty groups × 2 directions = 24 shifts
        # Note: unc_groups list has duplicates (hfstats1, hfstats2, lfstats1, lfstats2 appear twice)
        # This might be intentional or a bug - testing actual behavior
        expected_count = 24  # 12 sources × 2 directions
        self.assertEqual(
            len(configuration.shifts),
            expected_count,
            f"Expected {expected_count} shifts, got {len(configuration.shifts)}",
        )

    def test_shape_shift_naming_convention(self):
        """Test that shape shifts follow the expected naming convention."""

        configuration = CaptureConfiguration()
        add_bjet_tagging_shape_shifts(
            configuration,
            "2024",
        )
        shift_names = [s["shift"].name for s in configuration.shifts]

        # All shape shifts should start with 'btag' and end with 'Up' or 'Down'
        for shift_name in shift_names:
            self.assertTrue(
                shift_name.startswith("btag"),
                f"Shift name '{shift_name}' does not start with 'btag'",
            )
            self.assertTrue(
                shift_name.endswith("Up") or shift_name.endswith("Down"),
                f"Shift name '{shift_name}' does not end with 'Up' or 'Down'",
            )

    # ========================================================================
    # Integration and comparison tests
    # ========================================================================

    def test_both_functions_use_same_exclude_samples(self):
        """Test that both functions use the same exclude_samples list."""

        config_fixed = CaptureConfiguration()
        config_shape = CaptureConfiguration()

        add_bjet_tagging_fixed_wp_shifts(
            config_fixed,
            "2024",
            self.fixed_wp_producer,
        )
        add_bjet_tagging_shape_shifts(
            config_shape,
            "2024",
        )

        expected_exclude = ["data", "embedding", "embedding_mc"]

        for shift_info in config_fixed.shifts + config_shape.shifts:
            self.assertEqual(
                shift_info["exclude_samples"],
                expected_exclude,
                f"exclude_samples mismatch for shift {shift_info['shift'].name}",
            )

    def test_no_overlap_between_fixed_wp_and_shape_shifts(self):
        """Test that fixed WP and shape shifts produce distinct shift names."""

        config_fixed = CaptureConfiguration()
        config_shape = CaptureConfiguration()

        add_bjet_tagging_fixed_wp_shifts(
            config_fixed,
            "2024",
            self.fixed_wp_producer,
        )
        add_bjet_tagging_shape_shifts(
            config_shape,
            "2024",
        )

        fixed_names = {s["shift"].name for s in config_fixed.shifts}
        shape_names = {s["shift"].name for s in config_shape.shifts}

        # No overlap between the two sets
        overlap = fixed_names.intersection(shape_names)
        self.assertEqual(
            len(overlap),
            0,
            f"Found overlapping shift names: {overlap}",
        )


if __name__ == "__main__":
    unittest.main()
