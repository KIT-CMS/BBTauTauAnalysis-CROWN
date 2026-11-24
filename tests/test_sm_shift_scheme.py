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
from analysis_configurations.bbtautau.constants import ERAS_RUN2
from analysis_configurations.bbtautau.tests.helpers import build

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
