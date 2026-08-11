
from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup

from code_generation.systematics import SystematicShiftByQuantity


def add_unclustered_energy_shifts(
    configuration: Configuration,
    era: str,
):
    """
    Unclustered energy shifts of the missing transverse momentum.
    """

    # TODO check if we need to do this for x and y independently

    for direction in ["Up", "Down"]:
        configuration.add_shift(
            SystematicShiftByQuantity(
                name=f"CMS_scale_met_unclustered_energy_{era}{direction}",
                quantity_change={
                    "PuppiMET_pt": f"PuppiMET_ptUnclustered{direction}",
                    "PuppiMET_phi": f"PuppiMET_phiUnclustered{direction}",
                },
                scopes=["global"],
            ),
            exclude_samples=["data", "embedding", "embedding_mc"],
        )
