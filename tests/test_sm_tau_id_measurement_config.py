"""The tau-ID SF and ES measurement configuration (sm_tau_id_measurement_config.py).

Its choices follow jvoss's measurement production SFs_EMB_Run2_04_08_26 (README
section "Tau-ID measurement"). Pinned here, because each fails silently otherwise:
the trigger and its SFs per era, the MC muon and tau corrections, the prefiring
weight, the uncorrected embedding taus with their lowered pT threshold, the mu -> mu
embedding in mm, the columns of the tau-leg trigger measurement, and MC shifts that
change what the predecessor's shape systematics need.
"""

import gzip
import json
from pathlib import Path

import pytest

from analysis_configurations.bbtautau import sm_tau_id_measurement_config, tau_id_measurement
from analysis_configurations.bbtautau.constants import ERAS_RUN2
from analysis_configurations.bbtautau.tests.helpers import (
    V15_EMBEDDING_BRANCHES,
    build,
    find_producer,
    generate_code,
    nanoaod_inputs,
    output_names,
    producer_names,
)

MODULE = "sm_tau_id_measurement_config"
SCOPES = ("mt", "mm")
SAMPLES = ("data", "dyjets", "embedding")
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CROWN = Path(__file__).resolve().parents[3]
TRIGGER_SFS = {
    "trg_wgt_single_mu24": "Trg_IsoMu24_pt_eta_bins",
    "trg_wgt_single_mu27": "Trg_IsoMu27_pt_eta_bins",
    "trg_wgt_single_mu24ormu27": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
}
# the single-muon triggers per era (v7 spec C13): flag -> (HLT path, min pT, max
# |eta|, filter bit); 2016 the IsoMu22 family with the bit of each path, 2017
# IsoMu27, 2018 as the measurement production; all matched within Delta R 0.1 (K8)
ERA_TRIGGERS = {
    **{
        era: {
            "trg_single_mu22": ("HLT_IsoMu22", 24.0, 2.4, 1),
            "trg_single_mu22_tk": ("HLT_IsoTkMu22", 24.0, 2.4, 3),
            "trg_single_mu22_eta2p1": ("HLT_IsoMu22_eta2p1", 24.0, 2.1, 1),
            "trg_single_mu22_eta2p1_tk": ("HLT_IsoTkMu22_eta2p1", 24.0, 2.1, 3),
        }
        for era in ("2016preVFP", "2016postVFP")
    },
    "2017": {"trg_single_mu27": ("HLT_IsoMu27", 29.0, 2.4, 1)},
    "2018": {
        "trg_single_mu24": ("HLT_IsoMu24", 25.0, 2.5, 3),
        "trg_single_mu27": ("HLT_IsoMu27", 28.0, 2.5, 3),
    },
}
ERA_TRIGGER_SFS = {
    "2016preVFP": {"trg_wgt_single_mu22": "Trg_pt_eta_bins"},
    "2016postVFP": {"trg_wgt_single_mu22": "Trg_pt_eta_bins"},
    "2017": {"trg_wgt_single_mu27": "Trg_IsoMu27_pt_eta_bins"},
    "2018": TRIGGER_SFS,
}
# the tau-leg trigger columns of mt (v7_tt_emb_trigger 12.4): flag -> (HLT path or
# None, filter bits); every flag with min pT 20, |eta| < 2.5, ID 15, Delta R 0.4
EMBEDDING_FILTERS = {
    "2016": {"trg_emb_ditau_l2_2": (None, (12,)), "trg_emb_ditau_final_2": (None, (1, 8))},
    "2017": {"trg_emb_ditau_l2_2": (None, (23,)), "trg_emb_ditau_final_2": (None, (6,))},
}
MONITOR_2017 = {
    "trg_mon_mu24tau35_tightiso_tightid_2": (
        "HLT_IsoMu24_eta2p1_TightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg_CrossL1", (2, 4, 9, 17)
    ),
    "trg_mon_mu24tau35_mediumiso_tightid_2": (
        "HLT_IsoMu24_eta2p1_MediumChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg_CrossL1", (1, 4, 9, 17)
    ),
    "trg_mon_mu24tau35_tightiso_2": (
        "HLT_IsoMu24_eta2p1_TightChargedIsoPFTau35_Trk1_eta2p1_Reg_CrossL1", (2, 9, 17)
    ),
}
TAU_LEG_FLAGS = {
    **{
        era: {
            "trg_mon_mu19tau32_mediso_2": (
                "HLT_IsoMu19_eta2p1_MediumIsoPFTau32_Trk1_eta2p1_Reg", (1, 5, 7)
            ),
            "trg_mon_mu19tau32_medcombiso_2": (
                "HLT_IsoMu19_eta2p1_MediumCombinedIsoPFTau32_Trk1_eta2p1_Reg", (1, 5, 7)
            ),
            **EMBEDDING_FILTERS["2016"],
        }
        for era in ("2016preVFP", "2016postVFP")
    },
    "2017": {**MONITOR_2017, **EMBEDDING_FILTERS["2017"]},
    "2018": {
        **MONITOR_2017,
        "trg_mon_mu24tau35_mediumiso_hps_2": (
            "HLT_IsoMu24_eta2p1_MediumChargedIsoPFTauHPS35_Trk1_eta2p1_Reg_CrossL1", (1, 5, 9, 17)
        ),
        **EMBEDDING_FILTERS["2017"],
    },
}
TRIGGER_OBJECT_BITS = {
    "2016preVFP": (1, 5, 7),
    "2016postVFP": (1, 5, 7),
    "2017": (9, 17),
    "2018": (9, 17),
}
TRIGGER_OBJECT_COLUMNS = {"trgobj_pt_2", "trgobj_l1pt_2", "trgobj_l1iso_2"}
# the regrouped JES sources of the common shifts; the predecessor's 28 individual
# sources are not produced
REGROUPED_JES_SOURCES = [
    "Absolute", "Absolute_2018", "BBEC1", "BBEC1_2018", "EC2", "EC2_2018",
    "FlavorQCD", "HF", "HF_2018", "RelativeBal", "RelativeSample_2018",
]
PT_BINS = ("20to40", "40to60", "60toInf")
# Shape systematics of the predecessor measurement (jvoss's synced shapes of
# SFs_EMB_Run2_04_08_26__full), family -> the CROWN shifts behind it. Weight-only
# families (CMS_fake_j, CMS_htt_ttbarShape) and the embedding ttbar contamination
# are built downstream from nominal columns and are listed in the README. The vsJet
# SF families have no shifts: the measurement measures the SF.
PREDECESSOR_SHIFTS = {
    "CMS_PileUp": ["CMS_pileup_2018"],
    "CMS_eff_m_trigger_Run2018": ["CMS_eff_m_trigger_2018"],
    **{f"CMS_eff_t_dm{dm}_Run2018": [] for dm in (0, 1, 10, 11)},
    **{
        f"CMS_fake_m_WH{wheel}_Run2018": [f"CMS_fake_t_DeepTau2018v2p5_VSmu_wheel{wheel}_2018"]
        for wheel in range(1, 6)
    },
    "CMS_res_met_Run2018": ["CMS_res_met_RecoilCalibration_2018"],
    "CMS_scale_met_Run2018": ["CMS_scale_met_RecoilCalibration_2018"],
    "CMS_scale_fake_m_Run2018": [
        f"CMS_scale_t_DeepTau2018v2p5_genMuon_wheel{wheel}_2018" for wheel in range(1, 6)
    ],
    "CMS_scale_met_unclustered_energy_Run2018": ["CMS_scale_met_unclustered_energy_2018"],
    **{
        f"CMS_scale_t_dm{dm}_Run2018": [
            f"CMS_scale_t_DeepTau2018v2p5_DM{dm}_pt{pt}_genTau_2018" for pt in PT_BINS
        ]
        for dm in (0, 1, 10, 11)
    },
    "CMS_scale_j_<source>": [f"CMS_scale_j_{source}" for source in REGROUPED_JES_SOURCES],
    # CMS_scale_j_HEMIssue_Run2018: replaced by the 2018 HEM flag hem_veto, which
    # vetoes the affected events (v7 spec E29, C20)
}
# families of the tau and the trigger, which the predecessor has in mt only
MT_ONLY_FAMILIES = (
    "CMS_eff_t", "CMS_scale_t", "CMS_fake_m", "CMS_scale_fake_m", "CMS_eff_m_trigger",
)


def measurement(sample, shifts=("none",), scopes=SCOPES, era="2018"):
    return build(MODULE, sample, era=era, scopes=tuple(scopes), shifts=shifts)


def parameters(config, scope):
    return config.config_parameters[scope]["nominal"]


def shift_names(config, scope):
    return {name.removeprefix("__") for name in config.shifts[scope]}


def calls(sample, scope, producer, era="2018"):
    """The generated calls of ``producer`` in ``scope``, whitespace collapsed."""
    source = generate_code(MODULE, sample, era=era, scopes=SCOPES).directory
    (path,) = source.rglob(f"src/{scope}/{producer}.cxx")
    return " ".join(path.read_text().split())


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("shifts", [("none",), ("all",)])
@pytest.mark.parametrize("sample", SAMPLES)
def test_builds_for_mt_and_mm(sample, shifts, era):
    config = measurement(sample, shifts, era=era)
    assert set(SCOPES) <= set(config.scopes)


def test_other_eras_raise():
    with pytest.raises(ValueError, match="era '2024'"):
        tau_id_measurement.setup(None, "2024", "dyjets", ["mt"])


@pytest.mark.parametrize("scopes", [["et"], ["mt", "tt"], ["em"]])
def test_other_scopes_raise(scopes):
    with pytest.raises(ValueError, match="only, got"):
        measurement("dyjets", scopes=scopes)


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("sample", SAMPLES)
@pytest.mark.parametrize("scope", SCOPES)
def test_single_muon_trigger_of_the_era(sample, scope, era):
    """2016 the IsoMu22 family with the bit of each path, 2017 IsoMu27 (analysis
    triggers), 2018 IsoMu24 || IsoMu27 as the measurement production (filter bit 3,
    |eta| < 2.5, 25/28 GeV); all matched within Delta R 0.1."""
    flags = calls(sample, scope, "SingleMuTriggerFlags", era)
    for flag, (path, min_pt, max_eta, bit) in ERA_TRIGGERS[era].items():
        assert (
            f'"{flag}", "p4_1", "TrigObj_pt", "TrigObj_eta", "TrigObj_phi", '
            f'"TrigObj_id", "TrigObj_filterBits", "{path}", {min_pt}, {max_eta}, 13, {{{bit}}}, 0.1)'
        ) in flags
    assert flags.count("trigger::SingleObjectFlag(") == len(ERA_TRIGGERS[era])


def test_trigger_tables_match_the_module():
    assert {
        era: {
            t["flagname"]: (t["hlt_path"], t["min_pt"], t["max_abs_eta"], t["filter_bit"])
            for t in triggers
        }
        for era, triggers in tau_id_measurement.TM_SINGLE_MUON_TRIGGERS.items()
    } == ERA_TRIGGERS
    assert tau_id_measurement.TM_KIT_TRIGGER_SFS == ERA_TRIGGER_SFS


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("sample,producer,sf_type", [
    ("dyjets", "KitSingleMuonTriggerSF", "mc"),
    ("embedding", "MTGenerateSingleMuonTriggerSF", "emb"),
])
@pytest.mark.parametrize("scope", SCOPES)
def test_trigger_sfs_are_the_kit_sfs_of_the_first_muon(sample, producer, sf_type, scope, era):
    """MC evaluates with the pT cap of a defective payload bin (2016preVFP: 199.9 GeV
    below |eta| 0.9, none elsewhere), embedding with the core function."""
    sfs = calls(sample, scope, producer, era)
    for column, correction in ERA_TRIGGER_SFS[era].items():
        cap = ""
        if sf_type == "mc":
            capped = (era, correction) == ("2016preVFP", "Trg_pt_eta_bins")
            cap = ", 199.9, 0.9" if capped else ", 1000.0, 0.0"
        assert (
            f'"{column}", "pt_1", "eta_1", "data/embedding/muon_{era}UL.json.gz", '
            f'"{correction}", "{sf_type}", 1.0{cap})'
        ) in sfs
    function = "kit_muon_trigger(" if sf_type == "mc" else "Scalefactor("
    assert sfs.count(function) == len(ERA_TRIGGER_SFS[era])
    assert "SingleMuTriggerSF" not in producer_names(measurement(sample, era=era), scope)
    payload = CROWN / f"data/embedding/muon_{era}UL.json.gz"
    corrections = {c["name"] for c in json.load(gzip.open(payload))["corrections"]}
    assert set(ERA_TRIGGER_SFS[era].values()) <= corrections


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("sample", ("dyjets", "ttbar", "data", "embedding"))
def test_prefiring_weight_of_mc(sample, era):
    """E11: the MC carries prefiring_wgt (L1PreFiringWeight_Nom) and its Up/Dn
    columns in every era, 2018 included (the muon part), with the shift
    CMS_ecal_prefiring_<year> (E34 exception of the measurement); data and
    embedding have none."""
    outputs = generate_code(MODULE, sample, era=era, scopes=SCOPES).outputs
    columns = {"prefiring_wgt", "L1PreFiringWeight_Up", "L1PreFiringWeight_Dn"}
    for scope in SCOPES:
        if sample in ("data", "embedding"):
            assert not columns & outputs[scope], scope
        else:
            assert columns <= outputs[scope], scope
    if sample in ("dyjets", "ttbar"):
        config = measurement(sample, ("all",), era=era)
        shifts = {name.removeprefix("__") for name in config.shifts["mt"]}
        year = era[:4]
        assert {f"CMS_ecal_prefiring_{year}Up", f"CMS_ecal_prefiring_{year}Down"} <= shifts
        assert {f"CMS_eff_m_trigger_{era}Up", f"CMS_eff_m_trigger_{era}Down"} <= shifts


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tau_leg_trigger_flag_tables(era):
    """12.4: the monitoring flags of the tau leg and the embedding di-tau filters per
    era (HLT path, bits, min pT 20, |eta| < 2.5, ID 15, Delta R 0.4); bits are
    integers below 30 (the core flags test 30 bits), no flag name twice."""
    params = measurement("dyjets", era=era).config_parameters["mt"]["nominal"]
    entries = params["tau_leg_monitor_trigger"] + params["tau_leg_embedding_filter"]
    names = [e["flagname"] for e in entries]
    assert len(names) == len(set(names))
    table = {}
    for entry in entries:
        bits = tuple(int(bit) for bit in str(entry["filter_bit"]).split(","))
        assert all(0 <= bit < 30 for bit in bits)
        assert (entry["min_pt"], entry["max_abs_eta"], entry["particle_id"], entry["match_max_delta_r"]) == (
            20.0, 2.5, 15, 0.4
        )
        table[entry["flagname"]] = (entry.get("hlt_path"), bits)
    assert table == TAU_LEG_FLAGS[era]
    assert params["tau_leg_trigobj_filter_bits"] == ", ".join(map(str, TRIGGER_OBJECT_BITS[era]))
    assert (params["tau_leg_trigobj_particle_id"], params["tau_leg_trigobj_max_delta_r"]) == (15, 0.4)


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tau_leg_hlt_paths_exist_in_the_era(era):
    """Every monitoring path is a branch of the era's v15 files (data, MC or
    embedding; the fixtures hold the HLT branches of the first file of every listed
    nick, tests/fixtures/make_hlt_fixtures.py), and MC has each 2016/2017 path and
    the 2018 HPS one (the 2018 MC and embedding have no non-HPS path)."""
    branches = {
        kind: set((FIXTURES / f"nanoaod_v15_{era}_{kind}_hlt.txt").read_text().split())
        for kind in ("data", "mc", "embedding")
    }
    for flag, (path, _) in TAU_LEG_FLAGS[era].items():
        if path is None:
            continue
        assert any(path in paths for paths in branches.values()), path
        if era != "2018" or "HPS" in path:
            assert path in branches["mc"], path


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tau_leg_bits_mean_what_the_columns_claim(era):
    """The bit numbers against the TrigObj_filterBits doc string of the era's files:
    2016 Medium(Comb)Iso, OverlapFilter IsoMu, L1-HLT matched, Dz and embedding
    di-tau bit 12; 2017/2018 the iso and ID bits, mu-tau, regional paths, charged
    iso di-tau and embedding di-tau bit 23."""
    meaning = json.loads((FIXTURES / "nanoaod_v15_trigobj_filterbits.json").read_text())[era]
    tau = {int(bit): text for bit, text in meaning["embedding"]["Tau"].items()}
    names = {
        "2016": {1: "Medium(Comb)Iso", 5: "OverlapFilter IsoMu", 7: "L1-HLT matched", 8: "Dz", 12: "di-tau"},
        "2017": {
            1: "MediumChargedIso", 2: "TightChargedIso", 4: "TightID OOSC photons", 5: "HPS",
            6: "charged iso di-tau", 9: "mu-tau", 17: "regional paths", 23: "di-tau",
        },
    }["2016" if era.startswith("2016") else "2017"]
    used = {bit for _, bits in TAU_LEG_FLAGS[era].values() for bit in bits} | set(TRIGGER_OBJECT_BITS[era])
    for bit in used:
        assert tau[bit].startswith(names[bit]), (bit, tau[bit])
    # the embedding bit exists in embedding files only
    data_tau = {int(bit) for bit in meaning["data"]["Tau"]}
    assert (12 if era.startswith("2016") else 23) not in data_tau


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("sample", SAMPLES)
def test_tau_leg_columns_are_written_in_mt(sample, era):
    outputs = generate_code(MODULE, sample, era=era, scopes=SCOPES).outputs
    assert set(TAU_LEG_FLAGS[era]) | TRIGGER_OBJECT_COLUMNS <= outputs["mt"]
    assert not (set(TAU_LEG_FLAGS[era]) | TRIGGER_OBJECT_COLUMNS) & outputs["mm"]
    objects = calls(sample, "mt", "MTTauLegTriggerObject", era)
    bits = ", ".join(map(str, TRIGGER_OBJECT_BITS[era]))
    for column, quantity, value_type in [
        ("trgobj_pt_2", "TrigObj_pt", "Float_t"),
        ("trgobj_l1pt_2", "TrigObj_l1pt", "Float_t"),
        ("trgobj_l1iso_2", "TrigObj_l1iso", "Int_t"),
    ]:
        assert (
            f'trigger::MatchedObjectQuantity<{value_type}>(df'
        ) in objects
        assert (
            f'"{column}", "p4_2", "TrigObj_eta", "TrigObj_phi", "TrigObj_id", '
            f'"TrigObj_filterBits", "{quantity}", 15, {{{bits}}}, 0.4)'
        ) in objects


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


@pytest.mark.parametrize("sample,applied", [("dyjets", True), ("wjets", True), ("ttbar", False)])
def test_recoil_correction_of_dy_and_w(sample, applied):
    assert parameters(measurement(sample), "mt")["apply_recoil_correction"] is applied


def test_no_btag_sf():
    """The measurement weights no b-tag SF, like the precedent."""
    outputs = generate_code(MODULE, "dyjets", scopes=SCOPES).outputs
    assert not {o for scope in SCOPES for o in outputs[scope] if o.startswith("btag_weight")}


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
    branches = set(V15_EMBEDDING_BRANCHES.read_text().split())
    assert not nanoaod_inputs(measurement("embedding", ("all",))) - branches


@pytest.mark.parametrize("scope", SCOPES)
def test_every_predecessor_shape_systematic_has_its_shifts(scope):
    shifts = shift_names(measurement("dyjets", ("all",)), scope)
    for family, bases in PREDECESSOR_SHIFTS.items():
        if scope == "mm" and family.startswith(MT_ONLY_FAMILIES):
            continue
        for base in bases:
            assert {f"{base}Up", f"{base}Down"} <= shifts, family


def test_no_mc_shift_leaves_its_columns_nominal():
    """Every tau, trigger and recoil shift sets parameters its producer reads, and
    there are no shifts of the vsJet SF the measurement measures nor of the POG muon
    SFs it replaces."""
    config = measurement("dyjets", ("all",))
    shifts = {name.removeprefix("__"): change for name, change in config.shifts["mt"].items()}
    readers = {
        "CMS_fake_t_DeepTau2018v2p5_VSe": "TauIDVsEleSF2",
        "CMS_fake_t_DeepTau2018v2p5_VSmu": "TauIDVsMuSF2",
        "CMS_scale_t_": "TauPtCorrectionMC",
        "CMS_eff_m_trigger": "KitSingleMuonTriggerSF",
        "CMS_scale_met_RecoilCalibration": "RecoilCorrectionMet",
        "CMS_res_met_RecoilCalibration": "RecoilCorrectionMet",
    }
    for prefix, producer in readers.items():
        read = find_producer(config, "mt", producer).parameters["mt"]
        matching = {name: change for name, change in shifts.items() if name.startswith(prefix)}
        assert matching, prefix
        for name, change in matching.items():
            assert set(change) <= read, name
    assert not {name for name in shifts if name.startswith(("CMS_eff_t_", "CMS_eff_m_i"))}


def test_only_the_mc_tau_energy_scale_shifts_match_cms_scale_t():
    """-DSHIFTS selects shifts by case-insensitive substring, so 'CMS_scale_t' must
    select the MC tau energy scale shifts and nothing else: genuine taus per decay
    mode and pT bin, electrons per decay mode and ECAL region, muons per wheel."""
    config = measurement("dyjets", ("all",))
    matching = {
        name: change for name, change in config.shifts["mt"].items() if "cms_scale_t" in name.lower()
    }
    assert len(matching) == 2 * (4 * 3 + 4 * 2 + 5)
    assert all(set(change) == {"tau_es_variation"} for change in matching.values())


# nicks of the measurement lists per era: data, MC, embedding
LIST_LENGTHS = {
    "2016preVFP": (5, 15, 10),
    "2016postVFP": (3, 15, 6),
    "2017": (5, 15, 10),
    "2018": (4, 15, 8),
}


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_sample_list_covers_every_sample_type(era):
    """sample_list/README.md: sorted nicks of the era, SingleMuon data, mutau and muemb
    embedding, W in jet bins, and every sample type of the configuration."""
    analysis = Path(__file__).resolve().parents[1]
    database = analysis.parents[2] / "sample_database/nanoAOD_v15/datasets.json"
    if not database.is_file():
        pytest.skip("KingMaker's sample_database is required")
    datasets = json.loads(database.read_text())
    listed = (analysis / f"sample_list/sm_{era}_tau_id_measurement.txt").read_text()
    nicks = listed.splitlines()
    assert listed == "".join(f"{nick}\n" for nick in sorted(set(nicks)))
    entries = [datasets[nick] for nick in nicks]
    assert {entry["era"] for entry in entries} == {era}
    assert {entry["sample_type"] for entry in entries} == set(
        sm_tau_id_measurement_config.AVAILABLE_SAMPLES
    )
    counts = {"data": 0, "mc": 0, "embedding": 0}
    for nick, entry in zip(nicks, entries):
        kind = entry["sample_type"] if entry["sample_type"] in counts else "mc"
        counts[kind] += 1
        if kind == "data":
            assert nick.startswith(f"SingleMuon_Run{era[:4]}"), nick
        if kind == "embedding":
            assert ("_mutau_" in nick or "_muemb_" in nick) and "_B_ver1_" not in nick, nick
        if entry["sample_type"] == "wjets":
            assert nick.startswith(("WJetsToLNu_0J_", "WJetsToLNu_1J_", "WJetsToLNu_2J_")), nick
        if entry["sample_type"] == "dyjets":
            assert not nick.startswith("DYJetsToLL_LHEFilterPtZ-"), nick
    assert tuple(counts.values()) == LIST_LENGTHS[era]