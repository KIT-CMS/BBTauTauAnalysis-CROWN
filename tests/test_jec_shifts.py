"""The JES/JER shifts of ``variations/jec.py`` must reach the jet energy corrections.

The shift configs once set ``jet_jes_sources`` and ``jet_jer_shift``, which no producer
reads since the JEC parameters carry the ``ak4jet_``/``ak8jet_`` prefix. CROWN only
logs unused parameters, so every JES and JER variation silently equalled the nominal.
The JER value must also be bare (``up``), because the producer call quotes it, and
every JES source must exist in the era's JME payload, which names the era-specific
sources by its own era tokens (``Regrouped_Absolute_2022EE`` for 2022postEE).
"""

from pathlib import Path

import pytest

from analysis_configurations.bbtautau.constants import ERAS, ERAS_RUN2
from analysis_configurations.bbtautau.tests.helpers import build, find_producer

# The MC JEC chains every jet shift reruns: standard, regressed and Type-1 MET jets
JEC_MC_PRODUCERS = (
    "JetEnergyCorrectionMCPt",
    "JetEnergyCorrectionMCRegressedPt",
    "Type1JetEnergyCorrectionMCPt",
)
JET_SHIFTS = ("CMS_res_j", "CMS_scale_j", "CMS_HEM")


@pytest.fixture(scope="module")
def config():
    return build("sm_config", "ttbar", shifts=JET_SHIFTS)


@pytest.fixture(scope="module")
def jet_shifts(config):
    # shift names carry the "__" column suffix, e.g. "__CMS_res_j_2018Up"
    shifts = {
        name.removeprefix("__"): parameters
        for name, parameters in config.shifts["global"].items()
    }
    return {name: parameters for name, parameters in shifts.items() if name.startswith(JET_SHIFTS)}


def test_all_jet_shifts_are_scheduled(jet_shifts):
    # JER, HEMIssue (2018 only) and the eleven regrouped sources, up and down
    assert len(jet_shifts) == 26, sorted(jet_shifts)


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
        ("CMS_res_j_2018Up", "ak4jet_jer_shift", "up"),
        ("CMS_res_j_2018Down", "ak4jet_jer_shift", "down"),
        ("CMS_scale_j_AbsoluteUp", "ak4jet_jes_source", "Regrouped_Absolute"),
        ("CMS_scale_j_AbsoluteUp", "ak4jet_jes_shift_factor", 1),
        ("CMS_HEM_2018Down", "ak4jet_jes_source", "HEMIssue"),
        ("CMS_HEM_2018Down", "ak4jet_jes_shift_factor", -1),
        (
            "CMS_scale_j_RelativeSample_2018Down",
            "ak4jet_jes_source",
            "Regrouped_RelativeSample_2018",
        ),
    ],
)
def test_jet_shift_values(jet_shifts, shift, key, value):
    assert jet_shifts[shift][key] == value


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


@pytest.mark.parametrize(
    "module,era", [(module, era) for module, era in JEC_CASES if era in ERAS_RUN2]
)
def test_jer_tag_exists_in_the_era_payload(module, era):
    """The JER smearing reads the resolution, the scale factor and its uncertainty.
    Run 2 only: the 2023 JER tags (JRV2) are not in the pinned 2023 payloads (JRV3)."""
    nominal = build(module, "ttbar", era=era).config_parameters["global"]["nominal"]
    names = set(jec_payload(nominal).keys())
    tag, algo = nominal["ak4jet_jer_tag"], nominal["ak4jet_jec_algo"]
    for kind in ("PtResolution", "ScaleFactor", "SFUncertainty"):
        assert f"{tag}_MC_{kind}_{algo}" in names, kind
