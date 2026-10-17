"""Per-era inputs of the SM configuration in every Run-2 era (NanoAOD v15).

A name that is not in its payload, or a path of the wrong era, fails only at run
time on the grid or, worse, evaluates another era's correction. Each test reads the
configured name or path of one era and checks it against the file it points to.
"""

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from analysis_configurations.bbtautau.constants import ERAS_RUN2, SCOPES
from analysis_configurations.bbtautau.tests.helpers import build, era_cases, find_producer

ANALYSIS = Path(__file__).resolve().parents[1]
CROWN = ANALYSIS.parents[1]
DATASETS = CROWN.parent / "sample_database/nanoAOD_v15/datasets.json"
JET_ID_CORRECTIONS = {
    f"{jets}PUPPI_{wp}" for jets in ("AK4", "AK8") for wp in ("Tight", "TightLeptonVeto")
}


def corrections(path):
    """Correction name -> correction of a correctionlib JSON (gzipped or not)."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as handle:
        payload = json.load(handle)
    return {c["name"]: c for c in payload["corrections"]}


def nominal(era, scope="global", sample="ttbar"):
    scopes = ("et", "mt", "tt") if sample == "embedding" else tuple(SCOPES)
    return build("sm_config", sample, era=era, scopes=scopes).config_parameters[scope]["nominal"]


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_met_filters_are_single_flags(era):
    """Each entry is one Flag_ branch; a missing comma between two string literals
    joins them into one name that no file contains (2016 had that)."""
    filters = nominal(era)["met_filters"]
    assert filters and len(set(filters)) == len(filters)
    for name in filters:
        assert name.startswith("Flag_") and name.count("Flag_") == 1, name
    # the UL recommendation: ecalBadCalibFilter in 2017 and 2018 only
    assert ("Flag_ecalBadCalibFilter" in filters) == (era in ("2017", "2018"))


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_jet_id_payload_of_the_era(era):
    params = nominal(era)
    path = params["ak4jet_id_file"]
    assert path == f"payloads/jetid/Run2-{era}-UL-NanoAODv15/jetid.json.gz"
    assert params["ak4jet_id_name"] == "AK4PUPPI"
    assert set(corrections(ANALYSIS / path)) == JET_ID_CORRECTIONS
    # the copy is the one whose checksum payloads/jetid/README.md records
    digest = hashlib.sha256((ANALYSIS / path).read_bytes()).hexdigest()
    readme = (ANALYSIS / "payloads/jetid/README.md").read_text()
    (row,) = [line for line in readme.splitlines() if f"`Run2-{era}-UL-NanoAODv15`" in line]
    assert f"`{digest}`" in row
    assert "physicsobject::jet::quantity::ID" in find_producer(
        build("sm_config", "ttbar", era=era), "global", "JetID"
    ).call


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_kit_lepton_sf_files_of_the_era(era):
    """The lepton SF files of the Tau Embedding group (KIT) of the era, with the ID
    and isolation corrections the MC and embedding producers read."""
    electron = nominal(era, "et")
    muon = nominal(era, "mt")
    assert electron["mc_electron_sf_file"] == f"data/embedding/electron_{era}UL.json.gz"
    assert muon["mc_muon_sf_file"] == f"data/embedding/muon_{era}UL.json.gz"
    electron_names = set(corrections(CROWN / electron["mc_electron_sf_file"]))
    muon_names = set(corrections(CROWN / muon["mc_muon_sf_file"]))
    assert {electron["mc_electron_id_sf"], electron["mc_electron_iso_sf"]} <= electron_names
    assert {muon["mc_muon_id_sf"], muon["mc_muon_iso_sf"]} <= muon_names


def kit_trigger_sfs(era, scope, vec_config, file_parameter):
    """(flag, correction) of the KIT trigger SFs of ``scope`` and their payload."""
    params = nominal(era, scope)
    entries = params.get(vec_config, [])
    return [(e["flagname"], e["mc_trigger_sf"]) for e in entries], params[file_parameter]


@pytest.mark.parametrize("era", era_cases(ERAS_RUN2, "C7"))
def test_kit_electron_trigger_sf_names_exist(era):
    """et and ee evaluate the KIT single-electron trigger SFs of the era: 2016
    Ele25 (Trg25_Iso), 2017 Ele32 and Ele35 (Trg32_Iso, Trg35_Iso), 2018 Ele32."""
    expected = {
        "2016preVFP": {"trg_wgt_single_ele25": "Trg25_Iso_pt_eta_bins"},
        "2016postVFP": {"trg_wgt_single_ele25": "Trg25_Iso_pt_eta_bins"},
        "2017": {
            "trg_wgt_single_ele32": "Trg32_Iso_pt_eta_bins",
            "trg_wgt_single_ele35": "Trg35_Iso_pt_eta_bins",
        },
        "2018": {"trg_wgt_single_ele32": "Trg32_Iso_pt_eta_bins"},
    }[era]
    config = build("sm_config", "ttbar", era=era, scopes=("et", "ee"))
    for scope in ("et", "ee"):
        names = {p.name for p in config.producers[scope]}
        assert "ETGenerateSingleElectronTriggerSF_MC" in names, scope
        assert "SingleEleTriggerSF" not in names, scope
        sfs, path = kit_trigger_sfs(era, scope, "singlelectron_trigger_sf_mc", "mc_electron_sf_file")
        assert dict(sfs) == expected, scope
        assert set(expected.values()) <= set(corrections(CROWN / path)), scope


@pytest.mark.parametrize("era", era_cases(ERAS_RUN2, "C6", "C6_kit"))
def test_kit_muon_trigger_sf_names_exist(era):
    """mt, mm and em evaluate the KIT single-muon trigger SF of the era (E5): 2016
    the IsoMu22 family (Trg_pt_eta_bins), 2017 IsoMu27, 2018 IsoMu24."""
    expected = {
        "2016preVFP": {"trg_wgt_single_mu22": "Trg_pt_eta_bins"},
        "2016postVFP": {"trg_wgt_single_mu22": "Trg_pt_eta_bins"},
        "2017": {"trg_wgt_single_mu27": "Trg_IsoMu27_pt_eta_bins"},
        "2018": {"trg_wgt_single_mu24": "Trg_IsoMu24_pt_eta_bins"},
    }[era]
    config = build("sm_config", "ttbar", era=era, scopes=("mt", "mm", "em"))
    for scope in ("mt", "mm", "em"):
        assert "SingleMuTriggerSF" not in {p.name for p in config.producers[scope]}, scope
        sfs, path = kit_trigger_sfs(era, scope, "singlemuon_trigger_sf_mc", "mc_muon_sf_file")
        assert dict(sfs) == expected, scope
        assert set(expected.values()) <= set(corrections(CROWN / path)), scope


@pytest.mark.parametrize("era", era_cases(ERAS_RUN2, "btag_efficiency_payloads"))
@pytest.mark.parametrize("scope", SCOPES)
def test_btag_efficiency_payload_of_the_era(era, scope):
    """The strict b-tag consumer looks up every MC sample type of the era's lists in
    the era's per-channel efficiency payload, with the working points T and M."""
    path = nominal(era, scope)["bjet_eff_file"]
    assert path == f"payloads/btagging_efficiencies/upart/{era}/btag_efficiency_{scope}.json.gz"
    if not DATASETS.is_file():
        pytest.skip("KingMaker's sample_database is required")
    datasets = json.loads(DATASETS.read_text())
    nicks = (ANALYSIS / f"sample_list/sm_{era}_binned_mc.txt").read_text().split()
    sample_types = {datasets[nick]["sample_type"] for nick in nicks}
    (efficiency,) = corrections(ANALYSIS / path).values()
    axis = efficiency["data"]
    assert axis["input"] == "sample_type"
    assert sample_types <= {item["key"] for item in axis["content"]}
    working_points = axis["content"][0]["value"]
    assert working_points["input"] == "working_point"
    assert {item["key"] for item in working_points["content"]} == {"T", "M"}


@pytest.mark.parametrize("era", era_cases(ERAS_RUN2, "C12", "tau_embedding_payloads"))
def test_embedding_tau_payload_of_the_era(era):
    params = nominal(era, "mt", "embedding")
    path = params["tau_vsjet_es_sf_file"]
    assert path == (
        f"payloads/tau_embedding/Run2-{era}-UL-NanoAODv15/"
        f"DeepTau2018v2p5_id_es_embedding{era}UL.json.gz"
    )
    assert (ANALYSIS / path).is_file()


# The TAU POG v15 payload (2025-11-27) holds corrections of 2016 and 2017 that are
# byte-identical copies of 2018 (placeholders, README "Run-2 NanoAOD-v15 inputs").
# genmatch 1 of tau_energy_scale is the e -> tau energy scale.
TAU_PLACEHOLDERS = {
    "DeepTau2018v2p5VSe": ("2016preVFP", "2016postVFP"),
    "DeepTau2018v2p5VSmu": ("2016preVFP", "2016postVFP", "2017"),
    "tau_energy_scale:genmatch1": ("2016preVFP", "2016postVFP"),
}


def tau_node(path, name):
    """The data of a TAU payload correction, or of one genmatch of the energy scale."""
    name, _, genmatch = name.partition(":genmatch")
    data = corrections(path)[name]["data"]
    if not genmatch:
        return data
    (algorithm,) = data["content"]  # DeepTau2018v2p5
    node = algorithm["value"]["content"]  # behind the genmatch transform
    assert node["input"] == "genmatch"
    (match,) = [item["value"] for item in node["content"] if item["key"] == int(genmatch)]
    return match


@pytest.mark.parametrize("name", sorted(TAU_PLACEHOLDERS))
def test_tau_pog_placeholders_are_2018_copies(name):
    """The eras listed are copies of 2018, the others measured; a new snapshot that
    replaces a placeholder must update the README and this table."""
    files = {era: Path(nominal(era, "mt")["tau_ides_sf_file"]) for era in ERAS_RUN2}
    if not all(path.is_file() for path in files.values()):
        pytest.skip("TAU payloads require CVMFS")
    reference = tau_node(files["2018"], name)
    copies = {era for era in ERAS_RUN2 if tau_node(files[era], name) == reference} - {"2018"}
    assert copies == set(TAU_PLACEHOLDERS[name])
