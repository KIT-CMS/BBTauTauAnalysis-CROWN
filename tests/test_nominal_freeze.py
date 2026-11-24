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


MUON_PT_SCALE = (
    'xyh::energy_scale::ScalePt( df, "Muon_pt_scaled", "Muon_pt_corrected", "Muon_eta", '
    "{0.0, 1.2, 2.1}, {1.0, 1.0, 1.0} )"
)


def muon_pt_through_the_scope_level_scale(module, sample, era, scope, calls, outputs):
    """v8 spec C37: in mt and em of sm_config, simulated and embedded events read the muon pT
    through MuonPtScale, whose nominal factors of 1 pass the corrected pT on unchanged
    (tests/cpp/test_energy_scale.cxx). The selection, the pair selection and the four-vector
    of the muon read the scaled pT; the calls stay the same otherwise."""
    if module == "sm_config" and sample != "data" and scope in ("mt", "em"):
        readers = [call for call in calls if '"Muon_pt_corrected"' in call]
        assert len(readers) == 3, readers
        calls = [call.replace('"Muon_pt_corrected"', '"Muon_pt_scaled"') for call in calls]
        calls = calls + [MUON_PT_SCALE]
    return calls, outputs


ELECTRON_PT_SCALE = (
    'xyh::energy_scale::ScalePt( df, "Electron_pt_scaled", "Electron_pt_corrected", '
    '"Electron_eta", {0.0, 1.479}, {1.0, 1.0} )'
)


def embedded_electron_pt_through_the_scope_level_scale(module, sample, era, scope, calls, outputs):
    """v8 spec C32: in et of the sm_config embedding the electron pT is read through
    ElectronPtScale, whose nominal factors of 1 pass the corrected pT on unchanged. The
    selection, the pair selection and the four-vector of the electron read the scaled pT, the
    uncorrected four-vector of the MET propagation the unscaled one."""
    if module == "sm_config" and sample == "embedding" and scope == "et":
        readers = [call for call in calls if '"Electron_pt_corrected"' in call]
        assert len(readers) == 4, readers
        calls = [
            call
            if '"p4_1_uncorrected"' in call
            else call.replace('"Electron_pt_corrected"', '"Electron_pt_scaled"')
            for call in calls
        ]
        calls = calls + [ELECTRON_PT_SCALE]
    return calls, outputs


def ditau_trigger_sf_from_the_addon(module, sample, era, scope, calls, outputs):
    """v8 spec C39: the di-tau trigger SFs of sm_config come from the addon function with
    variations per decay mode, whose "nom" is the correction the core function evaluates
    (tests/cpp/test_tau_trigger_sf.cxx); the arguments of the calls stay the same."""
    core, addon = (
        "physicsobject::tau::scalefactor::Trigger(",
        "xyh::scalefactor::tau_trigger_per_decay_mode(",
    )
    # data has no trigger SF; the embedding reads the data efficiency of the di-tau leg with
    # the core function, which stays
    if module == "sm_config" and scope == "tt" and sample not in ("data", "embedding"):
        readers = [call for call in calls if call.startswith(core)]
        # both legs of every di-tau flag of the era
        assert readers and len(readers) % 2 == 0, readers
        assert all('"trg_wgtdouble_tau' in call and '"sf"' in call for call in readers), readers
        calls = [addon + call[len(core):] if call.startswith(core) else call for call in calls]
    return calls, outputs


# --- The columns of the shift production (v8 spec C23-C27, C40): calls and columns that are
# added, in sm_config only. No frozen call changes, so every column that was there keeps
# its value.

TAU_SCOPES = ("et", "mt", "tt")
JET_SLOTS = range(1, 9)
# the legs of a scope that are hadronic taus
TAU_LEGS = {"et": (2,), "mt": (2,), "tt": (1, 2)}


def is_simulation(sample):
    return sample not in ("data", "embedding")


def parton_shower_weight(module, sample, era, scope, calls, outputs):
    """v8 spec C23: simulated samples of sm_config compute ps_weight from PSWeight, read
    through a column that checks its length; 1 in the nominal."""
    if module == "sm_config" and is_simulation(sample):
        if scope == "global":
            calls = calls + [
                'xyh::theory_weights::CheckedSize(df, "PSWeight_checked", "PSWeight", {4})',
                'event::reweighting::PartonShower(df, "ps_weight", "PSWeight_checked", 1.0, 1.0)',
            ]
        else:
            outputs = outputs + ["ps_weight"]
    return calls, outputs


def pdf_weights_of_the_signal(module, sample, era, scope, calls, outputs):
    """v8 spec C24: the signal of sm_config writes the weights of the 100 PDF eigenvectors,
    lhe_pdf_weight_<i> = LHEPdfWeight[i]; no other sample has a PDF column."""
    if module == "sm_config" and sample == "hh2b2tau":
        if scope == "global":
            calls = calls + [
                'xyh::theory_weights::CheckedSize(df, "LHEPdfWeight_checked", "LHEPdfWeight", {101, 103})'
            ] + [
                f'event::quantity::Get<float>(df, "lhe_pdf_weight_{member}", "LHEPdfWeight_checked", {member})'
                for member in range(1, 101)
            ]
        else:
            outputs = outputs + [f"lhe_pdf_weight_{member}" for member in range(1, 101)]
    return calls, outputs


# Changes of the nominal surface since the frozen commit: functions
# (module, sample, era, scope, calls, outputs) -> (calls, outputs) applied in this order to the
# frozen calls and output columns of a scope. None of them may change the value of a column
# that stays.
EXPECTED_CHANGES = [
    diboson_gets_the_qcd_scale_weight,
    no_regressed_jets,
    muon_pt_through_the_scope_level_scale,
    embedded_electron_pt_through_the_scope_level_scale,
    ditau_trigger_sf_from_the_addon,
    parton_shower_weight,
    pdf_weights_of_the_signal,
]
# the changes that only add calls and columns: every frozen call and column is still there
ADDITIONS = EXPECTED_CHANGES[5:]

# The columns sm_config writes that the v7b n-tuples lack: the MET before the lepton and the
# recoil corrections, written since the n-tuples were produced (v8 spec 3.1); the columns of
# the shift production are added per scope by the ADDITIONS
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
        kept = (set(shifts[""]) - COLUMNS_REMOVED_SINCE_V7B) | COLUMNS_SINCE_V7B
        expected = list(kept)
        for addition in ADDITIONS:
            _, expected = addition("sm_config", "ttbar", era, scope, [], expected)
        # every column of the v7b n-tuples that is kept is written, and nothing but the
        # listed additions comes on top
        assert kept <= generated.outputs[scope], (scope, sorted(kept - generated.outputs[scope]))
        assert len(expected) == len(set(expected)), scope
        assert generated.outputs[scope] == set(expected), (
            scope,
            sorted(generated.outputs[scope] ^ set(expected)),
        )


@pytest.mark.parametrize("key", sorted(key for key in FROZEN["surfaces"] if key.startswith("sm_config/")))
def test_the_columns_of_the_shift_production_only_add_to_the_frozen_surface(key):
    """The additions of the shift production (C23-C27, C40) leave every frozen call and
    column in place: the surface before them is a subset of the generated one."""
    module, sample, era = key.split("/")
    frozen = frozen_surface(key)
    scopes = tuple(scope for scope in frozen["calls"] if scope != "global")
    generated = generate_code(module, sample, era=era, scopes=scopes)
    calls = generated_calls(generated)
    for scope in frozen["calls"]:
        before_calls = list(frozen["calls"][scope])
        before_outputs = list(frozen["outputs"].get(scope, []))
        for change in EXPECTED_CHANGES:
            if change not in ADDITIONS:
                before_calls, before_outputs = change(module, sample, era, scope, before_calls, before_outputs)
        assert set(before_calls) <= set(calls[scope]), scope
        assert set(before_outputs) <= generated.outputs.get(scope, set()), scope
