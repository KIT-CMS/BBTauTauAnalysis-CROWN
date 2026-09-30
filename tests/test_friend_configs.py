"""Friend-tree entry points: dispatch marker, era gate, output contracts and FF shifts.

The friend entries are thin wrappers around bodies shared in ``friend_common``,
so what is worth testing are the surfaces where a mistake is silent: the
``FriendTreeConfiguration`` marker ``generate_friends.run()`` dispatches on
(otherwise-unused ``# noqa: F401`` code an import cleanup would delete), the era
gate that must fire before ``build_config``, the emitted leaves, and the
payload-driven fake-factor shifts (a wrong syst key silently evaluates nominal).
"""

import functools
import gzip
import inspect
import json
import logging
from pathlib import Path
from unittest import mock

import pytest

from analysis_configurations.bbtautau import (
    fake_factors_friend_config,
    generate_friends,
    nmssm_fastmtt,
    nmssm_kinfit_resolved,
    sm_fake_factors,
    sm_fastmtt,
    sm_kinfit_resolved,
)
from analysis_configurations.bbtautau.constants import (
    ERAS,
    LEGACY_AVAILABLE_SAMPLES,
    SCOPES,
)
from analysis_configurations.bbtautau.producers import fakefactors
from analysis_configurations.bbtautau.tests.helpers import FakeArgs, output_names

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MAP_FASTMTT, MAP_KINFIT = str(FIXTURES / "fastmtt_quantities_map.json"), str(
    FIXTURES / "kinfit_quantities_map.json"
)
MAP_FF_2018, MAP_FF_2023, MAP_FF_2024 = (
    str(FIXTURES / f"fake_factors_{era}_quantities_map.json")
    for era in ("2018", "2023postBPix", "2024")
)
ENTRY_MODULES = (
    nmssm_fastmtt,
    sm_fastmtt,
    sm_kinfit_resolved,
    nmssm_kinfit_resolved,
    fake_factors_friend_config,
    sm_fake_factors,
)

FASTMTT_LEAVES = {"m_fastmtt", "pt_fastmtt", "eta_fastmtt", "phi_fastmtt"}
# The SM fixed-mass (125/125) fit exposes only these four, the NMSSM fit all 18.
SM_KINFIT_LEAVES = {"kinfit_convergence", "kinfit_chi2", "kinfit_prob", "kinfit_mHH"}
NMSSM_KINFIT_LEAVES = {
    f"kinfit_{quantity}{suffix}"
    for suffix in ("_YToBB", "_YToTauTau", "")
    for quantity in ("convergence", "mX", "mY", "mh", "chi2", "prob")
}


@pytest.mark.parametrize(
    "module", ENTRY_MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1]
)
def test_friend_entry_points_expose_friendtreeconfiguration(module):
    members = [name for name, _ in inspect.getmembers(module, inspect.isclass)]
    assert "FriendTreeConfiguration" in members
    assert (
        "Configuration" not in members
    )  # both markers would make generate_friends.run() raise


@pytest.mark.parametrize(
    "name,module,rejected_era",
    [
        ("sm_fastmtt", sm_fastmtt, "2024"),
        ("sm_kinfit_resolved", sm_kinfit_resolved, "2024"),
        ("sm_fake_factors", sm_fake_factors, "2024"),
        ("fake_factors_friend_config", fake_factors_friend_config, "2018"),
    ],
)
def test_friend_era_gates_fire_before_build_config(name, module, rejected_era):
    with mock.patch.object(
        module, "build_config", side_effect=AssertionError("must not be called")
    ):
        with pytest.raises(ValueError, match=rejected_era):
            generate_friends.run(FakeArgs(name, rejected_era))


@pytest.mark.parametrize(
    "module,scope,quantities_map,expected",
    [
        (nmssm_fastmtt, "mt", MAP_FASTMTT, FASTMTT_LEAVES),
        (sm_fastmtt, "mt", MAP_FASTMTT, FASTMTT_LEAVES),
        (sm_kinfit_resolved, "mt", MAP_KINFIT, SM_KINFIT_LEAVES),
        (nmssm_kinfit_resolved, "mt", MAP_KINFIT, NMSSM_KINFIT_LEAVES),
        (sm_fake_factors, "et", MAP_FF_2018, {"fake_factor_raw", "fake_factor"}),
        (sm_fake_factors, "mt", MAP_FF_2018, {"fake_factor_raw", "fake_factor"}),
        (
            sm_fake_factors,
            "tt",
            MAP_FF_2018,
            {"fake_factor_1_raw", "fake_factor_1", "fake_factor_2_raw", "fake_factor_2"},
        ),
    ],
    ids=lambda x: x.__name__.rsplit(".", 1)[-1] if inspect.ismodule(x) else None,
)
def test_friend_output_contracts(module, scope, quantities_map, expected):
    config = module.build_config(
        "2018",
        "ttbar",
        [scope],
        {"none"},
        LEGACY_AVAILABLE_SAMPLES,
        list(getattr(module, "AVAILABLE_ERAS", ERAS)),
        SCOPES,
        quantities_map,
    )
    assert output_names(config, scope) == expected


# --- fake-factor shifts ---------------------------------------------------------

# Variation parameter -> the parameter holding its correction name, over all legs.
NAME_PARAMETER = {
    prefix + wiring.variation: prefix + wiring.name
    for prefix in fakefactors.LEG_PREFIXES.values()
    for wiring in fakefactors.ROLE_WIRING.values()
}
RAW_VARIATIONS = {
    prefix + fakefactors.ROLE_WIRING[role].variation
    for prefix in fakefactors.LEG_PREFIXES.values()
    for role in fakefactors.RAW_ROLES
}


@functools.lru_cache(maxsize=None)
def build_all_shifts(module, era, scope, quantities_map):
    logging.disable(logging.CRITICAL)
    try:
        return module.build_config(
            era, "ttbar", [scope], {"all"}, LEGACY_AVAILABLE_SAMPLES,
            module.AVAILABLE_ERAS, SCOPES, quantities_map,
        )
    finally:
        logging.disable(logging.NOTSET)


def ff_shifts(config, scope):
    """Shift name -> parameter mapping of the fake-factor shifts (main-n-tuple shifts have none)."""
    return {name: mapping for name, mapping in config.shifts[scope].items() if mapping}


def payload_syst_keys(file, correction):
    """All syst keys of ``correction`` (of its stack members, if compound), from the JSON."""
    with gzip.open(Path(fake_factors_friend_config.__file__).parent / file, "rt") as handle:
        payload = json.load(handle)
    by_name = {c["name"]: c for c in payload["corrections"]}
    compounds = {c["name"]: c["stack"] for c in payload.get("compound_corrections") or []}
    members = compounds.get(correction, [correction])
    return {item["key"] for member in members for item in by_name[member]["data"]["content"]}


def assert_shifts_set_payload_keys(config, scope):
    nominal = config.config_parameters[scope]["nominal"]
    for name, mapping in ff_shifts(config, scope).items():
        ((parameter, key),) = mapping.items()
        file = nominal["ff_file" if parameter in RAW_VARIATIONS else "ff_corr_file"]
        assert key in payload_syst_keys(file, nominal[NAME_PARAMETER[parameter]]), name


@pytest.mark.parametrize("scope,expected", [("mt", 34), ("tt", 68)])
def test_sm_fake_factor_shifts(scope, expected):
    config = build_all_shifts(sm_fake_factors, "2018", scope, MAP_FF_2018)
    shifts = ff_shifts(config, scope)
    assert len(shifts) == expected
    assert_shifts_set_payload_keys(config, scope)
    if scope == "mt":
        assert shifts["__process_fractionsfrac_QCDUp"] == {
            "ff_fraction_variation": "process_fractionsfrac_QCD_up"
        }
    else:
        for mapping in shifts.values():
            ((parameter, key),) = mapping.items()
            assert parameter.startswith("ff_2_" if "_subleading" in key else "ff_1_")


@pytest.mark.parametrize("scope", ["mt", "tt"])
def test_sm_corrections_do_not_shift_the_raw_fake_factor(scope):
    config = build_all_shifts(sm_fake_factors, "2018", scope, MAP_FF_2018)
    for name, mapping in ff_shifts(config, scope).items():
        (parameter,) = mapping
        shifted = {q.name for q in config.outputs[scope] if name in q.get_shifts(scope)}
        assert len({leaf.removesuffix("_raw") for leaf in shifted}) == 1, name  # one leg
        assert any(leaf.endswith("_raw") for leaf in shifted) == (parameter in RAW_VARIATIONS)
        assert any(not leaf.endswith("_raw") for leaf in shifted), name


def test_nmssm_fake_factor_shifts_follow_the_payload():
    config = build_all_shifts(fake_factors_friend_config, "2024", "mt", MAP_FF_2024)
    assert_shifts_set_payload_keys(config, "mt")
    config = build_all_shifts(fake_factors_friend_config, "2023postBPix", "mt", MAP_FF_2023)
    assert_shifts_set_payload_keys(config, "mt")
    # the 06-10 payload holds the hardwired set before the payload-driven friend,
    # with the payload's fracTTbarUnc spelling (fracTTBarUnc evaluated nominal
    # silently)
    expected = {
        f"__{value}{direction}"
        for value in [
            "QCDFFunc", "QCDFFmcSubUnc", "ttbarFFunc",
            "process_fractionsfracQCDUnc", "process_fractionsfracTTbarUnc",
            *[
                f"{prefix}_Corr{kind}"
                for prefix in ["QCD_DR_SR", "QCD_non_closure", "ttbar_non_closure"]
                for kind in ["Stat1Sigma", "SystMCShift", "SystBandAsym"]
            ],
        ]
        for direction in ["Up", "Down"]
    }
    assert set(ff_shifts(config, "mt")) == expected
