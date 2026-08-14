from dataclasses import dataclass
from typing import Any
from collections.abc import Sequence

from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import SystematicShift


@dataclass
class KeyValueShift:
    name: str
    key: str
    value: Any


def _get_producer_scopes(
    producers: list[Producer | ProducerGroup] | Producer | ProducerGroup
) -> set[str]:
    """
    Get the scopes from a list of producers or a single producer.
    """
    if isinstance(producers, (Producer, ProducerGroup)):
        # If the input is a single object, return its scopes as a sorted tuple
        return tuple(sorted(producers.scopes))

    elif isinstance(producers, Sequence):
        # If multiple producers are provided, check for consistency in their
        # scopes first
        scopes = set()
        for producer in producers:
            scopes.add(tuple(sorted(producer.scopes)))

        if len(scopes) > 1:
            raise ValueError(
                "Inconsistent scopes found in the provided producers. "
                "All producers must have the same scopes."
            )

        return scopes.pop()

    else:
        raise TypeError(
            "Input must be a Producer, ProducerGroup, or a list of these."
        )


def add_systematic_shift(
    configuration: Configuration,
    shift: KeyValueShift,
    producers: list[Producer | ProducerGroup] | Producer | ProducerGroup,
    scopes: Sequence[str] = None,
    shift_kwargs: dict[str, Any] = None,
    add_kwargs: dict[str, Any] = None,
):
    # If scopes are not provided, get them from the producers
    scopes = (
        tuple(scopes)
        if scopes is not None
        else _get_producer_scopes(producers)
    )

    # Convert producers to a list if it's a single Producer or ProducerGroup
    if isinstance(producers, (Producer, ProducerGroup)):
        producers = [producers]

    # Get the shift key and value template
    shift_key = shift.key
    shift_value = shift.value

    for direction in ["up", "down"]:
        # Replace {direction} placeholder if it is present in shift_key or
        # shift_value
        if "{direction}" in shift_key:
            shift_key = shift_key.format(direction=direction)
        if "{direction}" in shift_value:
            shift_value = shift_value.format(direction=direction)

        # Add shift for the given direction to the configuration
        name = f"{shift.name}{direction.capitalize()}"
        configuration.add_shift(
            SystematicShift(
                name=name,
                shift_config={scopes: {shift_key: shift_value}},
                producers={scopes: producers},
                **(shift_kwargs if shift_kwargs is not None else {})
            ),
            **(add_kwargs if add_kwargs is not None else {})
        )
