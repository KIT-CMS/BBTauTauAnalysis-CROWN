from __future__ import annotations  # needed for type annotations in > python 3.7
from typing import List, Union
from .producers import fakefactors as fakefactors
from .producers import scalefactors as scalefactors
from .producers import pairquantities as pairquantities
from .quantities import output as q
from code_generation.friend_trees import FriendTreeConfiguration
from code_generation.modifiers import EraModifier

from .constants import ET_SCOPES, MT_SCOPES, ERAS_RUN2, SL_SCOPES

FAKE_FACTOR_VERSION = "fake-factors-2026-05-09"


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

    # Common configuration parameters in the semileptonic channels
    common_parameters_sl = {
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
        "ff_closure_corr_tt_variation": "nominal"
    }

    # -------------------------------------------------------------------------
    # Fake factor configuration in et channel
    # -------------------------------------------------------------------------

    configuration.add_config_parameters(
        ET_SCOPES,
        {
            "ff_file": EraModifier(
                {
                    **{
                        _era: "DOES NOT EXIST"  # placeholder
                        for _era in ERAS_RUN2
                    },
                    **{
                        _era: "DOES NOT EXIST"  # placeholder
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    "2024": f"payloads/fake_factors/{FAKE_FACTOR_VERSION}/2024/fake_factors_et.json.gz",
                },
            ),
            "ff_corr_file": EraModifier(
                {
                    **{
                        _era: "DOES NOT EXIST"  # placeholder
                        for _era in ERAS_RUN2
                    },
                    **{
                        _era: "DOES NOT EXIST"  # placeholder
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    "2024": f"payloads/fake_factors/{FAKE_FACTOR_VERSION}/2024/FF_corrections_et.json.gz",
                },
            ),
            **common_parameters_sl,
        },
    )

    # -------------------------------------------------------------------------
    # Fake factor configuration in mt channel
    # -------------------------------------------------------------------------

    configuration.add_config_parameters(
        MT_SCOPES,
        {
            "ff_file": EraModifier(
                {
                    **{
                        _era: "DOES NOT EXIST"  # placeholder
                        for _era in ERAS_RUN2
                    },
                    **{
                        _era: "DOES NOT EXIST"  # placeholder
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    "2024": f"payloads/fake_factors/{FAKE_FACTOR_VERSION}/2024/fake_factors_mt.json.gz",
                },
            ),
            "ff_corr_file": EraModifier(
                {
                    **{
                        _era: "DOES NOT EXIST"  # placeholder
                        for _era in ERAS_RUN2
                    },
                    **{
                        _era: "DOES NOT EXIST"  # placeholder
                        for _era in ["2022preEE", "2022postEE", "2023preBPix", "2023postBPix"]
                    },
                    "2024": f"payloads/fake_factors/{FAKE_FACTOR_VERSION}/2024/FF_corrections_mt.json.gz",
                },
            ),
            **common_parameters_sl,
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
        SL_SCOPES,
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
