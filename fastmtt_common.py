"""Shared FastMTT friend-tree builder.

Both `nmssm_fastmtt.py` and `sm_fastmtt.py` are thin entry points that
delegate to `build_fastmtt_config` below -- the body is a verbatim move of
what used to live directly in `nmssm_fastmtt.py`. Keeping it here means the
FastMTT producer/output wiring only has to be maintained in one place.
"""
from __future__ import annotations  # needed for type annotations in > python 3.7
from typing import List, Union
from .producers import pairquantities as pairquantities
from .quantities import output as q
from code_generation.friend_trees import FriendTreeConfiguration


def build_fastmtt_config(
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

    configuration.add_producers(
        ["mt", "et", "tt"],
        [
            pairquantities.FastMTTQuantities,
        ],
    )

    configuration.add_outputs(
        ["mt", "et", "tt"],
        [
            q.m_fastmtt,
            q.pt_fastmtt,
            q.eta_fastmtt,
            q.phi_fastmtt,
        ],
    )

    #########################
    # Finalize and validate the configuration
    #########################
    configuration.optimize()
    configuration.validate()
    configuration.report()
    return configuration.expanded_configuration()
