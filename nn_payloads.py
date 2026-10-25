"""NN classifier payloads of the friend sm_nn_classifier (nn spec 3.3): one manifest per model, era and scope.

Layout (payloads/nn_classifier/README.md): ``<model dir>/<era>/<scope>/manifest.json`` and the ONNX file of every
outer-fold residue next to it. The manifest is the one the trainer writes (bbtautau-nn export.py): ``model``,
``channel``, ``folds`` (n), ``files`` (residue r -> ``{file: model_k<n>_r<r>.onnx, sha256}``, scoring the events with
``event % n == r``), ``inputs`` and ``classes`` in order, and ``output`` (``probabilities``, or ``logits``, to which
the friend applies the softmax); ``binary_head: true`` declares a binary head as an extra last output column (absent:
none), since a model with one class more than its manifest lists would look the same. Everything is checked when the
friend is configured, with the standard library only (neither onnx nor onnxruntime is installed where the friend is
configured): the files exist and have their sha256, and each has exactly one float input [1, len(inputs)] and one
float output [1, C], or [1, C + 1] with the binary head, with no dynamic dimension.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Dict, List, NamedTuple, Tuple

REQUIRED_KEYS = ("model", "channel", "folds", "files", "inputs", "classes", "output")
OUTPUT_TYPES = ("probabilities", "logits")
MIN_FOLDS = 2  # every residue is scored by a model that never saw it
ONNX_FLOAT = 1  # TensorProto.FLOAT
_COLUMN_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class NNModel(NamedTuple):
    """A model of a friend production: its payload directory (relative to the analysis directory, one manifest per
    era and scope below it) and the prefix of its columns."""

    payload: str
    prefix: str


class NNPayload(NamedTuple):
    """The checked manifest of one model, era and scope."""

    model: str
    files: Tuple[str, ...]  # per residue r, relative to the analysis directory like the payload directory
    inputs: Tuple[str, ...]
    classes: Tuple[str, ...]
    n_outputs: int  # len(classes), plus one with a binary head
    softmax: bool  # the model gives logits

    @property
    def folds(self) -> int:
        return len(self.files)

    @property
    def binary_head(self) -> bool:
        return self.n_outputs == len(self.classes) + 1


def read_payload(analysis_dir: str, payload: str, era: str, scope: str) -> NNPayload:
    """The manifest of ``payload`` for ``era`` and ``scope``, checked against its ONNX files."""
    directory = os.path.join(payload, era, scope)
    path = os.path.join(analysis_dir, directory, "manifest.json")
    if not os.path.isfile(path):
        raise ValueError(f"NN classifier payload {payload} has no manifest for {era} {scope}: {path} is missing.")
    with open(path) as handle:
        manifest = json.load(handle)

    def fail(message):
        raise ValueError(f"NN classifier manifest {path}: {message}")

    missing = [key for key in REQUIRED_KEYS if key not in manifest]
    if missing:
        fail(f"missing keys {missing}")
    if manifest["channel"] != scope:
        fail(f"channel '{manifest['channel']}' in the payload directory of {scope}")
    folds = manifest["folds"]
    if not isinstance(folds, int) or folds < MIN_FOLDS:
        fail(f"folds {folds!r}, expected an integer >= {MIN_FOLDS}")
    if manifest["output"] not in OUTPUT_TYPES:
        fail(f"output '{manifest['output']}', expected one of {OUTPUT_TYPES}")
    if manifest.get("binary_head", False) not in (True, False):
        fail(f"binary_head {manifest['binary_head']!r}, expected true or false")
    inputs, classes = _names(manifest["inputs"], "inputs", fail), _names(manifest["classes"], "classes", fail)
    n_outputs = len(classes) + int(manifest.get("binary_head", False))
    for name in classes:
        if not _COLUMN_NAME.match(name):
            fail(f"class '{name}' is no column name")
    files = manifest["files"]
    if not isinstance(files, dict) or sorted(files) != sorted(str(r) for r in range(folds)):
        fail(f"files {sorted(files) if isinstance(files, dict) else files!r}, expected the residues 0 .. {folds - 1}")
    paths = []
    for r in range(folds):
        entry = files[str(r)]
        expected = f"model_k{folds}_r{r}.onnx"
        if entry.get("file") != expected:
            fail(f"residue {r} is '{entry.get('file')}', expected '{expected}'")
        onnx_path = os.path.join(analysis_dir, directory, expected)
        if not os.path.isfile(onnx_path):
            fail(f"{expected} is missing")
        with open(onnx_path, "rb") as handle:
            content = handle.read()
        if hashlib.sha256(content).hexdigest() != entry.get("sha256"):
            fail(f"sha256 of {expected} differs from the manifest")
        _check_signature(content, expected, len(inputs), n_outputs, fail)
        paths.append(os.path.join(directory, expected))
    return NNPayload(
        model=manifest["model"],
        files=tuple(paths),
        inputs=inputs,
        classes=classes,
        n_outputs=n_outputs,
        softmax=manifest["output"] == "logits",
    )


def _names(names, what, fail) -> Tuple[str, ...]:
    if not isinstance(names, list) or not names or not all(isinstance(n, str) and n for n in names):
        fail(f"{what} must be a non-empty list of names")
    if len(set(names)) != len(names):
        fail(f"duplicate {what} {sorted({n for n in names if names.count(n) > 1})}")
    return tuple(names)


def _check_signature(content: bytes, name: str, n_inputs: int, n_outputs: int, fail) -> None:
    """Check one input [1, n_inputs] and one output [1, n_outputs], both float."""
    inputs, outputs = onnx_signature(content)
    if len(inputs) != 1 or len(outputs) != 1:
        fail(f"{name} has {len(inputs)} inputs and {len(outputs)} outputs, CROWN evaluates exactly one of each")
    for kind, (tensor, elem_type, dims) in (("input", inputs[0]), ("output", outputs[0])):
        if elem_type != ONNX_FLOAT:
            fail(f"{name}: {kind} '{tensor}' has element type {elem_type}, expected float ({ONNX_FLOAT})")
        if len(dims) != 2 or None in dims:
            fail(f"{name}: {kind} '{tensor}' has the shape {dims}, expected [1, n] without a dynamic dimension")
        if dims[0] != 1:
            fail(f"{name}: {kind} '{tensor}' has the batch size {dims[0]}, CROWN evaluates one event at a time")
    if inputs[0][2][1] != n_inputs:
        fail(f"{name} takes {inputs[0][2][1]} inputs, the manifest lists {n_inputs}")
    if outputs[0][2][1] != n_outputs:
        fail(f"{name} gives {outputs[0][2][1]} outputs, the manifest declares {n_outputs} (classes and binary head)")


# --- the graph inputs and outputs of an ONNX file, without onnx ------------------------------------------------
# onnx.proto: ModelProto.graph = 7; GraphProto.initializer = 5, input = 11, output = 12; TensorProto.name = 8;
# ValueInfoProto.name = 1, type = 2; TypeProto.tensor_type = 1; TypeProto.Tensor.elem_type = 1, shape = 2;
# TensorShapeProto.dim = 1; Dimension.dim_value = 1, dim_param = 2.


def onnx_signature(content: bytes) -> Tuple[List[tuple], List[tuple]]:
    """(name, element type, dims) of the graph inputs (initializers excluded) and outputs of a serialized ONNX
    model; a dimension without a fixed value (dynamic or unknown) is None."""
    graphs = [value for field, value in _fields(memoryview(content)) if field == 7]
    if len(graphs) != 1:
        raise ValueError(f"expected one graph in the ONNX model, found {len(graphs)}")
    initializers, inputs, outputs = set(), [], []
    for field, value in _fields(graphs[0]):
        if field == 5:
            initializers |= {bytes(v).decode() for f, v in _fields(value) if f == 8}
        elif field == 11:
            inputs.append(_value_info(value))
        elif field == 12:
            outputs.append(_value_info(value))
    return [i for i in inputs if i[0] not in initializers], outputs


def _value_info(buffer) -> tuple:
    fields = _field_map(buffer)
    name = bytes(fields.get(1, [b""])[0]).decode()
    type_fields = _field_map(fields[2][0]) if 2 in fields else {}
    tensor = _field_map(type_fields[1][0]) if 1 in type_fields else {}  # not a tensor: no type, no shape
    elem_type = tensor.get(1, [None])[0]
    dims = []
    for dim in _field_map(tensor[2][0]).get(1, []) if 2 in tensor else []:
        value = _field_map(dim).get(1)
        dims.append(_int64(value[0]) if value and _int64(value[0]) > 0 else None)
    return name, elem_type, dims


def _field_map(buffer) -> Dict[int, list]:
    fields: Dict[int, list] = {}
    for field, value in _fields(buffer):
        fields.setdefault(field, []).append(value)
    return fields


def _fields(buffer):
    """(field number, value) of a protobuf message: varints as int, length-delimited fields as memoryview."""
    position = 0
    while position < len(buffer):
        key, position = _varint(buffer, position)
        field, wire = key >> 3, key & 7
        if wire == 0:
            value, position = _varint(buffer, position)
        elif wire == 2:
            length, position = _varint(buffer, position)
            value, position = buffer[position:position + length], position + length
        elif wire in (1, 5):
            size = 8 if wire == 1 else 4
            value, position = buffer[position:position + size], position + size
        else:
            raise ValueError(f"unsupported protobuf wire type {wire}")
        yield field, value


def _varint(buffer, position) -> Tuple[int, int]:
    result = shift = 0
    while True:
        byte = buffer[position]
        position += 1
        result |= (byte & 0x7F) << shift
        if byte < 0x80:
            return result, position
        shift += 7


def _int64(value: int) -> int:
    return value - (1 << 64) if value >= 1 << 63 else value
