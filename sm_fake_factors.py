"""SM HH fake-factor friend-tree entry point (2018)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .friend_common import build_fake_factor_friend

# Payload directory per era, relative to the analysis directory.
SM_PAYLOAD_DIRS = {"2018": "payloads/fake_factors/sm/fake-factors-2026-10-03/2018"}
AVAILABLE_ERAS = list(SM_PAYLOAD_DIRS)


def build_config(era, *args, **kwargs):
    return build_fake_factor_friend(SM_PAYLOAD_DIRS[era], era, *args, **kwargs)
