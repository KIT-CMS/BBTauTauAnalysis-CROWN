"""The columns the SM shift production adds to the n-tuples (v8 spec C23-C27, C40).

One block per item: the columns, the scopes and sample types that carry them, and the
parameters and producers behind them. That the additions change no column that was there is
the subject of test_nominal_freeze.py (the generated calls and columns of every surface), how
the shifts reach the new columns that of test_shift_inventory.py, and the C++ behind them is
exercised in test_cpp_runtime.py.
"""

import pytest

from analysis_configurations.bbtautau.analysis_profiles import (
    NMSSM_PROFILE,
    SM_BTAG_EFFICIENCY_PROFILE,
    SM_PROFILE,
    SM_TAU_ID_MEASUREMENT_PROFILE,
)
from analysis_configurations.bbtautau.constants import ERAS_RUN2, SCOPES
from analysis_configurations.bbtautau.producers import jets
from analysis_configurations.bbtautau.quantities import output as q
from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    generate_code,
    generated_calls,
    output_names,
    producer_names,
)

ALL_SCOPES = tuple(SCOPES)
TAU_SCOPES = ("et", "mt", "tt")
LIGHT_SCOPES = ("em", "ee", "mm")
TAU_LEGS = {"et": (2,), "mt": (2,), "tt": (1, 2)}
SLOTS = range(1, 9)
# sample types by what they carry: simulation, the signal among it, and the rest
SIMULATED = ("ttbar", "dyjets", "diboson", "hh2b2tau")
NOT_SIMULATED = ("data", "embedding")


def scopes_of(sample):
    return TAU_SCOPES if sample == "embedding" else ALL_SCOPES


def sm_config(sample, era, shifts=("none",)):
    return build("sm_config", sample, era=era, scopes=scopes_of(sample), shifts=shifts)


def shifts_of(config, scope):
    return {name.removeprefix("__"): change for name, change in config.shifts.get(scope, {}).items()}


# --- C23: parton shower ---------------------------------------------------------

PS_SHIFTS = {
    "ps_isrUp": {"ps_isr_variation": 2.0},
    "ps_isrDown": {"ps_isr_variation": 0.5},
    "ps_fsrUp": {"ps_fsr_variation": 2.0},
    "ps_fsrDown": {"ps_fsr_variation": 0.5},
}


@pytest.mark.parametrize("sample", SIMULATED)
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_parton_shower_weight_and_shifts_of_simulated_samples(era, sample):
    """ps_weight in every scope, 1 in the nominal, and the four shifts with the factor of the
    ISR or of the FSR scale: Up is the scale times 2, Down the scale times 0.5."""
    config = sm_config(sample, era, shifts=("ps_isr", "ps_fsr"))
    nominal = config.config_parameters["global"]["nominal"]
    assert (nominal["ps_isr_variation"], nominal["ps_fsr_variation"]) == (1.0, 1.0)
    assert nominal["ps_weight_sizes"] == "4"
    assert {"PSWeightChecked", "PartonShowerWeight"} <= producer_names(config, "global")
    weight = find_producer(config, "global", "PartonShowerWeight")
    # the weight reads the checked copy, so that a file with another length stops the job
    assert [quantity.name for quantity in weight.input["global"]] == ["PSWeight_checked"]
    assert [quantity.name for quantity in find_producer(config, "global", "PSWeightChecked").input["global"]] == ["PSWeight"]
    for scope in ("global", *ALL_SCOPES):
        assert shifts_of(config, scope) == PS_SHIFTS, scope
    for scope in ALL_SCOPES:
        assert "ps_weight" in output_names(config, scope)
        assert set(q.ps_weight.get_shifts(scope)) == {f"__{name}" for name in PS_SHIFTS}, scope


def test_parton_shower_shifts_evaluate_the_weight_at_their_scale_factor():
    """In the generated code the shifted weights call the core function with (ISR, FSR) =
    (2, 1), (0.5, 1), (1, 2), (1, 0.5): PSWeight[0], [2], [1], [3]
    (tests/cpp/test_theory_weights.cxx pins the index of each)."""
    generated = generate_code("sm_config", "ttbar", era="2018", scopes=("mt",), shifts=("ps_isr", "ps_fsr"))
    calls = [call for call in generated_calls(generated)["global"] if "PartonShower" in call]
    arguments = {"": "1.0, 1.0", "__ps_isrUp": "2.0, 1.0", "__ps_isrDown": "0.5, 1.0",
                 "__ps_fsrUp": "1.0, 2.0", "__ps_fsrDown": "1.0, 0.5"}
    assert sorted(calls) == sorted(
        f'event::reweighting::PartonShower(df, "ps_weight{suffix}", "PSWeight_checked", {values})'
        for suffix, values in arguments.items()
    )
    # one check of the length serves the nominal and every shift
    checks = [call for call in generated_calls(generated)["global"] if "CheckedSize" in call]
    assert checks == ['xyh::theory_weights::CheckedSize(df, "PSWeight_checked", "PSWeight", {4})']
    assert {name for name in generated.outputs["mt"] if "__" in name} == {
        f"ps_weight__{name}" for name in PS_SHIFTS
    }


@pytest.mark.parametrize("sample", NOT_SIMULATED)
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_data_and_embedding_have_no_parton_shower_weight(era, sample):
    config = sm_config(sample, era, shifts=("all",))
    assert not {"PSWeightChecked", "PartonShowerWeight"} & producer_names(config, "global")
    for scope in scopes_of(sample):
        assert "ps_weight" not in output_names(config, scope)
        assert not [name for name in shifts_of(config, scope) if name.startswith("ps_")]


@pytest.mark.parametrize(
    "module,sample,era,scopes",
    [
        ("nmssm_config", "ttbar", "2024", ("mt",)),
        ("sm_tau_id_measurement_config", "dyjets", "2018", ("mt", "mm")),
        ("sm_btag_efficiency_config", "ttbar", "2018", ("mt",)),
    ],
)
def test_the_other_configurations_have_no_parton_shower_shifts(module, sample, era, scopes):
    config = build(module, sample, era=era, scopes=scopes, shifts=("all",))
    for scope in scopes:
        assert "ps_weight" not in output_names(config, scope)
        assert not [name for name in shifts_of(config, scope) if name.startswith("ps_")]


