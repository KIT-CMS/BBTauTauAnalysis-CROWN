from collections.abc import Mapping

from code_generation.configuration import Configuration
from code_generation.modifiers import EraModifier

from .constants import (
    ET_SCOPES,
    MT_SCOPES,
    TT_SCOPES,
    ELECTRON_SCOPES,
    MUON_SCOPES,
    ERAS_RUN2,
    ERAS_RUN3,
)
from .helpers import cpp_list


def _get_updated_dict(
    orig_dict: dict,
    update: dict,
):
    """
    Copy the dictionary `orig_dict`, update its entries with the `update`
    dictionary, and return the result. The function does not modify the
    content of `orig_dict`.

    :param orig_dict: The original dictionary which is copied and modified.

    :param update: The key-value pairs to be added or updated.

    :returns: A copy of the originalt dictionary with its contents updated.
    """
    modified_dict = orig_dict.copy()
    modified_dict.update(update)
    return modified_dict


#
# SINGLE-LEPTON TRIGGERS
#
# The trigger-object filter bits of electrons (1 = WPTight) and muons (1 = Iso,
# 10 = Mu50) are the same in the NanoAOD v9 and v15 schemes of Run 2; in 2016,
# muon bit 3 is IsoTkMu, in 2017 and 2018 it is 1mu (the doc strings of
# TrigObj_filterBits, tests/fixtures/nanoaod_v15_trigobj_filterbits.json).
#
# The single-lepton trigger recommendations can be found at the following POG
# TWiki pages:
#
# - https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
# - https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIIISummary
# - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016 (2017, 2018, 2022, 2023, 2024)

# The trigger-object matching cone of the single-lepton triggers. The KIT tag and
# probe that measured the KIT trigger SFs matches within 0.1 (TauAnalysis-CROWN
# tauembedding_tagandprobe.py, max_deltaR_triggermatch), as MUO recommends (v7 spec
# K8); otherwise 0.4. The tau legs keep 0.4.
KIT_SINGLE_LEPTON_MATCH_MAX_DELTA_R = 0.1
SINGLE_LEPTON_MATCH_MAX_DELTA_R = 0.4

## Isolated-electron triggers

# HLT_Ele27_WPTight_Gsf (2016), final filter hltEle27WPTightGsfTrackIsoFilter, bit 1
ELE_27 = {
    "flagname": "trg_single_ele27",
    "hlt_path": "HLT_Ele27_WPTight_Gsf",
    "min_pt": 29.,
    "max_abs_eta": 2.5,
    "filter_bit": 1,
    "particle_id": 11,
    "match_max_delta_r": SINGLE_LEPTON_MATCH_MAX_DELTA_R,
}
# HLT_Ele25_eta2p1_WPTight_Gsf (2016, the legacy SM trigger with the KIT SF Trg25),
# final filter hltEle25erWPTightGsfTrackIsoFilter, bit 1
ELE_25_ETA2P1 = _get_updated_dict(
    ELE_27,
    {
        "flagname": "trg_single_ele25",
        "hlt_path": "HLT_Ele25_eta2p1_WPTight_Gsf",
        "min_pt": 27.,
        "max_abs_eta": 2.1,
    },
)
# HLT_Ele30_WPTight_Gsf (2022-2025), final filter hltEle30WPTightGsfTrackIsoFilter, bit 1
ELE_30 = _get_updated_dict(
    ELE_27,
    {"flagname": "trg_single_ele30", "hlt_path": "HLT_Ele30_WPTight_Gsf", "min_pt": 32.},
)
# HLT_Ele32_WPTight_Gsf (2017, 2018), final filter hltEle32WPTightGsfTrackIsoFilter,
# bit 1; in 2017 it exists from run 302026 on (no emulation from Ele32_L1DoubleEG)
ELE_32 = _get_updated_dict(
    ELE_27,
    {"flagname": "trg_single_ele32", "hlt_path": "HLT_Ele32_WPTight_Gsf", "min_pt": 34.},
)
# HLT_Ele35_WPTight_Gsf (2017), final filter hltEle35noerWPTightGsfTrackIsoFilter, bit 1
ELE_35 = _get_updated_dict(
    ELE_27,
    {"flagname": "trg_single_ele35", "hlt_path": "HLT_Ele35_WPTight_Gsf", "min_pt": 37.},
)

## High-pt-electron triggers (NMSSM)

# HLT_Ele115_CaloIdVT_GsfTrkIdT, final filter hltEle115CaloIdVTGsfTrkIdTGsfDphiFilter
ELE_115 = {
    "flagname": "trg_single_ele115",
    "hlt_path": "HLT_Ele115_CaloIdVT_GsfTrkIdT",
    "min_pt": 120.,
    "max_abs_eta": 2.5,
    "filter_bit": 11,
    "particle_id": 11,
    "match_max_delta_r": SINGLE_LEPTON_MATCH_MAX_DELTA_R,
}
# HLT_Photon175 (2016), final filter hltEG175HEFilter
PHOTON_175 = _get_updated_dict(
    ELE_115,
    {"flagname": "trg_single_photon175", "hlt_path": "HLT_Photon175", "min_pt": 180., "filter_bit": 13},
)
# HLT_Photon200 (2017), final filter hltEG200HEFilter
PHOTON_200 = _get_updated_dict(
    PHOTON_175,
    {"flagname": "trg_single_photon200", "hlt_path": "HLT_Photon200", "min_pt": 205.},
)

## Isolated-muon triggers

# HLT_IsoMu24 (2018, 2022-2025), final filter
# hltL3crIsoL1sSingleMu22L1f0L2f10QL3f24QL3trkIsoFiltered0p07 (2018), bit 1
ISO_MU_24 = {
    "flagname": "trg_single_mu24",
    "hlt_path": "HLT_IsoMu24",
    "min_pt": 26.,
    "max_abs_eta": 2.4,
    "filter_bit": 1,
    "particle_id": 13,
    "match_max_delta_r": SINGLE_LEPTON_MATCH_MAX_DELTA_R,
}
# HLT_IsoMu27 (2017), final filter
# hltL3crIsoL1sMu22Or25L1f0L2f10QL3f27QL3trkIsoFiltered0p07, bit 1
ISO_MU_27 = _get_updated_dict(
    ISO_MU_24, {"flagname": "trg_single_mu27", "hlt_path": "HLT_IsoMu27", "min_pt": 29.}
)
# The 2016 IsoMu22 family (legacy SM, KIT SF Trg_pt_eta_bins of their OR), p_T > 24 GeV:
# HLT_IsoMu22, final filter hltL3crIsoL1sMu20L1f0L2f10QL3f22QL3trkIsoFiltered0p09, bit 1
ISO_MU_22 = _get_updated_dict(
    ISO_MU_24, {"flagname": "trg_single_mu22", "hlt_path": "HLT_IsoMu22", "min_pt": 24.}
)
# HLT_IsoTkMu22, final filter hltL3fL1sMu20L1f0Tkf22QL3trkIsoFiltered0p09, bit 3 (IsoTkMu)
ISO_TK_MU_22 = _get_updated_dict(
    ISO_MU_22, {"flagname": "trg_single_mu22_tk", "hlt_path": "HLT_IsoTkMu22", "filter_bit": 3}
)
# HLT_IsoMu22_eta2p1, final filter
# hltL3crIsoL1sSingleMu20erL1f0L2f10QL3f22QL3trkIsoFiltered0p09, bit 1
ISO_MU_22_ETA2P1 = _get_updated_dict(
    ISO_MU_22,
    {"flagname": "trg_single_mu22_eta2p1", "hlt_path": "HLT_IsoMu22_eta2p1", "max_abs_eta": 2.1},
)
# HLT_IsoTkMu22_eta2p1, final filter hltL3fL1sMu20erL1f0Tkf22QL3trkIsoFiltered0p09, bit 3
ISO_TK_MU_22_ETA2P1 = _get_updated_dict(
    ISO_TK_MU_22,
    {"flagname": "trg_single_mu22_eta2p1_tk", "hlt_path": "HLT_IsoTkMu22_eta2p1", "max_abs_eta": 2.1},
)
# HLT_IsoTkMu24 (2016), final filter hltL3fL1sMu22L1f0Tkf24QL3trkIsoFiltered0p09, bit 3
ISO_TK_MU_24 = _get_updated_dict(
    ISO_MU_24, {"flagname": "trg_single_mu24_tk", "hlt_path": "HLT_IsoTkMu24", "filter_bit": 3}
)

## High-pt-muon triggers (NMSSM)

# HLT_Mu50, final filter hltL3fL1sMu22Or25L1f0L2f10QL3Filtered50Q, bit 10
MU_50 = {
    "flagname": "trg_single_mu50",
    "hlt_path": "HLT_Mu50",
    "min_pt": 55.,
    "max_abs_eta": 2.4,
    "filter_bit": 10,
    "particle_id": 13,
    "match_max_delta_r": SINGLE_LEPTON_MATCH_MAX_DELTA_R,
}
# HLT_TkMu50 (2016), final filter hltL3fL1sMu25f0TkFiltered50Q
TK_MU_50 = _get_updated_dict(MU_50, {"flagname": "trg_single_mu50_tk", "hlt_path": "HLT_TkMu50"})
# HLT_CascadeMu100 (2022-2025), final filter hltL3fL1sMu22Or25L1f0L2f10QL3Filtered100Q, bit 11
CASCADE_MU_100 = _get_updated_dict(
    MU_50,
    {"flagname": "trg_single_mu100_cascade", "hlt_path": "HLT_CascadeMu100", "min_pt": 105., "filter_bit": 11},
)
# HLT_HighPtTkMu100 (2022-2025), final filter hltL3fL1sMu25f0TkFiltered100Q, bit 11
HIGH_PT_TK_MU_100 = _get_updated_dict(
    CASCADE_MU_100, {"flagname": "trg_single_mu100_tk", "hlt_path": "HLT_HighPtTkMu100"}
)
# HLT_OldMu100 (2017, 2018), final filter hltL3fL1sMu22Or25L1f0L2f10QL3Filtered100Q, bit 11
OLD_MU_100 = _get_updated_dict(
    CASCADE_MU_100, {"flagname": "trg_single_mu100_old", "hlt_path": "HLT_OldMu100"}
)
# HLT_TkMu100 (2017, 2018), final filter hltL3fL1sMu25f0TkFiltered100Q, bit 11
TK_MU_100 = _get_updated_dict(
    CASCADE_MU_100, {"flagname": "trg_single_mu100_tk", "hlt_path": "HLT_TkMu100"}
)

# era -> (the analysis triggers the KIT SFs describe, further triggers). The
# analysis triggers (v7 spec E2-E6): muons 2016 the IsoMu22 family, 2017 IsoMu27
# (IsoMu24 is prescaled), 2018 and Run 3 IsoMu24; electrons 2016 Ele25_eta2p1,
# 2017 Ele32 (34-37 GeV) and Ele35 (from 37 GeV), 2018 Ele32, Run 3 Ele30.
SINGLE_ELECTRON_TRIGGERS = {
    **{era: ([ELE_30], [ELE_115]) for era in ERAS_RUN3},
    "2018": ([ELE_32], [ELE_115]),
    "2017": ([ELE_32, ELE_35], [ELE_115, PHOTON_200]),
    **{era: ([ELE_25_ETA2P1], [ELE_27, ELE_115, PHOTON_175]) for era in ("2016preVFP", "2016postVFP")},
}
SINGLE_MUON_TRIGGERS = {
    **{era: ([ISO_MU_24], [MU_50, CASCADE_MU_100, HIGH_PT_TK_MU_100]) for era in ERAS_RUN3},
    "2018": ([ISO_MU_24], [MU_50, OLD_MU_100, TK_MU_100]),
    "2017": ([ISO_MU_27], [ISO_MU_24, MU_50, OLD_MU_100, TK_MU_100]),
    **{
        era: (
            [ISO_MU_22, ISO_TK_MU_22, ISO_MU_22_ETA2P1, ISO_TK_MU_22_ETA2P1],
            [ISO_MU_24, ISO_TK_MU_24, MU_50, TK_MU_50],
        )
        for era in ("2016preVFP", "2016postVFP")
    },
}

# The KIT (Tau Embedding group) trigger SFs of the analysis triggers per Run-2 era:
# SF column -> correction of data/embedding/{muon,electron}_<era>UL.json.gz, for
# embedding (type "emb", both) and MC (type "mc", electrons only; the MC muons take
# POG_SINGLE_MUON_TRIGGER_SFS). The 2016 muon SF is that of the OR of the IsoMu22
# family (v7 spec E5, E6).
KIT_SINGLE_MUON_TRIGGER_SFS = {
    "2016preVFP": {"trg_wgt_single_mu22": "Trg_pt_eta_bins"},
    "2016postVFP": {"trg_wgt_single_mu22": "Trg_pt_eta_bins"},
    "2017": {"trg_wgt_single_mu27": "Trg_IsoMu27_pt_eta_bins"},
    "2018": {"trg_wgt_single_mu24": "Trg_IsoMu24_pt_eta_bins"},
}
KIT_SINGLE_ELECTRON_TRIGGER_SFS = {
    "2016preVFP": {"trg_wgt_single_ele25": "Trg25_Iso_pt_eta_bins"},
    "2016postVFP": {"trg_wgt_single_ele25": "Trg25_Iso_pt_eta_bins"},
    "2017": {
        "trg_wgt_single_ele32": "Trg32_Iso_pt_eta_bins",
        "trg_wgt_single_ele35": "Trg35_Iso_pt_eta_bins",
    },
    "2018": {"trg_wgt_single_ele32": "Trg32_Iso_pt_eta_bins"},
}

# The POG (MUO) single-muon trigger SFs of MC per Run-2 era (decision of
# 2026-10-18, in place of the KIT MC SF of v7 spec E5; embedding keeps the KIT
# SF): SF column (the KIT column names, which ShapeSmith reads) -> correction of
# the era's muon_Z.json.gz (muon_sf_file, MUO Run2-<era>-UL-NanoAODv9/2024-07-02),
# evaluated by scalefactors.PogSingleMuonTriggerSF. The POG denominator is the
# tight ID with tight PF isolation, the SM muons are medium ID with iso < 0.15:
# accepted. The 2016 SF is that of IsoMu24 || IsoTkMu24, applied to the IsoMu22
# family the 2016 flags take (the POG has no IsoMu22 SF).
POG_SINGLE_MUON_TRIGGER_SFS = {
    "2016preVFP": {"trg_wgt_single_mu22": "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"},
    "2016postVFP": {"trg_wgt_single_mu22": "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"},
    "2017": {"trg_wgt_single_mu27": "NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight"},
    "2018": {"trg_wgt_single_mu24": "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"},
}
# The (min pT, max |eta|) of the binning of these corrections, which ends there with
# flow "error"; the muons are evaluated at the pT and |eta| clamped into it. Below
# the pT range: the 2016 flags from 24 GeV (payload from 26 GeV) and the 2018 IsoMu24
# flag of the tau-ID measurement from 25 GeV; they take the SF of the lowest pT bin.
POG_MUON_TRIGGER_SF_RANGE = {
    "2016preVFP": (26.0, 2.4),
    "2016postVFP": (26.0, 2.4),
    "2017": (29.0, 2.4),
    "2018": (26.0, 2.4),
}


def pog_muon_trigger_sf_entries(era: str, sfs: Mapping[str, str] | None = None) -> list[dict]:
    """
    The vector configuration of scalefactors.PogSingleMuonTriggerSF in `era`: one
    entry per SF column of `sfs` (default POG_SINGLE_MUON_TRIGGER_SFS of the era,
    none in Run 3), nominal extrapolation, with the clamping range of the era.
    """
    if sfs is None:
        sfs = POG_SINGLE_MUON_TRIGGER_SFS.get(era, {})
    if not sfs:
        return []
    min_pt, max_abs_eta = POG_MUON_TRIGGER_SF_RANGE[era]
    return [
        {
            "flagname": column,
            "mc_trigger_sf": correction,
            "mc_muon_trg_extrapolation": 1.0,
            "mc_trigger_sf_min_pt": min_pt,
            "mc_trigger_sf_max_abs_eta": max_abs_eta,
        }
        for column, correction in sfs.items()
    ]


def single_lepton_triggers(table: dict, era: str, kit: bool) -> list[dict]:
    """
    The single-lepton trigger flags of `era` from `table` (SINGLE_ELECTRON_TRIGGERS
    or SINGLE_MUON_TRIGGERS). With `kit`, only the analysis triggers, matched
    within KIT_SINGLE_LEPTON_MATCH_MAX_DELTA_R; otherwise all, within 0.4.
    """
    analysis, further = table[era]
    if kit:
        return [
            _get_updated_dict(leg, {"match_max_delta_r": KIT_SINGLE_LEPTON_MATCH_MAX_DELTA_R})
            for leg in analysis
        ]
    return list(analysis) + list(further)


def kit_trigger_sf_entries(table: dict, era: str, sf_key: str, extrapolation_key: str) -> list[dict]:
    """The vector configuration of the KIT trigger SFs of `era`, nominal extrapolation."""
    return [
        {"flagname": column, sf_key: correction, extrapolation_key: 1.0}
        for column, correction in table.get(era, {}).items()
    ]


def _add_electron_triggers(configuration: Configuration, kit: bool):
    """
    Add the single-electron trigger flags to the scopes with at least one
    electron (`et`, `em`, `ee`), see SINGLE_ELECTRON_TRIGGERS.
    """
    configuration.add_config_parameters(
        ELECTRON_SCOPES,
        {
            "ele_trigger": EraModifier(
                {
                    era: single_lepton_triggers(SINGLE_ELECTRON_TRIGGERS, era, kit)
                    for era in SINGLE_ELECTRON_TRIGGERS
                }
            ),
        },
    )


def _add_muon_triggers(configuration: Configuration, kit: bool):
    """
    Add the single-muon trigger flags to the scopes with at least one muon
    (`mt`, `em`, `mm`), see SINGLE_MUON_TRIGGERS.
    """
    configuration.add_config_parameters(
        MUON_SCOPES,
        {
            "mu_trigger": EraModifier(
                {
                    era: single_lepton_triggers(SINGLE_MUON_TRIGGERS, era, kit)
                    for era in SINGLE_MUON_TRIGGERS
                }
            ),
        },
    )


def _add_kit_trigger_sfs(configuration: Configuration):
    """
    The single-lepton trigger SFs of MC in the Run-2 eras (empty in Run 3): the
    KIT electron SFs, read by scalefactors.ETGenerateSingleElectronTriggerSF_MC
    (every Run-2 configuration; the EGM Electron-HLT-SF exists in the Run-3
    payloads only), with type "mc", which the embedding switches to "emb"; and
    the POG muon SFs, read by scalefactors.PogSingleMuonTriggerSF
    (kit_single_lepton_triggers), which the embedding replaces by its KIT SFs
    (embedding_run2_v15).
    """
    configuration.add_config_parameters(
        ELECTRON_SCOPES,
        {
            "electron_trigger_sf_type": "mc",
            "singlelectron_trigger_sf_mc": EraModifier(
                {
                    era: kit_trigger_sf_entries(
                        KIT_SINGLE_ELECTRON_TRIGGER_SFS,
                        era,
                        "mc_trigger_sf",
                        "mc_electron_trg_extrapolation",
                    )
                    for era in ERAS_RUN2 + ERAS_RUN3
                }
            ),
        },
    )
    configuration.add_config_parameters(
        MUON_SCOPES,
        {
            "singlemuon_trigger_sf_mc": EraModifier(
                {era: pog_muon_trigger_sf_entries(era) for era in ERAS_RUN2 + ERAS_RUN3}
            ),
        },
    )


#
# DI-TAU TRIGGER LEGS IN EMBEDDING AND THE TAU-LEG MEASUREMENT
#
# Tau trigger-object bits of v15 (TrigObj_filterBits): 2016 1 = Medium(Comb)Iso,
# 5 = OverlapFilter IsoMu, 7 = L1-HLT matched, 8 = Dz, embedding adds 12 = di-tau
# (hltDoubleL2IsoTau26eta2p2); 2017/2018 1 = MediumChargedIso, 2 = TightChargedIso,
# 4 = TightID OOSC photons, 5 = HPS, 6 = charged iso di-tau, 9 = mu-tau, 17 =
# regional paths, embedding adds 23 = di-tau.

# The filter bits the di-tau legs of the tt embedding are matched to
# (TauEmbeddingSamplesUL): 2016 the final filter, 2017/2018 the earlier L2 filter.
EMBEDDING_DITAU_FILTER_BITS = {
    "2016preVFP": cpp_list([1, 8]),
    "2016postVFP": cpp_list([1, 8]),
    "2017": 23,
    "2018": 23,
}

# Columns of the tau-leg efficiency measurement of the di-tau trigger (v7 spec E33,
# docs v7_tt_emb_trigger 12.2, 12.4) in the mt scope of the tau-ID measurement: the
# tau h of the mu tau_h pair matched to the tau leg of the mu-tau monitoring paths
# (Delta R 0.4 as the di-tau flags), the quantities of the matched trigger object,
# and the di-tau filters of the embedding as diagnostics. The tau acceptance of tt is
# cut downstream. Filter bits are tuples of bit numbers, all required.
TAU_LEG = {"min_pt": 20.0, "max_abs_eta": 2.5, "particle_id": 15, "match_max_delta_r": 0.4}
_MONITOR_2017 = [
    # HLT_IsoMu24_eta2p1_TightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg_CrossL1, the
    # monitoring leg of DoubleTightChargedIsoPFTau35_Trk1_TightID
    {
        "flagname": "trg_mon_mu24tau35_tightiso_tightid_2",
        "hlt_path": "HLT_IsoMu24_eta2p1_TightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg_CrossL1",
        "filter_bit": (2, 4, 9, 17),
    },
    # HLT_IsoMu24_eta2p1_MediumChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg_CrossL1 (of
    # DoubleMediumChargedIsoPFTau40_Trk1_TightID above 40 GeV)
    {
        "flagname": "trg_mon_mu24tau35_mediumiso_tightid_2",
        "hlt_path": "HLT_IsoMu24_eta2p1_MediumChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg_CrossL1",
        "filter_bit": (1, 4, 9, 17),
    },
    # HLT_IsoMu24_eta2p1_TightChargedIsoPFTau35_Trk1_eta2p1_Reg_CrossL1 (of
    # DoubleTightChargedIsoPFTau40_Trk1 above 40 GeV)
    {
        "flagname": "trg_mon_mu24tau35_tightiso_2",
        "hlt_path": "HLT_IsoMu24_eta2p1_TightChargedIsoPFTau35_Trk1_eta2p1_Reg_CrossL1",
        "filter_bit": (2, 9, 17),
    },
]
TAU_LEG_MONITOR_TRIGGERS = {
    **{
        era: [
            # HLT_IsoMu19_eta2p1_MediumIsoPFTau32_Trk1_eta2p1_Reg (data 2016B-G, MC)
            {
                "flagname": "trg_mon_mu19tau32_mediso_2",
                "hlt_path": "HLT_IsoMu19_eta2p1_MediumIsoPFTau32_Trk1_eta2p1_Reg",
                "filter_bit": (1, 5, 7),
            },
            # HLT_IsoMu19_eta2p1_MediumCombinedIsoPFTau32_Trk1_eta2p1_Reg (data 2016H, MC)
            {
                "flagname": "trg_mon_mu19tau32_medcombiso_2",
                "hlt_path": "HLT_IsoMu19_eta2p1_MediumCombinedIsoPFTau32_Trk1_eta2p1_Reg",
                "filter_bit": (1, 5, 7),
            },
        ]
        for era in ("2016preVFP", "2016postVFP")
    },
    "2017": _MONITOR_2017,
    "2018": [
        # the 2017 paths exist in the 2018 data before run 317509
        *_MONITOR_2017,
        # HLT_IsoMu24_eta2p1_MediumChargedIsoPFTauHPS35_Trk1_eta2p1_Reg_CrossL1 (data
        # from run 317509, MC, embedding)
        {
            "flagname": "trg_mon_mu24tau35_mediumiso_hps_2",
            "hlt_path": "HLT_IsoMu24_eta2p1_MediumChargedIsoPFTauHPS35_Trk1_eta2p1_Reg_CrossL1",
            "filter_bit": (1, 5, 9, 17),
        },
    ],
}
# The di-tau filters of the embedding at the tau h, without HLT path: the L2 filter
# of the embedding bits and the final filter of the di-tau paths
TAU_LEG_EMBEDDING_FILTERS = {
    **{
        era: [
            {"flagname": "trg_emb_ditau_l2_2", "filter_bit": (12,)},
            {"flagname": "trg_emb_ditau_final_2", "filter_bit": (1, 8)},
        ]
        for era in ("2016preVFP", "2016postVFP")
    },
    **{
        era: [
            {"flagname": "trg_emb_ditau_l2_2", "filter_bit": (23,)},
            {"flagname": "trg_emb_ditau_final_2", "filter_bit": (6,)},
        ]
        for era in ("2017", "2018")
    },
}
# The bits of the tau trigger object whose pT, L1 pT and L1 isolation are written:
# the monitoring tau leg (2016 Medium(Comb)Iso, overlap with IsoMu, L1-HLT matched;
# 2017/2018 mu-tau and regional)
TAU_LEG_TRIGGER_OBJECT_BITS = {
    "2016preVFP": (1, 5, 7),
    "2016postVFP": (1, 5, 7),
    "2017": (9, 17),
    "2018": (9, 17),
}


def tau_leg_flags(entries: list[dict]) -> list[dict]:
    """The flag configurations of TAU_LEG_MONITOR_TRIGGERS / TAU_LEG_EMBEDDING_FILTERS
    entries: the common tau-leg parameters and the bits as a C++ list."""
    return [
        {**TAU_LEG, **entry, "filter_bit": cpp_list(list(entry["filter_bit"]))}
        for entry in entries
    ]


def _add_tautau_triggers(
    configuration: Configuration,
):
    """
    Add configuration of tau-tau trigger producers. The configuration adds
    tau-tau and tau-tau-jet triggers to the `tt` scope.

    The use of the following isolated electron triggers is recommended by the
    TAU POG:

    The tau trigger recommendations can be found at the following TAU POG TWiki
    page:

    - https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger
    """

    ## DeepTau trigger

    # HLT_DoubleMediumDeepTauPFTauHPS35_L2NN_eta2p1
    double_medium_deeptau_35_eta_2p1_parameters = {
        "flagname": "trg_double_tau35_mediumdeeptau",
        "hlt_path": "HLT_DoubleMediumDeepTauPFTauHPS35_L2NN_eta2p1",
        "p1_min_pt": 40.,
        "p1_max_abs_eta": 2.1,
        "p1_filter_bit": 7,
        "p1_particle_id": 15,
        "p2_min_pt": 40.,
        "p2_max_abs_eta": 2.1,
        "p2_filter_bit": 7,
        "p2_particle_id": 15,
        "match_max_delta_r": 0.4,
    }

    # HLT_DoubleMediumDeepTauPFTauHPS35_L2NN_eta2p1
    double_medium_deeptau_35_eta_2p1_2024_parameters = _get_updated_dict(
        double_medium_deeptau_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau35_mediumdeeptau",
            "hlt_path": "HLT_DoubleMediumDeepTauPFTauHPS35_L2NN_eta2p1",
            "p1_filter_bit": 11,
            "p2_filter_bit": 11,
        },
    )

    ## ParticleNet trigger

    # HLT_DoublePNetTauhPFJet30_Medium_L2NN_eta2p3
    double_medium_pnet_30_eta_2p3_parameters = _get_updated_dict(
        double_medium_deeptau_35_eta_2p1_2024_parameters,
        {
            "flagname": "trg_double_tau30_mediumpnet",
            "hlt_path": "HLT_DoublePNetTauhPFJet30_Medium_L2NN_eta2p3",
            "p1_min_pt": 35.,
            "p2_min_pt": 35.,
            "p1_max_abs_eta": 2.3,
            "p2_max_abs_eta": 2.3,
        },
    )

    # HLT_DoublePNetTauhPFJet30_Tight_L2NN_eta2p3
    double_tight_pnet_30_eta_2p3_parameters = _get_updated_dict(
        double_medium_pnet_30_eta_2p3_parameters,
        {
            "flagname": "trg_double_tau30_tightpnet",
            "hlt_path": "HLT_DoublePNetTauhPFJet30_Tight_L2NN_eta2p3",
        },
    )

    ## MVA-ID trigger

    # HLT_DoubleMediumChargedIsoPFTauHPS35_Trk1_eta2p1_Reg
    double_medium_chargediso_hps_35_eta_2p1_parameters = _get_updated_dict(
        double_medium_deeptau_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau35_mediumiso",
            "hlt_path": "HLT_DoubleMediumChargedIsoPFTauHPS35_Trk1_eta2p1_Reg",
            "p1_filter_bit": 6,
            "p2_filter_bit": 6,
        },
    )

    # HLT_DoubleTightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg
    double_tight_chargediso_35_eta_2p1_parameters = _get_updated_dict(
        double_medium_chargediso_hps_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau35_tightiso",
            "hlt_path": "HLT_DoubleTightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg",
        },
    )

    # HLT_DoubleMediumChargedIsoPFTau40_Trk1_TightID_eta2p1_Reg
    double_medium_chargediso_40_eta_2p1_parameters = _get_updated_dict(
        double_medium_chargediso_hps_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau40_mediumiso",
            "hlt_path": "HLT_DoubleMediumChargedIsoPFTau40_Trk1_TightID_eta2p1_Reg",
        },
    )

    # HLT_DoubleTightChargedIsoPFTau40_Trk1_eta2p1_Reg
    double_tight_chargediso_40_eta_2p1_parameters = _get_updated_dict(
        double_medium_chargediso_hps_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau40_tightiso",
            "hlt_path": "HLT_DoubleTightChargedIsoPFTau40_Trk1_eta2p1_Reg",
        },
    )

    # HLT_DoubleMediumIsoPFTau35_Trk1_eta2p1_Reg (2016): the 2016 tau bit scheme has
    # 1 = Medium(Comb)Iso and 8 = Dz, the final filter
    # hltDoublePFTau35TrackPt1MediumIsolationDz02Reg carries both
    double_medium_iso_35_eta_2p1_parameters = _get_updated_dict(
        double_medium_chargediso_hps_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau35_mediumiso",
            "hlt_path": "HLT_DoubleMediumIsoPFTau35_Trk1_eta2p1_Reg",
            "p1_filter_bit": cpp_list([1, 8]),
            "p2_filter_bit": cpp_list([1, 8]),
        },
    )

    # HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg (2016), final filter
    # hltDoublePFTau35TrackPt1MediumCombinedIsolationDz02Reg, bits 1 and 8
    double_medium_combinediso_35_eta_2p1_parameters = _get_updated_dict(
        double_medium_iso_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau35_mediumcombinediso",
            "hlt_path": "HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg",
        },
    )

    ## double-tau + jet triggers

    # HLT_DoubleMediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet60
    double_medium_deeptau_30_eta2p1_jet_60_parameters = {
        "flagname": "trg_double_tau30_jet60_mediumdeeptau",
        "hlt_path": "HLT_DoubleMediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet60",
        "p1_min_pt": 35.,
        "p1_max_abs_eta": 2.1,
        "p1_filter_bit": 14,
        "p1_particle_id": 15,
        "p2_min_pt": 35.,
        "p2_max_abs_eta": 2.1,
        "p2_filter_bit": 14,
        "p2_particle_id": 15,
        "match_max_delta_r": 0.4,
    }

    # HLT_DoubleMediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet75
    double_medium_deeptau_30_eta2p1_jet_75_parameters = _get_updated_dict(
        double_medium_deeptau_30_eta2p1_jet_60_parameters,
        {
            "flagname": "trg_double_tau30_jet75_mediumdeeptau",
            "hlt_path": "HLT_DoubleMediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet75",
        },
    )

    # HLT_DoublePNetTauhPFJet26_L2NN_eta2p3_PFJet60
    double_pnet_26_eta2p3_jet_60_parameters = _get_updated_dict(
        double_medium_deeptau_30_eta2p1_jet_60_parameters,
        {
            "flagname": "trg_double_tau26_jet60_pnet",
            "hlt_path": "HLT_DoublePNetTauhPFJet26_L2NN_eta2p3_PFJet60",
            "p1_min_pt": 30.,
            "p1_max_abs_eta": 2.3,
            "p2_min_pt": 30.,
            "p2_max_abs_eta": 2.3,
        },
    )

    # HLT_DoublePNetTauhPFJet26_L2NN_eta2p3_PFJet75
    double_pnet_26_eta2p3_jet_75_parameters = _get_updated_dict(
        double_pnet_26_eta2p3_jet_60_parameters,
        {
            "flagname": "trg_double_tau26_jet75_pnet",
            "hlt_path": "HLT_DoublePNetTauhPFJet26_L2NN_eta2p3_PFJet75",
        },
    )

    # 2018 double tau-tau triggers, shared by the data/MC and the embedding flags
    tautau_trigger_2018 = [
        # trigger:          HLT_DoubleMediumChargedIsoPFTauHPS35_Trk1_eta2p1_Reg
        # final tau filter: hltHpsDoublePFTau35TrackPt1MediumChargedIsolationDz02Reg
        # tau filter bit:   6
        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2018
        # comment:          Filter bits do not work in NANOAOD v9; data run >= 317509 and MC
        double_medium_chargediso_hps_35_eta_2p1_parameters,

        # trigger:          HLT_DoubleTightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg
        # final tau filter: hltDoublePFTau35TrackPt1TightChargedIsolationAndTightOOSCPhotonsDz02Reg
        # tau filter bit:   6
        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2018
        # comment:          data run < 317509
        double_tight_chargediso_35_eta_2p1_parameters,

        # trigger:          HLT_DoubleMediumChargedIsoPFTau40_Trk1_TightID_eta2p1_Reg
        # final tau filter: hltDoublePFTau40TrackPt1MediumChargedIsolationAndTightOOSCPhotonsDz02Reg
        # tau filter bit:   6
        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2018
        # comment:          data run < 317509
        double_medium_chargediso_40_eta_2p1_parameters,

        # trigger:          HLT_DoubleTightChargedIsoPFTau40_Trk1_eta2p1_Reg
        # final tau filter: hltDoublePFTau40TrackPt1TightChargedIsolationDz02Reg
        # tau filter bit:   6
        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2018
        # comment:          data run < 317509
        double_tight_chargediso_40_eta_2p1_parameters,
    ]

    # Run-2 double tau-tau triggers per era (v7 spec E7), shared by the data/MC flags,
    # the embedding flags and the trigger SFs
    tautau_trigger_run2 = {
        "2018": tautau_trigger_2018,
        "2017": [
            # trigger:          HLT_DoubleTightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg
            # final tau filter: hltDoublePFTau35TrackPt1TightChargedIsolationAndTightOOSCPhotonsDz02Reg
            # tau filter bit:   6
            # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2017
            double_tight_chargediso_35_eta_2p1_parameters,

            # trigger:          HLT_DoubleMediumChargedIsoPFTau40_Trk1_TightID_eta2p1_Reg
            # final tau filter: hltDoublePFTau40TrackPt1MediumChargedIsolationAndTightOOSCPhotonsDz02Reg
            # tau filter bit:   6
            # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2017
            double_medium_chargediso_40_eta_2p1_parameters,

            # trigger:          HLT_DoubleTightChargedIsoPFTau40_Trk1_eta2p1_Reg
            # final tau filter: hltDoublePFTau40TrackPt1TightChargedIsolationDz02Reg
            # tau filter bit:   6
            # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2017
            double_tight_chargediso_40_eta_2p1_parameters,
        ],
        **{
            _era: [
                # trigger:          HLT_DoubleMediumIsoPFTau35_Trk1_eta2p1_Reg
                # final tau filter: hltDoublePFTau35TrackPt1MediumIsolationDz02Reg
                # tau filter bits:  1, 8
                # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2016
                # comment:          data Run2016B-F and MC (the POG SF is that of this path)
                double_medium_iso_35_eta_2p1_parameters,

                # trigger:          HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg
                # final tau filter: hltDoublePFTau35TrackPt1MediumCombinedIsolationDz02Reg
                # tau filter bits:  1, 8
                # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2016
                # comment:          data Run2016H; downstream, MC takes the Iso path only (D9)
                double_medium_combinediso_35_eta_2p1_parameters,
            ]
            for _era in ["2016preVFP", "2016postVFP"]
        },
    }

    # Add triggers to the configuration
    configuration.add_config_parameters(
        TT_SCOPES,
        {
            "tautaujet_trigger": EraModifier(
                {
                    "2025": [
                        # trigger:          HLT_DoublePNetTauhPFJet26_L2NN_eta2p3_PFJet60
                        # final tau filter: hltHpsOverlapFilterDoublePNetTauh26PFJet60
                        # tau filter bit:   14
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_pnet_26_eta2p3_jet_60_parameters,

                        # trigger:          HLT_DoublePNetTauhPFJet26_L2NN_eta2p3_PFJet75
                        # final tau filter: hltHpsOverlapFilterDoublePNetTauh26PFJet75
                        # tau filter bit:   14
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_pnet_26_eta2p3_jet_75_parameters,
                    ],
                    "2024": [
                        # trigger:          HLT_DoubleMediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet60
                        # final tau filter: hltHpsOverlapFilterDeepTauDoublePFTau30PFJet60
                        # tau filter bit:   14
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_medium_deeptau_30_eta2p1_jet_60_parameters,

                        # trigger:          HLT_DoubleMediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet75
                        # final tau filter: hltHpsOverlapFilterDeepTauDoublePFTau30PFJet75
                        # tau filter bit:   14
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_medium_deeptau_30_eta2p1_jet_75_parameters,

                        # trigger:          HLT_DoublePNetTauhPFJet26_L2NN_eta2p3_PFJet60
                        # final tau filter: hltHpsOverlapFilterDoublePNetTauh26PFJet60
                        # tau filter bit:   14
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_pnet_26_eta2p3_jet_60_parameters,

                        # trigger:          HLT_DoublePNetTauhPFJet26_L2NN_eta2p3_PFJet75
                        # final tau filter: hltHpsOverlapFilterDoublePNetTauh26PFJet75
                        # tau filter bit:   14
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_pnet_26_eta2p3_jet_75_parameters,
                    ],
                    **{
                        _era: [
                            # trigger:          HLT_DoubleMediumDeepTauPFTauHPS30_L2NN_eta2p1_PFJet75
                            # final tau filter: hltHpsOverlapFilterDeepTauDoublePFTau30PFJet75
                            # tau filter bit:   14
                            # documentation:    - https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2022
                            #                   - https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2023
                            double_medium_deeptau_30_eta2p1_jet_75_parameters,
                        ]
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    **{
                        _era: []
                        for _era in ERAS_RUN2
                    },
                },
            ),
            "tautau_trigger": EraModifier(
                {
                    "2025": [
                        # trigger:          HLT_DoublePNetTauhPFJet30_Medium_L2NN_eta2p3
                        # final tau filter: hltDoublePFJets30PNetTauhTagMediumWPL2DoubleTau
                        # tau filter bit:   11 (for NANOAODv15)
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2025
                        double_medium_pnet_30_eta_2p3_parameters,

                        # trigger:          HLT_DoublePNetTauhPFJet30_Tight_L2NN_eta2p3
                        # final tau filter: hltDoublePFJets30PNetTauhTagTightWPL2DoubleTau
                        # tau filter bit:   11 (for NANOAODv15)
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2025
                        double_tight_pnet_30_eta_2p3_parameters,
                    ],
                    "2024": [
                        # trigger:          HLT_DoubleMediumDeepTauPFTauHPS35_L2NN_eta2p1
                        # final tau filter: hltHpsDoublePFTau35MediumDitauWPDeepTauL1HLTMatched
                        # tau filter bit:   11 (for NANOAODv15)
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_medium_deeptau_35_eta_2p1_2024_parameters,

                        # trigger:          HLT_DoublePNetTauhPFJet30_Medium_L2NN_eta2p3
                        # final tau filter: hltDoublePFJets30PNetTauhTagMediumWPL2DoubleTau
                        # tau filter bit:   11 (for NANOAODv15)
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_medium_pnet_30_eta_2p3_parameters,

                        # trigger:          HLT_DoublePNetTauhPFJet30_Tight_L2NN_eta2p3
                        # final tau filter: hltDoublePFJets30PNetTauhTagTightWPL2DoubleTau
                        # tau filter bit:   11 (for NANOAODv15)
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_tight_pnet_30_eta_2p3_parameters,
                    ],
                    **{
                        _era: [
                            # trigger:          HLT_DoubleMediumDeepTauPFTauHPS35_L2NN_eta2p1
                            # final tau filter: hltHpsDoublePFTau35MediumDitauWPDeepTauDz02
                            # tau filter bit:   7
                            # documentation:    - https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2022
                            #                   - https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2023
                            double_medium_deeptau_35_eta_2p1_parameters,
                        ]
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    **tautau_trigger_run2,
                },
            ),
            # Tau embedding: the embedded taus fire none of these HLT paths, so the
            # embedding flags (triggers.TauTauTriggerFlagsEmbedding) keep the flag
            # names but match the filter bits of TauEmbeddingSamplesUL alone: 2016
            # the final filter (bits 1 and 8), 2017 and 2018 the embedding di-tau
            # leg bit 23 (hltDoubleL2IsoTau26eta2p2). With the eps_data weight of
            # the tt embedding (v7 spec E33) they are diagnostic columns.
            "tautau_trigger_embedding": EraModifier(
                {
                    **{
                        _era: [
                            _get_updated_dict(
                                parameters,
                                {
                                    "p1_filter_bit": EMBEDDING_DITAU_FILTER_BITS[_era],
                                    "p2_filter_bit": EMBEDDING_DITAU_FILTER_BITS[_era],
                                },
                            )
                            for parameters in tautau_trigger_run2[_era]
                        ]
                        for _era in ERAS_RUN2
                    },
                    **{_era: [] for _era in ERAS_RUN3},
                },
            ),
        },
    )

    # double tau-tau trigger scale factors: the POG di-tau SF (WP Medium) of each
    # flag, per leg; the Run-2 lists follow from the flag lists
    common_double_tautau_trigger_args = {
        "tt_trigger_leg1_sf_name": "ditau",
        "tt_trigger_leg1_variation": "nom",
        "tt_trigger_leg2_sf_name": "ditau",
        "tt_trigger_leg2_variation": "nom",
    }
    run3_flags = {
        **{
            _era: "trg_double_tau35_mediumdeeptau"
            for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
        },
        **{_era: "trg_double_tau30_mediumpnet" for _era in ["2024", "2025"]},
    }
    tautau_flags = {
        **{
            _era: [parameters["flagname"] for parameters in tautau_trigger_run2[_era]]
            for _era in ERAS_RUN2
        },
        **{_era: [flag] for _era, flag in run3_flags.items()},
    }
    configuration.add_config_parameters(
        TT_SCOPES,
        {
            f"double_tautau_trigger_leg{leg}_sf": EraModifier(
                {
                    _era: [
                        {
                            # Run 2 drops the underscore after "wgt" (trg_wgtdouble_...,
                            # the names ShapeSmith reads), Run 3 keeps it
                            f"tt_trigger_leg{leg}_flagname": flag.replace(
                                "trg_", "trg_wgt" if _era in ERAS_RUN2 else "trg_wgt_"
                            )
                            + f"_leg{leg}",
                            "tt_trigger_flag": flag,
                            **common_double_tautau_trigger_args,
                        }
                        for flag in flags
                    ]
                    for _era, flags in tautau_flags.items()
                }
            )
            for leg in (1, 2)
        },
    )


def add_diTauTriggerSetup(configuration: Configuration, kit_single_lepton_triggers: bool = False):
    """
    Add the trigger flag and trigger SF configuration of all scopes. With
    `kit_single_lepton_triggers` (profile field), the single-lepton triggers are
    the analysis triggers of the KIT trigger SFs, matched within Delta R 0.1.
    """

    # Add the single-electron triggers to the et, em, and ee scopes
    _add_electron_triggers(configuration, kit_single_lepton_triggers)

    # Add the single-muon triggers to the mt, em, and mm scopes
    _add_muon_triggers(configuration, kit_single_lepton_triggers)

    # The KIT single-lepton trigger SFs of the Run-2 eras
    _add_kit_trigger_sfs(configuration)

    # Add double-tau and double-tau + jet triggers to the tt scope
    _add_tautau_triggers(configuration)

    # mu-tau trigger
    configuration.add_config_parameters(
        MT_SCOPES,
        {
            "double_mutau_trigger": EraModifier(
                {
                    **{
                        _era: [
                            # trigger:            HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1
                            # final filter muon:  hltL3crIsoBigORMu18erTauXXer2p1L1f0L2f10QL3f20QL3trkIsoFiltered
                            # filter bit muon:    1
                            # final filter tau:   hltHpsOverlapFilterIsoMu20LooseMuTauWPDeepTauPFTau27L1Seeded
                            # filter bit tau:     0, 4, 13  TODO implement matching to multiple filters
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                            {
                                "flagname": "trg_double_mu20tau27",
                                "hlt_path": "HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1",
                                "p1_min_pt": 22.,
                                "p1_max_abs_eta": 2.1,
                                "p1_particle_id": 13,
                                "p1_filter_bit": 1,
                                "p2_min_pt": 29.,
                                "p2_max_abs_eta": 2.1,
                                "p2_particle_id": 15,
                                "p2_filter_bit": 13,
                                "match_max_delta_r": 0.4,
                            }
                        ]
                        for _era in ["2024", "2025"]
                    },
                    **{
                        _era: [
                            # trigger:            HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1
                            # final filter muon:  hltL3crIsoBigORMu18erTauXXer2p1L1f0L2f10QL3f20QL3trkIsoFiltered
                            # filter bit muon:    1
                            # final filter tau:   hltHpsOverlapFilterIsoMu20LooseMuTauWPDeepTauPFTau27L1Seeded
                            # filter bit tau:     3, 9  TODO implement matching to multiple filters
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2022
                            #                     https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2023
                            {
                                "flagname": "trg_double_mu20tau27",
                                "hlt_path": "HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1",
                                "p1_min_pt": 22.,
                                "p1_max_abs_eta": 2.1,
                                "p1_particle_id": 13,
                                "p1_filter_bit": 1,
                                "p2_min_pt": 29.,
                                "p2_max_abs_eta": 2.1,
                                "p2_particle_id": 15,
                                "p2_filter_bit": 9,
                                "match_max_delta_r": 0.4,
                            }
                        ]
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    "2018": [
                        {
                            "flagname": "trg_cross_mu20tau27_hps",
                            "hlt_path": "HLT_IsoMu20_eta2p1_LooseChargedIsoPFTauHPS27_eta2p1_CrossL1",
                            "p1_min_pt": 21,
                            "p1_max_abs_eta": 2.1,
                            "p1_filter_bit": 3,
                            "p1_particle_id": 13,
                            "p2_min_pt": 32,
                            "p2_max_abs_eta": 2.1,
                            "p2_filter_bit": -1,  # TODO switch to "p2_filterbit": 4, if the bits are correct
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                        # the non HPS version exists for data only, but add it anyway to have the flag in the ntuple
                        {
                            "flagname": "trg_cross_mu20tau27",
                            "hlt_path": "HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1",
                            "p1_min_pt": 21,
                            "p1_max_abs_eta": 2.1,
                            "p1_filter_bit": 3,
                            "p1_particle_id": 13,
                            "p2_min_pt": 32,
                            "p2_max_abs_eta": 2.1,
                            "p2_filter_bit": -1,  # TODO switch to "p2_filterbit": 4, if the bits are correct
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                    ],
                    "2017": [
                        {
                            "flagname": "trg_cross_mu20tau27",
                            "hlt_path": "HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1",
                            "p1_min_pt": 21,
                            "p1_max_abs_eta": 2.1,
                            "p1_filter_bit": 3,
                            "p1_particle_id": 13,
                            "p2_min_pt": 32,
                            "p2_max_abs_eta": 2.1,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        }
                    ],
                    "2016postVFP": [
                        {
                            "flagname": "trg_cross_mu19tau20",
                            "hlt_path": "HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1",
                            "p1_min_pt": 20,
                            "p1_max_abs_eta": 2.1,
                            "p1_filter_bit": 3,
                            "p1_particle_id": 13,
                            "p2_min_pt": 22,
                            "p2_max_abs_eta": 2.1,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        }
                    ],
                    "2016preVFP": [
                        {
                            "flagname": "trg_cross_mu19tau20",
                            "hlt_path": "HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1",
                            "p1_min_pt": 20,
                            "p1_max_abs_eta": 2.1,
                            "p1_filter_bit": 3,
                            "p1_particle_id": 13,
                            "p2_min_pt": 22,
                            "p2_max_abs_eta": 2.1,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        }
                    ],
                }
            ),
        },
    )

    # e-tau trigger
    configuration.add_config_parameters(
        ET_SCOPES,
        {
            "double_eletau_trigger": EraModifier(
                {
                    **{
                        _era: [
                            # TODO check: do the trigger flags make sense for this trigger?
                            # trigger:            HLT_Ele30_WPTight_Gsf
                            # final filter ele:   hltOverlapFilterIsoEle24IsoTau30WPTightGsfCaloJet5
                            # filter bit ele:     2  TODO
                            # final filter tau:   hltHpsOverlapFilterIsoEle24WPTightGsfLooseETauWPDeepTauPFTau30
                            # filter bit tau:     3, 8  TODO
                            # documentation:      https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauTrigger#Trigger_Table_for_2022
                            {
                                "flagname": "trg_double_ele24tau30",
                                "hlt_path": "HLT_Ele24_eta2p1_WPTight_Gsf_LooseDeepTauPFTauHPS30_eta2p1_CrossL1",
                                "p1_min_pt": 26.,
                                "p1_max_abs_eta": 2.1,
                                "p1_filter_bit": -1,
                                "p1_particle_id": 11,
                                "p2_min_pt": 32.,
                                "p2_max_abs_eta": 2.1,
                                "p2_filter_bit": -1,
                                "p2_particle_id": 15,
                                "match_max_delta_r": 0.4,
                            }
                        ]
                        for _era in ERAS_RUN3
                    },
                    "2018": [
                        {
                            "flagname": "trg_cross_ele24tau30_hps",
                            "hlt_path": "HLT_Ele24_eta2p1_WPTight_Gsf_LooseChargedIsoPFTauHPS30_eta2p1_CrossL1",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 2.5,
                            "p1_filter_bit": 1,
                            "p1_particle_id": 11,
                            "p2_min_pt": 32,
                            "p2_max_abs_eta": 2.1,
                            "p2_filter_bit": -1,  # TODO switch to "p2_filterbit": 4, if the bits are correct
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                        # the non HPS version exists for data only, but add it anyway to have the flag in the ntuple
                        {
                            "flagname": "trg_cross_ele24tau30",
                            "hlt_path": "HLT_Ele24_eta2p1_WPTight_Gsf_LooseChargedIsoPFTau30_eta2p1_CrossL1",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 2.5,
                            "p1_filter_bit": 1,
                            "p1_particle_id": 11,
                            "p2_min_pt": 32,
                            "p2_max_abs_eta": 2.1,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                    ],
                    # The 2016 and 2017 e-tau cross triggers were configured with
                    # scrambled values (eta 35, filter bit 2.1, particle ID 2.1) that do
                    # not compile; no configuration uses them (the SM has no cross
                    # triggers, NMSSM writes no e-tau flag), so the lists are empty.
                    **{_era: [] for _era in ["2016preVFP", "2016postVFP", "2017"]},
                }
            ),
        },
    )

    # single electron trigger scale factors
    configuration.add_config_parameters(
        ELECTRON_SCOPES,
        {
            # TODO Update 2025 corrections as soon as dedicated corrections are available
            # The EGM Electron-HLT-SF exists in the Run-3 payloads only; every Run-2
            # configuration evaluates the KIT SF of its triggers instead
            # (scalefactors.ETGenerateSingleElectronTriggerSF_MC, _add_kit_trigger_sfs).
            "e_trigger_sf_file": EraModifier(
                {
                    **{_era: "DOES_NOT_EXIST" for _era in ERAS_RUN2},
                    "2022preEE": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-22CDSep23-Summer22-NanoAODv12/2025-12-15/electronHlt.json.gz",
                    "2022postEE": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-22EFGSep23-Summer22EE-NanoAODv12/2025-12-15/electronHlt.json.gz",
                    "2023preBPix": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-23CSep23-Summer23-NanoAODv12/2025-12-15/electronHlt.json.gz",
                    "2023postBPix": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-23DSep23-Summer23BPix-NanoAODv12/2025-12-15/electronHlt.json.gz",
                    "2024": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/2025-12-15/electronHlt.json.gz",
                    "2025": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/2025-12-15/electronHlt.json.gz",
                }
            ),
            "ele_trigger_sf": [
                {
                    "e_trigger_flagname": "trg_wgt_single_ele30",
                    "e_trigger_flag": "trg_single_ele30",
                    "e_trigger_era": EraModifier(
                        {
                            **{_era: "DOES_NOT_EXIST" for _era in ERAS_RUN2},
                            "2022preEE": "2022Re-recoBCD",
                            "2022postEE": "2022Re-recoE+PromptFG",
                            "2023preBPix": "2023PromptC",
                            "2023postBPix": "2023PromptD",
                            "2024": "2024Prompt",
                            "2025": "2024Prompt",  # TODO update as soon as dedicated corrections are available for 2025
                        }
                    ),
                    "e_trigger_sf_name": "Electron-HLT-SF",
                    "e_trigger_path_id_name": "HLT_SF_Ele30_MVAiso90ID",
                    "e_trigger_variation": "sf",
                },
            ],
        },
    )

    # double electron-tau trigger scale factors
    # TODO update scale factors for 2025 as soon as dedicated corrections are available
    configuration.add_config_parameters(
        ET_SCOPES,
        {
            "double_eletau_trigger_leg1_sf": [
                {
                    "et_trigger_flag": "trg_double_ele24tau30",
                    "et_trigger_leg1_flagname": "trg_wgt_double_ele24tau30_leg1",
                    "et_trigger_leg1_sf_file": EraModifier(
                        {
                            **{
                                _era: "DOES_NOT_EXIST"  # TODO does not exist for Run2 eras
                                for _era in ERAS_RUN2
                            },
                            **{
                                _era: f"data/hleprare/TriggerScaleFactors/{_era}/CrossEleTauHlt_EleLeg_v1.json"
                                for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix", "2024"]
                            },
                            "2025": f"data/hleprare/TriggerScaleFactors/2024/CrossEleTauHlt_EleLeg_v1.json",
                        }
                    ),
                    "et_trigger_leg1_era": EraModifier(
                        {
                            **{
                                _era: "DOES_NOT_EXIST"  # TODO does not exist for Run2 eras as correctionlib
                                for _era in ERAS_RUN2
                            },
                            "2022preEE": "2022Re-recoBCD",
                            "2022postEE": "2022Re-recoE+PromptFG",
                            "2023preBPix": "2023PromptC",
                            "2023postBPix": "2023PromptD",
                            "2024": "2024Prompt",
                            "2025": "2024Prompt",
                        }
                    ),
                    "et_trigger_leg1_sf_name": "Electron-HLT-SF",
                    "et_trigger_leg1_path_id_name": "HLT_SF_Ele24_TightID",
                    "et_trigger_leg1_variation": "sf",
                },
            ],
            "double_eletau_trigger_leg2_sf": [
                {
                    "et_trigger_leg2_flagname": "trg_wgt_double_ele24tau30_leg2",
                    "et_trigger_flag": "trg_double_ele24tau30",
                    "et_trigger_leg2_sf_name": "etau",
                    "et_trigger_leg2_variation": "nom",
                },
            ]
        },
    )

    # single muon trigger scale factors
    configuration.add_config_parameters(
        MUON_SCOPES,
        {
            "mu_trigger_sf": [
                {
                    "m_trigger_flagname": "trg_wgt_single_mu24",
                    "m_trigger_flag": "trg_single_mu24",
                    "m_trigger_sf_name": "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight",
                    "m_trigger_variation": "nominal",
                },
            ],
        },
    )

    # double muon-tau trigger scale factors
    # TODO update scale factors for 2025 as soon as dedicated corrections are available
    configuration.add_config_parameters(
        MT_SCOPES,
        {
            "double_mutau_trigger_leg1_sf": [
                {
                    "mt_trigger_leg1_sf_file": EraModifier(
                        {
                            # TODO clarify if we can actually just use the muon trigger SFs
                            "2016preVFP": "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run2-2016preVFP-UL-NanoAODv9/2024-07-02/muon_Z.json.gz",
                            "2016postVFP": "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run2-2016postVFP-UL-NanoAODv9/2024-07-02/muon_Z.json.gz",
                            "2017": "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run2-2017-UL-NanoAODv9/2024-07-02/muon_Z.json.gz",
                            "2018": "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run2-2018-UL-NanoAODv9/2024-07-02/muon_Z.json.gz",
                            **{
                                _era: f"data/hleprare/TriggerScaleFactors/{_era}/CrossMuTauHlt_MuLeg_v1.json"
                                for _era in ERAS_RUN3
                            },
                            # TODO update to 2025 correction as soon as it is available
                            "2025": "data/hleprare/TriggerScaleFactors/2024/CrossMuTauHlt_MuLeg_v1.json"
                        }
                    ),
                    "mt_trigger_leg1_flagname": "trg_wgt_double_mu20tau27_leg1",
                    "mt_trigger_flag": "trg_double_mu20tau27",
                    "mt_trigger_leg1_sf_name": "NUM_IsoMu20_DEN_CutBasedIdTight_and_PFIsoTight",
                    "mt_trigger_leg1_variation": "nominal",
                },
            ],
            "double_mutau_trigger_leg2_sf": [
                {
                    "mt_trigger_leg2_flagname": "trg_wgt_double_mu20tau27_leg2",
                    "mt_trigger_flag": "trg_double_mu20tau27",
                    "mt_trigger_leg2_sf_name": "mutau",
                    "mt_trigger_leg2_variation": "nom",
                },
            ],
        },
    )

    return configuration
