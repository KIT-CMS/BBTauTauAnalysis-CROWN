from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import SystematicShift

from ..producers import scalefactors as scalefactors


def add_bjet_tagging_fixed_wp_shifts(
    configuration: Configuration,
    era: str,
    producer: Producer | ProducerGroup,
):
    """
    Add systematic shifts for the working point (WP)-based b jet tagging scale
    factors.

    The procedure follows the
    [BTV recommendations](https://btv-wiki.docs.cern.ch/PerformanceCalibration/SFUncertaintiesAndCorrelations/#ak4-working-point-based-sfs-fixedwp-sfs).
    Currently, a reduced uncertainty scheme (one era-correlated and one
    era-uncorrelated uncertainty for b/c and for light-flavor jets,
    respectively).
    """

    # Producers that the variations are applied to
    producer = scalefactors.BJetWPUParT_SF

    # Scopes that the variations are applied to
    scopes = tuple(producer.scopes)

    # Samples to exclude (where b jet taggin already takes place on data jets)
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Add variations for b/c and for light-flavor jets independently
    for jet_flavor in ["bc", "light"]:
        for corr_type in ["correlated", "uncorrelated"]:
            for direction in ["up", "down"]:

                # Set value of the 'bjet_sf_variation_{jet_flavor}' parameter
                # for this shift
                shift_key = f"bjet_sf_variation_{jet_flavor}"
                shift_value = f"{direction}_{corr_type}"

                # Construct the shift name
                shift_name = f"CMS_btag_fixedWP_{jet_flavor}_{corr_type}"
                if corr_type == "uncorrelated":
                    shift_name += f"_{era}"
                shift_name += direction.capitalize()

                # Add the shift to the configuration
                configuration.add_shift(
                    SystematicShift(
                        name=shift_name,
                        shift_config={scopes: {shift_key: shift_value}},
                        producers={scopes: [producer]},
                    ),
                    exclude_samples=exclude_samples,
                )


def add_bjet_tagging_shape_shifts(
    configuration: Configuration,
    era: str,
    producer: Producer | ProducerGroup,
):
    """
    Add systematic shifts for shape-based b jet tagging scale factors.

    The procedure follows the
    [BTV recommendations](https://btv-wiki.docs.cern.ch/PerformanceCalibration/SFUncertaintiesAndCorrelations/#ak4-shape-correction-sfs-iterativefit).

    Notes
    -----

    This function only adds the core shifts of the method (`"hf"`, `"lf"`,
    ...). The shape-based scale factors also come along with dedicated `jes_*`
    shifts that need to be applied together with the corresponding jet energy
    scale shifts.
    """

    # Producer that the variations is applied to
    producer = scalefactors.BJetShapePNet_SF

    # Scopes that the variations are applied to
    scopes = tuple(producer.scopes)

    # Samples to exclude (where b jet taggin already takes place on data jets)
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Individual b jet tagging shifts, correlated between eras
    btag_shifts_correlated = [
        "hf",
        "lf",
        "cferr1",
        "cferr2",
    ]

    # Individual b jet tagging shifts, uncorrelated between eras
    btag_shifts_uncorrelated = [
        "hfstats1",
        "hfstats2",
        "lfstats1",
        "lfstats2",
    ]

    # Convenience function to add shift to config
    def _add_shift(name: str, shift_value: str):
        return configuration.add_shift(
            SystematicShift(
                name=name,
                shift_config={
                    scopes: {"bjet_sf_variation": shift_value},
                },
                producers={
                    scopes: [producer],
                },
            ),
            exclude_samples=exclude_samples,
        )

    # Add up and down variations for each uncertainty group
    for direction in ["up", "down"]:

        # Add correlated shifts (without era suffix)
        for shift in btag_shifts_correlated:
            _add_shift(
                f"CMS_btag_fullShape_{shift}{direction.capitalize()}",
                f"{direction}_{shift}",
            )

        # Add uncorrelated shifts (without era suffix)
        for shift in btag_shifts_uncorrelated:
            _add_shift(
                f"CMS_btag_fullShape_{shift}_{era}{direction.capitalize()}",
                f"{direction}_{shift}",
            )
