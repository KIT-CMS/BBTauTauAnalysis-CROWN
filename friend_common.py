"""Shared bodies of the friend-tree configurations (FastMTT, kinematic fit, fake factors)."""
from __future__ import annotations
import os
from typing import List, Union

from code_generation.friend_trees import FriendTreeConfiguration
from code_generation.systematics import SystematicShift

from . import ff_payloads
from .producers import fakefactors

FRIEND_SCOPES = ["mt", "et", "tt"]
ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))


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
    return _finish(configuration)


def build_fake_factor_friend(
    payload_dir: str,
    era: str,
    sample: str,
    scopes: List[str],
    shifts: List[str],
    available_sample_types: List[str],
    available_eras: List[str],
    available_scopes: List[str],
    quantities_map: Union[str, None] = None,
):
    """Fake-factor friend whose inputs and shifts are read from the payloads.

    ``payload_dir`` is relative to the analysis directory, where the payloads
    are read now and from where they are installed next to the executable.
    A friend has a single scope; only that scope's two payload files are read.
    """
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
    (scope,) = scopes
    legs = ff_payloads.read_legs(os.path.join(ANALYSIS_DIR, payload_dir), scope)
    files = ff_payloads.payload_files(payload_dir, scope)
    configuration.add_config_parameters(
        [scope],
        {"ff_file": files["fake_factors"], "ff_corr_file": files["FF_corrections"]},
    )
    for leg in legs:
        producers = fakefactors.fake_factor_producers(scope, leg)
        configuration.add_config_parameters([scope], fakefactors.leg_parameters(leg))
        configuration.add_producers(
            [scope], [*producers.inputs, producers.raw, producers.corrected]
        )
        configuration.add_outputs(
            [scope], [*producers.raw.output, *producers.corrected.output]
        )
        _add_fake_factor_shifts(configuration, scope, leg, producers)
    return _finish(configuration)


def _add_fake_factor_shifts(configuration, scope, leg, producers) -> None:
    """One shift per selected syst key; corrections do not act on the raw fake factor."""
    for correction in leg.corrections:
        if correction.role in fakefactors.RAW_ROLES:
            targets = [producers.raw, producers.corrected]
        else:
            targets = [producers.corrected]
        parameter = fakefactors.variation_parameter(leg, correction)
        for key in correction.shift_keys:
            configuration.add_shift(
                SystematicShift(
                    name=ff_payloads.shift_name(key),
                    shift_config={(scope,): {parameter: key}},
                    producers={(scope,): targets},
                )
            )


def _finish(configuration: FriendTreeConfiguration):
    configuration.optimize()
    configuration.validate()
    configuration.report()
    return configuration.expanded_configuration()
