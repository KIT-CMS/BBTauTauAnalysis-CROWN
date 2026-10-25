# NN classifier payloads

The models the friend `sm_nn_classifier.py` evaluates (nn spec 3.3, 3.4). Every model of a production is one
directory here, listed in `sm_nn_classifier.MODELS` with the prefix of its columns:

```
payloads/nn_classifier/<model>/
    README.md                       provenance of the model (below)
    <era>/<scope>/manifest.json     2016preVFP, 2016postVFP, 2017, 2018 x et, mt, tt, as the trainer installs it
    onnx/<source>/model_k<n>_r<r>.onnx
```

`model_k<n>_r<r>.onnx` is the model of outer fold r of n: it scores the events with `event % n == r` (unsigned 64-bit
event number), which it never saw in its training (n = 2: `r0` scores the even events and is trained on the odd ones).
A manifest refers to its files by a path relative to itself, so the eras and scopes of a model share them without
copies (`bbtautau-nn install`: `onnx/<channel>/` for an M0 model per channel, `onnx/joint/` for a model of all
channels); a file next to the manifest works as well. The manifest is the one of `bbtautau-nn install`
(`src/bbtautau_nn/install.py`), which assembles this layout from the exports (`export.py`):

| Key | |
|---|---|
| `model`, `channel` | model name and scope; `channel` must be the scope of the directory |
| `folds` | n &ge; 2 |
| `files` | residue `"r"` &rarr; `{"file": ..., "sha256": ...}` for every r < n; `file` is named `model_k<n>_r<r>.onnx`, relative to the manifest and inside the model directory (also after resolving symbolic links) |
| `inputs` | the inputs in the order of the model input: columns of the main n-tuple or of the FastMTT friend (`m/pt/eta/phi_fastmtt`), or constants; derived inputs (`mtt_coll_approx`, scaling, log pT) are computed in the graph |
| `classes` | the class names in the order of the model output (column names `<prefix>nn_score_<class>`) |
| `output` | `probabilities` (softmax in the graph, the default of the contract) or `logits` (the friend applies the softmax) |
| `binary_head` | optional, `true` if the model has a binary head as an extra last output column (spec 6.2, AB16); without it the output must have exactly one column per class, since a manifest missing a class would look like a binary head |
| `constants` | optional, input &rarr; number for the inputs that are constant in the era and scope of the manifest: `era_index` (2016preVFP 0, 2016postVFP 1, 2017 2, 2018 3) and `channel_index` (et 0, mt 1, tt 2) of a model of all eras and scopes (N17), and `iso_1` in tt, which such a graph ignores there; the friend defines a float column `<prefix>constant_<input>` per constant and puts it into the input vector at its position |

Other keys (era, training commit, export, configuration, closure) are provenance only. The friend checks every
manifest when it is configured and fails otherwise: the files exist and have their sha256, the residue files follow
the naming and stay inside the model directory, every file has exactly one float32 input `[1, len(inputs)]` and one
float32 output `[1, C]` or, with `binary_head`, `[1, C + 1]`, without a dynamic dimension (TorchScript export,
`dynamo=False`, opset 17, no `.onnx.data`), every constant is an input and a finite number, and no input read from a
column is a raw DeepTau vsJet score (`iso_2` in every tau scope, `iso_1` in tt, any column named after vsJet): they
define the application region of the jet fakes, so a classifier would learn the jetFakes label from them (nn spec 0,
5.3). The C++ (`cpp_addons/include/sm_classifier.hxx`) checks the shapes again when the sessions open and throws on an
input vector of another length and on a non-finite input or score.

Outputs per model with prefix `p` (e.g. `nn_m0_`): `p + predicted_class` (index of the largest class score, in the
order of `classes`), `p + predicted_max_value`, `p + nn_score_<class>` for every class and, with a binary head,
`p + binary_score`. Events outside the gate (`nn_gate.py`: ShapeSmith's tau skim selection with `control_regions`,
without the opposite-sign requirement) get -1 in every column and are not evaluated.

Paths are relative to the analysis directory; CMake installs `payloads/` next to the friend executable. A new model
or a changed payload needs a new directory here, an entry in `MODELS` and a new friend tag (KingMaker packs the
friend tarball once per tag and production).

The model README (written by `bbtautau-nn install`) records: the date, the training commit, every export with the
sha256 of its manifest, the run configuration, the ML export (directories, profile, sha256 of `classes.json`,
ShapeSmith commits), the inputs and constants, the sha256 of every file and the closure torch vs onnxruntime. No model
is installed yet: none is trained on v7b (nn spec 10, AP3/AP8).
