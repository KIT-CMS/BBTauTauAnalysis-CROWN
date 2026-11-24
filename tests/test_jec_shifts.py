"""The JES/JER shifts of ``variations/jec.py`` must reach the jet energy corrections.

The shift configs once set ``jet_jes_sources`` and ``jet_jer_shift``, which no producer
reads since the JEC parameters carry the ``ak4jet_``/``ak8jet_`` prefix. CROWN only
logs unused parameters, so every JES and JER variation silently equalled the nominal.
The JER value must also be bare (``up``), because the producer call quotes it, and
every JES source must exist in the era's JME payload, which names the era-specific
sources by its own era tokens (``Regrouped_Absolute_2022EE`` for 2022postEE).
"""

from pathlib import Path
import re

import pytest

from analysis_configurations.bbtautau.constants import ERAS, ERAS_RUN2
from analysis_configurations.bbtautau.tests.helpers import build, find_producer
from analysis_configurations.bbtautau.variations.jec import JER_REGIONS

# The MC JEC chains every jet shift reruns: standard, regressed and Type-1 MET jets
JEC_MC_PRODUCERS = (
    "JetEnergyCorrectionMCPt",
    "JetEnergyCorrectionMCRegressedPt",
    "Type1JetEnergyCorrectionMCPt",
)
JET_SHIFTS = ("CMS_res_j", "CMS_scale_j", "CMS_HEM")
# the era tokens of the era-specific JES sources in the Run-2 JME payloads
JME_ERA_TOKENS = {"2016preVFP": "2016APV", "2016postVFP": "2016", "2017": "2017", "2018": "2018"}


@pytest.fixture(scope="module", params=ERAS_RUN2)
def era(request):
    return request.param


@pytest.fixture(scope="module")
def config(era):
    return build("sm_config", "ttbar", era=era, shifts=JET_SHIFTS)


@pytest.fixture(scope="module")
def jet_shifts(config):
    # shift names carry the "__" column suffix, e.g. "__CMS_res_j_2018Up"
    shifts = {
        name.removeprefix("__"): parameters
        for name, parameters in config.shifts["global"].items()
    }
    return {name: parameters for name, parameters in shifts.items() if name.startswith(JET_SHIFTS)}


def test_all_jet_shifts_are_scheduled(jet_shifts, era):
    # The eleven regrouped sources and the six JER regions (v8 spec C33), up and
    # down; the SM has no HEMIssue shift, the 2018 HEM flag replaces it (v7 spec
    # E29, C20), and no inclusive JER shift, the sum of the regions
    assert len(jet_shifts) == 2 * (11 + 6), sorted(jet_shifts)
    assert not [name for name in jet_shifts if name.startswith("CMS_HEM")]
    assert {name for name in jet_shifts if name.startswith("CMS_res_j")} == {
        f"CMS_res_j_{region}_{era}{direction}"
        for region in JER_REGIONS
        for direction in ("Up", "Down")
    }


def test_jet_shift_parameters_are_read_by_every_jec_producer(config, jet_shifts):
    parameters = {
        name: find_producer(config, "global", name).parameters["global"]
        for name in JEC_MC_PRODUCERS
    }
    for shift, shift_config in jet_shifts.items():
        ak4 = {key for key in shift_config if key.startswith("ak4jet_")}
        assert ak4, shift
        for producer, used in parameters.items():
            assert ak4 <= used, (shift, producer, ak4 - used)
        assert not [
            key for key in shift_config if key.startswith(("jet_", "fatjet_"))
        ], shift


@pytest.mark.parametrize(
    "shift,key,value",
    [
        ("CMS_res_j_eta0to1p93_{era}Up", "ak4jet_jer_shift", "up_abseta0to1p93"),
        ("CMS_res_j_eta1p93to2p5_{era}Down", "ak4jet_jer_shift", "down_abseta1p93to2p5"),
        ("CMS_res_j_eta2p5to3_ptlt50_{era}Up", "ak4jet_jer_shift", "up_abseta2p5to3_pt0to50"),
        ("CMS_res_j_eta2p5to3_ptgt50_{era}Down", "ak4jet_jer_shift", "down_abseta2p5to3_pt50toInf"),
        ("CMS_res_j_eta3to5_ptlt50_{era}Down", "ak4jet_jer_shift", "down_abseta3toInf_pt0to50"),
        ("CMS_res_j_eta3to5_ptgt50_{era}Up", "ak4jet_jer_shift", "up_abseta3toInf_pt50toInf"),
        ("CMS_scale_j_AbsoluteUp", "ak4jet_jes_source", "Regrouped_Absolute"),
        ("CMS_scale_j_AbsoluteUp", "ak4jet_jes_shift_factor", 1),
        (
            "CMS_scale_j_RelativeSample_{era}Down",
            "ak4jet_jes_source",
            "Regrouped_RelativeSample_{jes_era}",
        ),
    ],
)
def test_jet_shift_values(jet_shifts, era, shift, key, value):
    tokens = {"era": era, "jes_era": JME_ERA_TOKENS[era]}
    value = value.format(**tokens) if isinstance(value, str) else value
    assert jet_shifts[shift.format(**tokens)][key] == value


def test_jer_regions_cover_every_jet_once():
    """The regions of JERC: |eta| < 1.93, 1.93 to 2.5, and 2.5 to 3 and above 3 each below
    and above 50 GeV. Every jet is in exactly one of them, so the six shifts add up to the
    shift of all jets; the selections follow the form the C++ parser reads."""
    pattern = re.compile(
        r"abseta(?P<eta_min>[0-9p]+)to(?P<eta_max>[0-9p]+|Inf)"
        r"(_pt(?P<pt_min>[0-9p]+)to(?P<pt_max>[0-9p]+|Inf))?"
    )

    def number(text, default):
        return default if text is None else float(text.replace("p", ".").replace("Inf", "inf"))

    regions = {}
    for name, selection in JER_REGIONS.items():
        match = pattern.fullmatch(selection)
        assert match, selection
        regions[name] = (
            number(match["eta_min"], 0.0), number(match["eta_max"], float("inf")),
            number(match["pt_min"], 0.0), number(match["pt_max"], float("inf")),
        )
    assert regions == {
        "eta0to1p93": (0.0, 1.93, 0.0, float("inf")),
        "eta1p93to2p5": (1.93, 2.5, 0.0, float("inf")),
        "eta2p5to3_ptlt50": (2.5, 3.0, 0.0, 50.0),
        "eta2p5to3_ptgt50": (2.5, 3.0, 50.0, float("inf")),
        "eta3to5_ptlt50": (3.0, float("inf"), 0.0, 50.0),
        "eta3to5_ptgt50": (3.0, float("inf"), 50.0, float("inf")),
    }
    for abs_eta in (0.0, 1.0, 1.93, 2.2, 2.5, 2.9, 3.0, 4.7, 5.2):
        for pt in (0.0, 15.0, 49.99, 50.0, 300.0):
            inside = [
                name
                for name, (eta_min, eta_max, pt_min, pt_max) in regions.items()
                if eta_min <= abs_eta < eta_max and pt_min <= pt < pt_max
            ]
            assert len(inside) == 1, (abs_eta, pt, inside)


def test_nmssm_keeps_the_inclusive_jer_shift():
    shifts = build("nmssm_config", "ttbar", era="2022postEE", shifts=("CMS_res_j",)).shifts["global"]
    assert {name: change["ak4jet_jer_shift"] for name, change in shifts.items()} == {
        "__CMS_res_j_2022postEEUp": "up",
        "__CMS_res_j_2022postEEDown": "down",
    }


def test_nmssm_keeps_the_hem_shift():
    """NMSSM has no HEM flag and keeps the HEMIssue shift of 2018."""
    shifts = build("nmssm_config", "ttbar", era="2018", shifts=("CMS_HEM",)).shifts["global"]
    assert shifts["__CMS_HEM_2018Down"]["ak4jet_jes_source"] == "HEMIssue"
    assert shifts["__CMS_HEM_2018Down"]["ak4jet_jes_shift_factor"] == -1
    assert shifts["__CMS_HEM_2018Up"]["ak4jet_jes_shift_factor"] == 1


def test_jer_shift_is_quoted_by_the_producer_call(config):
    for name in JEC_MC_PRODUCERS:
        assert (
            '"{ak4jet_jer_shift}"' in find_producer(config, "global", name).call
        ), name


# Every entry point over the eras it supports; nmssm_config accepts all of them.
JEC_CASES = [("nmssm_config", era) for era in ERAS] + [("sm_config", era) for era in ERAS_RUN2]


def jec_payload(nominal):
    correctionlib = pytest.importorskip("correctionlib")
    payload = Path(nominal["ak4jet_jec_file"])
    if not payload.is_file():
        pytest.skip("JME payloads require CVMFS")
    return correctionlib.CorrectionSet.from_file(str(payload))


@pytest.mark.parametrize("module,era", JEC_CASES)
def test_jes_sources_exist_in_the_era_payload(module, era):
    parameters = build(
        module, "ttbar", era=era, shifts=("CMS_scale_j",)
    ).config_parameters["global"]
    nominal = parameters["nominal"]
    corrections = jec_payload(nominal)
    if era in ERAS_RUN2:
        assert nominal["ak4regjet_jec_file"] == nominal["ak4jet_jec_file"]
        assert nominal["ak4regjet_jec_algo"] == nominal["ak4jet_jec_algo"]
    names = set(corrections.keys())
    tag, algo = nominal["ak4jet_jes_tag_mc"], nominal["ak4jet_jec_algo"]
    assert nominal["ak4jet_jes_tag_data"] == tag
    # the levels the JEC producers evaluate, in MC and in Run-2 data (Run-3 data
    # take run-dependent tags)
    for level in ("L1FastJet", "L2Relative", "L3Absolute", "L2L3Residual"):
        for kind in ("MC", "DATA") if era in ERAS_RUN2 else ("MC",):
            assert f"{tag}_{kind}_{level}_{algo}" in names, (kind, level)
    sources = {
        values["ak4jet_jes_source"]
        for shift, values in parameters.items()
        if shift.startswith("__CMS_scale_j")
    }
    assert len(sources) == 11, sorted(sources)
    missing = {s for s in sources if f"{tag}_MC_{s}_{algo}" not in names}
    assert not missing, sorted(missing)


@pytest.mark.parametrize("module,era", JEC_CASES)
def test_jer_tag_exists_in_the_era_payload(module, era):
    """The configured payload contains the JER resolution, scale factor and uncertainty."""
    nominal = build(module, "ttbar", era=era).config_parameters["global"]["nominal"]
    names = set(jec_payload(nominal).keys())
    tag, algo = nominal["ak4jet_jer_tag"], nominal["ak4jet_jec_algo"]
    for kind in ("PtResolution", "ScaleFactor", "SFUncertainty"):
        assert f"{tag}_MC_{kind}_{algo}" in names, kind
