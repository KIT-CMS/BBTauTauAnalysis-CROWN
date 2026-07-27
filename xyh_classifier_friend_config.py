from __future__ import annotations  # needed for type annotations in > python 3.7
from functools import reduce
from operator import add
from itertools import product
from typing import List, Union
from .producers import pairquantities as pairquantities
from .producers import pnn as pnn
from .quantities import output as q
from code_generation.friend_trees import FriendTreeConfiguration
from code_generation.producer import ProducerGroup

from .constants import HAD_TAU_SCOPES


XYH_MASS_POINTS_TEST = [
    (m_x, m_y)
    for m_x, m_y in product(
        [600, 800, 1200, 2000, 3000, 4000],
        [90, 150, 600, 800, 1400, 3500],
    )
    if m_x >= m_y + 125
]


def build_config(
    era: str,
    sample: str,
    scopes: List[str],
    shifts: List[str],
    available_sample_types: List[str],
    available_eras: List[str],
    available_scopes: List[str],
    quantities_map: Union[str, None] = None,
):

    # --------------------------------------------------------------------------
    # Configuration setup
    # --------------------------------------------------------------------------

    configuration = FriendTreeConfiguration(
        era,
        sample,
        scopes,
        shifts,
        available_sample_types,
        available_eras,
        available_scopes,
        quantities_map,
    )

    # --------------------------------------------------------------------------
    # Parameters
    # --------------------------------------------------------------------------

    for scope in HAD_TAU_SCOPES:
        configuration.add_config_parameters(
            [scope],
            {
                "pnn_num_reco_inputs": len(pnn.PNN_RECO_INPUTS),
                "pnn_num_param_inputs": len(pnn.PNN_PARAM_INPUT_NAMES),
                "pnn_num_outputs": 4,
            },
        )

        for decay_mode in ["y2b_h2tau", "y2tau_h2b"]:
            configuration.add_config_parameters(
                [scope],
                {
                    f"pnn_{decay_mode}_onnx_file_even": f"payloads/xyh_classifier/pnn-2026-07-10/{scope}/model__{decay_mode}__fold_0.onnx",
                    f"pnn_{decay_mode}_onnx_file_odd": f"payloads/xyh_classifier/pnn-2026-07-10/{scope}/model__{decay_mode}__fold_1.onnx",
                    f"pnn_{decay_mode}_param_trafo_file_even": f"payloads/xyh_classifier/pnn-2026-07-10/{scope}/parameter_transformations__{decay_mode}__fold_0.json",
                    f"pnn_{decay_mode}_param_trafo_file_odd": f"payloads/xyh_classifier/pnn-2026-07-10/{scope}/parameter_transformations__{decay_mode}__fold_1.json",
                },
            )

    # --------------------------------------------------------------------------
    # Producers
    # --------------------------------------------------------------------------

    configuration.add_producers(
        HAD_TAU_SCOPES,
        [
            pnn.PNNRecoInputs,
            ProducerGroup(
                name="PNNOutputScores",
                call=None,
                input=None,
                output=None,
                scopes=HAD_TAU_SCOPES,
                subproducers=[
                    pnn.PNNOutputScoreProducers[(decay_mode, m_x, m_y)]
                    for decay_mode in ["y2b_h2tau", "y2tau_h2b"]
                    for m_x, m_y in XYH_MASS_POINTS_TEST
                ],
            ),
            ProducerGroup(
                name="PNNMaxScoreIndices",
                call=None,
                input=None,
                output=None,
                scopes=HAD_TAU_SCOPES,
                subproducers=[
                    pnn.PNNMaxScoreIndexProducers[(decay_mode, m_x, m_y)]
                    for decay_mode in ["y2b_h2tau", "y2tau_h2b"]
                    for m_x, m_y in XYH_MASS_POINTS_TEST
                ],
            ),
            ProducerGroup(
                name="PNNMaxScoreValues",
                call=None,
                input=None,
                output=None,
                scopes=HAD_TAU_SCOPES,
                subproducers=[
                    pnn.PNNMaxScoreValueProducers[(decay_mode, m_x, m_y)]
                    for decay_mode in ["y2b_h2tau", "y2tau_h2b"]
                    for m_x, m_y in XYH_MASS_POINTS_TEST
                ],
            ),
        ],
    )

    # --------------------------------------------------------------------------
    # Outputs
    # --------------------------------------------------------------------------

    configuration.add_outputs(
        HAD_TAU_SCOPES,
        list(reduce(
            add,
            (
                [
                    q.get_quantity(f"max_score_index_{decay_mode}_mx{m_x}_my{m_y}"),
                    q.get_quantity(f"max_score_{decay_mode}_mx{m_x}_my{m_y}"),
                ]
                for decay_mode in ["y2b_h2tau", "y2tau_h2b"]
                for m_x, m_y in XYH_MASS_POINTS_TEST
            )
        ))
    )

    # --------------------------------------------------------------------------
    # Configuration validation and optimization
    # --------------------------------------------------------------------------

    configuration.optimize()
    configuration.validate()
    configuration.report()

    return configuration.expanded_configuration()
