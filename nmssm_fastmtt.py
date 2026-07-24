"""NMSSM FastMTT friend-tree entry point (thin; body lives in fastmtt_common).

Executable names/outputs are unchanged: the executable name derives from
this module's name (`nmssm_fastmtt`), and the four outputs
(`m/pt/eta/phi_fastmtt`) come from the shared builder below.
"""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from . import fastmtt_common

build_config = fastmtt_common.build_fastmtt_config
