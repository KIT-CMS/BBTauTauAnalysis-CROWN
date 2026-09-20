"""Surfaces of the Run-2 NanoAOD-v15 adaption that fail silently when they drift."""

from pathlib import Path

from analysis_configurations.bbtautau.producers import taus

CROWN_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = CROWN_ROOT / "analysis_configurations" / "bbtautau"
BUILD_SCRIPTS = sorted((ANALYSIS_ROOT / "build_scripts").glob("test_build_*.sh"))


def test_analysis_identity_is_bbtautau():
    """Folder, generators, build scripts and init.sh agree on the analysis name."""
    generate = (ANALYSIS_ROOT / "generate.py").read_text()
    generate_friends = (ANALYSIS_ROOT / "generate_friends.py").read_text()
    init_script = (CROWN_ROOT / "init.sh").read_text()
    scripts = [script.read_text() for script in BUILD_SCRIPTS]
    assert BUILD_SCRIPTS
    assert (
        'analysis_name = "bbtautau"' in generate
        and 'analysis_name = "bbtautau"' in generate_friends
    )
    assert all('local analysis="bbtautau"' in script for script in scripts)
    assert (
        "bbtautau)" in init_script
        and 'REPO="git@github.com:KIT-CMS/BBTauTauAnalysis-CROWN.git"' in init_script
    )
    assert "xyh_bbtautau" not in "\n".join(
        [generate, generate_friends, init_script, *scripts]
    )


def test_tau_pt_correction_matches_current_crown_signature():
    call = taus.TauPtCorrectionMC.call
    ordered_arguments = [
        '"{tau_id_algorithm}"',
        '"{tau_ides_sf_vsjet_wp}"',
        '"{tau_ides_sf_vsele_wp}"',
        "{vec_open}{tight_tau_decay_modes}{vec_close}",
        '"{tau_elefake_es_DM0_barrel}"',
        '"{tau_elefake_es_DM1_barrel}"',
        '"{tau_elefake_es_DM0_endcap}"',
        '"{tau_elefake_es_DM1_endcap}"',
        '"{tau_mufake_es}"',
        '"{tau_ES_shift_DM0}"',
        '"{tau_ES_shift_DM1}"',
        '"{tau_ES_shift_DM10}"',
        '"{tau_ES_shift_DM11}"',
    ]
    positions = [call.index(argument) for argument in ordered_arguments]
    assert positions == sorted(positions)
