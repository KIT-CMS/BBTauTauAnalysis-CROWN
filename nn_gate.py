"""Gate of the NN classifier friend (nn spec 3.4, N21): the models score only the events of the ShapeSmith tau skims.

``skim_cuts(channel, era)`` is ShapeSmith's ``cuts.skim_cuts(channel, era, control_regions=True)``
(BBTauTauAnalysis-ShapeSmith 2794db9, ``src/bbtautau_shapesmith/cuts.py:63-74``, triggers from ``triggers.py``): the
baseline without the opposite-sign requirement, with the loosest tau isolation (VVVLoose), >= 2 jets or a b pair with
a b tag, and in et and mt without the mT cut and with the lepton isolation below 0.5. That is the selection of the
``tau_control`` skims, and it contains the one of the ``tau_ff`` skims (``control_regions=False``) cut by cut, so
every event of either skim is scored (tests/test_nn_classifier_friend.py; ShapeSmith's sample cuts only remove
events). The friend writes -1 into every output of the other events and does not evaluate the models on them.

The cuts are written in ShapeSmith's syntax (pandas.eval) and translated for RDataFrame by ``cpp_expression``.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

YEARS = {"2016preVFP": "2016", "2016postVFP": "2016", "2017": "2017", "2018": "2018"}
HEM_ERAS = ("2018",)  # the veto of the events with a jet in the HEM 15/16 region (column hem_veto, 2018 only)

# The cuts of every era, per channel: tau legs (vsMu, vsEle WPs of the channel, VVVLoose vsJet) and selection.
_LEPTON_TAU = {
    "extraelec_veto": "(extraelec_veto < 0.5)",
    "extramuon_veto": "(extramuon_veto < 0.5)",
    "b_tagging": "(n_jets >= 2) | ((n_bjets >= 1) & (bpair_pt_2 > 0))",
    "against_muon": "(id_tau_vsMu_{vs_mu}_2 > 0.5)",
    "against_electron": "(id_tau_vsEle_{vs_ele}_2 > 0.5)",
    "tau_iso": "(id_tau_vsJet_VVVLoose_2 > 0.5)",
    "dilepton_veto": "(dilepton_veto < 0.5)",
    "lepton_iso": "iso_1 < 0.5",
    "tau_eta": "(abs(eta_2) < 2.3)",
    "lepton_eta": "(abs(eta_1) < 2.1)",
}
CHANNEL_CUTS = {
    "et": {name: cut.format(vs_mu="VLoose", vs_ele="Tight") for name, cut in _LEPTON_TAU.items()},
    "mt": {name: cut.format(vs_mu="Tight", vs_ele="VVLoose") for name, cut in _LEPTON_TAU.items()},
    "tt": {
        "extraelec_veto": "(extraelec_veto < 0.5)",
        "extramuon_veto": "(extramuon_veto < 0.5)",
        "b_tagging": "(n_jets >= 2) | ((n_bjets >= 1) & (bpair_pt_2 > 0))",
        "against_muon": "(id_tau_vsMu_VLoose_1 > 0.5) & (id_tau_vsMu_VLoose_2 > 0.5)",
        "against_electron": "(id_tau_vsEle_VVLoose_1 > 0.5) & (id_tau_vsEle_VVLoose_2 > 0.5)",
        "tau_iso": "(id_tau_vsJet_VVVLoose_1 > 0.5) & (id_tau_vsJet_VVVLoose_2 > 0.5)",
        "pt_selection": "(pt_1 > 40) & (pt_2 > 40)",
        "tau_eta": "(abs(eta_1) < 2.1) & (abs(eta_2) < 2.1)",
    },
}
# The trigger cut per year and channel (ShapeSmith triggers.TRIGGER[era][channel].cut): the flags with the offline
# thresholds; tt: the embedding without trigger, in 2016 the data with the OR of both di-tau paths, the MC the Iso one.
TRIGGER_CUTS = {
    "2016": {
        "et": "(pt_2 > 30) & (pt_1 > 27) & (trg_single_ele25 > 0.5)",
        "mt": "(pt_2 > 30) & (pt_1 > 24) & ((trg_single_mu22 > 0.5) | (trg_single_mu22_tk > 0.5)"
        " | (trg_single_mu22_eta2p1 > 0.5) | (trg_single_mu22_eta2p1_tk > 0.5))",
        "tt": "((is_embedding > 0.5) | ((is_data > 0.5) & ((trg_double_tau35_mediumiso > 0.5)"
        " | (trg_double_tau35_mediumcombinediso > 0.5))) | ((is_mc > 0.5) & (trg_double_tau35_mediumiso > 0.5)))",
    },
    "2017": {
        "et": "(pt_2 > 30) & (((pt_1 >= 34) & (pt_1 < 37) & (trg_single_ele32 > 0.5))"
        " | ((pt_1 >= 37) & (trg_single_ele35 > 0.5)))",
        "mt": "(pt_2 > 30) & (pt_1 > 29) & (trg_single_mu27 > 0.5)",
        "tt": "((is_embedding > 0.5) | ((trg_double_tau35_tightiso > 0.5) | (trg_double_tau40_mediumiso > 0.5)"
        " | (trg_double_tau40_tightiso > 0.5)))",
    },
    "2018": {
        "et": "(pt_2 > 30) & (pt_1 > 33) & (trg_single_ele32 > 0.5)",
        "mt": "(pt_2 > 30) & (pt_1 > 25) & (trg_single_mu24 > 0.5)",
        "tt": "((is_embedding > 0.5) | ((trg_double_tau35_mediumiso > 0.5) | (trg_double_tau35_tightiso > 0.5)"
        " | (trg_double_tau40_mediumiso > 0.5) | (trg_double_tau40_tightiso > 0.5)))",
    },
}


def skim_cuts(channel: str, era: str) -> Dict[str, str]:
    """The cuts of the gate, named and ordered as ShapeSmith's skim_cuts(channel, era, control_regions=True)."""
    cuts = dict(CHANNEL_CUTS[channel])
    cuts["trg_selection"] = TRIGGER_CUTS[YEARS[era]][channel]
    if era in HEM_ERAS:
        cuts["hem_veto"] = "(hem_veto < 0.5)"
    return cuts


def tau_ff_cuts(channel: str, era: str) -> Dict[str, str]:
    """The selection of the tau_ff skims, ShapeSmith's skim_cuts(channel, era, control_regions=False), for the checks
    that the gate contains it: a b pair with a b tag without the alternative of >= 2 jets, and in et and mt the lepton
    isolation below 0.15 and the mT cut; every other cut is the gate's."""
    cuts = skim_cuts(channel, era)
    cuts["b_tagging"] = "(n_bjets >= 1) & (bpair_pt_2 > 0)"
    if channel != "tt":
        cuts.update({"lepton_iso": "(iso_1 < 0.15)", "mt_cut": "(mt_1 < 70)"})
    return cuts


# pandas.eval tokens the translation knows; anything else (~, not, arithmetic, ...) fails the configuration
_TOKEN = re.compile(
    r"\s*(?:(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<number>\d+(?:\.\d*)?)(?![\w.])|(?P<op><=|>=|==|!=|[<>&|()]))"
)
_OPERATORS = {"&": "&&", "|": "||"}  # pandas.eval gives & and | the precedence of and and or
_UNSUPPORTED_NAMES = {"and", "or", "not", "True", "False", "inf", "nan"}  # pandas.eval keywords


def cpp_expression(cuts: Dict[str, str]) -> Tuple[str, List[str]]:
    """The AND of ``cuts`` as an RDataFrame expression whose columns are written $0, $1, ... (in the order of the
    returned column list), so that the friend can read them shifted; abs is std::abs."""
    columns: List[str] = []
    terms = []
    for name, cut in cuts.items():
        tokens, position = [], 0
        while position < len(cut.rstrip()):
            match = _TOKEN.match(cut, position)
            if match is None:
                raise ValueError(f"gate cut {name} '{cut}': cannot translate '{cut[position:]}' to C++")
            position = match.end()
            if match["name"] in _UNSUPPORTED_NAMES or (
                match["name"] and match["name"] != "abs" and cut[position:].lstrip().startswith("(")
            ):
                raise ValueError(f"gate cut {name} '{cut}': cannot translate '{match['name']}' to C++")
            if match["name"] == "abs":
                tokens.append("std::abs")
            elif match["name"]:
                if match["name"] not in columns:
                    columns.append(match["name"])
                tokens.append(f"${columns.index(match['name'])}")
            elif match["number"]:
                tokens.append(match["number"])
            else:
                tokens.append(_OPERATORS.get(match["op"], match["op"]))
        text = tokens[0]
        for before, token in zip(tokens, tokens[1:]):
            text += ("" if before in ("(", "std::abs") or token == ")" else " ") + token
        terms.append(f"({text})")
    return " && ".join(terms), columns
