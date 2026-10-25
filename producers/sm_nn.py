"""Producers of the NN classifier friend (sm_nn_classifier, nn spec 3.4), built from the gate and the payloads.

``gate_producer`` defines the gate flag (``nn_gate.skim_cuts``) once per friend; per model, ``classifier_producers``
builds the input vector in the order of the manifest (``fakefactors::BuildFloatVector``), the scores of the model of
the event's residue (``xyh::classifier::EvaluateFolds``, empty outside the gate) and the output columns
(``xyh::classifier::UnpackScores``, -1 outside the gate).
"""
from typing import Dict, List, NamedTuple

from code_generation.producer import Producer

from ..nn_payloads import NNPayload
from ..quantities import nanoAOD as nanoAOD
from ..quantities import output as q

GATE_CALL = """
    xyh::classifier::SelectionFlag(
        {df},
        {output},
        "{nn_gate_expression}",
        {input_vec}
    )
    """
BUILD_FLOAT_VECTOR_CALL = """
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """


def gate_producer(scope: str, columns: List[str]) -> Producer:
    """The gate flag from the gate expression (parameter ``nn_gate_expression``) over ``columns``."""
    return Producer(
        name="NNGate",
        call=GATE_CALL,
        input=[q.ntuple_column(name) for name in columns],
        output=[q.nn_gate],
        scopes=[scope],
    )


class ClassifierProducers(NamedTuple):
    inputs: Producer
    scores: Producer
    outputs: Producer


def output_names(prefix: str, payload: NNPayload) -> List[str]:
    """The output columns of a model, in the order of UnpackScores: class, maximum, one score per output."""
    names = [f"{prefix}predicted_class", f"{prefix}predicted_max_value"]
    names += [f"{prefix}nn_score_{name}" for name in payload.classes]
    if payload.binary_head:
        names.append(f"{prefix}binary_score")
    return names


def classifier_parameters(prefix: str, payload: NNPayload) -> Dict[str, object]:
    """The ONNX file of every residue and the dimensions the C++ checks the models against."""
    parameters = {f"{prefix}onnx_file_r{r}": file for r, file in enumerate(payload.files)}
    parameters.update(
        {
            f"{prefix}num_inputs": len(payload.inputs),
            f"{prefix}num_classes": len(payload.classes),
            f"{prefix}num_outputs": payload.n_outputs,
            f"{prefix}softmax": payload.softmax,
        }
    )
    return parameters


def classifier_producers(scope: str, prefix: str, payload: NNPayload) -> ClassifierProducers:
    """Input vector, scores and output columns of the model with column prefix ``prefix``."""
    inputs, scores = q.classifier_quantity(f"{prefix}inputs"), q.classifier_quantity(f"{prefix}scores")
    files = ", ".join(f'"{{{prefix}onnx_file_r{r}}}"' for r in range(payload.folds))
    return ClassifierProducers(
        inputs=Producer(
            name=f"NNInputs_{prefix}",
            call=BUILD_FLOAT_VECTOR_CALL,
            input=[q.ntuple_column(name) for name in payload.inputs],
            output=[inputs],
            scopes=[scope],
        ),
        scores=Producer(
            name=f"NNScores_{prefix}",
            call=f"""
    xyh::classifier::EvaluateFolds(
        {{df}},
        onnxSessionManager,
        {{output}},
        {{input}},
        {{vec_open}}{files}{{vec_close}},
        {{{prefix}num_inputs}},
        {{{prefix}num_classes}},
        {{{prefix}num_outputs}},
        {{{prefix}softmax}}
    )
    """,
            input=[inputs, nanoAOD.event, q.nn_gate],
            output=[scores],
            scopes=[scope],
        ),
        outputs=Producer(
            name=f"NNOutputs_{prefix}",
            call=f"""
    xyh::classifier::UnpackScores(
        {{df}},
        {{output_vec}},
        {{input}},
        {{{prefix}num_classes}}
    )
    """,
            input=[scores],
            output=[q.classifier_quantity(name) for name in output_names(prefix, payload)],
            scopes=[scope],
        ),
    )
