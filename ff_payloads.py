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
  fractions, whose process categories are the same everywhere and either
  {QCD, ttbar} or {QCD, Wjets, ttbar} (v7 spec E18, C15): the processes of the
  leg, whose fake factors the friend sums (``PROCESS_ORDER``);
- every process of the leg has its fake factors ``{p}{s}_fake_factors`` and its
  closure ``{p}{s}_compound_correction``; QCD has its DR->SR correction
  ``QCD{s}_DR_SR_correction``, Wjets one ``Wjets{s}_DR_SR_correction`` if the
  measurement provides it;
- a syst key is ``nominal``, ``<correction>nominal`` or ends in
  Up/Down/_up/_down, and the selected Up and Down keys pair one to one;
- the global non-closure keys ``{p}{s}_non_closure_Corr...`` are present in
  every stack member of ``{p}{s}_compound_correction``.

Shift selection: every directional key, except

- ``SystBandHigh``/``SystBandLow``, which describe the same smoothing band as
  ``SystBandAsym``: SystBandHigh Up is the curve re-smoothed with bandwidth
  x1.5 and Down its mirror 2*nominal - Up, SystBandLow the same with x0.5,
  SystBandAsym Up/Down are the x1.5/x0.5 curves
  (``smooth_function`` in /work/jvoss/FF_Updated/helper/ff_functions.py);
- the per-variable non-closure keys of the closure stack: only the global
  (coarse) keys are kept.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterator, List, NamedTuple, Optional, Set, Tuple

from .payload_io import get_correction, load_payload

# Fake-factor legs per scope, and the correction-name suffix of each leg.
SCOPE_LEGS = {"et": ("lt",), "mt": ("lt",), "tt": ("leading", "subleading")}
LEG_SUFFIXES = {"lt": "", "leading": "", "subleading": "_subleading"}

# TauFakeFactors variable names that differ from the n-tuple columns.
INPUT_ALIASES = {"njets": "n_jets", "nbtag": "n_bjets"}

# The process sets a fake-factor payload may have, read from the process
# categories of its fractions: QCD + ttbar, or QCD + W + ttbar (v7 spec E18). The
# friend sums the processes in PROCESS_ORDER, TauFakeFactors' order.
FRACTION_PROCESS_SETS = ({"QCD", "ttbar"}, {"QCD", "Wjets", "ttbar"})
PROCESS_ORDER = ("QCD", "Wjets", "ttbar")
DIRECTIONS = ("Up", "Down", "_up", "_down")
EXCLUDED_BAND_KEYS = ("SystBandHigh", "SystBandLow")


class _Role(NamedTuple):
    name: str
    file: str  # "fake_factors" or "FF_corrections"
    correction: str  # correction name, {s} is the leg suffix
    process: Optional[str]  # the process it belongs to, None for the fractions
    compound: bool = False
    optional: bool = False  # used only if the payload has it


# The corrections of one leg, in the order of the C++ inputs; the roles of a
# process the payload does not have are skipped.
ROLES = (
    _Role("ff_qcd", "fake_factors", "QCD{s}_fake_factors", "QCD"),
    _Role("ff_wjets", "fake_factors", "Wjets{s}_fake_factors", "Wjets"),
    _Role("ff_ttbar", "fake_factors", "ttbar{s}_fake_factors", "ttbar"),
    _Role("fractions", "fake_factors", "process_fractions{s}", None),
    _Role("dr_sr_qcd", "FF_corrections", "QCD{s}_DR_SR_correction", "QCD"),
    _Role(
        "dr_sr_wjets", "FF_corrections", "Wjets{s}_DR_SR_correction", "Wjets",
        optional=True,
    ),
    _Role("closure_qcd", "FF_corrections", "QCD{s}_compound_correction", "QCD", True),
    _Role(
        "closure_wjets", "FF_corrections", "Wjets{s}_compound_correction", "Wjets", True
    ),
    _Role(
        "closure_ttbar", "FF_corrections", "ttbar{s}_compound_correction", "ttbar", True
    ),
)
# The roles of the fake factors themselves (the raw fake factor); the others
# but the fractions are corrections of the fake factor of their process.
FAKE_FACTOR_ROLES = ("ff_qcd", "ff_wjets", "ff_ttbar")


@dataclass(frozen=True)
class FakeFactorCorrection:
    role: str
    name: str
    file: str
    inputs: Tuple[str, ...]  # n-tuple columns, in payload order
    shift_keys: Tuple[str, ...]
    process: Optional[str] = None  # None for the fractions
    compound: bool = False


@dataclass(frozen=True)
class FakeFactorLeg:
    name: str
    corrections: Tuple[FakeFactorCorrection, ...]  # in ROLES order
    processes: Tuple[str, ...]  # in PROCESS_ORDER

    def correction(self, role: str) -> FakeFactorCorrection:
        """The correction of ``role``; ``KeyError`` if the leg has none."""
        for correction in self.corrections:
            if correction.role == role:
                return correction
        raise KeyError(f"leg '{self.name}' has no correction of role '{role}'")

    @property
    def fake_factors(self) -> Tuple[FakeFactorCorrection, ...]:
        """The fake factors, one per process, in the order of ``processes``."""
        return tuple(c for c in self.corrections if c.role in FAKE_FACTOR_ROLES)

    @property
    def fractions(self) -> FakeFactorCorrection:
        return self.correction("fractions")

    @property
    def process_corrections(self) -> Tuple[FakeFactorCorrection, ...]:
        """The corrections of the fake factors (DR->SR, closure), in ROLES order."""
        return tuple(
            c for c in self.corrections if c.role not in FAKE_FACTOR_ROLES + ("fractions",)
        )


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
    legs = tuple(_read_leg(payloads, leg) for leg in SCOPE_LEGS[scope])
    _check_unique_shift_names(legs, scope)
    return legs


def _read_leg(payloads, leg: str) -> FakeFactorLeg:
    """The corrections of ``leg`` for the processes of its fractions."""
    suffix = LEG_SUFFIXES[leg]
    (fractions_role,) = [role for role in ROLES if role.name == "fractions"]
    path, payload = payloads[fractions_role.file]
    fractions = get_correction(payload, fractions_role.correction.format(s=suffix), path)
    present = _fraction_processes(fractions, path)
    processes = tuple(p for p in PROCESS_ORDER if p in present)
    corrections = []
    for role in ROLES:
        if role.process is not None and role.process not in processes:
            continue
        if role.optional and not _has_correction(payloads[role.file][1], role, suffix):
            continue
        corrections.append(_read_correction(payloads, role, suffix))
    return FakeFactorLeg(leg, tuple(corrections), processes)


def _has_correction(payload: dict, role: _Role, suffix: str) -> bool:
    kind = "compound_corrections" if role.compound else "corrections"
    name = role.correction.format(s=suffix)
    return any(c["name"] == name for c in payload.get(kind) or [])


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
        process=role.process,
        compound=role.compound,
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


def _fraction_processes(correction: dict, path: str) -> Set[str]:
    """The processes of the fractions: the same keys in every process category,
    one of FRACTION_PROCESS_SETS."""
    found = [
        {item["key"] for item in category["content"]}
        for category in _categories_on(correction["data"], "process")
    ]
    allowed = [sorted(processes) for processes in FRACTION_PROCESS_SETS]
    if not found or any(processes != found[0] for processes in found):
        raise ValueError(
            f"correction '{correction['name']}' in '{path}': process categories "
            f"{sorted(sorted(p) for p in found)} differ; each must be one of {allowed}"
        )
    if found[0] not in FRACTION_PROCESS_SETS:
        raise ValueError(
            f"correction '{correction['name']}' in '{path}': process categories "
            f"{sorted(found[0])}, the friend sums {allowed}"
        )
    return found[0]


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
