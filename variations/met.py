from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import (
    SystematicShift,
    SystematicShiftByQuantity,
)


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


def add_recoil_calibration_shifts(
    configuration: Configuration,
    era: str,
    producer: Producer | ProducerGroup,
    samples: list[str],
):
    """
    Shifts in the recoil calibration of the missing transverse momentum.
    """

    # Get scopes from the producer
    scopes = tuple(producer.scopes)

    # Individual shift types performed for the recoil calibration producer
    shifts = [
        {
            "correction_name": "Resp",
            "cms_name": f"CMS_scale_met_RecoilCalibration_{era}",
        },
        {
            "correction_name": "Resol",
            "cms_name": f"CMS_res_met_RecoilCalibration_{era}",
        },
    ]

    for shift in shifts:
        for shift_direction in ["Up", "Down"]:
            configuration.add_shift(
                SystematicShift(
                    name=f"{shift['correction_name']}{shift_direction}",
                    shift_config={
                        scopes: {
                            "recoil_correction_variation": (
                                f"{shift['correction_name']}{shift_direction}"
                            ),
                        },
                    },
                    producers={scopes: [producer]},
                ),
                samples=samples,
            )
