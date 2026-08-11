from code_generation.configuration import Configuration
from code_generation.systematics import SystematicShift

from .producers import scalefactors as scalefactors
from .constants import SCOPES


def add_bjet_tagging_fixed_wp_shifts(
    configuration: Configuration,
    era: str,
    producer: Producer | ProducerList,
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
    for jet_flavor in ["bc", "lf"]:
        for direction in ["up", "down"]:

            # Common uncertainty group correlated across eras
            name = (
                "btag"
                + jet_flavor.upper()
                + "Correlated"
                + direction.capitalize()
            )
            shift_value = f"{direction}_correlated"
            configuration.add_shift(
                SystematicShift(
                    name=name,
                    shift_config={
                        f"bjet_sf_variation_{jet_flavor}": shift_value,
                    },
                    producers={scopes: [producer]},
                ),
                exclude_samples=exclude_samples,
            )

            # Common uncertainty group that is uncorrelated across era
            name = (
                "btag"
                + jet_flavor.upper()
                + era
                + direction.capitalize()
            )
            shift_value = f"{direction}_uncorrelated"
            configuration.add_shift(
                SystematicShift(
                    name=name,
                    shift_config={
                        f"bjet_sf_variation_{jet_flavor}": shift_value,
                    },
                    producers={scopes: producers},
                ),
                exclude_samples=exclude_samples,
            )


def add_bjet_tagging_shape_shifts(
    configuration: Configuration,
    era: str,
):
    """
    Add systematic shifts for shape-based b jet tagging scale factors.

    The procedure follows the [BTV recommendations](https://btv-wiki.docs.cern.ch/PerformanceCalibration/SFUncertaintiesAndCorrelations/#ak4-shape-correction-sfs-iterativefit).

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

    # Sources of b jet tagging uncertainties for different jet flavors
    unc_groups = [
        "hf",
        "lf",
        "hfstats1",
        "hfstats2",
        "lfstats1",
        "lfstats2",
        "cferr1",
        "cferr2",
        "hfstats1",
        "hfstats2",
        "lfstats1",
        "lfstats2",
    ]

    # Add up and down variations for each uncertainty group
    for direction in ["up", "down"]:
        for source in unc_groups:
            name = f"btag{source.capitalize()}{direction.capitalize()}"
            shift_value = f"{direction}_{source}"
            configuration.add_shift(
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

    # Search for JES uncertainties
    for 
