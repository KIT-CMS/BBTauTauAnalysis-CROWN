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
    era: str,
    jes_source_fmt: str,
    jec_producers: list[Producer | ProducerGroup],
    jec_scopes: tuple[str],
    bjet_tagging_sf_producer: Producer | ProducerGroup | None = None,
    bjet_tagging_sf_scopes: tuple[str] | None = None,
    exclude_samples: list[str] | None = None,
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
        if m is None:
            raise ValueError(
                "Name of jet energy scale uncertainty source '{jes_source}' "
                + "could not be parsed."
            )
        name = (
            "jes"
            + (m.group(2) or jes_source)
            + (m.group(4) or "")
            + direction.capitalize()
        )

        # Construct the shift configuration and the producers that are affected
        shift_config = {
            jec_scopes: {
                "ak4jet_jes_shift_factor": jes_shift_factor[direction],
                "ak4jet_jes_sources": jes_source,
            },
        },
        producers = {jec_scopes: jec_producers},

        # Check if b jet tagging SF producer has been passed. If yes, add the
        # producer and the corresponding shift
        if (
            bjet_tagging_sf_producer is not None
            and bjet_tagging_sf_scopes is not None
        ):
            # Sanitize scope variable and construct name of the shift passed
            # to the b jet tagging SF producer
            shift_value = (
                direction
                + "_jes"
                + m.group(2)
                + (m.group(3) or '')
            )

            # Extend dictionaries for producers and shift config. Prevent that
            # JEC definitions are overwritten.
            shift_config.setdefault(bjet_tagging_sf_scopes, {}).update({
                "bjet_sf_variation": shift_value,
            })
            producers.setdefault(bjet_tagging_sf_scopes, []).append(
                bjet_tagging_sf_producer
            )

        # Add shift to the configuration
        configuration.add_shift(
            SystematicShift(
                name=name,
                shift_config=shift_config,
                producers=producers,
            ),
            exclude_samples=exclude_samples,
        )


def add_jec_shifts(
    configuration: Configuration,
    era: str,
    jec_producers: list[Producer | ProducerGroup],
    bjet_tagging_sf_producer: Producer | ProducerGroup = None,
):
    """
    Add systematic uncertainties related to the jet energy calibration (JEC)
    procedure.

    The function adds a systematic up and down shift for each uncertainty
    source in the jet energy scale (reduced scheme) and for the
    jet energy resolution (one inclusive uncertainty).

    The prodedure follows the JME recommentations for
    [JES](https://cms-jerc.web.cern.ch/Recommendations/#jet-energy-scale_1) and
    [JER](https://cms-jerc.web.cern.ch/Recommendations/#jet-energy-resolution_1)
    uncertainty treatment.

    Notes
    -----

    If shape-based b jet tagging SF are used, the corresponding producer should
    be varied simultaneously with the jet energy calibration shifts. In this
    case, do not forget to add the `bjet_tagging_sf_producer` parameter to this
    function.
    """

    # Get scopes of JEC producers, check for consistency
    jec_scopes = {set(p.scopes) for p in jec_producers}
    if len(jec_scopes) != 1:
        raise ValueError(
            "JEC producers passed to add_jec_shifts are not consistent in "
            + "their scope definition."
        )
    jec_scopes = tuple(jec_scopes.pop())

    # Get scopes of b jet tagging SF producer
    bjet_tagging_sf_scopes = None
    if bjet_tagging_sf_producer is not None:
        bjet_tagging_sf_scopes = tuple(bjet_tagging_sf_producer.scopes)

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
        _add_jes_shift(
            configuration,
            era,
            jes_source,
            jec_producers,
            jec_scopes=jec_scopes,
            bjet_tagging_sf_producer=bjet_tagging_sf_producer,
            bjet_tagging_sf_scopes=bjet_tagging_sf_scopes,
            exclude_samples=exclude_samples,
        )

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
                    jec_scopes: {
                        "ak4jet_jer_shift": direction,
                    },
                },
                producers={
                    jec_scopes: jec_producers,
                },
            ),
            exclude_samples=exclude_samples,
        )

    return configuration

