"""Shared build and generation helpers, fake CLI args and configuration accessors.

Not a test module. ``build()`` mirrors ``generate.py`` -- gate on the module's
``AVAILABLE_ERAS``, but always construct against ``ALL_SAMPLES`` --
and caches, so each (module, sample, era, scopes, shifts) surface is built once
per session. ``generate_code()`` emits the C++ code of a surface, also once per session.
The accessors keep the producer-group traversal in one place.
"""
import atexit
import functools
import hashlib
import importlib
import json
import logging
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import NamedTuple

import pytest

from analysis_configurations.bbtautau.constants import ERAS, ERAS_RUN2, ALL_SAMPLES, SCOPES
from code_generation.quantity import NanoAODQuantity

# The branches of one v15 embedding file (mutau 2018A nano_1)
V15_EMBEDDING_BRANCHES = (
    Path(__file__).resolve().parent / "fixtures/nanoaod_v15_embedding_2018_branches.txt"
)

# The toy ONNX models of the NN classifier friend (fixtures/make_nn_classifier_fixtures.py) and the
# quantities maps of its tests: the v7b ttbar n-tuple of every Run-2 era (et, mt, tt) and the FastMTT friend
FIXTURES = Path(__file__).resolve().parent / "fixtures"
NN_FIXTURES = FIXTURES / "nn_classifier"
NN_FASTMTT_MAP = FIXTURES / "nn_classifier_fastmtt_quantities_map.json"


def nn_classifier_payload(family, directory, eras=tuple(ERAS_RUN2), scopes=("et", "mt", "tt"), edit=None):
    """The toy model ``family`` in the layout of payloads/nn_classifier below ``directory``: per era and
    scope the ONNX files and the manifest the trainer writes; ``edit(manifest, era, scope)`` may change a
    manifest. Returns ``directory`` as a string."""
    spec = json.loads((NN_FIXTURES / "families.json").read_text())[family]
    folds = spec["folds"]
    for era in eras:
        for scope in scopes:
            target = Path(directory) / era / scope
            target.mkdir(parents=True, exist_ok=True)
            files = {}
            for residue in range(folds):
                name = f"model_k{folds}_r{residue}.onnx"
                shutil.copyfile(NN_FIXTURES / family / name, target / name)
                files[str(residue)] = {"file": name, "sha256": hashlib.sha256((target / name).read_bytes()).hexdigest()}
            manifest = {
                "model": f"toy_{family}",
                "channel": scope,
                "repetition": 0,
                "folds": folds,
                "files": files,
                "inputs": spec["inputs"],
                "classes": spec["classes"],
                "output": spec["output"],
                "opset": 17,
            }
            if spec["n_outputs"] == len(spec["classes"]) + 1:
                manifest["binary_head"] = True
            if "constants" in spec:
                manifest["constants"] = dict(spec["constants"])
            if edit is not None:
                edit(manifest, era, scope)
            (target / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return str(directory)


def nn_classifier_maps(era, directory, fastmtt=True):
    """The quantities maps of the NN classifier friend in ``era``: the v7b ttbar n-tuple and, with
    ``fastmtt``, the FastMTT friend (its 2018 map relabelled to ``era``)."""
    maps = [str(FIXTURES / f"nn_classifier_{era}_quantities_map.json")]
    if fastmtt:
        quantities_map = json.loads(NN_FASTMTT_MAP.read_text())
        quantities_map["quantities"] = {era: quantities_map["quantities"].pop("2018")}
        quantities_map["metadata"]["era"] = era
        path = Path(directory) / f"{era}_nn_classifier_fastmtt_quantities_map.json"
        path.write_text(json.dumps(quantities_map))
        maps.append(str(path))
    return maps


# Parts of the full Run-2 (v7) configuration that do not exist yet, with the eras
# whose tests they break (keys: the items of the v7 spec, or the payloads still to
# be measured). Tests mark those cases with ``pending``, a strict xfail: once a
# part exists, its cases pass and fail the run until the entry here is removed.
PENDING = {}  # nothing pending: the embedding tau ID/ES payloads of every era are measured (v7 spec 5.4)


def pending(era, *items):
    """Strict-xfail marks for ``era`` if one of ``items`` is pending for it."""
    missing = [item for item in items if era in PENDING[item]]
    if not missing:
        return []
    return [pytest.mark.xfail(strict=True, reason=f"{', '.join(missing)} pending for {era}")]


def era_cases(eras, *items):
    """``pytest.param`` per era, marked ``pending`` for ``items``."""
    return [pytest.param(era, marks=pending(era, *items), id=era) for era in eras]


@functools.lru_cache(maxsize=None)
def build(module_name, sample, era, scopes=("mt",), shifts=("none",)):
    """Build ``module_name``'s configuration for ``era`` (no default, so that every
    test names its era); cached, and quiet about logging."""
    module = importlib.import_module(f"analysis_configurations.bbtautau.{module_name}")
    logging.disable(logging.CRITICAL)
    try:
        return module.build_config(
            era, sample, list(scopes), {s.lower() for s in shifts},
            ALL_SAMPLES,
            list(getattr(module, "AVAILABLE_ERAS", ERAS)), SCOPES,
        )
    finally:
        logging.disable(logging.NOTSET)


class Generated(NamedTuple):
    directory: Path  # the generated sources
    outputs: dict  # scope -> set of output column names


_GENERATE = """
import json, sys
from analysis_configurations.bbtautau.tests.helpers import build
from code_generation.code_generation import CodeGenerator
module, sample, era, scopes, shifts, directory = json.loads(sys.argv[1])
config = build(module, sample, era, tuple(scopes), tuple(shifts))
generator = CodeGenerator("code_generation/analysis_template.cxx",
                          "code_generation/subset_template.cxx", config, "bbtautau",
                          module, f"{module}_{sample}_{era}", directory)
generator.generate_code()
with open(f"{directory}/outputs.json", "w") as f:
    json.dump(generator.output_commands, f)
"""


@functools.lru_cache(maxsize=None)
def generate_code(module_name, sample, era, scopes=("mt",), shifts=("none",)):
    """Generate the C++ code of one surface; cached, so each surface is generated once.

    Generation runs in a subprocess: it mutates module-level producers, so a second
    surface generated in the same process can fail.
    """
    directory = tempfile.mkdtemp(prefix=f"{module_name}_{sample}_{era}_")
    atexit.register(shutil.rmtree, directory, ignore_errors=True)
    arguments = json.dumps([module_name, sample, era, scopes, shifts, directory])
    result = subprocess.run(
        [sys.executable, "-c", _GENERATE, arguments],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with open(f"{directory}/outputs.json") as f:
        outputs = {scope: set(names) for scope, names in json.load(f).items()}
    return Generated(Path(directory), outputs)


def quantities_map(outputs, era, sample, config, path):
    """Write the quantities map of the output columns ``outputs`` (scope -> names, a shifted
    column as <name>__<shift>) to ``path`` and return the path as a string. It is the map an
    executable writes into its output file (CodeGenerator.set_shift_quantities_map: per scope
    the columns of every shift, "" for the nominal) in the JSON layout KingMaker hands to the
    friend builds (helpers/GetQuantitiesMap.py)."""
    scopes = {}
    for scope, names in outputs.items():
        shifts = scopes.setdefault(scope, {})
        for name in names:
            quantity, _, shift = name.partition("__")
            shifts.setdefault(shift, []).append(quantity)
    content = {
        "quantities": {era: {sample: {s: {k: sorted(v) for k, v in shifts.items()} for s, shifts in scopes.items()}}},
        "metadata": {"era": era, "sample_type": sample, "config": config},
    }
    Path(path).write_text(json.dumps(content))
    return str(path)


_GENERATE_FRIEND = """
import importlib, json, logging, sys
from analysis_configurations.bbtautau.constants import ALL_SAMPLES, ERAS, SCOPES
from code_generation.code_generation import CodeGenerator
module_name, sample, era, scope, shifts, maps, directory = json.loads(sys.argv[1])
module = importlib.import_module(f"analysis_configurations.bbtautau.{module_name}")
logging.disable(logging.CRITICAL)
config = module.build_config(era, sample, [scope], set(shifts), ALL_SAMPLES,
                             list(getattr(module, "AVAILABLE_ERAS", ERAS)), SCOPES, maps)
generator = CodeGenerator("code_generation/analysis_template_friends.cxx",
                          "code_generation/subset_template.cxx", config, "bbtautau",
                          module_name, f"{module_name}_{sample}_{era}_{scope}", directory)
generator.generate_code()
with open(f"{directory}/outputs.json", "w") as f:
    json.dump(generator.output_commands, f)
"""


def generate_friend_code(module_name, sample, era, scope, maps, shifts=("all",)):
    """Generate the C++ code of the friend ``module_name`` for one scope on the quantities maps
    ``maps`` (the main n-tuple first, then the friends it requires), as generate_friends.run
    does, in a subprocess: a friend build leaves the shifts of its inputs on module-level
    quantities. Returns a ``Generated`` with the output columns of the scope."""
    directory = tempfile.mkdtemp(prefix=f"{module_name}_{sample}_{era}_{scope}_")
    atexit.register(shutil.rmtree, directory, ignore_errors=True)
    arguments = json.dumps([module_name, sample, era, scope, list(shifts), list(maps), directory])
    result = subprocess.run(
        [sys.executable, "-c", _GENERATE_FRIEND, arguments],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-3000:]
    with open(f"{directory}/outputs.json") as f:
        outputs = {name: set(names) for name, names in json.load(f).items()}
    return Generated(Path(directory), outputs)


_CALL = re.compile(r"auto df\d+ = (.*?);", re.S)


def generated_calls(generated):
    """The producer calls of generated code per scope: every ``auto dfN = <call>;`` statement of
    src/<scope>/, with whitespace collapsed and the dataframe numbering removed, sorted. Together
    with the output columns they are what a build computes."""
    (code,) = generated.directory.glob("*_generated_code")
    return {
        scope.name: sorted(
            re.sub(r"\bdf\d+\b", "df", " ".join(call.split()))
            for source in sorted(scope.glob("*.cxx"))
            for call in _CALL.findall(source.read_text())
        )
        for scope in sorted((code / "src").iterdir())
    }


class FakeArgs:
    """Attributes ``generate.run``/``generate_friends.run`` read before their gates."""

    def __init__(self, config, era, sample="ttbar"):
        self.config, self.era, self.sample = config, era, sample
        self.scopes, self.shifts = ["mt"], ["none"]
        self.quantities_map = None
        self.logger = logging.getLogger(__name__)


def producer_names(config, scope):
    """Top-level producer names in ``scope``."""
    return {p.name for p in config.producers[scope]}


def output_names(config, scope):
    return {q.get_leaf(shift="", scope=scope) for q in config.outputs[scope]}


def find_producer(config, scope, name):
    """The producer called ``name`` in ``scope``, searching through groups.

    Several producers only exist as members of a ``ProducerGroup`` (e.g. the jet
    ID inside ``AuxJetCollectionQuantities``), which exposes its members as a
    scope -> list mapping in ``.producers``.
    """

    def walk(producer):
        if producer.name == name:
            return producer
        members = getattr(producer, "producers", None)
        if isinstance(members, dict):
            members = [p for group in members.values() for p in group]
        for member in members or []:
            found = walk(member)
            if found is not None:
                return found
        return None

    for producer in config.producers[scope]:
        found = walk(producer)
        if found is not None:
            return found
    raise AssertionError(f"no producer {name!r} in scope {scope!r}")


def nanoaod_inputs(config):
    """NanoAOD branches ``config`` reads: producer inputs, through groups, NanoAOD
    outputs and the MET filters."""

    def walk(producer, scope):
        inputs = (
            producer.input.get(scope, []) if isinstance(producer.input, dict) else []
        )
        yield from (q.name for q in inputs or [] if isinstance(q, NanoAODQuantity))
        members = getattr(producer, "producers", None)
        if isinstance(members, dict):
            members = members.get(scope, [])
        for member in members or []:
            yield from walk(member, scope)

    names = {
        name
        for scope in config.producers
        for p in config.producers[scope]
        for name in walk(p, scope)
    }
    names |= {
        q.name
        for scope in config.outputs
        for q in config.outputs[scope]
        if isinstance(q, NanoAODQuantity)
    }
    return names | set(config.config_parameters["global"]["nominal"]["met_filters"])
