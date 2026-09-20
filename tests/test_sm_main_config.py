"""SM 2018-UL NanoAOD-v15 config contracts, and the NMSSM path they must not disturb.

Each assertion pins a value that would otherwise regress silently into wrong physics
or a broken grid job: the truth-gen mothers and LHE dispatch per sample, the pinned
UParTAK4 b-tag and v15 jet/electron wiring, the per-variation weight columns, the
DY/W recoil treatment, and the era/sample gates.
"""

import importlib
from unittest import mock

import pytest

from analysis_configurations.bbtautau import btag_payloads, generate
from analysis_configurations.bbtautau.constants import SCOPES
from analysis_configurations.bbtautau.tests.helpers import (
    FakeArgs,
    build,
    find_producer,
    output_names,
    producer_names,
)

ALL_SCOPES = tuple(SCOPES)
LHE_PRODUCERS = {"LHE_Scale_weight", "NMSSM_LHE_Scale_weight"}


# module, sample, bb mother pdgid, tautau mother pdgid, the only LHE producer that may
# be scheduled. A lost SampleModifier key falls back to -1 and yields garbage truth
# pairs, so the background default is pinned as well.
@pytest.mark.parametrize(
    "module,sample,bb,tautau,lhe",
    [
        ("sm_config", "hh2b2tau", 25, 25, "LHE_Scale_weight"),
        ("nmssm_config", "nmssm_Ybb", 35, 25, "NMSSM_LHE_Scale_weight"),
        ("nmssm_config", "nmssm_Ytautau", 25, 35, "NMSSM_LHE_Scale_weight"),
        ("nmssm_config", "ttbar", -1, -1, "LHE_Scale_weight"),
    ],
)
def test_truth_mothers_and_lhe_dispatch(module, sample, bb, tautau, lhe):
    config = build(module, sample)
    params = config.config_parameters["mt"]["nominal"]
    assert (
        params["bb_truegen_mother_pdgid"],
        params["tautau_truegen_mother_pdgid"],
    ) == (
        bb,
        tautau,
    )
    assert (
        params["bb_truegen_daughter_1_pdgid"],
        params["tautau_truegen_daughter_1_pdgid"],
    ) == (
        5,
        15,
    )
    assert producer_names(config, "global") & LHE_PRODUCERS == {lhe}


def test_upart_btag_and_v15_input_wiring():
    config = build("sm_config", "ttbar", scopes=ALL_SCOPES)
    params = config.config_parameters["global"]["nominal"]
    payload = btag_payloads.btv_upart_payload("2018")
    assert params["bjet_max_abs_eta"] == 2.4
    assert params["bjet_score_column"] == "Jet_btagUParTAK4B"
    assert params["bjet_min_score"] == btag_payloads.load_upart_wps(payload)["M"]

    sf = config.config_parameters["mt"]["nominal"]
    assert sf["bjet_sf_file"] == payload
    # swapping these applies heavy-flavour SFs to light jets and vice versa
    assert (sf["bjet_sf_bc_name"], sf["bjet_sf_lf_name"]) == (
        "UParTAK4_comb",
        "UParTAK4_light",
    )
    # the efficiency lookup keys on the sample's own name and reads the per-channel payload
    assert sf["bjet_eff_sample_type"] == "ttbar"
    assert (
        build("sm_config", "hh2b2tau").config_parameters["mt"]["nominal"][
            "bjet_eff_sample_type"
        ]
        == "hh2b2tau"
    )
    assert (
        sf["bjet_eff_file"]
        == "payloads/btagging_efficiencies/upart/2018/btag_efficiency_mt.json.gz"
    )

    # the correctionlib jet ID, not the v9 Jet_jetId rename; the Run-3-style electron
    # scale+smear group, not the Run-2 rename (both era variants share one name)
    assert (
        "physicsobject::jet::quantity::ID"
        in find_producer(config, "global", "JetID").call
    )
    assert (
        "physicsobject::electron::PtCorrectionMC"
        in find_producer(config, "global", "ElectronPtCorrectionMC").call
    )

    # the Run-3 EGM Electron-HLT-SF correction does not exist for 2018 UL, so the et
    # scope evaluates TauAnalysis' Trg32_Iso_pt_eta_bins instead
    et = producer_names(config, "et")
    assert (
        "ETGenerateSingleElectronTriggerSF_MC" in et and "SingleEleTriggerSF" not in et
    )


def test_upart_weight_variation_columns_match_discovery():
    variations = btag_payloads.discover_upart_variations(
        btag_payloads.btv_upart_payload("2018")
    )
    keys = (variations["UParTAK4_comb"] | variations["UParTAK4_light"]) - {"central"}
    expected = {"btag_weight_upart"} | {f"btag_weight_upart_{k}" for k in keys}
    assert len(expected) == 83
    config = build("sm_config", "ttbar", scopes=ALL_SCOPES)
    for scope in ALL_SCOPES:
        assert {
            o for o in output_names(config, scope) if o.startswith("btag_weight_upart")
        } == expected, scope


def test_sm_dyw_recoil_wiring():
    """The merged dyjets/wjets names get the gen-boson four-vector and the intact
    recoil-correction group; everything else takes RenameMet."""
    for sample in ("dyjets", "wjets"):
        config = build("sm_config", sample)
        names = producer_names(config, "mt") | producer_names(config, "global")
        assert {
            "GenBosonQuantities",
            "MetScopes",
        } <= names and "RenameMet" not in names, sample
    ttbar = build("sm_config", "ttbar", scopes=ALL_SCOPES)
    names = producer_names(ttbar, "mt") | producer_names(ttbar, "global")
    assert "RenameMet" in names and not {"GenBosonQuantities", "MetScopes"} & names


@pytest.mark.parametrize(
    "module,era,sample,message",
    [
        ("sm_btag_efficiency_config", "2017", "ttbar", "does not support era '2017'"),
        ("sm_btag_efficiency_config", "2018", "data", "does not accept sample 'data'"),
        ("sm_config", "2022postEE", "ttbar", "does not support era '2022postEE'"),
    ],
)
def test_module_level_gates_fire_before_build_config(module, era, sample, message):
    """``generate.run`` rejects an unsupported era/sample without building."""
    entry = importlib.import_module(f"analysis_configurations.bbtautau.{module}")
    with mock.patch.object(
        entry, "build_config", side_effect=AssertionError("must not be called")
    ):
        with pytest.raises(ValueError, match=message):
            generate.run(FakeArgs(module, era, sample))


def test_nmssm_2018_keeps_legacy_jet_and_btag_path():
    """Every SM-only v15 switch is profile-gated, so NMSSM 2018 is untouched."""
    config = build("nmssm_config", "ttbar")
    params = config.config_parameters["global"]["nominal"]
    assert (params["bjet_max_abs_eta"], params["bjet_score_column"]) == (
        2.5,
        "Jet_btagDeepFlavB",
    )
    assert (params["ak4jet_id_wp"], params["ak4jet_id_file"]) == (2, "DOES_NOT_EXIST")
    assert "event::quantity::Rename" in find_producer(config, "global", "JetID").call
    mt, outs = producer_names(config, "mt"), output_names(config, "mt")
    assert "BJetShapeDeepJet_SF" in mt and "StrictUParTBtagWeight" not in mt
    assert "id_wgt_bjet" in outs and not {
        o for o in outs if o.startswith("btag_weight_upart")
    }
