"""Light-dilepton control channels (ee, em, mm) and the SM lepton-isolation sideband."""

from pathlib import Path
import subprocess
import sys

import pytest

from analysis_configurations.bbtautau.constants import SCOPES
from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    output_names,
    producer_names,
)

CONTROLS = ("ee", "em", "mm")
LEPTON_SFS = {
    "ee": {
        "id_wgt_ele_1",
        "id_wgt_ele_2",
        "reco_wgt_ele_1",
        "reco_wgt_ele_2",
        "trg_wgt_single_ele32",
    },
    "em": {
        "id_wgt_ele_1",
        "reco_wgt_ele_1",
        "id_wgt_mu_2",
        "iso_wgt_mu_2",
        "trg_wgt_single_mu24",
    },
    "mm": {
        "id_wgt_mu_1",
        "iso_wgt_mu_1",
        "id_wgt_mu_2",
        "iso_wgt_mu_2",
        "trg_wgt_single_mu24",
    },
}
Z_PAIR = {"ee": "ZElElPairSelection", "mm": "ZMuMuPairSelection"}


@pytest.mark.parametrize("sample", ["data", "ttbar", "dyjets"])
def test_main_control_output_contract(sample):
    config = build("sm_config", sample, scopes=CONTROLS)
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
        assert "SingleEleTriggerSF" not in producers
        # the Z pair comes from the core algorithm (pt ordering fixed upstream)
        assert Z_PAIR.get(scope, "EMPairSelection") in producers
        assert not {n for n in producers if n.startswith("ControlZ")}


def test_electron_reco_weight_is_the_era_keyed_addon_call():
    """The reco weight picks the payload's pt category itself, so the call carries the
    era id instead of a fixed category name."""
    config = build("sm_config", "ttbar", scopes=CONTROLS)
    for producer, leg in (("Ele_1_Reco_SF", 1), ("Ele_2_Reco_SF", 2)):
        reco = find_producer(config, "ee", producer)
        assert (
            "xyh::scalefactor::electron_reco(" in reco.call
            and "{ele_sf_year_id}" in reco.call
        )
        assert [q.name for q in reco.get_inputs("ee")] == [
            f"pt_{leg}",
            f"eta_{leg}",
            f"phi_{leg}",
        ]
        assert [q.name for q in reco.get_outputs("ee")] == [f"reco_wgt_ele_{leg}"]


@pytest.mark.parametrize(
    "module,sample",
    [
        ("sm_config", "data"),
        ("sm_config", "dyjets"),
        ("sm_btag_efficiency_config", "dyjets"),
    ],
)
def test_actual_cpp_generation_in_every_scope(module, sample, tmp_path):
    """Placeholder expansion and source emission for all six scopes, not just DAG
    validation: data (no SFs), MC with SFs and gen-boson recoil, and the MC-only
    efficiency profile."""
    script = f"""
from analysis_configurations.bbtautau.tests.helpers import build
from analysis_configurations.bbtautau.tests.test_sm_control_channels import LEPTON_SFS
from code_generation.code_generation import CodeGenerator
config = build({module!r}, {sample!r}, scopes={tuple(SCOPES)!r})
generator = CodeGenerator("code_generation/analysis_template.cxx", "code_generation/subset_template.cxx",
                          config, "bbtautau", {module!r}, "{module}_{sample}_2018", {str(tmp_path)!r})
generator.generate_code()
for scope, expected in LEPTON_SFS.items():
    outputs = set(generator.output_commands[scope])
    assert (expected <= outputs) if {sample!r} != "data" else not expected & outputs, (scope, expected ^ outputs)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert list(tmp_path.rglob("*.cxx"))


@pytest.mark.parametrize(
    "scope,parameter", [("et", "tight_electron_max_iso"), ("mt", "tight_muon_max_iso")]
)
def test_sm_tau_channels_keep_the_lepton_isolation_sideband(scope, parameter):
    """One SM production serves the nominal iso < 0.15 selection and the anti-isolated
    sidebands up to 0.5; NMSSM keeps the 0.4 object default."""
    for module, expected in (
        ("sm_config", 0.5),
        ("sm_btag_efficiency_config", 0.5),
        ("nmssm_config", 0.4),
    ):
        assert (
            build(module, "ttbar", scopes=(scope,)).config_parameters[scope]["nominal"][
                parameter
            ]
            == expected
        ), module
