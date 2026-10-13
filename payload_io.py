"""Config-time access to gzipped correctionlib payloads.

Uses only the standard library (``gzip`` + ``json``), so configurations that
read a payload at configuration time can be built and tested without the
correctionlib backend.
"""
from __future__ import annotations

import gzip
import json


def load_payload(path: str) -> dict:
    """Read and JSON-decode the gzipped correctionlib payload at ``path``."""
    try:
        with gzip.open(path, "rt") as handle:
            return json.load(handle)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"payload not found at '{path}'") from error


def get_correction(
    payload: dict, name: str, path: str, section: str = "corrections"
) -> dict:
    """Return the entry named ``name`` from ``section`` of a decoded payload.

    ``section`` is ``"corrections"`` or ``"compound_corrections"``; a section
    that is missing or null counts as empty.
    """
    entries = payload.get(section) or []
    for entry in entries:
        if entry.get("name") == name:
            return entry
    raise ValueError(
        f"{section} entry '{name}' not found in payload '{path}'; "
        f"found {[entry.get('name') for entry in entries]}"
    )
