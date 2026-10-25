# NN classifier payloads

The models the friend `sm_nn_classifier.py` evaluates (nn spec 3.3, 3.4). Every model of a production is one
directory here, listed in `sm_nn_classifier.MODELS` with the prefix of its columns:

```
payloads/nn_classifier/<model>/
    README.md                       provenance of the model (below)
    <era>/<scope>/manifest.json     2016preVFP, 2016postVFP, 2017, 2018 x et, mt, tt, as the trainer writes it
    <era>/<scope>/model_k<n>_r<r>.onnx
```

`model_k<n>_r<r>.onnx` is the model of outer fold r of n: it scores the events with `event % n == r` (unsigned 64-bit
event number), which it never saw in its training (n = 2: `r0` scores the even events and is trained on the odd ones).
The manifest is the one of `bbtautau-nn export` (`src/bbtautau_nn/export.py`):

| Key | |
|---|---|
| `model`, `channel` | model name and scope; `channel` must be the scope of the directory |
| `folds` | n &ge; 2 |
| `files` | residue `"r"` &rarr; `{"file": "model_k<n>_r<r>.onnx", "sha256": ...}` for every r < n |
| `inputs` | the input columns in the order of the model input: columns of the main n-tuple or of the FastMTT friend (`m/pt/eta/phi_fastmtt`); derived inputs (`mtt_coll_approx`, scaling, log pT) are computed in the graph |
| `classes` | the class names in the order of the model output (column names `<prefix>nn_score_<class>`) |
| `output` | `probabilities` (softmax in the graph, the default of the contract) or `logits` (the friend applies the softmax) |
| `binary_head` | optional, `true` if the model has a binary head as an extra last output column (spec 6.2, AB16); without it the output must have exactly one column per class, since a manifest missing a class would look like a binary head |

Other keys (training commit, configuration, closure) are provenance only. The friend checks every manifest when it is
configured and fails otherwise: the files exist and have their sha256, the residue files follow the naming, and every
file has exactly one float32 input `[1, len(inputs)]` and one float32 output `[1, C]` or, with `binary_head`,
`[1, C + 1]`, without a dynamic dimension (TorchScript export, `dynamo=False`, opset 17, no `.onnx.data`).
The C++ (`cpp_addons/include/sm_classifier.hxx`) checks the shapes again when the sessions open and throws on an input
vector of another length and on a non-finite input or score.

Outputs per model with prefix `p` (e.g. `nn_m0_`): `p + predicted_class` (index of the largest class score, in the
order of `classes`), `p + predicted_max_value`, `p + nn_score_<class>` for every class and, with a binary head,
`p + binary_score`. Events outside the gate (`nn_gate.py`: ShapeSmith's tau skim selection with `control_regions`,
without the opposite-sign requirement) get -1 in every column and are not evaluated.

Paths are relative to the analysis directory; CMake installs `payloads/` next to the friend executable. A new model
or a changed payload needs a new directory here, an entry in `MODELS` and a new friend tag (KingMaker packs the
friend tarball once per tag and production).

The model README records: the training repository and commit (`manifest.json` `training`), the run configuration, the
ML export (ShapeSmith run YAML, `ml_dir`, commit), the classes and their processes, the sha256 of every file and the
closure torch vs onnxruntime (`onnxruntime_closure`). No model is installed yet: none is trained on v7b
(nn spec 10, AP3/AP8).
