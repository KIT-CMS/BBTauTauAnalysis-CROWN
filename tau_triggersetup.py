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


def _add_electron_triggers(
    configuration: Configuration,
):
    """
    Add configuration of electron trigger producers. The configuration adds
    single-electron triggers to scopes with at least one electron (`et`, `em`,
    `ee`).

    The use of the following isolated electron triggers is recommended by the
    EGM POG:

    - 2016: `HLT_Ele27_WPTight_Gsf`
    - 2017: `HLT_Ele35_WPTight_Gsf || (HLT_Ele32_WPTight_Gsf && L1 seeds of HLT_Ele35_WPTight_Gsf)`
    - 2018: `HLT_Ele32_WPTight_Gsf`
    - 2022, 2023, 2024: `HLT_Ele30_WPTight_Gsf`

    The use of the following non-isolated electron triggers is recommended by
    the EGM POG:

    - 2016: `HLT_Ele115_CaloIdVT_GsfTrkIdT || HLT_Photon175`
    - 2017: `HLT_Ele115_CaloIdVT_GsfTrkIdT || HLT_Photon200`
    - 2018, 2022, 2023, 2024: `HLT_Ele115_CaloIdVT_GsfTrkIdT`

    The single-electron trigger recommendations can be found at the following
    EGM POG TWiki pages:

    - https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
    - https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIIISummary
    """

    ## Isolated-electron triggers

    # HLT_Ele27_WPTight_Gsf parameters
    ele_27_wptight_gsf_parameters = {
        "flagname": "trg_single_ele27",
        "hlt_path": "HLT_Ele27_WPTight_Gsf",
        "min_pt": 29.,
        "max_abs_eta": 2.5,
        "filter_bit": 1,
        "particle_id": 11,
        "match_max_delta_r": 0.4,
    }

    # HLT_Ele30_WPTight_Gsf parameters
    ele_30_wptight_gsf_parameters = _get_updated_dict(
        ele_27_wptight_gsf_parameters,
        {
            "flagname": "trg_single_ele30",
            "hlt_path": "HLT_Ele30_WPTight_Gsf",
            "min_pt": 32.,
        },
    )

    # HLT_Ele32_WPTight_Gsf parameters
    ele_32_wptight_gsf_parameters = _get_updated_dict(
        ele_27_wptight_gsf_parameters,
        {
            "flagname": "trg_single_ele32",
            "hlt_path": "HLT_Ele32_WPTight_Gsf",
            "min_pt": 34.,
        },
    )

    # HLT_Ele35_WPTight_Gsf parameters
    ele_35_wptight_gsf_parameters = _get_updated_dict(
        ele_27_wptight_gsf_parameters,
        {
            "flagname": "trg_single_ele35",
            "hlt_path": "HLT_Ele35_WPTight_Gsf",
            "min_pt": 37.,
        },
    )

    ## High-pt-electron triggers

    # HLT_Ele115_CaloIdVT_GsfTrkIdT
    ele_115_caloidvt_gsftrkidt_parameters = {
        "flagname": "trg_single_ele115",
        "hlt_path": "HLT_Ele115_CaloIdVT_GsfTrkIdT",
        "min_pt": 120.,
        "max_abs_eta": 2.5,
        "filter_bit": 11,
        "particle_id": 11,
        "match_max_delta_r": 0.4,
    }

    # HLT_Photon_175
    photon_175_parameters = _get_updated_dict(
        ele_115_caloidvt_gsftrkidt_parameters,
        {
            "flagname": "trg_single_photon175",
            "hlt_path": "HLT_Photon175",
            "min_pt": 180.,
            "filter_bit": 13,
        }
    )

    # HLT_Photon_200
    photon_200_parameters = _get_updated_dict(
        photon_175_parameters,
        {
            "flagname": "trg_single_photon200",
            "hlt_path": "HLT_Photon200",
            "min_pt": 205.,
        }
    )

    # Add triggers to the configuration
    configuration.add_config_parameters(
        ELECTRON_SCOPES,
        {
            "ele_trigger": EraModifier(
                {
                    **{
                        _era: [
                            # trigger:            HLT_Ele30_WPTight_Gsf
                            # final filter:       hltEle30WPTightGsfTrackIsoFilter
                            # filter bit:         1
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIIISummary
                            ele_30_wptight_gsf_parameters,

                            # trigger:            HLT_Ele115_CaloIdVT_GsfTrkIdT
                            # final filter:       hltEle115CaloIdVTGsfTrkIdTGsfDphiFilter
                            # filter bit:         11
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIIISummary
                            ele_115_caloidvt_gsftrkidt_parameters,
                        ]
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix", "2024"]
                    },
                    "2018": [
                            # trigger:            HLT_Ele32_WPTight_Gsf
                            # final filter:       hltEle32WPTightGsfTrackIsoFilter
                            # filter bit:         1
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            ele_32_wptight_gsf_parameters,

                            # trigger:            HLT_Ele115_CaloIdVT_GsfTrkIdT
                            # final filter:       hltEle115CaloIdVTGsfTrkIdTGsfDphiFilter
                            # filter bit:         11
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            ele_115_caloidvt_gsftrkidt_parameters,
                    ],
                    "2017": [
                            # trigger:            HLT_Ele32_WPTight_Gsf
                            # final filter:       hltEle32WPTightGsfTrackIsoFilter
                            # filter bit:         1
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            # comment:            Events must pass the L1 seed of HLT_Ele35_WPTight_Gsf
                            ele_32_wptight_gsf_parameters,

                            # trigger:            HLT_Ele35_WPTight_Gsf
                            # final filter:       hltEle35noerWPTightGsfTrackIsoFilter
                            # filter bit:         1
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            ele_35_wptight_gsf_parameters,

                            # trigger:            HLT_Ele115_CaloIdVT_GsfTrkIdT
                            # final filter:       hltEle115CaloIdVTGsfTrkIdTGsfDphiFilter
                            # filter bit:         11
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            ele_115_caloidvt_gsftrkidt_parameters,

                            # trigger:            HLT_Photon200
                            # final filter:       hltEG200HEFilter
                            # filter bit:         13
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            photon_200_parameters,
                    ],
                    **{
                        _era: [
                            # trigger:            HLT_Ele27_WPTight_Gsf
                            # final filter:       hltEle27WPTightGsfTrackIsoFilter
                            # filter bit:         1
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            ele_27_wptight_gsf_parameters,

                            # trigger:            HLT_Ele115_CaloIdVT_GsfTrkIdT
                            # final filter:       hltEle115CaloIdVTGsfTrkIdTGsfDphiFilter
                            # filter bit:         11
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            ele_115_caloidvt_gsftrkidt_parameters,

                            # trigger:            HLT_Photon200
                            # final filter:       hltEG175HEFilter
                            # filter bit:         13
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary
                            photon_175_parameters,
                        ]
                        for _era in ["2016preVFP", "2016postVFP"]
                    },
                },
            ),
        },
    )


def _add_muon_triggers(
    configuration: Configuration,
):
    """
    Add configuration of muon trigger producers. The configuration adds
    single-muon triggers to scopes with at least one muon (`mt`, `em`, `mm`).

    The use of the following isolated muon triggers is recommended by the MUO
    POG:

    - 2016: `HLT_IsoMu24 || HLT_IsoTkMu24`
    - 2017: `HLT_IsoMu27`
    - 2018, 2022, 2023, 2024: `HLT_IsoMu24`

    The use of the following non-isolated muon triggers is recommended by the
    MUO POG:

    - 2016: `HLT_Mu50 || HLT_TkMu50`
    - 2017, 2018: `HLT_Mu50 || HLT_OldMu100 || HLT_TkMu100`
    - 2022, 2023, 2024: `HLT_Mu50 || HLT_CascadeMu100 || HLT_HighPtTkMu100`

    The single-muon trigger recommendations can be found at the following MUO
    POG TWiki pages:

    - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
    - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2017
    - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2018
    - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2022
    - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2023
    - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2024
    """

    ## Isolated-muon triggers

    # HLT_IsoMu24 parameters
    iso_mu_24_parameters = {
        "flagname": "trg_single_mu24",
        "hlt_path": "HLT_IsoMu24",
        "min_pt": 26.,
        "max_abs_eta": 2.4,
        "filter_bit": 1,
        "particle_id": 13,
        "match_max_delta_r": 0.4,
    }

    # HLT_IsoMu27 parameters
    iso_mu_27_parameters = _get_updated_dict(
        iso_mu_24_parameters,
        {
            "flagname": "trg_single_mu27",
            "hlt_path": "HLT_IsoMu27",
            "min_pt": 29.,
        },
    )

    # HLT_IsoMu22 parameters
    iso_mu_22_parameters = _get_updated_dict(
        iso_mu_24_parameters,
        {
            "flagname": "trg_single_mu22",
            "hlt_path": "HLT_IsoMu22",
            "min_pt": 24.,
        },
    )

    # HLT_IsoTkMu22 parameters
    iso_tk_mu_22_parameters = _get_updated_dict(
        iso_mu_22_parameters,
        {
            "flagname": "trg_single_mu22_tk",
            "hlt_path": "HLT_IsoTkMu22",
            "filter_bit": 3,
        },
    )

    # HLT_IsoMu22_eta2p1 parameters
    iso_mu_22_eta2p1_parameters = _get_updated_dict(
        iso_mu_22_parameters,
        {
            "flagname": "trg_single_mu22_eta2p1",
            "hlt_path": "HLT_IsoMu22_eta2p1",
            "max_abs_eta": 2.1,
        },
    )

    # HLT_IsoTkMu22_eta2p1 parameters
    iso_tk_mu_22_eta2p1_parameters = _get_updated_dict(
        iso_tk_mu_22_parameters,
        {
            "flagname": "trg_single_mu22_eta2p1_tk",
            "hlt_path": "HLT_IsoTkMu22_eta2p1",
            "max_abs_eta": 2.1,
        },
    )

    # HLT_IsoTkMu24 parameters
    iso_tk_mu_24_2016_parameters = _get_updated_dict(
        iso_mu_24_parameters,
        {
            "flagname": "trg_single_mu24_tk",
            "hlt_path": "HLT_IsoTkMu24",
            "filter_bit": 3,
        },
    )

    ## High-pt-muon triggers

    # HLT_Mu50 parameters
    mu_50_parameters = {
        "flagname": "trg_single_mu50",
        "hlt_path": "HLT_Mu50",
        "min_pt": 55.,
        "max_abs_eta": 2.4,
        "filter_bit": 10,
        "particle_id": 13,
        "match_max_delta_r": 0.4,
    }

    # HLT_TkMu50 parameters
    tk_mu_50_parameters = _get_updated_dict(
        mu_50_parameters,
        {
            "flagname": "trg_single_mu50_tk",
            "hlt_path": "HLT_TkMu50",
        },
    )

    # HLT_CascadeMu100 parameters
    cascade_mu_100_parameters = _get_updated_dict(
        mu_50_parameters,
        {
            "flagname": "trg_single_mu100_cascade",
            "hlt_path": "HLT_CascadeMu100",
            "min_pt": 105.,
            "filter_bit": 11,
        },
    )

    # HLT_HighPtTkMu100 parameters
    high_pt_tk_mu_100_parameters = _get_updated_dict(
        cascade_mu_100_parameters,
        {
            "flagname": "trg_single_mu100_tk",
            "hlt_path": "HLT_HighPtTkMu100",
        },
    )

    # HLT_OldMu100 parameters
    old_mu_100_parameters = _get_updated_dict(
        cascade_mu_100_parameters,
        {
            "flagname": "trg_single_mu100_old",
            "hlt_path": "HLT_OldMu100",
        },
    )

    # HLT_TkMu100 parameters
    tk_mu_100_parameters = _get_updated_dict(
        cascade_mu_100_parameters,
        {
            "flagname": "trg_single_mu100_tk",
            "hlt_path": "HLT_TkMu100",
        },
    )

    # Add triggers to the configuration
    configuration.add_config_parameters(
        MUON_SCOPES,
        {
            "mu_trigger": EraModifier(
                {
                    **{
                        _era: [
                            # trigger:            HLT_IsoMu24
                            # final filter:       - hltL3crIsoL1sSingleMu22L1f0L2f10QL3f24QL3trkIsoFiltered0p08
                            #                     - hltL3crIsoL1sSingleMu22L1f0L2f10QL3f24QL3trkIsoFiltered
                            # filter bit:         1
                            # documentation:      - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2022
                            #                     - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2023
                            #                     - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2024
                            iso_mu_24_parameters,

                            # trigger:            HLT_Mu50
                            # final filter:       hltL3fL1sMu22Or25L1f0L2f10QL3Filtered50Q
                            # filter bit:         10
                            # documentation:      - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2022
                            #                     - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2023
                            #                     - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2024
                            mu_50_parameters,

                            # trigger:            HLT_CascadeMu100
                            # final filter:       hltL3fL1sMu22Or25L1f0L2f10QL3Filtered100Q
                            # filter bit:         11
                            # documentation:      - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2022
                            #                     - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2023
                            #                     - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2024
                            cascade_mu_100_parameters,

                            # trigger:            HLT_HighPtTkMu100
                            # final filter:       hltL3fL1sMu25f0TkFiltered100Q
                            # filter bit:         11
                            # documentation:      - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2022
                            #                     - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2023
                            #                     - https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2024
                            high_pt_tk_mu_100_parameters,
                        ]
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix", "2024"]
                    },
                    "2018": [
                        # trigger:            HLT_IsoMu24
                        # final filter:       hltL3crIsoL1sSingleMu22L1f0L2f10QL3f24QL3trkIsoFiltered0p07
                        # filter bit:         1
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2018
                        iso_mu_24_parameters,

                        # trigger:            HLT_Mu50
                        # final filter:       hltL3fL1sMu22Or25L1f0L2f10QL3Filtered50Q
                        # filter bit:         10
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2018
                        mu_50_parameters,

                        # trigger:            HLT_OldMu100
                        # final filter:       hltL3fL1sMu22Or25L1f0L2f10QL3Filtered100Q
                        # filter bit:         11
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2018
                        old_mu_100_parameters,

                        # trigger:            HLT_TkMu100
                        # final filter:       hltL3fL1sMu25f0TkFiltered100Q
                        # filter bit:         11
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2018
                        tk_mu_100_parameters,
                    ],
                    "2017": [
                        # trigger:            HLT_IsoMu24
                        # final filter:       hltL3crIsoL1sSingleMu22L1f0L2f10QL3f24QL3trkIsoFiltered0p07
                        # filter bit:         1
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2017
                        # comment:            Prescaled for ~4 fb^{-1}
                        iso_mu_24_parameters,

                        # trigger:            HLT_IsoMu27
                        # final filter:       hltL3crIsoL1sMu22Or25L1f0L2f10QL3f27QL3trkIsoFiltered0p07
                        # filter bit:         1
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2017
                        iso_mu_27_parameters,

                        # trigger:            HLT_Mu50
                        # final filter:       hltL3fL1sMu22Or25L1f0L2f10QL3Filtered50Q
                        # filter bit:         10
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2017
                        mu_50_parameters,

                        # trigger:            HLT_OldMu100
                        # final filter:       hltL3fL1sMu22Or25L1f0L2f10QL3Filtered100Q
                        # filter bit:         11
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2017
                        old_mu_100_parameters,

                        # trigger:            HLT_TkMu100
                        # final filter:       hltL3fL1sMu25f0TkFiltered100Q
                        # filter bit:         11
                        # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2017
                        tk_mu_100_parameters,
                    ],
                    **{
                        _era: [
                            # trigger:            HLT_IsoMu22
                            # final filter:       hltL3crIsoL1sMu20L1f0L2f10QL3f22QL3trkIsoFiltered0p09
                            # filter bit:         1
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
                            # comment:            Unclear whether this trigger is prescaled
                            iso_mu_22_parameters,

                            # trigger:            HLT_IsoTkMu22
                            # final filter:       hltL3fL1sMu20L1f0Tkf22QL3trkIsoFiltered0p09
                            # filter bit:         3
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
                            # comment:            Unclear whether this trigger is prescaled
                            iso_tk_mu_22_parameters,

                            # trigger:            HLT_IsoMu22_eta2p1
                            # final filter:       hltL3crIsoL1sSingleMu20erL1f0L2f10QL3f22QL3trkIsoFiltered0p09
                            # filter bit:         1
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
                            # comment:            Unclear whether this trigger is prescaled
                            iso_mu_22_eta2p1_parameters,

                            # trigger:            HLT_IsoTkMu22_eta2p1
                            # final filter:       hltL3fL1sMu20erL1f0Tkf22QL3trkIsoFiltered0p09
                            # filter bit:         3
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
                            # comment:            Unclear whether this trigger is prescaled
                            iso_tk_mu_22_eta2p1_parameters,

                            # trigger:            HLT_IsoMu24
                            # final filter:       hltL3crIsoL1sMu22L1f0L2f10QL3f24QL3trkIsoFiltered0p09
                            # filter bit:         1
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
                            iso_mu_24_parameters,

                            # trigger:            HLT_IsoTkMu24
                            # final filter:       hltL3fL1sMu22L1f0Tkf24QL3trkIsoFiltered0p09
                            # filter bit:         3
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
                            iso_tk_mu_24_2016_parameters,

                            # trigger:            HLT_Mu50
                            # final filter:       hltL3fL1sMu22Or25L1f0L2f10QL3Filtered50Q
                            # filter bit:         10
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
                            mu_50_parameters,

                            # trigger:            HLT_TkMu50
                            # final filter:       hltL3fL1sMu25f0TkFiltered50Q
                            # filter bit:         10
                            # documentation:      https://twiki.cern.ch/twiki/bin/view/CMS/MuonHLT2016
                            tk_mu_50_parameters,
                        ]
                        for _era in ["2016preVFP", "2016postVFP"]
                    },
                },
            ),
        },
    )

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
    double_medium_pnet_35_eta_2p3_parameters = _get_updated_dict(
        double_medium_deeptau_35_eta_2p1_2024_parameters,
        {
            "flagname": "trg_double_tau35_mediumpnet",
            "hlt_path": "HLT_DoublePNetTauhPFJet30_Medium_L2NN_eta2p3",
            "p1_max_abs_eta": 2.3,
            "p2_max_abs_eta": 2.3,
        },
    )

    # HLT_DoublePNetTauhPFJet30_Tight_L2NN_eta2p3
    double_tight_pnet_35_eta_2p3_parameters = _get_updated_dict(
        double_medium_pnet_35_eta_2p3_parameters,
        {
            "flagname": "trg_double_tau35_tightpnet",
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

    # HLT_DoubleMediumIsoPFTau35_Trk1_eta2p1_Reg
    double_medium_iso_35_eta_2p1_parameters = _get_updated_dict(
        double_medium_chargediso_hps_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau35_mediumiso",
            "hlt_path": "HLT_DoubleMediumIsoPFTau35_Trk1_eta2p1_Reg",
            "p1_filter_bit": 17,
            "p2_filter_bit": 17,
        },
    )

    # HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg
    double_medium_iso_35_eta_2p1_parameters = _get_updated_dict(
        double_medium_chargediso_hps_35_eta_2p1_parameters,
        {
            "flagname": "trg_double_tau35_mediumcombinediso",
            "hlt_path": "HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg",
            "p1_filter_bit": 17,
            "p2_filter_bit": 17,
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
                        double_medium_pnet_35_eta_2p3_parameters,

                        # trigger:          HLT_DoublePNetTauhPFJet30_Tight_L2NN_eta2p3
                        # final tau filter: hltDoublePFJets30PNetTauhTagTightWPL2DoubleTau
                        # tau filter bit:   11 (for NANOAODv15)
                        # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2024
                        double_tight_pnet_35_eta_2p3_parameters,
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
                    "2018": [
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
                    ],
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
                            # tau filter bit:   17
                            # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2016
                            # comment:          data Run2016B-F, MC; exact filter cannot be catched with filter bit
                            double_medium_iso_35_eta_2p1_parameters,

                            # trigger:          HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg
                            # final tau filter: hltDoublePFTau35TrackPt1MediumIsolationDz02Reg
                            # tau filter bit:   17
                            # documentation:    https://twiki.cern.ch/twiki/bin/view/CMS/TauTrigger#Trigger_Table_for_2016
                            # comment:          data Run 2016G; exact filter cannot be catched with filter bit
                            double_medium_iso_35_eta_2p1_parameters,
                        ]
                        for _era in ["2016preVFP", "2016postVFP"]
                    },
                },
            ),
        },
    )


def add_diTauTriggerSetup(configuration: Configuration):

    # Add isolated and non-isolated single-electron triggers to the et, em, and 
    # ee scopes
    _add_electron_triggers(configuration)

    # Add isolated and non-isolated single-muon triggers to the mt, em, and mm
    # scopes
    _add_muon_triggers(configuration)

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
                        for _era in ["2024"]
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
                    "2017": [
                        {
                            "flagname": "trg_cross_ele24tau30",
                            "hlt_path": "HLT_Ele24_eta2p1_WPTight_Gsf_LooseChargedIsoPFTau30_eta2p1_CrossL1",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 35,
                            "p1_filter_bit": 2.1,
                            "p1_particle_id": 2.1,
                            "p2_min_pt": 1,
                            "p2_max_abs_eta": 11,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                    ],
                    "2016postVFP": [
                        {
                            "flagname": "trg_cross_ele24tau20",
                            "hlt_path": "HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau20_SingleL1",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 25,
                            "p1_filter_bit": 2.1,
                            "p1_particle_id": 2.1,
                            "p2_min_pt": 1,
                            "p2_max_abs_eta": 11,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                        {
                            "flagname": "trg_cross_ele24tau20_crossL1",
                            "hlt_path": "HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau20",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 25,
                            "p1_filter_bit": 2.1,
                            "p1_particle_id": 2.1,
                            "p2_min_pt": 1,
                            "p2_max_abs_eta": 11,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                        {
                            "flagname": "trg_cross_ele24tau30",
                            "hlt_path": "HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau30",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 35,
                            "p1_filter_bit": 2.1,
                            "p1_particle_id": 2.1,
                            "p2_min_pt": 1,
                            "p2_max_abs_eta": 11,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                    ],
                    "2016preVFP": [
                        {
                            "flagname": "trg_cross_ele24tau20",
                            "hlt_path": "HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau20_SingleL1",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 32,
                            "p1_filter_bit": 2.5,
                            "p1_particle_id": 2.1,
                            "p2_min_pt": 1,
                            "p2_max_abs_eta": 11,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                        {
                            "flagname": "trg_cross_ele24tau20_crossL1",
                            "hlt_path": "HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau20",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 25,
                            "p1_filter_bit": 2.1,
                            "p1_particle_id": 2.1,
                            "p2_min_pt": 1,
                            "p2_max_abs_eta": 11,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                        {
                            "flagname": "trg_cross_ele24tau30",
                            "hlt_path": "HLT_Ele24_eta2p1_WPLoose_Gsf_LooseIsoPFTau30",
                            "p1_min_pt": 25,
                            "p1_max_abs_eta": 35,
                            "p1_filter_bit": 2.1,
                            "p1_particle_id": 2.1,
                            "p2_min_pt": 1,
                            "p2_max_abs_eta": 11,
                            "p2_filter_bit": 4,
                            "p2_particle_id": 15,
                            "match_max_delta_r": 0.4,
                        },
                    ],
                }
            ),
        },
    )

    # single electron trigger scale factors
    configuration.add_config_parameters(
        ELECTRON_SCOPES,
        {
            "e_trigger_sf_file": EraModifier(
                {  # TODO clarify if we can actually just use the electron trigger SFs
                    "2016preVFP": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2016preVFP-UL-NanoAODv9/2024-07-02/electron.json.gz",
                    "2016postVFP": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2016postVFP-UL-NanoAODv9/2024-07-02/electron.json.gz",
                    "2017": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2017-UL-NanoAODv9/2024-07-02/electron.json.gz",
                    "2018": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2018-UL-NanoAODv9/2024-07-02/electron.json.gz",
                    "2022preEE": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-22CDSep23-Summer22-NanoAODv12/2025-12-03/electronHlt.json.gz",
                    "2022postEE": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-22EFGSep23-Summer22EE-NanoAODv12/2025-12-03/electronHlt.json.gz",
                    "2023preBPix": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-23CSep23-Summer23-NanoAODv12/2025-12-03/electronHlt.json.gz",
                    "2023postBPix": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-23DSep23-Summer23BPix-NanoAODv12/2025-12-03/electronHlt.json.gz",
                    "2024": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/2025-12-15/electronHlt.json.gz",
                }
            ),
            "ele_trigger_sf": [
                {
                    "e_trigger_flagname": "trg_wgt_single_ele30",
                    "e_trigger_flag": "trg_single_ele30",
                    "e_trigger_era": EraModifier(
                        {
                            **{
                                _era: _era
                                for _era in ERAS_RUN2
                            },
                            "2022preEE": "2022Re-recoBCD",
                            "2022postEE": "2022Re-recoE+PromptFG",
                            "2023preBPix": "2023PromptC",
                            "2023postBPix": "2023PromptD",
                            "2024": "2024Prompt",
                        }
                    ),
                    "e_trigger_sf_name": "Electron-HLT-SF",
                    "e_trigger_path_id_name": "HLT_SF_Ele30_MVAiso90ID",
                    "e_trigger_variation": "sf",
                },
            ],
        },
    )

    # double electron trigger scale factors
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

    # double tau-tau trigger scale factors
    common_double_tautau_trigger_args = {
        "tt_trigger_leg1_sf_name": "ditau",
        "tt_trigger_leg1_variation": "nom",
        "tt_trigger_leg2_sf_name": "ditau",
        "tt_trigger_leg2_variation": "nom",
    }
    configuration.add_config_parameters(
        TT_SCOPES,
        {
            "double_tautau_trigger_leg1_sf": EraModifier(
                {
                    "2018": [
                        {
                            "tt_trigger_leg1_flagname": f"{flag.replace('trg_', 'trg_wgt')}_leg1",
                            "tt_trigger_flag": flag,
                            **common_double_tautau_trigger_args,
                        }
                        for flag in [
                            "trg_double_tau35_mediumiso",
                            "trg_double_tau35_tightiso",
                            "trg_double_tau40_mediumiso",
                            "trg_double_tau40_tightiso",
                        ]
                    ],
                    **{
                        _era: [
                            {
                                "tt_trigger_leg1_flagname": "trg_wgt_double_tau35_mediumdeeptau_leg1",
                                "tt_trigger_flag": "trg_double_tau35_mediumdeeptau",
                                **common_double_tautau_trigger_args,
                            },
                        ]
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    "2024": [
                        {
                            "tt_trigger_leg1_flagname": "trg_wgt_double_tau35_mediumpnet_leg1",
                            "tt_trigger_flag": "trg_double_tau35_mediumpnet",
                            **common_double_tautau_trigger_args,
                        },
                    ],
                },
            ),
            "double_tautau_trigger_leg2_sf": EraModifier(
                {
                    "2018": [
                        {
                            "tt_trigger_leg2_flagname": f"{flag.replace('trg_', 'trg_wgt')}_leg2",
                            "tt_trigger_flag": flag,
                            **common_double_tautau_trigger_args,
                        }
                        for flag in [
                            "trg_double_tau35_mediumiso",
                            "trg_double_tau35_tightiso",
                            "trg_double_tau40_mediumiso",
                            "trg_double_tau40_tightiso",
                        ]
                    ],
                    **{
                        _era: [
                            {
                                "tt_trigger_leg2_flagname": "trg_wgt_double_tau35_mediumdeeptau_leg2",
                                "tt_trigger_flag": "trg_double_tau35_mediumdeeptau",
                                **common_double_tautau_trigger_args,
                            },
                        ]
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    "2024": [
                        {
                            "tt_trigger_leg2_flagname": "trg_wgt_double_tau35_mediumpnet_leg2",
                            "tt_trigger_flag": "trg_double_tau35_mediumpnet",
                            **common_double_tautau_trigger_args,
                        },
                    ],
                },
            ),
        },
    )

    return configuration
