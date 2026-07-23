"""Synthetic ``btag_efficiency_<scope>.json.gz`` + ``provenance.json`` writer.

Used by the validated-payload-gate tests (``test_sm_main_config.py`` and
``test_sm_v15_jet_path.py``) to build a small, self-contained, PASSING payload
directory under a tempdir -- mirroring the real schema the SM b-tag
efficiency-measurement chain (``sm_btag_efficiency_config`` ->
``TauFakeFactors`` -> install) produces, without depending on the real
(externally-produced) payload. Follows the same generator-function pattern as
``tests/fixtures/make_btag_sf_strict_fixtures.py`` (the strict-consumer C++
test fixtures), but writes directly to an arbitrary directory at test time
instead of a fixed, checked-in JSON pair, since the payload here is
ephemeral/per-test rather than a committed golden fixture.

Correctionlib schema (5 levels, matching the real efficiency payload):
Category(sample_type) -> Category(working_point) -> Category(jet_flavor:int)
-> Binning(eta) -> Binning(pt) -> value.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os

WPS = ("L", "M", "T", "XT", "XXT")


def _flavor_category(value: float) -> dict:
    return {
        "nodetype": "category",
        "input": "jet_flavor",
        "content": [
            {
                "key": flavor,
                "value": {
                    "nodetype": "binning",
                    "input": "eta",
                    "edges": [0.0, 2.5],
                    "content": [
                        {
                            "nodetype": "binning",
                            "input": "pt",
                            "edges": [20.0, 1000.0],
                            "content": [value],
                            "flow": "clamp",
                        }
                    ],
                    "flow": "clamp",
                },
            }
            for flavor in (0, 4, 5)
        ],
    }


def _efficiency_correction(categories) -> dict:
    return {
        "name": "btag_efficiency",
        "version": 1,
        "inputs": [
            {"name": "sample_type", "type": "string"},
            {"name": "working_point", "type": "string"},
            {"name": "jet_flavor", "type": "int"},
            {"name": "eta", "type": "real"},
            {"name": "pt", "type": "real"},
        ],
        "output": {"name": "efficiency", "type": "real"},
        "data": {
            "nodetype": "category",
            "input": "sample_type",
            "content": [
                {
                    "key": sample_type,
                    "value": {
                        "nodetype": "category",
                        "input": "working_point",
                        "content": [
                            {"key": wp, "value": _flavor_category(0.1)}
                            for wp in WPS
                        ],
                    },
                }
                for sample_type in categories
            ],
        },
    }


def _sha256_of_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_passing_payload(
    payload_dir: str,
    scopes=("et", "mt", "tt"),
    categories=None,
) -> None:
    """Write a minimal, PASSING synthetic efficiency payload + provenance.

    Creates ``payload_dir`` (if needed) and writes one
    ``btag_efficiency_<scope>.json.gz`` per entry in ``scopes`` (each
    carrying every entry in ``categories`` on the ``sample_type`` axis, plus
    working points L/M/T/XT/XXT), and a ``provenance.json`` with
    ``validation_status: "passed"`` and a manifest of the real SHA256 of each
    written file -- i.e. a payload that
    ``btag_payloads.require_validated_payload`` accepts as-is.
    """
    if categories is None:
        from analysis_configurations.bbtautau import btag_payloads

        categories = btag_payloads.SM_BTAG_EFFICIENCY_CATEGORIES

    os.makedirs(payload_dir, exist_ok=True)
    payload = {
        "schema_version": 2,
        "description": "synthetic SM b-tag efficiency payload (gate test fixture)",
        "corrections": [_efficiency_correction(categories)],
    }

    manifest = {}
    for scope in scopes:
        file_name = f"btag_efficiency_{scope}.json.gz"
        file_path = os.path.join(payload_dir, file_name)
        with gzip.open(file_path, "wt") as handle:
            json.dump(payload, handle)
        manifest[file_name] = {"sha256": _sha256_of_file(file_path)}

    provenance = {
        "validation_status": "passed",
        "produced_by": "sm_btag_efficiency_config -> TauFakeFactors -> install",
        "manifest": manifest,
    }
    with open(os.path.join(payload_dir, "provenance.json"), "w") as handle:
        json.dump(provenance, handle)
