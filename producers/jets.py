"""
Producers for AK4 jet energy scale and resolution corrections, object selections, overlap vetoes, and quantities to be stored.
"""

from ..quantities import output as q
from ..quantities import nanoAOD
from analysis_configurations.quantities import nanoAODv9_run2, nanoAODv12_run3
from code_generation.producer import Producer, ProducerGroup
from code_generation.quantity import Quantity

from ..helpers import era_producer_groups
from ..constants import GLOBAL_SCOPES, SCOPES, ERAS_RUN2


# ------------------------------------------------------------------------------
# Auxiliary quantities for the `Jet` collection
# ------------------------------------------------------------------------------

#region

# Jet ID
# - For run 2, the jet ID can just be taken from the corresponding column in
#   nanoAOD.
# - For 2022 and 2023, the jet ID in nanoAOD v12 has a bug which must be
#   adressed.
# - For 2024, no jet ID column exists in nanoAOD v15 must be calculated using
#   a dedicated correction file.
JetID = {
    tuple(ERAS_RUN2): Producer(
        name="JetID",
        call="""
        event::quantity::Rename<ROOT::RVec<int>>(
            {df},
            {output},
            {input}
        )
        """,
        input=[nanoAODv9_run2.Jet_jetId],
        output=[q.Jet_ID],
        scopes=GLOBAL_SCOPES,
    ),
    ("2022preEE", "2022postEE", "2023preBPix", "2023postBPix"): Producer(
        name="JetID",
        call="""
        physicsobject::jet::quantities::CorrectJetIDRun3NanoV12(
            {df},
            {output},
            {input}
        )
        """,
        input=[
            nanoAOD.Jet_pt,
            nanoAOD.Jet_eta,
            nanoAODv12_run3.Jet_jetId,
            nanoAOD.Jet_neHEF,
            nanoAOD.Jet_neEmEF,
            nanoAOD.Jet_muEF,
            nanoAOD.Jet_chEmEF,
        ],
        output=[q.Jet_ID],
        scopes=GLOBAL_SCOPES,
    ),
    ("2024", "2025"): Producer(
        name="JetID",
        call="""
        physicsobject::jet::quantity::ID(
            {df},
            correctionManager,
            {output},
            {input},
            "{ak4jet_id_file}",
            "{ak4jet_id_name}"
        )
        """,
        input=[
            nanoAOD.Jet_eta,
            nanoAOD.Jet_chHEF,
            nanoAOD.Jet_neHEF,
            nanoAOD.Jet_chEmEF,
            nanoAOD.Jet_neEmEF,
            nanoAOD.Jet_muEF,
            nanoAOD.Jet_chMultiplicity,
            nanoAOD.Jet_neMultiplicity,
        ],
        output=[q.Jet_ID],
        scopes=GLOBAL_SCOPES,
    ),
}

# Value of the b jet tagger
# - For 2022 and 2023, PNet is used
# - For Run 2 and from 2024 on, UParT regression is used
# The b jet tagger column is defined in the configuration
JetBTagValue = Producer(
    name="JetBTagValue",
    call="""
    event::quantity::Rename<ROOT::RVec<float>>(
        {df},
        {output},
        \"{bjet_score_column}\"
    )
    """,
    input=[],
    output=[q.Jet_bTagValue],
    scopes=GLOBAL_SCOPES,
)

# Flag for jet passing the b jet tagging requirement
JetIsBTagged = Producer(
    name="JetIsBTagged",
    call="""
    physicsobject::jet::quantities::IsBTagged(
        {df},
        correctionManager,
        {output},
        {input},
        "{bjet_sf_file}",
        "{bjet_sf_wp_name}",
        "{bjet_btag_wp_name}"
    )
    """,
    input=[q.Jet_bTagValue],
    output=[q.Jet_isBTagged],
    scopes=GLOBAL_SCOPES,
)

# Absolute raw jet pt before JES corrections
JetRawPt = Producer(
    name="JetRawPt",
    call="physicsobject::jet::jec::Raw({df}, {output}, {input})",
    input=[nanoAOD.Jet_pt, nanoAOD.Jet_rawFactor],
    output=[q.Jet_rawPt],
    scopes=GLOBAL_SCOPES,
)

# Absolute raw jet mass before JES corrections
JetRawMass = Producer(
    name="JetRawMass",
    call="physicsobject::jet::jec::Raw({df}, {output}, {input})",
    input=[nanoAOD.Jet_mass, nanoAOD.Jet_rawFactor],
    output=[q.Jet_rawMass],
    scopes=GLOBAL_SCOPES,
)

# Calculate raw and muon-subtracted jet pt
JetRawMuonSubtrPt = Producer(
    name="JetRawMuonSubtrPt",
    call="physicsobject::jet::jec::RawMuonSubtr({df}, {output}, {input})",
    input=[
        nanoAOD.Jet_pt,
        nanoAOD.Jet_rawFactor,
        nanoAOD.Jet_muonSubtrFactor,
    ],
    output=[q.Jet_rawMuonSubtrPt],
    scopes=GLOBAL_SCOPES,
)

# Sum the charged and neutral electromagnetic energy fractions
JetEmEf = Producer(
    name="JetEmEf",
    call="event::quantity::SumVectors<float>({df}, {output}, {input})",
    input=[
        nanoAOD.Jet_chEmEF,
        nanoAOD.Jet_neEmEF,
    ],
    output=[q.Jet_EmEF],
    scopes=GLOBAL_SCOPES,
)

# Jet pt correction factor for PNet/UParT-based regression
# - For 2022 and 2023, the PNet regression is used
# - For Run 2 and from 2024 on, the UParT regression is used
JetRegPtRawCorr = {
    ("2022preEE", "2022postEE", "2023preBPix", "2023postBPix"): Producer(
        name="JetRegPtRawCorr",
        call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
        input=[nanoAOD.Jet_PNetRegPtRawCorr],
        output=[q.Jet_regPtRawCorr],
        scopes=GLOBAL_SCOPES,
    ),
    tuple(ERAS_RUN2) + ("2024", "2025"): Producer(
        name="JetRegPtRawCorr",
        call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
        input=[nanoAOD.Jet_UParTAK4RegPtRawCorr],
        output=[q.Jet_regPtRawCorr],
        scopes=GLOBAL_SCOPES,
    ),
}

# Jet pt correction factor for PNet/UParT-based regression, including neutrinos
# - For 2022 and 2023, the PNet regression is used
# - For Run 2 and from 2024 on, the UParT regression is used
JetRegPtRawCorrNeutrino = {
    ("2022preEE", "2022postEE", "2023preBPix", "2023postBPix"): Producer(
        name="JetRegPtRawCorrNeutrino",
        call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
        input=[nanoAOD.Jet_PNetRegPtRawCorrNeutrino],
        output=[q.Jet_regPtRawCorrNeutrino],
        scopes=GLOBAL_SCOPES,
    ),
    tuple(ERAS_RUN2) + ("2024", "2025"): Producer(
        name="JetRegPtRawCorrNeutrino",
        call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
        input=[nanoAOD.Jet_UParTAK4RegPtRawCorrNeutrino],
        output=[q.Jet_regPtRawCorrNeutrino],
        scopes=GLOBAL_SCOPES,
    ),
}

# Common column for pt regression resolution
# - For 2022 and 2023, the PNet regression is used
# - For Run 2 and from 2024 on, the UParT regression is used
JetRegPtRawRes = {
    ("2022preEE", "2022postEE", "2023preBPix", "2023postBPix"): Producer(
        name="JetRegPtRawRes",
        call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
        input=[nanoAOD.Jet_PNetRegPtRawRes],
        output=[q.Jet_regPtRawRes],
        scopes=GLOBAL_SCOPES,
    ),
    tuple(ERAS_RUN2) + ("2024", "2025"): Producer(
        name="JetRegPtRawRes",
        call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
        input=[nanoAOD.Jet_UParTAK4RegPtRawRes],
        output=[q.Jet_regPtRawRes],
        scopes=GLOBAL_SCOPES,
    ),
}

# Producer for absolute raw pt after PNet/UParT regression
JetRawPtRegressed = Producer(
    name="JetRawPtRegressed",
    call="physicsobject::jet::jec::Regressed({df}, {output}, {input}, \"{ak4jet_reg_algo}\")",
    input=[
        q.Jet_rawPt,
        q.Jet_regPtRawCorr,
        q.Jet_regPtRawCorrNeutrino,
        q.Jet_isBTagged,
    ],
    output=[q.Jet_rawPtRegressed],
    scopes=GLOBAL_SCOPES,
)

# Producer for absolute mass after PNet/UParT regression
JetRawMassRegressed = Producer(
    name="JetRawMassRegressed",
    call="physicsobject::jet::jec::Regressed({df}, {output}, {input}, \"{ak4jet_reg_algo}\")",
    input=[
        q.Jet_rawMass,
        q.Jet_regPtRawCorr,
        q.Jet_regPtRawCorrNeutrino,
        q.Jet_isBTagged,
    ],
    output=[q.Jet_rawMassRegressed],
    scopes=GLOBAL_SCOPES,
)

# Producer for absolute pt resolution of PNet/UParT regression
JetRawPtRegressedResolution = Producer(
    name="JetRawPtRegressedResolution",
    call="physicsobject::jet::jec::RegResolution({df}, {output}, {input})",
    input=[
        q.Jet_rawPt,
        q.Jet_regPtRawRes,
    ],
    output=[q.Jet_rawPtRegressedResolution],
    scopes=GLOBAL_SCOPES,
)

# Group of auxiliary `Jet` collection quantities
AuxJetCollectionQuantities = era_producer_groups(
    "AuxJetCollectionQuantities",
    [
        JetID,
        JetBTagValue,
        JetIsBTagged,
        JetRawPt,
        JetRawMass,
        JetRawMuonSubtrPt,
        JetEmEf,
        JetRegPtRawCorr,
        JetRegPtRawCorrNeutrino,
        JetRegPtRawRes,
        JetRawPtRegressed,
        JetRawMassRegressed,
        JetRawPtRegressedResolution,
    ],
    GLOBAL_SCOPES,
)

#endregion

# ------------------------------------------------------------------------------
# Auxiliary quantities for the `CorrT1METJet` collection
# ------------------------------------------------------------------------------

#region

# Dummy value or renaming of the EmEF column of CorrT1METJet collection
# - For eras up to 2023, the EmEF column of the CorrT1METJet collection does not
#   exist. Dummy values of 0 are added, causing that all CorrT1METJet objects
#   are passing the EmEF < 0.9 criterion.
# - For 2024, just rename the column.
CorrT1METJetEmEF = {
    tuple(ERAS_RUN2) + (
        "2022preEE",
        "2022postEE",
        "2023preBPix",
        "2023postBPix",
    ): Producer(
        name="CorrT1METJetEmEF",
        call="""
        event::quantity::Define<float>({df}, {output}, {input}, 0.0)
        """,
        input=[nanoAOD.nCorrT1METJet],
        output=[q.CorrT1METJet_EmEnergyFraction],
        scopes=GLOBAL_SCOPES,
    ),
    ("2024", "2025"): Producer(
        name="CorrT1METJetEmEF",
        call="""
        event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})
        """,
        input=[nanoAOD.CorrT1METJet_EmEF],
        output=[q.CorrT1METJet_EmEnergyFraction],
        scopes=GLOBAL_SCOPES,
    ),
}

# Calculate the muon-subtracted raw jet pt
# Here, 'Raw' is used because the maths stays the same as for the calculation of
# the raw jet pt from the nanoAOD jet pt:
# pt_muon_subtr = pt_raw * (1 - muon_subtr_factor)
CorrT1METJetRawMuonSubtrPt = Producer(
    name="CorrT1METJetRawMuonSubtr",
    call="physicsobject::jet::jec::Raw({df}, {output}, {input})",
    input=[
        nanoAOD.CorrT1METJet_rawPt,
        nanoAOD.CorrT1METJet_muonSubtrFactor,
    ],
    output=[q.CorrT1METJet_rawMuonSubtrPt],
    scopes=GLOBAL_SCOPES,
)

# Create a dummy jet ID column for this collection
# The jet ID is set to 2, meaning that all CorrT1METJet jets are set to pass the
# tight jet ID working point.
CorrT1METJetID = Producer(
    name="CorrT1METJetID",
    call="event::quantity::Define<int>({df}, {output}, {input}, 2)",
    input=[nanoAOD.nCorrT1METJet],
    output=[q.CorrT1METJet_ID],
    scopes=GLOBAL_SCOPES,
)

# Group of auxiliary `CorrT1METJet` collection quantities
AuxCorrT1METJetCollectionQuantities = era_producer_groups(
    "AuxCorr1T1METJetCollectionQuantities",
    [
        CorrT1METJetRawMuonSubtrPt,
        CorrT1METJetID,
        CorrT1METJetEmEF,
    ],
    GLOBAL_SCOPES,
)

#endregion

# ------------------------------------------------------------------------------
# `Type1Jet` collection and their energy corrections
# ------------------------------------------------------------------------------

#region

def _concatenate(
    jet_input_variable: Quantity,
    corrjet_input_variable: Quantity,
    output_variable: Quantity,
    dtype: str = "float",
    scopes: str = None,
):
    """
    Helper function for `Concatenate` producers for the `Type1Jet`
    collection.
    """

    return Producer(
        name=f"Concatenate{output_variable.name}",
        call=f"""
        event::quantity::Concatenate<{dtype}>(
            {{df}},
            {{output}},
            {{input}}
        )
        """,
        input=[jet_input_variable, corrjet_input_variable],
        output=[output_variable],
        scopes=scopes,
    )

# Concatenate producers for the `Type1Jet` collection
Type1JetCollection = ProducerGroup(
    name="Type1JetCollection",
    call=None,
    input=None,
    output=None,
    scopes=GLOBAL_SCOPES,
    subproducers=[
        _concatenate(
            jet_input_variable,
            corrjet_input_variable,
            output_column,
            data_type,
            scopes=GLOBAL_SCOPES,
        )
        for (
            (jet_input_variable, corrjet_input_variable),
            output_column,
            data_type,
        ) in [
            (
                (q.Jet_rawMuonSubtrPt, q.CorrT1METJet_rawMuonSubtrPt),
                q.Type1Jet_rawMuonSubtrPt,
                "float",
            ),
            (
                (nanoAOD.Jet_eta, nanoAOD.CorrT1METJet_eta),
                q.Type1Jet_eta,
                "float",
            ),
            (
                (nanoAOD.Jet_phi, nanoAOD.CorrT1METJet_phi),
                q.Type1Jet_phi,
                "float",
            ),
            (
                (nanoAOD.Jet_area, nanoAOD.CorrT1METJet_area),
                q.Type1Jet_area,
                "float",
            ),
            (
                (q.Jet_ID, q.CorrT1METJet_ID),
                q.Type1Jet_ID,
                "int",
            ),
            (
                (q.Jet_EmEF, q.CorrT1METJet_EmEnergyFraction),
                q.Type1Jet_EmEF,
                "float",
            ),
        ]
    ],
)

#endregion

# ------------------------------------------------------------------------------
# Jet energy scale and resolution corrections
# ------------------------------------------------------------------------------

#region

class StepwiseJERCProducerMetaConfiguration():

    _default_inputs = {
        "jet_raw_pt": q.Jet_rawPt,
        "jet_eta": nanoAOD.Jet_eta,
        "jet_phi": nanoAOD.Jet_phi,
        "jet_raw_mass": q.Jet_rawMass,
        "jet_area": nanoAOD.Jet_area,
        "jet_id": q.Jet_ID,
        "jet_seed": q.jet_seed,
        "genjet_pt": nanoAOD.GenJet_pt,
        "genjet_eta": nanoAOD.GenJet_eta,
        "genjet_phi": nanoAOD.GenJet_phi,
        "rho": nanoAOD.Rho_fixedGridRhoFastjetAll,
        "run": nanoAOD.run,
    }

    _default_outputs = {
        "jet_jec_result": q.Jet_jecResult,
        "jet_l1_pt": q.Jet_l1Pt,
        "jet_l2rel_pt": q.Jet_l2relPt,
        "jet_l2l3res_pt": q.Jet_l2l3resPt,
        "jet_corrected_pt": q.Jet_correctedPt,
        "jet_corrected_mass": q.Jet_correctedMass,
    }

    def __init__(
        self,
        input=None,
        output=None,
        scopes=None,
        config_parameter_prefix="ak4jet",
    ):

        for key, value in self._default_inputs.items():
            setattr(self, key, input.get(key, value) if input else value)
        for key, value in (input or {}).items():
            if key not in self._default_inputs:
                setattr(self, key, value)
        for key, value in self._default_outputs.items():
            setattr(self, key, output.get(key, value) if output else value)
        for key, value in (output or {}).items():
            if key not in self._default_outputs:
                setattr(self, key, value)

        self.scopes = scopes
        self.config_parameter_prefix = config_parameter_prefix

    def producers(self, name: str, data=False, mass=True):
        # Construct list of producers for the group
        producers = []

        # Pick the data or the MC JEC producer depending on the `data` flag
        if data:
            producers.append(
                self._produce_jet_pt_correction_data(name + "Pt")
            )
        else:
            producers.append(
                self._produce_jet_pt_correction_mc(name + "Pt")
            )

        # Optionally add the mass correction
        if mass:
            producers.append(
                self._produce_jet_mass_correction(name + "Mass"),
            )

        return ProducerGroup(
            name=name,
            call=None,
            input=None,
            output=None,
            scopes=self.scopes,
            subproducers=producers,
        )

    def _produce_jet_pt_correction_data(self, name: str):
        """Jet pt correction for data."""

        # Construct the function call
        call = f"""
            physicsobject::jet::jec::PtCorrectionData(
                {{df}},
                correctionManager,
                {{output}},
                {{input}},
                "{{{self.config_parameter_prefix}_jec_file}}",
                "{{{self.config_parameter_prefix}_jec_algo}}",
                "{{{self.config_parameter_prefix}_jes_tag_data}}",
                {{{self.config_parameter_prefix}_reapply_jes}},
                "{{era}}"
            )
            """

        return Producer(
            name=name,
            call=call,
            input=[
                self.jet_raw_pt,
                self.jet_eta,
                self.jet_phi,
                self.jet_area,
                self.rho,
                self.run,
            ],
            output=[
                self.jet_jec_result,
                self.jet_l1_pt,
                self.jet_l2rel_pt,
                self.jet_l2l3res_pt,
                self.jet_corrected_pt,
            ],
            scopes=self.scopes,
        )

    def _produce_jet_pt_correction_mc(self, name: str):
        """Jet pt correction for simulation."""

        # Construct the function call
        call=f"""
        physicsobject::jet::jec::PtCorrectionMC(
            {{df}},
            correctionManager,
            {{output}},
            {{input}},
            "{{{self.config_parameter_prefix}_jec_file}}",
            "{{{self.config_parameter_prefix}_jec_algo}}",
            "{{{self.config_parameter_prefix}_jes_tag_mc}}",
            "{{{self.config_parameter_prefix}_jer_tag}}",
            {{{self.config_parameter_prefix}_jes_sources}},
            {{{self.config_parameter_prefix}_jes_shift_factor}},
            "{{{self.config_parameter_prefix}_jer_shift}}",
            {{{self.config_parameter_prefix}_reapply_jes}},
            "{{era}}"
        )
        """

        return Producer(
            name=name,
            call=call,
            input=[
                self.jet_raw_pt,
                self.jet_eta,
                self.jet_phi,
                self.jet_area,
                self.jet_id,
                self.genjet_pt,
                self.genjet_eta,
                self.genjet_phi,
                self.rho,
                self.jet_seed,
            ],
            output=[
                self.jet_jec_result,
                self.jet_l1_pt,
                self.jet_l2rel_pt,
                self.jet_l2l3res_pt,
                self.jet_corrected_pt,
            ],
            scopes=self.scopes,
        )

    def _produce_jet_mass_correction(self, name: str):
        # Construct the function call
        call = """
        physicsobject::jet::jec::MassCorrectionFromPt(
            {df},
            {output},
            {input}
        )
        """

        return Producer(
            name=name,
            call=call,
            input=[
                self.jet_raw_mass,
                self.jet_raw_pt,
                self.jet_corrected_pt,
            ],
            output=[self.jet_corrected_mass],
            scopes=GLOBAL_SCOPES,
        )


# Version tag of the pinned 2018-v15 tight jet ID formula recomputed by
# JetIDTight2018PuppiV15 below. Must equal both:
#  - the header constant `xyh::object_selection::formula_version`
#    (cpp_addons/include/jetid_v15.hxx), and
#  - the "formula_version" field of
#    tests/fixtures/jetid_2018UL_puppi_tight_v1.json.
# common_config.py's blocking gate compares this constant against the
# fixture before allowing any SM (use_2018_v15_jet_path) entry point to
# build.
JETID_V15_FORMULA_VERSION = "jetid_2018UL_puppi_tight_v1"

# Reconstructed 2018 UL AK4 PUPPI tight jet ID (v15).
#
# NanoAOD v15 drops the precomputed Jet_jetId branch that NanoAODv9 shipped
# and its v15 `Jet` collection is AK4 PUPPI (not AK4 CHS), so for 2018 this
# producer recomputes the tight working point event-by-event from the v15
# composition branches instead of reading (or patching) a jetId bitmask --
# see docs/jetid_2018UL_puppi_v15.md for the pinned formula, its region
# structure, and sources, and tests/fixtures/jetid_2018UL_puppi_tight_v1.json
# for the machine-readable boundary fixture validated by
# tests/cpp/test_jetid_v15.cxx.
#
# Inputs are the nine v15 composition quantities, in the same order as the
# C++ signature `xyh::object_selection::tight_jet_id_2018_puppi_v15`. Note
# that `Jet_muEF` and `Jet_chEmEF` are read but unused by the *tight*
# (non-lepton-veto) formula computed here -- they (and `Jet_neMultiplicity`)
# are kept as inputs only so a future tightLepVeto/forward-region extension
# of this producer does not need to touch the Python call site.
#
# Selecting this producer for era 2018 (replacing the `JetID` dict above) is
# Task 8; this producer only needs to exist and be gated (see
# common_config.py) for now.
JetIDTight2018PuppiV15 = Producer(
    name="JetIDTight2018PuppiV15",
    call="xyh::object_selection::tight_jet_id_2018_puppi_v15({df}, {output}, {input})",
    input=[
        nanoAOD.Jet_eta,
        nanoAOD.Jet_neHEF,
        nanoAOD.Jet_neEmEF,
        nanoAOD.Jet_nConstituents,
        nanoAOD.Jet_chHEF,
        nanoAOD.Jet_muEF,
        nanoAOD.Jet_chEmEF,
        nanoAOD.Jet_chMultiplicity,
        nanoAOD.Jet_neMultiplicity,
    ],
    output=[q.Jet_ID],
    scopes=GLOBAL_SCOPES,
)

# Seed for the random number generator for jet energy resolution smearing
JERSmearingSeed = Producer(
    name="JERSmearingSeed",
    call="""
    event::quantity::GenerateSeed(
        {df},
        {output},
        {input},
        {ak4jet_jer_master_seed}
    )
    """,
    input=[nanoAOD.luminosityBlock, nanoAOD.run, nanoAOD.event],
    output=[q.jet_seed],
    scopes=GLOBAL_SCOPES,
)

# Configuration template for the jet pt and mass correction
JetEnergyCorrectionTemplate = StepwiseJERCProducerMetaConfiguration(
    scopes=GLOBAL_SCOPES,
)

# Jet pt and mass correction for AK4 jets in simulation
JetEnergyCorrectionMC = JetEnergyCorrectionTemplate.producers(
    "JetEnergyCorrectionMC",
    data=False,
)

# Jet pt and mass correction for AK4 jets in data
JetEnergyCorrectionData = JetEnergyCorrectionTemplate.producers(
    "JetEnergyCorrectionData",
    data=True,
)

# Configuration template for jet pt and mass correction after regression
JetEnergyCorrectionRegressedTemplate = StepwiseJERCProducerMetaConfiguration(
    input={
        "jet_raw_pt": q.Jet_rawPtRegressed,
        "jet_raw_mass": q.Jet_rawMassRegressed,
    },
    output={
        "jet_jec_result": q.Jet_jecResultRegressed,
        "jet_l1_pt": q.Jet_l1PtRegressed,
        "jet_l2rel_pt": q.Jet_l2relPtRegressed,
        "jet_l2l3res_pt": q.Jet_l2l3resPtRegressed,
        "jet_corrected_pt": q.Jet_correctedPtRegressed,
        "jet_corrected_mass": q.Jet_correctedMassRegressed,
    },
    scopes=GLOBAL_SCOPES,
)

# Jet pt and mass correction for AK4 jets after PNet/UParT regression in
# simulation
JetEnergyCorrectionMCRegressed = JetEnergyCorrectionRegressedTemplate.producers("JetEnergyCorrectionMCRegressed", data=False)

# Jet pt and mass correction for AK4 jets after PNet/UParT regression in
# simulation
JetEnergyCorrectionDataRegressed = JetEnergyCorrectionRegressedTemplate.producers("JetEnergyCorrectionDataRegressed", data=True)

# Configuration template for type1 jet pt correction
Type1JetEnergyCorrectionTemplate = StepwiseJERCProducerMetaConfiguration(
    input={
        "jet_raw_pt": q.Type1Jet_rawMuonSubtrPt,
        "jet_eta": q.Type1Jet_eta,
        "jet_phi": q.Type1Jet_phi,
        "jet_area": q.Type1Jet_area,
        "jet_id": q.Type1Jet_ID,
        "jet_seed": q.jet_seed,
        "genjet_pt": nanoAOD.GenJet_pt,
        "genjet_eta": nanoAOD.GenJet_eta,
        "genjet_phi": nanoAOD.GenJet_phi,
        "rho": nanoAOD.Rho_fixedGridRhoFastjetAll,
        "run": nanoAOD.run,
    },
    output={
        "jet_jec_result": q.Type1Jet_jecResult,
        "jet_l1_pt": q.Type1Jet_l1Pt,
        "jet_l2rel_pt": q.Type1Jet_l2relPt,
        "jet_l2l3res_pt": q.Type1Jet_l2l3resPt,
        "jet_corrected_pt": q.Type1Jet_correctedPt,
    },
    scopes=GLOBAL_SCOPES,
)

# Type1 jet pt and mass correction for AK4 jets in simulation
Type1JetEnergyCorrectionMC = Type1JetEnergyCorrectionTemplate.producers(
    "Type1JetEnergyCorrectionMC",
    data=False,
    mass=False,
)

# Type1 jet pt and mass correction for AK4 jets in data
Type1JetEnergyCorrectionData = Type1JetEnergyCorrectionTemplate.producers(
    "Type1JetEnergyCorrectionData",
    data=True,
    mass=False,
)

#endregion

#
# AK4 JET SELECTION
#

# Jet selection for run 2 (CHS jets)
GoodJetsWithPUID = Producer(
    name="GoodJetsWithPUID",
    call="xyh::object_selection::jet({df}, {output}, {input}, {ak4jet_min_pt}, {ak4jet_max_abs_eta}, {ak4jet_id_wp}, {ak4jet_apply_jet_horn_veto}, {ak4jet_puid_wp}, {ak4jet_puid_max_pt})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        q.Jet_ID,
        nanoAODv9_run2.Jet_puId,
    ],
    output=[q.good_jets_mask],
    scopes=GLOBAL_SCOPES,
)

# Jet selection for run 3 (PUPPI jets)
GoodJetsWithoutPUID = Producer(
    name="GoodJetsWithoutPUID",
    call="xyh::object_selection::jet({df}, {output}, {input}, {ak4jet_min_pt}, {ak4jet_max_abs_eta}, {ak4jet_id_wp}, {ak4jet_apply_jet_horn_veto})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        q.Jet_ID,
    ],
    output=[q.good_jets_mask],
    scopes=GLOBAL_SCOPES,
)

# Kinematic b jet selection for run 2 (CHS jets)
GoodBJetsBaseWithPUID = Producer(
    name="GoodBJetsBaseWithPUID",
    call="xyh::object_selection::jet({df}, {output}, {input}, {bjet_min_pt}, {bjet_max_abs_eta}, {ak4jet_id_wp}, {ak4jet_apply_jet_horn_veto}, {ak4jet_puid_wp}, {ak4jet_puid_max_pt})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        q.Jet_ID,
        nanoAODv9_run2.Jet_puId,
    ],
    output=[q.base_bjets_mask],
    scopes=GLOBAL_SCOPES,
)

# Kinematic b jet selection for run 3 (PUPPI jets)
GoodBJetsBaseWithoutPUID = Producer(
    name="GoodBJetsBaseWithoutPUID",
    call="xyh::object_selection::jet({df}, {output}, {input}, {bjet_min_pt}, {bjet_max_abs_eta}, {ak4jet_id_wp}, {ak4jet_apply_jet_horn_veto})",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        q.Jet_ID,
    ],
    output=[q.base_bjets_mask],
    scopes=GLOBAL_SCOPES,
)

# Full b jet selection for run 2, including the b tagging requirement (CHS jets)
GoodBJetsWithPUID = ProducerGroup(
    name="GoodBJetsWithPUID",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[q.Jet_isBTagged],
    output=[q.good_bjets_mask],
    subproducers=[
        GoodBJetsBaseWithPUID,
    ],
    scopes=GLOBAL_SCOPES,
)

# Full b jet selection for run 3, including the b tagging requirement (PUPPI jets)
GoodBJetsWithoutPUID = ProducerGroup(
    name="GoodBJetsWithoutPUID",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[q.Jet_isBTagged],
    output=[q.good_bjets_mask],
    subproducers=[
        GoodBJetsBaseWithoutPUID,
    ],
    scopes=GLOBAL_SCOPES,
)

# Producer group for jet and b jet selection in run 2 (CHS jets)
BaseJetSelectionWithPUID = ProducerGroup(
    name="GoodJetSelectionWithPUID",
    call=None,
    input=None,
    output=None,
    scopes=GLOBAL_SCOPES,
    subproducers=[
        GoodJetsWithPUID,
        GoodBJetsWithPUID,
    ],
)

# Producer group for jet and b jet selection in run 3 (PUPPI jets)
BaseJetSelectionWithoutPUID = ProducerGroup(
    name="GoodJetSelectionWithoutPUID",
    call=None,
    input=None,
    output=None,
    scopes=GLOBAL_SCOPES,
    subproducers=[
        GoodJetsWithoutPUID,
        GoodBJetsWithoutPUID,
    ],
)


#
# OVERLAP VETOES
#

# Check whether a jet is overlapping with the tight lepton candidates from resolved selection
VetoOverlappingJets = Producer(
    name="VetoOverlappingJets",
    call="physicsobject::jet::VetoOverlappingJets({df}, {output}, {input}, {ak4jet_veto_min_delta_r})",
    input=[
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.p4_1,
        q.p4_2,
    ],
    output=[q.jet_overlap_veto_mask],
    scopes=SCOPES,
)

# Create a mask that includes selected jets that do not overlap with the lepton candidates from the resolved selection
GoodJetsWithVeto = Producer(
    name="GoodJetsWithVeto",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[q.good_jets_mask, q.jet_overlap_veto_mask],
    output=[q.good_jets_with_veto_mask],
    scopes=SCOPES,
)

# Create a mask that includes selected b jets that do not overlap with the lepton candidates from the resolved selection
GoodBJetsWithVeto = Producer(
    name="GoodBJetsWithVeto",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[q.good_bjets_mask, q.jet_overlap_veto_mask],
    output=[q.good_bjets_with_veto_mask],
    scopes=SCOPES,
)

# Create a mask that merged the masks for the selected jets and b jets after overlap cleaning
GoodJetsOrBJetsWithVeto = Producer(
    name="GoodJetsOrBJetsWithVeto",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "any_of")',
    input=[q.good_jets_with_veto_mask, q.good_bjets_with_veto_mask],
    output=[],
    scopes=SCOPES,
)

# Final jet collection as list of indices of selected jets, ordered by pt for the resolved selection
JetCollection = ProducerGroup(
    name="JetCollection",
    call="physicsobject::OrderByPt({df}, {output}, {input})",
    input=[q.Jet_correctedPt],
    output=[q.good_jet_collection],
    scopes=SCOPES,
    subproducers=[GoodJetsOrBJetsWithVeto],
)

# Final b jet collection as list of indices of selected jets, ordered by pt for the resolved selection
BJetCollection = Producer(
    name="BJetCollection",
    call="physicsobject::OrderByPt({df}, {output}, {input})",
    input=[q.Jet_correctedPt, q.good_bjets_with_veto_mask],
    output=[q.good_bjet_collection],
    scopes=SCOPES,
)

# Producer group for the jet selection in the scopes after cleaning against leptons
JetSelection = ProducerGroup(
    name="JetSelection",
    call=None,
    input=[],
    output=[],
    scopes=SCOPES,
    subproducers=[
        VetoOverlappingJets,
        GoodJetsWithVeto,
        GoodBJetsWithVeto,
        JetCollection,
        BJetCollection,
    ],
)


#
# Number of jets (depending on the b jet tagger)
#

NumberOfJets = Producer(
    name="NumberOfJets",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_jet_collection],
    output=[q.n_jets],
    scopes=SCOPES,
)


#
# Quantities for the two leading jets
#

LVJet1 = Producer(
    name="LVJet1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_jet_collection,
    ],
    output=[q.jet_p4_1],
    scopes=SCOPES,
)

LVJet2 = Producer(
    name="LVJet2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_jet_collection,
    ],
    output=[q.jet_p4_2],
    scopes=SCOPES,
)

NumberOfJets = Producer(
    name="NumberOfJets",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_jet_collection],
    output=[q.n_jets],
    scopes=SCOPES,
)

NumberOfJets_boosted = Producer(
    name="NumberOfJets_boosted",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_jet_collection_boosted],
    output=[q.n_jets_boosted],
    scopes=SCOPES,
)

jpt_1 = Producer(
    name="jpt_1",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.jet_p4_1],
    output=[q.jpt_1],
    scopes=SCOPES,
)
jpt_2 = Producer(
    name="jpt_2",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.jet_p4_2],
    output=[q.jpt_2],
    scopes=SCOPES,
)
jeta_1 = Producer(
    name="jeta_1",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.jet_p4_1],
    output=[q.jeta_1],
    scopes=SCOPES,
)
jeta_2 = Producer(
    name="jeta_2",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.jet_p4_2],
    output=[q.jeta_2],
    scopes=SCOPES,
)
jphi_1 = Producer(
    name="jphi_1",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.jet_p4_1],
    output=[q.jphi_1],
    scopes=SCOPES,
)
jphi_2 = Producer(
    name="jphi_2",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.jet_p4_2],
    output=[q.jphi_2],
    scopes=SCOPES,
)
jtag_value_1 = Producer(
    name="jtag_value_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[q.Jet_bTagValue, q.good_jet_collection],
    output=[q.jtag_value_1],
    scopes=SCOPES,
)
jtag_value_2 = Producer(
    name="jtag_value_2",
    call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
    input=[q.Jet_bTagValue, q.good_jet_collection],
    output=[q.jtag_value_2],
    scopes=SCOPES,
)
jpt_nano_1 = Producer(
    name="jpt_nano_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Jet_pt, q.good_jet_collection],
    output=[q.jpt_nano_1],
    scopes=SCOPES,
)
jpt_nano_2 = Producer(
    name="jpt_nano_2",
    call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
    input=[nanoAOD.Jet_pt, q.good_jet_collection],
    output=[q.jpt_nano_2],
    scopes=SCOPES,
)
jpt_raw_1 = Producer(
    name="jpt_raw_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[q.Jet_rawPt, q.good_jet_collection],
    output=[q.jpt_raw_1],
    scopes=SCOPES,
)
jpt_raw_2 = Producer(
    name="jpt_raw_2",
    call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
    input=[q.Jet_rawPt, q.good_jet_collection],
    output=[q.jpt_raw_2],
    scopes=SCOPES,
)
jpt_regressed_1 = Producer(
    name="jpt_regressed_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[q.Jet_correctedPtRegressed, q.good_jet_collection],
    output=[q.jpt_regressed_1],
    scopes=SCOPES,
)
jpt_regressed_2 = Producer(
    name="jpt_regressed_2",
    call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
    input=[q.Jet_correctedPtRegressed, q.good_jet_collection],
    output=[q.jpt_regressed_2],
    scopes=SCOPES,
)
jpt_regressed_resolution_1 = Producer(
    name="jpt_regressed_resolution_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[q.Jet_rawPtRegressedResolution, q.good_jet_collection],
    output=[q.jpt_regressed_resolution_1],
    scopes=SCOPES,
)
jpt_regressed_resolution_2 = Producer(
    name="jpt_regressed_resolution_2",
    call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
    input=[q.Jet_rawPtRegressedResolution, q.good_jet_collection],
    output=[q.jpt_regressed_resolution_2],
    scopes=SCOPES,
)
mjj = Producer(
    name="m_jj",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.jet_p4_1, q.jet_p4_2],
    output=[q.mjj],
    scopes=SCOPES,
)
BasicJetQuantities = ProducerGroup(
    name="BasicJetQuantities",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        LVJet1,
        LVJet2,
        NumberOfJets,
        jpt_1,
        jeta_1,
        jphi_1,
        jtag_value_1,
        jpt_nano_1,
        jpt_raw_1,
        jpt_regressed_1,
        jpt_regressed_resolution_1,
        jpt_2,
        jeta_2,
        jphi_2,
        jtag_value_2,
        jpt_nano_2,
        jpt_raw_2,
        jpt_regressed_2,
        jpt_regressed_resolution_2,
        mjj,
    ],
)

##########################
# Basic b-Jet Quantities
# nbtag, pt, eta, phi, b-tag value
##########################

LVBJet1 = Producer(
    name="LVBJet1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_bjet_collection,
    ],
    output=[q.bjet_p4_1],
    scopes=SCOPES,
)
LVBJet2 = Producer(
    name="LVBJet2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.Jet_correctedPt,
        nanoAOD.Jet_eta,
        nanoAOD.Jet_phi,
        q.Jet_correctedMass,
        q.good_bjet_collection,
    ],
    output=[q.bjet_p4_2],
    scopes=SCOPES,
)

NumberOfBJets = Producer(
    name="NumberOfBJets",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_bjet_collection],
    output=[q.n_bjets],
    scopes=SCOPES,
)

NumberOfBJets_boosted = Producer(
    name="NumberOfBJets_boosted",
    call="physicsobject::Size<Int_t>({df}, {output}, {input})",
    input=[q.good_bjet_collection_boosted],
    output=[q.n_bjets_boosted],
    scopes=SCOPES,
)

BasicBJetQuantities = ProducerGroup(
    name="BasicBJetQuantities",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        NumberOfBJets,
    ],
)
