import os
from pathlib import Path

from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import SystematicShift

from ..constants import ERAS_RUN2
from ..helpers import cpp_list
from ..payload_io import get_correction, load_payload
from ._util import add_systematic_shift, KeyValueShift

# The CROWN root, which the payload paths of the configuration are relative to
CROWN_ROOT = Path(os.path.abspath(__file__)).parents[3]

# The |eta| regions of the electron energy scale of tau-embedded events: region
# name -> lower |eta| edge. The barrel ends at 1.479, as in
# embedding::electron::PtCorrection of the core.
EMBEDDING_ELECTRON_ES_REGIONS = {"barrel": 0.0, "endcap": 1.479}
# The payload of the Tau Embedding group (KIT) with the energy scale of the
# embedded electrons per era and region ("nom", "up", "down"), the same values
# as the POG tau_embedding.json.gz (TauEmbeddingSamplesUL). The Run-2 v15
# configuration does not apply its nominal correction; only the relative width
# of its uncertainty is used (v8 spec C32).
EMBEDDING_ELECTRON_ES_PAYLOADS = {
    era: f"data/embedding/eleES_{era}UL.json.gz" for era in ERAS_RUN2
}
EMBEDDING_ELECTRON_ES_CORRECTION = "eleES"
# Eras whose payload has no uncertainty (nom = up = down = 1.0): region ->
# relative width used instead. For 2017 these are the widths of 2016 and 2018
# in the same payload, +-0.5 % in the barrel and +-1.25 % in the endcap (v8 spec
# V34: without precedent for 2017, released by the analysts on 2026-11-24).
EMBEDDING_ELECTRON_ES_FIXED_WIDTHS = {
    "2017": {"barrel": 0.005, "endcap": 0.0125},
}


def embedding_electron_es_factors(era: str) -> dict[str, dict[str, float]]:
    """
    The pT factors of the electron energy scale shifts of tau-embedded events
    in `era`: region -> direction -> factor. They are the relative width of the
    payload, up / nom and down / nom, or 1 +- the fixed width of
    EMBEDDING_ELECTRON_ES_FIXED_WIDTHS in the eras whose payload has none.

    Raises a ValueError if the payload has an uncertainty where a fixed width
    is configured, or none where it is not: a new payload must change the
    configuration knowingly.
    """
    path = str(CROWN_ROOT / EMBEDDING_ELECTRON_ES_PAYLOADS[era])
    correction = get_correction(load_payload(path), EMBEDDING_ELECTRON_ES_CORRECTION, path)
    values = {
        region["key"]: {entry["key"]: entry["value"] for entry in region["value"]["content"]}
        for region in correction["data"]["content"]
    }
    fixed_widths = EMBEDDING_ELECTRON_ES_FIXED_WIDTHS.get(era, {})
    factors = {}
    for region in EMBEDDING_ELECTRON_ES_REGIONS:
        nominal, up, down = (values[region][key] for key in ("nom", "up", "down"))
        if region in fixed_widths:
            if not nominal == up == down == 1.0:
                raise ValueError(
                    f"The embedding electron energy scale of {era} ({region}) has the fixed "
                    f"width {fixed_widths[region]}, but the payload {path} carries "
                    f"nom/up/down = {nominal}/{up}/{down}."
                )
            factors[region] = {
                "up": 1.0 + fixed_widths[region],
                "down": 1.0 - fixed_widths[region],
            }
        else:
            if not 0.0 < down < nominal < up:
                raise ValueError(
                    f"The embedding electron energy scale of {era} ({region}) has no "
                    f"uncertainty in the payload {path}: nom/up/down = {nominal}/{up}/{down}."
                )
            factors[region] = {"up": up / nominal, "down": down / nominal}
    return factors


def embedding_electron_es_config() -> dict[str, str]:
    """
    The nominal parameters of the scope-level electron pT scale
    (producers.lepton_energy_scale.ElectronPtScale): every factor 1.
    """
    return {
        "electron_es_abs_eta_edges": cpp_list(list(EMBEDDING_ELECTRON_ES_REGIONS.values())),
        "electron_es_scale_factors": cpp_list([1.0] * len(EMBEDDING_ELECTRON_ES_REGIONS)),
    }


def add_embedding_electron_es_shifts(
    configuration: Configuration,
    era: str,
    producer: Producer,
    scopes: tuple[str, ...],
):
    """
    Add shifts of the electron energy scale of tau-embedded events for the given
    era: CMS_scale_e_barrel_emb_<era> and CMS_scale_e_endcap_emb_<era> scale the
    corrected pT of the electrons of one region by the factors of
    embedding_electron_es_factors. The pT is scaled before the selection, so
    the shift reaches the selection, the pair and, through the four-vector of
    the electron, the MET.
    """
    factors = embedding_electron_es_factors(era)
    for region in EMBEDDING_ELECTRON_ES_REGIONS:
        for direction in ["up", "down"]:
            configuration.add_shift(
                SystematicShift(
                    name=f"CMS_scale_e_{region}_emb_{era}{direction.capitalize()}",
                    shift_config={
                        scopes: {
                            "electron_es_scale_factors": cpp_list(
                                [
                                    factors[name][direction] if name == region else 1.0
                                    for name in EMBEDDING_ELECTRON_ES_REGIONS
                                ]
                            )
                        }
                    },
                    producers={scopes: [producer]},
                ),
                samples=["embedding"],
            )


def add_electron_id_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add shifts for electron ID scale factors for the given era.
    """

    # Exclude data, as well as embedding samples, which have their own electron
    # ID scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # List if shifts for the total systematic shift of the electron ID and isolation
    # scale factors 
    shifts = [
        KeyValueShift(
            name=f"CMS_eff_e_id_{era}",
            key="ele_id_sf_variation",
            value="sf{direction}",
        ),
    ]

    # Add up and down variation for each shift
    for shift in shifts:
        add_systematic_shift(
            configuration,
            shift,
            producers,
            add_kwargs={"exclude_samples": exclude_samples},
        )


def add_electron_es_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add shifts for electron energy scale variations for the given era.
    """

    # Exclude data, as well as embedding samples
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Systematic shifts for electron energy scale variations, consisting of
    # scale and smearing variations
    shifts = [
        KeyValueShift(
            name=f"CMS_scale_e_{era}",
            key="ele_es_variation",
            value="scale{Direction}",
        ),
        KeyValueShift(
            name=f"CMS_res_e_{era}",
            key="ele_es_variation",
            value="resolution{Direction}",
        ),
    ]

    # Add up and down variation for each shift
    for shift in shifts:
        add_systematic_shift(
            configuration,
            shift,
            producers,
            add_kwargs={"exclude_samples": exclude_samples},
        )
