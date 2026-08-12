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
    tau_id_vs_jet_algorithm: str,
):
    """
    Shift specifications of the tau ID vs jet scale factor variations for 2022
    and 2023.
    """
    return [
        *[
            {
                "variation_name": f"stat{i}_dm{dm}",
                "cms_name": f"CMS_eff_t_{tau_id_vs_jet_algorithm}_VSjet_dm_stat{i}_DM{dm}_{era}",
            }
            for i in range(1, 3)
            for dm in [0, 1, 10, 11]
        ],
        {
            "variation_name": "syst_alleras",
            "cms_name": f"CMS_eff_t_{tau_id_vs_jet_algorithm}_VSjet_dm_syst_alleras",
        },
        {
            "variation_name": f"syst_{era}",
            "cms_name": f"CMS_eff_t_{tau_id_vs_jet_algorithm}_VSjet_dm_syst_{era}",
        },
    ]


def _get_2024_2025_tau_id_vs_jet_shifts(
    era: str,
    tau_id_vs_jet_algorithm: str,
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
                "variation_name": f"custom_dm{dm}_pt{pt_start}to{pt_stop}",
                "cms_name": f"CMS_eff_t_{tau_id_vs_jet_algorithm}_VSjet_dm_DM{dm}_pt{pt_start}to{pt_stop}_{era}",
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
    tau_id_vs_jet_algorithm: str = "DeepTau2018v2p5",
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
        shifts = _get_run2_2022_2023_tau_id_vs_jet_shifts(era, tau_id_vs_jet_algorithm)
    elif era in ["2024", "2025"]:
        shifts = _get_2024_2025_tau_id_vs_jet_shifts(era, tau_id_vs_jet_algorithm)
    else:
        raise NotImplementedError(f"Shifts for era {era} are not implemented.")

    # Add up and down variation for each shift
    for shift in shifts:
        for direction in ["up", "down"]:
            shift_value = f"{direction}_{shift['variation_name']}"
            configuration.add_shift(
                SystematicShift(
                    name=f"{shift['cms_name']}{direction.capitalize()}",
                    shift_config={
                        tuple(scopes): {
                            "tau_id_sf_vsjet_variation": shift_value,
                        },
                    },
                    producers={tuple(scopes): producers},
                ),
            )


def add_tauVariations(
    configuration: Configuration,
    tau_id_vs_jet_sf_1_producer: Producer,
    tau_id_vs_jet_sf_2_producer: Producer,
    tau_id_vs_ele_sf_1_producer: Producer,
    tau_id_vs_ele_sf_2_producer: Producer,
    tau_id_vs_mu_sf_1_producer: Producer,
    tau_id_vs_mu_sf_2_producer: Producer,
    tau_pt_correction_producer: Producer,
    sample: str
):
    if sample == "embedding" or sample == "embedding_mc" or sample == "data":
        return configuration
    #########################
    # TauvsEleID scale factor shifts
    #########################
    configuration.add_shift(
        SystematicShift(
            name="vsEleBarrelDown",
            shift_config={("et", "mt"): {"tau_sf_vsele_barrel": "down"}},
            producers={("et", "mt"): tau_id_vs_ele_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsEleBarrelUp",
            shift_config={("et", "mt"): {"tau_sf_vsele_barrel": "up"}},
            producers={("et", "mt"): tau_id_vs_ele_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsEleEndcapDown",
            shift_config={("et", "mt"): {"tau_sf_vsele_endcap": "down"}},
            producers={("et", "mt"): tau_id_vs_ele_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsEleEndcapUp",
            shift_config={("et", "mt"): {"tau_sf_vsele_endcap": "up"}},
            producers={("et", "mt"): tau_id_vs_ele_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsEleBarrelDown",
            shift_config={"tt": {"tau_sf_vsele_barrel": "down"}},
            producers={
                "tt": [
                    tau_id_vs_ele_sf_1_producer,
                    tau_id_vs_ele_sf_2_producer,
                ]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsEleBarrelUp",
            shift_config={"tt": {"tau_sf_vsele_barrel": "up"}},
            producers={
                "tt": [
                    tau_id_vs_ele_sf_1_producer,
                    tau_id_vs_ele_sf_2_producer,
                ]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsEleEndcapDown",
            shift_config={"tt": {"tau_sf_vsele_endcap": "down"}},
            producers={
                "tt": [
                    tau_id_vs_ele_sf_1_producer,
                    tau_id_vs_ele_sf_2_producer,
                ]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsEleEndcapUp",
            shift_config={"tt": {"tau_sf_vsele_endcap": "up"}},
            producers={
                "tt": [
                    tau_id_vs_ele_sf_1_producer,
                    tau_id_vs_ele_sf_2_producer,
                ]
            },
        )
    )
    #########################
    # TauvsMuID scale factor shifts
    #########################
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel1Down",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel1": "down"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel1Up",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel1": "up"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel2Down",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel2": "down"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel2Up",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel2": "up"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel3Down",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel3": "down"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel3Up",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel3": "up"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel4Down",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel4": "down"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel4Up",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel4": "up"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel5Down",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel5": "down"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel5Up",
            shift_config={("et", "mt"): {"tau_sf_vsmu_wheel5": "up"}},
            producers={("et", "mt"): tau_id_vs_mu_sf_2_producer},
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel1Down",
            shift_config={"tt": {"tau_sf_vsmu_wheel1": "down"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel1Up",
            shift_config={"tt": {"tau_sf_vsmu_wheel1": "up"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel2Down",
            shift_config={"tt": {"tau_sf_vsmu_wheel2": "down"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel2Up",
            shift_config={"tt": {"tau_sf_vsmu_wheel2": "up"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel3Down",
            shift_config={"tt": {"tau_sf_vsmu_wheel3": "down"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel3Up",
            shift_config={"tt": {"tau_sf_vsmu_wheel3": "up"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel4Down",
            shift_config={"tt": {"tau_sf_vsmu_wheel4": "down"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel4Up",
            shift_config={"tt": {"tau_sf_vsmu_wheel4": "up"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel5Down",
            shift_config={"tt": {"tau_sf_vsmu_wheel5": "down"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="vsMuWheel5Up",
            shift_config={"tt": {"tau_sf_vsmu_wheel5": "up"}},
            producers={
                "tt": [tau_id_vs_mu_sf_1_producer, tau_id_vs_mu_sf_2_producer]
            },
        )
    )
    #########################
    # TES Shifts
    #########################
    configuration.add_shift(
        SystematicShift(
            name="tauEs1prong0pizeroDown",
            shift_config={("et", "mt", "tt"): {"tau_ES_shift_DM0": "down"}},
            producers={("et", "mt", "tt"): tau_pt_correction_producer},
            ignore_producers={
                "et": [pairselection.LVEl1, electrons.VetoElectrons],
                "mt": [pairselection.LVMu1, muons.VetoMuons],
                "tt": [],
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="tauEs1prong0pizeroUp",
            shift_config={("et", "mt", "tt"): {"tau_ES_shift_DM0": "up"}},
            producers={("et", "mt", "tt"): tau_pt_correction_producer},
            ignore_producers={
                "et": [pairselection.LVEl1, electrons.VetoElectrons],
                "mt": [pairselection.LVMu1, muons.VetoMuons],
                "tt": [],
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="tauEs1prong1pizeroDown",
            shift_config={("et", "mt", "tt"): {"tau_ES_shift_DM1": "down"}},
            producers={("et", "mt", "tt"): tau_pt_correction_producer},
            ignore_producers={
                "et": [pairselection.LVEl1, electrons.VetoElectrons],
                "mt": [pairselection.LVMu1, muons.VetoMuons],
                "tt": [],
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="tauEs1prong1pizeroUp",
            shift_config={("et", "mt", "tt"): {"tau_ES_shift_DM1": "up"}},
            producers={("et", "mt", "tt"): tau_pt_correction_producer},
            ignore_producers={
                "et": [pairselection.LVEl1, electrons.VetoElectrons],
                "mt": [pairselection.LVMu1, muons.VetoMuons],
                "tt": [],
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="tauEs3prong0pizeroDown",
            shift_config={("et", "mt", "tt"): {"tau_ES_shift_DM10": "down"}},
            producers={("et", "mt", "tt"): tau_pt_correction_producer},
            ignore_producers={
                "et": [pairselection.LVEl1, electrons.VetoElectrons],
                "mt": [pairselection.LVMu1, muons.VetoMuons],
                "tt": [],
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="tauEs3prong0pizeroUp",
            shift_config={("et", "mt", "tt"): {"tau_ES_shift_DM10": "up"}},
            producers={("et", "mt", "tt"): tau_pt_correction_producer},
            ignore_producers={
                "et": [pairselection.LVEl1, electrons.VetoElectrons],
                "mt": [pairselection.LVMu1, muons.VetoMuons],
                "tt": [],
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="tauEs3prong1pizeroDown",
            shift_config={("et", "mt", "tt"): {"tau_ES_shift_DM11": "down"}},
            producers={("et", "mt", "tt"): tau_pt_correction_producer},
            ignore_producers={
                "et": [pairselection.LVEl1, electrons.VetoElectrons],
                "mt": [pairselection.LVMu1, muons.VetoMuons],
                "tt": [],
            },
        )
    )
    configuration.add_shift(
        SystematicShift(
            name="tauEs3prong1pizeroUp",
            shift_config={("et", "mt", "tt"): {"tau_ES_shift_DM11": "up"}},
            producers={("et", "mt", "tt"): tau_pt_correction_producer},
            ignore_producers={
                "et": [pairselection.LVEl1, electrons.VetoElectrons],
                "mt": [pairselection.LVMu1, muons.VetoMuons],
                "tt": [],
            },
        )
    )
