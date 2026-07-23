#!/usr/bin/env python3
"""Validate ``systematics_sm_2018.yaml`` against its schema and the SM 2018
configuration surface it describes.

Two modes:

* default -- schema completeness (every entry carries the required fields,
  every value is one of the allowed enum members; a schema failure
  short-circuits the run and is reported on its own, since every later check
  below assumes the required fields are present). Given a schema-complete
  inventory: all four ``execution_class`` values are represented at least
  once; every SM ``crown_shift`` name the framework actually registers (built
  with ``shifts={"all"}`` across every SM MC sample nick,
  ``SM_SHIFT_ENUMERATION_SAMPLES``) is covered by at least one inventory
  entry's ``shift_name_patterns`` and every ``shift_name_patterns`` substring
  matches at least one such name ("unused pattern"), each registered shift
  belongs to exactly one entry's patterns ("ambiguous coverage" -- the
  single-owner rule, see the YAML header); and the dynamic UParTAK4
  ``variation_keys`` marker expands against the pinned BTV payload.
* ``--final-inference`` -- additionally rejects any entry with
  ``final_disposition: pending_review`` and any entry whose
  ``production_status`` is not ``produced`` unless its ``final_disposition``
  starts with ``excluded:``. This is a deliberately strict gate for
  paper/limit-ready inference; at this milestone the inventory is expected to
  fail it (several sources are still ``pending_review`` or
  ``registered_not_produced``/``planned`` without an ``excluded:`` disposition
  -- see the YAML file's own comments).

This script (and the ``analysis_configurations.bbtautau.btag_payloads`` /
``common_config`` / ``sm_config`` imports it performs to build the SM shift
registration) requires PyYAML. It is a standalone dev script, not imported by
``common_config.py`` or ``nmssm_config.py``.

Usage::

    python scripts/validate_systematics_inventory.py
    python scripts/validate_systematics_inventory.py --final-inference
"""
from __future__ import annotations

import argparse
import dataclasses
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

import yaml

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY_PATH = ANALYSIS_ROOT / "systematics_sm_2018.yaml"

# Make ``analysis_configurations`` importable when this script is invoked
# directly (``python scripts/validate_systematics_inventory.py``) rather than
# via ``python -m ...`` from the CROWN root -- Python only puts the *script's
# own directory* on sys.path in the former case, not the cwd, so the absolute
# ``analysis_configurations.bbtautau...`` imports below (and the module-level
# ``sm_config`` import right below this block) would otherwise raise
# ``ModuleNotFoundError``. Three parents up from this file: scripts/ ->
# bbtautau/ -> analysis_configurations/ -> CROWN root.
_CROWN_ROOT = Path(__file__).resolve().parents[3]
if str(_CROWN_ROOT) not in sys.path:
    sys.path.insert(0, str(_CROWN_ROOT))

from analysis_configurations.bbtautau import sm_config  # noqa: E402

EXECUTION_CLASSES = {
    "nominal_column",
    "crown_shift",
    "alternative_sample",
    "downstream",
}
PRODUCTION_STATUSES = {"produced", "registered_not_produced", "planned"}
REQUIRED_FIELDS = {
    "name",
    "execution_class",
    "affected_samples",
    "affected_channels",
    "source",
    "variation_keys",
    "correlation_policy",
    "production_status",
    "final_disposition",
}
# The literal marker used by nominal_column entries whose variation_keys are
# expanded at check time from a live (pinned) correctionlib payload rather
# than being spelled out in the YAML (see btag_payloads.discover_upart_variations).
DYNAMIC_VARIATION_KEYS_MARKER = "pinned payload (dynamic)"

# Every SM MC sample nick (i.e. all of sm_config.DEFAULT_SAMPLES except
# "data", which registers no shifts) rather than a hand-picked subset: several
# shift families are gated by `if sample in [...]`/`if "dyjets" in sample or
# "electroweak_boson" in sample` in common_config.py, so a proper subset is
# not safe to maintain by hand -- a full census is the only honest way to
# enumerate every crown_shift name the SM 2018 configuration surface can
# register. Measured at ~3s for all 13 samples x 6 scopes (see
# scripts/validate_systematics_inventory.py's own report / task-12 fix
# report), so the full census is cheap enough to always use.
SM_SHIFT_ENUMERATION_SAMPLES = tuple(
    sample for sample in sm_config.DEFAULT_SAMPLES if sample != "data"
)


def load_inventory(path: Path = DEFAULT_INVENTORY_PATH) -> List[dict]:
    """Read and parse ``systematics_sm_2018.yaml``, returning its entry list."""
    with open(path, "r") as handle:
        data = yaml.safe_load(handle)
    entries = data.get("systematics")
    if not isinstance(entries, list):
        raise ValueError(f"'{path}' has no top-level 'systematics' list")
    return entries


def check_schema(entries: List[dict]) -> List[str]:
    """Return a list of human-readable schema-violation messages (empty = OK)."""
    errors: List[str] = []
    seen_names: Set[str] = set()
    seen_classes: Set[str] = set()

    for index, entry in enumerate(entries):
        label = entry.get("name", f"<entry #{index}>")
        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            errors.append(f"{label}: missing required field(s) {sorted(missing)}")
            continue

        name = entry["name"]
        if name in seen_names:
            errors.append(f"duplicate entry name: {name!r}")
        seen_names.add(name)

        execution_class = entry["execution_class"]
        if execution_class not in EXECUTION_CLASSES:
            errors.append(
                f"{name}: execution_class {execution_class!r} not in "
                f"{sorted(EXECUTION_CLASSES)}"
            )
        else:
            seen_classes.add(execution_class)

        production_status = entry["production_status"]
        if production_status not in PRODUCTION_STATUSES:
            errors.append(
                f"{name}: production_status {production_status!r} not in "
                f"{sorted(PRODUCTION_STATUSES)}"
            )

        final_disposition = entry["final_disposition"]
        if not (
            final_disposition in ("propagate", "pending_review")
            or (
                isinstance(final_disposition, str)
                and final_disposition.startswith("excluded:")
            )
        ):
            errors.append(
                f"{name}: final_disposition {final_disposition!r} must be "
                "'propagate', 'pending_review', or start with 'excluded:'"
            )

        variation_keys = entry["variation_keys"]
        if not (
            isinstance(variation_keys, list)
            or variation_keys == DYNAMIC_VARIATION_KEYS_MARKER
        ):
            errors.append(
                f"{name}: variation_keys must be a list or the literal "
                f"marker {DYNAMIC_VARIATION_KEYS_MARKER!r}"
            )

        if execution_class == "crown_shift" and "shift_name_patterns" not in entry:
            errors.append(
                f"{name}: crown_shift entries must carry a "
                "'shift_name_patterns' field (may be an empty list for a "
                "not-yet-registered shift)"
            )

        if not entry.get("affected_samples"):
            errors.append(f"{name}: affected_samples must be a non-empty list")
        if not entry.get("affected_channels"):
            errors.append(f"{name}: affected_channels must be a non-empty list")
        if not entry.get("source"):
            errors.append(f"{name}: source must be non-empty")
        if not entry.get("correlation_policy"):
            errors.append(f"{name}: correlation_policy must be non-empty")

    missing_classes = EXECUTION_CLASSES - seen_classes
    if missing_classes:
        errors.append(
            f"no entry present for execution_class(es): {sorted(missing_classes)}"
        )

    return errors


def build_sm_registered_shifts(
    samples: Iterable[str] = SM_SHIFT_ENUMERATION_SAMPLES,
) -> Set[str]:
    """Build the SM config with ``shifts={"all"}`` across ``samples`` and
    return the union of every ``crown_shift`` name registered in any scope.

    Uses the same ``dataclasses.replace(SM_PROFILE, btag_payload_dir=...)`` +
    synthetic-passing-payload pattern as
    ``tests/test_sm_main_config.py::build_sm_valid_payload`` (and its
    ``tests/fixtures/sm_btag_efficiency_payload.write_passing_payload``
    fixture) so the strict validated-payload gate does not block the build
    before any shift is registered.
    """
    from analysis_configurations.bbtautau import common_config
    from analysis_configurations.bbtautau.analysis_profiles import SM_PROFILE
    from analysis_configurations.bbtautau.constants import SCOPES
    from analysis_configurations.bbtautau.tests.fixtures import (
        sm_btag_efficiency_payload as payload_fixture,
    )

    payload_dir = tempfile.mkdtemp(prefix="validate_systematics_inventory_")
    payload_fixture.write_passing_payload(payload_dir, scopes=("et", "mt", "tt"))
    profile = dataclasses.replace(SM_PROFILE, btag_payload_dir=payload_dir)

    registered: Set[str] = set()
    for sample in samples:
        cfg = common_config.build_config(
            profile,
            "2018",
            sample,
            list(SCOPES),
            {"all"},
            sm_config.AVAILABLE_SAMPLES,
            ["2018"],
            SCOPES,
        )
        for scope in list(SCOPES) + ["global"]:
            registered.update(cfg.shifts.get(scope, []))
    return registered


def check_shift_coverage(
    entries: List[dict], registered_shifts: Set[str]
) -> List[str]:
    """Enforce the coverage + single-owner invariants between ``crown_shift``
    entries' ``shift_name_patterns`` and the framework's actually-registered
    SM shift names (see the "single-owner rule" documented in the YAML
    header):

    * every name in ``registered_shifts`` must contain at least one
      ``crown_shift`` entry's ``shift_name_patterns`` substring ("uncovered"
      -- the original check);
    * every ``shift_name_patterns`` substring must match at least one name in
      ``registered_shifts`` ("unused pattern" -- a pattern that matches
      nothing is either stale or was never actually wired up, e.g. describing
      a shift that is not, in fact, registered for any SM sample);
    * no name in ``registered_shifts`` may be matched by patterns owned by
      more than one ``crown_shift`` entry ("ambiguous coverage" -- each
      registered shift must have exactly one inventory entry responsible for
      it, so downstream consumers of this inventory never have to guess
      which entry's classification/production_status/correlation_policy
      applies to a given shift name).
    """
    # (entry name, its shift_name_patterns) pairs, so ambiguity can be
    # attributed to specific entries rather than just reported as a bare list
    # of patterns.
    entry_patterns: List[Tuple[str, List[str]]] = [
        (entry.get("name", "<unnamed>"), entry.get("shift_name_patterns") or [])
        for entry in entries
        if entry.get("execution_class") == "crown_shift"
    ]
    all_patterns = [pattern for _, patterns in entry_patterns for pattern in patterns]

    errors: List[str] = []

    uncovered = sorted(
        shift
        for shift in registered_shifts
        if not any(pattern in shift for pattern in all_patterns)
    )
    if uncovered:
        errors.append(
            "registered SM crown shift(s) with no matching inventory entry "
            f"(shift_name_patterns): {uncovered}"
        )

    unused_patterns = sorted(
        pattern
        for pattern in set(all_patterns)
        if not any(pattern in shift for shift in registered_shifts)
    )
    if unused_patterns:
        errors.append(
            "unused pattern(s) in shift_name_patterns -- match zero "
            f"registered SM crown shifts: {unused_patterns}"
        )

    ambiguous = []
    for shift in sorted(registered_shifts):
        owners = sorted(
            {
                name
                for name, patterns in entry_patterns
                if any(pattern in shift for pattern in patterns)
            }
        )
        if len(owners) > 1:
            ambiguous.append(f"{shift!r} claimed by {owners}")
    if ambiguous:
        errors.append(
            "ambiguous coverage -- registered SM crown shift(s) matched by "
            "shift_name_patterns from more than one crown_shift entry "
            f"(single-owner rule violated): {ambiguous}"
        )

    return errors


def check_upart_dynamic_variation_keys(entries: List[dict]) -> List[str]:
    """The UParTAK4 nominal_column entry's dynamic marker must expand against
    the pinned BTV payload to a non-empty set of variation keys."""
    from analysis_configurations.bbtautau import btag_payloads

    dynamic_entries = [
        entry
        for entry in entries
        if entry.get("execution_class") == "nominal_column"
        and entry.get("variation_keys") == DYNAMIC_VARIATION_KEYS_MARKER
    ]
    if not dynamic_entries:
        return [
            "no nominal_column entry declares the dynamic UParT "
            f"variation_keys marker ({DYNAMIC_VARIATION_KEYS_MARKER!r})"
        ]

    errors: List[str] = []
    try:
        variations = btag_payloads.discover_upart_variations(
            btag_payloads.PINNED_BTV_2018_V15
        )
    except FileNotFoundError as error:
        return [f"could not expand the dynamic UParT variation_keys marker: {error}"]

    keys = (variations.get("UParTAK4_comb", set()) | variations.get(
        "UParTAK4_light", set()
    )) - {"central"}
    if not keys:
        errors.append(
            "UParT dynamic variation_keys expanded to zero keys against the "
            "pinned payload"
        )
    return errors


def check_final_inference_gate(entries: List[dict]) -> List[str]:
    """``--final-inference`` gate: no pending_review, and every non-produced
    entry must carry an 'excluded:' final_disposition.

    Entries missing ``final_disposition`` and/or ``production_status`` are
    skipped here rather than raising a ``KeyError``: ``run()`` short-circuits
    on any ``check_schema`` failure before this check ever runs, so in the
    normal CLI/``run()`` flow a schema-incomplete entry has already had its
    failure recorded there. This guard exists so calling this function
    directly (e.g. from a test, or from future code that does not go through
    ``run()``) degrades to "skip the incomplete entry" instead of crashing.
    """
    errors: List[str] = []
    for index, entry in enumerate(entries):
        if "final_disposition" not in entry or "production_status" not in entry:
            continue

        name = entry.get("name", f"<entry #{index}>")
        final_disposition = entry["final_disposition"]
        production_status = entry["production_status"]

        if final_disposition == "pending_review":
            errors.append(
                f"{name}: final_disposition=pending_review is not allowed "
                "under --final-inference"
            )
        elif production_status != "produced" and not final_disposition.startswith(
            "excluded:"
        ):
            errors.append(
                f"{name}: production_status={production_status!r} without an "
                "'excluded:' final_disposition is not allowed under "
                "--final-inference"
            )
    return errors


def run(
    final_inference: bool = False,
    inventory_path: Path = DEFAULT_INVENTORY_PATH,
) -> Tuple[bool, List[str]]:
    """Run all checks for the requested mode; returns ``(ok, error_messages)``.

    Short-circuits after ``check_schema``: every later check (shift coverage,
    the dynamic UParT variation-keys expansion, the final-inference gate)
    assumes every entry already carries its required fields (e.g. indexes
    ``entry["name"]``/``entry["final_disposition"]`` directly), so running
    them against a schema-incomplete inventory would raise a raw ``KeyError``
    instead of the clean itemized report this function promises. A missing
    field is already the most actionable failure mode on its own; there is
    nothing a downstream check could add.
    """
    entries = load_inventory(inventory_path)

    schema_errors = check_schema(entries)
    if schema_errors:
        return False, schema_errors

    errors: List[str] = []
    registered_shifts = build_sm_registered_shifts()
    errors += check_shift_coverage(entries, registered_shifts)
    errors += check_upart_dynamic_variation_keys(entries)
    if final_inference:
        errors += check_final_inference_gate(entries)

    return (len(errors) == 0), errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--final-inference",
        action="store_true",
        help=(
            "additionally reject pending_review entries and any "
            "non-produced entry lacking an 'excluded:' disposition"
        ),
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY_PATH,
        help="path to the systematics inventory YAML (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    ok, errors = run(
        final_inference=args.final_inference, inventory_path=args.inventory
    )

    mode = " (--final-inference)" if args.final_inference else ""
    if ok:
        print(f"OK: {args.inventory.name} passed validation{mode}")
        return 0

    print(f"FAILED: {len(errors)} problem(s) found in {args.inventory.name}{mode}:")
    for error in errors:
        print(f" - {error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
