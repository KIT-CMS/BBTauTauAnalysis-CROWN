"""v7 corrections of the SM configurations in every Run-2 era (spec C11, C19, C20,
C22): the prefiring weight of MC with its Up/Dn columns, the jet propagation to the
MET in every sample type, the 2018 HEM flag in place of the HEM shift, and the
electron SFs at the supercluster eta. NMSSM keeps its legacy treatment.
"""
import gzip
import json
from pathlib import Path

import pytest

from analysis_configurations.bbtautau import common_config
from analysis_configurations.bbtautau.constants import ERAS_RUN2, SCOPES
from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    generate_code,
    output_names,
    pending,
    producer_names,
)

ALL_SCOPES = tuple(SCOPES)
TAU_SCOPES = ("et", "mt", "tt")
CROWN = Path(__file__).resolve().parents[3]
PREFIRING_COLUMNS = {"prefiring_wgt", "L1PreFiringWeight_Up", "L1PreFiringWeight_Dn"}


def scopes_of(sample):
    return TAU_SCOPES if sample == "embedding" else ALL_SCOPES


def sample_era_cases(samples):
    """``pytest.param`` per sample and era; sm_config builds the embedding of an era
    once its embedding tau payload exists (``pending``)."""
    return [
        pytest.param(
            sample,
            era,
            marks=pending(era, "tau_embedding_payloads") if sample == "embedding" else [],
            id=f"{sample}-{era}",
        )
        for sample in samples
        for era in ERAS_RUN2
    ]


def shift_names(config, scope="mt"):
    return {name.removeprefix("__") for name in config.shifts[scope]}


# --- C11: prefiring ---------------------------------------------------------------


@pytest.mark.parametrize(
    "sample,era", sample_era_cases(["ttbar", "dyjets", "hh2b2tau", "data", "embedding"])
)
def test_prefiring_weight_of_mc_with_its_columns(sample, era):
    """E11/C11: MC of every Run-2 era (2018: the muon part) carries prefiring_wgt
    (L1PreFiringWeight_Nom) and the NanoAOD Up/Dn columns in every scope; data and
    embedding carry neither and do not run the producer."""
    config = build("sm_config", sample, era=era, scopes=scopes_of(sample))
    mc = sample not in ("data", "embedding")
    assert ("PrefireWeight" in producer_names(config, "global")) == mc
    for scope in scopes_of(sample):
        assert (PREFIRING_COLUMNS <= output_names(config, scope)) == mc, scope
        assert not (PREFIRING_COLUMNS & output_names(config, scope)) or mc, scope
    if mc:
        producer = find_producer(config, "global", "PrefireWeight")
        assert [q.name for q in producer.get_inputs("global")] == ["L1PreFiringWeight_Nom"]


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("module", ["sm_config", "sm_btag_efficiency_config"])
def test_no_prefiring_shifts_in_the_nominal_productions(module, era):
    """E34: the SM productions are nominal; the datacards take CMS_prefiring as lnN
    from the Up/Dn columns, so no CROWN shift exists (the tau-ID measurement has
    them, test_sm_tau_id_measurement_config)."""
    config = build(module, "ttbar", era=era, shifts=("all",))
    assert not {s for s in shift_names(config) if "prefiring" in s}


def test_prefiring_columns_in_the_generated_code():
    outputs = generate_code("sm_config", "ttbar", era="2018", scopes=("mt", "ee")).outputs
    for scope in ("mt", "ee"):
        assert PREFIRING_COLUMNS <= outputs[scope], scope


@pytest.mark.parametrize("era", ["2017", "2018"])
def test_nmssm_keeps_the_legacy_prefiring(era):
    """NMSSM: the weight on every sample of 2016/2017 with its shifts, none in 2018,
    no columns."""
    for sample in ("ttbar", "data"):
        config = build("nmssm_config", sample, era=era)
        assert ("PrefireWeight" in producer_names(config, "global")) == (era == "2017")
        assert not PREFIRING_COLUMNS & output_names(config, "mt")
    shifts = shift_names(build("nmssm_config", "ttbar", era=era, shifts=("all",)))
    assert bool({s for s in shifts if "prefiring" in s}) == (era == "2017")


# --- C19: MET propagation ----------------------------------------------------------


@pytest.mark.parametrize("sample,era", sample_era_cases(["ttbar", "dyjets", "data", "embedding"]))
def test_jets_propagate_to_the_met_in_every_sample_type(sample, era):
    """E28/C19: the re-calibrated jets are propagated to the PuppiMET in data, MC and
    embedding alike (difference method, pT > t1jet_min_pt)."""
    config = build("sm_config", sample, era=era, scopes=("mt",))
    params = config.config_parameters["global"]["nominal"]
    assert params["propagate_jets_to_met"] is True
    assert params["t1jet_min_pt"] == 15.0
    producer = find_producer(config, "global", "MetJetCorrection")
    inputs = [q.name for q in producer.get_inputs("global")]
    assert inputs[:2] == ["met_p4_uncorrected", "Jet_correctedPt"] and "Jet_pt" in inputs


@pytest.mark.parametrize(
    "module,era",
    [
        pytest.param(
            module,
            era,
            marks=pending(era, "tau_embedding_payloads") if module == "sm_config" else [],
            id=f"{module}-{era}",
        )
        for module in ("sm_config", "sm_tau_id_measurement_config")
        for era in ERAS_RUN2
    ],
)
def test_embedding_jets_get_the_data_calibration(module, era):
    """C19 precondition: the embedded events (jets of the recorded event) get the same
    jet calibration as data: the data producers with the same JES tag and payload.
    The tau-ID measurement builds the embedding of every era; sm_config once the
    embedding tau payload of the era exists."""
    data = build(module, "data", era=era, scopes=("mt",))
    embedding = build(module, "embedding", era=era, scopes=("mt",))
    names = (
        "JetEnergyCorrectionData",
        "JetEnergyCorrectionDataRegressed",
        "Type1JetEnergyCorrectionData",
    )
    for config in (data, embedding):
        global_producers = producer_names(config, "global")
        assert set(names) <= global_producers
        assert not {"JetEnergyCorrectionMC", "Type1JetEnergyCorrectionMC"} & global_producers
    for producer in names:
        assert find_producer(data, "global", producer).call == find_producer(
            embedding, "global", producer
        ).call
    keys = ("ak4jet_jes_tag_data", "ak4jet_jec_file", "ak4jet_jec_algo", "ak4jet_reapply_jes")
    for key in keys:
        assert (
            data.config_parameters["global"]["nominal"][key]
            == embedding.config_parameters["global"]["nominal"][key]
        ), key


@pytest.mark.parametrize("sample,propagate", [("ttbar", True), ("data", False)])
def test_nmssm_propagates_in_simulation_only(sample, propagate):
    params = build("nmssm_config", sample).config_parameters["global"]["nominal"]
    assert params["propagate_jets_to_met"] is propagate


# --- C20: HEM flag 2018 ------------------------------------------------------------

HEM_PARAMETERS = {
    "hem_veto_jet_min_pt": 15.0,
    "hem_veto_jet_id_wp": 6,
    "hem_veto_min_eta": -3.0,
    "hem_veto_max_eta": -1.3,
    "hem_veto_min_phi": -1.57,
    "hem_veto_max_phi": -0.87,
    "hem_veto_first_run": 319077,
}


@pytest.mark.parametrize("sample", ["ttbar", "dyjets", "data", "embedding"])
def test_hem_flag_in_2018(sample):
    """E29/C20: in 2018 every sample type writes hem_veto in every scope; data and
    embedding by run, MC by the luminosity fraction of the runs from 319077 on."""
    config = build("sm_config", sample, era="2018", scopes=scopes_of(sample))
    producer = find_producer(config, "global", "HemVetoFlag")
    assert "xyh::vetoes::hem_veto(" in producer.call
    assert [q.name for q in producer.get_inputs("global")] == [
        "Jet_correctedPt", "Jet_eta", "Jet_phi", "Jet_ID", "run", "luminosityBlock", "event",
    ]
    for scope in scopes_of(sample):
        assert "hem_veto" in output_names(config, scope), scope
    params = config.config_parameters["global"]["nominal"]
    assert {key: params[key] for key in HEM_PARAMETERS} == HEM_PARAMETERS
    assert params["hem_veto_by_run"] is (sample in ("data", "embedding"))
    assert params["hem_veto_affected_fraction"] == common_config.HEM_AFFECTED_LUMI_FRACTION_2018


def test_hem_fraction_is_the_lumi_fraction_of_the_golden_json():
    """The MC fraction: recorded luminosity of the 2018 golden-JSON lumisections from
    run 319077 on over all of them, from the UL pileup JSON (38.75 of 59.82 /fb)."""
    pileup = Path(
        "/cvmfs/cms-griddata.cern.ch/cat/metadata/DC/Collisions18/2026-05-28/13TeV/"
        "PileUp/UltraLegacy/pileup_latest.txt"
    )
    if not pileup.is_file():
        pytest.skip("The 2018 pileup JSON requires CVMFS")
    golden = json.loads(
        (CROWN / "data/golden_json/Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt").read_text()
    )
    lumis = json.loads(pileup.read_text())
    total = affected = 0.0
    for run, ranges in golden.items():
        per_ls = {entry[0]: entry[1] for entry in lumis[run]}
        lumi = sum(per_ls[ls] for low, high in ranges for ls in range(low, high + 1))
        total += lumi
        affected += lumi if int(run) >= 319077 else 0.0
    assert affected / total == pytest.approx(common_config.HEM_AFFECTED_LUMI_FRACTION_2018, abs=1e-6)


@pytest.mark.parametrize("era", ["2016preVFP", "2016postVFP", "2017"])
@pytest.mark.parametrize("sample", ["ttbar", "data"])
def test_no_hem_flag_before_2018(sample, era):
    config = build("sm_config", sample, era=era, scopes=("mt", "ee"))
    assert "HemVetoFlag" not in producer_names(config, "global")
    assert "hem_veto" not in output_names(config, "mt")
    assert not {k for k in config.config_parameters["global"]["nominal"] if k.startswith("hem_veto")}


def test_hem_shift_replaced_by_the_flag():
    """The HEM jet energy scale shift is gone where the flag exists; NMSSM 2018 keeps
    the shift and has no flag."""
    sm = build("sm_config", "ttbar", era="2018", shifts=("all",))
    assert not {s for s in shift_names(sm) if "HEM" in s}
    assert {"CMS_scale_j_Absolute_2018Up", "CMS_res_j_2018Down"} <= shift_names(sm)
    nmssm = build("nmssm_config", "ttbar", era="2018", shifts=("all",))
    assert {"CMS_HEM_2018Up", "CMS_HEM_2018Down"} <= shift_names(nmssm)
    assert "HemVetoFlag" not in producer_names(build("nmssm_config", "ttbar"), "global")


def test_hem_flag_in_the_tau_id_measurement():
    config = build("sm_tau_id_measurement_config", "dyjets", era="2018", scopes=("mt", "mm"))
    for scope in ("mt", "mm"):
        assert "hem_veto" in output_names(config, scope), scope


# --- C22: electron SFs at the supercluster eta -----------------------------------

ELECTRON_SFS = {
    "et": ("Ele_1_Reco_SF_ScEta", "Ele_1_ID_SF_ScEta"),
    "em": ("Ele_1_Reco_SF_ScEta", "Ele_1_ID_SF_ScEta"),
    "ee": ("Ele_1_Reco_SF_ScEta", "Ele_2_Reco_SF_ScEta", "Ele_1_ID_SF_ScEta", "Ele_2_ID_SF_ScEta"),
}


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_electron_sfs_at_the_supercluster_eta(era):
    """K7/C22: the EGM reconstruction and ID SFs read sc_eta = eta + deltaEtaSC of the
    pair electron, written as sc_eta_1 (et, em, ee) and sc_eta_2 (ee)."""
    config = build("sm_config", "ttbar", era=era, scopes=tuple(ELECTRON_SFS))
    for scope, producers in ELECTRON_SFS.items():
        for name in producers:
            leg = name[len("Ele_")]
            inputs = [q.name for q in find_producer(config, scope, name).get_inputs(scope)]
            assert inputs == [f"pt_{leg}", f"sc_eta_{leg}", f"phi_{leg}"], (scope, name)
        assert not {"Ele_1_ID_SF", "Ele_1_Reco_SF"} & {
            p.name for p in find_producer(config, scope, "EleID_SF_ScEta").producers[scope]
        }
        sc = find_producer(config, scope, "electron_sc_eta_1")
        assert "xyh::electron::supercluster_eta(" in sc.call and sc.call.endswith(", 0)")
        assert [q.name for q in sc.get_inputs(scope)] == [
            "Electron_eta", "Electron_deltaEtaSC", "dileptonpair",
        ]
        expected = {"sc_eta_1", "sc_eta_2"} if scope == "ee" else {"sc_eta_1"}
        assert {o for o in output_names(config, scope) if o.startswith("sc_eta")} == expected


@pytest.mark.parametrize("sample", ["data", "embedding"])
def test_supercluster_eta_columns_without_the_pog_sfs(sample):
    """Data and embedding keep the sc_eta columns; they get no POG electron SF."""
    scopes = ("et",) if sample == "embedding" else ("et", "ee")
    config = build("sm_config", sample, era="2018", scopes=scopes)
    for scope in scopes:
        assert "sc_eta_1" in output_names(config, scope)
        assert "EleID_SF_ScEta" not in producer_names(config, scope)


def test_nmssm_keeps_the_electron_eta():
    config = build("nmssm_config", "ttbar", scopes=("et",))
    inputs = [q.name for q in find_producer(config, "et", "Ele_1_ID_SF").get_inputs("et")]
    assert inputs == ["pt_1", "eta_1", "phi_1"]
    assert not {o for o in output_names(config, "et") if o.startswith("sc_eta")}


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_egm_payload_bins_change_at_the_barrel_edge(era):
    """The reason for C22: the EGM ID and reco SFs of the era jump at |eta_SC| = 1.444
    and 1.566, so an electron whose eta and supercluster eta straddle the edge gets
    another SF."""
    correctionlib = pytest.importorskip("correctionlib")
    params = build("sm_config", "ttbar", era=era, scopes=("et",)).config_parameters["et"]["nominal"]
    cset = correctionlib.CorrectionSet.from_file(params["ele_sf_file"])[params["ele_sf_cset_name"]]
    year = params["ele_sf_year_id"]
    for wp in (params["ele_id_sf_name"], "RecoAbove20"):
        for below, above in ((1.440, 1.448), (1.560, 1.570)):
            assert cset.evaluate(year, "sf", wp, below, 40.0) != cset.evaluate(
                year, "sf", wp, above, 40.0
            ), (wp, below)
