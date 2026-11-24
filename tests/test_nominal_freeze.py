"""The nominal of the configurations is frozen (v8 spec V1, C30).

The NN models, the fake factors, the embedding tau ID/ES, the tt trigger efficiencies, the
b-tag efficiencies and the DY tables are measured on the v7b n-tuples, so a production with
shifts must reproduce every nominal column of v7b. Two comparisons guard that:

- the code generated without shifts against fixtures/nominal_calls.json.gz, the producer
  calls and output columns of each surface at the commit the shift production branched from
  (written by fixtures/make_nominal_calls_fixture.py). The generated calls carry every
  parameter a producer reads, so equal calls and equal C++ sources give equal columns. Every
  intended difference is spelled out in EXPECTED_CHANGES;
- the output columns of sm_config against the quantities maps of the v7b n-tuples
  (fixtures/nn_classifier_<era>_quantities_map.json: ttbar, et, mt and tt).
"""

import gzip
import json
import re

import pytest

from analysis_configurations.bbtautau.constants import ERAS_RUN2
from analysis_configurations.bbtautau.tests.helpers import (
    FIXTURES,
    generate_code,
    generated_calls,
)

FROZEN = json.load(gzip.open(FIXTURES / "nominal_calls.json.gz"))

LHE_SCALE_WEIGHT = 'event::reweighting::LHEscale(df, "lhe_scale_weight", "LHEScaleWeight", 1.0, 1.0)'


def diboson_gets_the_qcd_scale_weight(module, sample, era, scope, calls, outputs):
    """v8 spec C34: sm_config computes lhe_scale_weight for diboson as for every other MC."""
    if module == "sm_config" and sample == "diboson":
        if scope == "global":
            calls = calls + [LHE_SCALE_WEIGHT]
        else:
            outputs = outputs + ["lhe_scale_weight"]
    return calls, outputs


# The calibration of the jets with the UParT pT regression, the bb pair built from them and
# their columns: every call and column that names them
REGRESSED_JETS = re.compile("regress|RegPt", re.IGNORECASE)
REGRESSED_JET_COLUMNS = {
    *[
        f"bpair_{quantity}_regressed_{index}"
        for quantity in ("pt", "eta", "phi", "mass", "btag_value", "pt_resolution")
        for index in (1, 2)
    ],
    "bpair_m_inv_regressed",
    "bpair_deltaR_regressed",
    "bpair_pt_dijet_regressed",
    "jpt_regressed_1",
    "jpt_regressed_2",
    "jpt_regressed_resolution_1",
    "jpt_regressed_resolution_2",
}


def no_regressed_jets(module, sample, era, scope, calls, outputs):
    """v8 spec C36: sm_config drops the 19 columns of the regressed jets and their producers."""
    if module == "sm_config":
        removed = {output for output in outputs if REGRESSED_JETS.search(output)}
        assert removed == (REGRESSED_JET_COLUMNS if scope != "global" else set())
        calls = [call for call in calls if not REGRESSED_JETS.search(call)]
        outputs = [output for output in outputs if output not in removed]
    return calls, outputs


# Changes of the nominal surface since the frozen commit: functions
# (module, sample, era, scope, calls, outputs) -> (calls, outputs) applied in this order to the
# frozen calls and output columns of a scope. None of them may change the value of a column
# that stays.
EXPECTED_CHANGES = [
    diboson_gets_the_qcd_scale_weight,
    no_regressed_jets,
]

# The columns sm_config writes that the v7b n-tuples lack: the MET before the lepton and the
# recoil corrections, written since the n-tuples were produced (v8 spec 3.1)
COLUMNS_SINCE_V7B = {
    "met_jetcorrected",
    "metphi_jetcorrected",
    "met_leptoncorrected",
    "metphi_leptoncorrected",
}
# The columns of the v7b n-tuples sm_config no longer writes (v8 spec C36)
COLUMNS_REMOVED_SINCE_V7B = REGRESSED_JET_COLUMNS


def frozen_surface(key):
    """The frozen calls and output columns of a surface per scope."""
    surface = FROZEN["surfaces"][key]
    return {
        kind: {
            scope: [FROZEN[kind][index] for index in indices]
            for scope, indices in surface[kind].items()
        }
        for kind in ("calls", "outputs")
    }


@pytest.mark.parametrize("key", sorted(FROZEN["surfaces"]))
def test_nominal_calls_and_outputs_are_the_frozen_ones(key):
    module, sample, era = key.split("/")
    frozen = frozen_surface(key)
    scopes = tuple(scope for scope in frozen["calls"] if scope != "global")
    generated = generate_code(module, sample, era=era, scopes=scopes)
    calls = generated_calls(generated)
    assert set(calls) == set(frozen["calls"])
    for scope in frozen["calls"]:
        expected_calls = list(frozen["calls"][scope])
        expected_outputs = list(frozen["outputs"].get(scope, []))
        for change in EXPECTED_CHANGES:
            expected_calls, expected_outputs = change(
                module, sample, era, scope, expected_calls, expected_outputs
            )
        unexpected = sorted(set(calls[scope]) ^ set(expected_calls))
        assert not unexpected, (scope, unexpected[:10])
        assert calls[scope] == sorted(expected_calls), scope
        outputs = sorted(generated.outputs.get(scope, []))
        assert outputs == sorted(expected_outputs), (
            scope,
            sorted(set(outputs) ^ set(expected_outputs)),
        )


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_sm_config_writes_the_columns_of_the_v7b_ntuples(era):
    quantities_map = json.loads((FIXTURES / f"nn_classifier_{era}_quantities_map.json").read_text())
    assert quantities_map["metadata"]["config"] == "sm_config"
    v7b = quantities_map["quantities"][era]["ttbar"]
    generated = generate_code("sm_config", "ttbar", era=era, scopes=tuple(v7b))
    for scope, shifts in v7b.items():
        expected = (set(shifts[""]) - COLUMNS_REMOVED_SINCE_V7B) | COLUMNS_SINCE_V7B
        assert generated.outputs[scope] == expected, (
            scope,
            sorted(generated.outputs[scope] ^ expected),
        )
