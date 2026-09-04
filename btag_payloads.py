"""UParT b-tagging payload helpers for the Run-2 UL NanoAOD v15 inputs.

Config-time helpers that read the pinned BTV ``correctionlib`` payload using
only the standard library (``gzip`` + ``json``).  ``correctionlib`` itself is
deliberately *not* imported here, so the analysis configuration can be
constructed (and unit-tested) without the C++ correction backend.

Working points and systematic variations are read directly from the selected
BTV payload.
"""
from __future__ import annotations

import gzip
import json
from typing import Dict, Set

from .constants import ERAS_RUN2

# Pinned BTV UParTAK4 payloads for the Run-2 UL NanoAOD v15 inputs, one per
# era.  Each pin is a dated CAT-metadata snapshot on cvmfs (never the rolling
# "latest" symlink); all four ship the UParTAK4_wp_values / UParTAK4_comb /
# UParTAK4_light corrections read below.
BTV_UPART_PAYLOADS: Dict[str, str] = {
    era: (
        "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/"
        f"Run2-{era}-UL-NanoAODv15/2026-06-18/btagging.json.gz"
    )
    for era in ERAS_RUN2
}


def btv_upart_payload(era: str) -> str:
    """Return the pinned BTV UParTAK4 payload path for ``era``.

    Raises a ``KeyError`` naming the pinned eras when ``era`` has no pin, so a
    profile enabling the UParT path for an unsupported era fails at config
    time instead of at run time inside correctionlib.
    """
    try:
        return BTV_UPART_PAYLOADS[era]
    except KeyError as error:
        raise KeyError(
            f"no pinned BTV UParTAK4 payload for era '{era}'; pinned eras: "
            f"{sorted(BTV_UPART_PAYLOADS)}"
        ) from error

# Names of the UParTAK4 corrections stored in the pinned payload.
WP_VALUES_CORRECTION = "UParTAK4_wp_values"
COMB_SF_CORRECTION = "UParTAK4_comb"
LIGHT_SF_CORRECTION = "UParTAK4_light"

def _load_payload(path: str) -> dict:
    """Read and JSON-decode a gzipped correctionlib payload from ``path``."""
    try:
        with gzip.open(path, "rt") as handle:
            return json.load(handle)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"BTV UParTAK4 payload not found at '{path}'"
        ) from error


def _get_correction(payload: dict, name: str, path: str) -> dict:
    """Return the correction named ``name`` from a decoded payload."""
    for correction in payload.get("corrections", []):
        if correction.get("name") == name:
            return correction
    found = [c.get("name") for c in payload.get("corrections", [])]
    raise ValueError(
        f"correction '{name}' not found in payload '{path}'; "
        f"found corrections {found}"
    )


def load_upart_wps(path: str) -> Dict[str, float]:
    """Read the ``UParTAK4_wp_values`` working points from the payload at ``path``.

    Walks ``corrections[name == "UParTAK4_wp_values"].data.content`` and
    returns its ``key`` -> ``value`` pairs.
    """
    payload = _load_payload(path)
    correction = _get_correction(payload, WP_VALUES_CORRECTION, path)
    return {
        item["key"]: item["value"]
        for item in correction["data"]["content"]
    }


def discover_upart_variations(path: str) -> Dict[str, Set[str]]:
    """Return the systematic-variation keys of the two UParTAK4 SF corrections.

    Collects ``data.content[*].key`` (the top-level ``systematic`` category) of
    the ``UParTAK4_comb`` and ``UParTAK4_light`` corrections, e.g.::

        {"UParTAK4_comb": {"central", "up", "down", "up_correlated", ...},
         "UParTAK4_light": {"central", "up", "down", "up_correlated", ...}}
    """
    payload = _load_payload(path)
    variations: Dict[str, Set[str]] = {}
    for name in (COMB_SF_CORRECTION, LIGHT_SF_CORRECTION):
        correction = _get_correction(payload, name, path)
        variations[name] = {
            item["key"]
            for item in correction["data"]["content"]
            if "key" in item
        }
    return variations
