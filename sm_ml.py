"""SM (non-resonant) ML friend-tree entry point -- Phase 1 gated stub.

There is currently no trained ONNX model for the SM (non-resonant HH -> bb
tau tau) analysis: unlike the resonance-search friends of the other
analysis profile in this repository, this profile has no per-mass-window
model to evaluate, so it needs no resonance-mass conditioning at all. What
it DOES need, once a model exists, is a small activation manifest
describing which channels are ready and where their payloads live. This
module implements ONLY that gate for now; it reads exclusively from
`payloads/ml/sm/2018/` (no other era, no other analysis's ML payload
directory) and refuses to build until that directory holds a complete
manifest.

Activation manifest
--------------------
`ACTIVATION_MANIFEST` (below) points at
`payloads/ml/sm/2018/activation.yaml`, a YAML document with this schema::

    channels:                       # mapping: channel/scope name -> entry.
                                     # Phase 1 REQUIRES this to be non-empty
                                     # after validation -- an empty mapping
                                     # is treated as "still gated", exactly
                                     # like a missing manifest file.
      <channel>:                    # e.g. "mt", "et", "tt"
        model_file: <path>          # ONNX model file, relative to the
                                     # manifest's own directory
                                     # (payloads/ml/sm/2018/).
        transformation_file: <path> # feature-transformation JSON file,
                                     # relative to the same directory.
        fold_count: <int>           # number of folds the model was
                                     # trained/split across (event-parity
                                     # k-folding).
        event_to_fold_rule: <str>   # human-readable rule mapping an event
                                     # number to a fold index (e.g.
                                     # "event % fold_count"). Recorded and
                                     # checked for presence here only; it is
                                     # the future inference producer's job
                                     # to apply it, not this module's.

Completeness checks performed by `_require_activation_manifest` before
`build_config` does anything else:

1. The manifest file itself exists at `ACTIVATION_MANIFEST`.
2. It parses to a mapping whose `channels` key is itself a mapping.
3. Every channel entry declares all four required keys above.
4. `fold_count` is a positive integer and `event_to_fold_rule` is a
   non-empty string.
5. The `model_file` / `transformation_file` paths each channel declares
   exist on disk (resolved relative to the manifest's directory).
6. At least one channel is declared (an otherwise well-formed manifest with
   an empty `channels` mapping still counts as "no trained model yet").

Phase 1 status: none of this exists yet -- `payloads/ml/sm/2018/` is not
even created, so step 1 above fails immediately and `build_config` raises
`FileNotFoundError` naming the manifest path. No channel is advertised and
no event-to-fold rule is hardcoded anywhere in this module; both come
exclusively from the manifest once one is produced.
"""
from __future__ import annotations

import os
from typing import List, Union

from code_generation.friend_trees import (  # noqa: F401  (dispatcher marker)
    FriendTreeConfiguration,
)

try:
    import yaml

    _HAS_YAML = True
except ImportError:  # pragma: no cover - exercised only without PyYAML
    yaml = None
    _HAS_YAML = False

# Friend build surface: 2018 only (Task-20 sm_fastmtt.py pattern). Checked
# both here (module level, read by generate_friends.py before build_config
# is ever invoked) and as the first statement of build_config below, so a
# direct call bypassing generate_friends.py is equally protected.
AVAILABLE_ERAS = ["2018"]

_ANALYSIS_ROOT = os.path.dirname(os.path.abspath(__file__))
SM_ML_PAYLOAD_DIR = os.path.join(_ANALYSIS_ROOT, "payloads", "ml", "sm", "2018")
ACTIVATION_MANIFEST = os.path.join(SM_ML_PAYLOAD_DIR, "activation.yaml")

_REQUIRED_CHANNEL_KEYS = (
    "model_file",
    "transformation_file",
    "fold_count",
    "event_to_fold_rule",
)

_PHASE1_STATUS = "no trained SM ONNX model; SM ML is gated"


def _require_activation_manifest(manifest_path: str) -> dict:
    """Load and validate the SM ML activation manifest at `manifest_path`.

    Raises `FileNotFoundError` if the manifest itself (or a file it
    references) is missing, or if it declares no channels at all -- with a
    message naming `manifest_path` and the Phase-1 status. Raises
    `ValueError` if the manifest exists but is malformed (see the module
    docstring for the schema). Raises `ImportError` if PyYAML is not
    installed in the running interpreter and the manifest file DOES exist
    (the missing-file case above never needs PyYAML, so it takes priority).
    Returns the parsed manifest dict on success.
    """
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(
            f"SM ML activation manifest not found at '{manifest_path}'; "
            f"Phase-1 status: {_PHASE1_STATUS}. Produce a completed "
            f"manifest plus the per-channel ONNX model and transformation "
            f"files it references under "
            f"'{os.path.dirname(manifest_path)}' before this friend can "
            f"build."
        )

    if not _HAS_YAML:
        raise ImportError(
            f"PyYAML is required to parse the SM ML activation manifest "
            f"at '{manifest_path}' but is not installed in this "
            f"interpreter."
        )

    with open(manifest_path, "r") as handle:
        manifest = yaml.safe_load(handle) or {}

    if not isinstance(manifest, dict):
        raise ValueError(
            f"SM ML activation manifest '{manifest_path}' must parse to a "
            f"mapping, got {type(manifest).__name__}."
        )

    channels = manifest.get("channels") or {}
    if not isinstance(channels, dict):
        raise ValueError(
            f"SM ML activation manifest '{manifest_path}': 'channels' must "
            f"be a mapping, got {type(channels).__name__}."
        )

    payload_dir = os.path.dirname(manifest_path)
    for channel, entry in channels.items():
        if not isinstance(entry, dict):
            raise ValueError(
                f"SM ML activation manifest '{manifest_path}': channel "
                f"'{channel}' entry must be a mapping, got "
                f"{type(entry).__name__}."
            )

        missing_keys = [key for key in _REQUIRED_CHANNEL_KEYS if key not in entry]
        if missing_keys:
            raise ValueError(
                f"SM ML activation manifest '{manifest_path}': channel "
                f"'{channel}' is missing required key(s) {missing_keys} "
                f"(required: {list(_REQUIRED_CHANNEL_KEYS)})."
            )

        fold_count = entry["fold_count"]
        if (
            not isinstance(fold_count, int)
            or isinstance(fold_count, bool)
            or fold_count < 1
        ):
            raise ValueError(
                f"SM ML activation manifest '{manifest_path}': channel "
                f"'{channel}' fold_count must be a positive integer, got "
                f"{fold_count!r}."
            )

        if not entry["event_to_fold_rule"]:
            raise ValueError(
                f"SM ML activation manifest '{manifest_path}': channel "
                f"'{channel}' event_to_fold_rule must be a non-empty "
                f"string."
            )

        for file_key in ("model_file", "transformation_file"):
            file_path = os.path.join(payload_dir, entry[file_key])
            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    f"SM ML activation manifest '{manifest_path}': "
                    f"channel '{channel}' references missing {file_key} "
                    f"'{file_path}'."
                )

    if not channels:
        raise FileNotFoundError(
            f"SM ML activation manifest '{manifest_path}' activates no "
            f"channels; Phase-1 status: {_PHASE1_STATUS}."
        )

    return manifest


def build_config(
    era: str,
    sample: str,
    scopes: List[str],
    shifts: List[str],
    available_sample_types: List[str],
    available_eras: List[str],
    available_scopes: List[str],
    quantities_map: Union[str, None] = None,
):
    if era not in AVAILABLE_ERAS:
        raise ValueError(
            f"Config 'sm_ml' does not support era '{era}' "
            f"(supported: {AVAILABLE_ERAS})."
        )

    # Validate the activation manifest + the files it references BEFORE
    # anything else -- no FriendTreeConfiguration is constructed, no
    # producer is imported, unless a complete manifest is on disk.
    # `ACTIVATION_MANIFEST` is referenced by name (not as a default
    # parameter) so tests can point it at a synthetic fixture via
    # `mock.patch.object(sm_ml, "ACTIVATION_MANIFEST", ...)`.
    manifest = _require_activation_manifest(ACTIVATION_MANIFEST)

    # Reachable only once a complete manifest + its files exist. There is
    # still no SM ONNX inference producer implemented (Phase 1 is
    # validation-only -- see the module docstring), so this is deliberately
    # the honest, clearly-labeled failure past the gate rather than a
    # partial/misleading build.
    channels = sorted(manifest["channels"])
    raise NotImplementedError(
        f"SM ML activation manifest at '{ACTIVATION_MANIFEST}' validated "
        f"successfully for channel(s) {channels}, but no ONNX inference "
        f"producer wiring exists yet for the SM profile (Phase 1 of this "
        f"friend is validation-only; see sm_ml.py's module docstring). "
        f"Implement the SM ML producer chain before calling build_config "
        f"with a populated manifest."
    )
