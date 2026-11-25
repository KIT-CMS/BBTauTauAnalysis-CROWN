from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup

from ._util import add_systematic_shift, KeyValueShift


def add_qcd_scale_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
    exclude_samples: tuple[str, ...] = (),
):
    """
    Add shifts of the renomalization and factorization scales.

    `exclude_samples` names the samples without the weight producer, besides
    data and embedding: a shift registered for a sample without the producer
    has no column (v8 spec C34).
    """

    # Exclude data, as well as embedding samples, and the samples without the
    # weight producer
    exclude_samples = sorted({"data", "embedding", "embedding_mc", *exclude_samples})

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


def add_parton_shower_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add shifts of the scale of the initial and of the final state radiation of
    the parton shower, ps_isr and ps_fsr (v8 spec C23).

    The value is the factor of the renormalization scale of the shower: Up is
    the scale times 2, which lowers alpha_s and gives less radiation, Down the
    scale times 0.5 with more radiation. `producers` evaluates
    `event::reweighting::PartonShower` with the keys below.
    """

    # Exclude data, as well as embedding samples
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # List of shifts for the scales of the parton shower
    shifts = [
        KeyValueShift(
            name="ps_isr",
            key="ps_isr_variation",
            value={"down": 0.5, "up": 2.0},
        ),
        KeyValueShift(
            name="ps_fsr",
            key="ps_fsr_variation",
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
