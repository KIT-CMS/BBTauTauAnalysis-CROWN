"""Export the SM selection contract for TauFakeFactors parity.

The 2018 b-tag efficiency measurement in TauFakeFactors runs its own
preselection over the CROWN probe-jet ntuples. That preselection must reproduce
*exactly* the event selection the CROWN ``sm_btag_efficiency_config`` already
applied, otherwise the efficiencies are measured on a different event sample
than the one the SM analysis uses. This script freezes that selection into a
machine-readable contract so the two repos cannot silently drift apart: the
TauFakeFactors parity test parses each ``preselection_<channel>.yaml`` and
asserts every contract threshold appears with the same value.

The contract is dumped from a *built* configuration of
``SM_BTAG_EFFICIENCY_PROFILE`` (``sm_btag_efficiency_config``), NOT the
production ``SM_PROFILE``: the efficiency profile carries the identical object /
trigger / tau definitions but has ``enable_btag_sf=False``.

Two source classes are recorded per channel and both are marked in the YAML:

* ``config_derived`` -- read straight out of the built config's per-scope
  ``config_parameters`` (trigger flag + offline pt, light-lepton and tau object
  kinematics, tau-ID working points, probe-jet acceptance);
* ``analysis_baseline`` -- the standard SM H->tautau signal-region cuts that are
  applied downstream of CROWN rather than being CROWN object-selection
  parameters (light-lepton relative isolation, transverse-mass window, the
  opposite-sign charge requirement, the extra-lepton vetoes, and the
  channel-specific vs-muon working point).

Usage
-----
    # from the CROWN repo root (so analysis_configurations imports resolve)
    python3 analysis_configurations/bbtautau/scripts/export_sm_selection_contract.py \
        --output analysis_configurations/bbtautau/scripts/selection_contract_2018_v1.yaml

The exported YAML is committed on the TauFakeFactors side under
``configs/btag_efficiency/2018/selection_contract_2018_v1.yaml``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Dict, List

import yaml

# Allow running as a plain script (python3 .../export_sm_selection_contract.py)
# from the CROWN repo root: make the package importable regardless of cwd.
_ANALYSIS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CROWN_ROOT = os.path.dirname(os.path.dirname(_ANALYSIS_ROOT))
if _CROWN_ROOT not in sys.path:
    sys.path.insert(0, _CROWN_ROOT)

from analysis_configurations.bbtautau import sm_btag_efficiency_config  # noqa: E402
from analysis_configurations.bbtautau.constants import (  # noqa: E402
    LEGACY_AVAILABLE_SAMPLES,
    SCOPES,
)

CONTRACT_VERSION = "2018_v1"
ERA = "2018"

# Channels the SM analysis (and the efficiency measurement) run on.
CHANNELS: List[str] = ["et", "mt", "tt"]

# Standard SM H->tautau signal-region cuts applied by the TauFakeFactors
# preselection downstream of CROWN (not CROWN object-selection parameters).
LEPTON_ISO_MAX = 0.15
TRANSVERSE_MASS_MAX = 50.0

# Channel-specific hadronic-tau-vs-muon working point applied as the SR cut.
# The vs-jet / vs-electron working points come straight from the config
# (tau_ides_sf_vsjet_wp / tau_ides_sf_vsele_wp); the vs-muon cut WP is the
# standard HTT channel convention (muon channel tightens vs-muon; the e-tau and
# tau-tau channels keep it loose).
VS_MU_WP_BY_CHANNEL = {"et": "VLoose", "mt": "Tight", "tt": "VLoose"}

# Extra-lepton vetoes per channel (the tau-tau channel carries no di-lepton
# veto column).
VETOES_BY_CHANNEL = {
    "et": ["extraelec_veto", "extramuon_veto", "dilepton_veto"],
    "mt": ["extraelec_veto", "extramuon_veto", "dilepton_veto"],
    "tt": ["extraelec_veto", "extramuon_veto"],
}


def _decay_modes(raw: str) -> List[int]:
    """Parse the CROWN ``tight_tau_decay_modes`` string (e.g. ``'0, 1, 10, 11'``)."""
    return [int(token.strip()) for token in str(raw).split(",") if token.strip() != ""]


def build_configuration():
    """Build the SM_BTAG_EFFICIENCY_PROFILE config (no payload gate)."""
    return sm_btag_efficiency_config.build_config(
        ERA,
        "ttbar",
        list(CHANNELS),
        {"none"},
        LEGACY_AVAILABLE_SAMPLES,
        [ERA],
        SCOPES,
    )


def _tau_baseline(params: Dict, channel: str) -> Dict:
    """Common hadronic-tau object baseline (config-derived + WPs)."""
    return {
        "min_pt": float(params["tight_tau_min_pt"]),
        "max_abs_eta": float(params["tight_tau_max_abs_eta"]),
        "max_abs_dz": float(params["tight_tau_max_abs_dz"]),
        "decay_modes": _decay_modes(params["tight_tau_decay_modes"]),
        # vs-jet / vs-ele read from the config; vs-mu is the channel SR convention.
        "vs_jet_wp": str(params["tau_ides_sf_vsjet_wp"]),
        "vs_ele_wp": str(params["tau_ides_sf_vsele_wp"]),
        "vs_mu_wp": VS_MU_WP_BY_CHANNEL[channel],
    }


def _probe_jet(params: Dict) -> Dict:
    return {
        "min_pt": float(params["btag_probe_min_pt"]),
        "max_abs_eta": float(params["btag_probe_max_abs_eta"]),
    }


def _et_channel(params: Dict) -> Dict:
    ele_trigger = params["ele_trigger"][0]
    return {
        "trigger": {
            "flags": [str(ele_trigger["flagname"])],
            "lepton_min_pt": float(ele_trigger["min_pt"]),
        },
        "lepton": {
            "kind": "electron",
            "min_pt": float(params["tight_electron_min_pt"]),
            "max_abs_eta": float(params["tight_electron_max_abs_eta"]),
            "max_abs_dxy": float(params["tight_electron_max_abs_dxy"]),
            "max_abs_dz": float(params["tight_electron_max_abs_dz"]),
            "id": str(params["tight_electron_id"]),
            "max_iso": LEPTON_ISO_MAX,
        },
        "tau": _tau_baseline(params, "et"),
        "transverse_mass_max": TRANSVERSE_MASS_MAX,
        "charge_requirement": "opposite_sign",
        "vetoes": VETOES_BY_CHANNEL["et"],
        "probe_jet": _probe_jet(params),
    }


def _mt_channel(params: Dict) -> Dict:
    mu_trigger = params["mu_trigger"][0]
    return {
        "trigger": {
            "flags": [str(mu_trigger["flagname"])],
            "lepton_min_pt": float(mu_trigger["min_pt"]),
        },
        "lepton": {
            "kind": "muon",
            "min_pt": float(params["tight_muon_min_pt"]),
            "max_abs_eta": float(params["tight_muon_max_abs_eta"]),
            "max_abs_dxy": float(params["tight_muon_max_abs_dxy"]),
            "max_abs_dz": float(params["tight_muon_max_abs_dz"]),
            "max_iso": LEPTON_ISO_MAX,
        },
        "tau": _tau_baseline(params, "mt"),
        "transverse_mass_max": TRANSVERSE_MASS_MAX,
        "charge_requirement": "opposite_sign",
        "vetoes": VETOES_BY_CHANNEL["mt"],
        "probe_jet": _probe_jet(params),
    }


def _tt_channel(params: Dict) -> Dict:
    tautau_trigger = params["tautau_trigger"][0]
    return {
        "trigger": {
            "flags": [str(tautau_trigger["flagname"])],
            "tau_min_pt": float(tautau_trigger["p1_min_pt"]),
        },
        "tau": _tau_baseline(params, "tt"),
        "charge_requirement": "opposite_sign",
        "vetoes": VETOES_BY_CHANNEL["tt"],
        "probe_jet": _probe_jet(params),
    }


CHANNEL_BUILDERS = {"et": _et_channel, "mt": _mt_channel, "tt": _tt_channel}


def build_contract() -> Dict:
    """Assemble the selection-contract payload (without ``contract_sha256``)."""
    configuration = build_configuration()
    channels: Dict[str, Dict] = {}
    for channel in CHANNELS:
        params = configuration.config_parameters[channel]["nominal"]
        channels[channel] = CHANNEL_BUILDERS[channel](params)

    return {
        "contract_version": CONTRACT_VERSION,
        "profile": "sm_btag_efficiency",
        "source_config": "sm_btag_efficiency_config",
        "era": ERA,
        "description": (
            "SM HH->bbtautau event-selection baseline exported from the bbtautau "
            "CROWN sm_btag_efficiency_config (SM_BTAG_EFFICIENCY_PROFILE) for "
            "parity with the TauFakeFactors 2018 b-tag efficiency preselection. "
            "Trigger flag/pt, light-lepton and tau kinematics, tau-ID vs-jet / "
            "vs-electron working points and probe-jet acceptance are read from the "
            "built config; light-lepton isolation, the transverse-mass window, the "
            "opposite-sign requirement, the vetoes and the vs-muon working point "
            "are the standard SM signal-region baseline applied by preselection."
        ),
        "channels": channels,
    }


def contract_sha256(contract: Dict) -> str:
    """Deterministic SHA256 over the canonical serialization of the content.

    The ``contract_sha256`` field itself is excluded from the digest input. The
    canonical form is compact, key-sorted JSON so the digest is reproducible
    across repos (the TauFakeFactors side recomputes it the same way).
    """
    payload = {key: value for key, value in contract.items() if key != "contract_sha256"}
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the SM selection contract for TauFakeFactors parity."
    )
    parser.add_argument(
        "--output",
        default="selection_contract_2018_v1.yaml",
        help="Path to write the contract YAML to (default: ./selection_contract_2018_v1.yaml).",
    )
    return parser


def main(argv=None) -> None:
    args = build_arg_parser().parse_args(argv)
    contract = build_contract()
    contract["contract_sha256"] = contract_sha256(contract)

    with open(args.output, "w") as handle:
        handle.write(
            "# AUTO-GENERATED by "
            "analysis_configurations/bbtautau/scripts/export_sm_selection_contract.py\n"
            "# Do not edit by hand: regenerate from the built SM config so the\n"
            "# contract_sha256 stays consistent with the CROWN selection.\n"
        )
        yaml.safe_dump(contract, handle, sort_keys=False, default_flow_style=False)
    print(f"Wrote selection contract to {args.output}")
    print(f"contract_sha256 = {contract['contract_sha256']}")


if __name__ == "__main__":
    main()
