"""
Tau embedding on the Run-2 NanoAOD-v15 inputs (2018 so far).

Embedded events are data apart from the simulated tau decays: the common data
rules (golden JSON, data JEC, no pileup or b-tag weights) already cover them,
and the MC producers of the tau and electron corrections stay. This module
adds what differs from both, per concern:

- event level: MET filters, embedding weights, the generator tau pair;
- light-lepton ID, isolation and trigger SFs of the Tau Embedding group;
- the tt trigger, matched to the embedding filter bit, and its SF;
- the tau energy scale and vsJet SF from the embedding tau payload, with shifts.

Every rule names ``samples="embedding"`` although ``setup`` only runs for
embedding builds, so that each rule stays correct when read out of context.
CROWN applies rules in no defined order, so the MC producers whose output
columns embedding keeps are replaced, never removed and re-appended.
"""

from code_generation.configuration import Configuration
from code_generation.rules import AppendProducer, RemoveProducer, ReplaceProducer

from .constants import ET_SCOPES, HAD_TAU_SCOPES, MT_SCOPES, SL_SCOPES, TT_SCOPES
from .helpers import cpp_list
from .producers import embedding, genparticles, scalefactors, taus, triggers
from .quantities import output as q
from .variations.taus import (
    add_embedding_tau_es_shifts,
    add_embedding_tau_id_vs_jet_shifts,
)

TAU_PAYLOAD = (
    "payloads/tau_embedding/Run2-2018-UL-NanoAODv15/"
    "DeepTau2018v2p5_id_es_embedding2018UL.json.gz"
)
# MC generator pair producer of each scope, replaced by the embedded tau pair
GEN_PAIRS = {
    "et": genparticles.ETGenPair,
    "mt": genparticles.MTGenPair,
    "tt": genparticles.TTGenPair,
}


def setup(configuration: Configuration, profile, era: str, scopes: list[str]):
    """Configure an embedding build of `profile` for `era` and `scopes`."""
    if era != "2018":
        raise ValueError(f"Run-2 v15 embedding exists for 2018 only, got era '{era}'.")
    unsupported = sorted(set(scopes) - set(profile.embedding_scopes))
    if unsupported:
        raise ValueError(
            f"Profile '{profile.name}' builds embedding for "
            f"{list(profile.embedding_scopes)} only, got {unsupported}."
        )

    _add_event_level(configuration)
    _add_generator_pair(configuration)
    _add_muon_scalefactors(configuration)
    _add_electron_scalefactors(configuration)
    _add_tautau_trigger(configuration)
    if profile.embedding_tau_corrections:
        _add_tau_corrections(configuration, era)
    else:
        _remove_tau_corrections(configuration)
    if profile.embedding_min_tau_pt is not None:
        configuration.add_config_parameters(
            HAD_TAU_SCOPES, {"tight_tau_min_pt": profile.embedding_min_tau_pt}
        )


def _add_event_level(configuration: Configuration):
    # the v15 embedding files do not contain Flag_BadPFMuonDzFilter
    met_filters = configuration.config_parameters["global"]["met_filters"]
    configuration.add_config_parameters(
        "global",
        {"met_filters": [f for f in met_filters if f != "Flag_BadPFMuonDzFilter"]},
    )
    # embedding generator weight and selection SFs, the latter evaluated on the
    # generator taus, which carry the kinematics of the replaced muons
    configuration.add_config_parameters(
        HAD_TAU_SCOPES,
        {
            "embedding_selection_sf_file": "data/embedding/embeddingselection_2018UL.json.gz",
            "embedding_selection_trigger_sf": "m_sel_trg_kit_ratio",
            "embedding_selection_id_sf": "EmbID_pt_eta_bins",
        },
    )
    configuration.add_modification_rule(
        HAD_TAU_SCOPES,
        AppendProducer(
            producers=[
                embedding.EmbeddingQuantities,
                embedding.TauEmbeddingSelectionSF,
            ],
            samples="embedding",
        ),
    )


def _add_generator_pair(configuration: Configuration):
    # the generator taus of the embedded Z -> tautau decay
    configuration.add_config_parameters(
        HAD_TAU_SCOPES,
        {
            "truegen_mother_pdgid": 23,
            "truegen_daughter_1_pdgid": 15,
            "truegen_daughter_2_pdgid": 15,
        },
    )
    for scope, gen_pair in GEN_PAIRS.items():
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


def _add_muon_scalefactors(configuration: Configuration):
    # The iso SF takes the correction of the muon's iso bin; the trigger SF has
    # no anti-isolated variant and applies at all iso values.
    configuration.add_config_parameters(
        MT_SCOPES,
        {
            "embedding_muon_sf_file": "data/embedding/muon_2018UL.json.gz",
            "embedding_muon_id_sf": "ID_pt_eta_bins",
            "embedding_muon_id_extrapolation": 1.0,
            "embedding_muon_iso_edges": cpp_list([0.15, 0.25]),
            "embedding_muon_iso_sfs": cpp_list(
                ["Iso_pt_eta_bins", "AIso1_pt_eta_bins", "AIso2_pt_eta_bins"]
            ),
            "embedding_muon_iso_extrapolation": 1.0,
            "singlemuon_trigger_sf": [
                {
                    "flagname": "trg_wgt_single_mu24",
                    "embedding_trigger_sf": "Trg_IsoMu24_pt_eta_bins",
                    "muon_trg_extrapolation": 1.0,
                },
            ],
        },
    )
    configuration.add_modification_rule(
        MT_SCOPES,
        ReplaceProducer(
            producers=[scalefactors.MuonIDIso_SF, embedding.TauEmbeddingMuonIDIsoSF],
            samples="embedding",
        ),
    )
    # the common rules remove the MC trigger SF for embedding
    configuration.add_modification_rule(
        MT_SCOPES,
        AppendProducer(
            producers=[embedding.MTGenerateSingleMuonTriggerSF], samples="embedding"
        ),
    )
    configuration.add_outputs(
        MT_SCOPES, embedding.MTGenerateSingleMuonTriggerSF.output_group
    )


def _add_electron_scalefactors(configuration: Configuration):
    # The KIT ID90 and iso SFs replace the POG ID SF; the iso SF takes the
    # correction of the electron's iso bin. The MC trigger SF producer reads the
    # same payload and takes its embedding type for all iso values.
    configuration.add_config_parameters(
        ET_SCOPES,
        {
            "embedding_electron_sf_file": "data/embedding/electron_2018UL.json.gz",
            "embedding_electron_id_sf": "ID90_pt_eta_bins",
            "embedding_electron_id_extrapolation": 1.0,
            "embedding_electron_iso_edges": cpp_list([0.15]),
            "embedding_electron_iso_sfs": cpp_list(
                ["Iso_pt_eta_bins", "AIso_pt_eta_bins"]
            ),
            "embedding_electron_iso_extrapolation": 1.0,
            "electron_trigger_sf_type": "emb",
        },
    )
    configuration.add_modification_rule(
        ET_SCOPES,
        ReplaceProducer(
            producers=[scalefactors.EleID_SF, embedding.TauEmbeddingElectronIDIsoSF],
            samples="embedding",
        ),
    )
    configuration.add_outputs(ET_SCOPES, [q.iso_wgt_ele_1])


def _add_tautau_trigger(configuration: Configuration):
    # The flags match the embedding filter bit instead of the HLT paths and keep
    # the MC flag names, so the MC trigger SF producer reads the embedding payload.
    configuration.add_modification_rule(
        TT_SCOPES,
        RemoveProducer(producers=[triggers.TauTauTriggerFlags], samples="embedding"),
    )
    configuration.add_modification_rule(
        TT_SCOPES,
        ReplaceProducer(
            producers=[scalefactors.TauTauTriggerSF, embedding.TauTauTriggerFlagsAndSFEmbedding],
            samples="embedding",
        ),
    )
    configuration.add_outputs(TT_SCOPES, triggers.TauTauTriggerFlagsEmbedding.output_group)
    configuration.add_config_parameters(
        TT_SCOPES,
        {
            "tau_trigger_sf_file": "data/embedding/tau_trigger2018_UL.json.gz",
            "tau_trigger_cset_name": "tauTriggerSF",
        },
    )


def _add_tau_corrections(configuration: Configuration, era: str):
    # The MC tau energy scale and vsJet SF producers read the embedding payload,
    # with the MC working points; the vsJet SF is binned in pT in all channels.
    configuration.add_config_parameters(
        HAD_TAU_SCOPES,
        {
            "tau_vsjet_es_sf_file": TAU_PAYLOAD,
            "tau_id_sf_vsjet_sf_dependence": "pt",
        },
    )
    # The payload fills DM11 with the fitted 3-prong category of DM10; the
    # shifts vary each decay mode on its own.
    add_embedding_tau_es_shifts(configuration, era, taus.TauPtCorrectionMC)
    add_embedding_tau_id_vs_jet_shifts(
        configuration,
        era,
        [scalefactors.TauIDVsJetSF2],
        SL_SCOPES,
        pt_bins=[(20, 40), (40, "Inf")],
    )
    # the tt selection requires both taus above 40 GeV
    add_embedding_tau_id_vs_jet_shifts(
        configuration,
        era,
        [scalefactors.TauIDVsJetSF1, scalefactors.TauIDVsJetSF2],
        TT_SCOPES,
        pt_bins=[(40, "Inf")],
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
