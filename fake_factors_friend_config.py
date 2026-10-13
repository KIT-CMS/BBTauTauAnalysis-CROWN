"""NMSSM fake-factor friend-tree entry point (Run 3)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .friend_common import build_fake_factor_friend

# Payload directory per era, relative to the analysis directory.
NMSSM_PAYLOAD_DIRS = {
    **{
        era: f"payloads/fake_factors/fake-factors-2026-06-10/{era}"
        for era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
    },
    # no tt payload for 2024
    **{
        era: f"payloads/fake_factors/fake-factors-2026-09-26/{era}"
        for era in ["2024", "2025"]
    },
}
AVAILABLE_ERAS = list(NMSSM_PAYLOAD_DIRS)


def build_config(era, *args, **kwargs):
    return build_fake_factor_friend(NMSSM_PAYLOAD_DIRS[era], era, *args, **kwargs)
