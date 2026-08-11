from __future__ import annotations  # needed for type annotations in > python 3.7

import string
import re

from code_generation.configuration import Configuration
from code_generation.systematics import SystematicShift
from code_generation.producer import Producer, ProducerGroup
from .producers import jets as jets
from .producers import scalefactors as scalefactors


def _add_jes_shift(
    configuration: Configuration,
    producers: list[Producer | ProducerGroup],
    jes_source_fmt: str,
    era: str,
):
    """
    Add up and down variations of a jet energy scale uncertainty source to
    the configuration.
    """

    # Validate the format string for the JEC uncertainty source and validate
    # that the only placeholder is 'era'
    fmt_params = {
        field_name
        for _, field_name, _, _ in string.Formatter().parse(jes_source_fmt)
    }
    if not fmt_params < {"era"}:
        raise ValueError(
            f"JEC source format string '{jes_source_fmt}' cannot be "
            + "evaluated. Format string is only allowed to contain the "
            + "'era' placeholder."
        )

    # Evaluate the format string
    jes_source = jes_source_fmt
    if len(fmt_params) > 0:
        jes_source = jes_source_fmt.format(era=era)

    # Define JES shift factors for 
    jes_shift_factor = {
        "up": 1,
        "down": -1,
    }

    for direction in ["up", "down"]:

        # Construct the shift's name: Remove 'Regrouped_' prefix, remove
        # underscore before era, and add direction. add a 'jes' prefix
        m = re.match(r"(Regrouped_)?([^_]*)(_(.*))?", jes_source)
        name = (
            "jes"
            + (m.group(2) or jes_source)
            + (m.group(4) or "")
            + direction.capitalize()
        )

        # Add shift to the configuration
        configuration.add_shift(
            SystematicShift(
                name=name,
                shift_config={
                    "global": {
                        "ak4jet_jes_shift_factor": jes_shift_factor[direction],
                        "ak4jet_jes_sources": jes_source,
                    },
                },
                producers={"global": producers},
            ),
            exclude_samples=["data", "embedding", "embedding_mc"],
        )


def add_jec_shifts(
    configuration: Configuration,
    era: str,
):
    """
    Add systematic uncertainties related to the jet energy calibration (JEC)
    procedure.

    The function adds a systematic up and down shift for each uncertainty
    source in the jet energy scale (reduced scheme) and for the
    jet energy resolution (one inclusive uncertainty).
    """

    # Producers that jet energy correction shifts are applied to
    producers = [
        jets.JetEnergyCorrectionMC,
        jets.JetEnergyCorrectionMCRegressed,
        jets.Type1JetEnergyCorrectionMC,
    ]

    # Samples to exclude (where jets are already taken from data)
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # -------------------------------------------------------------------------
    # Jet energy scale
    # -------------------------------------------------------------------------

    # Comment: If needed, the JES source groups could be extended to a more
    # granular scheme. Here, the "default" recommendation is implemented.
    # https://cms-jerc.web.cern.ch/Recommendations/#jet-energy-scale_1

    # Groups of uncertainty sources in jet energy scale corrections
    jes_sources = [
        "HEMIssue",  # only to be used in 2018
        "Regrouped_Absolute",
        "Regrouped_Absolute_{era}",
        "Regrouped_FlavorQCD",
        "Regrouped_BBEC1",
        "Regrouped_BBEC1_{era}",
        "Regrouped_HF",
        "Regrouped_HF_{era}",
        "Regrouped_EC2",
        "Regrouped_EC2_{era}",
        "Regrouped_RelativeBal",
        "Regrouped_RelativeSample_{era}",
    ]

    for jes_source in jes_sources:
        # The HEMIssue shift is only applied in 2018
        if jes_source == "HEMIssue" and era != "2018":
            continue

        # Add up and down variation to the configuration
        _add_jes_shift(configuration, era)

    # -------------------------------------------------------------------------
    # Jet energy resolution
    # -------------------------------------------------------------------------

    # Comment: If needed, the JER uncertainties could be extended to a more
    # granular scheme by shifting different (p_T, eta) regions independently.
    # Here, the "default" recommendation is implemented.
    # https://cms-jerc.web.cern.ch/Recommendations/#jet-energy-resolution_1

    for direction in ["up", "down"]:
        # Add shift to the configuration
        configuration.add_shift(
            SystematicShift(
                name=f"jerUnc{direction.capitalize()}",
                shift_config={
                    "global": {
                        "ak4jet_jer_shift": direction,
                    },
                },
                producers={
                    "global": producers,
                },
            ),
            exclude_samples=exclude_samples,
        )

    return configuration

