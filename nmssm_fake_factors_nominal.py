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

    # -------------------------------------------------------------------------
    # Base configuration
    # -------------------------------------------------------------------------

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
            "ff_2_fraction_name": "process_fractions_subleading",
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

    # -------------------------------------------------------------------------
    # Fake factor variations in semileptonic channels
    # -------------------------------------------------------------------------

    # Concise list of parameter variations
    parameter_variations_sl = [
        # --- Fake factor uncertainties
        {
            "name": "ff_qcd_variation",
            "values": ["QCDFFunc", "QCDFFmcSubUnc"],
            "producers": [
                fakefactors.RawFakeFactorSemileptonic,
                fakefactors.FakeFactorSemileptonic,
            ],
        },
        {
            "name": "ff_tt_variation",
            "values": ["ttbarFFunc"],
            "producers": [
                fakefactors.RawFakeFactorSemileptonic,
                fakefactors.FakeFactorSemileptonic,
            ],
        },
        # --- Process fraction uncertainties
        {
            "name": "ff_fraction_variation",
            "values": [
                "process_fractionsfracQCDUnc",
                "process_fractionsfracTTBarUnc",
            ],
            "producers": [
                fakefactors.RawFakeFactorSemileptonic,
                fakefactors.FakeFactorSemileptonic,
            ],
        },
        # --- DR -> SR correction uncertainties
        {
            "name": "ff_dr_sr_corr_qcd_variation",
            "values": [
                "QCD_DR_SR_CorrStat1Sigma",
                "QCD_DR_SR_CorrSystMCShift",
                "QCD_DR_SR_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorSemileptonic],
        },
        # --- Closure correction uncertainties
        {
            "name": "ff_closure_corr_qcd_variation",
            "values": [
                "QCD_non_closure_CorrStat1Sigma",
                "QCD_non_closure_CorrSystMCShift",
                "QCD_non_closure_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorSemileptonic],
        },
        {
            "name": "ff_closure_corr_tt_variation",
            "values": [
                "ttbar_non_closure_CorrStat1Sigma",
                "ttbar_non_closure_CorrSystMCShift",
                "ttbar_non_closure_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorSemileptonic],
        },
    ]

    # Apply parameter variations
    for parameter_variation in parameter_variations_sl:
        # Get parameter to vary, corresponding shift, and producers to apply
        # the shift to
        parameter = parameter_variation["name"]
        values = parameter_variation["values"]
        producers = parameter_variation["producers"]

        # Define a up and a down shift for each parameter value independently
        for value in values:
            for direction in ["Up", "Down"]:
                value_with_direction = f"{value}{direction}"
                configuration.add_shift(
                    name=value_with_direction,
                    shift_config={
                        tuple(SL_SCOPES): {
                            parameter: value_with_direction,
                        },
                    },
                    producers=producers,
                )

    # -------------------------------------------------------------------------
    # Fake factor variations in fullhadronic channel
    # -------------------------------------------------------------------------

    # Concise list of parameter variations
    parameter_variations_tt = [
        # --- Leading tau

        # --- Fake factor uncertainties
        {
            "name": "ff_1_qcd_variation",
            "values": ["QCDFFunc", "QCDFFmcSubUnc"],
            "producers": [
                fakefactors.RawFakeFactorFullhadronicLeading,
                fakefactors.FakeFactorFullhadronicLeading,
            ],
        },
        {
            "name": "ff_1_tt_variation",
            "values": ["ttbarFFunc"],
            "producers": [
                fakefactors.RawFakeFactorFullhadronicLeading,
                fakefactors.FakeFactorFullhadronicLeading,
            ],
        },
        # --- Process fraction uncertainties
        {
            "name": "ff_1_fraction_variation",
            "values": [
                "process_fractionsfracQCDUnc",
                "process_fractionsfracTTBarUnc",
            ],
            "producers": [
                fakefactors.RawFakeFactorFullhadronicLeading,
                fakefactors.FakeFactorFullhadronicLeading,
            ],
        },
        # --- DR -> SR correction uncertainties
        {
            "name": "ff_1_dr_sr_corr_qcd_variation",
            "values": [
                "QCD_DR_SR_CorrStat1Sigma",
                "QCD_DR_SR_CorrSystMCShift",
                "QCD_DR_SR_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorFullhadronicLeading],
        },
        # --- Closure correction uncertainties
        {
            "name": "ff_1_closure_corr_qcd_variation",
            "values": [
                "QCD_non_closure_CorrStat1Sigma",
                "QCD_non_closure_CorrSystMCShift",
                "QCD_non_closure_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorFullhadronicLeading],
        },
        {
            "name": "ff_1_closure_corr_tt_variation",
            "values": [
                "ttbar_non_closure_CorrStat1Sigma",
                "ttbar_non_closure_CorrSystMCShift",
                "ttbar_non_closure_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorFullhadronicLeading],
        },

        # --- Subleading tau

        # --- Fake factor uncertainties
        {
            "name": "ff_2_qcd_variation",
            "values": ["QCD_subleadingFFunc", "QCD_subleadingFFmcSubUnc"],
            "producers": [
                fakefactors.RawFakeFactorFullhadronicSubleading,
                fakefactors.FakeFactorFullhadronicSubleading,
            ],
        },
        {
            "name": "ff_2_tt_variation",
            "values": ["ttbar_subleadingFFunc"],
            "producers": [
                fakefactors.RawFakeFactorFullhadronicSubleading,
                fakefactors.FakeFactorFullhadronicSubleading,
            ],
        },
        # --- Process fraction uncertainties
        {
            "name": "ff_2_fraction_variation",
            "values": [
                "process_fractions_subleadingfracQCDUnc",
                "process_fractions_subleadingfracTTBarUnc",
            ],
            "producers": [
                fakefactors.RawFakeFactorFullhadronicSubleading,
                fakefactors.FakeFactorFullhadronicSubleading,
            ],
        },
        # --- DR -> SR correction uncertainties
        {
            "name": "ff_2_dr_sr_corr_qcd_variation",
            "values": [
                "QCD_subleading_DR_SR_CorrStat1Sigma",
                "QCD_subleading_DR_SR_CorrSystMCShift",
                "QCD_subleading_DR_SR_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorFullhadronicSubleading],
        },
        # --- Closure correction uncertainties
        {
            "name": "ff_2_closure_corr_qcd_variation",
            "values": [
                "QCD_subleading_non_closure_CorrStat1Sigma",
                "QCD_subleading_non_closure_CorrSystMCShift",
                "QCD_subleading_non_closure_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorFullhadronicSubleading],
        },
        {
            "name": "ff_1_closure_corr_tt_variation",
            "values": [
                "ttbar_subleading_non_closure_CorrStat1Sigma",
                "ttbar_subleading_non_closure_CorrSystMCShift",
                "ttbar_subleading_non_closure_CorrSystBandAsym",
            ],
            "producers": [fakefactors.FakeFactorFullhadronicSubleading],
        },
    ]

    # Apply parameter variations
    for parameter_variation in parameter_variations_tt:
        # Get parameter to vary, corresponding shift, and producers to apply
        # the shift to
        parameter = parameter_variation["name"]
        values = parameter_variation["values"]
        producers = parameter_variation["producers"]

        # Define a up and a down shift for each parameter value independently
        for value in values:
            for direction in ["Up", "Down"]:
                value_with_direction = f"{value}{direction}"
                configuration.add_shift(
                    name=value_with_direction,
                    shift_config={
                        tuple(FH_SCOPES): {
                            parameter: value_with_direction,
                        },
                    },
                    producers=producers,
                )

    # -------------------------------------------------------------------------
    # Configuration optimization and validation
    # -------------------------------------------------------------------------

    configuration.optimize()
    configuration.validate()
    configuration.report()

    return configuration.expanded_configuration()
