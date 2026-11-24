"""The shift scheme of the SM shift production (v8 spec section 4, AnalysisProfile.shifts).

One block per item of the spec: the shifts it adds or replaces, the scopes and sample types
that carry them, and the parameters behind them. The NMSSM analysis and the tau-ID
measurement keep the common shifts of variations/.
"""

import gzip
import json
from pathlib import Path
import re

import pytest

from analysis_configurations.bbtautau.analysis_profiles import (
    NMSSM_PROFILE,
    SM_BTAG_EFFICIENCY_PROFILE,
    SM_PROFILE,
    SM_TAU_ID_MEASUREMENT_PROFILE,
    ShiftScheme,
)
from analysis_configurations.bbtautau.constants import ERAS_RUN2, SCOPES
from analysis_configurations.bbtautau.variations.muons import MUON_ES_REGIONS
from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    output_names,
    producer_names,
)

CROWN = Path(__file__).resolve().parents[3]
TAU_SCOPES = ("et", "mt", "tt")
DECAY_MODES = (0, 1, 10, 11)
ALGO = "DeepTau2018v2p5"
# the era tokens of the TAU payloads
TAU_ERA_TOKENS = {
    "2016preVFP": "2016_preVFP",
    "2016postVFP": "2016_postVFP",
    "2017": "2017",
    "2018": "2018",
}


def shifts_of(config, scope):
    """Shift name without the column prefix -> changed parameters, of ``scope``."""
    return {name.removeprefix("__"): change for name, change in config.shifts[scope].items()}


def pairs(names):
    """The shift names without their direction; every one must have both directions."""
    bases = {re.sub(r"(Up|Down)$", "", name) for name in names}
    assert {f"{base}{direction}" for base in bases for direction in ("Up", "Down")} == set(names)
    return bases


def test_only_the_sm_analysis_has_the_scheme_of_the_shift_production():
    common = ShiftScheme()
    assert NMSSM_PROFILE.shifts == common
    assert SM_TAU_ID_MEASUREMENT_PROFILE.shifts == common
    assert SM_BTAG_EFFICIENCY_PROFILE.shifts == common
    assert SM_PROFILE.shifts != common


# --- C18: syst_TES of the vsJet SF -------------------------------------------


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_vs_jet_syst_tes_shifts_per_era_and_decay_mode(era):
    config = build("sm_config", "ttbar", era=era, scopes=TAU_SCOPES, shifts=("VSjet",))
    for scope in TAU_SCOPES:
        shifts = shifts_of(config, scope)
        syst_tes = {name: change for name, change in shifts.items() if "syst_TES" in name}
        assert pairs(syst_tes) == {
            f"CMS_eff_t_{ALGO}_VSjet_dm_syst_TES_{era}_dm{dm}" for dm in DECAY_MODES
        }
        for dm in DECAY_MODES:
            for direction in ("up", "down"):
                name = f"CMS_eff_t_{ALGO}_VSjet_dm_syst_TES_{era}_dm{dm}{direction.capitalize()}"
                assert syst_tes[name] == {
                    "tau_id_sf_vsjet_variation": f"syst_TES_{TAU_ERA_TOKENS[era]}_dm{dm}_{direction}"
                }
        # 2 x 4 statistical, syst_alleras, syst_<era> and 4 syst_TES
        assert len(pairs(shifts)) == 14


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_vs_jet_syst_tes_changes_the_sf_of_its_decay_mode_only(era):
    """Evaluated on the pinned TAU payload with the working points of the configuration: the
    variation of a decay mode changes the scale factor of genuine taus of that decay mode, up
    and down differently, and leaves every other decay mode at the nominal value."""
    correctionlib = pytest.importorskip("correctionlib")
    config = build("sm_config", "ttbar", era=era, scopes=TAU_SCOPES, shifts=("syst_TES",))
    for scope in TAU_SCOPES:
        nominal = config.config_parameters[scope]["nominal"]
        payload = Path(nominal["tau_ides_sf_file"])
        if not payload.is_file():
            pytest.skip("TAU payloads require CVMFS")
        correction = correctionlib.CorrectionSet.from_file(str(payload))[f"{ALGO}VSjet"]
        (entry,) = nominal["vsjet_tau_id_sf"]

        def sf(pt, dm, variation):
            return correction.evaluate(
                pt, dm, 5, entry["vsjet_wp"], nominal["tau_ides_sf_vsele_wp"], variation,
                nominal["tau_id_sf_vsjet_sf_dependence"],
            )

        for change in config.shifts[scope].values():
            variation = change["tau_id_sf_vsjet_variation"]
            varied_dm = int(re.search(r"_dm(\d+)_", variation).group(1))
            for dm in DECAY_MODES:
                for pt in (22.0, 45.0, 80.0, 200.0):
                    assert (sf(pt, dm, variation) != sf(pt, dm, "nom")) is (dm == varied_dm)
        for dm in DECAY_MODES:
            token = TAU_ERA_TOKENS[era]
            for pt in (22.0, 45.0, 80.0, 200.0):
                assert sf(pt, dm, f"syst_TES_{token}_dm{dm}_up") != sf(
                    pt, dm, f"syst_TES_{token}_dm{dm}_down"
                )


def test_nmssm_has_no_vs_jet_syst_tes_shift():
    config = build("nmssm_config", "ttbar", era="2022postEE", scopes=TAU_SCOPES, shifts=("VSjet",))
    assert not [name for name in config.shifts["mt"] if "syst_TES" in name]


# --- C21, C29: tau energy scale shifts ---------------------------------------

# the custom variations of the core tau variation handler
# (src/variation_handlers/taus.cxx, TauVariationHandler::match_custom_variation)
CUSTOM_VARIATION = re.compile(
    r"(up|down)_custom(_(genEle|genMu|genTau))?(_dm(0|1|10|11))?"
    r"(_pt(\d+)to(\d+|Inf))?(_(barrel|endcap|wheel[1-5]))?"
)


def tau_es_pairs(era):
    genuine = {f"CMS_scale_t_{ALGO}_DM{dm}_genTau_{era}" for dm in DECAY_MODES}
    electron_fakes = {
        f"CMS_scale_t_{ALGO}_DM{dm}_genElectron_{region}_{era}"
        for dm in DECAY_MODES
        for region in ("barrel", "endcap")
    }
    muon_fakes = {f"CMS_scale_t_{ALGO}_DM{dm}_genMuon_{era}" for dm in DECAY_MODES}
    return {"et": genuine | electron_fakes, "mt": genuine | muon_fakes, "tt": genuine}


@pytest.mark.parametrize("sample", ["ttbar", "dyjets", "diboson", "hh2b2tau"])
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tau_energy_scale_shifts_per_decay_mode_and_scope(era, sample):
    """Genuine taus: one pair per decay mode in every tau scope, without pT bins. e -> tau
    fakes: decay mode x barrel/endcap in et only. mu -> tau fakes: one pair per decay mode in
    mt only. In every MC sample type (v8 spec C21, C29)."""
    config = build("sm_config", sample, era=era, scopes=TAU_SCOPES, shifts=("CMS_scale_t",))
    expected = tau_es_pairs(era)
    for scope in TAU_SCOPES:
        shifts = shifts_of(config, scope)
        assert pairs(shifts) == expected[scope]
        assert all(set(change) == {"tau_es_variation"} for change in shifts.values())


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tau_energy_scale_variations_are_understood_by_the_core_handler(era):
    source = (CROWN / "src/variation_handlers/taus.cxx").read_text()
    assert '"(up|down)_custom(_(genEle|genMu|genTau))?(_dm(0|1|10|11))?("' in source
    config = build("sm_config", "ttbar", era=era, scopes=TAU_SCOPES, shifts=("CMS_scale_t",))
    expected = {
        "genTau": {"gen": "genTau", "pt": None, "region": None},
        "genMuon": {"gen": "genMu", "pt": None, "region": None},
        "genElectron": {"gen": "genEle", "pt": None},
    }
    for scope in TAU_SCOPES:
        for name, change in shifts_of(config, scope).items():
            match = CUSTOM_VARIATION.fullmatch(change["tau_es_variation"])
            assert match, change
            kind = re.search(r"_(genTau|genMuon|genElectron)_", name).group(1)
            direction, gen, dm, pt, region = match.group(1, 3, 5, 6, 10)
            assert direction == re.search(r"(Up|Down)$", name).group(1).lower()
            assert f"_DM{dm}_" in name
            found = {"gen": gen, "pt": pt, "region": region}
            assert expected[kind].items() <= found.items(), name
            if kind == "genElectron":
                assert region in ("barrel", "endcap") and f"_{region}_" in name


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_tau_energy_scale_payload_has_the_width_the_shifts_assume(era):
    """Why one shift per decay mode suffices (v8 spec C21): on the pinned TAU payload the scale
    of genuine taus depends on pT only through the step at 140 GeV, and the scale of mu -> tau
    fakes is 1 +- 1 % for every decay mode, pT and eta."""
    correctionlib = pytest.importorskip("correctionlib")
    nominal = build("sm_config", "ttbar", era=era, scopes=TAU_SCOPES).config_parameters
    for scope in TAU_SCOPES:
        parameters = nominal[scope]["nominal"]
        payload = Path(parameters["tau_vsjet_es_sf_file"])
        if not payload.is_file():
            pytest.skip("TAU payloads require CVMFS")
        correction = correctionlib.CorrectionSet.from_file(str(payload))[parameters["tau_ES_json_name"]]

        def scale(pt, eta, dm, genmatch, variation):
            return correction.evaluate(
                pt, eta, dm, genmatch, parameters["tau_id_algorithm"],
                parameters["tau_ides_sf_vsjet_wp"], parameters["tau_ides_sf_vsele_wp"], variation,
            )

        for dm in DECAY_MODES:
            for variation in ("nom", "up", "down"):
                below = {scale(pt, eta, dm, 5, variation) for pt in (20.0, 39.0, 41.0, 61.0, 139.0) for eta in (0.2, 2.2)}
                above = {scale(pt, eta, dm, 5, variation) for pt in (140.0, 300.0) for eta in (0.2, 2.2)}
                assert len(below) == 1 and len(above) == 1, (dm, variation)
            for genmatch in (2, 4):
                values = {
                    variation: {scale(pt, eta, dm, genmatch, variation) for pt in (25.0, 80.0, 200.0) for eta in (0.2, 1.0, 1.5, 2.2)}
                    for variation in ("nom", "up", "down")
                }
                assert values == {"nom": {1.0}, "up": {1.01}, "down": {0.99}}, (dm, genmatch)


def test_nmssm_keeps_the_common_tau_energy_scale_shifts():
    """Genuine taus per decay mode and pT bin, e -> tau per decay mode and ECAL region and
    mu -> tau per muon wheel, in every tau scope."""
    config = build("nmssm_config", "ttbar", era="2022postEE", scopes=TAU_SCOPES, shifts=("CMS_scale_t",))
    for scope in TAU_SCOPES:
        assert len(pairs(shifts_of(config, scope))) == 4 * 3 + 4 * 2 + 5


# --- C34: QCD scale on diboson ----------------------------------------------

QCD_SCALE_SHIFTS = {
    "QCDscale_renUp": {"muR": 2.0},
    "QCDscale_renDown": {"muR": 0.5},
    "QCDscale_facUp": {"muF": 2.0},
    "QCDscale_facDown": {"muF": 0.5},
}


def qcd_scale(config, scope):
    return {
        name: change for name, change in shifts_of(config, scope).items() if name.startswith("QCDscale")
    }


@pytest.mark.parametrize("sample", ["diboson", "ttbar", "hh2b2tau"])
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_qcd_scale_weight_and_shifts_on_every_mc_sample(era, sample):
    config = build("sm_config", sample, era=era, scopes=tuple(SCOPES), shifts=("QCDscale",))
    assert "LHE_Scale_weight" in producer_names(config, "global")
    for scope in SCOPES:
        assert "lhe_scale_weight" in output_names(config, scope)
        assert qcd_scale(config, scope) == QCD_SCALE_SHIFTS


@pytest.mark.parametrize(
    "module,sample,era,scopes",
    [
        ("sm_config", "data", "2018", tuple(SCOPES)),
        ("sm_config", "embedding", "2018", TAU_SCOPES),
        # the surfaces of smrun2_tau_id_v2 and smrun2_btag_eff_v1 and the NMSSM analysis
        ("sm_tau_id_measurement_config", "diboson", "2018", ("mt", "mm")),
        ("sm_btag_efficiency_config", "diboson", "2018", tuple(SCOPES)),
        ("nmssm_config", "diboson", "2024", tuple(SCOPES)),
        ("nmssm_config", "hh2b2tau", "2024", tuple(SCOPES)),
    ],
)
def test_no_qcd_scale_shift_without_the_weight_producer(module, sample, era, scopes):
    """A sample without the producer has neither the column nor the shifts: registered alone,
    the shifts have no shifted column."""
    config = build(module, sample, era=era, scopes=scopes, shifts=("QCDscale",))
    assert "LHE_Scale_weight" not in producer_names(config, "global")
    for scope in scopes:
        assert "lhe_scale_weight" not in output_names(config, scope)
        assert not qcd_scale(config, scope)


# --- C36: no columns of the regressed jets -----------------------------------

REGRESSED = re.compile("regress|RegPt", re.IGNORECASE)


def all_producers(config, scope):
    """Every producer of ``scope``, through groups."""

    def walk(producer):
        yield producer
        members = getattr(producer, "producers", None)
        if isinstance(members, dict):
            members = members.get(scope, [])
        for member in members or []:
            yield from walk(member)

    return [producer for top in config.producers[scope] for producer in walk(top)]


def input_names(producer, scope):
    inputs = producer.input.get(scope) if isinstance(producer.input, dict) else producer.input
    return [quantity.name for quantity in inputs or []]


@pytest.mark.parametrize("sample", ["ttbar", "data", "embedding"])
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_sm_config_has_no_regressed_jets(era, sample):
    """Neither the 19 columns bpair_*_regressed* and jpt_regressed* nor a producer that
    computes or reads a quantity of the regressed jets, in simulation, data and embedding."""
    scopes = TAU_SCOPES if sample == "embedding" else tuple(SCOPES)
    config = build("sm_config", sample, era=era, scopes=scopes, shifts=("all",))
    for scope in ("global", *scopes):
        if scope != "global":
            assert not [name for name in output_names(config, scope) if REGRESSED.search(name)]
        for producer in all_producers(config, scope):
            assert not REGRESSED.search(producer.name), producer
            names = [q.name for q in producer.output or []] + input_names(producer, scope)
            assert not [name for name in names if REGRESSED.search(name)], producer


@pytest.mark.parametrize(
    "module,sample,era",
    [
        ("nmssm_config", "ttbar", "2024"),
        ("sm_tau_id_measurement_config", "dyjets", "2018"),
        ("sm_btag_efficiency_config", "ttbar", "2018"),
    ],
)
def test_other_configurations_keep_the_regressed_jets(module, sample, era):
    config = build(module, sample, era=era, scopes=("mt",))
    assert {"jpt_regressed_1", "jpt_regressed_resolution_2"} <= output_names(config, "mt")
    assert find_producer(config, "global", "JetEnergyCorrectionMCRegressedPt")


# --- C37: muon energy scale ---------------------------------------------------

MUON_ES_PAIRS = {
    "mt": ("etalt1p2", "eta1p2to2p1"),
    "em": ("etalt1p2", "eta1p2to2p1", "eta2p1to2p4"),
}
# |eta| region -> relative uncertainty (H -> tautau legacy, without Rochester correction)
MUON_ES_UNCERTAINTIES = {"etalt1p2": 0.004, "eta1p2to2p1": 0.009, "eta2p1to2p4": 0.027}
MUON_PT_READERS = {
    "mt": {"GoodMuons", "MTPairSelection", "LVMu1"},
    "em": {"GoodMuons", "EMPairSelection", "LVMu2"},
}


def numbers(text):
    return [float(number) for number in text.split(",")]


def test_muon_energy_scale_regions():
    assert {name: edge for name, (edge, _) in MUON_ES_REGIONS.items()} == {
        "etalt1p2": 0.0, "eta1p2to2p1": 1.2, "eta2p1to2p4": 2.1,
    }
    assert {name: unc for name, (_, unc) in MUON_ES_REGIONS.items()} == MUON_ES_UNCERTAINTIES


@pytest.mark.parametrize("sample", ["ttbar", "dyjets", "embedding"])
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_muon_energy_scale_shifts_in_mt_and_em(era, sample):
    """Three pairs in em (|eta| < 1.2: +-0.4 %, 1.2 to 2.1: +-0.9 %, from 2.1: +-2.7 %) and
    the first two in mt, for simulated and embedded events; no other scope has them."""
    scopes = TAU_SCOPES if sample == "embedding" else tuple(SCOPES)
    config = build("sm_config", sample, era=era, scopes=scopes, shifts=("CMS_scale_m_",))
    for scope in scopes:
        shifts = {
            name: change for name, change in shifts_of(config, scope).items()
            if name.startswith("CMS_scale_m_eta")
        }
        assert pairs(shifts) == {
            f"CMS_scale_m_{region}_{era}" for region in MUON_ES_PAIRS.get(scope, ())
        }
        if scope not in MUON_ES_PAIRS:
            continue
        nominal = config.config_parameters[scope]["nominal"]
        assert numbers(nominal["muon_es_abs_eta_edges"]) == [0.0, 1.2, 2.1]
        assert numbers(nominal["muon_es_scale_factors"]) == [1.0, 1.0, 1.0]
        for index, region in enumerate(MUON_ES_UNCERTAINTIES):
            if region not in MUON_ES_PAIRS[scope]:
                continue
            for direction, sign in (("Up", 1), ("Down", -1)):
                change = shifts[f"CMS_scale_m_{region}_{era}{direction}"]
                assert set(change) == {"muon_es_scale_factors"}
                expected = [1.0, 1.0, 1.0]
                expected[index] = 1.0 + sign * MUON_ES_UNCERTAINTIES[region]
                assert numbers(change["muon_es_scale_factors"]) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("sample", ["ttbar", "embedding"])
def test_muon_energy_scale_reaches_the_selection_the_pair_and_the_met(sample):
    """The scale acts before the selection: the muon selection, the pair selection and the
    four-vector of the muon read the scaled pT, the uncorrected four-vector the NanoAOD pT,
    so the MET propagation sees the shift; the loose muons of the vetoes stay unscaled."""
    scopes = ("mt",) if sample == "embedding" else ("mt", "em")
    config = build("sm_config", sample, era="2018", scopes=scopes)
    for scope in scopes:
        scale = find_producer(config, scope, "MuonPtScale")
        assert input_names(scale, scope) == ["Muon_pt_corrected", "Muon_eta"]
        assert {"muon_es_abs_eta_edges", "muon_es_scale_factors"} <= scale.parameters[scope]
        readers = {
            producer.name: input_names(producer, scope)
            for producer in all_producers(config, scope)
        }
        assert {
            name for name, inputs in readers.items() if "Muon_pt_scaled" in inputs
        } == MUON_PT_READERS[scope]
        assert {
            name for name, inputs in readers.items() if "Muon_pt_corrected" in inputs
        } == {"MuonPtScale"}
        uncorrected = "LVMu1Uncorrected" if scope == "mt" else "LVMu2Uncorrected"
        assert "Muon_pt" in readers[uncorrected]
        assert {"p4_1", "p4_2", "p4_1_uncorrected", "p4_2_uncorrected"} <= set(
            readers["MetLeptonCorrection"]
        )
    assert "Muon_pt_corrected" in input_names(
        find_producer(config, "global", "BaseMuons"), "global"
    )


@pytest.mark.parametrize(
    "module,sample,era,scopes",
    [
        ("sm_config", "data", "2018", ("mt", "em")),
        ("sm_config", "ttbar", "2018", ("et", "tt", "ee", "mm")),
        ("sm_tau_id_measurement_config", "dyjets", "2018", ("mt", "mm")),
        ("sm_btag_efficiency_config", "ttbar", "2018", ("mt", "em")),
        ("nmssm_config", "ttbar", "2018", ("mt", "em")),
    ],
)
def test_no_muon_energy_scale_elsewhere(module, sample, era, scopes):
    config = build(module, sample, era=era, scopes=scopes, shifts=("CMS_scale_m_",))
    for scope in scopes:
        assert "MuonPtScale" not in {p.name for p in all_producers(config, scope)}
        assert not [name for name in config.shifts.get(scope, {}) if "CMS_scale_m_eta" in name]
        assert "muon_es_scale_factors" not in config.config_parameters[scope]["nominal"]

