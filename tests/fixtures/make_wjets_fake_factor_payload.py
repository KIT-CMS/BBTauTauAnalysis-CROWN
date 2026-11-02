#!/usr/bin/env python3
"""Synthetic QCD + W + ttbar fake-factor payload for the tests of v7 spec C15.

There is no measured W payload yet (it follows from the v7 fake-factor
measurement), so the tests derive one from a measured QCD + ttbar payload of et
and mt: the W+jets fake factors, DR->SR correction and closure are copies of the
QCD ones, renamed (``Wjets...``) and scaled so that W cannot be mistaken for QCD
(fake factors x0.5, DR->SR x1.1, closure x0.9), and the fractions get a Wjets
category, the QCD fractions x0.25, with the shifts ``frac_Wjets_up/down``. Only
the structure matters, not the physics: the fractions no longer sum to 1.

    python3 make_wjets_fake_factor_payload.py <measured payload dir> <output dir>
"""
import copy
import gzip
import json
import sys
from pathlib import Path

SCOPES = ("et", "mt")
FF_SCALE, FRACTION_SCALE, DR_SR_SCALE, CLOSURE_SCALE = 0.5, 0.25, 1.1, 0.9


def _scale(node, factor):
    """Multiply every value of the binnings below ``node`` (flow values too)."""
    if isinstance(node, dict):
        if node.get("nodetype") == "binning":
            node["content"] = [
                c * factor if isinstance(c, (int, float)) else _scale(c, factor)
                for c in node["content"]
            ]
            flow = node.get("flow")
            if isinstance(flow, (int, float)):
                node["flow"] = flow * factor
            elif isinstance(flow, dict):
                _scale(flow, factor)
            return node
        for value in node.values():
            _scale(value, factor)
    elif isinstance(node, list):
        for value in node:
            _scale(value, factor)
    return node


def _as_wjets(correction, factor):
    """A copy of a QCD correction for W: name and syst keys renamed, scaled."""
    result = copy.deepcopy(correction)
    result["name"] = "Wjets" + result["name"][len("QCD"):]
    data = result["data"]
    for item in data["content"]:
        if item["key"].startswith("QCD"):
            item["key"] = "Wjets" + item["key"][len("QCD"):]
    _scale(data, factor)
    return result


def _add_wjets_fractions(fractions):
    """Add the Wjets category to every process category and the Wjets shifts."""

    def walk(node):
        if isinstance(node, dict):
            if node.get("nodetype") == "category" and node.get("input") == "process":
                (qcd,) = [item for item in node["content"] if item["key"] == "QCD"]
                wjets = {"key": "Wjets", "value": _scale(copy.deepcopy(qcd["value"]), FRACTION_SCALE)}
                node["content"].insert(1, wjets)
                return
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(fractions["data"])
    data = fractions["data"]
    shifts = [item for item in data["content"] if "frac_QCD" in item["key"]]
    for item in shifts:
        data["content"].append(
            {"key": item["key"].replace("frac_QCD", "frac_Wjets"), "value": copy.deepcopy(item["value"])}
        )


def make(source: Path, target: Path, scopes=SCOPES) -> Path:
    """Write the W payloads of ``scopes`` from the measured ones in ``source``."""
    target.mkdir(parents=True, exist_ok=True)
    for scope in scopes:
        with gzip.open(source / f"fake_factors_{scope}.json.gz", "rt") as handle:
            fake_factors = json.load(handle)
        with gzip.open(source / f"FF_corrections_{scope}.json.gz", "rt") as handle:
            corrections = json.load(handle)

        by_name = {c["name"]: c for c in fake_factors["corrections"]}
        fake_factors["corrections"].insert(1, _as_wjets(by_name["QCD_fake_factors"], FF_SCALE))
        _add_wjets_fractions(by_name["process_fractions"])

        by_name = {c["name"]: c for c in corrections["corrections"]}
        compounds = {c["name"]: c for c in corrections["compound_corrections"]}
        corrections["corrections"].append(_as_wjets(by_name["QCD_DR_SR_correction"], DR_SR_SCALE))
        stack = []
        for member in compounds["QCD_compound_correction"]["stack"]:
            wjets = _as_wjets(by_name[member], CLOSURE_SCALE)
            corrections["corrections"].append(wjets)
            stack.append(wjets["name"])
        compound = copy.deepcopy(compounds["QCD_compound_correction"])
        compound["name"] = "Wjets_compound_correction"
        compound["stack"] = stack
        corrections["compound_corrections"].append(compound)

        for name, payload in (("fake_factors", fake_factors), ("FF_corrections", corrections)):
            with gzip.open(target / f"{name}_{scope}.json.gz", "wt") as handle:
                json.dump(payload, handle)
    return target


if __name__ == "__main__":
    print(make(Path(sys.argv[1]), Path(sys.argv[2])))
