from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import SystematicShift

from ..helpers import cpp_list
from ._util import add_systematic_shift, KeyValueShift

# Uncertainty of the muon energy scale without Rochester correction, as in the
# H -> tautau legacy analyses (v8 spec C37, Q25): region name -> (lower |eta|
# edge, relative uncertainty). The last region has no upper edge; NanoAOD
# muons end at |eta| = 2.4.
MUON_ES_REGIONS = {
    "etalt1p2": (0.0, 0.004),
    "eta1p2to2p1": (1.2, 0.009),
    "eta2p1to2p4": (2.1, 0.027),
}


def muon_es_factors(region: str | None = None, direction: str = "up") -> str:
    """
    The pT scale factors of the regions of MUON_ES_REGIONS, parameter
    muon_es_scale_factors: 1 for every region, or `region` varied up or down by
    its uncertainty.
    """
    sign = {"up": 1, "down": -1}[direction]
    return cpp_list(
        [
            round(1.0 + sign * uncertainty, 6) if name == region else 1.0
            for name, (_, uncertainty) in MUON_ES_REGIONS.items()
        ]
    )


def add_muon_es_config(configuration: Configuration, scopes: list[str]):
    """
    The nominal parameters of the scope-level muon pT scale
    (producers.lepton_energy_scale.MuonPtScale): every factor 1.
    """
    configuration.add_config_parameters(
        scopes,
        {
            "muon_es_abs_eta_edges": cpp_list([edge for edge, _ in MUON_ES_REGIONS.values()]),
            "muon_es_scale_factors": muon_es_factors(),
        },
    )


def add_muon_es_shifts(
    configuration: Configuration,
    era: str,
    producer: Producer,
    regions: dict[str, tuple[str, ...]],
):
    """
    Add shifts of the muon energy scale for the given era:
    CMS_scale_m_<region>_<era> scales the pT of the muons of an |eta| region of
    MUON_ES_REGIONS in the scopes that list it in `regions` (scope -> region
    names), for simulated and embedded events. The pT is scaled before the
    selection, so the shift reaches the selection, the pair and, through the
    four-vector of the muon, the MET.
    """
    unknown = {name for names in regions.values() for name in names} - set(MUON_ES_REGIONS)
    if unknown:
        raise ValueError(f"Unknown muon energy scale regions {sorted(unknown)}.")
    for region in MUON_ES_REGIONS:
        scopes = tuple(scope for scope, names in regions.items() if region in names)
        if not scopes:
            continue
        for direction in ["up", "down"]:
            configuration.add_shift(
                SystematicShift(
                    name=f"CMS_scale_m_{region}_{era}{direction.capitalize()}",
                    shift_config={
                        scopes: {"muon_es_scale_factors": muon_es_factors(region, direction)}
                    },
                    producers={scopes: [producer]},
                ),
                exclude_samples=["data"],
            )


def add_muon_id_iso_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
):
    """
    Add shifts for muon ID and isolation scale factors for the given era.
    """

    # Exclude data, as well as embedding samples, which have their own muon ID
    # and isolation scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # List if shifts for the total systematic shift of the muon ID and isolation
    # scale factors 
    shifts = [
        KeyValueShift(
            name=f"CMS_eff_m_id_{era}",
            key="muon_id_sf_variation",
            value="syst{direction}",
        ),
        KeyValueShift(
            name=f"CMS_eff_m_iso_{era}",
            key="muon_iso_sf_variation",
            value="syst{direction}",
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
