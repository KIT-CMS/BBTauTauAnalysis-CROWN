"""Shared build helper, fake CLI args and configuration accessors for the suite.

Not a test module. ``build()`` mirrors ``generate.py`` -- gate on the module's
``AVAILABLE_ERAS``, but always construct against ``LEGACY_AVAILABLE_SAMPLES`` --
and caches, so each (module, sample, era, scopes, shifts) surface is built once
per session. The accessors keep the producer-group traversal in one place.
"""
import functools
import importlib
import logging

from analysis_configurations.bbtautau.constants import ERAS, LEGACY_AVAILABLE_SAMPLES, SCOPES


@functools.lru_cache(maxsize=None)
def build(module_name, sample, era="2018", scopes=("mt",), shifts=("none",)):
    """Build ``module_name``'s configuration; cached, and quiet about logging."""
    module = importlib.import_module(f"analysis_configurations.bbtautau.{module_name}")
    logging.disable(logging.CRITICAL)
    try:
        return module.build_config(
            era, sample, list(scopes), {s.lower() for s in shifts},
            LEGACY_AVAILABLE_SAMPLES,
            list(getattr(module, "AVAILABLE_ERAS", ERAS)), SCOPES,
        )
    finally:
        logging.disable(logging.NOTSET)


class FakeArgs:
    """Attributes ``generate.run``/``generate_friends.run`` read before their gates."""

    def __init__(self, config, era, sample="ttbar"):
        self.config, self.era, self.sample = config, era, sample
        self.scopes, self.shifts = ["mt"], ["none"]
        self.quantities_map = None
        self.logger = logging.getLogger(__name__)


def producer_names(config, scope):
    """Top-level producer names in ``scope``."""
    return {p.name for p in config.producers[scope]}


def output_names(config, scope):
    return {q.get_leaf(shift="", scope=scope) for q in config.outputs[scope]}


def find_producer(config, scope, name):
    """The producer called ``name`` in ``scope``, searching through groups.

    Several producers only exist as members of a ``ProducerGroup`` (e.g. the jet
    ID inside ``AuxJetCollectionQuantities``), which exposes its members as a
    scope -> list mapping in ``.producers``.
    """

    def walk(producer):
        if producer.name == name:
            return producer
        members = getattr(producer, "producers", None)
        if isinstance(members, dict):
            members = [p for group in members.values() for p in group]
        for member in members or []:
            found = walk(member)
            if found is not None:
                return found
        return None

    for producer in config.producers[scope]:
        found = walk(producer)
        if found is not None:
            return found
    raise AssertionError(f"no producer {name!r} in scope {scope!r}")
