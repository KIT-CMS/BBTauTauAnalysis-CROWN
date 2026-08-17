from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup

from ._util import add_systematic_shift, KeyValueShift


def add_qcd_scale_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add shifts of the renomalization and factorization scales.
    """

    # Exclude data, as well as embedding samples
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # List of shifts for the renormalization and factorization scales
    shifts = [
        KeyValueShift(
            name="QCDscale_ren",
            key="muR",
            value={"down": 0.5, "up": 2.0},
        ),
        KeyValueShift(
            name="QCDscale_fac",
            key="muF",
            value={"down": 0.5, "up": 2.0},
        ),
    ]

    # Add up and down variation for each shift
    for shift in shifts:
        add_systematic_shift(
            configuration,
            shift,
            producers,
            add_kwargs={"exclude_samples": exclude_samples},
        )
