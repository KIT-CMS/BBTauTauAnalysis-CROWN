"""Fake-factor payload conventions, read at configuration time.

A payload directory holds two TauFakeFactors files per channel,
``fake_factors_<ch>.json.gz`` and ``FF_corrections_<ch>.json.gz``. For every
fake-factor leg of a channel this module reads the correction names, the
inputs in payload order and the syst keys that become shifts, and checks the
conventions the friend relies on. Pure Python (``payload_io``), no CROWN
import.

Required conventions (``ValueError`` naming file and correction otherwise):

- every correction (every stack member of a compound correction) has a
  ``category`` node on ``syst`` at the top, with a default: the friend's
  ``"nominal"`` resolves to it, since fake factors have no nominal key. A
  ``nominal`` / ``<correction>nominal`` key, where present, equals it;
- the inputs are ``[process] + real ... + syst``, with ``process`` only in the
  fractions, whose process categories are exactly QCD and ttbar (the strings
  the C++ passes);
- a syst key is ``nominal``, ``<correction>nominal`` or ends in
  Up/Down/_up/_down, and the selected Up and Down keys pair one to one;
- the global non-closure keys ``{p}{s}_non_closure_Corr...`` are present in
  every stack member of ``{p}{s}_compound_correction``.

Shift selection: every directional key, except

- ``SystBandHigh``/``SystBandLow``, which describe the same smoothing band as
  ``SystBandAsym``: SystBandHigh Up is the curve re-smoothed with bandwidth
  x1.5 and Down its mirror 2*nominal - Up, SystBandLow the same with x0.5,
  SystBandAsym Up/Down are the x1.5/x0.5 curves
  (/work/jvoss/FF_Updated/helper/ff_functions.py:1575-1584);
- the per-variable non-closure keys of the closure stack: only the global
  (coarse) keys are kept.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterator, List, NamedTuple, Set, Tuple

from .payload_io import get_correction, load_payload

# Fake-factor legs per scope, and the correction-name suffix of each leg.
SCOPE_LEGS = {"et": ("lt",), "mt": ("lt",), "tt": ("leading", "subleading")}
LEG_SUFFIXES = {"lt": "", "leading": "", "subleading": "_subleading"}

# TauFakeFactors variable names that differ from the n-tuple columns.
INPUT_ALIASES = {"njets": "n_jets", "nbtag": "n_bjets"}

FRACTION_PROCESSES = {"QCD", "ttbar"}
DIRECTIONS = ("Up", "Down", "_up", "_down")
EXCLUDED_BAND_KEYS = ("SystBandHigh", "SystBandLow")


class _Role(NamedTuple):
    name: str
    file: str  # "fake_factors" or "FF_corrections"
    correction: str  # correction name, {s} is the leg suffix
    compound: bool = False


# The corrections of one leg, in the order of the C++ inputs.
ROLES = (
    _Role("ff_qcd", "fake_factors", "QCD{s}_fake_factors"),
    _Role("ff_ttbar", "fake_factors", "ttbar{s}_fake_factors"),
    _Role("fractions", "fake_factors", "process_fractions{s}"),
    _Role("dr_sr_qcd", "FF_corrections", "QCD{s}_DR_SR_correction"),
    _Role("closure_qcd", "FF_corrections", "QCD{s}_compound_correction", True),
    _Role("closure_ttbar", "FF_corrections", "ttbar{s}_compound_correction", True),
)


@dataclass(frozen=True)
class FakeFactorCorrection:
    role: str
    name: str
    file: str
    inputs: Tuple[str, ...]  # n-tuple columns, in payload order
    shift_keys: Tuple[str, ...]


@dataclass(frozen=True)
class FakeFactorLeg:
    name: str
    corrections: Tuple[FakeFactorCorrection, ...]  # in ROLES order


def payload_files(payload_dir: str, scope: str) -> Dict[str, str]:
    """The two payload files of ``scope``, keyed "fake_factors" / "FF_corrections".

    The corrections file may carry the name of its TauFakeFactors corrections
    configuration, ``FF_corrections_<ch>_default.json.gz``; a relative
    ``payload_dir`` is looked up in the analysis directory.
    """
    files = {
        kind: f"{payload_dir}/{kind}_{scope}.json.gz"
        for kind in ("fake_factors", "FF_corrections")
    }
    default = f"{payload_dir}/FF_corrections_{scope}_default.json.gz"
    analysis_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isfile(os.path.join(analysis_dir, files["FF_corrections"])) and os.path.isfile(
        os.path.join(analysis_dir, default)
    ):
        files["FF_corrections"] = default
    return files


def shift_name(key: str) -> str:
    """CROWN shift name of a syst key: a trailing ``_up``/``_down`` becomes ``Up``/``Down``."""
    for old, new in (("_up", "Up"), ("_down", "Down")):
        if key.endswith(old):
            return key[: -len(old)] + new
    return key


def read_legs(payload_dir: str, scope: str) -> Tuple[FakeFactorLeg, ...]:
    """Describe the fake-factor legs of ``scope`` from its payloads in ``payload_dir``."""
    if scope not in SCOPE_LEGS:
        raise ValueError(
            f"scope '{scope}' has no fake-factor legs; fake factors exist for "
            f"{sorted(SCOPE_LEGS)}"
        )
    payloads = {
        kind: (path, load_payload(path))
        for kind, path in payload_files(payload_dir, scope).items()
    }
    legs = tuple(
        FakeFactorLeg(
            leg,
            tuple(_read_correction(payloads, role, LEG_SUFFIXES[leg]) for role in ROLES),
        )
        for leg in SCOPE_LEGS[scope]
    )
    _check_unique_shift_names(legs, scope)
    return legs


def _read_correction(payloads, role: _Role, suffix: str) -> FakeFactorCorrection:
    path, payload = payloads[role.file]
    name = role.correction.format(s=suffix)
    fractions = role.name == "fractions"
    if role.compound:
        correction = get_correction(payload, name, path, "compound_corrections")
        keys = _global_closure_keys(payload, correction, path)
    else:
        correction = get_correction(payload, name, path)
        keys = _directional_keys(correction, path)
    if fractions:
        _check_fraction_processes(correction, path)
    shift_keys = sorted(
        key for key in keys if not any(band in key for band in EXCLUDED_BAND_KEYS)
    )
    _check_pairs(shift_keys, name, path)
    return FakeFactorCorrection(
        role=role.name,
        name=name,
        file=path,
        inputs=_input_names(correction, fractions, path),
        shift_keys=tuple(shift_keys),
    )


def _directional_keys(correction: dict, path: str) -> Set[str]:
    """The Up/Down keys of the top-level syst category; nominal keys are skipped."""
    name = correction["name"]
    data = correction.get("data") or {}
    if (
        data.get("nodetype") != "category"
        or data.get("input") != "syst"
        or data.get("default") is None
    ):
        raise ValueError(
            f"correction '{name}' in '{path}': the top-level node must be a "
            "category on 'syst' with a default (the nominal)"
        )
    keys = set()
    for item in data["content"]:
        key = item["key"]
        if key in ("nominal", f"{name}nominal"):
            if item["value"] != data["default"]:
                raise ValueError(
                    f"correction '{name}' in '{path}': key '{key}' differs "
                    "from the default"
                )
        elif key.endswith(DIRECTIONS):
            keys.add(key)
        else:
            raise ValueError(
                f"correction '{name}' in '{path}': syst key '{key}' is neither "
                "nominal nor ends in Up/Down/_up/_down"
            )
    return keys


def _global_closure_keys(payload: dict, compound: dict, path: str) -> Set[str]:
    """The global non-closure keys of a compound correction, present in every member."""
    name = compound["name"]
    prefix = name.replace("_compound_correction", "_non_closure_Corr")
    members = {
        member: _directional_keys(get_correction(payload, member, path), path)
        for member in compound["stack"]
    }
    keys = {key for member_keys in members.values() for key in member_keys}
    global_keys = {key for key in keys if key.startswith(prefix)}
    for member, member_keys in members.items():
        missing = global_keys - member_keys
        if missing:
            raise ValueError(
                f"compound correction '{name}' in '{path}': stack member "
                f"'{member}' lacks the global keys {sorted(missing)}"
            )
    return global_keys


def _check_pairs(keys: List[str], name: str, path: str) -> None:
    """Raise unless every selected Up key has its Down partner and vice versa."""
    names = {shift_name(key) for key in keys}
    unpaired = [key for key in keys if _partner(shift_name(key)) not in names]
    if unpaired:
        raise ValueError(
            f"correction '{name}' in '{path}': syst keys without their "
            f"Up/Down partner: {unpaired}"
        )


def _partner(name: str) -> str:
    if name.endswith("Up"):
        return name[: -len("Up")] + "Down"
    return name[: -len("Down")] + "Up"


def _input_names(correction: dict, fractions: bool, path: str) -> Tuple[str, ...]:
    """The real inputs in payload order, aliased to n-tuple columns."""
    signature = [(i["name"], i["type"]) for i in correction["inputs"]]
    head = [("process", "string")] if fractions else []
    body = signature[len(head) : -1]
    if (
        signature[: len(head)] != head
        or signature[-1:] != [("syst", "string")]
        or any(kind != "real" for _, kind in body)
    ):
        expected = "[process] + real ... + syst" if fractions else "real ... + syst"
        raise ValueError(
            f"correction '{correction['name']}' in '{path}': inputs {signature} "
            f"are not {expected}"
        )
    return tuple(INPUT_ALIASES.get(name, name) for name, _ in body)


def _check_fraction_processes(correction: dict, path: str) -> None:
    for category in _categories_on(correction["data"], "process"):
        processes = {item["key"] for item in category["content"]}
        if processes != FRACTION_PROCESSES:
            raise ValueError(
                f"correction '{correction['name']}' in '{path}': process "
                f"categories {sorted(processes)}, the C++ evaluates exactly "
                f"{sorted(FRACTION_PROCESSES)}"
            )


def _categories_on(node, input_name: str) -> Iterator[dict]:
    """All category nodes on ``input_name`` below ``node``."""
    if isinstance(node, dict):
        if node.get("nodetype") == "category" and node.get("input") == input_name:
            yield node
        for value in node.values():
            yield from _categories_on(value, input_name)
    elif isinstance(node, list):
        for value in node:
            yield from _categories_on(value, input_name)


def _check_unique_shift_names(legs: Tuple[FakeFactorLeg, ...], scope: str) -> None:
    """CROWN keeps one shift per name and scope, so a duplicate would overwrite another."""
    seen: Dict[str, str] = {}
    for leg in legs:
        for correction in leg.corrections:
            for key in correction.shift_keys:
                name = shift_name(key)
                if seen.setdefault(name, correction.name) != correction.name:
                    raise ValueError(
                        f"shift '{name}' in scope '{scope}' comes from both "
                        f"'{seen[name]}' and '{correction.name}' ({correction.file})"
                    )
