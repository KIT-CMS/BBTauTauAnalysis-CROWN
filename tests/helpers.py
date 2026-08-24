"""Shared build helpers and configuration accessors for the test suite.

Not a test module. Every test file builds configurations through the three
``build_*`` helpers here and inspects them through the three accessors, so the
sample/era surfaces and the producer-group traversal exist in exactly one
place.
"""
from analysis_configurations.bbtautau import (
    nmssm_config,
    sm_btag_efficiency_config,
    sm_config,
)
from analysis_configurations.bbtautau.constants import (
    ERAS,
    LEGACY_AVAILABLE_SAMPLES,
    SCOPES,
)


def build_nmssm(sample, era="2018", scopes=("mt",), shifts=("none",)):
    return nmssm_config.build_config(
        era, sample, list(scopes), {s.lower() for s in shifts},
        LEGACY_AVAILABLE_SAMPLES, ERAS, SCOPES,
    )


def build_sm(sample, era="2018", scopes=("mt",), shifts=("none",)):
    return sm_config.build_config(
        era, sample, list(scopes), {s.lower() for s in shifts},
        sm_config.AVAILABLE_SAMPLES, [era], SCOPES,
    )


def build_sm_btag_eff(sample, era="2018", scopes=("mt",), available=None):
    return sm_btag_efficiency_config.build_config(
        era, sample, list(scopes), {"none"},
        list(available) if available is not None
        else list(sm_btag_efficiency_config.AVAILABLE_SAMPLES),
        [era], SCOPES,
    )


def producer_names(config, scope):
    """Top-level producer names in ``scope``."""
    return {p.name for p in config.producers[scope]}


def all_producer_names(config, scope):
    """Producer names in ``scope`` including every nested subproducer.

    Several producers are members of a producer group (e.g. the jet ID inside
    ``AuxJetCollectionQuantities``), so an assertion about whether a producer
    runs at all has to look through groups. A ``ProducerGroup`` exposes its
    members as ``.producers``, a scope -> list mapping.
    """
    names = set()

    def collect(producer):
        if producer.name in names:
            return
        names.add(producer.name)
        members = getattr(producer, "producers", None)
        if isinstance(members, dict):
            members = [p for group in members.values() for p in group]
        for member in members or []:
            collect(member)

    for producer in config.producers[scope]:
        collect(producer)
    return names


def output_names(config, scope):
    return {q.get_leaf(shift="", scope=scope) for q in config.outputs[scope]}
