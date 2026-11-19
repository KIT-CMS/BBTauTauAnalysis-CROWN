"""NMSSM fake-factor friend-tree entry point (Run 3)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .constants import ERAS_RUN3
from .friend_common import build_fake_factor_friend

# Payload directory per era, relative to the analysis directory.
NMSSM_PAYLOAD_DIRS = {
    era: f"payloads/fake_factors/fake-factors-2026-10-25/{era}" for era in ERAS_RUN3
}
AVAILABLE_ERAS = list(NMSSM_PAYLOAD_DIRS)


def build_config(era, *args, **kwargs):
    return build_fake_factor_friend(NMSSM_PAYLOAD_DIRS[era], era, *args, **kwargs)
