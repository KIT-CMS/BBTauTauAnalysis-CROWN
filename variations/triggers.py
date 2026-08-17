from code_generation.configuration import Configuration
from code_generation.producer import Producer, ProducerGroup
from code_generation.systematics import SystematicShift


def add_single_electron_trigger_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup] | Producer | ProducerGroup,
    scope: str,
):
    """
    Add shifts for single-electron trigger scale factors for the given era and
    scope.
    """

    # If producers is a single Producer or ProducerGroup, convert it to a list
    if isinstance(producers, (Producer, ProducerGroup)):
        producers = [producers]

    # Exclude data, as well as embedding samples, which have their own electron
    # ID scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Get the nominal configuration
    nominal_config = configuration.config_parameters[scope]["ele_trigger_sf"][0]

    for direction in ["up", "down"]:
        # Create a new configuration for the shifted SFs
        shifted_config = nominal_config.copy()
        shifted_config.update({
            "e_trigger_variation":  f"sf{direction}"
        })

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_eff_e_trigger_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        "ele_trigger_sf": [shifted_config],
                    }
                },
                producers={scope: producers},
            ),
            exclude_samples=exclude_samples,
        )


def add_single_muon_trigger_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup] | Producer | ProducerGroup,
    scope: str,
):
    """
    Add shifts for single-muon trigger scale factors for the given era and
    scope.
    """

    # If producers is a single Producer or ProducerGroup, convert it to a list
    if isinstance(producers, (Producer, ProducerGroup)):
        producers = [producers]

    # Exclude data, as well as embedding samples, which have their own electron
    # ID scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Get the nominal configuration
    nominal_config = configuration.config_parameters[scope]["mu_trigger_sf"][0]

    for direction in ["up", "down"]:
        # Create a new configuration for the shifted SFs
        shifted_config = nominal_config.copy()
        shifted_config.update({
            "mu_trigger_variation":  f"syst{direction}"
        })

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_eff_m_trigger_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        "mu_trigger_sf": [shifted_config],
                    }
                },
                producers={scope: producers},
            ),
            exclude_samples=exclude_samples,
        )


def add_double_electron_tau_trigger_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup] | Producer | ProducerGroup,
    scope: str,
):
    """
    Add shifts for double-electron-tau trigger scale factors for the given era
    and scope.
    """

    # If producers is a single Producer or ProducerGroup, convert it to a list
    if isinstance(producers, (Producer, ProducerGroup)):
        producers = [producers]

    # Exclude data, as well as embedding samples, which have their own electron
    # ID scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Get the nominal configuration
    nominal_config_leg1 = (
        configuration.config_parameters[scope]["double_eletau_trigger_leg1_sf"]
    )
    nominal_config_leg2 = (
        configuration.config_parameters[scope]["double_eletau_trigger_leg2_sf"]
    )

    for direction in ["up", "down"]:
        # Create a new configuration for the shifted SFs
        shifted_config_leg1 = nominal_config_leg1.copy()[0]
        shifted_config_leg1.update({
            "et_trigger_leg1_variation": f"sf{direction}"
        })
        shifted_config_leg2 = nominal_config_leg2.copy()[0]
        shifted_config_leg2.update({
            "et_trigger_leg2_variation": direction
        })

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_trig_t_etau_Medium_eff_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        "double_eletau_trigger_leg1_sf": [shifted_config_leg1],
                        "double_eletau_trigger_leg2_sf": [shifted_config_leg2],
                    }
                },
                producers={scope: producers},
            ),
            exclude_samples=exclude_samples,
        )


def add_double_muon_tau_trigger_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup] | Producer | ProducerGroup,
    scope: str,
):
    """
    Add shifts for double-muon-tau trigger scale factors for the given era
    and scope.
    """

    # If producers is a single Producer or ProducerGroup, convert it to a list
    if isinstance(producers, (Producer, ProducerGroup)):
        producers = [producers]

    # Exclude data, as well as embedding samples, which have their own electron
    # ID scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Get the nominal configuration
    nominal_config_leg1 = (
        configuration.config_parameters[scope]["double_mutau_trigger_leg1_sf"]
    )
    nominal_config_leg2 = (
        configuration.config_parameters[scope]["double_mutau_trigger_leg2_sf"]
    )

    for direction in ["up", "down"]:
        # Create a new configuration for the shifted SFs
        shifted_config_leg1 = nominal_config_leg1.copy()[0]
        shifted_config_leg1.update({
            "mt_trigger_leg1_variation": f"syst{direction}"
        })
        shifted_config_leg2 = nominal_config_leg2.copy()[0]
        shifted_config_leg2.update({
            "mt_trigger_leg2_variation": direction
        })

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_trig_t_mutau_Medium_eff_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        "double_mutau_trigger_leg1_sf": [shifted_config_leg1],
                        "double_mutau_trigger_leg2_sf": [shifted_config_leg2],
                    }
                },
                producers={scope: producers},
            ),
            exclude_samples=exclude_samples,
        )


def add_double_tautau_trigger_shifts(
    configuration: Configuration,
    era: str,
    producers: list[Producer | ProducerGroup] | Producer | ProducerGroup,
    scope: str,
):
    """
    Add shifts for double-tau trigger scale factors for the given era and
    scope.
    """

    # If producers is a single Producer or ProducerGroup, convert it to a list
    if isinstance(producers, (Producer, ProducerGroup)):
        producers = [producers]

    # Exclude data, as well as embedding samples, which have their own electron
    # ID scale factors
    exclude_samples = ["data", "embedding", "embedding_mc"]

    # Get the nominal configuration
    nominal_config_leg1 = (
        configuration.config_parameters[scope]["double_tautau_trigger_leg1_sf"]
    )
    nominal_config_leg2 = (
        configuration.config_parameters[scope]["double_tautau_trigger_leg2_sf"]
    )

    for direction in ["up", "down"]:
        # Create a new configuration for the shifted SFs
        shifted_config_leg1 = nominal_config_leg1.copy()[0]
        shifted_config_leg1.update({
            "tt_trigger_leg1_variation": direction
        })
        shifted_config_leg2 = nominal_config_leg2.copy()[0]
        shifted_config_leg2.update({
            "tt_trigger_leg2_variation": direction
        })

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_trig_t_ditau_Medium_eff_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        "double_tautau_trigger_leg1_sf": [shifted_config_leg1],
                        "double_tautau_trigger_leg2_sf": [shifted_config_leg2],
                    }
                },
                producers={scope: producers},
            ),
            exclude_samples=exclude_samples,
        )
