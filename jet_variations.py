from __future__ import annotations  # needed for type annotations in > python 3.7

from code_generation.configuration import Configuration
from code_generation.systematics import SystematicShift
from code_generation.producer import Producer
from .producers import jets as jets
# from .producers import fatjets as fatjets
from .producers import scalefactors as scalefactors
from .helpers import get_for_era
from .constants import ERAS_RUN3


def _present_samples(configuration: Configuration, *samples):
    """Restrict a hardcoded exclude-sample list to the active sample surface.

    ``Configuration.add_shift`` validates every named ``exclude_samples`` entry
    against ``available_sample_types`` and raises for a name that is absent.
    Reduced profile surfaces (e.g. the MC-only b-tag efficiency profile, which
    carries no ``data``/``embedding``/``embedding_mc``) would trip that check
    on these unconditional JER/JES shift registrations. Intersecting is a no-op
    for the full legacy surface (all names present, order preserved -> byte
    identical registration) and drops absent names for reduced surfaces.
    """
    return [s for s in samples if s in configuration.available_sample_types]


def add_jetVariations(
    configuration: Configuration,
    era: str,
    bjet_id_sf_producer: Producer,
):
    # Get the producers
    producers = [
        jets.JetEnergyCorrectionMC,
        jets.JetEnergyCorrectionMCRegressed,
        jets.Type1JetEnergyCorrectionMC,
    ]

    #########################
    # Jet energy resolution
    #########################
    configuration.add_shift(
        SystematicShift(
            name="jerUncUp",
            shift_config={
                "global": {
                    "jet_jer_shift": '"up"',
                    "fatjet_jer_shift": '"up"',
                },
                # ("mt", "et", "tt"): {"bjet_sf_variation": "up_jer"},
            },
            producers={
                "global": producers,
                # ("mt", "et", "tt"): {scalefactors.btagging_SF},
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jerUncDown",
            shift_config={
                "global": {
                    "jet_jer_shift": '"down"',
                    "fatjet_jer_shift": '"down"',
                },
                # ("mt", "et", "tt"): {"bjet_sf_variation": "down_jer"},
            },
            producers={
                "global": producers,
                # ("mt", "et", "tt"): {scalefactors.btagging_SF},
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    #########################
    # Jet energy scale - Total
    #########################
    JEC_sources = '{"Total"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncTotalUp",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jes"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {bjet_id_sf_producer},
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncTotalDown",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jes"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {bjet_id_sf_producer},
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    #########################
    # HEM 15/16 issue
    #########################
    if era == "2018":
        JEC_sources = '{"HEMIssue"}'
        configuration.add_shift(
            SystematicShift(
                name="jesUncHEMIssueUp",
                shift_config={
                    "global": {
                        "ak4jet_jes_shift_factor": 1,
                        "jet_jes_sources": JEC_sources,
                        "ak8jet_jes_shift_factor": 1,
                        "fatjet_jes_sources": JEC_sources,
                    }
                },
                producers={
                    "global": producers,
                },
            ),
            exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
        )
        configuration.add_shift(
            SystematicShift(
                name="jesUncHEMIssueDown",
                shift_config={
                    "global": {
                        "ak4jet_jes_shift_factor": -1,
                        "jet_jes_sources": JEC_sources,
                        "ak8jet_jes_shift_factor": -1,
                        "fatjet_jes_sources": JEC_sources,
                    }
                },
                producers={
                "global": producers,
            },
            ),
            exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
        )

    #########################
    # Jet energy scale - reduced set (only present for AK4 jets)
    #########################
    JEC_sources = '{"Regrouped_Absolute"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncAbsoluteUp",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesAbsolute"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncAbsoluteDown",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jesAbsolute"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"' + "Regrouped_Absolute_{}".format(era) + '"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncAbsolute{}Up".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {
                    "bjet_sf_variation": "up_jesAbsolute_{}".format(era)
                },
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncAbsolute{}Down".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {
                    "bjet_sf_variation": "down_jesAbsolute_{}".format(era)
                },
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"Regrouped_FlavorQCD"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncFlavorQCDUp",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesFlavorQCD"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncFlavorQCDDown",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jesFlavorQCD"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"Regrouped_BBEC1"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncBBEC1Up",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesBBEC1"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncBBEC1Down",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jesBBEC1"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"' + "Regrouped_BBEC1_{}".format(era) + '"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncBBEC1{}Up".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesBBEC1_{}".format(era)},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncBBEC1{}Down".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {
                    "bjet_sf_variation": "down_jesBBEC1_{}".format(era)
                },
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"Regrouped_HF"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncHFUp",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesHF"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncHFDown",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jesHF"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"' + "Regrouped_HF_{}".format(era) + '"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncHF{}Up".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesHF_{}".format(era)},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncHF{}Down".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jesHF_{}".format(era)},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"Regrouped_EC2"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncEC2Up",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesEC2"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncEC2Down",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jesEC2"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"' + "Regrouped_EC2_{}".format(era) + '"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncEC2{}Up".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesEC2_{}".format(era)},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncEC2{}Down".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jesEC2_{}".format(era)},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"Regrouped_RelativeBal"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncRelativeBalUp",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "up_jesRelativeBal"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncRelativeBalDown",
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {"bjet_sf_variation": "down_jesRelativeBal"},
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    JEC_sources = '{"' + "Regrouped_RelativeSample_{}".format(era) + '"}'
    configuration.add_shift(
        SystematicShift(
            name="jesUncRelativeSample{}Up".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": 1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": 1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {
                    "bjet_sf_variation": "up_jesRelativeSample_{}".format(era)
                },
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )
    configuration.add_shift(
        SystematicShift(
            name="jesUncRelativeSample{}Down".format(era),
            shift_config={
                "global": {
                    "ak4jet_jes_shift_factor": -1,
                    "jet_jes_sources": JEC_sources,
                    "ak8jet_jes_shift_factor": -1,
                    "fatjet_jes_sources": JEC_sources,
                },
                ("mt", "et", "tt"): {
                    "bjet_sf_variation": "down_jesRelativeSample_{}".format(era)
                },
            },
            producers={
                "global": producers,
                ("mt", "et", "tt"): {
                    bjet_id_sf_producer,
                },
            },
        ),
        exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    )

    #########################
    # Jet energy scale - individual
    #########################
    # JEC_sources = '{"AbsoluteStat"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncAbsoluteStatUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesAbsoluteStat",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncAbsoluteStatDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesAbsoluteStat",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"AbsoluteScale"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncAbsoluteScaleUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesAbsoluteScale",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncAbsoluteScaleDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesAbsoluteScale",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"AbsoluteMPFBias"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncAbsoluteMPFBiasUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesAbsoluteMPFBias",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncAbsoluteMPFBiasDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesAbsoluteMPFBias",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"Fragmentation"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncFragmentationUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesFragmentation",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncFragmentationDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesFragmentation",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"SinglePionECAL"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncSinglePionECALUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesSinglePionECAL",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncSinglePionECALDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesSinglePionECAL",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"SinglePionHCAL"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncSinglePionHCALUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesSinglePionHCAL",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncSinglePionHCALDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesSinglePionHCAL",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"FlavorQCD"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncFlavorQCDUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesFlavorQCD",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncFlavorQCDDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesFlavorQCD",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"TimePtEta"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncTimePtEtaUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesTimePtEta",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncTimePtEtaDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesTimePtEta",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeJEREC1"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeJEREC1Up",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeJEREC1",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeJEREC1Down",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeJEREC1",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeJEREC2"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeJEREC2Up",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeJEREC2",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeJEREC2Down",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeJEREC2",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeJERHF"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeJERHFUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeJERHF",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeJERHFDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeJERHF",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativePtBB"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativePtBBUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativePtBB",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativePtBBDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativePtBB",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativePtEC1"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativePtEC1Up",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativePtEC1",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativePtEC1Down",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativePtEC1",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativePtEC2"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativePtEC2Up",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativePtEC2",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativePtEC2Down",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativePtEC2",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativePtHF"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativePtHFUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativePtHF",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativePtHFDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativePtHF",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeBal"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeBalUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeBal",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeBalDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeBal",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeSample"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeSampleUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeSample",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeSampleDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeSample",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeFSR"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeFSRUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeFSR",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeFSRDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeFSR",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeStatFSR"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeStatFSRUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeStatFSR",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeStatFSRDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeStatFSR",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeStatEC"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeStatECUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeStatEC",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeStatECDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeStatEC",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"RelativeStatHF"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeStatHFUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesRelativeStatHF",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncRelativeStatHFDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesRelativeStatHF",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"PileUpDataMC"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpDataMCUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesPileUpDataMC",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpDataMCDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesPileUpDataMC",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"PileUpPtRef"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtRefUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesPileUpPtRef",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtRefDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesPileUpPtRef",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"PileUpPtBB"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtBBUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesPileUpPtBB",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtBBDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesPileUpPtBB",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"PileUpPtEC1"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtEC1Up",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesPileUpPtEC1",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtEC1Down",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesPileUpPtEC1",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"PileUpPtEC2"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtEC2Up",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesPileUpPtEC2",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtEC2Down",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesPileUpPtEC2",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    # JEC_sources = '{"PileUpPtHF"}'
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtHFUp",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": 1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "up_jesPileUpPtHF",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )
    # configuration.add_shift(
    #     SystematicShift(
    #         name="jesUncPileUpPtHFDown",
    #         shift_config={
    #             "global": {
    #                 "ak4jet_jes_shift_factor": -1,
    #                 "jet_jes_sources": JEC_sources,
    #                 "bjet_sf_variation": "down_jesPileUpPtHF",
    #             }
    #         },
    #         producers={"global": JECSimulation},
    #     ),
    #     exclude_samples=_present_samples(configuration, "data", "embedding", "embedding_mc"),
    # )

    return configuration
