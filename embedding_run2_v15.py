"""
Tau embedding on the Run-2 NanoAOD-v15 inputs (2016preVFP, 2016postVFP, 2017, 2018).

Embedded events are data apart from the simulated tau decays: the common data
rules (golden JSON, data JEC, no pileup or b-tag weights) already cover them,
and the MC producers of the tau and electron corrections stay. This module
adds what differs from both, per concern:

- event level: MET filters, embedding weights, the generator lepton pair;
- light-lepton ID, isolation and trigger SFs of the Tau Embedding group;
- the tt trigger: no trigger requirement, the data efficiency of the di-tau leg of
  each tau as weight (v7 spec E33); the flags matched to the embedding filter bits
  stay as diagnostics;
- the tau energy scale and vsJet SF from the embedding tau payload, with shifts.

The inputs of an era are the entries of KIT_EMBEDDING_PAYLOADS,
TAU_EMBEDDING_ID_ES_PAYLOADS and TT_EMBEDDING_TRIGGER_EFFICIENCIES; nothing else
names an era.

The mm scope holds the mu -> mu embedded events, which only the tau-ID measurement
profile builds (``embedding_scopes``).

Every rule names ``samples="embedding"`` although ``setup`` only runs for
embedding builds, so that each rule stays correct when read out of context.
CROWN applies rules in no defined order, so the MC producers whose output
columns embedding keeps are replaced, never removed and re-appended.
"""

from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from code_generation.configuration import Configuration
from code_generation.rules import AppendProducer, RemoveProducer, ReplaceProducer

from .constants import (
    ERAS_RUN2,
    ET_SCOPES,
    HAD_TAU_SCOPES,
    MM_SCOPES,
    MT_SCOPES,
    SL_SCOPES,
    TT_SCOPES,
)
from .helpers import cpp_list
from .producers import embedding, genparticles, scalefactors, taus, triggers
from .quantities import output as q
from .tau_triggersetup import KIT_SINGLE_ELECTRON_TRIGGER_SFS, KIT_SINGLE_MUON_TRIGGER_SFS
from .variations.taus import (
    add_embedding_tau_es_shifts,
    add_embedding_tau_id_vs_jet_shifts,
)


@dataclass(frozen=True)
class KitEmbeddingPayloads:
    """The payloads of the Tau Embedding group (KIT) for the embedding of one era."""

    # selection SFs of the embedded muons (embeddingselection_<era>UL)
    selection: str
    # muon ID, iso and trigger SFs, and the trigger SF column -> correction
    muon: str
    muon_trigger_sfs: Mapping[str, str]
    # electron ID, iso and trigger SFs, and the trigger SF column -> correction
    electron: str
    electron_trigger_sfs: Mapping[str, str]
    # MET filters the embedding files of the era lack
    missing_met_filters: Tuple[str, ...] = ()


# The trigger SFs are those of the analysis triggers (v7 spec E5, E6), the same
# corrections as in MC with type "emb". Only the 2018 embedding files lack
# Flag_BadPFMuonDzFilter; 2016 and 2017 keep it.
KIT_EMBEDDING_PAYLOADS = {
    era: KitEmbeddingPayloads(
        selection=f"data/embedding/embeddingselection_{era}UL.json.gz",
        muon=f"data/embedding/muon_{era}UL.json.gz",
        muon_trigger_sfs=KIT_SINGLE_MUON_TRIGGER_SFS[era],
        electron=f"data/embedding/electron_{era}UL.json.gz",
        electron_trigger_sfs=KIT_SINGLE_ELECTRON_TRIGGER_SFS[era],
        missing_met_filters=("Flag_BadPFMuonDzFilter",) if era == "2018" else (),
    )
    for era in ERAS_RUN2
}

# The tau energy scale and vsJet SF of the embedded taus, measured per era with
# ShapeSmith on smrun2_tau_id_v2 (its MC; data and embedding of smrun2_tau_id_v1;
# v7 spec E16, 5.4) at payloads/tau_embedding/Run2-<era>-UL-NanoAODv15/. Only the profiles that correct
# the embedded taus (embedding_tau_corrections) need the era's entry.
TAU_EMBEDDING_ID_ES_PAYLOADS = {
    era: (
        f"payloads/tau_embedding/Run2-{era}-UL-NanoAODv15/"
        f"DeepTau2018v2p5_id_es_embedding{era}UL.json.gz"
    )
    for era in ERAS_RUN2
}


@dataclass(frozen=True)
class TtEmbeddingTriggerEfficiency:
    """The data efficiency of the di-tau trigger leg the tt embedding is weighted with."""

    # correctionlib file; None takes the POG TAU payload of the era
    # (tau_trigger_sf_file of the configuration)
    file: Optional[str]
    correction: str
    # isolation class of the tau (Medium, AntiMedium = VVVLoose and not Medium)
    # -> working point of the payload
    working_points: Mapping[str, str]


# v7 spec E33 (docs v7_tt_emb_trigger 12.6): the eff_data of the di-tau leg measured
# per era with ShapeSmith on smrun2_tau_id_v2 (its MC; data and embedding of
# smrun2_tau_id_v1; mu tau_h tag and probe) at
# payloads/tau_trigger_embedding/Run2-<era>-UL-NanoAODv15/, in both isolation
# classes: Medium and VVVLoose_not_Medium (VVVLoose and not Medium).
TT_EMBEDDING_TRIGGER_EFFICIENCIES = {
    era: TtEmbeddingTriggerEfficiency(
        file=(
            f"payloads/tau_trigger_embedding/Run2-{era}-UL-NanoAODv15/"
            f"ditau_trigger_DeepTau2018v2p5_embedding{era}UL.json.gz"
        ),
        correction="tau_trigger",
        working_points={"Medium": "Medium", "AntiMedium": "VVVLoose_not_Medium"},
    )
    for era in ERAS_RUN2
}
TT_EMBEDDING_TRIGGER_MODES = ("eff_data",)
EMBEDDING_SCOPES = HAD_TAU_SCOPES + MM_SCOPES
# MC generator pair producer of each scope and the PDG ID of the embedded
# leptons that replace it: taus, or muons in mm
GEN_PAIRS = {
    "et": (genparticles.ETGenPair, 15),
    "mt": (genparticles.MTGenPair, 15),
    "tt": (genparticles.TTGenPair, 15),
    "mm": (genparticles.MuMuGenPair, 13),
}


def setup(configuration: Configuration, profile, era: str, scopes: list[str]):
    """Configure an embedding build of `profile` for `era` and `scopes`."""
    if era not in KIT_EMBEDDING_PAYLOADS:
        raise ValueError(
            f"Run-2 v15 embedding exists for {sorted(KIT_EMBEDDING_PAYLOADS)} only, "
            f"got era '{era}'."
        )
    unsupported = sorted(set(scopes) - set(profile.embedding_scopes))
    if unsupported:
        raise ValueError(
            f"Profile '{profile.name}' builds embedding for "
            f"{list(profile.embedding_scopes)} only, got {unsupported}."
        )
    if profile.tt_embedding_trigger not in TT_EMBEDDING_TRIGGER_MODES:
        raise ValueError(
            f"tt_embedding_trigger '{profile.tt_embedding_trigger}' is not implemented: "
            f"only {list(TT_EMBEDDING_TRIGGER_MODES)} (variant B, the filter bits times "
            "eps_data / eps_EMB, needs the measured eps_EMB of the tt embedding)."
        )
    tau_payload = None
    if profile.embedding_tau_corrections:
        tau_payload = TAU_EMBEDDING_ID_ES_PAYLOADS.get(era)
        if tau_payload is None:
            raise ValueError(
                f"No embedding tau ID/ES payload for era '{era}': measure it (v7 spec "
                "5.4) and add it to embedding_run2_v15.TAU_EMBEDDING_ID_ES_PAYLOADS; "
                f"profile '{profile.name}' corrects the embedded taus."
            )
    payloads = KIT_EMBEDDING_PAYLOADS[era]

    _add_event_level(configuration, payloads)
    _add_generator_pair(configuration)
    _add_muon_scalefactors(configuration, payloads)
    _add_electron_scalefactors(configuration, payloads, profile)
    _add_tautau_trigger(configuration, TT_EMBEDDING_TRIGGER_EFFICIENCIES[era])
    if profile.embedding_tau_corrections:
        _add_tau_corrections(configuration, era, tau_payload)
    else:
        _remove_tau_corrections(configuration)
    if profile.embedding_min_tau_pt is not None:
        configuration.add_config_parameters(
            HAD_TAU_SCOPES, {"tight_tau_min_pt": profile.embedding_min_tau_pt}
        )


def _add_event_level(configuration: Configuration, payloads: KitEmbeddingPayloads):
    # the MET filters the era's v15 embedding files lack
    met_filters = configuration.config_parameters["global"]["met_filters"]
    configuration.add_config_parameters(
        "global",
        {"met_filters": [f for f in met_filters if f not in payloads.missing_met_filters]},
    )
    # embedding generator weight and selection SFs, the latter evaluated on the
    # generator leptons, which carry the kinematics of the replaced muons
    configuration.add_config_parameters(
        EMBEDDING_SCOPES,
        {
            "embedding_selection_sf_file": payloads.selection,
            "embedding_selection_trigger_sf": "m_sel_trg_kit_ratio",
            "embedding_selection_id_sf": "EmbID_pt_eta_bins",
        },
    )
    configuration.add_modification_rule(
        EMBEDDING_SCOPES,
        AppendProducer(
            producers=[
                embedding.EmbeddingQuantities,
                embedding.TauEmbeddingSelectionSF,
            ],
            samples="embedding",
        ),
    )


def _add_generator_pair(configuration: Configuration):
    # the generator leptons of the embedded Z decay
    for scope, (gen_pair, lepton_pdgid) in GEN_PAIRS.items():
        configuration.add_config_parameters(
            [scope],
            {
                "truegen_mother_pdgid": 23,
                "truegen_daughter_1_pdgid": lepton_pdgid,
                "truegen_daughter_2_pdgid": lepton_pdgid,
            },
        )
        configuration.add_modification_rule(
            [scope],
            ReplaceProducer(
                producers=[gen_pair, genparticles.EmbeddingGenPair], samples="embedding"
            ),
        )
    # the v15 embedding files carry no generator jets
    configuration.add_modification_rule(
        HAD_TAU_SCOPES,
        RemoveProducer(producers=[genparticles.gen_taujet_pt_2], samples="embedding"),
    )
    configuration.add_modification_rule(
        TT_SCOPES,
        RemoveProducer(producers=[genparticles.gen_taujet_pt_1], samples="embedding"),
    )


def _add_muon_scalefactors(configuration: Configuration, payloads: KitEmbeddingPayloads):
    # The iso SF takes the correction of the muon's iso bin in mt and the isolated
    # one for both muons in mm; the trigger SF of the first muon has no
    # anti-isolated variant and applies at all iso values.
    configuration.add_config_parameters(
        MT_SCOPES + MM_SCOPES,
        {
            "embedding_muon_sf_file": payloads.muon,
            "embedding_muon_id_sf": "ID_pt_eta_bins",
            "embedding_muon_id_extrapolation": 1.0,
            "embedding_muon_iso_extrapolation": 1.0,
            "singlemuon_trigger_sf": [
                {
                    "flagname": column,
                    "embedding_trigger_sf": correction,
                    "muon_trg_extrapolation": 1.0,
                }
                for column, correction in payloads.muon_trigger_sfs.items()
            ],
        },
    )
    configuration.add_config_parameters(
        MT_SCOPES,
        {
            "embedding_muon_iso_edges": cpp_list([0.15, 0.25]),
            "embedding_muon_iso_sfs": cpp_list(
                ["Iso_pt_eta_bins", "AIso1_pt_eta_bins", "AIso2_pt_eta_bins"]
            ),
        },
    )
    configuration.add_config_parameters(
        MM_SCOPES, {"embedding_muon_iso_sf": "Iso_pt_eta_bins"}
    )
    configuration.add_modification_rule(
        MT_SCOPES + MM_SCOPES,
        ReplaceProducer(
            producers=[scalefactors.MuonIDIso_SF, embedding.TauEmbeddingMuonIDIsoSF],
            samples="embedding",
        ),
    )
    # the common rules remove the MC trigger SF for embedding
    configuration.add_modification_rule(
        MT_SCOPES + MM_SCOPES,
        AppendProducer(
            producers=[embedding.MTGenerateSingleMuonTriggerSF], samples="embedding"
        ),
    )
    configuration.add_outputs(
        MT_SCOPES + MM_SCOPES, embedding.MTGenerateSingleMuonTriggerSF.output_group
    )


def _add_electron_scalefactors(
    configuration: Configuration, payloads: KitEmbeddingPayloads, profile
):
    # The KIT ID90 and iso SFs replace the POG ID SF; the iso SF takes the
    # correction of the electron's iso bin. The MC trigger SF producer reads the
    # same payload (mc_electron_sf_file) and takes its embedding type for all iso
    # values.
    configuration.add_config_parameters(
        ET_SCOPES,
        {
            "embedding_electron_sf_file": payloads.electron,
            "embedding_electron_id_sf": "ID90_pt_eta_bins",
            "embedding_electron_id_extrapolation": 1.0,
            "embedding_electron_iso_edges": cpp_list([0.15]),
            "embedding_electron_iso_sfs": cpp_list(
                ["Iso_pt_eta_bins", "AIso_pt_eta_bins"]
            ),
            "embedding_electron_iso_extrapolation": 1.0,
            "electron_trigger_sf_type": "emb",
            "singlelectron_trigger_sf_mc": [
                {
                    "flagname": column,
                    "mc_trigger_sf": correction,
                    "mc_electron_trg_extrapolation": 1.0,
                }
                for column, correction in payloads.electron_trigger_sfs.items()
            ],
        },
    )
    configuration.add_modification_rule(
        ET_SCOPES,
        ReplaceProducer(
            producers=[
                scalefactors.electron_id_sf(profile.electron_sf_supercluster_eta),
                embedding.TauEmbeddingElectronIDIsoSF,
            ],
            samples="embedding",
        ),
    )
    configuration.add_outputs(ET_SCOPES, [q.iso_wgt_ele_1])


def _add_tautau_trigger(configuration: Configuration, efficiency: TtEmbeddingTriggerEfficiency):
    # v7 spec E33, variant A: the embedded taus fire no di-tau path, so tt embedding
    # has no trigger requirement and is weighted with the data efficiency of the
    # di-tau leg of each tau, trg_effdata_emb_<class>_<leg> for both isolation
    # classes; downstream takes the class of each tau. The flags of the filter bits
    # of TauEmbeddingSamplesUL keep the MC flag names as diagnostic columns; the
    # MC trigger SF is removed.
    configuration.add_modification_rule(
        TT_SCOPES,
        RemoveProducer(producers=[triggers.TauTauTriggerFlags], samples="embedding"),
    )
    configuration.add_modification_rule(
        TT_SCOPES,
        ReplaceProducer(
            producers=[scalefactors.TauTauTriggerSF, embedding.TauTauTriggerFlagsAndEffDataEmbedding],
            samples="embedding",
        ),
    )
    configuration.add_outputs(
        TT_SCOPES,
        [
            triggers.TauTauTriggerFlagsEmbedding.output_group,
            embedding.TauTauTriggerEffDataEmbedding_1.output_group,
            embedding.TauTauTriggerEffDataEmbedding_2.output_group,
        ],
    )
    configuration.add_config_parameters(
        TT_SCOPES,
        {
            "tt_embedding_trigger_eff_file": (
                efficiency.file
                if efficiency.file is not None
                else configuration.config_parameters["tt"]["tau_trigger_sf_file"]
            ),
            "tt_embedding_trigger_eff_name": efficiency.correction,
            "tt_embedding_trigger_eff_syst": "nom",
            **{
                f"tt_embedding_trigger_eff_leg{leg}": [
                    {"flagname": f"trg_effdata_emb_{iso_class}_{leg}", "tt_embedding_trigger_eff_wp": wp}
                    for iso_class, wp in efficiency.working_points.items()
                ]
                for leg in (1, 2)
            },
        },
    )


def _add_tau_corrections(configuration: Configuration, era: str, tau_payload: str):
    # The MC tau energy scale and vsJet SF producers read the embedding payload,
    # with the MC working points. Both are binned in the decay mode only, like
    # the POG corrections of MC: the pT-binned energy scale steps at an
    # uncorrected pT of 40 GeV, which leaves an empty band just below 40 GeV in
    # the corrected pT.
    configuration.add_config_parameters(
        HAD_TAU_SCOPES,
        {
            "tau_vsjet_es_sf_file": tau_payload,
            "tau_ES_json_name": "tau_energy_scale_dm_binned",
            "tau_id_sf_vsjet_sf_dependence": "dm",
        },
    )
    # The payload fills DM11 with the fitted 3-prong category of DM10; the
    # shifts vary each decay mode on its own.
    add_embedding_tau_es_shifts(configuration, era, taus.TauPtCorrectionMC)
    add_embedding_tau_id_vs_jet_shifts(
        configuration, era, [scalefactors.TauIDVsJetSF2], SL_SCOPES
    )
    add_embedding_tau_id_vs_jet_shifts(
        configuration,
        era,
        [scalefactors.TauIDVsJetSF1, scalefactors.TauIDVsJetSF2],
        TT_SCOPES,
    )


def _remove_tau_corrections(configuration: Configuration):
    # uncorrected tau energy scale (a factor 1 per decay mode) and no vsJet SF
    configuration.add_config_parameters(
        HAD_TAU_SCOPES, {f"tau_ES_shift_DM{dm}": 1.0 for dm in (0, 1, 10, 11)}
    )
    configuration.add_modification_rule(
        HAD_TAU_SCOPES,
        ReplaceProducer(
            producers=[taus.TauPtCorrectionMC, taus.TauPtCorrection_byValue],
            samples="embedding",
        ),
    )
    configuration.add_modification_rule(
        HAD_TAU_SCOPES,
        RemoveProducer(producers=[scalefactors.TauIDVsJetSF2], samples="embedding"),
    )
    configuration.add_modification_rule(
        TT_SCOPES,
        RemoveProducer(producers=[scalefactors.TauIDVsJetSF1], samples="embedding"),
    )
