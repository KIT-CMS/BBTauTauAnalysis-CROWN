"""Shared body of the friend-tree configurations (FastMTT, kinematic fit)."""
from __future__ import annotations
from typing import List, Union

from code_generation.friend_trees import FriendTreeConfiguration

FRIEND_SCOPES = ["mt", "et", "tt"]


def build_friend_config(
    producers: list,
    outputs: list,
    era: str,
    sample: str,
    scopes: List[str],
    shifts: List[str],
    available_sample_types: List[str],
    available_eras: List[str],
    available_scopes: List[str],
    quantities_map: Union[str, None] = None,
):
    configuration = FriendTreeConfiguration(
        era,
        sample,
        scopes,
        shifts,
        available_sample_types,
        available_eras,
        available_scopes,
        quantities_map,
    )
    configuration.add_producers(FRIEND_SCOPES, producers)
    configuration.add_outputs(FRIEND_SCOPES, outputs)

    configuration.optimize()
    configuration.validate()
    configuration.report()
    return configuration.expanded_configuration()
