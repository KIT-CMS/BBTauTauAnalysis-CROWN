from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup

from ._util import add_systematic_shift, KeyValueShift


def add_electron_id_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add shifts for electron ID scale factors for the given era.
    """

    # Exclude data, as well as embedding samples, which have their own electron ID
    # and isolation scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"],

    # List if shifts for the total systematic shift of the electron ID and isolation
    # scale factors 
    shifts = [
        KeyValueShift(
            name=f"CMS_eff_e_id_{era}",
            key="ele_id_sf_variation",
            value="sf{direction}",
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


def add_electron_es_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add shifts for electron energy scale variations for the given era.
    """

    # Exclude data, as well as embedding samples
    exclude_samples = ["data", "embedding", "embedding_mc"],

    # Systematic shifts for electron energy scale variations, consisting of
    # scale and smearing variations
    shifts = [
        KeyValueShift(
            name=f"CMS_scale_e_{era}",
            key="ele_es_variation",
            value="scale_{direction}",
        ),
        KeyValueShift(
            name=f"CMS_res_e_{era}",
            key="ele_es_variation",
            value="smear_{direction}",
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
