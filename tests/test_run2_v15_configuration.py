"""Surfaces of the Run-2 NanoAOD-v15 adaption that fail silently when they drift."""

import gzip
import json
from pathlib import Path
import re

import pytest

from analysis_configurations.bbtautau.constants import ERAS_RUN2, ERAS_RUN3
from analysis_configurations.bbtautau.producers import scalefactors, taus
from analysis_configurations.bbtautau.tests.helpers import build

CROWN_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = CROWN_ROOT / "analysis_configurations" / "bbtautau"
BUILD_SCRIPTS = sorted((ANALYSIS_ROOT / "build_scripts").glob("test_build_*.sh"))


def test_analysis_identity_is_bbtautau():
    """Folder, generators, build scripts and init.sh agree on the analysis name."""
    generate = (ANALYSIS_ROOT / "generate.py").read_text()
    generate_friends = (ANALYSIS_ROOT / "generate_friends.py").read_text()
    init_script = (CROWN_ROOT / "init.sh").read_text()
    scripts = [script.read_text() for script in BUILD_SCRIPTS]
    assert BUILD_SCRIPTS
    assert (
        'analysis_name = "bbtautau"' in generate
        and 'analysis_name = "bbtautau"' in generate_friends
    )
    assert all('local analysis="bbtautau"' in script for script in scripts)
    assert (
        "bbtautau)" in init_script
        and 'REPO="git@github.com:KIT-CMS/BBTauTauAnalysis-CROWN.git"' in init_script
    )
    assert "xyh_bbtautau" not in "\n".join(
        [generate, generate_friends, init_script, *scripts]
    )


def test_tau_pt_correction_matches_current_crown_signature():
    call = taus.TauPtCorrectionMC.call
    assert "physicsobject::tau::experimental::PtCorrectionMC(" in call
    ordered_arguments = [
        '"{tau_vsjet_es_sf_file}"',
        '"{tau_ES_json_name}"',
        '"{tau_id_algorithm}"',
        '"{tau_ides_sf_vsjet_wp}"',
        '"{tau_ides_sf_vsele_wp}"',
        '"{tau_es_variation}"',
    ]
    positions = [call.index(argument) for argument in ordered_arguments]
    assert positions == sorted(positions)


# Core declarations the tau producers call, read from the header of the CROWN tree
# the tests run in, so that a core pin with another signature fails here and not
# only in the compilation of the generated code (core 14f82c1 added id_vsmu_wp to
# experimental::Id_vsJet, which no generate.py run notices).
TAUS_HEADER = CROWN_ROOT / "include/taus.hxx"


def _strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", " ", text)


def _split_top_level(text):
    """Split at the commas outside (), <> and {}."""
    parts, depth, current = [], 0, ""
    for char in text:
        if char in "(<{":
            depth += 1
        elif char in ")>}":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())
    return parts


def core_declarations(header, qualified_name):
    """Parameter-name lists of every declaration of ``qualified_name`` in ``header``."""
    *namespaces, function = qualified_name.split("::")
    text = _strip_comments(header.read_text())
    token = re.compile(r"namespace\s+(\w+)\s*\{|\{|\}|\b(\w+)\s*\(")
    stack, found, position = [], [], 0
    while True:
        match = token.search(text, position)
        if match is None:
            return found
        position = match.end()
        if match.group(1):
            stack.append(match.group(1))
        elif match.group(0) == "{":
            stack.append(None)
        elif match.group(0) == "}":
            stack.pop()
        elif match.group(2) == function and [n for n in stack if n] == namespaces:
            depth, end = 1, position
            while depth:
                depth += {"(": 1, ")": -1}.get(text[end], 0)
                end += 1
            parameters = _split_top_level(text[position : end - 1])
            found.append([re.findall(r"\w+", p.split("=")[0])[-1] for p in parameters])
            position = end


def call_arguments(producer, scope):
    """Arguments of ``producer``'s call with ``{input}`` expanded to its columns."""
    call = " ".join(producer.call.split())
    arguments = _split_top_level(call[call.index("(") + 1 : call.rindex(")")])
    columns = [f"column:{q.name}" for q in producer.input[scope]]
    expanded = []
    for argument in arguments:
        expanded.extend(columns if argument == "{input}" else [argument])
    return expanded


@pytest.mark.parametrize(
    "producer, function, scope, expected",
    [
        (
            scalefactors.TauIDVsJetSF2,
            "physicsobject::tau::scalefactor::experimental::Id_vsJet",
            "mt",
            {
                "sf_file": '"{tau_vsjet_es_sf_file}"',
                "sf_name": '"{discriminator}"',
                "id_vsjet_wp": '"{vsjet_wp}"',
                "id_vse_wp": '"{tau_ides_sf_vsele_wp}"',
                "id_vsmu_wp": "{tau_ides_sf_vsmu_wp}",  # a C++ literal
                "sf_dependence": '"{tau_id_sf_vsjet_sf_dependence}"',
                "variation": '"{tau_id_sf_vsjet_variation}"',
            },
        ),
        (
            scalefactors.TauIDVsEleSF2,
            "physicsobject::tau::scalefactor::experimental::Id_vsEle",
            "mt",
            {"sf_file": '"{tau_ides_sf_file}"', "id_vse_wp": '"{vsele_wp}"', "era": '"{era}"'},
        ),
        (
            scalefactors.TauIDVsMuSF2,
            "physicsobject::tau::scalefactor::experimental::Id_vsMu",
            "mt",
            {
                "id_vsmu_wp": '"{vsmu_wp}"',
                "id_vse_wp": '"{vsmu_vsele_wp}"',
                "id_vsjet_wp": '"{vsmu_vsjet_wp}"',
            },
        ),
        (
            taus.TauPtCorrectionMC,
            "physicsobject::tau::experimental::PtCorrectionMC",
            "mt",
            {
                "sf_file": '"{tau_vsjet_es_sf_file}"',
                "id_vsjet_wp": '"{tau_ides_sf_vsjet_wp}"',
                "id_vse_wp": '"{tau_ides_sf_vsele_wp}"',
                "variation": '"{tau_es_variation}"',
            },
        ),
    ],
    ids=["Id_vsJet", "Id_vsEle", "Id_vsMu", "PtCorrectionMC"],
)
def test_tau_producers_match_the_core_signature(producer, function, scope, expected):
    """One argument per parameter of the core declaration, the named ones in place."""
    (parameters,) = core_declarations(TAUS_HEADER, function)
    assert function + "(" in " ".join(producer.call.split()).replace("( ", "(")
    arguments = call_arguments(producer, scope)
    assert len(arguments) == len(parameters), dict(zip(parameters, arguments))
    bound = dict(zip(parameters, arguments))
    assert {name: bound[name] for name in expected} == expected


def _vsjet_inputs(path, name):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as handle:
        (correction,) = [c for c in json.load(handle)["corrections"] if c["name"] == name]
    return [i["name"] for i in correction["inputs"]]


@pytest.mark.parametrize(
    "module,sample,era",
    [("sm_config", "ttbar", era) for era in ERAS_RUN2]
    + [("sm_config", "embedding", "2018")]  # the only embedding tau payload so far (5.4)
    + [("nmssm_config", "ttbar", era) for era in ERAS_RUN3],
)
def test_vsjet_sf_vsmu_wp_matches_the_payload_inputs(module, sample, era):
    """An empty vsMu WP evaluates the payload with 7 inputs, a set one with 8; the
    payload of the era must have exactly that wp_VSmu input or the evaluation throws."""
    config = build(module, sample, era=era, scopes=("et", "mt", "tt"))
    for scope in ("et", "mt", "tt"):
        params = config.config_parameters[scope]["nominal"]
        path = Path(params["tau_vsjet_es_sf_file"])
        path = path if path.is_absolute() else ANALYSIS_ROOT / path
        if not path.is_file():
            pytest.skip("TAU payloads require CVMFS")
        literal = params["tau_ides_sf_vsmu_wp"]
        assert re.fullmatch(r'"\w*"', literal), literal  # the call does not quote it
        vsmu_wp = literal.strip('"')
        for entry in params["vsjet_tau_id_sf"]:
            inputs = _vsjet_inputs(path, entry["discriminator"])
            assert ("wp_VSmu" in inputs) == bool(vsmu_wp), (scope, inputs)
            assert len(inputs) == (8 if vsmu_wp else 7), (scope, inputs)
