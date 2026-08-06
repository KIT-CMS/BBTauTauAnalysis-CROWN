from ..quantities import output as q
from ..quantities import nanoAOD
from code_generation.producer import Producer, ProducerGroup
from code_generation.quantity import Quantity
from itertools import product
from ..constants import SCOPES


# ------------------------------------------------------------------------------
# Reconstruction of the H/Y -> b b candidate
# ------------------------------------------------------------------------------


class BBPairSelectionMetaConfiguration():

    _default_inputs = {
        "jet_pt": q.Jet_correctedPt,
        "jet_eta": nanoAOD.Jet_eta,
        "jet_phi": nanoAOD.Jet_phi,
        "jet_mass": q.Jet_correctedMass,
        "good_bjet_collection": q.good_bjet_collection,
        "good_jet_collection": q.good_jet_collection,
        "jet_btag_value": q.Jet_bTagValue,
    }

    _default_outputs = {
        "dibjetpair": q.dibjetpair,
    }

    def __init__(
        self,
        input=None,
        output=None,
        scopes=None,
    ):

        for key, value in self._default_inputs.items():
            setattr(self, key, input.get(key, value) if input else value)
        for key, value in self._default_outputs.items():
            setattr(self, key, output.get(key, value) if output else value)

        self.scopes = scopes

    def producers(self, name: str):
        return self._produce_bb_pair_selection(name=name)

    def configuration_parameters(self):
        return {
            "scopes": self.scopes,
            "parameters": {
                "bb_pairselection_min_dR": 0.4,
            },
        }

    def outputs(self):
        return {
            "scopes": [],
            "outputs": [
                self.dibjetpair,
            ],
        }

    def _produce_bb_pair_selection(
        self,
        name: str,
    ):
        call = f"""
        bb_pairselection::PairSelection(
            {{df}},
            {{input_vec}},
            "{self.jet_btag_value.name}",
            {{output}},
            {{bb_pairselection_min_dR}},
            {{bjet_min_score}}
        )
        """
        return Producer(
            name=name,
            call=call,
            input=[
                self.jet_pt,
                self.jet_eta,
                self.jet_phi,
                self.jet_mass,
                self.good_bjet_collection,
                self.good_jet_collection,
            ],
            output=[self.dibjetpair],
            scopes=SCOPES,
        )


# bb pair selection meta producer using ordinary jet pt after JEC 
BBPairSelection = BBPairSelectionMetaConfiguration(
    input={
        "jet_pt": q.Jet_correctedPt,
        "jet_mass": q.Jet_correctedMass,
    },
    output={
        "dibjetpair": q.dibjetpair,
    },
    scopes=SCOPES,
).producers("BBPairSelection")


# bb pair selection meta producer using PNet/UParT-regressed jet pt after JEC
BBPairSelectionRegressed = BBPairSelectionMetaConfiguration(
    input={
        "jet_pt": q.Jet_correctedPtRegressed,
        "jet_mass": q.Jet_correctedMassRegressed,
    },
    output={
        "dibjetpair": q.dibjetpair_regressed,
    },
    scopes=SCOPES,
).producers("BBPairSelectionRegressed")


# ------------------------------------------------------------------------------
# Single b jet quantities of the selected bb candidate 
# ------------------------------------------------------------------------------


class BQuantitiesMetaConfiguration():

    _default_inputs = {
        "jet_pt": q.Jet_correctedPt,
        "jet_eta": nanoAOD.Jet_eta,
        "jet_phi": nanoAOD.Jet_phi,
        "jet_mass": q.Jet_correctedMass,
        "jet_btag_value": q.Jet_bTagValue,
        "dibjetpair": q.dibjetpair,
    }

    _default_outputs = {
        "bpair_p4_1": q.bpair_p4_1,
        "bpair_p4_2": q.bpair_p4_2,
        "bpair_pt_1": q.bpair_pt_1,
        "bpair_pt_2": q.bpair_pt_2,
        "bpair_eta_1": q.bpair_eta_1,
        "bpair_eta_2": q.bpair_eta_2,
        "bpair_phi_1": q.bpair_phi_1,
        "bpair_phi_2": q.bpair_phi_2,
        "bpair_mass_1": q.bpair_mass_1,
        "bpair_mass_2": q.bpair_mass_2,
        "bpair_btag_value_1": q.bpair_btag_value_1,
        "bpair_btag_value_2": q.bpair_btag_value_2,
    }

    def __init__(
        self,
        input=None,
        output=None,
        scopes=None,
    ):

        for key, value in self._default_inputs.items():
            setattr(self, key, input.get(key, value) if input else value)
        for key, value in input.items():
            if key not in self._default_inputs:
                setattr(self, key, value)
        for key, value in self._default_outputs.items():
            setattr(self, key, output.get(key, value) if output else value)
        for key, value in output.items():
            if key not in self._default_outputs:
                setattr(self, key, value)

        self.scopes = scopes

    def producers(self, name: str) -> Producer | ProducerGroup:
        return self._produce_quantities(name)

    def _produce_get(
        self,
        name: str,
        input_variable: Quantity,
        output_variable: Quantity,
        index: int,
        dtype: str = "float",
    ):
        call = f"""
        event::quantity::Get<{dtype}>(
            {{df}},
            {{output}},
            {{input}},
            {index}
        )
        """
        return Producer(
            name=name,
            call=call,
            input=[input_variable, self.dibjetpair],
            output=[output_variable],
            scopes=self.scopes,
        )

    def _produce_quantities(self, name: str):
        # List of producers that constitute the producer group
        producers = []

        # Create producers for the four-momentum of each jet in the pair
        for index in [0, 1]:
            # Construct the function call
            call = f"""
            lorentzvector::Build({{df}}, {{output}}, {{input}}, {index})
            """

            # Append the producer to the list
            producers.append(
                Producer(
                    name=f"{name}_bpair_p4_{index + 1}",
                    call=call,
                    input=[
                        self.jet_pt,
                        self.jet_eta,
                        self.jet_phi,
                        self.jet_mass,
                        self.dibjetpair,
                    ],
                    output=[getattr(self, f"bpair_p4_{index + 1}")],
                    scopes=self.scopes,
                )
            )

        # Create producers for each observable and each jet in the pair
        for variable, index in product(["pt", "eta", "phi", "mass", "btag_value"], [0, 1]):
            # Get input and output variables
            input_variable = getattr(self, f"jet_{variable}")
            output_variable = getattr(self, f"bpair_{variable}_{index + 1}")

            # Append the producer to the list
            producers.append(
                self._produce_get(
                    name=f"{name}_bpair_{variable}_{index + 1}",
                    input_variable=input_variable,
                    output_variable=output_variable,
                    index=index,
                )
            )

        # Add jet pt resolution from the regression
        base_variable = "bpair_pt_resolution_regressed"
        for index in [0, 1]:
            variable = f"{base_variable}_{index + 1}"
            if hasattr(self, variable):
                # Get input and output variables
                input_variable = getattr(self, "jet_pt_resolution_regressed")
                output_variable = getattr(self, variable)

                producers.append(
                    self._produce_get(
                        name=f"{name}_{variable}",
                        input_variable=input_variable,
                        output_variable=output_variable,
                        index=index,
                    )
                )

        # Merge producers into a producer group
        producer_group = ProducerGroup(
            name=name,
            call=None,
            input=None,
            output=None,
            scopes=self.scopes,
            subproducers=producers,
        )

        return producer_group


BQuantities = BQuantitiesMetaConfiguration(
    input={
        "jet_pt": q.Jet_correctedPt,
        "jet_mass": q.Jet_correctedMass,
        "dibjetpair": q.dibjetpair,
    },
    output={
        "bpair_p4_1": q.bpair_p4_1,
        "bpair_p4_2": q.bpair_p4_2,
        "bpair_pt_1": q.bpair_pt_1,
        "bpair_pt_2": q.bpair_pt_2,
        "bpair_eta_1": q.bpair_eta_1,
        "bpair_eta_2": q.bpair_eta_2,
        "bpair_phi_1": q.bpair_phi_1,
        "bpair_phi_2": q.bpair_phi_2,
        "bpair_mass_1": q.bpair_mass_1,
        "bpair_mass_2": q.bpair_mass_2,
        "bpair_btag_value_1": q.bpair_btag_value_1,
        "bpair_btag_value_2": q.bpair_btag_value_2,
    },
    scopes=SCOPES,
).producers("BQuantities")


BQuantitiesRegressed = BQuantitiesMetaConfiguration(
    input={
        "jet_pt": q.Jet_correctedPtRegressed,
        "jet_mass": q.Jet_correctedMassRegressed,
        "jet_pt_resolution_regressed": q.Jet_rawPtRegressedResolution,
        "dibjetpair": q.dibjetpair_regressed,
    },
    output={
        "bpair_p4_1": q.bpair_p4_regressed_1,
        "bpair_p4_2": q.bpair_p4_regressed_2,
        "bpair_pt_1": q.bpair_pt_regressed_1,
        "bpair_pt_2": q.bpair_pt_regressed_2,
        "bpair_eta_1": q.bpair_eta_regressed_1,
        "bpair_eta_2": q.bpair_eta_regressed_2,
        "bpair_phi_1": q.bpair_phi_regressed_1,
        "bpair_phi_2": q.bpair_phi_regressed_2,
        "bpair_mass_1": q.bpair_mass_regressed_1,
        "bpair_mass_2": q.bpair_mass_regressed_2,
        "bpair_btag_value_1": q.bpair_btag_value_regressed_1,
        "bpair_btag_value_2": q.bpair_btag_value_regressed_2,
        "bpair_pt_resolution_regressed_1": q.bpair_pt_resolution_regressed_1,
        "bpair_pt_resolution_regressed_2": q.bpair_pt_resolution_regressed_2,
    },
    scopes=SCOPES,
).producers("BQuantitiesRegressed")


# ------------------------------------------------------------------------------
# Combined pair quantities of the selected bb candidate 
# ------------------------------------------------------------------------------


class BBPairQuantitiesMetaConfiguration():

    _default_inputs = {
        "bpair_p4_1": q.bpair_p4_1,
        "bpair_p4_2": q.bpair_p4_2,
    }

    _default_outputs = {
        "bpair_p4": q.bpair_p4,
        "bpair_pt": q.bpair_pt_dijet,
        "bpair_eta": q.bpair_eta,
        "bpair_phi": q.bpair_phi,
        "bpair_mass": q.bpair_m_inv,
        "bpair_delta_r": q.bpair_deltaR,
    }

    def __init__(
        self,
        input=None,
        output=None,
        scopes=None,
    ):

        for key, value in self._default_inputs.items():
            setattr(self, key, input.get(key, value) if input else value)
        for key, value in self._default_outputs.items():
            setattr(self, key, output.get(key, value) if output else value)

        self.scopes = scopes

    def producers(self, name: str) -> Producer | ProducerGroup:
        return self._produce_quantities(name)

    def _produce_quantities(self, name: str):
        # List of producers that constitute the producer group
        producers = []

        # Sum the four-momenta of the two jets to get the four-momentum of the b-jet pair
        producers.append(
            Producer(
                name=f"{name}_p4_bpair",
                call="lorentzvector::Sum({df}, {output}, {input})",
                input=[self.bpair_p4_1, self.bpair_p4_2],
                output=[self.bpair_p4],
                scopes=self.scopes,
            )
        )

        # Get four-vector properties of the b-jet pair
        for variable in ["pt", "eta", "phi", "mass"]:
            # Construct the function call
            call = f"""
            lorentzvector::Get{variable.capitalize()}({{df}}, {{output}}, {{input}})
            """

            # Append the producer to the list
            producers.append(
                Producer(
                    name=f"{name}_bpair_{variable}",
                    call=call,
                    input=[self.bpair_p4],
                    output=[getattr(self, f"bpair_{variable}")],
                    scopes=self.scopes,
                )
            )

        # Calculate the deltaR between the two jets in the pair
        producers.append(
            Producer(
                name=f"{name}_bpair_deltaR",
                call="quantities::DeltaR({df}, {output}, {input})",
                input=[self.bpair_p4_1, self.bpair_p4_2],
                output=[self.bpair_delta_r],
                scopes=self.scopes,
            )
        )

        # Merge producers into a producer group
        producer_group = ProducerGroup(
            name=name,
            call=None,
            input=None,
            output=None,
            scopes=self.scopes,
            subproducers=producers,
        )

        return producer_group


BBPairQuantities = BBPairQuantitiesMetaConfiguration(
    input={
        "bpair_p4_1": q.bpair_p4_1,
        "bpair_p4_2": q.bpair_p4_2,
        "bpair_pt_1": q.bpair_pt_1,
        "bpair_pt_2": q.bpair_pt_2,
        "bpair_eta_1": q.bpair_eta_1,
        "bpair_eta_2": q.bpair_eta_2,
        "bpair_phi_1": q.bpair_phi_1,
        "bpair_phi_2": q.bpair_phi_2,
        "bpair_mass_1": q.bpair_mass_1,
        "bpair_mass_2": q.bpair_mass_2,
    },
    output={
        "bpair_p4": q.bpair_p4,
        "bpair_pt": q.bpair_pt_dijet,
        "bpair_eta": q.bpair_eta,
        "bpair_phi": q.bpair_phi,
        "bpair_mass": q.bpair_m_inv,
        "bpair_delta_r": q.bpair_deltaR,
    },
    scopes=SCOPES,
).producers("BBPairQuantities")


BBPairQuantitiesRegressed = BBPairQuantitiesMetaConfiguration(
    input={
        "bpair_p4_1": q.bpair_p4_regressed_1,
        "bpair_p4_2": q.bpair_p4_regressed_2,
        "bpair_pt_1": q.bpair_pt_regressed_1,
        "bpair_pt_2": q.bpair_pt_regressed_2,
        "bpair_eta_1": q.bpair_eta_regressed_1,
        "bpair_eta_2": q.bpair_eta_regressed_2,
        "bpair_phi_1": q.bpair_phi_regressed_1,
        "bpair_phi_2": q.bpair_phi_regressed_2,
        "bpair_mass_1": q.bpair_mass_regressed_1,
        "bpair_mass_2": q.bpair_mass_regressed_2,
    },
    output={
        "bpair_p4": q.bpair_p4_regressed,
        "bpair_pt": q.bpair_pt_dijet_regressed,
        "bpair_eta": q.bpair_eta_regressed,
        "bpair_phi": q.bpair_phi_regressed,
        "bpair_mass": q.bpair_m_inv_regressed,
        "bpair_delta_r": q.bpair_deltaR_regressed,
    },
    scopes=SCOPES,
).producers("BBPairQuantitiesRegressed")


# Combine all bb pair producers into a single producer group for convenience
AllBBPairProducers = ProducerGroup(
    name="AllBBPairProducers",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        BBPairSelection,
        BBPairSelectionRegressed,
        BQuantities,
        BQuantitiesRegressed,
        BBPairQuantities,
        BBPairQuantitiesRegressed,
    ]
)