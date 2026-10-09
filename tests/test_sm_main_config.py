"""SM 2018-UL NanoAOD-v15 config contracts, and the NMSSM path they must not disturb.

Each assertion pins a value that would otherwise regress silently into wrong physics
or a broken grid job: the truth-gen mothers and LHE dispatch per sample, the pinned
UParTAK4 b-tag and v15 jet/electron wiring, the per-variation weight columns, the
DY/W recoil treatment, the diagnostic columns, the era/sample gates and the sample
lists.
"""

import importlib
import json
from pathlib import Path
from unittest import mock

import pytest

from analysis_configurations.bbtautau import (
    btag_payloads,
    generate,
    sm_btag_efficiency_config,
)
from analysis_configurations.bbtautau.constants import SCOPES
from analysis_configurations.bbtautau.tests.helpers import (
    FakeArgs,
    build,
    find_producer,
    generate_code,
    output_names,
    producer_names,
)

ALL_SCOPES = tuple(SCOPES)
LHE_PRODUCERS = {"LHE_Scale_weight", "NMSSM_LHE_Scale_weight"}
PILEUP_COLUMNS = {"npv_good", "rho"}
FLAVOUR_COLUMNS = {
    f"{jets}_hadronFlavour_{index}" for jets in ("jet", "bpair") for index in (1, 2)
}
# inclusive LO ttZ, ttZ -> nunu (in TTZToLLNuNu_M-10) and the twin of ZZTo2Q2Nu
DOUBLE_COUNTED = ("ttZJets_", "TTZToNuNu_", "ZZTo2Nu2Q_5f_")


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
    # b/c jets below the lowest calibrated pT of the comb SFs take the SF there
    assert sf["bjet_sf_bc_min_pt"] == btag_payloads.load_upart_comb_min_pt(payload) == 30.0
    assert "{bjet_sf_bc_min_pt}" in find_producer(config, "mt", "StrictUParTBtagWeightNominal").call
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


def test_v15_data_electrons_get_the_egm_scale():
    """v15 electrons come without scale and smearing: data take the "Scale" of the
    pinned EGM payload through the Run-3 producer, as MC take its "SmearAndSyst"."""
    config = build("sm_config", "data")
    producer = find_producer(config, "global", "ElectronPtCorrectionData")
    assert "physicsobject::electron::PtCorrectionData" in producer.call
    params = config.config_parameters["global"]["nominal"]
    assert params["ele_es_sf_data_name"] == "Scale"
    assert "/EGM/Run2-2018-UL-NanoAODv15/" in params["ele_es_file"]
    correctionlib = pytest.importorskip("correctionlib")
    scale = correctionlib.CorrectionSet.from_file(params["ele_es_file"]).compound["Scale"]
    # the input order PtCorrectionData evaluates
    assert [i.name for i in scale.inputs] == ["syst", "run", "ScEta", "r9", "pt", "seedGain"]


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
    recoil-correction group, with the correction on; everything else takes RenameMet."""
    for sample in ("dyjets", "wjets"):
        config = build("sm_config", sample)
        names = producer_names(config, "mt") | producer_names(config, "global")
        assert {
            "GenBosonQuantities",
            "MetScopes",
        } <= names and "RenameMet" not in names, sample
        assert config.config_parameters["mt"]["nominal"]["apply_recoil_correction"], sample
    ttbar = build("sm_config", "ttbar", scopes=ALL_SCOPES)
    names = producer_names(ttbar, "mt") | producer_names(ttbar, "global")
    assert "RenameMet" in names and not {"GenBosonQuantities", "MetScopes"} & names


def test_sm_recoil_correction_counts_the_recipe_jets():
    """The v15 recoil correction counts the jets of the HTT recipe (pT > 30 GeV,
    |eta| < 4.7, jet ID, DeltaR > 0.5 to both pair objects), not all NanoAOD jets;
    NMSSM keeps all jets."""
    config = build("sm_config", "dyjets")

    def inputs(name):
        return [q.name for q in find_producer(config, "mt", name).get_inputs("mt")]

    assert inputs("RecoilCorrectionMet")[-1] == "Jet_recoilPt"
    assert inputs("RecoilJetPt") == ["Jet_correctedPt", "recoil_jets_mask"]
    assert inputs("RecoilJetsMask") == [
        "good_recoil_jets_mask",
        "recoil_jet_overlap_veto_mask",
    ]
    assert inputs("VetoOverlappingRecoilJets")[-2:] == ["p4_1", "p4_2"]
    assert "{ak4jet_id_wp}" in find_producer(config, "global", "GoodRecoilJets").call
    params = config.config_parameters
    assert (
        params["global"]["nominal"]["recoil_jet_min_pt"],
        params["global"]["nominal"]["recoil_jet_max_abs_eta"],
        params["mt"]["nominal"]["recoil_jet_veto_min_delta_r"],
    ) == (30.0, 4.7, 0.5)
    nmssm = build("nmssm_config", "dyjets_amcatnlo")
    recoil = find_producer(nmssm, "mt", "RecoilCorrectionMet")
    assert recoil.get_inputs("mt")[-1].name == "Jet_correctedPt"


def test_sm_recoil_file_has_the_labelled_z_pt_bins():
    """The legacy 2018 recoil file has the Z pT bin edges 0-5 instead of the
    0/10/20/30/50/1000 GeV its labels name; the v15 path reads the fixed copy."""
    ROOT = pytest.importorskip("ROOT")
    path = build("sm_config", "dyjets").config_parameters["mt"]["nominal"][
        "recoil_correction_file"
    ]
    assert path.startswith("payloads/")
    file = ROOT.TFile.Open(str(Path(__file__).resolve().parents[1] / path))
    axis = file.Get("ZPtBinsH").GetXaxis()
    edges = [axis.GetBinLowEdge(i) for i in range(1, axis.GetNbins() + 2)]
    labels = [axis.GetBinLabel(i) for i in range(1, axis.GetNbins() + 1)]
    file.Close()
    assert edges == [0, 10, 20, 30, 50, 1000]
    assert labels == ["Pt0to10", "Pt10to20", "Pt20to30", "Pt30to50", "PtGt50"]


@pytest.mark.parametrize(
    "module,sample,propagate",
    [
        ("sm_config", "ttbar", False),
        ("sm_config", "dyjets", False),
        ("sm_config", "data", False),
        ("sm_config", "embedding", False),
        ("nmssm_config", "ttbar", True),
        ("nmssm_config", "data", False),
    ],
)
def test_jet_propagation_to_the_met(module, sample, propagate):
    """The v15 nominal MET of MC is the NanoAOD PuppiMET, as in data and embedding;
    NMSSM propagates the re-applied JEC to the MET of MC."""
    params = build(module, sample).config_parameters["global"]["nominal"]
    assert params["propagate_jets_to_met"] is propagate


@pytest.mark.parametrize(
    "module,sample,final_met",
    [
        ("sm_config", "ttbar", "RenameMet"),
        ("sm_config", "data", "RenameMet"),
        ("sm_config", "embedding", "RenameMet"),
        ("sm_config", "dyjets", "RecoilCorrectionMet"),
        ("nmssm_config", "ttbar", "RenameMet"),
    ],
)
def test_met_keeps_the_lepton_propagation(module, sample, final_met):
    """The final MET starts from the lepton-corrected MET, also in samples whose
    recoil correction is replaced by a rename."""
    scopes = ("et", "mt", "tt")
    config = build(module, sample, scopes=scopes)
    for scope in scopes:
        inputs = find_producer(config, scope, final_met).get_inputs(scope)
        assert inputs[0].name == "met_p4_leptoncorrected", scope


@pytest.mark.parametrize("sample", ["ttbar", "data", "embedding"])
def test_pileup_and_jet_flavour_columns(sample):
    """npv_good and rho in every sample kind, the jet hadron flavours in MC only,
    in every scope; NMSSM writes neither."""
    scopes = ("et", "mt", "tt") if sample == "embedding" else ALL_SCOPES
    config = build("sm_config", sample, scopes=scopes)
    for scope in scopes:
        outputs = output_names(config, scope)
        assert PILEUP_COLUMNS <= outputs, scope
        if sample == "ttbar":
            assert FLAVOUR_COLUMNS <= outputs, scope
        else:
            assert not FLAVOUR_COLUMNS & outputs, scope
    if sample == "ttbar":
        bpair = find_producer(config, "mt", "bpair_hadronFlavour_1").get_inputs("mt")
        assert [q.name for q in bpair] == ["Jet_hadronFlavour", "dibjetpair"]
        jet = find_producer(config, "mt", "jet_hadronFlavour_1").get_inputs("mt")
        assert [q.name for q in jet] == ["Jet_hadronFlavour", "good_jet_collection"]
    nmssm = output_names(build("nmssm_config", sample if sample != "embedding" else "ttbar"), "mt")
    assert not (PILEUP_COLUMNS | FLAVOUR_COLUMNS) & nmssm


@pytest.mark.parametrize("sample", ["dyjets", "wjets"])
def test_sm_recoil_shifts_set_the_run2_flags(sample):
    """The Run-2 recoil producer reads bool flags, not the Run-3 variation name."""
    config = build("sm_config", sample, shifts=("all",))
    read = find_producer(config, "mt", "RecoilCorrectionMet").parameters["mt"]
    for systematic, name in [("response", "scale"), ("resolution", "res")]:
        for direction in ("Up", "Down"):
            change = config.shifts["mt"][f"__CMS_{name}_met_RecoilCalibration_2018{direction}"]
            assert change == {
                f"apply_recoil_{systematic}_systematic": True,
                f"recoil_systematic_shift_{direction.lower()}": True,
            }
            assert set(change) <= read


@pytest.mark.parametrize("module", ["sm_config", "nmssm_config"])
def test_mt_generates_with_every_shift(module):
    """The single-muon trigger SF shifts carry the trigger flag the SF producer
    gates on; without it, code generation with shifts=all failed in mt."""
    outputs = generate_code(module, "ttbar", shifts=("all",)).outputs["mt"]
    assert {
        f"trg_wgt_single_mu24__CMS_eff_m_trigger_2018{variation}"
        for variation in ("Up", "Down")
    } <= outputs


@pytest.mark.parametrize(
    "module,era,sample,message",
    [
        ("sm_btag_efficiency_config", "2017", "ttbar", "does not support era '2017'"),
        ("sm_btag_efficiency_config", "2018", "data", "does not accept sample 'data'"),
        ("sm_config", "2022postEE", "ttbar", "does not support era '2022postEE'"),
        ("sm_tau_id_measurement_config", "2017", "dyjets", "does not support era '2017'"),
        ("sm_tau_id_measurement_config", "2018", "hh2b2tau", "does not accept sample 'hh2b2tau'"),
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


def test_sm_sample_lists_follow_their_rules():
    """sample_list/README.md: each ``_mc`` list is its full list without the 12 data
    nicks, every MC sample type is populated, and no list double counts ttZ or ZZ."""
    analysis = Path(__file__).resolve().parents[1]
    database = analysis.parents[2] / "sample_database/nanoAOD_v15/datasets.json"
    if not database.is_file():
        pytest.skip("KingMaker's sample_database is required")
    datasets = json.loads(database.read_text())
    for name, length in [("binned", 77), ("inclusive", 69)]:
        nicks = (analysis / f"sample_list/sm_2018_{name}.txt").read_text().splitlines()
        mc = [nick for nick in nicks if datasets[nick]["sample_type"] != "data"]
        assert len(nicks) == length and len(nicks) - len(mc) == 12, name
        assert (analysis / f"sample_list/sm_2018_{name}_mc.txt").read_text() == "".join(
            f"{nick}\n" for nick in mc
        )
        assert {datasets[nick]["era"] for nick in nicks} == {"2018"}
        assert {datasets[nick]["sample_type"] for nick in mc} == set(
            sm_btag_efficiency_config.AVAILABLE_SAMPLES
        )
        assert not [nick for nick in nicks if nick.startswith(DOUBLE_COUNTED)], name
