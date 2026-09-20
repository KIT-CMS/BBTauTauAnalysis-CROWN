"""Cross-repository light-dilepton production and calibration contracts."""

from pathlib import Path

import pytest

from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    output_names,
    producer_names,
)

CONTROLS = ("ee", "em", "mm")
PROBES = {f"btag_probe_jet_{name}" for name in ("pt", "eta", "hadron_flavour", "upart")}
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


@pytest.mark.parametrize("sample", ["data", "ttbar", "dyjets"])
def test_main_control_output_contract(sample):
    config = build("sm_config", sample, scopes=CONTROLS)
    for scope in CONTROLS:
        outputs = output_names(config, scope)
        params = config.config_parameters[scope]["nominal"]
        assert params["bjet_eff_file"].endswith(f"/btag_efficiency_{scope}.json.gz")
        if sample == "data":
            assert not (outputs & LEPTON_SFS[scope])
            assert "btag_weight_upart" not in outputs
        else:
            assert {s for s in LEPTON_SFS[scope] if not s.startswith("trg_")} <= outputs
            assert "btag_weight_upart" in outputs
        if scope in ("ee", "em"):
            assert params["tight_electron_min_pt"] == 15.0
            assert params["tight_electron_max_iso"] == 0.4
        if scope in ("mm", "em"):
            assert params["tight_muon_min_pt"] == 15.0
            assert params["tight_muon_max_iso"] == 0.4
        assert "SingleEleTriggerSF" not in producer_names(config, scope)
        # The Z pair comes from the core algorithm (pt ordering fixed upstream),
        # not from an analysis-specific copy.
        z_pair = {"ee": "ZElElPairSelection", "mm": "ZMuMuPairSelection"}.get(scope)
        if z_pair:
            assert z_pair in producer_names(config, scope)
        assert not {
            n for n in producer_names(config, scope) if n.startswith("ControlZ")
        }


def test_electron_reco_weight_is_the_era_keyed_addon_call():
    """The reco weight picks the payload's pt category itself, so the call
    carries the era id instead of a fixed category name."""
    config = build("sm_config", "ttbar", scopes=CONTROLS)
    for producer, leg in (("Ele_1_Reco_SF", 1), ("Ele_2_Reco_SF", 2)):
        reco = find_producer(config, "ee", producer)
        assert "xyh::scalefactor::electron_reco(" in reco.call
        assert "{ele_sf_year_id}" in reco.call
        assert [q.name for q in reco.get_inputs("ee")] == [
            f"pt_{leg}",
            f"eta_{leg}",
            f"phi_{leg}",
        ]
        assert [q.name for q in reco.get_outputs("ee")] == [f"reco_wgt_ele_{leg}"]


@pytest.mark.parametrize("sample", ["ttbar", "dyjets"])
def test_control_probe_collection_has_no_tag_requirement(sample):
    config = build("sm_btag_efficiency_config", sample, scopes=CONTROLS)
    for scope in CONTROLS:
        outputs = output_names(config, scope)
        assert (
            PROBES | {s for s in LEPTON_SFS[scope] if not s.startswith("trg_")}
            <= outputs
        )
        assert (
            not {"n_bjets", "mass_tautaubb", "btag_weight_upart", "id_wgt_bjet"}
            & outputs
        )
        mask = find_producer(config, scope, "BtagProbeJetMask")
        assert [q.name for q in mask.get_inputs(scope)] == [
            "base_bjets_mask",
            "jet_overlap_veto_mask",
        ]


@pytest.mark.parametrize(
    "module,sample",
    [("sm_config", s) for s in ("data", "ttbar", "dyjets")]
    + [("sm_btag_efficiency_config", s) for s in ("ttbar", "dyjets")],
)
def test_control_actual_cpp_generation(module, sample, tmp_path):
    """Exercise placeholder expansion and source emission, not just DAG validation."""
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[3]
    script = """
import sys
from analysis_configurations.bbtautau.tests.helpers import build
from code_generation.code_generation import CodeGenerator
module, sample, output = sys.argv[1:]
config = build(module, sample, scopes=("ee", "em", "mm"))
generator = CodeGenerator("code_generation/analysis_template.cxx", "code_generation/subset_template.cxx", config, "bbtautau", module, f"{module}_{sample}_2018", output)
generator.generate_code()
from analysis_configurations.bbtautau.tests.test_sm_control_channels import LEPTON_SFS
for scope in ("ee", "em", "mm"):
    outputs = set(generator.output_commands[scope])
    if sample != "data":
        assert LEPTON_SFS[scope] <= outputs, (scope, LEPTON_SFS[scope] - outputs)
    else:
        assert not LEPTON_SFS[scope] & outputs
"""
    result = subprocess.run(
        [sys.executable, "-c", script, module, sample, str(tmp_path)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert list(tmp_path.rglob("*.cxx"))


@pytest.mark.parametrize(
    "scope,parameter", [("et", "tight_electron_max_iso"), ("mt", "tight_muon_max_iso")]
)
def test_sm_tau_channels_keep_the_lepton_isolation_sideband(scope, parameter):
    """One SM production serves the nominal iso < 0.15 selection and the
    anti-isolated sidebands up to 0.5; NMSSM keeps the 0.4 object default."""
    for module, expected in (
        ("sm_config", 0.5),
        ("sm_btag_efficiency_config", 0.5),
        ("nmssm_config", 0.4),
    ):
        params = build(module, "ttbar", scopes=(scope,)).config_parameters[scope][
            "nominal"
        ]
        assert params[parameter] == expected, module
