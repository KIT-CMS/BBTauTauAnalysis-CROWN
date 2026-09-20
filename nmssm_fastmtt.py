"""NMSSM FastMTT friend-tree entry point."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .friend_common import build_friend_config
from .producers import pairquantities
from .quantities import output as q


def build_config(*args, **kwargs):
    return build_friend_config(
        [pairquantities.FastMTTQuantities],
        [q.m_fastmtt, q.pt_fastmtt, q.eta_fastmtt, q.phi_fastmtt],
        *args,
        **kwargs,
    )
