from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import SystematicShiftByQuantity
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


# The eras whose MC build_config weights with the L1 prefiring weight
# (event.PrefireWeight) and gives the prefiring shifts. The tau-ID measurement
# adds the other Run-2 eras (2018: the muon prefiring, v7 spec E11).
COMMON_PREFIRING_ERAS = ("2016preVFP", "2016postVFP", "2017")


def add_prefiring_shifts(
    configuration: Configuration,
    era: str,
):
    """
    Add L1 trigger prefiring shifts for the given era: the NanoAOD weight
    L1PreFiringWeight (ECAL and muon prefiring; in 2018 the muon part only)
    varied by its Up/Dn columns, named CMS_ecal_prefiring_<year> after the
    datacard name of the ECAL issue.
    """

    # Raise exception if this function is called for an era without the
    # prefiring weight
    if era not in ["2016preVFP", "2016postVFP", "2017", "2018"]:
        raise ValueError(
            f"Prefiring shifts are not applicable for era '{era}'."
        )

    # Exclude data, as well as embedding samples, which have their own muon ID
    # and isolation scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Extract the year from the era string (e.g., "2016preVFP" -> "2016")
    year = era[:4]

    # Add up and down variation for each shift, the NanoAOD branches carry the
    # suffixes "Up" and "Dn"
    for direction, suffix in [("up", "Up"), ("down", "Dn")]:
        configuration.add_shift(
            SystematicShiftByQuantity(
                name=f"CMS_ecal_prefiring_{year}{direction.capitalize()}",
                quantity_change={
                    nanoAOD_run2.L1PreFiringWeight_Nom: getattr(
                        nanoAOD_run2,
                        f"L1PreFiringWeight_{suffix}",
                    ),
                },
                scopes=["global"],
            ),
            exclude_samples=exclude_samples,
        )
