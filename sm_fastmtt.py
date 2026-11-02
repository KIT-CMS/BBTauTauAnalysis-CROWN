"""SM FastMTT friend-tree entry point: the NMSSM friend on the SM ntuples (Run-2 v15 eras)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .constants import ERAS_RUN2
from .nmssm_fastmtt import build_config  # noqa: F401

AVAILABLE_ERAS = list(ERAS_RUN2)
