"""SM Run-2 UL NanoAOD-v15 config contracts, and the NMSSM path they must not disturb.

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
from analysis_configurations.bbtautau.producers import scalefactors
from analysis_configurations.bbtautau.constants import (
    ERAS_RUN2,
    RUN2_V15_RECOIL_CORRECTION_ERAS,
    SCOPES,
)
from analysis_configurations.bbtautau.tests.helpers import (
    FakeArgs,
    build,
    find_producer,
    generate_code,
    output_names,
    producer_names,
)

ALL_SCOPES = tuple(SCOPES)
CROWN = Path(__file__).resolve().parents[3]
LHE_PRODUCERS = {"LHE_Scale_weight", "NMSSM_LHE_Scale_weight"}
PILEUP_COLUMNS = {"npv_good", "rho"}
FLAVOUR_COLUMNS = {
    f"{jets}_hadronFlavour_{index}" for jets in ("jet", "bpair") for index in (1, 2)
}
# inclusive LO ttZ and ttW, ttZ -> nunu (in TTZToLLNuNu_M-10) and ZH(bb) with Z -> bb
# (in the ZToQQ samples)
DOUBLE_COUNTED = ("ttZJets_", "ttWJets_", "TTZToNuNu_", "ZH_HToBB_ZToBB_", "ggZH_HToBB_ZToBB_")
# the two samples of ZZ -> 2nu2q; an era takes one of them
ZZ_TO_2NU2Q = ("ZZTo2Nu2Q_5f_", "ZZTo2Q2Nu_")


def sm_era_cases(*rows, nmssm=()):
    """``pytest.param`` rows of sm_config in every Run-2 era and of nmssm_config in
    2018. Each row starts with module and sample; the era follows them."""
    cases = []
    for row in rows:
        for era in ERAS_RUN2:
            cases.append(pytest.param(row[0], row[1], era, *row[2:]))
    cases += [pytest.param(row[0], row[1], "2018", *row[2:]) for row in nmssm]
    return cases


# module, sample, era, bb mother pdgid, tautau mother pdgid, the only LHE producer that
# may be scheduled. A lost SampleModifier key falls back to -1 and yields garbage
# truth pairs, so the background default is pinned as well.
@pytest.mark.parametrize(
    "module,sample,era,bb,tautau,lhe",
    sm_era_cases(
        ("sm_config", "hh2b2tau", 25, 25, "LHE_Scale_weight"),
        nmssm=[
            ("nmssm_config", "nmssm_Ybb", 35, 25, "NMSSM_LHE_Scale_weight"),
            ("nmssm_config", "nmssm_Ytautau", 25, 35, "NMSSM_LHE_Scale_weight"),
            ("nmssm_config", "ttbar", -1, -1, "LHE_Scale_weight"),
        ],
    ),
)
def test_truth_mothers_and_lhe_dispatch(module, sample, era, bb, tautau, lhe):
    config = build(module, sample, era=era)
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


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_upart_btag_and_v15_input_wiring(era):
    config = build("sm_config", "ttbar", era=era, scopes=ALL_SCOPES)
    params = config.config_parameters["global"]["nominal"]
    payload = btag_payloads.btv_upart_payload(era)
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
    # the efficiency lookup keys on the sample's own name and reads the per-channel
    # payload of the era
    assert sf["bjet_eff_sample_type"] == "ttbar"
    assert (
        build("sm_config", "hh2b2tau", era=era).config_parameters["mt"]["nominal"][
            "bjet_eff_sample_type"
        ]
        == "hh2b2tau"
    )
    assert (
        sf["bjet_eff_file"]
        == f"payloads/btagging_efficiencies/upart/{era}/btag_efficiency_mt.json.gz"
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


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_et_trigger_sf_is_the_kit_one(era):
    """The EGM Electron-HLT-SF correction does not exist for Run-2 UL, so the et scope
    evaluates the trigger SF of the Tau Embedding group (KIT)."""
    et = producer_names(build("sm_config", "ttbar", era=era, scopes=("et",)), "et")
    assert (
        "ETGenerateSingleElectronTriggerSF_MC" in et and "SingleEleTriggerSF" not in et
    )


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_v15_data_electrons_get_the_egm_scale(era):
    """v15 electrons come without scale and smearing: data take the "Scale" of the
    pinned EGM payload through the Run-3 producer, as MC take its "SmearAndSyst"."""
    config = build("sm_config", "data", era=era)
    producer = find_producer(config, "global", "ElectronPtCorrectionData")
    assert "physicsobject::electron::PtCorrectionData" in producer.call
    params = config.config_parameters["global"]["nominal"]
    assert params["ele_es_sf_data_name"] == "Scale"
    assert f"/EGM/Run2-{era}-UL-NanoAODv15/" in params["ele_es_file"]
    correctionlib = pytest.importorskip("correctionlib")
    scale = correctionlib.CorrectionSet.from_file(params["ele_es_file"]).compound["Scale"]
    # the input order PtCorrectionData evaluates
    assert [i.name for i in scale.inputs] == ["syst", "run", "ScEta", "r9", "pt", "seedGain"]


# the fixed-WP b-tag nuisances (v7 spec C14): flavour group x correlation x direction
BTAG_COMPONENTS = [
    f"{direction}_{flavour}_{correlation}"
    for flavour in ("bc", "light")
    for correlation in ("correlated", "uncorrelated")
    for direction in ("up", "down")
]


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_upart_weight_columns_are_the_fixed_wp_nuisances(era):
    """C14: the nominal weight and the eight variations of the fixed-WP nuisances
    (b/c and light, correlated and uncorrelated, up and down; the other flavour
    group central), each with the count of its factors set to 1 (K1); 18 columns
    instead of the 83 breakdown columns."""
    expected = {"btag_weight_upart", "btag_unity_jets_upart"}
    expected |= {f"btag_weight_upart_{c}" for c in BTAG_COMPONENTS}
    expected |= {f"btag_unity_jets_upart_{c}" for c in BTAG_COMPONENTS}
    config = build("sm_config", "ttbar", era=era, scopes=ALL_SCOPES)
    for scope in ALL_SCOPES:
        assert {
            o for o in output_names(config, scope) if o.startswith(("btag_weight_upart", "btag_unity"))
        } == expected, scope
    group = find_producer(config, "mt", "StrictUParTBtagWeight")
    calls = {p.name: p.call for p in group.producers["mt"]}
    assert '"central", "central")' in calls["StrictUParTBtagWeightNominal"]
    for component in BTAG_COMPONENTS:
        direction, flavour, correlation = component.split("_")
        key = f'"{direction}_{correlation}"'
        varied = f'{key}, "central")' if flavour == "bc" else f'"central", {key})'
        assert calls[f"StrictUParTBtagWeight_{component}"].endswith(varied), component
    for call in calls.values():
        if "multi_wp_event_weight" in call:
            assert "{vec_open}{bjet_sf_working_points}{vec_close}" in call


def test_upart_dispatch_requires_the_payload_keys():
    variations = btag_payloads.discover_upart_variations(
        btag_payloads.btv_upart_payload("2018")
    )
    dispatch = scalefactors.upart_variation_dispatch(variations)
    assert [d["suffix"] for d in dispatch] == BTAG_COMPONENTS
    broken = dict(variations, UParTAK4_light=variations["UParTAK4_light"] - {"up_uncorrelated"})
    with pytest.raises(KeyError, match="up_uncorrelated.*UParTAK4_light"):
        scalefactors.upart_variation_dispatch(broken)


# The legacy HTT recoil files describe v15 in 2018 only (met_recoil_study,
# 2026-10-18); DY and W of the other eras take the MET of every other sample.
RECOIL_ERAS = [era for era in ERAS_RUN2 if era in RUN2_V15_RECOIL_CORRECTION_ERAS]
NO_RECOIL_ERAS = [era for era in ERAS_RUN2 if era not in RUN2_V15_RECOIL_CORRECTION_ERAS]
RECOIL_CHAIN = ("MetLeptonCorrectionOnPuppiMet", "RecoilCorrectionMet", "MetJetScaleAfterRecoil")


def has_producer(config, scope, name):
    try:
        find_producer(config, scope, name)
    except AssertionError:
        return False
    return True


def test_recoil_correction_eras():
    """Only the 2018 recoil file closes the v15 Z -> mumu MET; the 2016 and 2017
    files worsen it."""
    assert RUN2_V15_RECOIL_CORRECTION_ERAS == ("2018",)
    assert RECOIL_ERAS == ["2018"]


@pytest.mark.parametrize("era", RECOIL_ERAS)
def test_sm_dyw_recoil_wiring(era):
    """In the recoil-correction eras the merged dyjets/wjets names get the
    gen-boson four-vector, the recoil chain with the correction on and the
    JES-only jet pt; everything else replaces the correction by RenameMet and
    drops the chain around it."""
    for sample in ("dyjets", "wjets"):
        config = build("sm_config", sample, era=era)
        assert "GenBosonQuantities" in producer_names(config, "mt"), sample
        assert all(has_producer(config, "mt", name) for name in RECOIL_CHAIN), sample
        assert not has_producer(config, "mt", "RenameMet"), sample
        assert has_producer(config, "global", "JetScaledPt"), sample
        assert config.config_parameters["mt"]["nominal"]["apply_recoil_correction"], sample
    for sample in ("ttbar", "data", "embedding"):
        config = build("sm_config", sample, era=era, scopes=ALL_SCOPES if sample == "ttbar" else ("mt",))
        assert has_producer(config, "mt", "RenameMet"), sample
        assert not any(has_producer(config, "mt", name) for name in RECOIL_CHAIN), sample
        assert not has_producer(config, "global", "JetScaledPt"), sample
        assert "GenBosonQuantities" not in producer_names(config, "mt"), sample


@pytest.mark.parametrize("era", NO_RECOIL_ERAS)
@pytest.mark.parametrize("sample", ["dyjets", "wjets", "ttbar"])
def test_sm_no_recoil_correction_outside_the_recoil_eras(sample, era):
    """Outside the recoil-correction eras DY and W keep the propagated MET of every
    other simulated sample: no recoil producer, no recoil jets and no recoil
    shifts, the final MET is the renamed MET with propagated jets and leptons."""
    config = build("sm_config", sample, era=era, shifts=("all",))
    assert not any(has_producer(config, "mt", name) for name in RECOIL_CHAIN)
    assert not has_producer(config, "global", "GoodRecoilJets")
    assert not has_producer(config, "global", "JetScaledPt")
    assert [q.name for q in find_producer(config, "mt", "RenameMet").get_inputs("mt")] == [
        "met_p4_leptoncorrected"
    ]
    assert not [shift for shift in config.shifts["mt"] if "RecoilCalibration" in shift]


@pytest.mark.parametrize("era", RECOIL_ERAS)
@pytest.mark.parametrize("sample", ["dyjets", "wjets"])
def test_sm_recoil_correction_before_the_jet_propagation(sample, era):
    """The recoil correction acts on the MET its legacy file was derived on, the
    NanoAOD PuppiMET with the propagated leptons; the jet energy scale of the
    re-calibrated jets (pT > 15 GeV, JES with its shifts, without the JER
    smearing) is propagated afterwards, as in data. Propagating the JER-smeared
    jets before the correction counted the resolution twice (v7: data/MC of the
    MET tail 60-150 GeV in mm 0.76 instead of 0.98)."""
    config = build("sm_config", sample, era=era)

    def io(name, scope="mt"):
        producer = find_producer(config, scope, name)
        return (
            [q.name for q in producer.get_inputs(scope)],
            [q.name for q in producer.get_outputs(scope)],
        )

    assert io("MetLeptonCorrectionOnPuppiMet") == (
        ["met_p4_uncorrected", "p4_1_uncorrected", "p4_2_uncorrected", "p4_1", "p4_2"],
        ["met_p4_recoil_input"],
    )
    assert io("RecoilCorrectionMet") == (
        ["met_p4_recoil_input", "gen_boson_p4", "gen_vis_boson_p4", "Jet_recoilPt"],
        ["met_p4_recoil_nojets"],
    )
    assert io("MetJetScaleAfterRecoil") == (
        [
            "met_p4_recoil_nojets", "Jet_scaledPt", "Jet_eta", "Jet_phi",
            "Jet_correctedMass", "Jet_pt", "Jet_eta", "Jet_phi", "Jet_mass",
        ],
        ["met_p4_recoilcorrected"],
    )
    assert io("JetScaledPt", "global") == (["Jet_jecResult"], ["Jet_scaledPt"])
    assert "jec::ScaledPt" in find_producer(config, "global", "JetScaledPt").call
    assert io("MetPt")[0] == ["met_p4_recoilcorrected"]
    params = config.config_parameters["mt"]["nominal"]
    assert (params["propagate_jets_to_met"], params["t1jet_min_pt"]) == (True, 15.0)
    assert params["is_wjets"] is (sample == "wjets")


# Every sample type the recoil rules exclude from RenameMet (common_config,
# recoil_samples): the merged SM names and the legacy NMSSM ones.
RECOIL_SAMPLE_TYPES = (
    "dyjets", "wjets", "dyjets_madgraph", "dyjets_amcatnlo", "dyjets_amcatnlo_ll",
    "dyjets_amcatnlo_tt", "dyjets_powheg", "wjets_madgraph", "wjets_amcatnlo",
)


@pytest.mark.parametrize("era", RECOIL_ERAS)
@pytest.mark.parametrize("sample", RECOIL_SAMPLE_TYPES + ("ttbar", "diboson", "data", "embedding"))
def test_sm_jet_scaled_pt_comes_with_the_recoil_chain(sample, era):
    """Every sample type that keeps the recoil chain gets the JES-only jet pt it
    propagates after the correction, also the legacy DY/W names (before, only the
    merged dyjets/wjets did, and a v15 build of dyjets_amcatnlo read a column no
    producer defined); the other samples get neither. Jet_scaledPt is an
    intermediate column, not an output."""
    config = build("sm_config", sample, era=era)
    chain = has_producer(config, "mt", "MetJetScaleAfterRecoil")
    assert chain is (sample in RECOIL_SAMPLE_TYPES)
    assert all(has_producer(config, "mt", name) for name in RECOIL_CHAIN) is chain
    assert has_producer(config, "global", "JetScaledPt") is chain
    assert not any("Jet_scaledPt" in {q.name for q in outputs} for outputs in config.outputs.values())


@pytest.mark.parametrize("era", RECOIL_ERAS)
def test_sm_recoil_corrected_met_follows_the_jes_and_recoil_shifts(era):
    """The generated DY code writes the MET under the JES shifts (propagated after
    the recoil correction through Jet_scaledPt) and under the recoil shifts. The
    unclustered-energy shift varies the NanoAOD PuppiMET, so for DY and W it acts
    before the recoil correction, as it did before the fix (there through the
    jet-propagated MET); the HTT recipe applies the recoil shifts instead of it to
    recoil-corrected samples, to be decided with the shift production (nominal
    unaffected, see variations/met.py)."""
    met = {o for o in generate_code("sm_config", "dyjets", era, shifts=("all",)).outputs["mt"] if o.startswith("met__")}
    assert {"met__CMS_scale_j_AbsoluteUp", f"met__CMS_scale_j_Absolute_{era}Down"} <= met
    assert {f"met__CMS_{kind}_met_RecoilCalibration_{era}{d}" for kind in ("scale", "res") for d in ("Up", "Down")} <= met
    assert {f"met__CMS_scale_met_unclustered_energy_{era}{d}" for d in ("Up", "Down")} <= met


@pytest.mark.parametrize("era", RECOIL_ERAS)
def test_sm_recoil_correction_counts_the_recipe_jets(era):
    """The v15 recoil correction counts the jets of the HTT recipe (pT > 30 GeV,
    |eta| < 4.7, jet ID, DeltaR > 0.5 to both pair objects), not all NanoAOD jets;
    NMSSM keeps all jets."""
    config = build("sm_config", "dyjets", era=era)

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
    nmssm = build("nmssm_config", "dyjets_amcatnlo", era="2018")
    recoil = find_producer(nmssm, "mt", "RecoilCorrectionMet")
    assert [q.name for q in recoil.get_inputs("mt")] == [
        "met_p4_leptoncorrected", "gen_boson_p4", "gen_vis_boson_p4", "Jet_correctedPt",
    ]


@pytest.mark.parametrize("era", RECOIL_ERAS)
def test_sm_recoil_file_has_the_labelled_z_pt_bins(era):
    """The recoil files of CROWN (one 2016 file for both halves) had the Z pT bin
    edges 0-5 instead of the 0/10/20/30/50/1000 GeV their labels name; the CROWN
    pin must contain the fix (27262f4)."""
    ROOT = pytest.importorskip("ROOT")
    path = build("sm_config", "dyjets", era=era).config_parameters["mt"]["nominal"][
        "recoil_correction_file"
    ]
    year = era[:4]
    assert path == f"data/recoil_corrections/Type1_PuppiMET_{year}.root"
    file = ROOT.TFile.Open(str(CROWN / path))
    axis = file.Get("ZPtBinsH").GetXaxis()
    edges = [axis.GetBinLowEdge(i) for i in range(1, axis.GetNbins() + 2)]
    labels = [axis.GetBinLabel(i) for i in range(1, axis.GetNbins() + 1)]
    file.Close()
    assert edges == [0, 10, 20, 30, 50, 1000]
    assert labels == ["Pt0to10", "Pt10to20", "Pt20to30", "Pt30to50", "PtGt50"]


@pytest.mark.parametrize(
    "module,sample,era,propagate",
    sm_era_cases(
        ("sm_config", "ttbar", True),
        ("sm_config", "dyjets", True),
        ("sm_config", "data", True),
        ("sm_config", "embedding", True),
        nmssm=[("nmssm_config", "ttbar", True), ("nmssm_config", "data", False)],
    ),
)
def test_jet_propagation_to_the_met(module, sample, era, propagate):
    """The v15 inputs propagate the re-applied JEC to the MET in data, MC and
    embedding alike (v7 spec E28, C19); NMSSM in MC only."""
    params = build(module, sample, era=era).config_parameters["global"]["nominal"]
    assert params["propagate_jets_to_met"] is propagate


@pytest.mark.parametrize(
    "module,sample,era,final_met",
    sm_era_cases(
        ("sm_config", "ttbar", "RenameMet"),
        ("sm_config", "data", "RenameMet"),
        ("sm_config", "embedding", "RenameMet"),
        nmssm=[("nmssm_config", "ttbar", "RenameMet")],
    )
    + [pytest.param("sm_config", "dyjets", era, "RenameMet") for era in NO_RECOIL_ERAS]
    + [
        pytest.param("sm_config", "dyjets", era, "MetLeptonCorrectionOnPuppiMet")
        for era in RECOIL_ERAS
    ],
)
def test_met_keeps_the_lepton_propagation(module, sample, era, final_met):
    """The final MET carries the lepton propagation, also in samples whose recoil
    correction is replaced by a rename; the recoil-corrected samples propagate
    the leptons to the PuppiMET the correction reads."""
    scopes = ("et", "mt", "tt")
    config = build(module, sample, era=era, scopes=scopes)
    for scope in scopes:
        inputs = find_producer(config, scope, final_met).get_inputs(scope)
        expected = (
            "met_p4_uncorrected"
            if final_met == "MetLeptonCorrectionOnPuppiMet"
            else "met_p4_leptoncorrected"
        )
        assert inputs[0].name == expected, scope


@pytest.mark.parametrize(
    "module,sample,era", sm_era_cases(("sm_config", "ttbar"), ("sm_config", "data"), ("sm_config", "embedding"))
)
def test_pileup_and_jet_flavour_columns(module, sample, era):
    """npv_good and rho in every sample kind, the jet hadron flavours in MC only,
    in every scope; NMSSM writes neither."""
    scopes = ("et", "mt", "tt") if sample == "embedding" else ALL_SCOPES
    config = build(module, sample, era=era, scopes=scopes)
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
    nmssm_sample = sample if sample != "embedding" else "ttbar"
    nmssm = output_names(build("nmssm_config", nmssm_sample, era="2018"), "mt")
    assert not (PILEUP_COLUMNS | FLAVOUR_COLUMNS) & nmssm


@pytest.mark.parametrize("era", RECOIL_ERAS)
@pytest.mark.parametrize("sample", ["dyjets", "wjets"])
def test_sm_recoil_shifts_set_the_run2_flags(sample, era):
    """The Run-2 recoil producer reads bool flags, not the Run-3 variation name."""
    config = build("sm_config", sample, era=era, shifts=("all",))
    read = find_producer(config, "mt", "RecoilCorrectionMet").parameters["mt"]
    for systematic, name in [("response", "scale"), ("resolution", "res")]:
        for direction in ("Up", "Down"):
            change = config.shifts["mt"][f"__CMS_{name}_met_RecoilCalibration_{era}{direction}"]
            assert change == {
                f"apply_recoil_{systematic}_systematic": True,
                f"recoil_systematic_shift_{direction.lower()}": True,
            }
            assert set(change) <= read


# the single-muon trigger SF column of the SM configuration per era
SM_MUON_TRIGGER_SF = {
    "2016preVFP": "trg_wgt_single_mu22",
    "2016postVFP": "trg_wgt_single_mu22",
    "2017": "trg_wgt_single_mu27",
    "2018": "trg_wgt_single_mu24",
}


@pytest.mark.parametrize("module,sample,era", sm_era_cases(("sm_config", "ttbar"), nmssm=[("nmssm_config", "ttbar")]))
def test_mt_generates_with_every_shift(module, sample, era):
    """The single-muon trigger SF shifts carry the trigger flag the SF producer
    gates on; without it, code generation with shifts=all failed in mt."""
    outputs = generate_code(module, sample, era=era, shifts=("all",)).outputs["mt"]
    assert {
        f"{SM_MUON_TRIGGER_SF[era]}__CMS_eff_m_trigger_{era}{variation}"
        for variation in ("Up", "Down")
    } <= outputs


SM_MODULES = ("sm_config", "sm_btag_efficiency_config", "sm_tau_id_measurement_config")


@pytest.mark.parametrize("module", SM_MODULES)
def test_sm_modules_accept_every_run2_era(module):
    entry = importlib.import_module(f"analysis_configurations.bbtautau.{module}")
    assert entry.AVAILABLE_ERAS == ERAS_RUN2


@pytest.mark.parametrize(
    "module,era,sample,message",
    [
        ("sm_btag_efficiency_config", "2024", "ttbar", "does not support era '2024'"),
        ("sm_btag_efficiency_config", "2017", "data", "does not accept sample 'data'"),
        ("sm_config", "2022postEE", "ttbar", "does not support era '2022postEE'"),
        ("sm_tau_id_measurement_config", "2023preBPix", "dyjets", "does not support era '2023preBPix'"),
        ("sm_tau_id_measurement_config", "2016preVFP", "hh2b2tau", "does not accept sample 'hh2b2tau'"),
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
    config = build("nmssm_config", "ttbar", era="2018")
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


# nicks of the binned lists per era: all, data
BINNED_LENGTHS = {"2016preVFP": (84, 15), "2016postVFP": (75, 9), "2017": (84, 15), "2018": (81, 12)}


@pytest.fixture(scope="module")
def datasets():
    database = CROWN.parent / "sample_database/nanoAOD_v15/datasets.json"
    if not database.is_file():
        pytest.skip("KingMaker's sample_database is required")
    return json.loads(database.read_text())


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_sm_sample_lists_follow_their_rules(era, datasets):
    """sample_list/README.md: the binned list of the era, sorted; its ``_mc`` list is the
    full list without the data nicks; every MC sample type of the b-tag efficiency
    profile is populated (2016postVFP has no VH -> tautau sample); data from SingleMuon,
    SingleElectron (EGamma in 2018) and Tau; and no phase space counted twice."""
    lists = Path(__file__).resolve().parents[1] / "sample_list"
    full = (lists / f"sm_{era}_binned.txt").read_text()
    nicks = full.splitlines()
    assert full == "".join(f"{nick}\n" for nick in sorted(set(nicks)))
    data = [nick for nick in nicks if datasets[nick]["sample_type"] == "data"]
    mc = [nick for nick in nicks if nick not in data]
    assert (len(nicks), len(data)) == BINNED_LENGTHS[era]
    assert (lists / f"sm_{era}_binned_mc.txt").read_text() == "".join(f"{nick}\n" for nick in mc)
    assert {datasets[nick]["era"] for nick in nicks} == {era}
    expected = set(sm_btag_efficiency_config.AVAILABLE_SAMPLES)
    if era == "2016postVFP":
        expected -= {"rem_htautau"}
    assert {datasets[nick]["sample_type"] for nick in mc} == expected
    electron = "EGamma_" if era == "2018" else "SingleElectron_"
    streams = ("SingleMuon_", electron, "Tau_")
    assert all(nick.startswith(streams) for nick in data)
    assert {stream for stream in streams for nick in data if nick.startswith(stream)} == set(streams)
    assert not [nick for nick in nicks if nick.startswith(DOUBLE_COUNTED)]
    assert len([nick for nick in nicks if nick.startswith(ZZ_TO_2NU2Q)]) == 1
    # the PtZ bins and the inclusive M-50 sample (its npartons == 0 part)
    dy = [nick for nick in mc if datasets[nick]["sample_type"] == "dyjets"]
    assert len([nick for nick in dy if nick.startswith("DYJetsToLL_LHEFilterPtZ-")]) == 6
    assert len([nick for nick in dy if nick.startswith("DYJetsToLL_M-50_")]) == 1
    wjets = [nick for nick in mc if datasets[nick]["sample_type"] == "wjets"]
    assert sorted(nick.split("_")[1] for nick in wjets) == ["0J", "1J", "2J"]
    # the powheg signal and its node_SM cross-check
    hh = [nick for nick in mc if datasets[nick]["sample_type"] == "hh2b2tau"]
    assert len(hh) == 2 and len([nick for nick in hh if "_kl-1p00_" in nick]) == 1


def test_sm_2018_inclusive_lists_swap_the_w_and_dy_partitions(datasets):
    lists = Path(__file__).resolve().parents[1] / "sample_list"
    binned = (lists / "sm_2018_binned.txt").read_text().splitlines()
    inclusive = (lists / "sm_2018_inclusive.txt").read_text().splitlines()
    assert inclusive == sorted(inclusive)
    partitions = {
        nick
        for nick in binned
        if nick.startswith(("WJetsToLNu_0J_", "WJetsToLNu_1J_", "WJetsToLNu_2J_", "DYJetsToLL_LHEFilterPtZ-"))
    }
    (added,) = set(inclusive) - set(binned)
    assert added.startswith("WJetsToLNu_TuneCP5_13TeV-amcatnloFXFX")
    assert set(inclusive) == (set(binned) - partitions) | {added}
    mc = [nick for nick in inclusive if datasets[nick]["sample_type"] != "data"]
    assert (lists / "sm_2018_inclusive_mc.txt").read_text() == "".join(f"{nick}\n" for nick in mc)
