from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from ..quantities import nanoAOD_run2

from ._util import add_systematic_shift, KeyValueShift


def add_pileup_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add pileup reweighting shifts for the given era.
    """

    # Exclude data, as well as embedding samples, which have their own muon ID
    # and isolation scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # List if shifts for the total systematic shift of the muon ID and isolation
    # scale factors 
    shifts = [
        KeyValueShift(
            name=f"CMS_pileup_{era}",
            key="PU_reweighting_variation",
            value="{direction}",
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


def add_prefiring_shifts(
    configuration: Configuration,
    era: str,
):
    """
    Add L1 ECAL trigger prefiring shifts for the given era.
    """

    # Raise exception if this function is called for an era that does not have
    # the prefiring issue
    if era not in ["2016preVFP", "2016postVFP", "2017"]:
        raise ValueError(
            f"Prefiring shifts are not applicable for era '{era}'."
        )

    # Exclude data, as well as embedding samples, which have their own muon ID
    # and isolation scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Extract the year from the era string (e.g., "2016preVFP" -> "2016")
    year = era[:4]

    # Add up and down variation for each shift
    for direction in ["up", "down"]:
        configuration.add_shift(
            name=f"CMS_ecal_prefiring_{year}{direction.capitalize()}",
            quantity_change={
                nanoAOD_run2.L1PreFiringWeight_Nom: getattr(
                    nanoAOD_run2,
                    f"L1PreFiringWeight_{direction.capitalize()}",
                ),
            },
            scopes=["global"],
            exclude_samples=exclude_samples,
        )
