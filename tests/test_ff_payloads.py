"""Fake-factor payload reading: inputs, shift selection and the convention checks.

The real payloads pin what the friend reads (input orders, shift counts); small
edits of the SM mt payload, written to a temporary directory, exercise every
configuration-time error.
"""
import copy
import functools
import gzip
import json
from pathlib import Path

import pytest

from analysis_configurations.bbtautau import ff_payloads, sm_fake_factors
from analysis_configurations.bbtautau.producers import fakefactors

ANALYSIS = Path(__file__).resolve().parents[1]
PAYLOADS = ANALYSIS / "payloads" / "fake_factors"
SM_2018 = ANALYSIS / sm_fake_factors.SM_PAYLOAD_DIRS["2018"]  # the production payload
SM_2018_COMMISSIONING = PAYLOADS / "sm" / "fake-factors-2026-09-22" / "2018"  # base of the edited payloads
NMSSM_2023 = PAYLOADS / "fake-factors-2026-06-10" / "2023postBPix"
NMSSM_2025 = PAYLOADS / "fake-factors-2026-09-26" / "2025"
LEGS = [("et", "lt"), ("mt", "lt"), ("tt", "leading"), ("tt", "subleading")]


def legs(payload_dir, scope):
    return {leg.name: leg for leg in ff_payloads.read_legs(str(payload_dir), scope)}


def corrections(payload_dir, scope, leg):
    return {c.role: c for c in legs(payload_dir, scope)[leg].corrections}


def all_shift_keys(leg):
    return [key for c in leg.corrections for key in c.shift_keys]


@functools.lru_cache(maxsize=None)
def _load(path):
    with gzip.open(path, "rt") as handle:
        return json.load(handle)


def payload_inputs(scope, name):
    """Inputs of correction ``name`` straight from the SM payload JSON."""
    for kind in ("fake_factors", "FF_corrections"):
        payload = _load(SM_2018 / f"{kind}_{scope}.json.gz")
        for c in payload["corrections"] + (payload.get("compound_corrections") or []):
            if c["name"] == name:
                names = [i["name"] for i in c["inputs"]]
                return tuple(n for n in names if n not in ("process", "syst"))
    raise AssertionError(name)


# --- 1. inputs ------------------------------------------------------------------


@pytest.mark.parametrize("scope,leg", LEGS)
def test_sm_inputs_follow_payload_order(scope, leg):
    description = legs(SM_2018, scope)[leg]
    producers = fakefactors.fake_factor_producers(scope, description)
    for correction, producer in zip(description.corrections, producers.inputs):
        assert correction.inputs == payload_inputs(scope, correction.name)
        assert tuple(q.name for q in producer.input[scope]) == correction.inputs


@pytest.mark.parametrize(
    "scope,leg,closure",
    [
        ("mt", "lt", ("tau_decaymode_2", "pt_1", "jpt_1", "met", "mt_tot", "mass_2", "iso_1", "n_jets")),
        ("tt", "leading", ("tau_decaymode_1", "pt_2", "met", "mt_tot", "pt_vis", "mass_1", "mass_2", "n_jets")),
        ("tt", "subleading", ("tau_decaymode_2", "pt_1", "met", "mt_tot", "pt_vis", "mass_2", "mass_1", "n_jets")),
    ],
)
def test_sm_closure_input_orders(scope, leg, closure):
    by_role = corrections(SM_2018, scope, leg)
    assert by_role["closure_qcd"].inputs == closure
    assert by_role["closure_ttbar"].inputs == closure


def test_nmssm_inputs_are_aliased():
    assert corrections(NMSSM_2023, "mt", "lt")["fractions"].inputs == ("m_vis", "n_bjets")
    assert corrections(NMSSM_2023, "mt", "lt")["ff_qcd"].inputs == ("pt_2", "n_jets")


# --- 2. shift selection ---------------------------------------------------------


def test_sm_mt_shift_selection():
    keys = all_shift_keys(legs(SM_2018, "mt")["lt"])
    assert len(keys) == 34
    assert not [k for k in keys if "SystBandHigh" in k or "SystBandLow" in k]
    assert not [k for k in keys if "_non_closure_" in k and "_non_closure_Corr" not in k]
    assert not [k for k in keys if k.endswith("nominal")]
    assert "process_fractionsfrac_QCD_up" in keys  # the exact payload key


def test_sm_tt_legs_have_disjoint_shift_names():
    tt = legs(SM_2018, "tt")
    names = {
        leg: {ff_payloads.shift_name(k) for k in all_shift_keys(tt[leg])}
        for leg in ("leading", "subleading")
    }
    assert len(names["leading"]) == len(names["subleading"]) == 34
    assert not names["leading"] & names["subleading"]
    assert "QCD_subleadingStatShiftUp" in names["subleading"]


@pytest.mark.parametrize("payload_dir", [NMSSM_2023, NMSSM_2025], ids=["06-10", "09-26"])
def test_nmssm_shift_counts(payload_dir):
    for scope, leg in LEGS:
        assert len(all_shift_keys(legs(payload_dir, scope)[leg])) == 28


def test_nmssm_0610_fraction_keys_are_spelled_as_in_the_payload():
    keys = corrections(NMSSM_2023, "mt", "lt")["fractions"].shift_keys
    assert "process_fractionsfracTTbarUncUp" in keys


def test_shift_names_normalize_only_the_direction():
    assert ff_payloads.shift_name("process_fractionsfrac_QCD_up") == "process_fractionsfrac_QCDUp"
    assert ff_payloads.shift_name("process_fractionsfrac_QCD_down") == "process_fractionsfrac_QCDDown"
    assert ff_payloads.shift_name("QCDStatShiftUp") == "QCDStatShiftUp"


# --- 3. configuration-time errors -----------------------------------------------


@pytest.fixture
def sm_mt():
    """Editable copies of the two SM mt payloads, written by ``write`` to a directory."""
    return {
        kind: copy.deepcopy(_load(SM_2018_COMMISSIONING / f"{kind}_mt.json.gz"))
        for kind in ("fake_factors", "FF_corrections")
    }


def write(tmp_path, payloads):
    for kind, payload in payloads.items():
        with gzip.open(tmp_path / f"{kind}_mt.json.gz", "wt") as handle:
            json.dump(payload, handle)
    return str(tmp_path)


def correction(payloads, name):
    for kind in ("fake_factors", "FF_corrections"):
        for c in payloads[kind]["corrections"] + (payloads[kind].get("compound_corrections") or []):
            if c["name"] == name:
                return c
    raise AssertionError(name)


def rename_key(c, old, new):
    (item,) = [item for item in c["data"]["content"] if item["key"] == old]
    item["key"] = new


def drop_key(c, key):
    c["data"]["content"] = [item for item in c["data"]["content"] if item["key"] != key]


def test_missing_file_names_the_path(tmp_path):
    with pytest.raises(FileNotFoundError, match="fake_factors_mt.json.gz"):
        ff_payloads.read_legs(str(tmp_path), "mt")


def test_scope_without_legs_raises():
    with pytest.raises(ValueError, match="scope 'em'"):
        ff_payloads.read_legs(str(SM_2018), "em")


def test_missing_correction(tmp_path, sm_mt):
    correction(sm_mt, "QCD_DR_SR_correction")["name"] = "renamed"
    with pytest.raises(ValueError, match="QCD_DR_SR_correction.*FF_corrections_mt"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


def test_additional_fraction_process(tmp_path, sm_mt):
    fractions = correction(sm_mt, "process_fractions")
    (shifted,) = [
        item["value"]
        for item in fractions["data"]["content"]
        if item["key"] == "process_fractionsfrac_QCD_up"
    ]
    shifted["content"].append(dict(shifted["content"][0], key="Wjets"))
    with pytest.raises(ValueError, match="process_fractions.*Wjets"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


def test_syst_not_last(tmp_path, sm_mt):
    inputs = correction(sm_mt, "QCD_fake_factors")["inputs"]
    inputs.insert(0, inputs.pop())
    with pytest.raises(ValueError, match="QCD_fake_factors.*real ... \\+ syst"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


@pytest.mark.parametrize("dropped", ["QCDStatShiftDown", "QCDStatShiftUp"])
def test_unpaired_key(tmp_path, sm_mt, dropped):
    drop_key(correction(sm_mt, "QCD_fake_factors"), dropped)
    with pytest.raises(ValueError, match="QCD_fake_factors.*partner"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


def test_key_without_direction(tmp_path, sm_mt):
    rename_key(correction(sm_mt, "QCD_fake_factors"), "QCDStatShiftUp", "QCDStat")
    with pytest.raises(ValueError, match="QCD_fake_factors.*'QCDStat'"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


def test_missing_default(tmp_path, sm_mt):
    correction(sm_mt, "ttbar_fake_factors")["data"]["default"] = None
    with pytest.raises(ValueError, match="ttbar_fake_factors.*default"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


def test_syst_not_at_the_top(tmp_path, sm_mt):
    c = correction(sm_mt, "ttbar_fake_factors")
    c["data"] = c["data"]["default"]
    with pytest.raises(ValueError, match="ttbar_fake_factors.*top-level"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


def test_nominal_key_differs_from_default(tmp_path, sm_mt):
    c = correction(sm_mt, "QCD_DR_SR_correction")
    (nominal,) = [item for item in c["data"]["content"] if item["key"] == "nominal"]
    nominal["value"] = 1.0
    with pytest.raises(ValueError, match="QCD_DR_SR_correction.*'nominal' differs"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


def test_global_closure_key_missing_in_a_stack_member(tmp_path, sm_mt):
    c = correction(sm_mt, "QCD_non_closure_met_correction")
    drop_key(c, "QCD_non_closure_CorrStatShiftUp")
    drop_key(c, "QCD_non_closure_CorrStatShiftDown")
    with pytest.raises(ValueError, match="QCD_compound_correction.*QCD_non_closure_met_correction"):
        ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")


def test_input_that_is_no_quantity(tmp_path, sm_mt):
    correction(sm_mt, "QCD_fake_factors")["inputs"][0]["name"] = "no_such_column"
    (leg,) = ff_payloads.read_legs(write(tmp_path, sm_mt), "mt")
    with pytest.raises(ValueError, match="no_such_column.*QCD_fake_factors"):
        fakefactors.fake_factor_producers("mt", leg)


def test_duplicate_shift_name_across_tt_legs(tmp_path):
    payloads = {
        kind: copy.deepcopy(_load(SM_2018_COMMISSIONING / f"{kind}_tt.json.gz"))
        for kind in ("fake_factors", "FF_corrections")
    }
    subleading = correction(payloads, "QCD_subleading_fake_factors")
    for suffix in ("Up", "Down"):
        rename_key(subleading, f"QCD_subleadingStatShift{suffix}", f"QCDStatShift{suffix}")
    for kind, payload in payloads.items():
        with gzip.open(tmp_path / f"{kind}_tt.json.gz", "wt") as handle:
            json.dump(payload, handle)
    with pytest.raises(ValueError, match="QCDStatShift.*QCD_fake_factors.*QCD_subleading_fake_factors"):
        ff_payloads.read_legs(str(tmp_path), "tt")
