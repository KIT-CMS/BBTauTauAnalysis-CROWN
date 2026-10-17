"""Light-dilepton control channels (ee, em, mm) and the SM lepton-isolation sideband."""

import pytest

from analysis_configurations.bbtautau.constants import ERAS_RUN2, SCOPES
from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    generate_code,
    output_names,
    producer_names,
)

CONTROLS = ("ee", "em", "mm")
LEPTON_SFS = {
    "ee": {"id_wgt_ele_1", "id_wgt_ele_2", "reco_wgt_ele_1", "reco_wgt_ele_2"},
    "em": {"id_wgt_ele_1", "reco_wgt_ele_1", "id_wgt_mu_2", "iso_wgt_mu_2"},
    "mm": {"id_wgt_mu_1", "iso_wgt_mu_1", "id_wgt_mu_2", "iso_wgt_mu_2"},
}
# trigger SF columns per era: the single-muon trigger in em and mm (the muon of em
# is its second leg) and the single-electron trigger in ee; em has no electron
# trigger
MUON_TRIGGER_SF = {
    "2016preVFP": "trg_wgt_single_mu22",
    "2016postVFP": "trg_wgt_single_mu22",
    "2017": "trg_wgt_single_mu27",
    "2018": "trg_wgt_single_mu24",
}
ELECTRON_TRIGGER_SFS = {
    "2016preVFP": {"trg_wgt_single_ele25"},
    "2016postVFP": {"trg_wgt_single_ele25"},
    "2017": {"trg_wgt_single_ele32", "trg_wgt_single_ele35"},
    "2018": {"trg_wgt_single_ele32"},
}
Z_PAIR = {"ee": "ZElElPairSelection", "mm": "ZMuMuPairSelection"}


def trigger_sfs(era):
    return {
        "ee": ELECTRON_TRIGGER_SFS[era],
        "em": {MUON_TRIGGER_SF[era]},
        "mm": {MUON_TRIGGER_SF[era]},
    }


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("sample", ["data", "ttbar", "dyjets"])
def test_main_control_output_contract(sample, era):
    config = build("sm_config", sample, era=era, scopes=CONTROLS)
    for scope in CONTROLS:
        outputs, producers = output_names(config, scope), producer_names(config, scope)
        params = config.config_parameters[scope]["nominal"]
        assert params["bjet_eff_file"].endswith(f"/btag_efficiency_{scope}.json.gz")
        if sample == "data":
            assert (
                not outputs & LEPTON_SFS[scope] and "btag_weight_upart" not in outputs
            )
        else:
            assert {s for s in LEPTON_SFS[scope] if not s.startswith("trg_")} <= outputs
            assert "btag_weight_upart" in outputs
        if scope in ("ee", "em"):
            assert (
                params["tight_electron_min_pt"],
                params["tight_electron_max_iso"],
            ) == (
                15.0,
                0.4,
            )
        if scope in ("mm", "em"):
            assert (params["tight_muon_min_pt"], params["tight_muon_max_iso"]) == (
                15.0,
                0.4,
            )
        # em takes no electron trigger, ee the trigger SF of et
        assert "SingleEleTriggerFlags" not in producer_names(config, "em")
        # the Z pair comes from the core algorithm (pt ordering fixed upstream)
        assert Z_PAIR.get(scope, "EMPairSelection") in producers
        assert not {n for n in producers if n.startswith("ControlZ")}


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_ee_takes_the_kit_electron_trigger_sf(era):
    """The POG Electron-HLT-SF does not exist for Run-2 UL; ee evaluates the trigger
    SF of the Tau Embedding group, as et."""
    config = build("sm_config", "ttbar", era=era, scopes=CONTROLS)
    for scope in CONTROLS:
        assert "SingleEleTriggerSF" not in producer_names(config, scope), scope
    assert "ETGenerateSingleElectronTriggerSF_MC" in producer_names(config, "ee")


def test_electron_reco_weight_is_the_era_keyed_addon_call():
    """The reco weight picks the payload's pt category itself, so the call carries the
    era id instead of a fixed category name; it reads the supercluster eta (C22)."""
    config = build("sm_config", "ttbar", scopes=CONTROLS)
    for producer, leg in (("Ele_1_Reco_SF_ScEta", 1), ("Ele_2_Reco_SF_ScEta", 2)):
        reco = find_producer(config, "ee", producer)
        assert (
            "xyh::scalefactor::electron_reco(" in reco.call
            and "{ele_sf_year_id}" in reco.call
        )
        assert [q.name for q in reco.get_inputs("ee")] == [
            f"pt_{leg}",
            f"sc_eta_{leg}",
            f"phi_{leg}",
        ]
        assert [q.name for q in reco.get_outputs("ee")] == [f"reco_wgt_ele_{leg}"]


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize(
    "module,sample",
    [
        ("sm_config", "data"),
        ("sm_config", "dyjets"),
        ("sm_btag_efficiency_config", "dyjets"),
    ],
)
def test_actual_cpp_generation_in_every_scope(module, sample, era):
    """Placeholder expansion and source emission for all six scopes, not just DAG
    validation: data (no weight in any scope), MC with SFs and gen-boson recoil, and
    the MC-only efficiency profile."""
    generated = generate_code(module, sample, era=era, scopes=tuple(SCOPES))
    assert list(generated.directory.rglob("*.cxx"))
    if sample == "data":
        for scope in SCOPES:
            weights = {o for o in generated.outputs[scope] if "wgt" in o or "weight" in o}
            assert not weights, (scope, weights)
    else:
        for scope, expected in LEPTON_SFS.items():
            outputs = generated.outputs[scope]
            assert expected <= outputs, (scope, expected - outputs)


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_control_trigger_sf_columns(era):
    """The trigger SF columns of the era's single-lepton triggers in ee, em and mm."""
    generated = generate_code("sm_config", "dyjets", era=era, scopes=CONTROLS)
    for scope, expected in trigger_sfs(era).items():
        written = {o for o in generated.outputs[scope] if o.startswith("trg_wgt_")}
        assert written == expected, scope


@pytest.mark.parametrize(
    "scope,parameter,nmssm",
    [("et", "tight_electron_max_iso", 10000.0), ("mt", "tight_muon_max_iso", 0.4)],
)
def test_sm_tau_channels_keep_the_lepton_isolation_sideband(scope, parameter, nmssm):
    """One SM production serves the nominal iso < 0.15 selection and the anti-isolated
    sidebands up to 0.5; NMSSM keeps its object defaults (no electron isolation
    pre-cut, muons up to 0.4)."""
    for module, expected in (
        ("sm_config", 0.5),
        ("sm_btag_efficiency_config", 0.5),
        ("nmssm_config", nmssm),
    ):
        assert (
            build(module, "ttbar", scopes=(scope,)).config_parameters[scope]["nominal"][
                parameter
            ]
            == expected
        ), module


@pytest.mark.parametrize(
    "module,electron_id,ele_sf,muon_id,muon_sfs",
    [
        (
            "sm_config",
            "Electron_mvaIso_WP90",
            "wp90iso",
            "Muon_mediumId",
            ("NUM_MediumID_DEN_TrackerMuons", "NUM_TightRelIso_DEN_MediumID"),
        ),
        (
            "nmssm_config",
            "Electron_mvaIso_WP80",
            "wp80iso",
            "Muon_tightId",
            ("NUM_TightID_DEN_TrackerMuons", "NUM_TightRelIso_DEN_TightID"),
        ),
    ],
)
def test_lepton_ids_and_their_sfs(module, electron_id, ele_sf, muon_id, muon_sfs):
    """SM keeps the lepton IDs the KIT (Tau Embedding group) lepton SFs are measured
    for, NMSSM those of the object defaults, each with the POG SFs of its IDs."""
    config = build(module, "ttbar", scopes=("et", "mt"))
    electron = config.config_parameters["et"]["nominal"]
    muon = config.config_parameters["mt"]["nominal"]
    assert (electron["tight_electron_id"], electron["ele_id_sf_name"]) == (electron_id, ele_sf)
    assert (muon["tight_muon_id"], muon["muon_id_sf_name"], muon["muon_iso_sf_name"]) == (
        muon_id,
        *muon_sfs,
    )
    assert config.config_parameters["global"]["nominal"]["loose_electron_id"] == electron_id
