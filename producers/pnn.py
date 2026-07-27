from code_generation.producer import Producer

from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from ..constants import HAD_TAU_SCOPES, XYH_MASS_POINTS


# Define constants for reconstructed input variables and parameters
PNN_RECO_INPUTS = [
    q.n_jets,
    q.n_bjets,
    q.pt_1,
    q.pt_2,
    q.eta_1,
    q.eta_2,
    q.phi_1,
    q.phi_2,
    q.m_vis,
    q.pt_vis,
    q.deltaR_ditaupair,
    q.bpair_pt_1,
    q.bpair_pt_2,
    q.bpair_eta_1,
    q.bpair_eta_2,
    q.bpair_phi_1,
    q.bpair_phi_2,
    q.bpair_btag_value_1,
    q.bpair_btag_value_2,
    q.bpair_m_inv,
    q.bpair_pt_dijet,
    q.bpair_deltaR,
    q.met,
    q.metphi,
    q.mt_1,
    q.mt_2,
    q.mt_tot,
]
PNN_PARAM_INPUT_NAMES = [
    "m_x",
    "m_y",
]
PNN_PARAM_INPUT_VALUES = XYH_MASS_POINTS
N_INPUTS = len(PNN_RECO_INPUTS) + len(PNN_PARAM_INPUT_NAMES)


# Reconstructed variables that serve as input to the neural network classifier
PNNRecoInputs = Producer(
    name="PNNRecoInputs",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=PNN_RECO_INPUTS,
    output=[q.pnn_reco_inputs],
    scopes=HAD_TAU_SCOPES,
)


PNNOutputScoreProducers = {}
PNNMaxScoreIndexProducers = {}
PNNMaxScoreValueProducers = {}

for decay_mode in ["y2b_h2tau", "y2tau_h2b"]:
    for m_x, m_y in PNN_PARAM_INPUT_VALUES:

        # Producer of neural network output vector 
        PNNOutputScoreProducers[(decay_mode, m_x, m_y)] = Producer(
            name=f"PNNOutputScores{decay_mode}MX{m_x}MY{m_y}",
            call=(
                f"""
                xyh::classifier::EvaluatePNN(
                    {{df}},
                    onnxSessionManager,
                    {{output}},
                    {{input}},
                    "{{pnn_{decay_mode}_onnx_file_even}}",
                    "{{pnn_{decay_mode}_onnx_file_odd}}",
                    "{{pnn_{decay_mode}_param_trafo_file_even}}",
                    "{{pnn_{decay_mode}_param_trafo_file_odd}}",
                    {{pnn_num_reco_inputs}},
                    {{pnn_num_param_inputs}},
                    {{pnn_num_outputs}},
                    {m_x},
                    {m_y}
                )
                """
            ),
            input=[q.pnn_reco_inputs, nanoAOD.event],
            output=[q.get_quantity(f"scores_{decay_mode}_mx{m_x}_my{m_y}")],
            scopes=HAD_TAU_SCOPES,
        )

        # Producer of output class with maximal score
        PNNMaxScoreIndexProducers[(decay_mode, m_x, m_y)] = Producer(
            name=f"PNNMaxScoreIndex{decay_mode}MX{m_x}MY{m_y}",
            call=(
                """
                xyh::classifier::GetMaxScoreIndex(
                    {df},
                    {output},
                    {input}
                )
                """
            ),
            input=[q.get_quantity(f"scores_{decay_mode}_mx{m_x}_my{m_y}")],
            output=[q.get_quantity(f"max_score_index_{decay_mode}_mx{m_x}_my{m_y}")],
            scopes=HAD_TAU_SCOPES,
        )

        # Producer of score at output class with maximal score
        PNNMaxScoreValueProducers[(decay_mode, m_x, m_y)] = Producer(
            name=f"PNNMaxScoreValue{decay_mode}MX{m_x}MY{m_y}",
            call=(
                """
                xyh::classifier::GetMaxScoreValue(
                    {df},
                    {output},
                    {input}
                )
                """
            ),
            input=[
                q.get_quantity(f"scores_{decay_mode}_mx{m_x}_my{m_y}"),
                q.get_quantity(f"max_score_index_{decay_mode}_mx{m_x}_my{m_y}"),
            ],
            output=[q.get_quantity(f"max_score_{decay_mode}_mx{m_x}_my{m_y}")],
            scopes=HAD_TAU_SCOPES,
        )
