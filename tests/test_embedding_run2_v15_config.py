"""Tau embedding on the Run-2 v15 inputs (embedding_run2_v15.py) for the SM analysis.

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
from analysis_configurations.bbtautau.constants import ERAS_RUN2, LEGACY_AVAILABLE_SAMPLES, SCOPES
from analysis_configurations.bbtautau.tau_triggersetup import (
    KIT_SINGLE_ELECTRON_TRIGGER_SFS,
    KIT_SINGLE_MUON_TRIGGER_SFS,
)
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
CROWN = ANALYSIS.parents[1]
CHANNELS = ("et", "mt", "tt")
POG_TAU_FILE = "/cvmfs/cms-griddata.cern.ch/cat/metadata/TAU/Run2-{era}-UL-NanoAODv15/2025-11-27/tau.json.gz"
TAU_PAYLOAD = embedding_run2_v15.TAU_EMBEDDING_ID_ES_PAYLOADS["2018"]
# the corrected embedding without its tau payload: builds in every era
UNCORRECTED = replace(SM_PROFILE, embedding_tau_corrections=False)
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
    # E33: the data efficiency of the di-tau leg per tau and isolation class, and the
    # filter-bit flags as diagnostics
    | {f"trg_effdata_emb_{iso}_{leg}" for iso in ("Medium", "AntiMedium") for leg in (1, 2)}
    | {
        f"trg_double_tau{trigger}"
        for trigger in ("35_mediumiso", "35_tightiso", "40_mediumiso", "40_tightiso")
    },
}
ABSENT = {"puweight", "lhe_scale_weight", "reco_wgt_ele_1", "btag_weight_upart"}
# no MC trigger SF of the tt embedding (E33)
ABSENT_TT = {
    f"trg_wgtdouble_tau{trigger}_leg{leg}"
    for trigger in ("35_mediumiso", "35_tightiso", "40_mediumiso", "40_tightiso")
    for leg in (1, 2)
}


def embedding(shifts=("none",)):
    # 2018: the only era with an embedding tau ID/ES payload so far (PENDING)
    return build("sm_config", "embedding", era="2018", scopes=CHANNELS, shifts=shifts)


def build_profile(profile, scopes, shifts=("none",), era="2018"):
    """``build()`` for a profile that no config module uses."""
    logging.disable(logging.CRITICAL)
    try:
        return common_config.build_config(
            profile,
            era,
            "embedding",
            list(scopes),
            set(shifts),
            LEGACY_AVAILABLE_SAMPLES,
            list(ERAS_RUN2),
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
    "era,scopes,message",
    [
        ("2018", ["em"], "only, got"),
        ("2018", ["ee"], "only, got"),
        ("2018", ["mt", "mm"], "only, got"),
        ("2024", ["mt"], "era '2024'"),
    ],
)
def test_requests_outside_the_profile_raise(era, scopes, message):
    with pytest.raises(ValueError, match=message):
        embedding_run2_v15.setup(None, SM_PROFILE, era, scopes)


def test_an_era_without_its_tau_payload_raises(monkeypatch):
    """The SM corrects the embedded taus: an era without its tau payload raises
    (every Run-2 era has one, so the table is patched)."""
    payloads = dict(embedding_run2_v15.TAU_EMBEDDING_ID_ES_PAYLOADS)
    del payloads["2017"]
    monkeypatch.setattr(embedding_run2_v15, "TAU_EMBEDDING_ID_ES_PAYLOADS", payloads)
    with pytest.raises(ValueError, match="No embedding tau ID/ES payload for era '2017'"):
        embedding_run2_v15.setup(None, SM_PROFILE, "2017", ["mt"])


def test_only_the_eff_data_tt_trigger_is_implemented():
    with pytest.raises(ValueError, match="variant B"):
        embedding_run2_v15.setup(None, replace(SM_PROFILE, tt_embedding_trigger="sf"), "2018", ["tt"])


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_payload_table_of_the_era(era):
    """C12: one entry per era, with the files of the era and corrections they hold;
    the trigger SFs are those of the analysis triggers of MC (E5, E6)."""
    payloads = embedding_run2_v15.KIT_EMBEDDING_PAYLOADS[era]
    assert payloads.selection == f"data/embedding/embeddingselection_{era}UL.json.gz"
    assert payloads.muon == f"data/embedding/muon_{era}UL.json.gz"
    assert payloads.electron == f"data/embedding/electron_{era}UL.json.gz"
    assert payloads.muon_trigger_sfs == KIT_SINGLE_MUON_TRIGGER_SFS[era]
    assert payloads.electron_trigger_sfs == KIT_SINGLE_ELECTRON_TRIGGER_SFS[era]
    names = {
        path: {c["name"] for c in json.load(gzip.open(CROWN / path))["corrections"]}
        for path in (payloads.selection, payloads.muon, payloads.electron)
    }
    assert {"m_sel_trg_kit_ratio", "EmbID_pt_eta_bins"} <= names[payloads.selection]
    assert {"ID_pt_eta_bins", "Iso_pt_eta_bins", "AIso1_pt_eta_bins", "AIso2_pt_eta_bins"} | set(
        payloads.muon_trigger_sfs.values()
    ) <= names[payloads.muon]
    assert {"ID90_pt_eta_bins", "Iso_pt_eta_bins", "AIso_pt_eta_bins"} | set(
        payloads.electron_trigger_sfs.values()
    ) <= names[payloads.electron]
    # only the 2018 v15 embedding files lack Flag_BadPFMuonDzFilter
    assert payloads.missing_met_filters == (("Flag_BadPFMuonDzFilter",) if era == "2018" else ())


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_embedding_reads_the_payloads_of_its_era(era):
    """No file of another era: the selection, lepton and trigger SFs, the MET filters
    and the di-tau trigger efficiency of the era's tables (built without the tau
    payload, which only 2018 has so far)."""
    config = build_profile(UNCORRECTED, CHANNELS, era=era)
    payloads = embedding_run2_v15.KIT_EMBEDDING_PAYLOADS[era]
    filters = parameters(config, "global")["met_filters"]
    assert ("Flag_BadPFMuonDzFilter" in filters) == (era != "2018")
    for scope in CHANNELS:
        assert parameters(config, scope)["embedding_selection_sf_file"] == payloads.selection
    mt, et, tt = (parameters(config, scope) for scope in ("mt", "et", "tt"))
    assert mt["embedding_muon_sf_file"] == payloads.muon
    assert {e["flagname"]: e["embedding_trigger_sf"] for e in mt["singlemuon_trigger_sf"]} == (
        payloads.muon_trigger_sfs
    )
    assert et["embedding_electron_sf_file"] == payloads.electron
    assert et["mc_electron_sf_file"] == payloads.electron
    assert et["electron_trigger_sf_type"] == "emb"
    assert {e["flagname"]: e["mc_trigger_sf"] for e in et["singlelectron_trigger_sf_mc"]} == (
        payloads.electron_trigger_sfs
    )
    assert tt["tt_embedding_trigger_eff_file"] == POG_TAU_FILE.format(era=era)
    for scope in CHANNELS:
        for key, value in parameters(config, scope).items():
            if key.startswith(("embedding_", "tt_embedding_")) and str(value).endswith(".json.gz"):
                assert era in value, (scope, key, value)


def test_every_nanoaod_input_exists_in_the_v15_embedding_files():
    """Branch list of one v15 embedding file (mutau 2018A nano_1; eltau and tautau
    carry the same 1476 branches)."""
    branches = set(V15_EMBEDDING_BRANCHES.read_text().split())
    assert not nanoaod_inputs(embedding(shifts=("all",))) - branches


@pytest.mark.parametrize("scope", CHANNELS)
def test_output_contract(scope):
    # generated, because vector producers name their output columns only then
    outputs = generate_code("sm_config", "embedding", era="2018", scopes=CHANNELS).outputs[scope]
    assert PRESENT[scope] <= outputs, PRESENT[scope] - outputs
    assert not (ABSENT | ABSENT_TT) & outputs
    assert "is_embedding" in outputs and "genWeight" in outputs


@pytest.mark.parametrize("scope", CHANNELS)
def test_tau_corrections_read_the_embedding_payload_with_the_analysis_working_points(
    scope,
):
    config = embedding()
    params = parameters(config, scope)
    assert params["tau_vsjet_es_sf_file"] == TAU_PAYLOAD
    assert (params["tau_ides_sf_vsjet_wp"], params["tau_ides_sf_vsele_wp"]) == (
        "Medium",
        VSELE_WP[scope],
    )
    assert [p["vsjet_wp"] for p in params["vsjet_tau_id_sf"]] == ["Medium"]
    assert (params["tau_ES_json_name"], params["tau_id_sf_vsjet_sf_dependence"]) == (
        "tau_energy_scale_dm_binned",
        "dm",
    )
    # vsE/vsMu stay with the POG SFs, which are 1 for genuine taus
    assert params["tau_ides_sf_file"] == POG_TAU_FILE.format(era="2018")
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
    # E33: no KIT tt trigger file, the POG eff_data of the era instead
    tt = parameters(config, "tt")
    assert (tt["tau_trigger_sf_file"], tt["tau_trigger_cset_name"]) == (
        POG_TAU_FILE.format(era="2018"),
        "tau_trigger",
    )
    assert "TauTauTriggerFlagsAndEffDataEmbedding" in producer_names(config, "tt")
    assert not {"TauTauTriggerFlags", "DoubleTauTauTriggerSF"} & producer_names(config, "tt")
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
    src = generate_code("sm_config", "embedding", era="2018", scopes=CHANNELS).directory
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
    flags_and_efficiency = text["TauTauTriggerFlagsAndEffDataEmbedding"]
    flags = flags_and_efficiency[: flags_and_efficiency.index("scalefactor::Trigger(")]
    assert flags.count("trigger::DoubleObjectFlag(") == 4
    assert flags.count("15, 15, {23}, {23}, 0.4)") == 4 and "HLT_" not in flags
    # E33: eps_data of both legs in both isolation classes, from the flag-free
    # overload (no trigger requirement)
    efficiency = " ".join(flags_and_efficiency[len(flags):].split())
    for leg in (1, 2):
        for iso, wp in (("Medium", "Medium"), ("AntiMedium", "VVVLoose")):
            assert (
                f'"trg_effdata_emb_{iso}_{leg}", "pt_{leg}", "tau_decaymode_{leg}", '
                f'"{POG_TAU_FILE.format(era="2018")}", "tau_trigger", "ditau", "{wp}", '
                '"eff_data", "nom")'
            ) in efficiency
    assert efficiency.count("scalefactor::Trigger(") == 4


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tt_embedding_filter_bits_of_the_era(era):
    """E7: the diagnostic flags match TauEmbeddingSamplesUL's bits, 2016 the final
    filter (1 and 8), 2017 and 2018 the L2 filter bit 23, without HLT path."""
    config = build_profile(UNCORRECTED, ["tt"], era=era)
    flags = parameters(config, "tt")["tautau_trigger_embedding"]
    expected = "1, 8" if era.startswith("2016") else 23
    assert flags and {(f["p1_filter_bit"], f["p2_filter_bit"]) for f in flags} == {(expected, expected)}
    assert [f["flagname"] for f in flags] == [
        f["flagname"] for f in parameters(build("sm_config", "dyjets", era=era, scopes=("tt",)), "tt")["tautau_trigger"]
    ]


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tt_embedding_trigger_efficiencies_evaluate(era):
    """12.6: every combination the consumer books (working point of each isolation
    class, eff_data, decay mode, nominal) evaluates without exception in the tt
    acceptance -- the flag-free overload would return 1 silently otherwise."""
    correctionlib = pytest.importorskip("correctionlib")
    efficiency = embedding_run2_v15.TT_EMBEDDING_TRIGGER_EFFICIENCIES[era]
    path = efficiency.file or POG_TAU_FILE.format(era=era)
    if not Path(path).is_file():
        pytest.skip("TAU payloads require CVMFS")
    correction = correctionlib.CorrectionSet.from_file(path)[efficiency.correction]
    assert set(efficiency.working_points) == {"Medium", "AntiMedium"}
    for wp in efficiency.working_points.values():
        for dm in (0, 1, 10, 11):
            for pt in (40.0, 60.0, 150.0, 1000.0):
                value = correction.evaluate(pt, dm, "ditau", wp, "eff_data", "nom")
                assert 0 < value <= 1, (wp, dm, pt, value)


def expected_shifts():
    """The payload tau shifts, one per decay mode."""
    shifts = {}
    for direction in ("Up", "Down"):
        value = direction.lower()
        for dm in (0, 1, 10, 11):
            shifts[f"CMS_scale_t_emb_DeepTau2018v2p5_DM{dm}_2018{direction}"] = {
                "tau_es_variation": f"{value}_custom_genTau_dm{dm}"
            }
            shifts[f"CMS_eff_t_emb_DeepTau2018v2p5_VSjet_DM{dm}_2018{direction}"] = {
                "tau_id_sf_vsjet_variation": f"{value}_custom_dm{dm}"
            }
    return shifts


@pytest.mark.parametrize("scope", CHANNELS)
def test_embedding_shifts_are_the_payload_tau_shifts_and_reach_their_producers(scope):
    config = embedding(shifts=("all",))
    shifts = shifts_of(config, scope)
    assert shifts == expected_shifts()
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


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tau_payload_contract(era):
    """The two corrections read from the payload of every era cover the analysis
    working points, are flat in pT (no step at 40 GeV), and are 1 for every tau that
    is not a genuine hadronic tau."""
    correctionlib = pytest.importorskip("correctionlib")
    payload = ANALYSIS / embedding_run2_v15.TAU_EMBEDDING_ID_ES_PAYLOADS[era]
    corrections = correctionlib.CorrectionSet.from_file(str(payload))
    names = {c["name"] for c in json.load(gzip.open(payload))["corrections"]}
    assert {"DeepTau2018v2p5VSjet", "tau_energy_scale_dm_binned"} <= names
    vsjet = corrections["DeepTau2018v2p5VSjet"]
    es = corrections["tau_energy_scale_dm_binned"]
    for vsele in ("VVLoose", "Tight"):
        for syst in ("nom", "up", "down"):
            for dm in (0, 1, 10, 11):
                assert {
                    vsjet.evaluate(pt, dm, 5, "Medium", vsele, syst, "dm")
                    for pt in (25.0, 39.9, 40.1, 100.0)
                } == {vsjet.evaluate(45.0, dm, 5, "Medium", vsele, syst, "dm")}
                assert vsjet.evaluate(45.0, dm, 5, "Medium", vsele, syst, "dm") > 0
                assert {
                    es.evaluate(pt, 1.0, dm, 5, "DeepTau2018v2p5", "Medium", vsele, syst)
                    for pt in (25.0, 39.9, 40.1, 100.0)
                } == {
                    es.evaluate(45.0, 1.0, dm, 5, "DeepTau2018v2p5", "Medium", vsele, syst)
                }
                assert (
                    es.evaluate(
                        45.0, 1.0, dm, 5, "DeepTau2018v2p5", "Medium", vsele, syst
                    )
                    > 0
                )
                for genmatch in (0, 1, 2, 3, 4, 6):
                    assert (
                        vsjet.evaluate(45.0, dm, genmatch, "Medium", vsele, syst, "dm")
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


EMBEDDING_LENGTHS = {"2016preVFP": 15, "2016postVFP": 9, "2017": 15, "2018": 12}


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_embedding_sample_list_follows_its_rule(era):
    """sample_list/README.md: the sorted eltau/mutau/tautau embedding nicks of the
    era, without the 2016 B ver1 nicks (no golden lumisection)."""
    database = ANALYSIS.parents[2] / "sample_database/nanoAOD_v15/datasets.json"
    if not database.is_file():
        pytest.skip("KingMaker's sample_database is required")
    datasets = json.loads(database.read_text())
    nicks = sorted(
        nick
        for nick, entry in datasets.items()
        if entry["sample_type"] == "embedding"
        and entry["era"] == era
        and "_B_ver1_" not in nick
        and any(token in nick for token in ("_eltau_", "_mutau_", "_tautau_"))
    )
    assert len(nicks) == EMBEDDING_LENGTHS[era]
    listed = (ANALYSIS / f"sample_list/sm_{era}_embedding.txt").read_text()
    assert listed == "".join(f"{nick}\n" for nick in nicks)