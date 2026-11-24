"""The shift inventory of sm_config (v8 spec 3.2 and section 4, C30).

Every shift pair of the SM shift production, written out per family: the eras, sample types
and scopes that carry it, and what it may change. The tests compare

- the shifts every sample type registers in every Run-2 era and scope with this list, so a
  shift that appears, vanishes or moves to another scope fails here before it reaches a
  production (ShapeSmith requires the shifts of the n-tuples and its declarations to agree);
- the shifted columns of the generated code with it: every registered shift has shifted
  columns, a weight shift changes the columns of its weight only, and a kinematic shift
  reaches the columns it is meant for.
"""

from dataclasses import dataclass
import re
from typing import Callable

import pytest

from analysis_configurations.bbtautau.constants import (
    ERAS_RUN2,
    RUN2_V15_RECOIL_CORRECTION_ERAS,
    SCOPES,
)
from analysis_configurations.bbtautau.tests.helpers import build, generate_code
import analysis_configurations.bbtautau.sm_config as sm_config

ALGO = "DeepTau2018v2p5"
DECAY_MODES = (0, 1, 10, 11)
ALL_SCOPES = tuple(SCOPES)
TAU_SCOPES = ("et", "mt", "tt")
MC = tuple(s for s in sm_config.AVAILABLE_SAMPLES if s not in ("data", "embedding"))


def recoil_corrected(era, sample):
    """DY and W of the eras with the Run-2 v15 recoil correction."""
    return era in RUN2_V15_RECOIL_CORRECTION_ERAS and sample in ("dyjets", "wjets")


def simulated(era, sample):
    return sample in MC


@dataclass(frozen=True)
class Family:
    """A family of shift pairs: their names in an era and scope, the samples that carry them,
    and the columns they change. ``weights`` matches the only columns a weight shift may
    change; ``reaches`` names columns a kinematic shift must change and ``spares`` columns it
    must leave alone (by scope where they differ). The jets are cleaned against the pair, so
    every shift that can change the pair rewrites the jet columns as well."""

    name: str
    pairs: Callable  # (era, scope) -> shift names without Up/Down
    samples: Callable = simulated  # (era, sample) -> bool
    weights: str = ""
    reaches: Callable = lambda scope: ()
    spares: Callable = lambda scope: ()


def in_scopes(scopes, names):
    """``names(era)`` in ``scopes``, nothing elsewhere."""
    return lambda era, scope: set(names(era)) if scope in scopes else set()


def jet_columns(scope):
    return ("jpt_1", "jpt_2", "n_jets", "n_bjets", "bpair_pt_1", "bpair_m_inv", "met", "metphi")


def lepton_leg(scope):
    """The pT of the light lepton and of the tau of a scope."""
    return {"et": "pt_1", "mt": "pt_1", "em": "pt_2"}.get(scope)


FAMILIES = [
    # --- kinematic ---------------------------------------------------------------------
    Family(
        "jet energy scale, regrouped sources",
        in_scopes(ALL_SCOPES, lambda era: {
            *(f"CMS_scale_j_{source}" for source in ("Absolute", "BBEC1", "EC2", "FlavorQCD", "HF", "RelativeBal")),
            *(f"CMS_scale_j_{source}_{era}" for source in ("Absolute", "BBEC1", "EC2", "HF", "RelativeSample")),
        }),
        reaches=jet_columns,
        spares=lambda scope: ("pt_1", "pt_2", "m_vis"),
    ),
    Family(
        "jet energy resolution, six regions (C33)",
        in_scopes(ALL_SCOPES, lambda era: {
            f"CMS_res_j_{region}_{era}"
            for region in (
                "eta0to1p93", "eta1p93to2p5", "eta2p5to3_ptlt50", "eta2p5to3_ptgt50",
                "eta3to5_ptlt50", "eta3to5_ptgt50",
            )
        }),
        reaches=lambda scope: ("jpt_1", "jpt_2", "n_jets", "bpair_pt_1"),
        spares=lambda scope: ("pt_1", "pt_2", "m_vis"),
    ),
    Family(
        "unclustered energy, not on recoil-corrected samples (C38)",
        in_scopes(ALL_SCOPES, lambda era: {f"CMS_scale_met_unclustered_energy_{era}"}),
        samples=lambda era, sample: sample in MC and not recoil_corrected(era, sample),
        reaches=lambda scope: ("met", "metphi", "met_uncorrected"),
        spares=lambda scope: ("pt_1", "pt_2", "m_vis", "jpt_1", "n_jets"),
    ),
    Family(
        "recoil calibration",
        in_scopes(ALL_SCOPES, lambda era: {
            f"CMS_scale_met_RecoilCalibration_{era}", f"CMS_res_met_RecoilCalibration_{era}",
        }),
        samples=recoil_corrected,
        reaches=lambda scope: ("met", "metphi"),
        spares=lambda scope: ("pt_1", "pt_2", "m_vis", "jpt_1", "n_jets", "met_uncorrected"),
    ),
    Family(
        "electron energy scale and resolution",
        in_scopes(ALL_SCOPES, lambda era: {f"CMS_scale_e_{era}", f"CMS_res_e_{era}"}),
        reaches=lambda scope: {"et": ("pt_1", "m_vis"), "em": ("pt_1", "m_vis"), "ee": ("pt_1", "pt_2")}.get(
            scope, ("extraelec_veto",)
        ),
        spares=lambda scope: ("met_uncorrected", "met_jetcorrected"),
    ),
    Family(
        "tau energy scale, genuine taus per decay mode (C21)",
        in_scopes(TAU_SCOPES, lambda era: {
            f"CMS_scale_t_{ALGO}_DM{dm}_genTau_{era}" for dm in DECAY_MODES
        }),
        reaches=lambda scope: ("pt_2", "m_vis", "met", "mt_2", lepton_leg(scope) or "pt_1"),
    ),
    Family(
        "tau energy scale, e -> tau fakes, et only (C29)",
        in_scopes(("et",), lambda era: {
            f"CMS_scale_t_{ALGO}_DM{dm}_genElectron_{region}_{era}"
            for dm in DECAY_MODES
            for region in ("barrel", "endcap")
        }),
        reaches=lambda scope: ("pt_2", "m_vis", "met", "pt_1"),
    ),
    Family(
        "tau energy scale, mu -> tau fakes per decay mode, mt only (C21, C29)",
        in_scopes(("mt",), lambda era: {
            f"CMS_scale_t_{ALGO}_DM{dm}_genMuon_{era}" for dm in DECAY_MODES
        }),
        reaches=lambda scope: ("pt_2", "m_vis", "met", "pt_1"),
    ),
    Family(
        "muon energy scale (C37)",
        lambda era, scope: {
            f"CMS_scale_m_{region}_{era}"
            for region in {
                "mt": ("etalt1p2", "eta1p2to2p1"),
                "em": ("etalt1p2", "eta1p2to2p1", "eta2p1to2p4"),
            }.get(scope, ())
        },
        samples=lambda era, sample: sample != "data",
        reaches=lambda scope: (lepton_leg(scope), "m_vis", "met", "metphi", "nmuons"),
        spares=lambda scope: ("met_uncorrected", "met_jetcorrected", "dilepton_veto"),
    ),
    # --- weights -----------------------------------------------------------------------
    Family(
        "tau vsJet SF, with syst_TES (C18)",
        in_scopes(TAU_SCOPES, lambda era: {
            *(f"CMS_eff_t_{ALGO}_VSjet_dm_stat{i}_DM{dm}_{era}" for i in (1, 2) for dm in DECAY_MODES),
            f"CMS_eff_t_{ALGO}_VSjet_dm_syst_alleras",
            f"CMS_eff_t_{ALGO}_VSjet_dm_syst_{era}",
            *(f"CMS_eff_t_{ALGO}_VSjet_dm_syst_TES_{era}_dm{dm}" for dm in DECAY_MODES),
        }),
        weights=r"id_wgt_tau_vsJet_\w+_[12]",
    ),
    Family(
        "tau vsEle SF",
        in_scopes(TAU_SCOPES, lambda era: {
            f"CMS_fake_t_{ALGO}_VSe_DM{dm}_{region}_{era}"
            for dm in DECAY_MODES
            for region in ("barrel", "endcap")
        }),
        weights=r"id_wgt_tau_vsEle_\w+_[12]",
    ),
    Family(
        "tau vsMu SF",
        in_scopes(TAU_SCOPES, lambda era: {
            f"CMS_fake_t_{ALGO}_VSmu_wheel{wheel}_{era}" for wheel in range(1, 6)
        }),
        weights=r"id_wgt_tau_vsMu_\w+_[12]",
    ),
    Family(
        "pileup",
        in_scopes(ALL_SCOPES, lambda era: {f"CMS_pileup_{era}"}),
        weights=r"puweight",
    ),
    Family(
        "QCD scale, diboson included (C34)",
        in_scopes(ALL_SCOPES, lambda era: {"QCDscale_ren", "QCDscale_fac"}),
        weights=r"lhe_scale_weight",
    ),
    Family(
        "parton shower, ISR and FSR scale (C23)",
        in_scopes(ALL_SCOPES, lambda era: {"ps_isr", "ps_fsr"}),
        weights=r"ps_weight",
    ),
    Family(
        "muon ID and isolation SF",
        in_scopes(("mt", "em", "mm"), lambda era: {f"CMS_eff_m_id_{era}", f"CMS_eff_m_iso_{era}"}),
        weights=r"(id|iso)_wgt_mu_[12]",
    ),
    Family(
        "muon trigger SF",
        in_scopes(("mt", "em", "mm"), lambda era: {f"CMS_eff_m_trigger_{era}"}),
        weights=r"trg_wgt_single_mu\w*",
    ),
    Family(
        "electron ID SF",
        in_scopes(("et", "em", "ee"), lambda era: {f"CMS_eff_e_id_{era}"}),
        weights=r"(id|reco)_wgt_ele_[12]",
    ),
    Family(
        "electron trigger SF",
        in_scopes(("et", "ee"), lambda era: {f"CMS_eff_e_trigger_{era}"}),
        weights=r"trg_wgt_single_ele\w*",
    ),
    Family(
        "di-tau trigger SF per decay mode (C39)",
        in_scopes(("tt",), lambda era: {f"CMS_eff_trigger_tt_dm{dm}_{era}" for dm in DECAY_MODES}),
        weights=r"trg_wgtdouble_tau\w*",
    ),
    # --- embedding -----------------------------------------------------------------------
    Family(
        "embedding tau energy scale",
        in_scopes(TAU_SCOPES, lambda era: {f"CMS_scale_t_emb_{ALGO}_DM{dm}_{era}" for dm in DECAY_MODES}),
        samples=lambda era, sample: sample == "embedding",
        reaches=lambda scope: ("pt_2", "m_vis", "met", lepton_leg(scope) or "pt_1"),
    ),
    Family(
        "embedding tau vsJet SF",
        in_scopes(TAU_SCOPES, lambda era: {f"CMS_eff_t_emb_{ALGO}_VSjet_DM{dm}_{era}" for dm in DECAY_MODES}),
        samples=lambda era, sample: sample == "embedding",
        weights=r"id_wgt_tau_vsJet_\w+_[12]",
    ),
    Family(
        "embedding electron energy scale (C32)",
        in_scopes(("et",), lambda era: {f"CMS_scale_e_{region}_emb_{era}" for region in ("barrel", "endcap")}),
        samples=lambda era, sample: sample == "embedding",
        reaches=lambda scope: ("pt_1", "m_vis", "met", "metphi", "nelectrons"),
        spares=lambda scope: ("met_uncorrected", "met_jetcorrected", "dilepton_veto"),
    ),
]

# The number of pairs per scope: simulation, the recoil-corrected DY and W (two recoil pairs
# for the unclustered energy pair), embedding
PAIRS = {
    "mc": {"et": 66, "mt": 65, "tt": 60, "em": 32, "ee": 27, "mm": 28},
    "recoil": {"et": 67, "mt": 66, "tt": 61, "em": 33, "ee": 28, "mm": 29},
    "embedding": {"et": 10, "mt": 10, "tt": 8},
    "data": {scope: 0 for scope in ALL_SCOPES},
}


def scopes_of(sample):
    return TAU_SCOPES if sample == "embedding" else ALL_SCOPES


def expected_pairs(era, sample, scope):
    """Family -> shift pairs of a sample type in an era and scope."""
    return {
        family.name: family.pairs(era, scope)
        for family in FAMILIES
        if family.samples(era, sample) and family.pairs(era, scope)
    }


def both_directions(pairs):
    return {f"{pair}{direction}" for pair in pairs for direction in ("Up", "Down")}


@pytest.mark.parametrize("sample", sm_config.AVAILABLE_SAMPLES)
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_shift_inventory(era, sample):
    """The registered shifts of every sample type, era and scope are the listed pairs, both
    directions each."""
    scopes = scopes_of(sample)
    config = build("sm_config", sample, era=era, scopes=scopes, shifts=("all",))
    kind = (
        sample if sample in ("data", "embedding") else "recoil" if recoil_corrected(era, sample) else "mc"
    )
    for scope in scopes:
        families = expected_pairs(era, sample, scope)
        expected = set().union(*families.values()) if families else set()
        assert sum(map(len, families.values())) == len(expected), "a pair in two families"
        registered = {name.removeprefix("__") for name in config.shifts.get(scope, {})}
        assert registered == both_directions(expected), (
            scope,
            sorted(registered ^ both_directions(expected)),
        )
        assert len(expected) == PAIRS[kind][scope], scope


# The surfaces whose generated code is checked column by column: the sample types that differ
# in their shifts, in every era
COLUMN_SURFACES = [
    pytest.param(era, sample, id=f"{era}-{sample}")
    for era in ERAS_RUN2
    for sample in ("ttbar", "dyjets", "diboson", "hh2b2tau", "embedding")
]


@pytest.mark.parametrize("era,sample", COLUMN_SURFACES)
def test_shifted_columns(era, sample):
    """In the generated code, every registered shift has shifted columns and no column has an
    unregistered shift (a shift registered for a sample without the producer behind it has
    none, as the QCD scale on diboson had); a weight shift changes the columns of its weight
    and nothing else, in particular no kinematic column; a kinematic shift changes the
    columns it is meant for and leaves alone those of other objects."""
    scopes = scopes_of(sample)
    generated = generate_code("sm_config", sample, era=era, scopes=scopes, shifts=("all",))
    for scope in scopes:
        columns = {}
        nominal = set()
        for output in generated.outputs[scope]:
            name, _, shift = output.partition("__")
            if shift:
                columns.setdefault(shift, set()).add(name)
            else:
                nominal.add(name)
        families = expected_pairs(era, sample, scope)
        expected = set().union(*families.values()) if families else set()
        assert set(columns) == both_directions(expected), (
            scope,
            sorted(set(columns) ^ both_directions(expected)),
        )
        for family in FAMILIES:
            for shift in both_directions(families.get(family.name, ())):
                shifted = columns[shift]
                assert shifted <= nominal, (scope, shift)
                if family.weights:
                    unexpected = {c for c in shifted if not re.fullmatch(family.weights, c)}
                    assert not unexpected, (scope, shift, sorted(unexpected))
                else:
                    reaches = {c for c in family.reaches(scope) if c}
                    assert reaches <= nominal, (scope, shift, sorted(reaches - nominal))
                    assert reaches <= shifted, (scope, shift, sorted(reaches - shifted))
                    assert not set(family.spares(scope)) & shifted, (
                        scope,
                        shift,
                        sorted(set(family.spares(scope)) & shifted),
                    )
