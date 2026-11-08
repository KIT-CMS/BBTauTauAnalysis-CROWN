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
    nominal_config = configuration.config_parameters[scope]["ele_trigger_sf"]

    for direction in ["up", "down"]:
        shifted_config = []
        for n in nominal_config:
            # Create a new configuration for the shifted SFs
            s = n.copy()
            s.update({
                "e_trigger_variation":  f"sf{direction}"
            })
            shifted_config.append(s)

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_eff_e_trigger_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        "ele_trigger_sf": shifted_config,
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
    nominal_config = configuration.config_parameters[scope]["mu_trigger_sf"]

    for direction in ["up", "down"]:
        # Create a new configuration for the shifted SFs
        shifted_config = []
        for n in nominal_config:
            s = n.copy()
            s.update({
                "mu_trigger_variation":  f"syst{direction}"
            })

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_eff_m_trigger_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        "mu_trigger_sf": shifted_config,
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
    nominal_config = {
        i: configuration.config_parameters[scope][f"eletau_trigger_leg{i}_sf"]
        for i in [1, 2]
    }

    for direction in ["up", "down"]:
        # Create a new configuration for the shifted SFs
        shifted_config = {}
        for i, nominal_config_leg in nominal_config.items():
            for n in nominal_config_leg:
                s = n.copy()
                s.update({
                    f"et_trigger_leg{i}_variation": (
                        f"sf{direction}"
                        if i == 1 else
                        direction
                    )
                })
                shifted_config.setdefault(i, []).append(s)

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_trig_t_etau_Medium_eff_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        f"eletau_trigger_leg{i}_sf": shifted_config_leg
                        for i, shifted_config_leg in shifted_config.items()
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
    nominal_config = {
        i: configuration.config_parameters[scope][f"mutau_trigger_leg{i}_sf"]
        for i in [1, 2]
    }

    for direction in ["up", "down"]:
        shifted_config = {}
        for i, nominal_config_leg in nominal_config.items():
            # Create a new configuration for the shifted SFs
            for n in nominal_config_leg:
                s = nominal_config_leg.copy()
                s.update({
                    f"mt_trigger_leg{i}_variation": (
                        f"syst{direction}"
                        if i == 1 else
                        direction
                    )
                })
                shifted_config.setdefault(i, []).append(s)

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_trig_t_mutau_Medium_eff_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        f"mutau_trigger_leg{i}_sf": shifted_config_leg
                        for i, shifted_config_leg in shifted_config.items()
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
    nominal_config = {
            i: configuration.config_parameters[scope][f"tautau_trigger_leg{i}_sf"]
        for i in [1, 2]
    }

    for direction in ["up", "down"]:
        # Create a new configuration for the shifted SFs
        shifted_config = {}
        for i, nominal_config_leg in nominal_config.items():
            for n in nominal_config_leg:
                s = n.copy()
                s.update({
                    f"tt_trigger_leg{i}_variation": direction
                })
                shifted_config.setdefault(i, []).append(s)

        # Add the shift to the configuration 
        configuration.add_shift(
            SystematicShift(
                name=f"CMS_trig_t_ditau_Medium_eff_{era}{direction.capitalize()}",
                shift_config={
                    scope: {
                        f"tautau_trigger_leg{i}_sf": shifted_config_leg
                        for i, shifted_config_leg in shifted_config.items()
                    }
                },
                producers={scope: producers},
            ),
            exclude_samples=exclude_samples,
        )

