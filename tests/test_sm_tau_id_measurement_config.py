"""The tau-ID SF and ES measurement configuration (sm_tau_id_measurement_config.py).

Its choices follow jvoss's measurement production SFs_EMB_Run2_04_08_26 (README
section "Tau-ID measurement"). Pinned here, because each fails silently otherwise:
the trigger and its SFs, the MC muon and tau corrections, the uncorrected embedding
taus with their lowered pT threshold, the mu -> mu embedding in mm, and MC shifts
that change what the predecessor's shape systematics need.
"""

import json
from pathlib import Path

import pytest

from analysis_configurations.bbtautau import sm_tau_id_measurement_config
from analysis_configurations.bbtautau.tau_variations import POG_TAU_VSJET_2018_COMPONENTS
from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    generate_code,
    output_names,
    producer_names,
)
from analysis_configurations.bbtautau.tests.test_embedding_run2_v15_config import (
    BRANCHES,
    nanoaod_inputs,
)

MODULE = "sm_tau_id_measurement_config"
SCOPES = ("mt", "mm")
SAMPLES = ("data", "dyjets", "embedding")
TRIGGER_SFS = {
    "trg_wgt_single_mu24": "Trg_IsoMu24_pt_eta_bins",
    "trg_wgt_single_mu27": "Trg_IsoMu27_pt_eta_bins",
    "trg_wgt_single_mu24ormu27": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
}
JES_SOURCES = [
    "AbsoluteMPFBias", "AbsoluteScale", "AbsoluteStat", "FlavorQCD", "Fragmentation",
    "PileUpDataMC", "PileUpPtBB", "PileUpPtEC1", "PileUpPtEC2", "PileUpPtHF",
    "PileUpPtRef", "RelativeBal", "RelativeFSR", "RelativeJEREC1", "RelativeJEREC2",
    "RelativeJERHF", "RelativePtBB", "RelativePtEC1", "RelativePtEC2", "RelativePtHF",
    "RelativeSample2018", "RelativeStatEC", "RelativeStatFSR", "RelativeStatHF",
    "SinglePionECAL", "SinglePionHCAL", "TimePtEta", "Total", "HEMIssue",
]
# the predecessor's family spelling of a JES source, where it differs
JES_FAMILY_NAMES = {
    "PileUpPtEC1": "PileupPtEC1",
    "PileUpPtRef": "PileupPtRef",
    "RelativeSample2018": "RelativeSample",
}
# Shape systematics of the predecessor measurement (jvoss's synced shapes of
# SFs_EMB_Run2_04_08_26__full), family -> the CROWN shifts behind it. Weight-only
# families (CMS_fake_j, CMS_htt_ttbarShape) and the embedding ttbar contamination
# are built downstream from nominal columns and are listed in the README.
PREDECESSOR_SHIFTS = {
    "CMS_PileUp": ["PileUp"],
    "CMS_eff_m_trigger_Run2018": ["singleMuonTriggerSF"],
    **{
        f"CMS_eff_t_dm{dm}_Run2018": [
            f"vsJetTau{component}DM{dm}" for component in ("Stat1", "Stat2", "SystTes")
        ]
        for dm in (0, 1, 10, 11)
    },
    **{f"CMS_fake_m_WH{wheel}_Run2018": [f"vsMuWheel{wheel}"] for wheel in range(1, 6)},
    "CMS_res_met_Run2018": ["metRecoilResol"],
    "CMS_scale_met_Run2018": ["metRecoilResp"],
    "CMS_scale_fake_m_Run2018": ["tauMuFakeEs"],
    "CMS_scale_met_unclustered_energy_Run2018": ["metUnclusteredEn"],
    **{
        f"CMS_scale_t_dm{dm}_Run2018": [f"tauEs{token}"]
        for dm, token in [
            (0, "1prong0pizero"), (1, "1prong1pizero"),
            (10, "3prong0pizero"), (11, "3prong1pizero"),
        ]
    },
    **{
        f"CMS_scale_j_{JES_FAMILY_NAMES.get(source, source)}": [f"jesUnc{source}"]
        for source in JES_SOURCES
        if source != "HEMIssue"
    },
    "CMS_scale_j_HEMIssue_Run2018": ["jesUncHEMIssue"],
}
# families of the tau and the trigger, which the predecessor has in mt only
MT_ONLY_FAMILIES = (
    "CMS_eff_t", "CMS_scale_t", "CMS_fake_m", "CMS_scale_fake_m", "CMS_eff_m_trigger",
)
# the vsJet SF components correlated across decay modes, which no predecessor
# family carries (its per-DM shifts evaluated the nominal SF)
CORRELATED_VSJET_SHIFTS = ["vsJetTauSyst2018", "vsJetTauSystAllEras"]


def measurement(sample, shifts=("none",), scopes=SCOPES):
    return build(MODULE, sample, scopes=tuple(scopes), shifts=shifts)


def parameters(config, scope):
    return config.config_parameters[scope]["nominal"]


def shift_names(config, scope):
    return {name.removeprefix("__") for name in config.shifts[scope]}


def calls(sample, scope, producer):
    """The generated calls of ``producer`` in ``scope``, whitespace collapsed."""
    source = generate_code(MODULE, sample, scopes=SCOPES).directory
    (path,) = source.rglob(f"src/{scope}/{producer}.cxx")
    return " ".join(path.read_text().split())


@pytest.mark.parametrize("shifts", [("none",), ("all",)])
@pytest.mark.parametrize("sample", SAMPLES)
def test_builds_for_mt_and_mm(sample, shifts):
    config = measurement(sample, shifts)
    assert set(SCOPES) <= set(config.scopes)


@pytest.mark.parametrize("scopes", [["et"], ["mt", "tt"], ["em"]])
def test_other_scopes_raise(scopes):
    with pytest.raises(ValueError, match="only, got"):
        measurement("dyjets", scopes=scopes)


@pytest.mark.parametrize("sample", SAMPLES)
@pytest.mark.parametrize("scope", SCOPES)
def test_trigger_is_isomu24_or_isomu27(sample, scope):
    """As in the measurement production: filter bit 3, |eta| < 2.5, 25/28 GeV."""
    flags = calls(sample, scope, "SingleMuTriggerFlags")
    for flag, path, min_pt in [("mu24", "IsoMu24", 25.0), ("mu27", "IsoMu27", 28.0)]:
        assert (
            f'"trg_single_{flag}", "p4_1", "TrigObj_pt", "TrigObj_eta", "TrigObj_phi", '
            f'"TrigObj_id", "TrigObj_filterBits", "HLT_{path}", {min_pt}, 2.5, 13, {{3}}, 0.4)'
        ) in flags
    assert flags.count("trigger::SingleObjectFlag(") == 2


@pytest.mark.parametrize("sample,producer,sf_type", [
    ("dyjets", "MTGenerateSingleMuonTriggerSF_MC", "mc"),
    ("embedding", "MTGenerateSingleMuonTriggerSF", "emb"),
])
@pytest.mark.parametrize("scope", SCOPES)
def test_trigger_sfs_are_the_kit_sfs_of_the_first_muon(sample, producer, sf_type, scope):
    sfs = calls(sample, scope, producer)
    for column, correction in TRIGGER_SFS.items():
        assert (
            f'"{column}", "pt_1", "eta_1", "data/embedding/muon_2018UL.json.gz", '
            f'"{correction}", "{sf_type}", 1.0)'
        ) in sfs
    assert "SingleMuTriggerSF" not in producer_names(measurement(sample), scope)


@pytest.mark.parametrize("scope,legs", [("mt", (1,)), ("mm", (1, 2))])
def test_mc_muon_id_iso_sfs_are_the_kit_mc_sfs(scope, legs):
    sfs = calls("dyjets", scope, "TauEmbeddingMuonIDIsoSF_MC")
    for leg in legs:
        for column, correction in [("id", "ID_pt_eta_bins"), ("iso", "Iso_pt_eta_bins")]:
            assert (
                f'"{column}_wgt_mu_{leg}", "pt_{leg}", "eta_{leg}", '
                f'"data/embedding/muon_2018UL.json.gz", "{correction}", "mc", 1.0)'
            ) in sfs
    assert "MuonIDIso_SF" not in producer_names(measurement("dyjets"), scope)


def test_mc_tau_corrections():
    """ES of vsJet Loose; vsJet SFs for Medium and Tight (vsEle VVLoose), vsEle SFs
    for VVLoose and Tight."""
    config = measurement("dyjets")
    params = parameters(config, "mt")
    assert (params["tau_ides_sf_vsjet_wp"], params["tau_ides_sf_vsele_wp"]) == (
        "Loose",
        "VVLoose",
    )
    assert [p["vsjet_wp"] for p in params["vsjet_tau_id_sf"]] == ["Medium", "Tight"]
    assert [p["vsele_wp"] for p in params["vsele_tau_id_sf"]] == ["VVLoose", "Tight"]
    outputs = generate_code(MODULE, "dyjets", scopes=SCOPES).outputs["mt"]
    assert {
        "id_wgt_tau_vsJet_Medium_2", "id_wgt_tau_vsJet_Tight_2",
        "id_wgt_tau_vsEle_VVLoose_2", "id_wgt_tau_vsEle_Tight_2",
        "id_tau_vsJet_Medium_2", "id_tau_vsJet_Tight_2",
        "id_tau_vsEle_VVLoose_2", "id_tau_vsEle_Tight_2", "id_tau_vsMu_Tight_2",
    } <= outputs


@pytest.mark.parametrize("scope", SCOPES)
def test_tag_and_probe_and_grid_columns(scope):
    """The selection, the weights and the ES grid ShapeSmith derives downstream."""
    needed = {
        f"{variable}_{leg}" for variable in ("pt", "eta", "phi", "mass", "q", "iso")
        for leg in (1, 2)
    } | {"met", "metphi", "mt_1", "m_vis", "pt_tautau", "extramuon_veto", "extraelec_veto"}
    if scope == "mt":
        needed |= {"tau_decaymode_2", "dilepton_veto"}
    for sample in SAMPLES:
        outputs = generate_code(MODULE, sample, scopes=SCOPES).outputs[scope]
        assert needed | {"trg_single_mu24", "trg_single_mu27"} <= outputs
        if sample != "data":
            assert {"gen_match_1", "gen_match_2", *TRIGGER_SFS} <= outputs


def test_embedding_taus_stay_uncorrected():
    """By-value ES of 1, no vsJet SF, the lowered pT threshold and no emb* shifts."""
    config = measurement("embedding", ("all",))
    params = parameters(config, "mt")
    assert find_producer(config, "mt", "TauPtCorrection").call.startswith(
        "embedding::tau::PtCorrection_byValue("
    )
    assert {params[f"tau_ES_shift_DM{dm}"] for dm in (0, 1, 10, 11)} == {1.0}
    assert params["tight_tau_min_pt"] == pytest.approx(20 / 1.2)
    assert not {o for o in output_names(config, "mt") if o.startswith("id_wgt_tau_vsJet")}
    assert not config.shifts["mt"] and not config.shifts["mm"]
    byvalue = calls("embedding", "mt", "TauPtCorrection")
    assert '"Tau_decayMode", 1.0, 1.0, 1.0, 1.0)' in byvalue


def test_mm_embedding_is_the_mu_to_mu_embedding():
    """EmbeddingGenPair 13/13, the ID/iso SFs of both muons and the selection SFs."""
    config = measurement("embedding")
    producers = producer_names(config, "mm")
    assert {"EmbeddingGenPair", "TauEmbeddingMuonIDIsoSF", "TauEmbeddingSelectionSF"} <= producers
    assert '"GenPart_pt", 23, 13, 13)' in calls("embedding", "mm", "EmbeddingGenPair")
    sfs = calls("embedding", "mm", "TauEmbeddingMuonIDIsoSF")
    for leg in (1, 2):
        for column, correction in [("id", "ID_pt_eta_bins"), ("iso", "Iso_pt_eta_bins")]:
            assert (
                f'"{column}_wgt_mu_{leg}", "pt_{leg}", "eta_{leg}", '
                f'"data/embedding/muon_2018UL.json.gz", "{correction}", "emb", 1.0)'
            ) in sfs
    outputs = generate_code(MODULE, "embedding", scopes=SCOPES).outputs["mm"]
    weights = {"emb_genweight", "emb_triggersel_wgt", "emb_idsel_wgt_1", "emb_idsel_wgt_2"}
    assert weights <= outputs


def test_every_nanoaod_input_exists_in_the_v15_embedding_files():
    """The muemb 2018A files carry the same 1476 branches as the mutau fixture."""
    branches = set(BRANCHES.read_text().split())
    assert not nanoaod_inputs(measurement("embedding", ("all",))) - branches


@pytest.mark.parametrize("scope", SCOPES)
def test_every_predecessor_shape_systematic_has_its_shifts(scope):
    shifts = shift_names(measurement("dyjets", ("all",)), scope)
    for family, bases in PREDECESSOR_SHIFTS.items():
        if scope == "mm" and family.startswith(MT_ONLY_FAMILIES):
            continue
        for base in bases:
            assert {f"{base}Up", f"{base}Down"} <= shifts, family
    if scope == "mt":
        for base in CORRELATED_VSJET_SHIFTS:
            assert {f"{base}Up", f"{base}Down"} <= shifts


def test_no_mc_shift_leaves_its_columns_nominal():
    """Every tau and trigger shift sets parameters its producer reads (the
    add_tauVariations vsJet, vsEle and vsMu shifts set keys no producer reads), and
    the POG muon SF shifts are gone with the POG SFs."""
    config = measurement("dyjets", ("all",))
    shifts = {name.removeprefix("__"): change for name, change in config.shifts["mt"].items()}
    pog_muon_sf_shifts = ("vsEle", "muonIdSF", "muonIsoSF", "singleMuTriggerSF")
    readers = {
        "vsJetTau": "TauIDVsJetSF2",
        "vsMuWheel": "TauIDVsMuSF2",
        "tauEs": "TauPtCorrectionMC",
        "singleMuonTriggerSF": "MTGenerateSingleMuonTriggerSF_MC",
    }
    for prefix, producer in readers.items():
        read = find_producer(config, "mt", producer).parameters["mt"]
        matching = {name: change for name, change in shifts.items() if name.startswith(prefix)}
        assert matching, prefix
        for name, change in matching.items():
            assert set(change) <= read, name
    assert not {name for name in shifts if name.startswith(pog_muon_sf_shifts)}


def test_pog_vsjet_components_are_not_nominal():
    """Each component key exists in the POG payload for its decay modes."""
    correctionlib = pytest.importorskip("correctionlib")
    config = measurement("dyjets")
    params = parameters(config, "mt")
    vsjet = correctionlib.CorrectionSet.from_file(params["tau_vsjet_es_sf_file"])[
        "DeepTau2018v2p5VSjet"
    ]
    for key, decay_modes in POG_TAU_VSJET_2018_COMPONENTS.values():
        for dm in decay_modes:
            for wp in ("Medium", "Tight"):
                nominal = vsjet.evaluate(30.0, dm, 5, wp, "VVLoose", "nom", "dm")
                for syst in (f"{key}_up", f"{key}_down"):
                    shifted = vsjet.evaluate(30.0, dm, 5, wp, "VVLoose", syst, "dm")
                    assert shifted != nominal, (syst, dm, wp)


def test_sample_list_covers_every_sample_type():
    """sample_list/README.md: sorted 2018 nicks, SingleMuon data, mutau and muemb
    embedding, and every sample type of the configuration."""
    analysis = Path(__file__).resolve().parents[1]
    database = analysis.parents[2] / "sample_database/nanoAOD_v15/datasets.json"
    if not database.is_file():
        pytest.skip("KingMaker's sample_database is required")
    datasets = json.loads(database.read_text())
    listed = (analysis / "sample_list/sm_2018_tau_id_measurement.txt").read_text()
    nicks = listed.splitlines()
    assert listed == "".join(f"{nick}\n" for nick in sorted(nicks))
    entries = [datasets[nick] for nick in nicks]
    assert {entry["era"] for entry in entries} == {"2018"}
    assert {entry["sample_type"] for entry in entries} == set(
        sm_tau_id_measurement_config.AVAILABLE_SAMPLES
    )
    for nick, entry in zip(nicks, entries):
        if entry["sample_type"] == "data":
            assert nick.startswith("SingleMuon_Run2018"), nick
        if entry["sample_type"] == "embedding":
            assert "_mutau_" in nick or "_muemb_" in nick, nick
    assert len(nicks) == 25
