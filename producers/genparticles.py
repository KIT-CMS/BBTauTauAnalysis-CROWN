from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from code_generation.producer import Producer, ProducerGroup

from ..constants import ET_SCOPES, MT_SCOPES, TT_SCOPES, EE_SCOPES, MM_SCOPES, EM_SCOPES, HAD_TAU_SCOPES, SCOPES


####################
# Set of producers to get the genParticles from the ditaupair
####################
MTGenPair = Producer(
    name="MTGenPair",
    call="ditau_pairselection::buildgenpair({df}, {output}, {input})",
    input=[q.dileptonpair, nanoAOD.Muon_genPartIdx, nanoAOD.Tau_genPartIdx],
    output=[q.gen_dileptonpair],
    scopes=MT_SCOPES,
)
ETGenPair = Producer(
    name="ETGenPair",
    call="ditau_pairselection::buildgenpair({df}, {output}, {input})",
    input=[q.dileptonpair, nanoAOD.Electron_genPartIdx, nanoAOD.Tau_genPartIdx],
    output=[q.gen_dileptonpair],
    scopes=ET_SCOPES,
)
TTGenPair = Producer(
    name="TTGenPair",
    call="ditau_pairselection::buildgenpair({df}, {output}, {input})",
    input=[q.dileptonpair, nanoAOD.Tau_genPartIdx, nanoAOD.Tau_genPartIdx],
    output=[q.gen_dileptonpair],
    scopes=TT_SCOPES,
)
EMGenPair = Producer(
    name="EMGenPair",
    call="ditau_pairselection::buildgenpair({df}, {output}, {input})",
    input=[q.dileptonpair, nanoAOD.Electron_genPartIdx, nanoAOD.Muon_genPartIdx],
    output=[q.gen_dileptonpair],
    scopes=EM_SCOPES,
)
MuMuGenPair = Producer(
    name="MuMuGenPair",
    call="ditau_pairselection::buildgenpair({df}, {output}, {input})",
    input=[q.dileptonpair, nanoAOD.Muon_genPartIdx, nanoAOD.Muon_genPartIdx],
    output=[q.gen_dileptonpair],
    scopes=MM_SCOPES,
)
ElElGenPair = Producer(
    name="ElElGenPair",
    call="ditau_pairselection::buildgenpair({df}, {output}, {input})",
    input=[q.dileptonpair, nanoAOD.Electron_genPartIdx, nanoAOD.Electron_genPartIdx],
    output=[q.gen_dileptonpair],
    scopes=EE_SCOPES,
)
MuMuTrueGenPair = Producer(
    name="GenPair",
    call="ditau_pairselection::buildtruegenpair({df}, {output}, {input}, {truegen_mother_pdgid}, {truegen_daughter_1_pdgid}, {truegen_daughter_2_pdgid})",
    input=[
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_status,
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_genPartIdxMother,
        nanoAOD.GenPart_pt,
    ],
    output=[q.truegenpair],
    scopes=MM_SCOPES,
)
BBGenPair = Producer(
    name="BBGenPair",
    call="ditau_pairselection::buildgenpair({df}, {output}, {input})",
    input=[q.dibjetpair, nanoAOD.Jet_genJetIdx, nanoAOD.Jet_genJetIdx],
    output=[q.gen_dibjetpair],
    scopes=SCOPES,
)
YbbTrueGenPair = Producer(
    name="YbbTrueGenPair",
    call="ditau_pairselection::buildtruegenpair({df}, {output}, {input}, {bb_truegen_mother_pdgid}, {bb_truegen_daughter_1_pdgid}, {bb_truegen_daughter_2_pdgid})",
    input=[
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_status,
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_genPartIdxMother,
        nanoAOD.GenPart_pt,
    ],
    output=[q.gen_truebpair],
    scopes=SCOPES,
)
YtautauTrueGenPair = Producer(
    name="YtautauTrueGenPair",
    call="ditau_pairselection::buildtruegenpair({df}, {output}, {input}, {tautau_truegen_mother_pdgid}, {tautau_truegen_daughter_1_pdgid}, {tautau_truegen_daughter_2_pdgid})",
    input=[
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_status,
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_genPartIdxMother,
        nanoAOD.GenPart_pt,
    ],
    output=[q.gen_truetaupair],
    scopes=SCOPES,
)
EmbeddingGenPair = Producer(
    name="EmbeddingGenPair",
    call="ditau_pairselection::buildtruegenpair({df}, {output}, {input}, {truegen_mother_pdgid}, {truegen_daughter_1_pdgid}, {truegen_daugher_2_pdgid})",
    input=[
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_status,
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_genPartIdxMother,
        nanoAOD.GenPart_pt,
    ],
    output=[q.gen_dileptonpair],
    scopes=SCOPES,
)
####################
# Set of general producers for Gen DiTauPair Quantities
####################

LVGenParticle1 = Producer(
    name="LVGenParticle1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.gen_dileptonpair,
    ],
    output=[q.gen_p4_1],
    scopes=SCOPES,
)
LVGenParticle2 = Producer(
    name="LVGenParticle2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.gen_dileptonpair,
    ],
    output=[q.gen_p4_2],
    scopes=SCOPES,
)
LVTrueGenParticle1 = Producer(
    name="LVTrueGenParticle1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.truegenpair,
    ],
    output=[q.gen_p4_1],
    scopes=SCOPES,
)
LVTrueGenParticle2 = Producer(
    name="LVTrueGenParticle2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.truegenpair,
    ],
    output=[q.gen_p4_2],
    scopes=SCOPES,
)
LVGenJet1 = Producer(
    name="LVGenJet1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.GenJet_pt,
        nanoAOD.GenJet_eta,
        nanoAOD.GenJet_phi,
        nanoAOD.GenJet_mass,
        q.gen_dibjetpair,
    ],
    output=[q.genjet_p4_1],
    scopes=SCOPES,
)
LVGenJet2 = Producer(
    name="LVGenJet2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.GenJet_pt,
        nanoAOD.GenJet_eta,
        nanoAOD.GenJet_phi,
        nanoAOD.GenJet_mass,
        q.gen_dibjetpair,
    ],
    output=[q.genjet_p4_2],
    scopes=SCOPES,
)
LVTrueGenB1 = Producer(
    name="LVTrueGenB1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.gen_truebpair,
    ],
    output=[q.gen_b_p4_1],
    scopes=SCOPES,
)
LVTrueGenB2 = Producer(
    name="LVTrueGenB2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.gen_truebpair,
    ],
    output=[q.gen_b_p4_2],
    scopes=SCOPES,
)
LVTrueGenTau1 = Producer(
    name="LVTrueGenTau1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.gen_truetaupair,
    ],
    output=[q.gen_tau_p4_1],
    scopes=SCOPES,
)
LVTrueGenTau2 = Producer(
    name="LVTrueGenTau2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.gen_truetaupair,
    ],
    output=[q.gen_tau_p4_2],
    scopes=SCOPES,
)

gen_pt_1 = Producer(
    name="gen_pt_1",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.gen_p4_1],
    output=[q.gen_pt_1],
    scopes=SCOPES,
)
gen_pt_2 = Producer(
    name="gen_pt_2",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.gen_p4_2],
    output=[q.gen_pt_2],
    scopes=SCOPES,
)
gen_eta_1 = Producer(
    name="gen_eta_1",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.gen_p4_1],
    output=[q.gen_eta_1],
    scopes=SCOPES,
)
gen_eta_2 = Producer(
    name="gen_eta_2",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.gen_p4_2],
    output=[q.gen_eta_2],
    scopes=SCOPES,
)
gen_phi_1 = Producer(
    name="gen_phi_1",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.gen_p4_1],
    output=[q.gen_phi_1],
    scopes=SCOPES,
)
gen_phi_2 = Producer(
    name="gen_phi_2",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.gen_p4_2],
    output=[q.gen_phi_2],
    scopes=SCOPES,
)
gen_mass_1 = Producer(
    name="gen_mass_1",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_p4_1],
    output=[q.gen_mass_1],
    scopes=SCOPES,
)
gen_mass_2 = Producer(
    name="gen_mass_2",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_p4_2],
    output=[q.gen_mass_2],
    scopes=SCOPES,
)
gen_pdgid_1 = Producer(
    name="gen_pdgid_1",
    call="event::quantity::Get<int>({df}, {output}, {input}, 0)",
    input=[nanoAOD.GenPart_pdgId, q.gen_dileptonpair],
    output=[q.gen_pdgid_1],
    scopes=SCOPES,
)
gen_pdgid_2 = Producer(
    name="gen_pdgid_2",
    call="event::quantity::Get<int>({df}, {output}, {input}, 1)",
    input=[nanoAOD.GenPart_pdgId, q.gen_dileptonpair],
    output=[q.gen_pdgid_2],
    scopes=SCOPES,
)
gen_m_vis = Producer(
    name="gen_m_vis",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_p4_1, q.gen_p4_2],
    output=[q.gen_m_vis],
    scopes=SCOPES,
)
gen_taujet_pt_1 = Producer(
    name="gen_taujet_pt_1",
    call="event::quantity::GetGenJetForObject<float>({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.GenJet_pt,
        nanoAOD.Jet_genJetIdx,
        nanoAOD.Tau_jetIdx,
        q.dileptonpair,
    ],
    output=[q.gen_taujet_pt_1],
    scopes=TT_SCOPES,
)
gen_taujet_pt_2 = Producer(
    name="gen_taujet_pt_2",
    call="event::quantity::GetGenJetForObject<float>({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.GenJet_pt,
        nanoAOD.Jet_genJetIdx,
        nanoAOD.Tau_jetIdx,
        q.dileptonpair,
    ],
    output=[q.gen_taujet_pt_2],
    scopes=HAD_TAU_SCOPES,
)

genjet_pt_1 = Producer(
    name="genjet_pt_1",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.genjet_p4_1],
    output=[q.genjet_pt_1],
    scopes=SCOPES,
)
genjet_pt_2 = Producer(
    name="genjet_pt_2",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.genjet_p4_2],
    output=[q.genjet_pt_2],
    scopes=SCOPES,
)
genjet_eta_1 = Producer(
    name="genjet_eta_1",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.genjet_p4_1],
    output=[q.genjet_eta_1],
    scopes=SCOPES,
)
genjet_eta_2 = Producer(
    name="genjet_eta_2",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.genjet_p4_2],
    output=[q.genjet_eta_2],
    scopes=SCOPES,
)
genjet_phi_1 = Producer(
    name="genjet_phi_1",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.genjet_p4_1],
    output=[q.genjet_phi_1],
    scopes=SCOPES,
)
genjet_phi_2 = Producer(
    name="genjet_phi_2",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.genjet_p4_2],
    output=[q.genjet_phi_2],
    scopes=SCOPES,
)
genjet_mass_1 = Producer(
    name="genjet_mass_1",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.genjet_p4_1],
    output=[q.genjet_mass_1],
    scopes=SCOPES,
)
genjet_mass_2 = Producer(
    name="genjet_mass_2",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.genjet_p4_2],
    output=[q.genjet_mass_2],
    scopes=SCOPES,
)
genjet_hadFlavour_1 = Producer(
    name="genjet_hadFlavour_1",
    call="event::quantity::Get<UChar_t>({df}, {output}, {input}, 0)",
    input=[nanoAOD.GenJet_hadronFlavour, q.gen_dibjetpair],
    output=[q.genjet_hadFlavour_1],
    scopes=SCOPES,
)
genjet_hadFlavour_2 = Producer(
    name="genjet_hadFlavour_2",
    call="event::quantity::Get<UChar_t>({df}, {output}, {input}, 1)",
    input=[nanoAOD.GenJet_hadronFlavour, q.gen_dibjetpair],
    output=[q.genjet_hadFlavour_2],
    scopes=SCOPES,
)
genjet_m_inv = Producer(
    name="genjet_m_inv",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.genjet_p4_1, q.genjet_p4_2],
    output=[q.genjet_m_inv],
    scopes=SCOPES,
)
gen_b_pt_1 = Producer(
    name="gen_b_pt_1",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.gen_b_p4_1],
    output=[q.gen_b_pt_1],
    scopes=SCOPES,
)
gen_b_pt_2 = Producer(
    name="gen_b_pt_2",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.gen_b_p4_2],
    output=[q.gen_b_pt_2],
    scopes=SCOPES,
)
gen_b_eta_1 = Producer(
    name="gen_b_eta_1",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.gen_b_p4_1],
    output=[q.gen_b_eta_1],
    scopes=SCOPES,
)
gen_b_eta_2 = Producer(
    name="gen_b_eta_2",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.gen_b_p4_2],
    output=[q.gen_b_eta_2],
    scopes=SCOPES,
)
gen_b_phi_1 = Producer(
    name="gen_b_phi_1",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.gen_b_p4_1],
    output=[q.gen_b_phi_1],
    scopes=SCOPES,
)
gen_b_phi_2 = Producer(
    name="gen_b_phi_2",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.gen_b_p4_2],
    output=[q.gen_b_phi_2],
    scopes=SCOPES,
)
gen_b_mass_1 = Producer(
    name="gen_b_mass_1",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_b_p4_1],
    output=[q.gen_b_mass_1],
    scopes=SCOPES,
)
gen_b_mass_2 = Producer(
    name="gen_b_mass_2",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_b_p4_2],
    output=[q.gen_b_mass_2],
    scopes=SCOPES,
)
gen_b_m_inv = Producer(
    name="gen_b_m_inv",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_b_p4_1, q.gen_b_p4_2],
    output=[q.gen_b_m_inv],
    scopes=SCOPES,
)
gen_b_deltaR = Producer(
    name="gen_b_deltaR",
    call="quantities::DeltaR({df}, {output}, {input})",
    input=[q.gen_b_p4_1, q.gen_b_p4_2],
    output=[q.gen_b_deltaR],
    scopes=SCOPES,
)

gen_tau_pt_1 = Producer(
    name="gen_tau_pt_1",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.gen_tau_p4_1],
    output=[q.gen_tau_pt_1],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_pt_2 = Producer(
    name="gen_tau_pt_2",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.gen_tau_p4_2],
    output=[q.gen_tau_pt_2],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_eta_1 = Producer(
    name="gen_tau_eta_1",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.gen_tau_p4_1],
    output=[q.gen_tau_eta_1],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_eta_2 = Producer(
    name="gen_tau_eta_2",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.gen_tau_p4_2],
    output=[q.gen_tau_eta_2],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_phi_1 = Producer(
    name="gen_tau_phi_1",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.gen_tau_p4_1],
    output=[q.gen_tau_phi_1],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_phi_2 = Producer(
    name="gen_tau_phi_2",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.gen_tau_p4_2],
    output=[q.gen_tau_phi_2],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_mass_1 = Producer(
    name="gen_tau_mass_1",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_tau_p4_1],
    output=[q.gen_tau_mass_1],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_mass_2 = Producer(
    name="gen_tau_mass_2",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_tau_p4_2],
    output=[q.gen_tau_mass_2],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_m_inv = Producer(
    name="gen_tau_m_inv",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.gen_tau_p4_1, q.gen_tau_p4_2],
    output=[q.gen_tau_m_inv],
    scopes=HAD_TAU_SCOPES,
)
gen_tau_deltaR = Producer(
    name="gen_tau_deltaR",
    call="quantities::DeltaR({df}, {output}, {input})",
    input=[q.gen_tau_p4_1, q.gen_tau_p4_2],
    output=[q.gen_tau_deltaR],
    scopes=HAD_TAU_SCOPES,
)

UnrollGenJetLV1 = ProducerGroup(
    name="UnrollGenJetLV1",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        genjet_pt_1,
        genjet_eta_1,
        genjet_phi_1,
        genjet_mass_1,
        genjet_hadFlavour_1,
    ],
)
UnrollGenJetLV2 = ProducerGroup(
    name="UnrollGenJetLV2",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        genjet_pt_2,
        genjet_eta_2,
        genjet_phi_2,
        genjet_mass_2,
        genjet_hadFlavour_2,
    ],
)
UnrollGenBLV1 = ProducerGroup(
    name="UnrollGenBLV1",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[gen_b_pt_1, gen_b_eta_1, gen_b_phi_1, gen_b_mass_1],
)
UnrollGenBLV2 = ProducerGroup(
    name="UnrollGenBLV2",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[gen_b_pt_2, gen_b_eta_2, gen_b_phi_2, gen_b_mass_2],
)
UnrollGenTrueTauLV1 = ProducerGroup(
    name="UnrollGenTrueTauLV1",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers=[gen_tau_pt_1, gen_tau_eta_1, gen_tau_phi_1, gen_tau_mass_1],
)
UnrollGenTrueTauLV2 = ProducerGroup(
    name="UnrollGenTrueTauLV2",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[gen_tau_pt_2, gen_tau_eta_2, gen_tau_phi_2, gen_tau_mass_2],
)

UnrollGenMuLV1 = ProducerGroup(
    name="UnrollGenMuLV1",
    call=None,
    input=None,
    output=None,
    scopes=MT_SCOPES + MM_SCOPES,
    subproducers=[gen_pt_1, gen_eta_1, gen_phi_1, gen_mass_1, gen_pdgid_1],
)
UnrollGenMuLV2 = ProducerGroup(
    name="UnrollGenMuLV2",
    call=None,
    input=None,
    output=None,
    scopes=EM_SCOPES + MM_SCOPES,
    subproducers=[gen_pt_2, gen_eta_2, gen_phi_2, gen_mass_2, gen_pdgid_2],
)
UnrollGenElLV1 = ProducerGroup(
    name="UnrollGenElLV1",
    call=None,
    input=None,
    output=None,
    scopes=ET_SCOPES + EE_SCOPES + EM_SCOPES,
    subproducers=[gen_pt_1, gen_eta_1, gen_phi_1, gen_mass_1, gen_pdgid_1],
)
UnrollGenElLV2 = ProducerGroup(
    name="UnrollGenElLV2",
    call=None,
    input=None,
    output=None,
    scopes=EE_SCOPES,
    subproducers=[gen_pt_2, gen_eta_2, gen_phi_2, gen_mass_2, gen_pdgid_2],
)
UnrollGenTauLV1 = ProducerGroup(
    name="UnrollGenTauLV1",
    call=None,
    input=None,
    output=None,
    scopes=TT_SCOPES,
    subproducers=[
        gen_pt_1,
        gen_eta_1,
        gen_phi_1,
        gen_mass_1,
        gen_pdgid_1,
        gen_taujet_pt_1,
    ],
)
UnrollGenTauLV2 = ProducerGroup(
    name="UnrollGenLV2",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers=[
        gen_pt_2,
        gen_eta_2,
        gen_phi_2,
        gen_mass_2,
        gen_pdgid_2,
        gen_taujet_pt_2,
    ],
)

GenDiBjetPairQuantities = ProducerGroup(
    name="GenDiBjetPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        BBGenPair,
        LVGenJet1,
        LVGenJet2,
        UnrollGenJetLV1,
        UnrollGenJetLV2,
        genjet_m_inv,
    ],
)
GenBPairQuantities = ProducerGroup(
    name="GenBPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        YbbTrueGenPair,
        LVTrueGenB1,
        LVTrueGenB2,
        UnrollGenBLV1,
        UnrollGenBLV2,
        gen_b_m_inv,
        gen_b_deltaR,
    ],
)
GenTauPairQuantities = ProducerGroup(
    name="GenTauPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=HAD_TAU_SCOPES,
    subproducers=[
        YtautauTrueGenPair,
        LVTrueGenTau1,
        LVTrueGenTau2,
        UnrollGenTrueTauLV1,
        UnrollGenTrueTauLV2,
        gen_tau_m_inv,
        gen_tau_deltaR,
    ],
)
MTGenDiTauPairQuantities = ProducerGroup(
    name="MTGenDiTauPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=MT_SCOPES,
    subproducers=[
        MTGenPair,
        LVGenParticle1,
        LVGenParticle2,
        UnrollGenMuLV1,
        UnrollGenTauLV2,
        gen_m_vis,
    ],
)
ETGenDiTauPairQuantities = ProducerGroup(
    name="ETGenDiTauPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=ET_SCOPES,
    subproducers=[
        ETGenPair,
        LVGenParticle1,
        LVGenParticle2,
        UnrollGenElLV1,
        UnrollGenTauLV2,
        gen_m_vis,
    ],
)
TTGenDiTauPairQuantities = ProducerGroup(
    name="TTGenDiTauPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=TT_SCOPES,
    subproducers=[
        TTGenPair,
        LVGenParticle1,
        LVGenParticle2,
        UnrollGenTauLV1,
        UnrollGenTauLV2,
        gen_m_vis,
    ],
)
EMGenDiTauPairQuantities = ProducerGroup(
    name="EMGenDiTauPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=EM_SCOPES,
    subproducers=[
        EMGenPair,
        LVGenParticle1,
        LVGenParticle2,
        UnrollGenElLV1,
        UnrollGenMuLV2,
        gen_m_vis,
    ],
)
ElElGenPairQuantities = ProducerGroup(
    name="ElElGenPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=EE_SCOPES,
    subproducers=[
        ElElGenPair,
        LVGenParticle1,
        LVGenParticle2,
        UnrollGenElLV1,
        UnrollGenElLV2,
        gen_m_vis,
    ],
)
MuMuGenPairQuantities = ProducerGroup(
    name="MuMuGenPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=MM_SCOPES,
    subproducers=[
        MuMuGenPair,
        LVGenParticle1,
        LVGenParticle2,
        UnrollGenMuLV1,
        UnrollGenMuLV2,
        gen_m_vis,
    ],
)
MuMuTrueGenDiTauPairQuantities = ProducerGroup(
    name="MuMuGenPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=MM_SCOPES,
    subproducers=[
        MuMuTrueGenPair,
        LVTrueGenParticle1,
        LVTrueGenParticle2,
        UnrollGenMuLV1,
        UnrollGenMuLV2,
        gen_m_vis,
    ],
)


#######################
# DiTau Genmatching
#######################

GenPairForGenMatching = Producer(
    name="GenPairForGenMatching",
    call="genparticles::tau::HadronicGenTaus({df}, {output}, {input})",
    input=[
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_genPartIdxMother,
    ],
    output=[q.hadronic_gen_taus],
    scopes=SCOPES,
)

GenMatchP1 = Producer(
    name="GenMatchP1",
    call="genparticles::tau::GenMatching({df}, {output}, {input})",
    input=[
        q.hadronic_gen_taus,
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.p4_1,
    ],
    output=[q.gen_match_1],
    scopes=SCOPES,
)

GenMatchP2 = Producer(
    name="GenMatchP2",
    call="genparticles::tau::GenMatching({df}, {output}, {input})",
    input=[
        q.hadronic_gen_taus,
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.p4_2,
    ],
    output=[q.gen_match_2],
    scopes=SCOPES,
)

GenMatching = ProducerGroup(
    name="GenMatching",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        GenPairForGenMatching,
        GenMatchP1,
        GenMatchP2,
    ],
)

GenMatchBoostedP1 = Producer(
    name="GenMatchBoostedP1",
    call="genparticles::tau::GenMatching({df}, {output}, {input})",
    input=[
        q.hadronic_gen_taus,
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.boosted_p4_1,
    ],
    output=[q.boosted_gen_match_1],
    scopes=SCOPES,
)

GenMatchBoostedP2 = Producer(
    name="GenMatchBoostedP2",
    call="genparticles::tau::GenMatching({df}, {output}, {input})",
    input=[
        q.hadronic_gen_taus,
        nanoAOD.GenPart_pdgId,
        nanoAOD.GenPart_statusFlags,
        nanoAOD.GenPart_pt,
        nanoAOD.GenPart_eta,
        nanoAOD.GenPart_phi,
        nanoAOD.GenPart_mass,
        q.boosted_p4_2,
    ],
    output=[q.boosted_gen_match_2],
    scopes=SCOPES,
)

GenMatchingBoosted = ProducerGroup(
    name="GenMatchingBoosted",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        GenMatchBoostedP1,
        GenMatchBoostedP2,
    ],
)

GenMatchingBPairFlag = Producer(
    name="GenMatchingBPairFlag",
    call="genmatching::jet::particlePairRecoGenMatchFlag({df}, {output}, {input}, {gen_bpair_match_deltaR})",
    input=[
        q.gen_b_p4_1,
        q.gen_b_p4_2,
        q.bpair_p4_1,
        q.bpair_p4_2,
    ],
    output=[q.gen_bpair_match_flag],
    scopes=SCOPES,
)
GenMatchingBoostedTauPairFlag = Producer(
    name="GenMatchingBoostedTauPairFlag",
    call="genmatching::jet::particlePairRecoGenMatchFlag({df}, {output}, {input}, {gen_taupair_match_deltaR})",
    input=[
        q.gen_tau_p4_1,
        q.gen_tau_p4_2,
        q.boosted_p4_1,
        q.boosted_p4_2,
    ],
    output=[q.gen_boostedtaupair_match_flag],
    scopes=SCOPES,
)
CalculateGenBosonVector = Producer(
        call='genparticles::GetBoson({df}, {output}, {input}, {is_data})',
        input=[
            nanoAOD.GenPart_pt,
            nanoAOD.GenPart_eta,
            nanoAOD.GenPart_phi,
            nanoAOD.GenPart_mass,
            nanoAOD.GenPart_pdgId,
            nanoAOD.GenPart_status,
            nanoAOD.GenPart_statusFlags,
        ],
        output=[q.genboson_p4],
        scopes=["global"]
    )