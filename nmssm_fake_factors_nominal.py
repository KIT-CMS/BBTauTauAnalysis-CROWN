from __future__ import annotations  # needed for type annotations in > python 3.7
from typing import List, Union
from .producers import fakefactors as fakefactors
from .producers import scalefactors as scalefactors
from .producers import pairquantities as pairquantities
from .quantities import output as q
from code_generation.friend_trees import FriendTreeConfiguration
from code_generation.modifiers import EraModifier

from .constants import TT_SCOPES, ERAS_RUN2, ERAS_RUN3, SL_SCOPES, FH_SCOPES

FAKE_FACTOR_VERSION = "fake-factors-2026-06-10"


def build_config(
    era: str,
    sample: str,
    scopes: List[str],
    shifts: List[str],
    available_sample_types: List[str],
    available_eras: List[str],
    available_scopes: List[str],
    quantities_map: Union[str, None] = None,
):
    configuration = FriendTreeConfiguration(
        era,
        sample,
        scopes,
        shifts,
        available_sample_types,
        available_eras,
        available_scopes,
        quantities_map,
    )

    # -------------------------------------------------------------------------
    # Fake factor parameter configuration
    # -------------------------------------------------------------------------

    for _channel in ["et", "mt", "tt"]:
        configuration.add_config_parameters(
            [_channel],
            {
                "ff_file": EraModifier(
                    {
                        **{
                            _era: "DOES NOT EXIST"  # placeholder
                            for _era in ERAS_RUN2
                        },
                        **{
                            _era: f"payloads/fake_factors/{FAKE_FACTOR_VERSION}/{_era}/fake_factors_{_channel}.json.gz"
                            for _era in ERAS_RUN3
                        },
                    },
                ),
                "ff_corr_file": EraModifier(
                    {
                        **{
                            _era: "DOES NOT EXIST"  # placeholder
                            for _era in ERAS_RUN2
                        },
                        **{
                            _era: f"payloads/fake_factors/{FAKE_FACTOR_VERSION}/{_era}/FF_corrections_{_channel}.json.gz"
                            for _era in ERAS_RUN3
                        },
                    },
                ),
            },
        )

    # Common parameters for semileptonic channels
    configuration.add_config_parameters(
        SL_SCOPES,
        {
            # --- Correction set names
            "ff_qcd_name": "QCD_fake_factors",
            "ff_tt_name": "ttbar_fake_factors",
            "ff_fraction_name": "process_fractions",
            "ff_corr_dr_sr_qcd_name": "QCD_DR_SR_correction",
            "ff_corr_closure_qcd_name": "QCD_compound_correction",
            "ff_corr_closure_tt_name": "ttbar_compound_correction",
            # --- Variations
            "ff_qcd_variation": "nominal",
            "ff_tt_variation": "nominal",
            "ff_fraction_variation": "nominal",
            "ff_dr_sr_corr_qcd_variation": "nominal",
            "ff_closure_corr_qcd_variation": "nominal",
            "ff_closure_corr_tt_variation": "nominal",
        },
    )

    # Common parameters for fullhadronic channels
    configuration.add_config_parameters(
        TT_SCOPES,
        {
            # --- Leading tau fake ---
            # --- Correction set names
            "ff_1_qcd_name": "QCD_fake_factors",
            "ff_1_tt_name": "ttbar_fake_factors",
            "ff_1_fraction_name": "process_fractions",
            "ff_1_corr_dr_sr_qcd_name": "QCD_DR_SR_correction",
            "ff_1_corr_closure_qcd_name": "QCD_compound_correction",
            "ff_1_corr_closure_tt_name": "ttbar_compound_correction",
            # --- Variations
            "ff_1_qcd_variation": "nominal",
            "ff_1_tt_variation": "nominal",
            "ff_1_fraction_variation": "nominal",
            "ff_1_dr_sr_corr_qcd_variation": "nominal",
            "ff_1_closure_corr_qcd_variation": "nominal",
            "ff_1_closure_corr_tt_variation": "nominal",
            # --- Subleading tau fake ---
            # --- Correction set names
            "ff_2_qcd_name": "QCD_subleading_fake_factors",
            "ff_2_tt_name": "ttbar_subleading_fake_factors",
            "ff_2_fraction_name": "process_fractions",
            "ff_2_corr_dr_sr_qcd_name": "QCD_subleading_DR_SR_correction",
            "ff_2_corr_closure_qcd_name": "QCD_subleading_compound_correction",
            "ff_2_corr_closure_tt_name": "ttbar_subleading_compound_correction",
            # --- Variations
            "ff_2_qcd_variation": "nominal",
            "ff_2_tt_variation": "nominal",
            "ff_2_fraction_variation": "nominal",
            "ff_2_dr_sr_corr_qcd_variation": "nominal",
            "ff_2_closure_corr_qcd_variation": "nominal",
            "ff_2_closure_corr_tt_variation": "nominal",
        },
    )

    # -------------------------------------------------------------------------
    # Fake factor producers in semileptonic channels
    # -------------------------------------------------------------------------

    configuration.add_producers(
        SL_SCOPES,
        [
            fakefactors.FakeFactorSemileptonicQCDInput,
            fakefactors.FakeFactorSemileptonicTTInput,
            fakefactors.FakeFactorSemileptonicFractionInput,
            fakefactors.FakeFactorDRSRCorrectionSemileptonicQCDInput,
            fakefactors.FakeFactorClosureCorrectionSemileptonicQCDInput,
            fakefactors.FakeFactorClosureCorrectionSemileptonicTTInput,
            fakefactors.RawFakeFactorSemileptonic,
            fakefactors.FakeFactorSemileptonic,
        ],
    )

    # -------------------------------------------------------------------------
    # Fake factor producers in fullhadronic channel
    # -------------------------------------------------------------------------

    configuration.add_producers(
        FH_SCOPES,
        [
            fakefactors.FakeFactorFullhadronicLeadingQCDInput,
            fakefactors.FakeFactorFullhadronicLeadingTTInput,
            fakefactors.FakeFactorFullhadronicLeadingFractionInput,
            fakefactors.FakeFactorDRSRCorrectionFullhadronicLeadingQCDInput,
            fakefactors.FakeFactorClosureCorrectionFullhadronicLeadingQCDInput,
            fakefactors.FakeFactorClosureCorrectionFullhadronicLeadingTTInput,
            fakefactors.RawFakeFactorFullhadronicLeading,
            fakefactors.FakeFactorFullhadronicLeading,
            fakefactors.FakeFactorFullhadronicSubleadingQCDInput,
            fakefactors.FakeFactorFullhadronicSubleadingTTInput,
            fakefactors.FakeFactorFullhadronicSubleadingFractionInput,
            fakefactors.FakeFactorDRSRCorrectionFullhadronicSubleadingQCDInput,
            fakefactors.FakeFactorClosureCorrectionFullhadronicSubleadingQCDInput,
            fakefactors.FakeFactorClosureCorrectionFullhadronicSubleadingTTInput,
            fakefactors.RawFakeFactorFullhadronicSubleading,
            fakefactors.FakeFactorFullhadronicSubleading,
        ],
    )

    # -------------------------------------------------------------------------
    # Fake factor outputs in semileptonic channels
    # -------------------------------------------------------------------------

    configuration.add_outputs(
        SL_SCOPES,
        [
            q.fake_factor_raw,
            q.fake_factor,
        ],
    )

    # -------------------------------------------------------------------------
    # Fake factor outputs in fullhadronic channels
    # -------------------------------------------------------------------------

    configuration.add_outputs(
        FH_SCOPES,
        [
            q.fake_factor_1_raw,
            q.fake_factor_1,
            q.fake_factor_2_raw,
            q.fake_factor_2,
        ],
    )

    #########################
    # Finalize and validate the configuration
    #########################

    configuration.optimize()
    configuration.validate()
    configuration.report()

    return configuration.expanded_configuration()
