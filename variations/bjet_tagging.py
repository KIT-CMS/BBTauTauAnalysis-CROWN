from itertools import product

from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup

from ..producers import scalefactors as scalefactors
from ._util import add_systematic_shift, KeyValueShift

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

    # Samples to exclude (where b jet taggin already takes place on data jets)
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # List of b jet tagging scale factor shifts
    shifts = []
    for jet_flavor, correlation_type in product(
        ["bc", "light"],
        ["correlated", "uncorrelated"],
    ):
        name = f"CMS_btag_fixedWP_{jet_flavor}_{correlation_type}"
        if correlation_type == "uncorrelated":
            name += f"_{era}"
        shifts.append(
            KeyValueShift(
                name=name,
                key=f"bjet_sf_variation_{jet_flavor}",
                value=f"{{direction}}_{correlation_type}"
            )
        )

    # Add shifts to the configuration
    for shift in shifts:
        add_systematic_shift(
            configuration,
            shift,
            producer,
            add_kwargs={"exclude_samples": exclude_samples},
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

    # Samples to exclude (where b jet taggin already takes place on data jets)
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # List of b jet tagging scale factor shifts
    shifts = []

    # Shifts which are correlated between eras
    for name in [
        "hf",
        "lf",
        "cferr1",
        "cferr2",
    ]:
        shifts.append(
            KeyValueShift(
                name=f"CMS_btag_fullShape_{name}",
                key="bjet_sf_variation",
                value=f"{{direction}}_{name}",
            )
        )

    # Shifts which are uncorrelated between eras
    for name in [
        "hfstats1",
        "hfstats2",
        "lfstats1",
        "lfstats2",
    ]:
        shifts.append(
            KeyValueShift(
                name=f"CMS_btag_fullShape_{name}_{era}",
                key="bjet_sf_variation",
                value=f"{{direction}}_{name}",
            )
        )

    # Add shifts to the configuration
    for shift in shifts:
        add_systematic_shift(
            configuration,
            shift,
            producer,
            add_kwargs={"exclude_samples": exclude_samples},
        )
