"""SM FastMTT friend-tree entry point: the NMSSM friend on the SM ntuples (2018 only)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .nmssm_fastmtt import build_config  # noqa: F401

AVAILABLE_ERAS = ["2018"]
