"""Pinned 2018 UL NanoAOD v15 UParT b-tagging payload helpers.

Config-time helpers that read the pinned BTV ``correctionlib`` payload using
only the standard library (``gzip`` + ``json``).  ``correctionlib`` itself is
deliberately *not* imported here, so the analysis configuration can be
constructed (and unit-tested) without the C++ correction backend.

The payload is validated against a small set of frozen constants: a silent
upstream re-derivation of the working points is turned into a loud, actionable
error at build time rather than a subtle physics bug in the produced ntuples.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from typing import Dict, Iterable, Set

# Pinned BTV UParTAK4 payload for the SM 2018 UL NanoAOD v15 path.  The pin is a
# dated CAT-metadata snapshot on cvmfs; bumping it requires revalidating the
# working points and systematic variations below.
PINNED_BTV_2018_V15 = (
    "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/"
    "Run2-2018-UL-NanoAODv15/2026-06-18/btagging.json.gz"
)

# Names of the UParTAK4 corrections stored in the pinned payload.
WP_VALUES_CORRECTION = "UParTAK4_wp_values"
COMB_SF_CORRECTION = "UParTAK4_comb"
LIGHT_SF_CORRECTION = "UParTAK4_light"

# Working points frozen against the pinned payload.  ``load_upart_wps`` raises
# if the payload no longer matches these values (revalidate before bumping).
EXPECTED_UPART_WPS: Dict[str, float] = {
    "L": 0.0308,
    "M": 0.161,
    "T": 0.5405,
    "XT": 0.6992,
    "XXT": 0.9655,
}

_REVALIDATE_HINT = (
    "revalidate the SM UParTAK4 working points and systematic variations "
    "against the new file and update btag_payloads.PINNED_BTV_2018_V15 / "
    "EXPECTED_UPART_WPS accordingly"
)


def _load_payload(path: str) -> dict:
    """Read and JSON-decode a gzipped correctionlib payload from ``path``."""
    try:
        with gzip.open(path, "rt") as handle:
            return json.load(handle)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"pinned BTV UParTAK4 payload not found at '{path}'; {_REVALIDATE_HINT}"
        ) from error


def _get_correction(payload: dict, name: str, path: str) -> dict:
    """Return the correction named ``name`` from a decoded payload."""
    for correction in payload.get("corrections", []):
        if correction.get("name") == name:
            return correction
    found = [c.get("name") for c in payload.get("corrections", [])]
    raise ValueError(
        f"correction '{name}' not found in payload '{path}'; "
        f"found corrections {found}; {_REVALIDATE_HINT}"
    )


def load_upart_wps(path: str = PINNED_BTV_2018_V15) -> Dict[str, float]:
    """Read the ``UParTAK4_wp_values`` working points from the pinned payload.

    Walks ``corrections[name == "UParTAK4_wp_values"].data.content`` collecting
    the ``key`` -> ``value`` pairs, then validates them against the frozen
    :data:`EXPECTED_UPART_WPS`.  Raises ``FileNotFoundError`` if the payload is
    missing and ``ValueError`` if the working points drifted from the pin.
    """
    payload = _load_payload(path)
    correction = _get_correction(payload, WP_VALUES_CORRECTION, path)
    working_points = {
        item["key"]: item["value"]
        for item in correction["data"]["content"]
    }
    if working_points != EXPECTED_UPART_WPS:
        raise ValueError(
            f"UParTAK4 working points in '{path}' do not match the pin: "
            f"expected {EXPECTED_UPART_WPS}, found {working_points}; "
            f"{_REVALIDATE_HINT}"
        )
    return working_points


def discover_upart_variations(
    path: str = PINNED_BTV_2018_V15,
) -> Dict[str, Set[str]]:
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


# ---------------------------------------------------------------------------
# Validated per-scope b-tag EFFICIENCY payload gate (SM main config).
#
# Unlike the SF payload above (a single pinned cvmfs file, validated against
# frozen constants), the efficiency payload is produced per-analysis by the
# TauFakeFactors framework from the SM b-tag-efficiency ntuples and installed
# alongside the analysis config. It therefore needs a *provenance* check
# instead of a content pin: did the installed files actually come out of the
# validated measurement chain, unmodified?
# ---------------------------------------------------------------------------

# The 13 sample-type categories the SM efficiency-measurement chain
# (sm_btag_efficiency_config -> TauFakeFactors -> install) produces on the
# ``sample_type`` axis of every per-scope ``btag_efficiency_<scope>.json.gz``.
# Fixed by the physics program, independent of which subset of samples any
# particular build call declares as ``available_sample_types``.
SM_BTAG_EFFICIENCY_CATEGORIES: tuple = (
    "hh2b2tau",
    "dyjets",
    "wjets",
    "ttbar",
    "singletop",
    "diboson",
    "electroweak_boson",
    "ggh_htautau",
    "vbf_htautau",
    "vbf_hbb",
    "rem_hbb",
    "rem_higgs",
    "rem_ttbar",
)

# Directory this module lives in doubles as the bbtautau analysis-config root
# (``btag_payloads.py`` sits directly under ``analysis_configurations/bbtautau/``);
# ``AnalysisProfile.btag_payload_dir`` is a path relative to it.
_ANALYSIS_ROOT = os.path.dirname(os.path.abspath(__file__))

PRODUCTION_CHAIN_HINT = (
    "produce via sm_btag_efficiency_config -> TauFakeFactors -> install"
)


def resolve_payload_dir(payload_dir) -> str:
    """Resolve an ``AnalysisProfile.btag_payload_dir`` to an absolute path.

    Relative paths (the normal case, e.g.
    ``"payloads/btagging_efficiencies/upart_nanoaodv15/2018"``) are resolved
    against the bbtautau analysis-config root, matching how
    ``common_config.add_bjet_config`` interpolates the same field into the
    runtime ``bjet_eff_file`` config parameter. Absolute paths (as used by
    tests pointing at a synthetic fixture directory) are returned unchanged.
    Raises ``ValueError`` if ``payload_dir`` is ``None`` (a profile that
    requires the validated payload must also set a directory for it).
    """
    if payload_dir is None:
        raise ValueError(
            "AnalysisProfile.require_validated_btag_payload is True but "
            "btag_payload_dir is not set; " + PRODUCTION_CHAIN_HINT
        )
    return os.path.join(_ANALYSIS_ROOT, payload_dir)


def _sha256_of_file(path: str) -> str:
    """Return the hex SHA256 digest of the raw bytes of ``path``."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sample_type_categories(payload: dict, path: str) -> Set[str]:
    """Return the top-level ``sample_type`` category keys of a payload.

    Scans ``payload["corrections"]`` for the correction whose ``data`` node is
    a ``category`` keyed on ``"sample_type"`` (the efficiency correction's
    outermost axis) and returns its ``key`` values.
    """
    for correction in payload.get("corrections", []):
        data = correction.get("data", {})
        if data.get("nodetype") == "category" and data.get("input") == "sample_type":
            return {item["key"] for item in data.get("content", []) if "key" in item}
    raise ValueError(
        f"no 'sample_type' category axis found in any correction of payload "
        f"'{path}'; {PRODUCTION_CHAIN_HINT}"
    )


def require_validated_payload(
    payload_dir: str,
    channel_scopes: Iterable[str],
    expected_categories: Iterable[str],
) -> dict:
    """Gate the strict UParTAK4 efficiency payload before code generation.

    Reads ``<payload_dir>/provenance.json`` and enforces that the per-scope
    efficiency payloads it describes came out of the validated production
    chain (``sm_btag_efficiency_config -> TauFakeFactors -> install``) before
    any producer referencing them is scheduled:

    * ``provenance["validation_status"] == "passed"``;
    * the SHA256 of every ``btag_efficiency_<scope>.json.gz`` (one per entry
      in ``channel_scopes``) matches the corresponding
      ``provenance["manifest"]`` entry;
    * every category in ``expected_categories`` is present on the
      ``sample_type`` axis of each payload's correctionlib JSON.

    Raises ``FileNotFoundError`` if the provenance file or a per-scope
    payload file is missing, naming both the expected path and the
    production chain that creates it. Raises ``ValueError`` naming the
    offending file for a failed validation status, a checksum mismatch, or a
    missing category. Returns the parsed provenance dict on success.
    """
    provenance_path = os.path.join(payload_dir, "provenance.json")
    try:
        with open(provenance_path, "r") as handle:
            provenance = json.load(handle)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"validated b-tag efficiency payload provenance not found at "
            f"'{provenance_path}'; {PRODUCTION_CHAIN_HINT}"
        ) from error

    status = provenance.get("validation_status")
    if status != "passed":
        raise ValueError(
            f"b-tag efficiency payload at '{payload_dir}' has "
            f"validation_status={status!r} (expected 'passed'); "
            f"{PRODUCTION_CHAIN_HINT}"
        )

    manifest = provenance.get("manifest", {})
    expected_categories = set(expected_categories)
    for scope in channel_scopes:
        file_name = f"btag_efficiency_{scope}.json.gz"
        file_path = os.path.join(payload_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"validated b-tag efficiency payload '{file_path}' not "
                f"found; {PRODUCTION_CHAIN_HINT}"
            )

        actual_sha256 = _sha256_of_file(file_path)
        manifest_entry = manifest.get(file_name) or {}
        expected_sha256 = manifest_entry.get("sha256")
        if expected_sha256 != actual_sha256:
            raise ValueError(
                f"b-tag efficiency payload '{file_path}' failed checksum "
                f"validation against provenance manifest: expected "
                f"sha256={expected_sha256!r}, found {actual_sha256!r}; "
                f"{PRODUCTION_CHAIN_HINT}"
            )

        payload = _load_payload(file_path)
        found_categories = _sample_type_categories(payload, file_path)
        missing = sorted(expected_categories - found_categories)
        if missing:
            raise ValueError(
                f"b-tag efficiency payload '{file_path}' is missing expected "
                f"sample_type categories {missing}; {PRODUCTION_CHAIN_HINT}"
            )

    return provenance
