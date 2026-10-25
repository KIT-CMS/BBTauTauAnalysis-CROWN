"""NN classifier friend sm_nn_classifier (nn spec 3.3, 3.4, N21): the payload checks at configuration time and
the gate.

A wrong payload must fail the configuration, not give scores: a manifest of another scope, a file that is
missing or changed after the manifest, a model whose shapes differ from the manifest or have a dynamic
dimension, or residue files named against the convention. The gate must keep every event of the ShapeSmith
tau skims (tau_control and tau_ff), and its C++ translation must select what ShapeSmith's pandas.eval selects.
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

from analysis_configurations.bbtautau import friend_common, nn_gate, nn_payloads, sm_nn_classifier
from analysis_configurations.bbtautau.constants import ERAS_RUN2, LEGACY_AVAILABLE_SAMPLES, SCOPES
from analysis_configurations.bbtautau.nn_payloads import NNModel
from analysis_configurations.bbtautau.tests.helpers import nn_classifier_maps, nn_classifier_payload
from code_generation.exceptions import InvalidInputError

TAU_SCOPES = ("et", "mt", "tt")
ANALYSIS = Path(nn_payloads.__file__).resolve().parent


def build(models, tmp_path, era="2018", scope="mt", analysis_dir=None):
    logging.disable(logging.CRITICAL)
    try:
        with mock.patch.object(sm_nn_classifier, "MODELS", models), mock.patch.object(
            friend_common, "ANALYSIS_DIR", analysis_dir or friend_common.ANALYSIS_DIR
        ):
            return sm_nn_classifier.build_config(
                era, "ttbar", [scope], {"none"}, LEGACY_AVAILABLE_SAMPLES, sm_nn_classifier.AVAILABLE_ERAS, SCOPES,
                nn_classifier_maps(era, tmp_path),
            )
    finally:
        logging.disable(logging.NOTSET)


# --- payload checks ---------------------------------------------------------------


def _set(key, value):
    def edit(manifest, era, scope):
        manifest[key] = value(manifest) if callable(value) else value

    return edit


def _file(residue, key, value):
    def edit(manifest, era, scope):
        manifest["files"][str(residue)][key] = value

    return edit


def _swap_residues(manifest, era, scope):
    manifest["files"]["0"], manifest["files"]["1"] = manifest["files"]["1"], manifest["files"]["0"]


@pytest.mark.parametrize(
    "edit,message",
    [
        (_set("channel", "et"), "channel 'et'"),
        (_set("folds", 1), "folds 1"),
        (_set("output", "scores"), "output 'scores'"),
        (_set("inputs", lambda m: m["inputs"] + ["met"]), "takes 19 inputs, the manifest lists 20"),
        (_set("inputs", lambda m: m["inputs"][:-1] + [m["inputs"][0]]), "duplicate inputs"),
        (_set("classes", lambda m: m["classes"][:-1]), "gives 5 outputs, the manifest declares 4"),
        (_set("binary_head", True), "gives 5 outputs, the manifest declares 6"),
        (_set("classes", lambda m: m["classes"][:-1] + ["jet-fakes"]), "no column name"),
        (_set("files", lambda m: {"0": m["files"]["0"]}), "expected the residues 0 .. 1"),
        (_file(1, "sha256", "0" * 64), "sha256 of model_k2_r1.onnx"),
        (_file(1, "file", "model_k2_r0.onnx"), "residue 1 is 'model_k2_r0.onnx'"),
        (_swap_residues, "residue 0 is 'model_k2_r1.onnx'"),
        (lambda m, era, scope: m.pop("classes"), "missing keys ['classes']"),
    ],
    ids=[
        "scope", "one_fold", "output_type", "input_count", "duplicate_input", "output_count", "binary_head",
        "class_name", "residues", "sha256", "file_name", "swapped_residues", "missing_key",
    ],
)
def test_manifest_errors_fail_the_configuration(edit, message, tmp_path):
    payload = nn_classifier_payload("k2", tmp_path / "m0", eras=["2018"], scopes=["mt"], edit=edit)
    with pytest.raises(ValueError, match=re.escape(message)):
        build((NNModel(payload, "nn_m0_"),), tmp_path)


def test_dynamic_dimension_fails_the_configuration(tmp_path):
    payload = nn_classifier_payload("dynamic", tmp_path / "dynamic", eras=["2018"], scopes=["mt"])
    with pytest.raises(ValueError, match="without a dynamic dimension"):
        build((NNModel(payload, "nn_dyn_"),), tmp_path)


def test_missing_file_and_era_fail_the_configuration(tmp_path):
    payload = nn_classifier_payload("k2", tmp_path / "m0", eras=["2018"], scopes=["mt"])
    with pytest.raises(ValueError, match="no manifest for 2017 mt"):
        build((NNModel(payload, "nn_m0_"),), tmp_path, era="2017")
    os.remove(Path(payload) / "2018/mt/model_k2_r1.onnx")
    with pytest.raises(ValueError, match="model_k2_r1.onnx is missing"):
        build((NNModel(payload, "nn_m0_"),), tmp_path)


@pytest.mark.parametrize("prefixes", [("nn_m0_", "nn_m0_"), ("nn_m0",), ("",), ("nn-m0_",)])
def test_column_prefixes_are_unique_names(prefixes, tmp_path):
    payload = nn_classifier_payload("k2", tmp_path / "m0", eras=["2018"], scopes=["mt"])
    with pytest.raises(ValueError, match="prefixes"):
        build(tuple(NNModel(payload, prefix) for prefix in prefixes), tmp_path)


def test_light_lepton_scopes_are_refused(tmp_path):
    payload = nn_classifier_payload("k2", tmp_path / "m0", eras=["2018"], scopes=["mt"])
    with pytest.raises(ValueError, match="not in em"):
        build((NNModel(payload, "nn_m0_"),), tmp_path, scope="em")


def test_unknown_input_column_fails_the_configuration(tmp_path):
    def rename(manifest, era, scope):
        manifest["inputs"][0] = "mtt_coll_approx"  # computed in the graph of a real model, no n-tuple column

    payload = nn_classifier_payload("k2", tmp_path / "m0", eras=["2018"], scopes=["mt"], edit=rename)
    with pytest.raises(InvalidInputError, match="mtt_coll_approx"):
        build((NNModel(payload, "nn_m0_"),), tmp_path)


def test_logits_take_the_softmax_and_files_are_relative_to_the_analysis(tmp_path):
    """A model giving logits gets the softmax in C++; a payload directory relative to the analysis directory
    (the layout of payloads/nn_classifier, installed next to the executable) stays relative."""
    relative = "payloads/nn_classifier/logits_v1"
    nn_classifier_payload("k2_logits", tmp_path / relative, eras=["2018"], scopes=["mt"])
    config = build((NNModel(relative, "nn_l_"),), tmp_path, analysis_dir=str(tmp_path))
    nominal = config.config_parameters["mt"]["nominal"]
    assert nominal["nn_l_softmax"] is True and nominal["nn_l_num_outputs"] == 3
    assert nominal["nn_l_onnx_file_r1"] == f"{relative}/2018/mt/model_k2_r1.onnx"


def test_payload_readme_exists():
    """payloads/nn_classifier holds the layout description; no model is installed before one is trained on v7b."""
    assert (ANALYSIS / "payloads/nn_classifier/README.md").is_file()
    assert sm_nn_classifier.MODELS == ()


# --- gate ---------------------------------------------------------------------------

_UPPER_BOUND = re.compile(r"\(?(\w+) < ([0-9.]+)\)?\Z")


def implied(cut, gate_cut):
    """``cut`` implies ``gate_cut``: the same cut, ``gate_cut`` an OR with ``cut``, or the same upper
    bound on a column, at least as high in the gate."""
    if gate_cut == cut or gate_cut.endswith(f" | ({cut})"):
        return True
    bound, gate_bound = _UPPER_BOUND.match(cut), _UPPER_BOUND.match(gate_cut)
    return bool(bound and gate_bound and bound[1] == gate_bound[1] and float(gate_bound[2]) >= float(bound[2]))


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("channel", TAU_SCOPES)
def test_gate_contains_the_tau_skims(channel, era):
    """N21: the gate is a conjunction of cuts, each implied by the cut of the same name of the tau_ff skim
    selection, and equal to the tau_control one, so both skims are subsets (ShapeSmith's sample cuts only
    remove events)."""
    gate = nn_gate.skim_cuts(channel, era)
    tau_ff = nn_gate.tau_ff_cuts(channel, era)
    assert "os" not in gate and ("hem_veto" in gate) == (era == "2018")
    for name, cut in gate.items():
        assert name in tau_ff and implied(tau_ff[name], cut), (name, tau_ff.get(name), cut)
    assert set(tau_ff) - set(gate) == ({"mt_cut"} if channel != "tt" else set())


def shapesmith_cuts():
    """ShapeSmith's analysis cuts module from the sibling checkouts (SHAPESMITH_DIR, default the ShapeSmith
    folder next to KingMaker), or skip."""
    root = Path(os.environ.get("SHAPESMITH_DIR", ANALYSIS.parents[3] / "ShapeSmith"))
    sources = [root / "ShapeSmith/src", root / "BBTauTauAnalysis-ShapeSmith/src"]
    if not all(path.is_dir() for path in sources):
        pytest.skip(f"ShapeSmith checkouts not found under {root}")
    sys.path[:0] = [str(path) for path in sources]
    try:
        from bbtautau_shapesmith import cuts
    except ImportError as error:
        pytest.skip(f"ShapeSmith not importable: {error}")
    finally:
        del sys.path[: len(sources)]
    return cuts


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("channel", TAU_SCOPES)
def test_gate_is_shapesmiths_skim_selection(channel, era):
    """The gate is ShapeSmith's skim_cuts(control_regions=True), cut by cut and in order, and
    nn_gate.tau_ff_cuts its skim_cuts(control_regions=False)."""
    cuts = shapesmith_cuts()
    assert list(nn_gate.skim_cuts(channel, era).items()) == list(cuts.skim_cuts(channel, era, True).items())
    assert nn_gate.tau_ff_cuts(channel, era) == cuts.skim_cuts(channel, era, False)


def test_gate_translation():
    expression, columns = nn_gate.cpp_expression(
        {"a": "(n_jets >= 2) | ((n_bjets >= 1) & (bpair_pt_2 > 0))", "b": "(abs(eta_1) < 2.1)", "c": "iso_1 < 0.5"}
    )
    assert columns == ["n_jets", "n_bjets", "bpair_pt_2", "eta_1", "iso_1"]
    assert expression == "(($0 >= 2) || (($1 >= 1) && ($2 > 0))) && ((std::abs($3) < 2.1)) && ($4 < 0.5)"
    for unsupported in ("~(pt_1 > 3)", "pt_1 + pt_2 > 3", "(pt_1 > 3) and (pt_2 > 3)", "pt_1 > 1e3", "sqrt(pt_1) > 3"):
        with pytest.raises(ValueError, match="cannot translate"):
            nn_gate.cpp_expression({"x": unsupported})


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("channel", TAU_SCOPES)
def test_gate_translation_selects_what_pandas_selects(channel, era):
    """The translated expression in RDataFrame (cling) and ShapeSmith's cuts in pandas.eval give the same
    flag on random events around every threshold, in all sample kinds."""
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    ROOT = pytest.importorskip("ROOT")
    cuts = nn_gate.skim_cuts(channel, era)
    expression, columns = nn_gate.cpp_expression(cuts)
    rng = np.random.default_rng(sum(map(ord, channel + era)))
    n = 20000
    kind = rng.integers(0, 3, n)
    values = {}
    for column in columns:
        if column in ("is_data", "is_mc", "is_embedding"):
            values[column] = kind == ("is_data", "is_mc", "is_embedding").index(column)
        elif column.startswith(("trg_", "id_tau_")):
            values[column] = rng.random(n) < 0.9
        elif column.endswith("_veto"):
            values[column] = rng.random(n) < 0.1
        elif column in ("n_jets", "n_bjets"):
            values[column] = rng.integers(0, 4, n).astype(np.int32)
        elif column.startswith("eta_"):
            values[column] = rng.uniform(-2.5, 2.5, n).astype(np.float32)
        elif column == "iso_1":
            values[column] = rng.uniform(0, 0.6, n).astype(np.float32)
        elif column == "bpair_pt_2":
            values[column] = rng.choice(np.array([-10, 0, 40], dtype=np.float32), n)
        else:  # pT
            values[column] = rng.uniform(20, 60, n).astype(np.float32)
    expected = np.ones(n, dtype=bool)
    frame = pd.DataFrame(values)
    for cut in cuts.values():
        expected &= pd.eval(cut, resolvers=(frame,)).to_numpy(dtype=bool)
    code = re.sub(r"\$(\d+)", lambda match: columns[int(match[1])], expression)
    arrays = {name: (array.astype(np.int32) if array.dtype == bool else array) for name, array in values.items()}
    flags = ROOT.RDF.FromNumpy(arrays).Define("gate", f"static_cast<bool>({code})").AsNumpy(["gate"])["gate"]
    assert 0.01 < expected.mean() < 0.99
    assert (flags.astype(bool) == expected).all()
