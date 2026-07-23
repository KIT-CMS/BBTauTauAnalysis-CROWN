#!/usr/bin/env python3
"""Generate the synthetic correctionlib fixtures for the strict UParTAK4 b-tag
event-weight C++ test (``tests/cpp/test_btag_sf_strict.cxx``).

The fixtures are small, hand-chosen, *self-contained* correctionlib v2
payloads so the algebra of the strict consumer can be verified against
hand-computed numbers without depending on the real (large) pinned payload.
They mirror the real payload SCHEMA:

  * SF file ``btag_sf_strict_sf.json`` -- corrections
    ``UParTAK4_comb`` / ``UParTAK4_light`` / ``UParTAK4_wp_values``.
    SF nesting: Category(systematic) -> Category(working_point) ->
    Category(flavor:int) -> Binning(abseta) -> Binning(pt) -> value.
    ``UParTAK4_comb`` carries flavors {5, 4} and a comb-only systematic
    component ``hf`` (``up_hf`` / ``down_hf``); ``UParTAK4_light`` carries
    flavor {0} and the ``correlated`` / ``uncorrelated`` components. NO
    ``default`` on the systematic category, so an unknown variation key raises
    inside correctionlib (exercised by test case (e)).
  * efficiency file ``btag_sf_strict_eff.json`` -- correction
    ``btag_efficiency`` with nesting Category(sample_type) ->
    Category(working_point) -> Category(jet_flavor:int) -> Binning(eta) ->
    Binning(pt) -> value. Three sample_type regimes drive the throw tests:
      - ``valid``   : monotonic, in-(0,1] efficiencies (test a, d);
      - ``zero``    : flavor-5 medium-WP efficiency == 0 (test b, eff<=0);
      - ``nonmono`` : flavor-5 eff(M) < eff(T) (test c, non-monotonic).

Five WP keys are kept for dispatch realism; the algebra tests exercise the
M/T (b) and L/M (light) bins. Re-run this script to regenerate the JSONs after
changing any value; commit the JSONs alongside it.

Documented values (see the C++ test for the hand-computed weights):

  UParTAK4_comb SF(flavor 5): base = {L:0.98, M:0.95, T:0.90, XT:0.85, XXT:0.80}
  UParTAK4_comb SF(flavor 4): base = {L:0.90, M:0.88, T:0.85, XT:0.82, XXT:0.80}
    systematic delta: central 0, up +0.10, down -0.10, up_hf +0.10, down_hf -0.10
  UParTAK4_light SF(flavor 0): base = {L:0.98, M:0.96, T:0.94, XT:0.92, XXT:0.90}
    systematic delta: central 0, up +/-0.05, correlated +/-0.03, uncorrelated +/-0.02
  btag_efficiency valid:
    flavor 5: {L:0.80, M:0.60, T:0.40, XT:0.25, XXT:0.10}
    flavor 4: {L:0.50, M:0.30, T:0.15, XT:0.08, XXT:0.03}
    flavor 0: {L:0.20, M:0.05, T:0.02, XT:0.01, XXT:0.005}
  btag_efficiency zero    : == valid, but flavor 5 M -> 0.0
  btag_efficiency nonmono : flavor 5 -> {L:0.80, M:0.30, T:0.50, XT:0.25, XXT:0.10}
"""
import json
import os

WPS = ["L", "M", "T", "XT", "XXT"]  # loosest -> tightest (payload key order)

COMB_BASE = {
    5: {"L": 0.98, "M": 0.95, "T": 0.90, "XT": 0.85, "XXT": 0.80},
    4: {"L": 0.90, "M": 0.88, "T": 0.85, "XT": 0.82, "XXT": 0.80},
}
COMB_DELTA = {
    "central": 0.0,
    "up": 0.10,
    "down": -0.10,
    "up_hf": 0.10,
    "down_hf": -0.10,
}
LIGHT_BASE = {0: {"L": 0.98, "M": 0.96, "T": 0.94, "XT": 0.92, "XXT": 0.90}}
LIGHT_DELTA = {
    "central": 0.0,
    "up": 0.05,
    "down": -0.05,
    "up_correlated": 0.03,
    "down_correlated": -0.03,
    "up_uncorrelated": 0.02,
    "down_uncorrelated": -0.02,
}

EFF_VALID = {
    5: {"L": 0.80, "M": 0.60, "T": 0.40, "XT": 0.25, "XXT": 0.10},
    4: {"L": 0.50, "M": 0.30, "T": 0.15, "XT": 0.08, "XXT": 0.03},
    0: {"L": 0.20, "M": 0.05, "T": 0.02, "XT": 0.01, "XXT": 0.005},
}
EFF_ZERO = {
    5: dict(EFF_VALID[5], M=0.0),
    4: dict(EFF_VALID[4]),
    0: dict(EFF_VALID[0]),
}
EFF_NONMONO = {
    5: {"L": 0.80, "M": 0.30, "T": 0.50, "XT": 0.25, "XXT": 0.10},
    4: dict(EFF_VALID[4]),
    0: dict(EFF_VALID[0]),
}


def pt_binning(value):
    """Single-bin pt binning with a constant flow value."""
    return {
        "nodetype": "binning",
        "input": "pt",
        "edges": [20.0, 1000.0],
        "content": [value],
        "flow": value,
    }


def abseta_binning(value, edge=2.4):
    """Single-bin abseta binning; flow=error mirrors the real payload."""
    return {
        "nodetype": "binning",
        "input": "abseta",
        "edges": [0.0, edge],
        "content": [pt_binning(value)],
        "flow": "error",
    }


def flavor_category(base, systematic, wp, flavors):
    return {
        "nodetype": "category",
        "input": "flavor",
        "content": [
            {"key": flavor, "value": abseta_binning(base[flavor][wp] + systematic)}
            for flavor in flavors
        ],
    }


def sf_correction(name, base, delta, flavors):
    return {
        "name": name,
        "version": 1,
        "inputs": [
            {"name": "systematic", "type": "string"},
            {"name": "working_point", "type": "string"},
            {"name": "flavor", "type": "int"},
            {"name": "abseta", "type": "real"},
            {"name": "pt", "type": "real"},
        ],
        "output": {"name": "weight", "type": "real"},
        "data": {
            "nodetype": "category",
            "input": "systematic",
            # NO default: an unknown variation key raises (test case (e)).
            "content": [
                {
                    "key": syst,
                    "value": {
                        "nodetype": "category",
                        "input": "working_point",
                        "content": [
                            {
                                "key": wp,
                                "value": flavor_category(base, shift, wp, flavors),
                            }
                            for wp in WPS
                        ],
                    },
                }
                for syst, shift in delta.items()
            ],
        },
    }


def wp_values_correction():
    return {
        "name": "UParTAK4_wp_values",
        "version": 1,
        "inputs": [{"name": "working_point", "type": "string"}],
        "output": {"name": "cut", "type": "real"},
        "data": {
            "nodetype": "category",
            "input": "working_point",
            # Synthetic thresholds; the C++ takes wp_values as an argument, so
            # this correction is present for schema realism only.
            "content": [
                {"key": "L", "value": 0.1},
                {"key": "M", "value": 0.3},
                {"key": "T", "value": 0.5},
                {"key": "XT", "value": 0.7},
                {"key": "XXT", "value": 0.9},
            ],
        },
    }


def eff_flavor_category(regime, wp):
    return {
        "nodetype": "category",
        "input": "jet_flavor",
        "content": [
            {
                "key": flavor,
                "value": {
                    "nodetype": "binning",
                    "input": "eta",
                    "edges": [0.0, 2.5],
                    "content": [
                        {
                            "nodetype": "binning",
                            "input": "pt",
                            "edges": [20.0, 1000.0],
                            "content": [regime[flavor][wp]],
                            "flow": "clamp",
                        }
                    ],
                    "flow": "clamp",
                },
            }
            for flavor in (0, 4, 5)
        ],
    }


def eff_correction():
    regimes = {"valid": EFF_VALID, "zero": EFF_ZERO, "nonmono": EFF_NONMONO}
    return {
        "name": "btag_efficiency",
        "version": 1,
        "inputs": [
            {"name": "sample_type", "type": "string"},
            {"name": "working_point", "type": "string"},
            {"name": "jet_flavor", "type": "int"},
            {"name": "eta", "type": "real"},
            {"name": "pt", "type": "real"},
        ],
        "output": {"name": "efficiency", "type": "real"},
        "data": {
            "nodetype": "category",
            "input": "sample_type",
            "content": [
                {
                    "key": sample_type,
                    "value": {
                        "nodetype": "category",
                        "input": "working_point",
                        "content": [
                            {"key": wp, "value": eff_flavor_category(regime, wp)}
                            for wp in WPS
                        ],
                    },
                }
                for sample_type, regime in regimes.items()
            ],
        },
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))

    sf_payload = {
        "schema_version": 2,
        "description": "synthetic UParTAK4 b-tag SF fixture (strict consumer test)",
        "corrections": [
            sf_correction("UParTAK4_comb", COMB_BASE, COMB_DELTA, [5, 4]),
            sf_correction("UParTAK4_light", LIGHT_BASE, LIGHT_DELTA, [0]),
            wp_values_correction(),
        ],
    }
    eff_payload = {
        "schema_version": 2,
        "description": "synthetic b-tag efficiency fixture (strict consumer test)",
        "corrections": [eff_correction()],
    }

    with open(os.path.join(here, "btag_sf_strict_sf.json"), "w") as handle:
        json.dump(sf_payload, handle, indent=2)
        handle.write("\n")
    with open(os.path.join(here, "btag_sf_strict_eff.json"), "w") as handle:
        json.dump(eff_payload, handle, indent=2)
        handle.write("\n")
    print("wrote btag_sf_strict_sf.json and btag_sf_strict_eff.json to", here)


if __name__ == "__main__":
    main()
