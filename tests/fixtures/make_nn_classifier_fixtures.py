#!/usr/bin/env python3
"""Generate the toy ONNX models of the NN classifier friend tests (sm_nn_classifier, nn spec 3.3, 3.4).

Needs torch, onnx and onnxruntime, so it runs in LCG_110_cuda (on the CPU), not in the test environments; its
outputs are committed under ``tests/fixtures/nn_classifier/``:

  * ``<family>/model_k<n>_r<r>.onnx``: the model of residue r, exported as the trainer does
    (``bbtautau-nn`` export.py: TorchScript exporter, ``dynamo=False``, opset 17, one file, input ``[1, N]`` float32,
    output ``[1, C]``), each residue with its own weights, so that a fold mix-up changes every score;
  * ``<family>/inputs.txt`` (one event per line) and ``<family>/outputs_r<r>.txt``: onnxruntime's outputs of the
    model of residue r on these events, the reference of ``tests/cpp/test_sm_classifier.cxx``;
  * ``families.json``: inputs, classes, folds, output type and output width of every family, from which the Python
    tests write manifests in the payload layout (``payloads/nn_classifier/README.md``).

Families: ``k2`` (2 folds, 5 classes, probabilities), ``k4`` (4 folds, 5 classes and a binary head, so C + 1
outputs), ``k2_logits`` (2 folds, 3 classes, logits; the friend applies the softmax), ``dynamic`` (a dynamic batch
axis, which the friend refuses) and ``k2_constants`` (2 folds, 5 classes, with the constant inputs ``era_index`` and
``channel_index`` between the columns, as the models of all eras and scopes take them; their values are in every row
of ``inputs.txt`` and in ``families.json`` ``constants``).

    source /cvmfs/sft.cern.ch/lcg/views/LCG_110_cuda/x86_64-el9-gcc13-opt/setup.sh
    CUDA_VISIBLE_DEVICES= python3 tests/fixtures/make_nn_classifier_fixtures.py
"""
import json
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch

OUT = Path(__file__).resolve().parent / "nn_classifier"
OPSET = 17
N_EVENTS = 64

# the inputs of the thesis recipe with the v7b names (nbtag -> n_bjets, njets -> n_jets; mtt_coll_approx is
# computed in the graph of a real model and is no input), all in the main n-tuple or the FastMTT friend
M0_INPUTS = [
    "bpair_btag_value_1", "bpair_btag_value_2", "bpair_deltaR", "bpair_m_inv", "bpair_pt_1", "bpair_pt_dijet",
    "deltaR_ditaupair", "jpt_1", "m_fastmtt", "mjj", "n_bjets", "n_jets", "pt_fastmtt", "m_vis", "mt_tot", "jpt_2",
    "pt_1", "pt_dijet", "pt_vis",
]
V7B_CLASSES = ["HH", "tautau", "Top", "jetFakes", "Other"]
FAMILIES = {
    "k2": dict(folds=2, inputs=M0_INPUTS, classes=V7B_CLASSES, output="probabilities", binary_head=False),
    "k4": dict(
        folds=4,
        inputs=M0_INPUTS + ["pt_2", "met", "metphi", "eta_fastmtt", "phi_fastmtt"],
        classes=V7B_CLASSES,
        output="probabilities",
        binary_head=True,
    ),
    "k2_logits": dict(
        folds=2, inputs=["pt_1", "pt_2", "m_vis", "n_jets"], classes=["HH", "Top", "Other"], output="logits",
        binary_head=False,
    ),
    "dynamic": dict(folds=2, inputs=["pt_1", "pt_2", "m_vis"], classes=["HH", "Other"], output="probabilities",
                    binary_head=False, dynamic=True),
    "k2_constants": dict(
        folds=2, inputs=["pt_1", "era_index", "m_vis", "channel_index", "pt_2", "n_jets"], classes=V7B_CLASSES,
        output="probabilities", binary_head=False, constants={"era_index": 3.0, "channel_index": 1.0},
    ),
}


class Toy(torch.nn.Module):
    """Scaler in the graph, one hidden layer, softmax (or logits), optionally a sigmoid binary head appended."""

    def __init__(self, n_inputs, n_classes, output, binary_head, seed):
        super().__init__()
        generator = torch.Generator().manual_seed(seed)
        self.register_buffer("shift", torch.rand(n_inputs, generator=generator) * 50)
        self.register_buffer("scale", 10 + torch.rand(n_inputs, generator=generator) * 40)
        self.hidden = torch.nn.Linear(n_inputs, 8)
        self.classes = torch.nn.Linear(8, n_classes)
        self.binary = torch.nn.Linear(8, 1) if binary_head else None
        for parameter in self.parameters():
            torch.nn.init.normal_(parameter, std=1.0, generator=generator)
        self.output = output

    def forward(self, x):
        hidden = torch.tanh(self.hidden((x - self.shift) / self.scale))
        scores = self.classes(hidden)
        if self.output == "probabilities":
            scores = torch.softmax(scores, dim=1)
        if self.binary is not None:
            scores = torch.cat([scores, torch.sigmoid(self.binary(hidden))], dim=1)
        return scores


def export(model, n_inputs, path, dynamic):
    with torch.no_grad():
        torch.onnx.export(
            model.eval(),
            (torch.zeros(1, n_inputs),),
            str(path),
            dynamo=False,
            opset_version=OPSET,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}} if dynamic else None,
        )
    onnx.checker.check_model(onnx.load(str(path)))


def write_rows(path, rows):
    path.write_text("".join(" ".join(f"{v:.9g}" for v in row) + "\n" for row in rows))


def main():
    rng = np.random.default_rng(20261025)
    families = {}
    for index, (family, spec) in enumerate(FAMILIES.items()):
        directory = OUT / family
        directory.mkdir(parents=True, exist_ok=True)
        n_inputs, n_classes = len(spec["inputs"]), len(spec["classes"])
        # inputs around the scaler of every residue, read back exactly from the text the C++ test reads
        x = (rng.uniform(0, 50, (N_EVENTS, n_inputs)) + rng.normal(0, 30, (N_EVENTS, n_inputs))).astype(np.float32)
        for name, value in spec.get("constants", {}).items():
            x[:, spec["inputs"].index(name)] = value
        write_rows(directory / "inputs.txt", x)
        x = np.loadtxt(directory / "inputs.txt", dtype=np.float32, ndmin=2)
        outputs = []
        for r in range(spec["folds"]):
            model = Toy(n_inputs, n_classes, spec["output"], spec["binary_head"], seed=100 * index + r)
            path = directory / f"model_k{spec['folds']}_r{r}.onnx"
            export(model, n_inputs, path, spec.get("dynamic", False))
            session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
            got = np.concatenate([session.run(None, {"input": row[None]})[0] for row in x])
            with torch.no_grad():
                expected = model(torch.as_tensor(x)).numpy()
            assert np.abs(got - expected).max() < 1e-6, (family, r)
            write_rows(directory / f"outputs_r{r}.txt", got)
            outputs.append(got)
        # every pair of residues differs on every event, so a fold mix-up is visible in each one
        for a in range(len(outputs)):
            for b in range(a):
                assert np.abs(outputs[a] - outputs[b]).max(axis=1).min() > 1e-3, (family, a, b)
        families[family] = {
            "folds": spec["folds"],
            "inputs": spec["inputs"],
            "classes": spec["classes"],
            "output": spec["output"],
            "n_outputs": n_classes + int(spec["binary_head"]),
            "dynamic": spec.get("dynamic", False),
            **({"constants": spec["constants"]} if "constants" in spec else {}),
        }
    (OUT / "families.json").write_text(json.dumps(families, indent=1) + "\n")


if __name__ == "__main__":
    main()
