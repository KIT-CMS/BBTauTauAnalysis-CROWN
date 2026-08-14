from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import SystematicShift
from .producers import scalefactors as scalefactors
from .producers import pairselection as pairselection
from .producers import muons as muons
from .producers import electrons as electrons
from .producers import taus as taus

from .constants import ERAS_RUN2


def _get_run2_2022_2023_tau_id_vs_jet_shifts(
    era: str,
    tau_id_algorithm: str,
):
    """
    Shift specifications of the tau ID vs jet scale factor variations for 2022
    and 2023.
    """
    return [
        *[
            {
                "cms_name": f"CMS_eff_t_{tau_id_algorithm}_VSjet_dm_stat{i}_DM{dm}_{era}",
                "shift_key": "tau_id_sf_vsjet_variation",
                "shift_value": f"{{direction}}_stat{i}_dm{dm}",
            }
            for i in range(1, 3)
            for dm in [0, 1, 10, 11]
        ],
        {
            "cms_name": f"CMS_eff_t_{tau_id_algorithm}_VSjet_dm_syst_alleras",
            "shift_key": "tau_id_sf_vsjet_variation",
            "shift_value": "{{direction}}_syst_alleras",
        },
        {
            "cms_name": f"CMS_eff_t_{tau_id_algorithm}_VSjet_dm_syst_{era}",
            "shift_key": "tau_id_sf_vsjet_variation",
            "shift_value": f"{{direction}}_syst_{era}",
        },
    ]


def _get_2024_2025_tau_id_vs_jet_shifts(
    era: str,
    tau_id_algorithm: str,
):
    """
    Shift specifications of the tau ID vs jet scale factor variations for 2024
    and 2025.
    """

    # Set DMs and pt bin edges to the ones used in the scale factor measurement
    dm_bins = [0, 1, 10, 11]
    pt_edges = [20, 40, 60, 200]

    return [
        *[
            {
                "cms_name": f"CMS_eff_t_{tau_id_algorithm}_VSjet_dm_DM{dm}_pt{pt_start}to{pt_stop}_{era}",
                "shift_key": "tau_id_sf_vsjet_variation",
                "shift_value": f"{{direction}}_custom_dm{dm}_pt{pt_start}to{pt_stop}",
            }
            for dm in dm_bins
            for pt_start, pt_stop in zip(pt_edges[:-1], pt_edges[1:])
        ],
    ]


def add_tau_id_vs_jet_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
    scopes: list[str],
    tau_id_algorithm: str = "DeepTau2018v2p5",
):
    """
    Add shifts for tau ID vs jet scale factors for the given era.
     
    The shifts follow the uncertainty scheme
    [recommended by the TAU POG](https://tau-wiki.docs.cern.ch/Corrections/#id-scale-factors).

    Two uncertainty schemes are implemented, depending on the data-taking era:

    - For Run 2 and 2022/2023, the uncertainties are directly taken from the
      correction file. The uncertainties are organized into statistical
      uncertainties of the measurement and systematic uncertainties
      corresponding to different correlation schemes (uncorrelated, correlated
      across eras, correlated across DM bins and eras, ...).

    - For 2024/2025, the uncertainties are decorrelated for the DM and pt bins,
      in which the measurement have been performed.
    """

    # Get list of shifts. The shifts are organized as dictionaries with the key
    # 'variation_name' for the variation to be used for the SF evaluation and
    # 'cms_name' for the name of the shift to be used in the output.
    shifts = None
    if era in ERAS_RUN2 + [
        "2022preEE",
        "2022postEE",
        "2023preBPix",
        "2023postBPix",
    ]:
        shifts = _get_run2_2022_2023_tau_id_vs_jet_shifts(era, tau_id_algorithm=tau_id_algorithm)
    elif era in ["2024", "2025"]:
        shifts = _get_2024_2025_tau_id_vs_jet_shifts(era, tau_id_algorithm=tau_id_algorithm)
    else:
        raise NotImplementedError(f"Shifts for era {era} are not implemented.")

    # Add up and down variation for each shift
    for shift in shifts:
        for direction in ["up", "down"]:
            configuration.add_shift(
                SystematicShift(
                    name=f"{shift['cms_name']}{direction.capitalize()}",
                    shift_config={
                        tuple(scopes): {
                            shift["shift_key"]: shift["shift_value"].format(direction=direction),
                        },
                    },
                    producers={tuple(scopes): producers},
                )
            )


def add_tau_id_vs_e_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
    scopes: list[str],
    tau_id_algorithm: str = "DeepTau2018v2p5",
):
    """
    Add shifts for tau ID vs electron scale factors for the given era.
     
    The shifts follow the uncertainty scheme
    [recommended by the TAU POG](https://tau-wiki.docs.cern.ch/Corrections/#corrections-for-electrons-misidentidfied-as-taus).

    The corrections have been calculated binned in hadronic tau decay modes
    (0, 1, 10, 11) and absolute pseudorapidity (representing ECAL barrel and
    ECAL endcaps). Shifts are performed independently for each of these 2D bins.
    """

    # Independent shifts of the tau ID vs electron scale factor. Shifts are
    # decorrelated between 2D bins in DM x (barrel, endcap).
    shifts = [
        {
            "cms_name": f"CMS_fake_t_{tau_id_algorithm}_VSe_DM{dm}_{eta_region}_{era}",
            "shift_key": "tau_id_sf_vsele_variation",
            "shift_value": f"{{direction}}_custom_dm{dm}_{eta_region}",
        }
        for dm in [0, 1, 10, 11]
        for eta_region in ["barrel", "endcap"]
    ]

    # Add up and down variation for each shift
    for shift in shifts:
        for direction in ["up", "down"]:
            configuration.add_shift(
                SystematicShift(
                    name=f"{shift['cms_name']}{direction.capitalize()}",
                    shift_config={
                        tuple(scopes): {
                            shift["shift_key"]: shift["shift_value"].format(
                                direction=direction
                            ),
                        },
                    },
                    producers={tuple(scopes): producers},
                )
            )


def add_tau_id_vs_mu_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup],
    scopes: list[str],
    tau_id_algorithm: str = "DeepTau2018v2p5",
):
    """
    Add shifts for tau ID vs muon scale factors for the given era.
     
    The shifts follow the uncertainty scheme
    [recommended by the TAU POG](https://tau-wiki.docs.cern.ch/Corrections/#corrections-for-muons-misidentidfied-as-taus).

    The corrections have been calculated binned in the absolute pseudorapidity
    (representing the muon wheels). Shifts are performed independently in
    these bins.
    """

    # Independent shifts of the tau ID vs muon scale factor. Shifts are
    # decorrelated between the different muon wheel regions. 
    shifts = [
        {
            "cms_name": f"CMS_fake_t_{tau_id_algorithm}_VSmu_{eta_region}_{era}",
            "shift_key": "tau_id_sf_vsele_variation",
            "shift_value": f"{{direction}}_custom_{eta_region}",
        }
        for eta_region in (f"wheel{i}" for i in range(1, 6))
    ]

    # Add up and down variation for each shift
    for shift in shifts:
        for direction in ["up", "down"]:
            configuration.add_shift(
                SystematicShift(
                    name=f"{shift['cms_name']}{direction.capitalize()}",
                    shift_config={
                        tuple(scopes): {
                            shift["shift_key"]: shift["shift_value"].format(
                                direction=direction
                            ),
                        },
                    },
                    producers={tuple(scopes): producers},
                )
            )


def add_tau_es_shifts(
    configuration: Configuration,
    era: str,
    producer: Producer | ProducerGroup,
    tau_id_algorithm: str = "DeepTau2018v2p5",
):
    """
    Add shifts for tau energy scale (TES) for the given era.

    The shifts follow the uncertainty scheme
    [recommended by the TAU POG](https://tau-wiki.docs.cern.ch/Corrections/#energy-scale).

    For energy scale variations of genuine hadronic tau decays, variations
    between different DMs are decorrelated. For energy scale variations of
    $\\text{e} \\to \\tau{\\text{h}}$ and $\\mu \\to \\tau{\\text{h}}$ fakes,
    the correlation scheme from the corresponding tau ID (`VSe` and `VSmu`) is
    adopted.
    """

    # Get scopes from the producer object
    scopes = tuple(producer.scopes)

    # Specify properties of the shifts
    shifts = [
        # Shifts for genuine taus decaying hadronically
        *[
            {
                "cms_name": f"CMS_scale_t_{tau_id_algorithm}_DM{dm}_genTau_{era}",
                "shift_key": "tau_es_variation",
                "shift_value": f"{{direction}}_custom_genTau_dm{dm}",
            }
            for dm in [0, 1, 10, 11]
        ],

        # Shifts for electrons faking hadronic taus
        *[
            {
                "cms_name": f"CMS_scale_t_{tau_id_algorithm}_DM{dm}_genElectron_{eta_region}_{era}",
                "shift_key": "tau_es_variation",
                "shift_value": f"{{direction}}_custom_genEle_dm{dm}_{eta_region}",
            }
            for dm in [0, 1, 10, 11]
            for eta_region in ["barrel", "endcap"]
        ],

        # Shifts for muons faking hadronic taus
        *[
            {
                "cms_name": f"CMS_scale_t_{tau_id_algorithm}_genMuon_{eta_region}_{era}",
                "shift_key": "tau_es_variation",
                "shift_value": f"{{direction}}_custom_genMu_{eta_region}",
            }
            for eta_region in (f"wheel{i}" for i in range(1, 6))
        ],
    ]

    # Add up and down variation for each shift 
    for shift in shifts:
        shift_key = shift["shift_key"]
        cms_name = shift["cms_name"]
        for direction in ["up", "down"]:
            shift_value = shift["shift_value"].format(direction=direction)
            configuration.add_shift(
                SystematicShift(
                    name=f"{cms_name}{direction.capitalize()}",
                    shift_config={
                        tuple(scopes): {
                            shift_key: shift_value,
                        },
                    },
                    producers={tuple(scopes): [producer]},
                    # TODO understand why these producers need to be ignored
                    ignore_producers={
                        "et": [pairselection.LVEl1, electrons.VetoElectrons],
                        "mt": [pairselection.LVMu1, muons.VetoMuons],
                        "tt": [],
                    },
                )
            )
