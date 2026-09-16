from __future__ import annotations  # needed for type annotations in > python 3.7

from typing import List
from code_generation.rules import AppendProducer, RemoveProducer, ReplaceProducer
from .producers import embedding as embedding
from .producers import scalefactors as scalefactors
from .producers import pairquantities as pairquantities
from .producers import genparticles as genparticles
from .producers import taus as taus
from .producers import boostedtaus as boostedtaus
from .producers import jets as jets
from .producers import triggers as triggers
from .producers import electrons as electrons
from .quantities import output as q
from code_generation.configuration import Configuration
from code_generation.systematics import SystematicShift, get_adjusted_add_shift_SystematicShift
from code_generation.modifiers import EraModifier
from code_generation.helpers import defaults
from .scripts.SpecialSetups import ES_ID_SCHEME
import numpy as np
measure_tauES = False
measure_eleES = False


def setup_embedding(configuration: Configuration, scopes: List[str], era: str):
    configuration.add_config_parameters(
        "global",
        {
            "met_filters": EraModifier(
                {
                    "2016preVFP": [
                        "Flag_goodVertices",
                        "Flag_globalSuperTightHalo2016Filter",
                        "Flag_HBHENoiseFilter",
                        "Flag_HBHENoiseIsoFilter",
                        "Flag_EcalDeadCellTriggerPrimitiveFilter",
                        "Flag_BadPFMuonFilter",
                        "Flag_eeBadScFilter",
                    ],
                    "2016postVFP": [
                        "Flag_goodVertices",
                        "Flag_globalSuperTightHalo2016Filter",
                        "Flag_HBHENoiseFilter",
                        "Flag_HBHENoiseIsoFilter",
                        "Flag_EcalDeadCellTriggerPrimitiveFilter",
                        "Flag_BadPFMuonFilter",
                        "Flag_eeBadScFilter",
                    ],
                    "2017": [
                        "Flag_goodVertices",
                        "Flag_globalSuperTightHalo2016Filter",
                        "Flag_HBHENoiseFilter",
                        "Flag_HBHENoiseIsoFilter",
                        "Flag_EcalDeadCellTriggerPrimitiveFilter",
                        "Flag_BadPFMuonFilter",
                        "Flag_eeBadScFilter",
                        "Flag_ecalBadCalibFilter",
                    ],
                    "2018": [
                        "Flag_goodVertices",
                        "Flag_globalSuperTightHalo2016Filter",
                        "Flag_HBHENoiseFilter",
                        "Flag_HBHENoiseIsoFilter",
                        "Flag_EcalDeadCellTriggerPrimitiveFilter",
                        "Flag_BadPFMuonFilter",
                        "Flag_eeBadScFilter",
                        "Flag_ecalBadCalibFilter",
                    ],
                }
            ),
        },
    )
    configuration.add_modification_rule(
        scopes,
        AppendProducer(
            producers=embedding.EmbeddingQuantities,
            samples=["embedding", "embedding_mc"],
        ),
    )

    # modify the gen particle producer
    configuration.add_modification_rule(
        ["mt"],
        ReplaceProducer(
            producers=[genparticles.MTGenPair, genparticles.EmbeddingGenPair],
            samples=["embedding", "embedding_mc"],
            scopes=["mt"],
        ),
    )
    configuration.add_modification_rule(
        ["et"],
        ReplaceProducer(
            producers=[genparticles.ETGenPair, genparticles.EmbeddingGenPair],
            samples=["embedding", "embedding_mc"],
            scopes=["et"],
        ),
    )
    configuration.add_modification_rule(
        ["tt"],
        ReplaceProducer(
            producers=[genparticles.TTGenPair, genparticles.EmbeddingGenPair],
            samples=["embedding", "embedding_mc"],
            scopes=["tt"],
        ),
    )
    configuration.add_modification_rule(
        ["mm"],
        ReplaceProducer(
            producers=[genparticles.MuMuGenPair, genparticles.EmbeddingGenPair],
            samples=["embedding", "embedding_mc"],
            scopes=["mm"],
        ),
    )
    configuration.add_config_parameters(
        ["mt", "et", "tt"],
        {
            "truegen_mother_pdgid": 23,
            "truegen_daughter_1_pdgid": 15,
            "truegen_daugher_2_pdgid": 15,
        },
    )
    configuration.add_config_parameters(
        ["mm"],
        {
            "truegen_mother_pdgid": 23,
            "truegen_daughter_1_pdgid": 13,
            "truegen_daugher_2_pdgid": 13,
        },
    )

    # add embedding selection scalefactors
    configuration.add_config_parameters(
        scopes,
        {
            "embedding_selection_sf_file": EraModifier(
                {
                    "2016preVFP": "data/embedding/embeddingselection_2016preVFPUL.json.gz",
                    "2016postVFP": "data/embedding/embeddingselection_2016postVFPUL.json.gz",
                    "2017": "data/embedding/embeddingselection_2017UL.json.gz",
                    "2018": "data/embedding/embeddingselection_2018UL.json.gz",
                }
            ),
            "embedding_selection_trigger_sf": "m_sel_trg_kit_ratio",
            "embedding_selection_id_sf": "EmbID_pt_eta_bins",
        },
    )
    configuration.add_modification_rule(
        scopes,
        AppendProducer(
            producers=embedding.TauEmbeddingSelectionSF, samples=["embedding"]
        ),
    )
    # add muon scalefactors from embedding measurements
    configuration.add_config_parameters(
        ["mt", "mm"],
        {
            "embedding_muon_sf_file": EraModifier(
                {
                    "2016preVFP": "data/embedding/muon_2016preVFPUL.json.gz",
                    "2016postVFP": "data/embedding/muon_2016postVFPUL.json.gz",
                    "2017": "data/embedding/muon_2017UL.json.gz",
                    "2018": "data/embedding/muon_2018UL.json.gz",
                }
            ),
            "embedding_muon_id_sf": "ID_pt_eta_bins",
            "embedding_muon_iso_sf": "Iso_pt_eta_bins",
            "embedding_muon_id_extrapolation": 1.0,
            "embedding_muon_iso_extrapolation": 1.0,
        },
    )
    # add electron scalefactors from embedding measurements
    configuration.add_config_parameters(
        ["et"],
        {
            "embedding_electron_sf_file": EraModifier(
                {
                    "2016preVFP": "data/embedding/electron_2016preVFPUL.json.gz",
                    "2016postVFP": "data/embedding/electron_2016postVFPUL.json.gz",
                    "2017": "data/embedding/electron_2017UL.json.gz",
                    "2018": "data/embedding/electron_2018UL.json.gz",
                }
            ),
            "embedding_electron_id_sf": "ID90_pt_eta_bins",
            "embedding_electron_iso_sf": "Iso_pt_eta_bins",
            "embedding_electron_id_extrapolation": 1.0,
            "embedding_electron_iso_extrapolation": 1.0,
        },
    )
    # muon trigger SF settings from embedding measurements
    configuration.add_config_parameters(
        ["mt", "mm"],
        {
            "singlemuon_trigger_sf": EraModifier(
                {
                    "2018": [
                        {
                            "flagname": "trg_wgt_single_mu24",
                            "embedding_trigger_sf": "Trg_IsoMu24_pt_eta_bins",
                            "muon_trg_extrapolation": 1.0,  # for nominal case
                        },
                        # {
                        #     "flagname": "trg_wgt_single_mu27",
                        #     "embedding_trigger_sf": "Trg_IsoMu27_pt_eta_bins",
                        #     "muon_trg_extrapolation": 1.0,  # for nominal case
                        # },
                        # {
                        #     "flagname": "trg_wgt_single_mu24ormu27",
                        #     "embedding_trigger_sf": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
                        #     "muon_trg_extrapolation": 1.0,  # for nominal case
                        # },
                    ],
                    "2017": [
                        {
                            "flagname": "trg_wgt_single_mu24",
                            "embedding_trigger_sf": "Trg_IsoMu24_pt_eta_bins",
                            "muon_trg_extrapolation": 1.0,  # for nominal case
                        },
                        {
                            "flagname": "trg_wgt_single_mu27",
                            "embedding_trigger_sf": "Trg_IsoMu27_pt_eta_bins",
                            "muon_trg_extrapolation": 1.0,  # for nominal case
                        },
                        {
                            "flagname": "trg_wgt_single_mu24ormu27",
                            "embedding_trigger_sf": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
                            "muon_trg_extrapolation": 1.0,  # for nominal case
                        },
                    ],
                    "2016postVFP": [
                        {
                            "flagname": "trg_wgt_single_mu22",
                            "embedding_trigger_sf": "Trg_pt_eta_bins",
                            "muon_trg_extrapolation": 1.0,  # for nominal case
                        },
                    ],
                    "2016preVFP": [
                        {
                            "flagname": "trg_wgt_single_mu22",
                            "embedding_trigger_sf": "Trg_pt_eta_bins",
                            "muon_trg_extrapolation": 1.0,  # for nominal case
                        },
                    ],
                }
            )
        },
    )
    # electron trigger SF settings from embedding measurements
    configuration.add_config_parameters(
        ["et"],
        {
            "singlelectron_trigger_sf": EraModifier(
                {
                    "2018": [
                        {
                            "flagname": "trg_wgt_single_ele32",
                            "embedding_trigger_sf": "Trg32_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        },
                        {
                            "flagname": "trg_wgt_single_ele35",
                            "embedding_trigger_sf": "Trg35_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        },
                        {
                            "flagname": "trg_wgt_single_ele32orele35",
                            "embedding_trigger_sf": "Trg32_or_Trg35_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        },
                        # {
                        #     "flagname": "trg_wgt_single_ele27orele32orele35",
                        #     "embedding_trigger_sf": "Trg_Iso_pt_eta_bins",
                        #     "electron_trg_extrapolation": 1.0,  # for nominal case
                        # },
                    ],
                    "2017": [
                        {
                            "flagname": "trg_wgt_single_ele32",
                            "embedding_trigger_sf": "Trg32_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        },
                        {
                            "flagname": "trg_wgt_single_ele35",
                            "embedding_trigger_sf": "Trg35_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        },
                        {
                            "flagname": "trg_wgt_single_ele32orele35",
                            "embedding_trigger_sf": "Trg32_or_Trg35_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        },
                        {
                            "flagname": "trg_wgt_single_ele27orele32orele35",
                            "embedding_trigger_sf": "Trg_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        },
                    ],
                    "2016postVFP": [
                        {
                            "flagname": "trg_wgt_single_ele25",
                            "embedding_trigger_sf": "Trg25_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        }
                    ],
                    "2016preVFP": [
                        {
                            "flagname": "trg_wgt_single_ele25",
                            "embedding_trigger_sf": "Trg25_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.0,  # for nominal case
                        }
                    ],
                }
            )
        },
    )
    # ditau trigger SF settings for embedding
    configuration.add_config_parameters(
        ["tt"],
        {
            "ditau_trigger_wp": "Medium",
            "ditau_trigger_type": "ditau",
            "ditau_trigger_corrtype": "sf",
            "ditau_trigger_syst": "nom",
            "emb_ditau_trigger_file": EraModifier(
                {
                    "2016preVFP": "",
                    "2016postVFP": "",
                    "2017": "",
                    "2018": "data/embedding/tau_trigger2018_UL.json.gz",
                }
            ),
        },
    )
    configuration.add_modification_rule(
        ["mt"],
        AppendProducer(
            producers=[
                embedding.TauEmbeddingMuonIDSF_1,
                embedding.TauEmbeddingMuonIsoSF_1,
                # embedding.TauEmbeddingBoostedMuonIDSF_1,
                # embedding.TauEmbeddingBoostedMuonIsoSF_1,
                embedding.MTGenerateSingleMuonTriggerSF,
            ],
            samples=["embedding"],
        ),
    )
    configuration.add_modification_rule(
        ["et"],
        AppendProducer(
            producers=[
                # embedding.TauEmbeddingElectronIsoSF_1,
                # embedding.TauEmbeddingElectronIDSF_1,
                # embedding.TauEmbeddingBoostedElectronIDSF_1,
                # embedding.TauEmbeddingBoostedElectronIsoSF_1,
                embedding.ETGenerateSingleElectronTriggerSF,
            ],
            samples=["embedding"],
        ),
    )
    configuration.add_producers(
        "et",
        [
            embedding.TauEmbeddingElectronIsoSF_1,
            embedding.TauEmbeddingElectronIDSF_1,
        ],
    )
    configuration.add_outputs(
            ["et"],
            [
                q.iso_wgt_ele_1,
                q.id_wgt_emb_ele_1,
            ],
        )
    configuration.add_modification_rule(
        ["tt"],
        AppendProducer(
            producers=[embedding.TTGenerateDoubleTauTriggerSF],
            samples=["embedding", "embedding_mc"],
        ),
    )
    configuration.add_modification_rule(
        ["mm"],
        AppendProducer(
            producers=[
                embedding.TauEmbeddingMuonIDSF_1,
                embedding.TauEmbeddingMuonIsoSF_1,
                embedding.TauEmbeddingMuonIDSF_2,
                embedding.TauEmbeddingMuonIsoSF_2,
                embedding.MTGenerateSingleMuonTriggerSF,
            ],
            samples=["embedding"],
        ),
    )
    # remove some gen producers
    configuration.add_modification_rule(
        ["et", "mt", "tt"],
        RemoveProducer(
            producers=[pairquantities.taujet_pt_2, genparticles.gen_taujet_pt_2],
            samples=["embedding", "embedding_mc"],
        ),
    )
    configuration.add_modification_rule(
        ["tt"],
        RemoveProducer(
            producers=[pairquantities.taujet_pt_1, genparticles.gen_taujet_pt_1],
            samples=["embedding", "embedding_mc"],
        ),
    )
    # configuration.add_modification_rule(
    #     "global",
    #     RemoveProducer(
    #         producers=jets.JetEnergyCorrection, samples=["embedding", "embdding_mc"]
    #     ),
    # )

    # For the tau related triggers, in embedding, we cannot use a trigger path directly, since they are not
    # correctly represented in embedded samples. Instead, it is possible to match to an earlier filter
    # within the trigger sequence. In order to do this, we have to use another producer
    # and not the regular trigger producer. Also we have to match to special filter bits:
    # tt -> bit 20
    # mt -> bit 21
    configuration.add_config_parameters(
        ["tt"],
        {
            # here we do not match to the hlt path, only the filter
            "doubletau_trigger_embedding": EraModifier(
                {
                    "2018": [
                        {
                            "flagname": "trg_double_tau35_mediumiso",
                            "p1_ptcut": 35,
                            "p2_ptcut": 35,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": -1,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": -1,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                        {
                            "flagname": "trg_double_tau40_tightiso",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": -1,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": -1,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                        {
                            "flagname": "trg_double_tau40_mediumiso",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": -1,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": -1,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                        {
                            "flagname": "trg_double_tau35_tightiso",
                            "p1_ptcut": 35,
                            "p2_ptcut": 35,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": -1,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": -1,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                    ],
                    "2017": [
                        {
                            "flagname": "trg_double_tau40_tightiso",
                            "hlt_path": "HLT_DoubleTightChargedIsoPFTau40_Trk1_eta2p1_Reg",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": 6,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": 6,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                        {
                            "flagname": "trg_double_tau40_mediumiso_tightid",
                            "hlt_path": "HLT_DoubleMediumChargedIsoPFTau40_Trk1_TightID_eta2p1_Reg",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": 6,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": 6,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                        {
                            "flagname": "trg_double_tau35_tightiso_tightid",
                            "hlt_path": "HLT_DoubleTightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": 6,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": 6,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                    ],
                    "2016postVFP": [
                        {
                            "flagname": "trg_double_tau35_mediumiso",
                            "hlt_path": "HLT_DoubleMediumIsoPFTau35_Trk1_eta2p1_Reg",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": 6,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": 6,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                        {
                            "flagname": "trg_double_tau35_mediumcombiso",
                            "hlt_path": "HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": 6,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": 6,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                    ],
                    "2016preVFP": [
                        {
                            "flagname": "trg_double_tau35_mediumiso",
                            "hlt_path": "HLT_DoubleMediumIsoPFTau35_Trk1_eta2p1_Reg",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": 6,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": 6,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                        {
                            "flagname": "trg_double_tau35_mediumcombiso",
                            "hlt_path": "HLT_DoubleMediumCombinedIsoPFTau35_Trk1_eta2p1_Reg",
                            "p1_ptcut": 40,
                            "p2_ptcut": 40,
                            "p1_etacut": 2.1,
                            "p2_etacut": 2.1,
                            "p1_filterbit": 6,
                            "p1_trigger_particle_id": 15,
                            "p2_filterbit": 6,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        },
                    ],
                }
            ),
        },
    )

    configuration.add_config_parameters(
        ["mt"],
        {
            "mutau_cross_trigger_embedding": EraModifier(
                {
                    "2018": [
                        {
                            "flagname": "trg_cross_mu20tau27_hps",
                            "p1_ptcut": 21,
                            "p1_etacut": 2.5,
                            "p1_filterbit": 3,
                            "p1_trigger_particle_id": 13,
                            "p2_ptcut": 32,
                            "p2_etacut": 2.1,
                            "p2_filterbit": 20,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        }
                    ],
                    "2017": [
                        {
                            "flagname": "trg_cross_mu20tau27",
                            "hlt_path": "HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1",
                            "p1_ptcut": 21,
                            "p1_etacut": 2.1,
                            "p1_filterbit": 3,
                            "p1_trigger_particle_id": 13,
                            "p2_ptcut": 32,
                            "p2_etacut": 2.1,
                            "p2_filterbit": 4,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        }
                    ],
                    "2016preVFP": [
                        {
                            "flagname": "trg_cross_mu19tau20",
                            "hlt_path": "HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1",
                            "p1_ptcut": 20,
                            "p1_etacut": 2.1,
                            "p1_filterbit": 3,
                            "p1_trigger_particle_id": 13,
                            "p2_ptcut": 25,
                            "p2_etacut": 2.1,
                            "p2_filterbit": 4,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        }
                    ],
                    "2016postVFP": [
                        {
                            "flagname": "trg_cross_mu19tau20",
                            "hlt_path": "HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1",
                            "p1_ptcut": 20,
                            "p1_etacut": 2.1,
                            "p1_filterbit": 3,
                            "p1_trigger_particle_id": 13,
                            "p2_ptcut": 25,
                            "p2_etacut": 2.1,
                            "p2_filterbit": 4,
                            "p2_trigger_particle_id": 15,
                            "max_deltaR_triggermatch": 0.4,
                        }
                    ],
                }
            ),
        },
    )

    # use other trigger flags for embedding samples
    configuration.add_modification_rule(
        "tt",
        ReplaceProducer(
            producers=[
                triggers.TauTauTriggerFlags,
                triggers.TTGenerateDoubleTriggerFlagsEmbedding,
            ],
            samples="embedding",
        ),
    )
    configuration.add_outputs(
        "tt", triggers.TTGenerateDoubleTriggerFlagsEmbedding.output_group
    )

    # use other trigger flags for embedding samples
    # configuration.add_modification_rule(
    #     "mt",
    #     ReplaceProducer(
    #         producers=[
    #             triggers.MTGenerateCrossTriggerFlags,
    #             triggers.MTGenerateCrossTriggerFlagsEmbedding,
    #         ],
    #         samples="embedding",
    #     ),
    # )
    # configuration.add_outputs(
    #     "mt", triggers.MTGenerateCrossTriggerFlagsEmbedding.output_group
    # )

    ######################
    ## Tau ID SFs
    ######################

    # replace TauID producers for embedding samples
    configuration.add_config_parameters(
        ["mt", "et"],
        {
            "tau_emb_sf_file": EraModifier(
                {
                    "2016preVFP": "data/embedding/tau_2016preVFPUL.json.gz",
                    "2016postVFP": "data/embedding/tau_2016postVFPUL.json.gz",
                    "2017": "data/embedding/tau_2017UL.json.gz",
                    "2018": "payloads/Tau_ID_ES/embedding/DeepTau2018v2p5_id_es_embedding2018UL.json.gz",
                }
            ),
            "tau_emb_ES_json_name": configuration.ES_ID_SCHEME.embedding.tau_emb_ES_json_name,
            "tau_emb_sf_vsjet_DM0": "nom",
            "tau_emb_sf_vsjet_DM1": "nom",
            "tau_emb_sf_vsjet_DM10": "nom",
            "tau_emb_sf_vsjet_DM11": "nom",
            "tau_emb_sf_vsjet_DM0_20to40": "nom",
            "tau_emb_sf_vsjet_DM0_40toInf": "nom",
            "tau_emb_sf_vsjet_DM1_20to40": "nom",
            "tau_emb_sf_vsjet_DM1_40toInf": "nom",
            "tau_emb_sf_vsjet_DM10_20to40": "nom",
            "tau_emb_sf_vsjet_DM10_40toInf": "nom",
            "tau_emb_sf_vsjet_DM11_20to40": "nom",
            "tau_emb_sf_vsjet_DM11_40toInf": "nom",
            "tau_emb_ES_WP": "Tight",
            "tau_vsjet_vseleWP": "VVLoose",
            "tau_emb_id_sf_correctionset": "DeepTau2018v2p5VSjet",
            "tau_emb_vsjet_sf_dependence": configuration.ES_ID_SCHEME.embedding.tau_emb_vsjet_sf_dependence,
            "vsjet_tau_id_sf_embedding": [
                {
                    "tau_1_vsjet_sf_outputname": "id_wgt_tau_vsJet_{wp}_1".format(
                        wp=wp
                    ),
                    "tau_2_vsjet_sf_outputname": "id_wgt_tau_vsJet_{wp}_2".format(
                        wp=wp
                    ),
                    "vsjet_tau_id_WP": "{wp}".format(wp=wp),
                }
                for wp in [
                    # "VVVLoose",
                    # "VVLoose",
                    # "VLoose",
                    # "Loose",
                    "Medium",
                    "Tight",
                    # "VTight",
                    # "VVTight",
                ]
            ],
        },
    )
    configuration.add_config_parameters(
        ["tt", "mt"],
        {
            "tau_emb_vsele_WP_for_vsjet_sf": "VVLoose",
        },
    )
    configuration.add_config_parameters(
        ["et"],
        {
            "tau_emb_vsele_WP_for_vsjet_sf": "Tight",
        },
    )
    # replace TauID producers for embedding samples
    configuration.add_config_parameters(
        ["tt"],
        {
            "tau_emb_sf_file": EraModifier(
                {
                    "2016preVFP": "data/embedding/tau_2016preVFPUL.json.gz",
                    "2016postVFP": "data/embedding/tau_2016postVFPUL.json.gz",
                    "2017": "data/embedding/tau_2017UL.json.gz",
                    "2018": "payloads/Tau_ID_ES/embedding/DeepTau2018v2p5_id_es_embedding2018UL.json.gz",
                }
            ),
            "tau_emb_ES_json_name": configuration.ES_ID_SCHEME.embedding.tau_emb_ES_json_name,
            "tau_emb_sf_vsjet_DM0": "nom",
            "tau_emb_sf_vsjet_DM1": "nom",
            "tau_emb_sf_vsjet_DM10": "nom",
            "tau_emb_sf_vsjet_DM11": "nom",
            "tau_emb_sf_vsjet_DM0_20to40": "nom",
            "tau_emb_sf_vsjet_DM0_40toInf": "nom",
            "tau_emb_sf_vsjet_DM1_20to40": "nom",
            "tau_emb_sf_vsjet_DM1_40toInf": "nom",
            "tau_emb_sf_vsjet_DM10_20to40": "nom",
            "tau_emb_sf_vsjet_DM10_40toInf": "nom",
            "tau_emb_sf_vsjet_DM11_20to40": "nom",
            "tau_emb_sf_vsjet_DM11_40toInf": "nom",
            "tau_emb_ES_WP": "Tight",
            "tau_vsjet_vseleWP": "VVLoose",
            "tau_emb_id_sf_correctionset": "DeepTau2018v2p5VSjet",
            "tau_emb_vsjet_sf_dependence": configuration.ES_ID_SCHEME.embedding.tau_emb_vsjet_sf_dependence, 
            "vsjet_tau_id_sf_embedding": [
                {
                    "tau_1_vsjet_sf_outputname": "id_wgt_tau_vsJet_{wp}_1".format(
                        wp=wp
                    ),
                    "tau_2_vsjet_sf_outputname": "id_wgt_tau_vsJet_{wp}_2".format(
                        wp=wp
                    ),
                    "vsjet_tau_id_WP": "{wp}".format(wp=wp),
                }
                for wp in [
                    # "VVVLoose",
                    # "VVLoose",
                    # "VLoose",
                    # "Loose",
                    "Medium",
                    "Tight",
                    # "VTight",
                    # "VVTight",
                ]
            ],
        },
    )
    configuration.add_modification_rule(
        ["mt", "et", "tt"],
        ReplaceProducer(
            producers=[
                taus.TauEnergyCorrectionMC,
                configuration.ES_ID_SCHEME.embedding.producerGroupES,
            ],
            samples=["embedding"],
        ),
    )
    configuration.add_modification_rule(
        ["et", "mt"],
        ReplaceProducer(
            producers=[scalefactors.TauIDVsJetSF2,configuration.ES_ID_SCHEME.embedding.producerID_2],
            samples=["embedding"],
        ),
    )
    configuration.add_modification_rule(
        ["tt"],
        ReplaceProducer(
            producers=[scalefactors.TauIDVsJetSF1, configuration.ES_ID_SCHEME.embedding.producerID_1],
            samples=["embedding"],
        ),
    )
    configuration.add_modification_rule(
        ["tt"],
        ReplaceProducer(
            producers=[scalefactors.TauIDVsJetSF2, configuration.ES_ID_SCHEME.embedding.producerID_2],
            samples=["embedding"],
        ),
    )
    configuration.add_outputs(
        ["et", "mt"],
        configuration.ES_ID_SCHEME.embedding.producerID_2.output_group,
    )
    configuration.add_outputs(
        "tt",
        [
            configuration.ES_ID_SCHEME.embedding.producerID_1.output_group,
            configuration.ES_ID_SCHEME.embedding.producerID_2.output_group,
        ],
    )
    # and add the variations for it
    # !!! The corresponding producer has to be picked in taus.py, either the pt inclusive or exclusive one. They are named the same !!!
    add_shift = get_adjusted_add_shift_SystematicShift(configuration)
    with defaults(shift_map={"Up": "up", "Down": "down"}):
        with defaults(scopes=("et", "mt")):
            with defaults(producers=[configuration.ES_ID_SCHEME.embedding.producerID_2]):
                for dm in ["DM0", "DM1", "DM10", "DM11"]:
                    for var in configuration.ES_ID_SCHEME.pt_binning:
                        add_shift(name=f"vsJetTau{dm}{var}", shift_key=f"tau_emb_sf_vsjet_{dm}{var}")

        with defaults(scopes="tt", producers=[configuration.ES_ID_SCHEME.embedding.producerID_1, configuration.ES_ID_SCHEME.embedding.producerID_2]):
            for dm in ["DM0", "DM1", "DM10", "DM11"]:
                for var in configuration.ES_ID_SCHEME.pt_binning:
                    add_shift(name=f"vsJetTau{dm}{var}", shift_key=f"tau_emb_sf_vsjet_{dm}{var}")

    #########################
    # Electron id/iso sf shifts
    #########################
    
    configuration.add_shift(
        SystematicShift(
            name="electronIdSFUp",
            scopes=["et"],
            shift_config={
                ("et"): {"embedding_electron_id_extrapolation": 1.02},
            },
            producers={
                ("et"): [
                    embedding.TauEmbeddingElectronIDSF_1,
                ],
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="electronIdSFDown",
            scopes=["et"],
            shift_config={
                ("et"): {"embedding_electron_id_extrapolation": 0.98},
            },
            producers={
                ("et"): [
                    embedding.TauEmbeddingElectronIDSF_1,
                ],
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="electronIsoSFUp",
            scopes=["et"],
            shift_config={
                ("et"): {"embedding_electron_iso_extrapolation": 1.02},
            },
            producers={
                ("et"): [
                    embedding.TauEmbeddingElectronIsoSF_1,
                ],
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="electronIsoSFDown",
            scopes=["et"],
            shift_config={
                ("et"): {"embedding_electron_iso_extrapolation": 0.98},
            },
            producers={
                ("et"): [
                    embedding.TauEmbeddingElectronIsoSF_1,
                ],
            },
        ),
        samples=["embedding", "embedding_mc"],
    )

    #########################
    # Muon id/iso sf shifts
    #########################
    
    configuration.add_shift(
        SystematicShift(
            name="muonIdSFUp",
            scopes=["mt"],
            shift_config={
                ("mt"): {"embedding_muon_id_extrapolation": 1.02},
            },
            producers={
                ("mt"): [
                    embedding.TauEmbeddingMuonIDSF_1,
                ],
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="muonIdSFDown",
            scopes=["mt"],
            shift_config={
                ("mt"): {"embedding_muon_id_extrapolation": 0.98},
            },
            producers={
                ("mt"): [
                    embedding.TauEmbeddingMuonIDSF_1,
                ],
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="muonIsoSFUp",
            scopes=["mt"],
            shift_config={
                ("mt"): {"embedding_muon_iso_extrapolation": 1.02},
            },
            producers={
                ("mt"): [
                    embedding.TauEmbeddingMuonIsoSF_1,
                ],
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="muonIsoSFDown",
            scopes=["mt"],
            shift_config={
                ("mt"): {"embedding_muon_iso_extrapolation": 0.98},
            },
            producers={
                ("mt"): [
                    embedding.TauEmbeddingMuonIsoSF_1,
                ],
            },
        ),
        samples=["embedding", "embedding_mc"],
    )

    #########################
    # Trigger shifts
    #########################
    configuration.add_shift(
        SystematicShift(
            name="singleElectronTriggerSFUp",
            shift_config={
                ("et"): {
                    "singlelectron_trigger_sf": [
                        {
                            "flagname": "trg_wgt_single_ele32orele35",
                            "embedding_trigger_sf": "Trg32_or_Trg35_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.02,
                        },
                        {
                            "flagname": "trg_wgt_single_ele32",
                            "embedding_trigger_sf": "Trg32_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.02,
                        },
                        {
                            "flagname": "trg_wgt_single_ele35",
                            "embedding_trigger_sf": "Trg35_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.02,
                        },
                        {
                            "flagname": "trg_wgt_single_ele27orele32orele35",
                            "embedding_trigger_sf": "Trg_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 1.02,
                        },
                    ]
                }
            },
            producers={("et"): embedding.ETGenerateSingleElectronTriggerSF},
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="singleElectronTriggerSFDown",
            shift_config={
                ("et"): {
                    "singlelectron_trigger_sf": [
                        {
                            "flagname": "trg_wgt_single_ele32orele35",
                            "embedding_trigger_sf": "Trg32_or_Trg35_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 0.98,
                        },
                        {
                            "flagname": "trg_wgt_single_ele32",
                            "embedding_trigger_sf": "Trg32_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 0.98,
                        },
                        {
                            "flagname": "trg_wgt_single_ele35",
                            "embedding_trigger_sf": "Trg35_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 0.98,
                        },
                        {
                            "flagname": "trg_wgt_single_ele27orele32orele35",
                            "embedding_trigger_sf": "Trg_Iso_pt_eta_bins",
                            "electron_trg_extrapolation": 0.98,
                        },
                    ]
                }
            },
            producers={("et"): embedding.ETGenerateSingleElectronTriggerSF},
        ),
        samples=["embedding", "embedding_mc"],
    )

    configuration.add_shift(
        SystematicShift(
            name="singleMuonTriggerSFUp",
            shift_config={
                ("mt", "mm"): {
                    "singlemuon_trigger_sf": EraModifier(
                        {
                            "2018": [
                                {
                                    "flagname": "trg_wgt_single_mu24",
                                    "embedding_trigger_sf": "Trg_IsoMu24_pt_eta_bins",
                                    "muon_trg_extrapolation": 1.02,
                                },
                                {
                                #     "flagname": "trg_wgt_single_mu27",
                                #     "embedding_trigger_sf": "Trg_IsoMu27_pt_eta_bins",
                                #     "muon_trg_extrapolation": 1.02,
                                # },
                                # {
                                #     "flagname": "trg_wgt_single_mu24ormu27",
                                #     "embedding_trigger_sf": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
                                #     "muon_trg_extrapolation": 1.02,
                                },
                            ],
                            "2017": [
                                {
                                    "flagname": "trg_wgt_single_mu24",
                                    "embedding_trigger_sf": "Trg_IsoMu24_pt_eta_bins",
                                    "muon_trg_extrapolation": 1.02,
                                },
                                {
                                    "flagname": "trg_wgt_single_mu27",
                                    "embedding_trigger_sf": "Trg_IsoMu27_pt_eta_bins",
                                    "muon_trg_extrapolation": 1.02,
                                },
                                {
                                    "flagname": "trg_wgt_single_mu24ormu27",
                                    "embedding_trigger_sf": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
                                    "muon_trg_extrapolation": 1.02,
                                },
                            ],
                            "2016postVFP": [
                                {
                                    "flagname": "trg_wgt_single_mu22",
                                    "embedding_trigger_sf": "Trg_pt_eta_bins",
                                    "muon_trg_extrapolation": 1.02,
                                },
                            ],
                            "2016preVFP": [
                                {
                                    "flagname": "trg_wgt_single_mu22",
                                    "embedding_trigger_sf": "Trg_pt_eta_bins",
                                    "muon_trg_extrapolation": 1.02,  # for nominal case
                                },
                            ],
                        }
                    )
                }
            },
            producers={
                ("mt"): embedding.MTGenerateSingleMuonTriggerSF,
                ("mm"): embedding.MTGenerateSingleMuonTriggerSF,
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="singleMuonTriggerSFDown",
            shift_config={
                ("mt", "mm"): {
                    "singlemuon_trigger_sf": EraModifier(
                        {
                            "2018": [
                                {
                                    "flagname": "trg_wgt_single_mu24",
                                    "embedding_trigger_sf": "Trg_IsoMu24_pt_eta_bins",
                                    "muon_trg_extrapolation": 0.98,
                                },
                                # {
                                #     "flagname": "trg_wgt_single_mu27",
                                #     "embedding_trigger_sf": "Trg_IsoMu27_pt_eta_bins",
                                #     "muon_trg_extrapolation": 0.98,
                                # },
                                # {
                                #     "flagname": "trg_wgt_single_mu24ormu27",
                                #     "embedding_trigger_sf": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
                                #     "muon_trg_extrapolation": 0.98,
                                # },
                            ],
                            "2017": [
                                {
                                    "flagname": "trg_wgt_single_mu24",
                                    "embedding_trigger_sf": "Trg_IsoMu24_pt_eta_bins",
                                    "muon_trg_extrapolation": 0.98,
                                },
                                {
                                    "flagname": "trg_wgt_single_mu27",
                                    "embedding_trigger_sf": "Trg_IsoMu27_pt_eta_bins",
                                    "muon_trg_extrapolation": 0.98,
                                },
                                {
                                    "flagname": "trg_wgt_single_mu24ormu27",
                                    "embedding_trigger_sf": "Trg_IsoMu27_or_IsoMu24_pt_eta_bins",
                                    "muon_trg_extrapolation": 0.98,
                                },
                            ],
                            "2016postVFP": [
                                {
                                    "flagname": "trg_wgt_single_mu22",
                                    "embedding_trigger_sf": "Trg_pt_eta_bins",
                                    "muon_trg_extrapolation": 0.98,
                                },
                            ],
                            "2016preVFP": [
                                {
                                    "flagname": "trg_wgt_single_mu22",
                                    "embedding_trigger_sf": "Trg_pt_eta_bins",
                                    "muon_trg_extrapolation": 0.98,
                                },
                            ],
                        }
                    )
                }
            },
            producers={
                ("mt"): embedding.MTGenerateSingleMuonTriggerSF,
                ("mm"): embedding.MTGenerateSingleMuonTriggerSF,
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="ditauTriggerSFUp",
            shift_config={
                ("tt"): {"ditau_trigger_syst": "up"}
            },
            producers={
                ("tt"): embedding.TTGenerateDoubleTauTriggerSF,
            },
        ),
        samples=["embedding", "embedding_mc"],
    )
    configuration.add_shift(
        SystematicShift(
            name="ditauTriggerSFDown",
            shift_config={
                ("tt"): {"ditau_trigger_syst": "down"}
            },
            producers={
                ("tt"): embedding.TTGenerateDoubleTauTriggerSF,
            },
        ),
        samples=["embedding", "embedding_mc"],
    )

    if measure_tauES:
        ###################
        # Tau ES variations for measurement
        # first set the initial variation to nominal

        configuration.add_config_parameters(
            "mt",
            {
                "tau_ES_shift_DM0_byValue": 1.0,
                "tau_ES_shift_DM1_byValue": 1.0,
                "tau_ES_shift_DM10_byValue": 1.0,
                "tau_ES_shift_DM11_byValue": 1.0,
            },
        )
        configuration.add_modification_rule(
            "mt",
            ReplaceProducer(
                producers=[
                    configuration.ES_ID_SCHEME.embedding.producerGroupES,
                    taus.TauEnergyCorrection_Embedding_Measurement,
                ],
                samples=["embedding"],
            ),
        )
        # tauESvariations = [x for x in np.arange(20.0, -20.0 - 0.1, -0.1).round(2).tolist() if x != 0 and x>=-20.0]
        # tauESvariations = [x for x in np.arange(20.0, -20.0 - 0.2, -0.2).round(2).tolist() if x < -12.0 or x > 8.0] # even 
        # tauESvariations = [x for x in np.arange(19.9, -20.0, -0.2).round(2).tolist()] # odd
        tauESvariations = []
        for tauESvariation in tauESvariations:
            name = str(round(tauESvariation, 2)).replace("-", "minus").replace(".", "p")
            configuration.add_shift(
                SystematicShift(
                    name=f"EMBtauESshift_{name}",
                    shift_config={
                        ("mt"): {
                            "tau_ES_shift_DM0_byValue": 1.0
                            + (round(tauESvariation / 100.0, 5)),
                            "tau_ES_shift_DM1_byValue": 1.0
                            + (round(tauESvariation / 100.0, 5)),
                            "tau_ES_shift_DM10_byValue": 1.0
                            + (round(tauESvariation / 100.0, 5)),
                            "tau_ES_shift_DM11_byValue": 1.0
                            + (round(tauESvariation / 100.0, 5)),
                        }
                    },
                    producers={("mt"): taus.TauPtCorrection_byValue},
                ),
                samples=["embedding"],
            )
    else:
        add_shift = get_adjusted_add_shift_SystematicShift(configuration)
        with defaults(shift_map={"Up": "up", "Down": "down"}):
            with defaults(scopes=("et", "mt", "tt")):
                with defaults(producers=[configuration.ES_ID_SCHEME.embedding.producerGroupES],
                                exclude_samples=["data"]):
                            for dm in ["DM0", "DM1", "DM10", "DM11"]:
                                for var in configuration.ES_ID_SCHEME.pt_binning:
                                    add_shift(name=f"tauEs{dm}{var}", shift_key=f"tau_ES_shift_{dm}{var}")

    if measure_eleES:
        ###################
        # Ele fake ES variations for measurement
        # first set the initial variation to nominal
        configuration.add_config_parameters(
            "global",
            {
                "ele_energyscale_barrel": 1.0,
                "ele_energyscale_endcap": 1.0,
            },
        )
        configuration.add_modification_rule(
            "global",
            ReplaceProducer(
                producers=[
                    electrons.ElectronPtCorrectionMC.get(era,"v15"),
                    electrons.ElectronPtCorrectionEmbedding,
                ],
                samples=["embedding"],
            ),
        )
        elefakeESvariations = [-1.5 + 0.05 * i for i in range(0, 51)]
        for elefakeESvariation in elefakeESvariations:
            name = (
                str(round(elefakeESvariation, 2))
                .replace("-", "minus")
                .replace(".", "p")
            )
            configuration.add_shift(
                SystematicShift(
                    name=f"EMBelefakeESshift_{name}",
                    shift_config={
                        ("global"): {
                            "ele_energyscale_barrel": 1.0
                            + (round(elefakeESvariation / 100.0, 5)),
                            "ele_energyscale_endcap": 1.0
                            + (round(elefakeESvariation / 100.0, 5)),
                        }
                    },
                    producers={("global"): electrons.ElectronPtCorrectionEmbedding},
                ),
                samples=["embedding"],
            )
    else:
        # add embedding electron energy scale scalefactors
        configuration.add_config_parameters(
            "global",
            {
                "embedding_electron_es_sf_file": EraModifier(
                    {
                        "2016preVFP": "data/embedding/eleES_2016preVFPUL.json.gz",
                        "2016postVFP": "data/embedding/eleES_2016postVFPUL.json.gz",
                        "2017": "data/embedding/eleES_2017UL.json.gz",
                        "2018": "data/embedding/eleES_2018UL.json.gz",
                    }
                ),
                "ele_ES_json_name": "eleES",
                "ele_energyscale_barrel": "nom",
                "ele_energyscale_endcap": "nom",
            },
        )
        configuration.add_modification_rule(
            "global",
            ReplaceProducer(
                producers=[
                    electrons.ElectronPtCorrectionMC.get(era, "v15"),
                    electrons.ElectronPtCorrectionEmbedding,
                ],
                samples=["embedding"],
            ),
        )
        configuration.add_shift(
            SystematicShift(
                name="eleEsBarrelUp",
                shift_config={("global"): {"ele_energyscale_barrel": "up"}},
                producers={("global"): electrons.ElectronPtCorrectionEmbedding},
            ),
            samples=["embedding"],
        )
        configuration.add_shift(
            SystematicShift(
                name="eleEsBarrelDown",
                shift_config={
                    ("global"): {"ele_energyscale_barrel": "down"},
                },
                producers={("global"): electrons.ElectronPtCorrectionEmbedding},
            ),
            samples=["embedding"],
        )
        configuration.add_shift(
            SystematicShift(
                name="eleEsEndcapUp",
                shift_config={
                    ("global"): {
                        "ele_energyscale_endcap": "up",
                    }
                },
                producers={("global"): electrons.ElectronPtCorrectionEmbedding},
            ),
            samples=["embedding"],
        )
        configuration.add_shift(
            SystematicShift(
                name="eleEsEndcapDown",
                shift_config={
                    ("global"): {
                        "ele_energyscale_endcap": "down",
                    }
                },
                producers={("global"): electrons.ElectronPtCorrectionEmbedding},
            ),
            samples=["embedding"],
        )

    return configuration
