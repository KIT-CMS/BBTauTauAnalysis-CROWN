from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import (
    SystematicShift,
    SystematicShiftByQuantity,
)

from ._util import add_systematic_shift, KeyValueShift
from ..quantities import nanoAOD


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
                    nanoAOD.PuppiMET_pt: getattr(
                        nanoAOD,
                        f"PuppiMET_ptUnclustered{direction}",
                    ),
                    nanoAOD.PuppiMET_phi: getattr(
                        nanoAOD,
                        f"PuppiMET_phiUnclustered{direction}",
                    ),
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

    # Individual shift types performed for the recoil calibration producer
    shifts = [
        KeyValueShift(
            name=f"CMS_scale_met_RecoilCalibration_{era}",
            key="recoil_correction_variation",
            value="Resp{Direction}",
        ),
        KeyValueShift(
            name=f"CMS_res_met_RecoilCalibration_{era}",
            key="recoil_correction_variation",
            value="Resol{Direction}",
        ),
    ]

    for shift in shifts:
        add_systematic_shift(configuration, shift, producer)
