from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup

from ._util import add_systematic_shift, KeyValueShift


def add_muon_id_iso_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add shifts for muon ID and isolation scale factors for the given era.
    """

    # Exclude data, as well as embedding samples, which have their own muon ID
    # and isolation scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"],

    # List if shifts for the total systematic shift of the muon ID and isolation
    # scale factors 
    shifts = [
        KeyValueShift(
            name=f"CMS_eff_m_id_{era}",
            key="muon_id_sf_variation",
            value="syst{direction}",
        ),
        KeyValueShift(
            name=f"CMS_eff_m_iso_{era}",
            key="muon_iso_sf_variation",
            value="syst{direction}",
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
