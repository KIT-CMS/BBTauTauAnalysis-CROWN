"""Every shift must set parameters its producers read, and leave the nominal alone.

CROWN only logs unused parameters, so a shift that sets a misspelled key (e.g.
``mu_trigger_variation`` where the trigger SF reads ``m_trigger_variation``) builds
and writes shifted columns that equal the nominal. A shift helper that edits the
nominal configuration in place changes the nominal columns of every build.
"""

import gzip
import json
from pathlib import Path

import pytest

from analysis_configurations.bbtautau.constants import SCOPES
from analysis_configurations.bbtautau.tests.helpers import build

# The eras each analysis produces: SM 2018 on the Run-2 v15 inputs, NMSSM Run 3
SURFACES = [
    ("sm_config", "ttbar", "2018", tuple(SCOPES)),
    ("sm_config", "dyjets", "2018", tuple(SCOPES)),
    ("sm_config", "embedding", "2018", ("et", "mt", "tt")),
    ("sm_tau_id_measurement_config", "dyjets", "2018", ("mt", "mm")),
    ("nmssm_config", "ttbar", "2024", tuple(SCOPES)),
    ("nmssm_config", "dyjets_amcatnlo_ll", "2022postEE", tuple(SCOPES)),
]


def _producers(producer, scope):
    yield producer
    members = getattr(producer, "producers", None)
    if isinstance(members, dict):
        members = members.get(scope, [])
    for member in members or []:
        yield from _producers(member, scope)


def _read_parameters(config, scope):
    """Parameters read by the producers of ``scope`` and of the global scope, whose
    shifts CROWN also lists in every other scope, and the entry keys read per
    vector configuration, including the key of the output name."""
    read, entries = set(), {}
    for producer_scope in {scope, "global"}:
        for top in config.producers.get(producer_scope, []):
            for producer in _producers(top, producer_scope):
                parameters = producer.parameters.get(producer_scope, set())
                read |= parameters
                vec_config = getattr(producer, "vec_config", None)
                if vec_config:
                    entries.setdefault(vec_config, {producer.outputname}).update(parameters)
    return read, entries


@pytest.mark.parametrize("module,sample,era,scopes", SURFACES)
def test_every_shifted_parameter_is_read(module, sample, era, scopes):
    config = build(module, sample, era=era, scopes=scopes, shifts=("all",))
    unread = []
    for scope in config.shifts:
        read, entries = _read_parameters(config, scope)
        nominal = config.config_parameters[scope]["nominal"]
        for shift, change in config.shifts[scope].items():
            for key, value in change.items():
                if key not in read:
                    unread.append((scope, shift, key))
                elif isinstance(value, list) and key in entries:
                    # entry keys whose value differs from the nominal entry
                    unread += [
                        (scope, shift, f"{key}.{entry_key}")
                        for entry, nominal_entry in zip(value, nominal[key])
                        for entry_key in entry
                        if entry[entry_key] != nominal_entry.get(entry_key)
                        and entry_key not in entries[key]
                    ]
    assert not unread, sorted(set(unread))


# the values that select the nominal correction, per payload convention
NOMINAL_VARIATIONS = {"nom", "nominal", "sf", "central", False}


def _variation_parameters(parameters):
    """(key, value) of the variation parameters, also inside vector configurations."""
    for key, value in parameters.items():
        entries = [(key, value)]
        if isinstance(value, list):
            entries = [
                (entry_key, entry_value)
                for entry in value
                if isinstance(entry, dict)
                for entry_key, entry_value in entry.items()
            ]
        for entry_key, entry_value in entries:
            if "factor" not in entry_key and (
                "variation" in entry_key or "_shift" in entry_key
            ):
                yield entry_key, entry_value


@pytest.mark.parametrize("module,sample,era,scopes", SURFACES)
def test_nominal_parameters_select_the_nominal_corrections(module, sample, era, scopes):
    """Shift helpers run whatever shifts are selected, so one that edits the nominal
    configuration in place changes the nominal of every build."""
    config = build(module, sample, era=era, scopes=scopes, shifts=("all",))
    shifted_nominal = [
        (scope, key, value)
        for scope, parameters in config.config_parameters.items()
        for key, value in _variation_parameters(parameters["nominal"])
        if value not in NOMINAL_VARIATIONS
    ]
    assert not shifted_nominal, shifted_nominal


def test_prefiring_shifts_build():
    config = build("nmssm_config", "ttbar", era="2017", shifts=("CMS_ecal_prefiring",))
    assert set(config.shifts["global"]) == {
        "__CMS_ecal_prefiring_2017Up",
        "__CMS_ecal_prefiring_2017Down",
    }


def test_tau_vs_mu_shifts_vary_the_vs_mu_sf():
    config = build("sm_config", "dyjets", scopes=("mt", "tt"), shifts=("VSmu",))
    for scope in ("mt", "tt"):
        changes = config.shifts[scope].values()
        assert changes and all(set(change) == {"tau_id_sf_vsmu_variation"} for change in changes)


@pytest.mark.parametrize("module,era", [("sm_config", "2018"), ("nmssm_config", "2022postEE")])
def test_tau_vs_jet_variations_exist_in_the_era_payload(module, era):
    """The Run-2/2022/2023 vsJet variations are evaluated as given by the payload."""
    config = build(module, "ttbar", era=era, scopes=("mt",), shifts=("VSjet",))
    payload = Path(config.config_parameters["mt"]["nominal"]["tau_ides_sf_file"])
    if not payload.is_file():
        pytest.skip("TAU payloads require CVMFS")
    (vsjet,) = [
        c for c in json.load(gzip.open(payload))["corrections"] if c["name"].endswith("VSjet")
    ]
    keys = set()

    def walk(node):
        if isinstance(node, dict):
            if node.get("nodetype") == "category" and node.get("input") == "syst":
                keys.update(item["key"] for item in node["content"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(vsjet["data"])
    variations = {
        change["tau_id_sf_vsjet_variation"] for change in config.shifts["mt"].values()
    }
    assert len(variations) == 20, sorted(variations)
    assert variations <= keys, sorted(variations - keys)
