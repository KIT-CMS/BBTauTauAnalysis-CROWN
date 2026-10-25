"""Friend-tree entry points: dispatch marker, era gate, output contracts, FF shifts and the NN classifier.

The friend entries are thin wrappers around bodies shared in ``friend_common``,
so what is worth testing are the surfaces where a mistake is silent: the
``FriendTreeConfiguration`` marker ``generate_friends.run()`` dispatches on
(otherwise-unused ``# noqa: F401`` code an import cleanup would delete), the era
gate that must fire before ``build_config``, the emitted leaves, and the
payload-driven fake-factor shifts (a wrong syst key silently evaluates nominal).
"""

import functools
import gzip
import inspect
import json
import logging
from pathlib import Path
from unittest import mock

import pytest

from analysis_configurations.bbtautau import (
    fake_factors_friend_config,
    generate_friends,
    nmssm_fastmtt,
    nmssm_kinfit_resolved,
    nn_gate,
    sm_fake_factors,
    sm_fake_factors_w,
    sm_fastmtt,
    sm_kinfit_resolved,
    sm_nn_classifier,
)
from analysis_configurations.bbtautau.constants import (
    ERAS,
    ERAS_RUN2,
    LEGACY_AVAILABLE_SAMPLES,
    SCOPES,
)
from analysis_configurations.bbtautau.nn_payloads import NNModel
from analysis_configurations.bbtautau.producers import fakefactors
from analysis_configurations.bbtautau.tests.helpers import (
    FakeArgs,
    find_producer,
    nn_classifier_maps,
    nn_classifier_payload,
    output_names,
)
from code_generation.exceptions import InvalidInputError

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MAP_FASTMTT, MAP_KINFIT = str(FIXTURES / "fastmtt_quantities_map.json"), str(
    FIXTURES / "kinfit_quantities_map.json"
)
MAP_FF_2018, MAP_FF_2023, MAP_FF_2024 = (
    str(FIXTURES / f"fake_factors_{era}_quantities_map.json")
    for era in ("2018", "2023postBPix", "2024")
)
ENTRY_MODULES = (
    nmssm_fastmtt,
    sm_fastmtt,
    sm_kinfit_resolved,
    nmssm_kinfit_resolved,
    fake_factors_friend_config,
    sm_fake_factors,
    sm_fake_factors_w,
    sm_nn_classifier,
)

FASTMTT_LEAVES = {"m_fastmtt", "pt_fastmtt", "eta_fastmtt", "phi_fastmtt"}
# The SM fixed-mass (125/125) fit exposes only these four, the NMSSM fit all 18.
SM_KINFIT_LEAVES = {"kinfit_convergence", "kinfit_chi2", "kinfit_prob", "kinfit_mHH"}
NMSSM_KINFIT_LEAVES = {
    f"kinfit_{quantity}{suffix}"
    for suffix in ("_YToBB", "_YToTauTau", "")
    for quantity in ("convergence", "mX", "mY", "mh", "chi2", "prob")
}


@pytest.mark.parametrize(
    "module", ENTRY_MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1]
)
def test_friend_entry_points_expose_friendtreeconfiguration(module):
    members = [name for name, _ in inspect.getmembers(module, inspect.isclass)]
    assert "FriendTreeConfiguration" in members
    assert (
        "Configuration" not in members
    )  # both markers would make generate_friends.run() raise


@pytest.mark.parametrize(
    "name,module,rejected_era",
    [
        ("sm_fastmtt", sm_fastmtt, "2024"),
        ("sm_kinfit_resolved", sm_kinfit_resolved, "2024"),
        ("sm_fake_factors", sm_fake_factors, "2024"),
        ("sm_fake_factors_w", sm_fake_factors_w, "2024"),
        ("sm_nn_classifier", sm_nn_classifier, "2024"),
        ("fake_factors_friend_config", fake_factors_friend_config, "2018"),
    ],
)
def test_friend_era_gates_fire_before_build_config(name, module, rejected_era):
    with mock.patch.object(
        module, "build_config", side_effect=AssertionError("must not be called")
    ):
        with pytest.raises(ValueError, match=rejected_era):
            generate_friends.run(FakeArgs(name, rejected_era))


@pytest.mark.parametrize(
    "module,scope,quantities_map,expected",
    [
        (nmssm_fastmtt, "mt", MAP_FASTMTT, FASTMTT_LEAVES),
        (sm_fastmtt, "mt", MAP_FASTMTT, FASTMTT_LEAVES),
        (sm_kinfit_resolved, "mt", MAP_KINFIT, SM_KINFIT_LEAVES),
        (nmssm_kinfit_resolved, "mt", MAP_KINFIT, NMSSM_KINFIT_LEAVES),
        (sm_fake_factors, "et", MAP_FF_2018, {"fake_factor_raw", "fake_factor"}),
        (sm_fake_factors, "mt", MAP_FF_2018, {"fake_factor_raw", "fake_factor"}),
        (
            sm_fake_factors,
            "tt",
            MAP_FF_2018,
            {"fake_factor_1_raw", "fake_factor_1", "fake_factor_2_raw", "fake_factor_2"},
        ),
    ],
    ids=lambda x: x.__name__.rsplit(".", 1)[-1] if inspect.ismodule(x) else None,
)
def test_friend_output_contracts(module, scope, quantities_map, expected):
    config = module.build_config(
        "2018",
        "ttbar",
        [scope],
        {"none"},
        LEGACY_AVAILABLE_SAMPLES,
        list(getattr(module, "AVAILABLE_ERAS", ERAS)),
        SCOPES,
        quantities_map,
    )
    assert output_names(config, scope) == expected


def relabelled_map(path, era, tmp_path):
    """The 2018 fixture quantities map relabelled to ``era``."""
    quantities_map = json.loads(Path(path).read_text())
    quantities_map["quantities"] = {era: quantities_map["quantities"].pop("2018")}
    quantities_map["metadata"]["era"] = era
    relabelled = tmp_path / f"{era}_{Path(path).name}"
    relabelled.write_text(json.dumps(quantities_map))
    return str(relabelled)


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize(
    "module,quantities_map,expected",
    [
        (sm_fastmtt, MAP_FASTMTT, FASTMTT_LEAVES),
        (sm_kinfit_resolved, MAP_KINFIT, SM_KINFIT_LEAVES),
    ],
    ids=["sm_fastmtt", "sm_kinfit_resolved"],
)
def test_sm_friends_build_in_every_run2_era(module, quantities_map, expected, era, tmp_path):
    """The SM FastMTT and kinematic-fit friends hold no era-specific input."""
    assert module.AVAILABLE_ERAS == ERAS_RUN2
    config = module.build_config(
        era,
        "ttbar",
        ["mt"],
        {"none"},
        LEGACY_AVAILABLE_SAMPLES,
        module.AVAILABLE_ERAS,
        SCOPES,
        relabelled_map(quantities_map, era, tmp_path),
    )
    assert output_names(config, "mt") == expected


def test_sm_fake_factor_payload_eras():
    """Both 2016 halves read the one 2016 payload; an era is available once its
    payload directory exists."""
    eras = sm_fake_factors.PAYLOAD_ERAS
    assert set(eras) == set(ERAS_RUN2)
    assert eras["2016preVFP"] == eras["2016postVFP"] == "2016"
    analysis = Path(sm_fake_factors.__file__).parent
    assert sm_fake_factors.AVAILABLE_ERAS == list(sm_fake_factors.SM_PAYLOAD_DIRS)
    for era, directory in sm_fake_factors.SM_PAYLOAD_DIRS.items():
        assert directory == sm_fake_factors.PAYLOADS[eras[era]]
        assert directory.endswith(f"/{eras[era]}") and (analysis / directory).is_dir(), era


# --- fake-factor shifts ---------------------------------------------------------

# Variation parameter -> the parameter holding its correction name, over all legs.
NAME_PARAMETER = {
    prefix + wiring.variation: prefix + wiring.name
    for prefix in fakefactors.LEG_PREFIXES.values()
    for wiring in fakefactors.ROLE_WIRING.values()
}
RAW_VARIATIONS = {
    prefix + fakefactors.ROLE_WIRING[role].variation
    for prefix in fakefactors.LEG_PREFIXES.values()
    for role in fakefactors.RAW_ROLES
}


@functools.lru_cache(maxsize=None)
def build_all_shifts(module, era, scope, quantities_map):
    logging.disable(logging.CRITICAL)
    try:
        return module.build_config(
            era, "ttbar", [scope], {"all"}, LEGACY_AVAILABLE_SAMPLES,
            module.AVAILABLE_ERAS, SCOPES, quantities_map,
        )
    finally:
        logging.disable(logging.NOTSET)


def ff_shifts(config, scope):
    """Shift name -> parameter mapping of the fake-factor shifts (main-n-tuple shifts have none)."""
    return {name: mapping for name, mapping in config.shifts[scope].items() if mapping}


def payload_syst_keys(file, correction):
    """All syst keys of ``correction`` (of its stack members, if compound), from the JSON."""
    with gzip.open(Path(fake_factors_friend_config.__file__).parent / file, "rt") as handle:
        payload = json.load(handle)
    by_name = {c["name"]: c for c in payload["corrections"]}
    compounds = {c["name"]: c["stack"] for c in payload.get("compound_corrections") or []}
    members = compounds.get(correction, [correction])
    return {item["key"] for member in members for item in by_name[member]["data"]["content"]}


def assert_shifts_set_payload_keys(config, scope):
    nominal = config.config_parameters[scope]["nominal"]
    for name, mapping in ff_shifts(config, scope).items():
        ((parameter, key),) = mapping.items()
        file = nominal["ff_file" if parameter in RAW_VARIATIONS else "ff_corr_file"]
        assert key in payload_syst_keys(file, nominal[NAME_PARAMETER[parameter]]), name


@pytest.mark.parametrize("scope,expected", [("mt", 34), ("tt", 68)])
def test_sm_fake_factor_shifts(scope, expected):
    config = build_all_shifts(sm_fake_factors, "2018", scope, MAP_FF_2018)
    shifts = ff_shifts(config, scope)
    assert len(shifts) == expected
    assert_shifts_set_payload_keys(config, scope)
    if scope == "mt":
        assert shifts["__process_fractionsfrac_QCDUp"] == {
            "ff_fraction_variation": "process_fractionsfrac_QCD_up"
        }
    else:
        for mapping in shifts.values():
            ((parameter, key),) = mapping.items()
            assert parameter.startswith("ff_2_" if "_subleading" in key else "ff_1_")


@pytest.mark.parametrize("scope", ["mt", "tt"])
def test_sm_corrections_do_not_shift_the_raw_fake_factor(scope):
    config = build_all_shifts(sm_fake_factors, "2018", scope, MAP_FF_2018)
    for name, mapping in ff_shifts(config, scope).items():
        (parameter,) = mapping
        shifted = {q.name for q in config.outputs[scope] if name in q.get_shifts(scope)}
        assert len({leaf.removesuffix("_raw") for leaf in shifted}) == 1, name  # one leg
        assert any(leaf.endswith("_raw") for leaf in shifted) == (parameter in RAW_VARIATIONS)
        assert any(not leaf.endswith("_raw") for leaf in shifted), name


@pytest.mark.parametrize("scope", ["et", "mt", "tt"])
def test_sm_fake_factors_build_on_embedding(scope, tmp_path):
    """The friend runs on the embedding n-tuples like on MC and propagates their tau
    energy scale shifts, here the ttbar fixture relabelled as embedding."""
    quantities_map = json.loads(Path(MAP_FF_2018).read_text())
    ttbar = quantities_map["quantities"]["2018"].pop("ttbar")
    quantities_map["quantities"]["2018"]["embedding"] = {
        name: {
            "": inputs[""],
            "CMS_scale_t_emb_DeepTau2018v2p5_DM10_2018Up": inputs[
                "CMS_scale_t_DeepTau2018v2p5_DM0_pt20to40_genTau_2018Up"
            ],
        }
        for name, inputs in ttbar.items()
    }
    quantities_map["metadata"]["sample_type"] = "embedding"
    path = tmp_path / "quantities_map.json"
    path.write_text(json.dumps(quantities_map))
    config = sm_fake_factors.build_config(
        "2018", "embedding", [scope], {"all"}, LEGACY_AVAILABLE_SAMPLES,
        sm_fake_factors.AVAILABLE_ERAS, SCOPES, str(path),
    )
    assert "__CMS_scale_t_emb_DeepTau2018v2p5_DM10_2018Up" in config.shifts[scope]
    assert len(ff_shifts(config, scope)) == (68 if scope == "tt" else 34)


def test_nmssm_fake_factor_shifts_follow_the_payload():
    config = build_all_shifts(fake_factors_friend_config, "2024", "mt", MAP_FF_2024)
    assert_shifts_set_payload_keys(config, "mt")
    config = build_all_shifts(fake_factors_friend_config, "2023postBPix", "mt", MAP_FF_2023)
    assert_shifts_set_payload_keys(config, "mt")
    # the 06-10 payload holds the hardwired set before the payload-driven friend,
    # with the payload's fracTTbarUnc spelling (fracTTBarUnc evaluated nominal
    # silently)
    expected = {
        f"__{value}{direction}"
        for value in [
            "QCDFFunc", "QCDFFmcSubUnc", "ttbarFFunc",
            "process_fractionsfracQCDUnc", "process_fractionsfracTTbarUnc",
            *[
                f"{prefix}_Corr{kind}"
                for prefix in ["QCD_DR_SR", "QCD_non_closure", "ttbar_non_closure"]
                for kind in ["Stat1Sigma", "SystMCShift", "SystBandAsym"]
            ],
        ]
        for direction in ["Up", "Down"]
    }
    assert set(ff_shifts(config, "mt")) == expected


# --- fake factors with W (v7 spec C15) ------------------------------------------


@pytest.fixture(scope="module")
def wjets_payload(tmp_path_factory):
    """A QCD + W + ttbar payload of et and mt, derived from the SM 2018 one
    (tests/fixtures/make_wjets_fake_factor_payload.py)."""
    import sys

    sys.path.insert(0, str(FIXTURES))
    try:
        import make_wjets_fake_factor_payload as wjets
    finally:
        sys.path.remove(str(FIXTURES))
    source = Path(sm_fake_factors.__file__).parent / sm_fake_factors.SM_PAYLOAD_DIRS["2018"]
    return wjets.make(source, tmp_path_factory.mktemp("wjets_payload"))


def build_wjets_friend(payload, scope, shifts=("all",)):
    from analysis_configurations.bbtautau.friend_common import build_fake_factor_friend

    logging.disable(logging.CRITICAL)
    try:
        return build_fake_factor_friend(
            str(payload), "2018", "ttbar", [scope], set(shifts), LEGACY_AVAILABLE_SAMPLES,
            sm_fake_factors.AVAILABLE_ERAS, SCOPES, MAP_FF_2018,
        )
    finally:
        logging.disable(logging.NOTSET)


@pytest.mark.parametrize("scope", ["et", "mt"])
def test_fake_factor_friend_with_wjets(wjets_payload, scope):
    """C15: a QCD + W + ttbar payload adds the W fake factors, DR->SR correction and
    closure to the sum and their shifts (W fake factors and W fractions also act on
    the raw fake factor); the outputs stay the same columns."""
    config = build_wjets_friend(wjets_payload, scope)
    assert output_names(config, scope) == {"fake_factor_raw", "fake_factor"}
    nominal = config.config_parameters[scope]["nominal"]
    assert nominal["ff_wjets_name"] == "Wjets_fake_factors"
    assert nominal["ff_corr_dr_sr_wjets_name"] == "Wjets_DR_SR_correction"
    assert nominal["ff_corr_closure_wjets_name"] == "Wjets_compound_correction"
    shifts = ff_shifts(config, scope)
    assert len(shifts) == 54  # 34 of QCD + ttbar, 18 of W, 2 of the W fractions
    assert shifts["__WjetsStatShiftUp"] == {"ff_wjets_variation": "WjetsStatShiftUp"}
    assert shifts["__process_fractionsfrac_WjetsUp"] == {
        "ff_fraction_variation": "process_fractionsfrac_Wjets_up"
    }
    for name, mapping in shifts.items():
        (parameter,) = mapping
        shifted = {q.name for q in config.outputs[scope] if name in q.get_shifts(scope)}
        raw = parameter in RAW_VARIATIONS
        assert ("fake_factor_raw" in shifted) == raw and "fake_factor" in shifted, name
    (corrected,) = [p for p in config.producers[scope] if p.name == "FakeFactor_lt"]
    assert '{vec_open}"QCD", "Wjets", "ttbar"{vec_close}' in corrected.call
    assert '{vec_open}"QCD", "Wjets", "QCD", "Wjets", "ttbar"{vec_close}' in corrected.call
    assert [q.name for q in corrected.input[scope]] == [
        "ff_input_fraction", "ff_input_qcd", "ff_input_wjets", "ff_input_tt",
        "ff_corr_dr_sr_input_qcd", "ff_corr_dr_sr_input_wjets",
        "ff_corr_closure_input_qcd", "ff_corr_closure_input_wjets", "ff_corr_closure_input_tt",
    ]


@pytest.mark.parametrize("scope", ["et", "mt", "tt"])
def test_two_process_friend_sums_qcd_and_ttbar(scope):
    """The measured QCD + ttbar payload sums exactly these two processes, with the
    corrections in the order of the friend before C15."""
    config = build_all_shifts(sm_fake_factors, "2018", scope, MAP_FF_2018)
    for producer in config.producers[scope]:
        if producer.name.startswith("FakeFactor_"):
            assert '{vec_open}"QCD", "ttbar"{vec_close}' in producer.call
            assert '{vec_open}"QCD", "QCD", "ttbar"{vec_close}' in producer.call
            assert "{vec_open}0, 1, 1{vec_close}" in producer.call


# --- the two fake-factor friends of P5 side by side (v7 spec E18, C15) ----------

_GENERATE_FRIEND = """
import json, logging, sys
from analysis_configurations.bbtautau import {module}
from analysis_configurations.bbtautau.constants import LEGACY_AVAILABLE_SAMPLES, SCOPES
from code_generation.code_generation import CodeGenerator
payload, scope, quantities_map, directory = json.loads(sys.argv[1])
{module}.SM_PAYLOAD_DIRS["2018"] = payload
logging.disable(logging.CRITICAL)
config = {module}.build_config("2018", "ttbar", [scope], {{"none"}}, LEGACY_AVAILABLE_SAMPLES,
                               ["2018"], SCOPES, quantities_map)
generator = CodeGenerator("code_generation/analysis_template_friends.cxx",
                          "code_generation/subset_template.cxx", config, "bbtautau",
                          "{module}", "{module}_ttbar_2018_" + scope, directory)
generator.generate_code()
"""


def generate_friend(module, payload, scope, directory):
    """Generate the C++ code of a fake-factor friend entry point with ``payload`` in
    a subprocess (code generation mutates module-level producers)."""
    import subprocess
    import sys

    name = module.__name__.rsplit(".", 1)[-1]
    arguments = json.dumps([str(payload), scope, MAP_FF_2018, str(directory)])
    return subprocess.run(
        [sys.executable, "-c", _GENERATE_FRIEND.format(module=name), arguments],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )


def test_fake_factor_entry_points_share_the_payload_eras():
    """ff_v7 and ff_v7_w are built from one checkout, with the same era mapping."""
    assert sm_fake_factors_w.PAYLOAD_ERAS is sm_fake_factors.PAYLOAD_ERAS
    assert sm_fake_factors.PROCESSES == ("QCD", "ttbar")
    assert sm_fake_factors_w.PROCESSES == ("QCD", "Wjets", "ttbar")
    # tt has no W+jets fake factor: ff_v7b_w of tt sums QCD + ttbar
    assert sm_fake_factors_w.SCOPE_PROCESSES == {"et": sm_fake_factors_w.PROCESSES, "mt": sm_fake_factors_w.PROCESSES, "tt": sm_fake_factors.PROCESSES}
    assert set(sm_fake_factors_w.SM_PAYLOAD_DIRS) <= set(ERAS_RUN2)
    assert sm_fake_factors_w.AVAILABLE_ERAS == list(sm_fake_factors_w.SM_PAYLOAD_DIRS)
    analysis = Path(sm_fake_factors_w.__file__).parent
    for era, directory in sm_fake_factors_w.SM_PAYLOAD_DIRS.items():
        assert directory == sm_fake_factors_w.PAYLOADS[sm_fake_factors_w.PAYLOAD_ERAS[era]]
        assert (analysis / directory).is_dir(), era
        assert directory not in sm_fake_factors.PAYLOADS.values(), era


@pytest.mark.parametrize("scope", ["et", "mt"])
def test_both_fake_factor_entry_points_generate(wjets_payload, scope, tmp_path):
    """sm_fake_factors generates with the two-process payload, sm_fake_factors_w with
    the three-process one, and each rejects the payload of the other variant."""
    two = Path(sm_fake_factors.__file__).parent / sm_fake_factors.SM_PAYLOAD_DIRS["2018"]
    cases = [
        (sm_fake_factors, two, True),
        (sm_fake_factors_w, wjets_payload, True),
        (sm_fake_factors, wjets_payload, False),
        (sm_fake_factors_w, two, False),
    ]
    for index, (module, payload, accepted) in enumerate(cases):
        directory = tmp_path / str(index)
        directory.mkdir()
        result = generate_friend(module, payload, scope, directory)
        if accepted:
            assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
            sources = "\n".join(p.read_text() for p in directory.rglob("*.cxx"))
            assert "FakeFactor" in sources
            assert ('"Wjets"' in sources) == (module is sm_fake_factors_w)
        else:
            assert result.returncode != 0
            assert "this friend expects" in result.stderr, result.stderr[-2000:]


# --- the v7b payloads of P5 (ff_v7b, ff_v7b_w) in every era and sample kind ------


def relabelled_ff_map(era, sample, tmp_path):
    """The 2018 ttbar fake-factor quantities map relabelled to ``era`` and ``sample``."""
    quantities_map = json.loads(Path(MAP_FF_2018).read_text())
    quantities_map["quantities"] = {era: {sample: quantities_map["quantities"]["2018"]["ttbar"]}}
    quantities_map["metadata"].update(era=era, sample_type=sample)
    relabelled = tmp_path / f"{era}_{sample}_fake_factors_quantities_map.json"
    relabelled.write_text(json.dumps(quantities_map))
    return str(relabelled)


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("module", [sm_fake_factors, sm_fake_factors_w], ids=["ff_v7b", "ff_v7b_w"])
def test_both_fake_factor_friends_build_in_every_run2_era_and_sample_kind(module, era, tmp_path):
    """P5 builds ff_v7b and ff_v7b_w for the data, the MC and the embedding of every
    Run-2 era from the v7b payloads (2016preVFP and 2016postVFP from the one 2016
    payload); the friend does not depend on the sample kind, W+jets enters et and
    mt of ff_v7b_w only, and every correction of the configuration is in the payload
    of the era."""
    assert module.AVAILABLE_ERAS == ERAS_RUN2
    payload_era = module.PAYLOAD_ERAS[era]
    directory = module.SM_PAYLOAD_DIRS[era]
    variant = "fake-factors-2026-10-19" + ("-w" if module is sm_fake_factors_w else "")
    assert directory == f"payloads/fake_factors/sm/{variant}/{payload_era}"
    analysis = Path(module.__file__).parent
    for scope in ("et", "mt", "tt"):
        built = {}
        for sample in ("data", "ttbar", "embedding"):
            config = module.build_config(
                era, sample, [scope], {"all"}, LEGACY_AVAILABLE_SAMPLES,
                module.AVAILABLE_ERAS, SCOPES, relabelled_ff_map(era, sample, tmp_path),
            )
            nominal = config.config_parameters[scope]["nominal"]
            assert nominal["ff_file"] == f"{directory}/fake_factors_{scope}.json.gz"
            assert nominal["ff_corr_file"] == f"{directory}/FF_corrections_{scope}.json.gz"
            with gzip.open(analysis / nominal["ff_file"], "rt") as handle:
                names = {c["name"] for c in json.load(handle)["corrections"]}
            with gzip.open(analysis / nominal["ff_corr_file"], "rt") as handle:
                payload = json.load(handle)
            names |= {c["name"] for c in payload["corrections"]}
            names |= {c["name"] for c in payload.get("compound_corrections") or []}
            used = {value for key, value in nominal.items() if key.endswith("_name") and value}
            assert used and used <= names, sorted(used - names)
            assert any("Wjets" in name for name in used) == (module is sm_fake_factors_w and scope != "tt")
            built[sample] = (sorted(output_names(config, scope)), sorted(ff_shifts(config, scope)))
        assert built["data"] == built["ttbar"] == built["embedding"], scope


# --- NN classifier friend (nn spec 3.4, N1, N21, N28) ---------------------------

V7B_CLASSES = ("HH", "tautau", "Top", "jetFakes", "Other")
# the inputs of the toy models (tests/fixtures/nn_classifier/families.json)
M0_INPUTS = [
    "bpair_btag_value_1", "bpair_btag_value_2", "bpair_deltaR", "bpair_m_inv", "bpair_pt_1", "bpair_pt_dijet",
    "deltaR_ditaupair", "jpt_1", "m_fastmtt", "mjj", "n_bjets", "n_jets", "pt_fastmtt", "m_vis", "mt_tot", "jpt_2",
    "pt_1", "pt_dijet", "pt_vis",
]
M0_K4_INPUTS = M0_INPUTS + ["pt_2", "met", "metphi", "eta_fastmtt", "phi_fastmtt"]


def nn_columns(prefix, classes, binary_head=False):
    columns = {f"{prefix}predicted_class", f"{prefix}predicted_max_value"}
    columns |= {f"{prefix}nn_score_{name}" for name in classes}
    return columns | ({f"{prefix}binary_score"} if binary_head else set())


@pytest.fixture(scope="module")
def nn_models(tmp_path_factory):
    """The models of a production in the layout of payloads/nn_classifier, every Run-2 era and tau
    scope: an M0-like model with two folds and one with four folds and a binary head (toy models)."""
    root = tmp_path_factory.mktemp("nn_classifier")
    return (
        NNModel(nn_classifier_payload("k2", root / "m0"), "nn_m0_"),
        NNModel(nn_classifier_payload("k4", root / "m0_k4"), "nn_m0k4_"),
    )


def build_nn_friend(models, era, scope, maps, shifts=("none",)):
    logging.disable(logging.CRITICAL)
    try:
        with mock.patch.object(sm_nn_classifier, "MODELS", models):
            return sm_nn_classifier.build_config(
                era, "ttbar", [scope], set(shifts), LEGACY_AVAILABLE_SAMPLES,
                sm_nn_classifier.AVAILABLE_ERAS, SCOPES, maps,
            )
    finally:
        logging.disable(logging.NOTSET)


@pytest.mark.parametrize("scope", ["et", "mt", "tt"])
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_nn_classifier_friend_builds_in_every_run2_era(nn_models, era, scope, tmp_path):
    """sm_nn_classifier builds in every Run-2 era and tau scope on the v7b ttbar n-tuple with the FastMTT
    friend: every model writes class, maximum and one score per output with its prefix, reads its
    inputs in the order of the manifest and the files of its era and scope, one per residue; the gate
    is the translated skim selection of the era and scope."""
    assert sm_nn_classifier.AVAILABLE_ERAS == ERAS_RUN2
    config = build_nn_friend(nn_models, era, scope, nn_classifier_maps(era, tmp_path))
    assert output_names(config, scope) == nn_columns("nn_m0_", V7B_CLASSES) | nn_columns(
        "nn_m0k4_", V7B_CLASSES, binary_head=True
    )
    nominal = config.config_parameters[scope]["nominal"]
    expression, columns = nn_gate.cpp_expression(nn_gate.skim_cuts(scope, era))
    assert nominal["nn_gate_expression"] == expression
    assert [q.name for q in find_producer(config, scope, "NNGate").input[scope]] == columns
    for (payload, prefix), inputs, folds, outputs in zip(nn_models, (M0_INPUTS, M0_K4_INPUTS), (2, 4), (5, 6)):
        assert [nominal[f"{prefix}onnx_file_r{r}"] for r in range(folds)] == [
            f"{payload}/{era}/{scope}/model_k{folds}_r{r}.onnx" for r in range(folds)
        ]
        assert f"{prefix}onnx_file_r{folds}" not in nominal
        assert (nominal[f"{prefix}num_inputs"], nominal[f"{prefix}num_classes"]) == (len(inputs), 5)
        assert (nominal[f"{prefix}num_outputs"], nominal[f"{prefix}softmax"]) == (outputs, False)
        assert [q.name for q in find_producer(config, scope, f"NNInputs_{prefix}").input[scope]] == inputs
        scores = find_producer(config, scope, f"NNScores_{prefix}")
        assert [q.name for q in scores.input[scope]] == [f"{prefix}inputs", "event", "nn_gate"]
        assert scores.call.count("onnx_file_r") == folds


def test_nn_classifier_friend_reads_fastmtt_from_its_friend(nn_models, tmp_path):
    """The models read m/pt/eta/phi_fastmtt, which only the FastMTT friend has: without its quantities
    map (no friend chain) the configuration fails."""
    with pytest.raises(InvalidInputError, match="fastmtt"):
        build_nn_friend(nn_models, "2018", "mt", nn_classifier_maps("2018", tmp_path, fastmtt=False))


def test_nn_classifier_friend_without_models_fails(tmp_path):
    assert sm_nn_classifier.MODELS == ()  # none is trained on v7b yet
    with pytest.raises(ValueError, match="no model"):
        build_nn_friend((), "2018", "mt", nn_classifier_maps("2018", tmp_path))


def test_nn_classifier_friend_shifts_the_gate_and_the_scores(nn_models, tmp_path):
    """With shifted inputs in the quantities map (P6), the gate, the input vectors, the scores and every
    output column are shifted; a shift of a column no model and no gate cut reads shifts nothing."""
    maps = nn_classifier_maps("2018", tmp_path)
    quantities_map = json.loads(Path(maps[0]).read_text())
    inputs = quantities_map["quantities"]["2018"]["ttbar"]["mt"]
    inputs["CMS_scale_t_DM0_2018Up"] = ["pt_2", "m_vis", "pt_vis", "mt_tot", "met", "metphi"]
    inputs["CMS_unrelated_2018Up"] = ["genWeight"]
    maps[0] = str(tmp_path / "shifted.json")
    Path(maps[0]).write_text(json.dumps(quantities_map))
    config = build_nn_friend(nn_models, "2018", "mt", maps, shifts=("all",))
    # (the shared input quantities keep the shifts of configurations built before in this process, so only
    # the shifts of this map are checked)
    for leaf in output_names(config, "mt"):
        (quantity,) = [q for q in config.outputs["mt"] if q.name == leaf]
        shifts = set(quantity.get_shifts("mt"))
        assert "__CMS_scale_t_DM0_2018Up" in shifts and "__CMS_unrelated_2018Up" not in shifts, leaf
    assert "__CMS_scale_t_DM0_2018Up" in find_producer(config, "mt", "NNGate").output[0].get_shifts("mt")


_GENERATE_NN_FRIEND = """
import json, logging, sys
from analysis_configurations.bbtautau import sm_nn_classifier
from analysis_configurations.bbtautau.constants import LEGACY_AVAILABLE_SAMPLES, SCOPES
from analysis_configurations.bbtautau.nn_payloads import NNModel
from code_generation.code_generation import CodeGenerator
models, era, scope, maps, directory = json.loads(sys.argv[1])
sm_nn_classifier.MODELS = tuple(NNModel(*model) for model in models)
logging.disable(logging.CRITICAL)
config = sm_nn_classifier.build_config(era, "ttbar", [scope], {"none"}, LEGACY_AVAILABLE_SAMPLES,
                                       sm_nn_classifier.AVAILABLE_ERAS, SCOPES, maps)
generator = CodeGenerator("code_generation/analysis_template_friends.cxx",
                          "code_generation/subset_template.cxx", config, "bbtautau",
                          "sm_nn_classifier", f"sm_nn_classifier_ttbar_{era}_{scope}", directory)
generator.generate_code()
with open(f"{directory}/outputs.json", "w") as f:
    json.dump(generator.output_commands, f)
"""


# one scope per era (a generation takes ~20 s); the configurations of every era and scope are built above
@pytest.mark.parametrize("era,scope", [("2016preVFP", "tt"), ("2016postVFP", "et"), ("2017", "mt"), ("2018", "tt")])
def test_nn_classifier_friend_generates_in_every_run2_era(nn_models, era, scope, tmp_path):
    """The C++ code (in a subprocess, code generation mutates module-level producers): the gate flag with
    the columns of the era, one EvaluateFolds per model with its files in residue order and its
    dimensions, and the unpacked outputs."""
    import subprocess
    import sys

    directory = tmp_path / scope
    directory.mkdir()
    arguments = json.dumps([list(nn_models), era, scope, nn_classifier_maps(era, tmp_path), str(directory)])
    result = subprocess.run(
        [sys.executable, "-c", _GENERATE_NN_FRIEND, arguments],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    sources = "\n".join(p.read_text() for p in sorted(directory.rglob("*.cxx")))
    (gate,) = [p.read_text() for p in directory.rglob("*.cxx") if "SelectionFlag" in p.read_text()]
    expression, columns = nn_gate.cpp_expression(nn_gate.skim_cuts(scope, era))
    assert f'"{expression}"' in gate and "{" + ",".join(f'"{c}"' for c in columns) + "}" in gate
    assert ('"hem_veto"' in gate) == (era == "2018")
    for (payload, prefix), folds, inputs, outputs in zip(nn_models, (2, 4), (19, 24), (5, 6)):
        files = ", ".join(f'"{payload}/{era}/{scope}/model_k{folds}_r{r}.onnx"' for r in range(folds))
        assert f'"{prefix}scores",\n        "{prefix}inputs", "event", "nn_gate",\n        {{{files}}},' in sources
        assert f"{{{files}}},\n        {inputs},\n        5,\n        {outputs},\n        false" in sources
    assert sources.count("xyh::classifier::UnpackScores(") == 2
    with open(directory / "outputs.json") as f:
        written = set(json.load(f)[scope])
    assert written == nn_columns("nn_m0_", V7B_CLASSES) | nn_columns("nn_m0k4_", V7B_CLASSES, True)
