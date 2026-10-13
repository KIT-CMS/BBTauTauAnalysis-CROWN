"""Fake-factor producers of one leg, built from its payload description.

``ff_payloads`` reads the corrections of a leg (inputs in payload order, syst
keys); this module turns them into CROWN producers: one ``BuildFloatVector``
per correction, the raw fake factor (fractions and fake factors only) and the
corrected one (times DR->SR and closure corrections).
"""
from typing import Dict, List, NamedTuple

from code_generation.producer import Producer
from code_generation.quantity import Quantity

from ..ff_payloads import FakeFactorCorrection, FakeFactorLeg
from ..quantities import output as q

# Leg -> prefix of its config parameters and input-vector quantities.
LEG_PREFIXES = {"lt": "ff_", "leading": "ff_1_", "subleading": "ff_2_"}
# Leg -> (raw, corrected) fake-factor outputs.
LEG_OUTPUTS = {
    "lt": (q.fake_factor_raw, q.fake_factor),
    "leading": (q.fake_factor_1_raw, q.fake_factor_1),
    "subleading": (q.fake_factor_2_raw, q.fake_factor_2),
}


class _Wiring(NamedTuple):
    name: str  # parameter holding the correction name
    variation: str  # parameter holding the syst key
    input: str  # input-vector quantity


# Role (ff_payloads.ROLES) -> names without the leg prefix.
ROLE_WIRING = {
    "ff_qcd": _Wiring("qcd_name", "qcd_variation", "input_qcd"),
    "ff_ttbar": _Wiring("tt_name", "tt_variation", "input_tt"),
    "fractions": _Wiring("fraction_name", "fraction_variation", "input_fraction"),
    "dr_sr_qcd": _Wiring(
        "corr_dr_sr_qcd_name", "dr_sr_corr_qcd_variation", "corr_dr_sr_input_qcd"
    ),
    "closure_qcd": _Wiring(
        "corr_closure_qcd_name", "closure_corr_qcd_variation", "corr_closure_input_qcd"
    ),
    "closure_ttbar": _Wiring(
        "corr_closure_tt_name", "closure_corr_tt_variation", "corr_closure_input_tt"
    ),
}
# The roles of the raw fake factor; the others are corrections.
RAW_ROLES = ("ff_qcd", "ff_ttbar", "fractions")

BUILD_FLOAT_VECTOR_CALL = """
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """


class FakeFactorProducers(NamedTuple):
    inputs: List[Producer]
    raw: Producer
    corrected: Producer


def fake_factor_producers(scope: str, leg: FakeFactorLeg) -> FakeFactorProducers:
    """The input-vector, raw and corrected fake-factor producers of ``leg``."""
    raw = [c for c in leg.corrections if c.role in RAW_ROLES]
    corrections = [c for c in leg.corrections if c.role not in RAW_ROLES]

    def parameters(of, kind):
        return [_parameter(leg, c, kind) for c in of]

    raw_output, corrected_output = LEG_OUTPUTS[leg.name]
    return FakeFactorProducers(
        inputs=[
            Producer(
                name=f"FakeFactorInput_{leg.name}_{c.role}",
                call=BUILD_FLOAT_VECTOR_CALL,
                input=[_payload_input(name, c) for name in c.inputs],
                output=[_input_vector(leg, c)],
                scopes=[scope],
            )
            for c in leg.corrections
        ],
        raw=Producer(
            name=f"RawFakeFactor_{leg.name}",
            call=_call(
                "RawFakeFactorSemileptonic",
                ["ff_file", *parameters(raw, "name"), *parameters(raw, "variation")],
            ),
            input=[_input_vector(leg, c) for c in raw],
            output=[raw_output],
            scopes=[scope],
        ),
        corrected=Producer(
            name=f"FakeFactor_{leg.name}",
            call=_call(
                "FakeFactorSemileptonic",
                [
                    "ff_file",
                    *parameters(raw, "name"),
                    "ff_corr_file",
                    *parameters(corrections, "name"),
                    *parameters(raw, "variation"),
                    *parameters(corrections, "variation"),
                ],
            ),
            input=[_input_vector(leg, c) for c in leg.corrections],
            output=[corrected_output],
            scopes=[scope],
        ),
    )


def leg_parameters(leg: FakeFactorLeg) -> Dict[str, str]:
    """Correction names and the nominal variation of every correction of ``leg``."""
    parameters = {}
    for c in leg.corrections:
        parameters[_parameter(leg, c, "name")] = c.name
        parameters[_parameter(leg, c, "variation")] = "nominal"
    return parameters


def variation_parameter(leg: FakeFactorLeg, correction: FakeFactorCorrection) -> str:
    return _parameter(leg, correction, "variation")


def _parameter(leg: FakeFactorLeg, correction: FakeFactorCorrection, kind: str) -> str:
    return LEG_PREFIXES[leg.name] + getattr(ROLE_WIRING[correction.role], kind)


def _input_vector(leg: FakeFactorLeg, correction: FakeFactorCorrection) -> Quantity:
    return getattr(q, LEG_PREFIXES[leg.name] + ROLE_WIRING[correction.role].input)


def _payload_input(name: str, correction: FakeFactorCorrection) -> Quantity:
    """The quantity of ``quantities/output.py`` whose branch name is ``name``."""
    matches = {
        id(value): value
        for value in vars(q).values()
        if isinstance(value, Quantity) and value.name == name
    }
    if len(matches) != 1:
        raise ValueError(
            f"input '{name}' of correction '{correction.name}' in "
            f"'{correction.file}' matches {len(matches)} quantities in "
            "quantities/output.py, expected exactly one"
        )
    return next(iter(matches.values()))


def _call(function: str, parameters: List[str]) -> str:
    """C++ call of ``fakefactors::xyh::<function>`` with the quoted ``parameters``."""
    arguments = ",\n        ".join(f'"{{{parameter}}}"' for parameter in parameters)
    return f"""
    fakefactors::xyh::{function}(
        {{df}},
        correctionManager,
        {{output}},
        {{input}},
        {arguments}
    )
    """
