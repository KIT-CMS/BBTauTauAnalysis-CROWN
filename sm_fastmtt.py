"""SM FastMTT friend-tree entry point (thin; body lives in fastmtt_common).

The friend build surface for the SM profile is currently 2018-only (no
friends of the efficiency profile are needed for other eras). This is
enforced by two independent gates, mirroring the pattern used for the main
SM config (see `sm_config.py` / `common_config.build_config`):

  1. `AVAILABLE_ERAS` below is read by `generate_friends.py` BEFORE
     `build_config` is ever invoked.
  2. The explicit check at the top of `build_config` here, so that calling
     this module's `build_config` directly (bypassing `generate_friends.py`)
     is equally protected. It fires before `quantities_map` is touched.
"""
from typing import List, Union

from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from . import fastmtt_common

AVAILABLE_ERAS = ["2018"]


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
            f"Config 'sm_fastmtt' does not support era '{era}' "
            f"(supported: {AVAILABLE_ERAS})."
        )
    return fastmtt_common.build_fastmtt_config(
        era,
        sample,
        scopes,
        shifts,
        available_sample_types,
        available_eras,
        available_scopes,
        quantities_map,
    )
