"""Trigger flags and trigger SFs per era (v7 spec C6-C9, E2-E8, K8).

A flag whose HLT path or filter bit does not exist is silently false, a trigger SF
of the wrong trigger silently wrong. The tables here pin the triggers of every
Run-2 era and check them against the HLT branches and the TrigObj_filterBits doc
strings of the era's v15 files (tests/fixtures, written by make_hlt_fixtures.py).
"""

import json
from pathlib import Path

import pytest

from analysis_configurations.bbtautau.constants import ERAS, ERAS_RUN2, ERAS_RUN3, SCOPES
from analysis_configurations.bbtautau.tests.helpers import build, generate_code, producer_names

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VEC_CONFIGS = {
    "et": ("ele_trigger", "double_eletau_trigger"),
    "ee": ("ele_trigger",),
    "em": ("ele_trigger", "mu_trigger"),
    "mt": ("mu_trigger", "double_mutau_trigger"),
    "mm": ("mu_trigger",),
    "tt": ("tautau_trigger", "tautau_trigger_embedding", "tautaujet_trigger"),
}
# SM single-lepton flags per era: flag -> (HLT path, min pT, max |eta|, filter bit)
SM_MUON_TRIGGERS = {
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
    "2018": {"trg_single_mu24": ("HLT_IsoMu24", 26.0, 2.4, 1)},
}
SM_ELECTRON_TRIGGERS = {
    **{
        era: {"trg_single_ele25": ("HLT_Ele25_eta2p1_WPTight_Gsf", 27.0, 2.1, 1)}
        for era in ("2016preVFP", "2016postVFP")
    },
    "2017": {
        "trg_single_ele32": ("HLT_Ele32_WPTight_Gsf", 34.0, 2.5, 1),
        "trg_single_ele35": ("HLT_Ele35_WPTight_Gsf", 37.0, 2.5, 1),
    },
    "2018": {"trg_single_ele32": ("HLT_Ele32_WPTight_Gsf", 34.0, 2.5, 1)},
}
# di-tau flags per era (E7): flag -> (HLT path, filter bits of both legs)
DITAU_TRIGGERS = {
    **{
        era: {
            "trg_double_tau35_mediumiso": ("HLT_DoubleMediumIsoPFTau35_Trk1_eta2p1_Reg", (1, 8)),
            "trg_double_tau35_mediumcombinediso": (
                "HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg",
                (1, 8),
            ),
        }
        for era in ("2016preVFP", "2016postVFP")
    },
    "2017": {
        "trg_double_tau35_tightiso": ("HLT_DoubleTightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg", (6,)),
        "trg_double_tau40_mediumiso": ("HLT_DoubleMediumChargedIsoPFTau40_Trk1_TightID_eta2p1_Reg", (6,)),
        "trg_double_tau40_tightiso": ("HLT_DoubleTightChargedIsoPFTau40_Trk1_eta2p1_Reg", (6,)),
    },
    "2018": {
        "trg_double_tau35_mediumiso": ("HLT_DoubleMediumChargedIsoPFTauHPS35_Trk1_eta2p1_Reg", (6,)),
        "trg_double_tau35_tightiso": ("HLT_DoubleTightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg", (6,)),
        "trg_double_tau40_mediumiso": ("HLT_DoubleMediumChargedIsoPFTau40_Trk1_TightID_eta2p1_Reg", (6,)),
        "trg_double_tau40_tightiso": ("HLT_DoubleTightChargedIsoPFTau40_Trk1_eta2p1_Reg", (6,)),
    },
}


def bits(value):
    """Filter bits of a flag entry: an integer or a C++ list body such as "1, 8"."""
    return tuple(int(bit) for bit in str(value).split(","))


def parameters(config, scope):
    return config.config_parameters[scope]["nominal"]


def hlt_branches(era):
    return {
        kind: set((FIXTURES / f"nanoaod_v15_{era}_{kind}_hlt.txt").read_text().split())
        for kind in ("data", "mc", "embedding")
    }


def bit_meanings(era, kind="mc"):
    meaning = json.loads((FIXTURES / "nanoaod_v15_trigobj_filterbits.json").read_text())[era][kind]
    return {obj: {int(bit): text for bit, text in bits.items()} for obj, bits in meaning.items()}


@pytest.mark.parametrize(
    "module,era",
    [("sm_config", era) for era in ERAS_RUN2] + [("nmssm_config", era) for era in ERAS],
)
def test_flag_lists_have_unique_names_and_integer_bits(module, era):
    """C8: no era list repeats a flag name (the 2016 tt dict used to be overwritten,
    so both 2016 entries were one path), and every filter bit is an integer in the
    30 bits the core matching tests."""
    config = build(module, "ttbar", era=era, scopes=tuple(SCOPES))
    for scope, vec_configs in VEC_CONFIGS.items():
        for vec_config in vec_configs:
            entries = parameters(config, scope).get(vec_config, [])
            names = [entry["flagname"] for entry in entries]
            assert len(names) == len(set(names)), (scope, vec_config, names)
            for entry in entries:
                for key in ("filter_bit", "p1_filter_bit", "p2_filter_bit"):
                    if key in entry:
                        assert all(-1 <= bit < 30 for bit in bits(entry[key])), (vec_config, entry)


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize(
    "scope,vec_config,table",
    [
        ("mt", "mu_trigger", SM_MUON_TRIGGERS),
        ("mm", "mu_trigger", SM_MUON_TRIGGERS),
        ("em", "mu_trigger", SM_MUON_TRIGGERS),
        ("et", "ele_trigger", SM_ELECTRON_TRIGGERS),
        ("ee", "ele_trigger", SM_ELECTRON_TRIGGERS),
    ],
)
def test_sm_single_lepton_triggers_of_the_era(scope, vec_config, table, era):
    """E2-E6: only the analysis triggers the KIT SFs describe, matched within
    Delta R 0.1 as in the KIT tag and probe (K8): 2016 the IsoMu22 family (bit 1
    IsoMu, 3 IsoTkMu) and Ele25_eta2p1, 2017 IsoMu27 and Ele32/Ele35, 2018 IsoMu24
    and Ele32. The flags keep the trigger's |eta| (2.4 for muons); the |eta| < 2.1
    of the tau channels is cut downstream."""
    entries = parameters(build("sm_config", "ttbar", era=era, scopes=(scope,)), scope)[vec_config]
    assert {
        e["flagname"]: (e["hlt_path"], e["min_pt"], e["max_abs_eta"], e["filter_bit"]) for e in entries
    } == table[era]
    assert {e["match_max_delta_r"] for e in entries} == {0.1}
    assert {e["particle_id"] for e in entries} == {13 if vec_config == "mu_trigger" else 11}


@pytest.mark.parametrize("era", ["2018", "2024"])
def test_nmssm_keeps_its_single_lepton_triggers(era):
    """NMSSM keeps the high-pT triggers and the Delta R 0.4 of the legacy setup."""
    config = build("nmssm_config", "ttbar", era=era, scopes=("mt", "et"))
    muons = parameters(config, "mt")["mu_trigger"]
    electrons = parameters(config, "et")["ele_trigger"]
    assert "trg_single_mu50" in {e["flagname"] for e in muons}
    assert "trg_single_ele115" in {e["flagname"] for e in electrons}
    assert {e["match_max_delta_r"] for e in muons + electrons} == {0.4}


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_ditau_triggers_of_the_era(era):
    """E7, C8: 2016 the Iso and CombinedIso paths with the final-filter bits 1
    (Medium(Comb)Iso) and 8 (Dz), 2017 the three paths, 2018 the four, bit 6; both
    legs pT > 40 GeV, |eta| < 2.1, Delta R 0.4."""
    entries = parameters(build("sm_config", "ttbar", era=era, scopes=("tt",)), "tt")["tautau_trigger"]
    table = {}
    for e in entries:
        assert bits(e["p1_filter_bit"]) == bits(e["p2_filter_bit"])
        assert (e["p1_min_pt"], e["p2_min_pt"], e["p1_max_abs_eta"], e["p2_max_abs_eta"]) == (40.0, 40.0, 2.1, 2.1)
        assert e["match_max_delta_r"] == 0.4
        table[e["flagname"]] = (e["hlt_path"], bits(e["p1_filter_bit"]))
    assert table == DITAU_TRIGGERS[era]


# Run 3 (NMSSM): the SF of one flag per era, unchanged
RUN3_DITAU_SF_FLAGS = {
    **{era: "trg_double_tau35_mediumdeeptau" for era in ("2022preEE", "2022postEE", "2023preBPix", "2023postBPix")},
    **{era: "trg_double_tau30_mediumpnet" for era in ("2024", "2025")},
}


@pytest.mark.parametrize("era", ERAS)
def test_ditau_sf_lists_follow_the_flag_lists(era):
    """C8: in Run 2 one POG di-tau SF (WP Medium, per leg) per flag of the era,
    written as trg_wgt<flag without trg>_leg<n> (the names ShapeSmith reads); Run 3
    keeps its one SF per era, trg_wgt_<...>."""
    module = "sm_config" if era in ERAS_RUN2 else "nmssm_config"
    params = parameters(build(module, "ttbar", era=era, scopes=("tt",)), "tt")
    flags = [e["flagname"] for e in params["tautau_trigger"]] if era in ERAS_RUN2 else [RUN3_DITAU_SF_FLAGS[era]]
    for leg in (1, 2):
        entries = params[f"double_tautau_trigger_leg{leg}_sf"]
        assert [e["tt_trigger_flag"] for e in entries] == flags
        prefix = "trg_wgt" if era in ERAS_RUN2 else "trg_wgt_"
        assert [e[f"tt_trigger_leg{leg}_flagname"] for e in entries] == [
            flag.replace("trg_", prefix) + f"_leg{leg}" for flag in flags
        ]
        assert {(e[f"tt_trigger_leg{leg}_sf_name"], e[f"tt_trigger_leg{leg}_variation"]) for e in entries} == {
            ("ditau", "nom")
        }


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_ditau_sf_columns_are_written(era):
    """The 2016 and 2017 tt MC gets the SF columns of its flags (they were empty)."""
    outputs = generate_code("sm_config", "dyjets", era=era, scopes=tuple(SCOPES)).outputs["tt"]
    for flag in DITAU_TRIGGERS[era]:
        for leg in (1, 2):
            assert flag.replace("trg_", "trg_wgt") + f"_leg{leg}" in outputs
        assert flag in outputs


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_hlt_paths_exist_in_the_era(era):
    """Every HLT path of the SM flags is a branch of the era's MC and embedding files
    and of its data (in the union over run periods). Exceptions by the menus:
    CombinedIso exists in the data from 2016H on (postVFP), the 2018 non-HPS di-tau
    paths in the data before run 317509 only."""
    branches = hlt_branches(era)
    paths = [path for path, *_ in SM_MUON_TRIGGERS[era].values()]
    paths += [path for path, *_ in SM_ELECTRON_TRIGGERS[era].values()]
    paths += [path for path, _ in DITAU_TRIGGERS[era].values()]
    for path in paths:
        data_only = era == "2018" and path.startswith("HLT_Double") and "HPS" not in path
        if not data_only:
            assert path in branches["mc"] and path in branches["embedding"], path
        if path != "HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg" or era == "2016postVFP":
            assert path in branches["data"], path


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_filter_bits_mean_what_the_flags_claim(era):
    """The bit numbers against the TrigObj_filterBits doc string of the era: electron
    1 = WPTight, muon 1 = Iso and in 2016 3 = IsoTkMu, tau 1 = Medium(Comb)Iso and 8 =
    Dz in 2016, 6 = charged iso di-tau in 2017/2018; the embedding di-tau bits 12
    (2016) and 23 (2017/2018)."""
    mc, embedding = bit_meanings(era), bit_meanings(era, "embedding")
    assert mc["Electron"][1].startswith("1e (WPTight")
    assert mc["Muon"][1] == "Iso"
    if era.startswith("2016"):
        assert mc["Muon"][3] == "IsoTkMu"
        assert (mc["Tau"][1], mc["Tau"][8]) == ("Medium(Comb)Iso", "Dz")
        assert embedding["Tau"][12].startswith("di-tau (for tau leg trigger object matching in embedding")
    else:
        assert mc["Tau"][6] == "charged iso di-tau"
        assert embedding["Tau"][23].startswith("di-tau (for tau leg trigger object matching in embedding")


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_no_cross_triggers_in_the_sm(era):
    """E8, C9: the e-tau and mu-tau cross triggers are not part of the SM scopes
    (profile field lepton_tau_cross_triggers); NMSSM keeps them."""
    sm = build("sm_config", "ttbar", era=era, scopes=("et", "mt"))
    assert "DoubleEleTauTriggerFlags" not in producer_names(sm, "et")
    assert "DoubleMuTauTriggerFlags" not in producer_names(sm, "mt")
    nmssm = build("nmssm_config", "ttbar", era=era, scopes=("et", "mt"))
    assert "DoubleEleTauTriggerFlags" in producer_names(nmssm, "et")
    assert "DoubleMuTauTriggerFlags" in producer_names(nmssm, "mt")
    # the scrambled 2016/2017 e-tau dicts are gone
    if era != "2018":
        assert parameters(nmssm, "et")["double_eletau_trigger"] == []


@pytest.mark.parametrize("era", ERAS_RUN2)
@pytest.mark.parametrize("module", ["sm_config", "nmssm_config"])
def test_no_pog_electron_trigger_sf_in_run2(module, era):
    """C7: the EGM Electron-HLT-SF does not exist in Run 2; every Run-2 configuration
    evaluates the KIT SF of its electron trigger in et, ee and em."""
    config = build(module, "ttbar", era=era, scopes=("et", "ee", "em"))
    for scope in ("et", "ee", "em"):
        assert "SingleEleTriggerSF" not in producer_names(config, scope), scope
    for scope in ("et", "ee"):
        assert "ETGenerateSingleElectronTriggerSF_MC" in producer_names(config, scope), scope


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_kit_muon_trigger_sf_reads_the_muon_of_each_scope(era):
    """C6: KitSingleMuonTriggerSF evaluates the muon of mt and mm (leg 1) and em (leg
    2), type mc, from the KIT file of the era; data has no trigger SF."""
    generated = generate_code("sm_config", "dyjets", era=era, scopes=("mt", "em", "mm"))
    for scope, leg in (("mt", 1), ("mm", 1), ("em", 2)):
        (path,) = generated.directory.rglob(f"src/{scope}/KitSingleMuonTriggerSF.cxx")
        call = " ".join(path.read_text().split())
        assert f'"pt_{leg}", "eta_{leg}", "data/embedding/muon_{era}UL.json.gz"' in call, scope
        assert '"mc", 1.0)' in call
    data = generate_code("sm_config", "data", era=era, scopes=("mt", "em", "mm")).outputs
    assert not {o for scope in ("mt", "em", "mm") for o in data[scope] if o.startswith("trg_wgt")}


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_kit_trigger_sf_shifts(era):
    """C6: CMS_eff_m_trigger_<era> scales the KIT muon trigger SF by 1.02 / 0.98 in
    mt, mm and em (the TauAnalysis convention, the KIT files have no variations);
    CMS_eff_e_trigger_<era> the electron one in et and ee."""
    config = build("sm_config", "dyjets", era=era, scopes=tuple(SCOPES), shifts=("all",))
    for scope, name, key, extrapolation in [
        *((s, "CMS_eff_m_trigger", "singlemuon_trigger_sf_mc", "mc_muon_trg_extrapolation") for s in ("mt", "mm", "em")),
        *((s, "CMS_eff_e_trigger", "singlelectron_trigger_sf_mc", "mc_electron_trg_extrapolation") for s in ("et", "ee")),
    ]:
        shifts = {n.removeprefix("__"): change for n, change in config.shifts[scope].items()}
        for direction, factor in (("Up", 1.02), ("Down", 0.98)):
            entries = shifts[f"{name}_{era}{direction}"][key]
            assert entries and {e[extrapolation] for e in entries} == {factor}, (scope, direction)


@pytest.mark.parametrize("era", ERAS_RUN3)
def test_run3_single_lepton_triggers_unchanged(era):
    """The Run-3 NMSSM flags and the POG trigger SFs stay as they were."""
    config = build("nmssm_config", "ttbar", era=era, scopes=("mt", "et"))
    assert [e["flagname"] for e in parameters(config, "mt")["mu_trigger"]] == [
        "trg_single_mu24", "trg_single_mu50", "trg_single_mu100_cascade", "trg_single_mu100_tk",
    ]
    assert [e["flagname"] for e in parameters(config, "et")["ele_trigger"]] == [
        "trg_single_ele30", "trg_single_ele115",
    ]
    assert "SingleMuTriggerSF" in producer_names(config, "mt")
    assert "SingleEleTriggerSF" in producer_names(config, "et")
