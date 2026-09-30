"""Tau embedding on the Run-2 v15 inputs (embedding_run2_v15.py) for the SM 2018 analysis.

The contracts pinned here fail silently otherwise: a missing weight column, an MC
weight left in the embedding n-tuple, a correction read from the wrong payload or
working point, a tt trigger flag that never fires, a shift that changes nothing, or
a NanoAOD branch the v15 embedding files do not contain.
"""

from dataclasses import replace
import gzip
import json
import logging
from pathlib import Path
from unittest import mock

import pytest

from analysis_configurations.bbtautau import common_config, embedding_run2_v15
from analysis_configurations.bbtautau.analysis_profiles import NMSSM_PROFILE, SM_PROFILE
from analysis_configurations.bbtautau.constants import LEGACY_AVAILABLE_SAMPLES, SCOPES
from analysis_configurations.bbtautau.tests.helpers import (
    V15_EMBEDDING_BRANCHES,
    build,
    find_producer,
    generate_code,
    nanoaod_inputs,
    output_names,
    producer_names,
)

ANALYSIS = Path(__file__).resolve().parents[1]
CHANNELS = ("et", "mt", "tt")
POG_TAU_FILE = "/cvmfs/cms-griddata.cern.ch/cat/metadata/TAU/Run2-2018-UL-NanoAODv15/2025-11-27/tau.json.gz"
VSELE_WP = {"et": "Tight", "mt": "VVLoose", "tt": "VVLoose"}

EMBEDDING_WEIGHTS = {
    "emb_genweight",
    "emb_triggersel_wgt",
    "emb_idsel_wgt_1",
    "emb_idsel_wgt_2",
}
PRESENT = {
    "et": EMBEDDING_WEIGHTS
    | {
        "id_wgt_tau_vsJet_Medium_2",
        "id_wgt_ele_1",
        "iso_wgt_ele_1",
        "trg_wgt_single_ele32",
    },
    "mt": EMBEDDING_WEIGHTS
    | {
        "id_wgt_tau_vsJet_Medium_2",
        "id_wgt_mu_1",
        "iso_wgt_mu_1",
        "trg_wgt_single_mu24",
    },
    "tt": EMBEDDING_WEIGHTS
    | {"id_wgt_tau_vsJet_Medium_1", "id_wgt_tau_vsJet_Medium_2"}
    | {
        f"trg_wgtdouble_tau{trigger}_leg{leg}"
        for trigger in ("35_mediumiso", "35_tightiso", "40_mediumiso", "40_tightiso")
        for leg in (1, 2)
    },
}
ABSENT = {"puweight", "lhe_scale_weight", "reco_wgt_ele_1", "btag_weight_upart"}


def embedding(shifts=("none",)):
    return build("sm_config", "embedding", scopes=CHANNELS, shifts=shifts)


def build_profile(profile, scopes, shifts=("none",)):
    """``build()`` for a profile that no config module uses."""
    logging.disable(logging.CRITICAL)
    try:
        return common_config.build_config(
            profile,
            "2018",
            "embedding",
            list(scopes),
            set(shifts),
            LEGACY_AVAILABLE_SAMPLES,
            ["2018"],
            SCOPES,
        )
    finally:
        logging.disable(logging.NOTSET)


def parameters(config, scope):
    return config.config_parameters[scope]["nominal"]


def shifts_of(config, scope):
    """Shift name (without the ``__`` column prefix) -> changed parameters."""
    return {
        name.removeprefix("__"): change for name, change in config.shifts[scope].items()
    }


@pytest.mark.parametrize(
    "era,scopes",
    [("2018", ["em"]), ("2018", ["ee"]), ("2018", ["mt", "mm"]), ("2017", ["mt"])],
)
def test_requests_outside_the_profile_raise(era, scopes):
    with pytest.raises(ValueError, match="'2017'" if era == "2017" else "only, got"):
        embedding_run2_v15.setup(None, SM_PROFILE, era, scopes)


def test_every_nanoaod_input_exists_in_the_v15_embedding_files():
    """Branch list of one v15 embedding file (mutau 2018A nano_1; eltau and tautau
    carry the same 1476 branches)."""
    branches = set(V15_EMBEDDING_BRANCHES.read_text().split())
    assert not nanoaod_inputs(embedding(shifts=("all",))) - branches


@pytest.mark.parametrize("scope", CHANNELS)
def test_output_contract(scope):
    # generated, because vector producers name their output columns only then
    outputs = generate_code("sm_config", "embedding", scopes=CHANNELS).outputs[scope]
    assert PRESENT[scope] <= outputs, PRESENT[scope] - outputs
    assert not ABSENT & outputs
    assert "is_embedding" in outputs and "genWeight" in outputs


@pytest.mark.parametrize("scope", CHANNELS)
def test_tau_corrections_read_the_embedding_payload_with_the_analysis_working_points(
    scope,
):
    config = embedding()
    params = parameters(config, scope)
    assert params["tau_vsjet_es_sf_file"] == embedding_run2_v15.TAU_PAYLOAD
    assert (params["tau_ides_sf_vsjet_wp"], params["tau_ides_sf_vsele_wp"]) == (
        "Medium",
        VSELE_WP[scope],
    )
    assert [p["vsjet_wp"] for p in params["vsjet_tau_id_sf"]] == ["Medium"]
    assert (params["tau_ES_json_name"], params["tau_id_sf_vsjet_sf_dependence"]) == (
        "tau_energy_scale",
        "pt",
    )
    # vsE/vsMu stay with the POG SFs, which are 1 for genuine taus
    assert params["tau_ides_sf_file"] == POG_TAU_FILE
    for name in ("TauPtCorrectionMC", "TauIDVsJetSF2"):
        assert (
            "tau_vsjet_es_sf_file"
            in find_producer(config, scope, name).parameters[scope]
        )
    for name in ("TauIDVsEleSF2", "TauIDVsMuSF2"):
        assert (
            "tau_ides_sf_file" in find_producer(config, scope, name).parameters[scope]
        )


def test_event_level_and_lepton_scale_factors():
    config = embedding()
    assert "Flag_BadPFMuonDzFilter" not in parameters(config, "global")["met_filters"]
    # the electron energy scale stays the MC EGM scale and smearing
    assert "ElectronPtCorrectionMC" in {p.name for p in config.producers["global"]}
    assert parameters(config, "et")["electron_trigger_sf_type"] == "emb"
    assert "TauEmbeddingElectronIDIsoSF" in producer_names(config, "et")
    assert "EleID_SF" not in producer_names(config, "et")
    assert "TauEmbeddingMuonIDIsoSF" in producer_names(config, "mt")
    assert not {"MuonIDIso_SF", "SingleMuTriggerSF"} & producer_names(config, "mt")
    tt = parameters(config, "tt")
    assert (tt["tau_trigger_sf_file"], tt["tau_trigger_cset_name"]) == (
        "data/embedding/tau_trigger2018_UL.json.gz",
        "tauTriggerSF",
    )
    for scope in CHANNELS:
        assert "EmbeddingGenPair" in producer_names(config, scope)
        assert not {"gen_taujet_pt_1", "gen_taujet_pt_2"} & producer_names(
            config, scope
        )


def test_rendered_calls_of_the_embedding_producers():
    """The iso-binned SFs and the tt trigger flags pass C++ vectors, so their calls are
    checked as generated: iso edges and corrections per flavour with its eta
    convention, and the ditau flags matched to filter bit 23 without an HLT path,
    ahead of the trigger SF."""
    src = generate_code("sm_config", "embedding", scopes=CHANNELS).directory
    text = {path.stem: path.read_text() for path in src.rglob("src/*/*.cxx")}
    muon = " ".join(text["TauEmbeddingMuonIDIsoSF"].split())
    assert (
        '"iso_1", "data/embedding/muon_2018UL.json.gz", {0.15, 0.25}, '
        '{"Iso_pt_eta_bins", "AIso1_pt_eta_bins", "AIso2_pt_eta_bins"}, "emb", 1.0, true)'
    ) in muon
    electron = " ".join(text["TauEmbeddingElectronIDIsoSF"].split())
    assert (
        '"iso_1", "data/embedding/electron_2018UL.json.gz", {0.15}, '
        '{"Iso_pt_eta_bins", "AIso_pt_eta_bins"}, "emb", 1.0, false)'
    ) in electron
    flags_and_sf = text["TauTauTriggerFlagsAndSFEmbedding"]
    flags = flags_and_sf[: flags_and_sf.index("scalefactor::Trigger(")]
    assert flags.count("trigger::DoubleObjectFlag(") == 4
    assert flags.count("15, 15, {23}, {23}, 0.4)") == 4 and "HLT_" not in flags


def expected_shifts(scope):
    """The payload tau shifts, one per decay mode (and pT bin for the vsJet SF); tt,
    which selects taus above 40 GeV, carries no 20-40 GeV vsJet shifts."""
    pt_bins = ("40toInf",) if scope == "tt" else ("20to40", "40toInf")
    shifts = {}
    for direction in ("Up", "Down"):
        value = direction.lower()
        for dm in (0, 1, 10, 11):
            shifts[f"CMS_scale_t_emb_DeepTau2018v2p5_DM{dm}_2018{direction}"] = {
                "tau_es_variation": f"{value}_custom_genTau_dm{dm}"
            }
            for pt in pt_bins:
                shifts[f"CMS_eff_t_emb_DeepTau2018v2p5_VSjet_DM{dm}_pt{pt}_2018{direction}"] = {
                    "tau_id_sf_vsjet_variation": f"{value}_custom_dm{dm}_pt{pt}"
                }
    return shifts


@pytest.mark.parametrize("scope", CHANNELS)
def test_embedding_shifts_are_the_payload_tau_shifts_and_reach_their_producers(scope):
    config = embedding(shifts=("all",))
    shifts = shifts_of(config, scope)
    assert shifts == expected_shifts(scope)
    es_reader = find_producer(config, scope, "TauPtCorrectionMC").parameters[scope]
    vsjet_readers = [
        find_producer(config, scope, name).parameters[scope]
        for name in (
            ["TauIDVsJetSF1", "TauIDVsJetSF2"] if scope == "tt" else ["TauIDVsJetSF2"]
        )
    ]
    for name, change in shifts.items():
        for reader in [es_reader] if name.startswith("CMS_scale_t_emb") else vsjet_readers:
            assert set(change) <= reader, name


def test_tau_payload_contract():
    """The two corrections read from the payload cover the analysis working points and
    are 1 for every tau that is not a genuine hadronic tau."""
    correctionlib = pytest.importorskip("correctionlib")
    payload = ANALYSIS / embedding_run2_v15.TAU_PAYLOAD
    corrections = correctionlib.CorrectionSet.from_file(str(payload))
    names = {c["name"] for c in json.load(gzip.open(payload))["corrections"]}
    assert {"DeepTau2018v2p5VSjet", "tau_energy_scale"} <= names
    vsjet, es = corrections["DeepTau2018v2p5VSjet"], corrections["tau_energy_scale"]
    for vsele in ("VVLoose", "Tight"):
        for syst in ("nom", "up", "down"):
            for dm in (0, 1, 10, 11):
                assert vsjet.evaluate(45.0, dm, 5, "Medium", vsele, syst, "pt") > 0
                assert (
                    es.evaluate(
                        45.0, 1.0, dm, 5, "DeepTau2018v2p5", "Medium", vsele, syst
                    )
                    > 0
                )
                for genmatch in (0, 1, 2, 3, 4, 6):
                    assert (
                        vsjet.evaluate(45.0, dm, genmatch, "Medium", vsele, syst, "pt")
                        == 1.0
                    )
                    assert (
                        es.evaluate(
                            45.0,
                            1.0,
                            dm,
                            genmatch,
                            "DeepTau2018v2p5",
                            "Medium",
                            vsele,
                            syst,
                        )
                        == 1.0
                    )


def test_nmssm_embedding_keeps_the_legacy_setup():
    with mock.patch.object(common_config, "setup_embedding") as legacy:
        build_profile(NMSSM_PROFILE, ["mt"])
    legacy.assert_called_once()


def test_profile_restricts_the_embedding_scopes():
    profile = replace(SM_PROFILE, embedding_scopes=("mt",))
    build_profile(profile, ["mt"])
    with pytest.raises(ValueError, match=r"\['et'\]"):
        build_profile(profile, ["et", "mt"])


def test_profile_without_tau_corrections():
    """No payload energy scale (a factor 1), no vsJet SF and no payload tau shifts."""
    config = build_profile(
        replace(SM_PROFILE, embedding_tau_corrections=False), CHANNELS, ("all",)
    )
    for scope in CHANNELS:
        assert not config.shifts[scope]
        correction = find_producer(config, scope, "TauPtCorrection")
        assert correction.call.startswith("embedding::tau::PtCorrection_byValue(")
        assert {
            parameters(config, scope)[f"tau_ES_shift_DM{dm}"] for dm in (0, 1, 10, 11)
        } == {1.0}
        assert not {
            o for o in output_names(config, scope) if o.startswith("id_wgt_tau_vsJet")
        }


def test_profile_lowers_the_embedding_tau_pt_threshold():
    config = build_profile(replace(SM_PROFILE, embedding_min_tau_pt=20 / 1.2), ["mt"])
    assert parameters(config, "mt")["tight_tau_min_pt"] == pytest.approx(
        16.667, abs=1e-3
    )


def test_embedding_sample_list_follows_its_rule():
    """sample_list/README.md: the sorted eltau/mutau/tautau 2018 embedding nicks."""
    database = ANALYSIS.parents[2] / "sample_database/nanoAOD_v15/datasets.json"
    if not database.is_file():
        pytest.skip("KingMaker's sample_database is required")
    datasets = json.loads(database.read_text())
    nicks = sorted(
        nick
        for nick, entry in datasets.items()
        if entry["sample_type"] == "embedding"
        and entry["era"] == "2018"
        and any(token in nick for token in ("_eltau_", "_mutau_", "_tautau_"))
    )
    assert len(nicks) == 12
    listed = (ANALYSIS / "sample_list/sm_2018_embedding.txt").read_text()
    assert listed == "".join(f"{nick}\n" for nick in nicks)
