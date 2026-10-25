"""Shared bodies of the friend-tree configurations (FastMTT, kinematic fit, fake factors, NN classifier)."""
from __future__ import annotations
import os
from typing import List, Sequence, Tuple, Union

from code_generation.friend_trees import FriendTreeConfiguration
from code_generation.systematics import SystematicShift

from . import ff_payloads, nn_gate, nn_payloads
from .producers import fakefactors, sm_nn

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
    processes: Union[Tuple[str, ...], None] = None,
):
    """Fake-factor friend whose inputs and shifts are read from the payloads.

    ``payload_dir`` is relative to the analysis directory, where the payloads
    are read now and from where they are installed next to the executable.
    A friend has a single scope; only that scope's two payload files are read.
    With ``processes``, every leg of the payload must sum exactly these processes
    (in ``ff_payloads.PROCESS_ORDER``), so that the friend of one variant cannot
    be built from the payload of the other.
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
    for leg in legs:
        if processes is not None and tuple(leg.processes) != tuple(processes):
            raise ValueError(
                f"Fake-factor payload {payload_dir} sums {list(leg.processes)} in the "
                f"{leg.name} leg of {scope}, this friend expects {list(processes)}."
            )
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


def build_nn_classifier_friend(
    models: Sequence[nn_payloads.NNModel],
    era: str,
    sample: str,
    scopes: List[str],
    shifts: List[str],
    available_sample_types: List[str],
    available_eras: List[str],
    available_scopes: List[str],
    quantities_map: Union[str, None] = None,
):
    """NN classifier friend (nn spec 3.4): the scores of every model of ``models`` inside the gate.

    The manifest of every model for the era and the scope is read and checked now (``nn_payloads``); its inputs
    are columns of the main n-tuple or of the friends in the quantities maps (the FastMTT friend for
    ``m/pt/eta/phi_fastmtt``), whose absence fails the configuration. Every model writes its columns with its own
    prefix; outside the gate (``nn_gate``) every column is -1.
    """
    (scope,) = scopes
    if scope not in FRIEND_SCOPES:
        raise ValueError(f"The NN classifier friend runs in {FRIEND_SCOPES}, not in {scope}.")
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
    if not models:
        raise ValueError("The NN classifier friend has no model: list the models of the production in MODELS.")
    prefixes = [model.prefix for model in models]
    for prefix in prefixes:
        if not prefix.endswith("_") or not prefix[:-1].isidentifier() or prefixes.count(prefix) > 1:
            raise ValueError(f"NN classifier column prefixes {prefixes}: each must be unique, a name ending in '_'.")
    expression, columns = nn_gate.cpp_expression(nn_gate.skim_cuts(scope, era))
    configuration.add_config_parameters([scope], {"nn_gate_expression": expression})
    producers, outputs = [sm_nn.gate_producer(scope, columns)], []
    for model in models:
        payload = nn_payloads.read_payload(ANALYSIS_DIR, model.payload, era, scope)
        classifier = sm_nn.classifier_producers(scope, model.prefix, payload)
        configuration.add_config_parameters([scope], sm_nn.classifier_parameters(model.prefix, payload))
        producers += [classifier.inputs, classifier.scores, classifier.outputs]
        outputs += classifier.outputs.output
    configuration.add_producers([scope], producers)
    configuration.add_outputs([scope], outputs)
    return _finish(configuration)


def _finish(configuration: FriendTreeConfiguration):
    configuration.optimize()
    configuration.validate()
    configuration.report()
    return configuration.expanded_configuration()
