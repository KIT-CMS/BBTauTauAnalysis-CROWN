from ..quantities import output as q
from ..quantities import nanoAOD
from code_generation.producer import Producer, ProducerGroup, ExtendedVectorProducer


####################
# Set of producers used for selection of good boosted taus
####################

boostedTauPtCorrection = Producer(
    name="boostedTauPtCorrection",
    call='physicsobject::tau::PtCorrectionMC_genuineTau({df}, correctionManager, {output}, {input}, "{boostedtau_sf_file}", "{boostedtau_ES_json_name}", "{boostedtau_id_algorithm}", "{boostedtau_ES_shift_DM0}", "{boostedtau_ES_shift_DM1}", "{boostedtau_ES_shift_DM10}", "{boostedtau_ES_shift_DM11}")',
    input=[
        nanoAOD.boostedTau_pt,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_decayMode,
        nanoAOD.boostedTau_genPartFlav,
    ],
    output=[q.boostedTau_pt_corrected],
    scopes=["et", "mt", "tt"],
)
boostedTauMassCorrection = Producer(
    name="boostedTauMassCorrection",
    call="physicsobject::MassCorrectionWithPt({df}, {output}, {input})",
    input=[
        nanoAOD.boostedTau_mass,
        nanoAOD.boostedTau_pt,
        q.boostedTau_pt_corrected,
    ],
    output=[q.boostedTau_mass_corrected],
    scopes=["et", "mt", "tt"],
)
boostedTauEnergyCorrection = ProducerGroup(
    name="boostedTauEnergyCorrection",
    call=None,
    input=None,
    output=None,
    scopes=["et", "mt", "tt"],
    subproducers=[
        boostedTauPtCorrection,
        boostedTauMassCorrection,
    ],
)
boostedTauPtCorrection_data = Producer(
    name="boostedTauPtCorrection_data",
    call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
    input=[nanoAOD.boostedTau_pt],
    output=[q.boostedTau_pt_corrected],
    scopes=["et", "mt", "tt"],
)
boostedTauMassCorrection_data = Producer(
    name="boostedTauMassCorrection_data",
    call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
    input=[nanoAOD.boostedTau_mass],
    output=[q.boostedTau_mass_corrected],
    scopes=["et", "mt", "tt"],
)
boostedTauEnergyCorrection_data = ProducerGroup(
    name="boostedTauEnergyCorrection",
    call=None,
    input=None,
    output=None,
    scopes=["et", "mt", "tt"],
    subproducers=[
        boostedTauPtCorrection_data,
        boostedTauMassCorrection_data,
    ],
)

boostedTauPtCut = Producer(
    name="boostedTauPtCut",
    call="physicsobject::CutMin<float>({df}, {output}, {input}, {min_boostedtau_pt})",
    input=[q.boostedTau_pt_corrected],
    output=[],
    scopes=["et", "mt", "tt"],
)
boostedTauEtaCut = Producer(
    name="boostedTauEtaCut",
    call="physicsobject::CutAbsMax<float>({df}, {output}, {input}, {max_boostedtau_eta})",
    input=[nanoAOD.boostedTau_eta],
    output=[],
    scopes=["et", "mt", "tt"],
)
boostedTauDMCut = Producer(
    name="boostedTauDMCut",
    call="physicsobject::CutQuantity<int>({df}, {output}, {input}, {vec_open}{boostedtau_dms}{vec_close})",
    input=[nanoAOD.boostedTau_decayMode],
    output=[],
    scopes=["et", "mt", "tt"],
)
MVAisoBoostedTauIDCut = Producer(
    name="MVAisoBoostedTauIDCut",
    call="physicsobject::CutMin<UChar_t>({df}, {output}, {input}, {iso_boostedtau_id_bit})",
    input=[nanoAOD.boostedTau_idMVAoldDM2017v2],
    output=[],
    scopes=["et", "mt", "tt"],
)
AntiEleBoostedTauIDCut = Producer(
    name="AntiEleBoostedTauIDCut",
    call="physicsobject::CutMin<UChar_t>({df}, {output}, {input}, {antiele_boostedtau_id_bit})",
    input=[nanoAOD.boostedTau_idAntiEle2018],
    output=[],
    scopes=["et", "mt", "tt"],
)
AntiMuBoostedTauIDCut = Producer(
    name="AntiMuBoostedTauIDCut",
    call="physicsobject::CutMin<UChar_t>({df}, {output}, {input}, {antimu_boostedtau_id_bit})",
    input=[nanoAOD.boostedTau_idAntiMu],
    output=[],
    scopes=["et", "mt", "tt"],
)

GoodBoostedTaus = ProducerGroup(
    name="GoodBoostedTaus",
    call='physicsobject::CombineMasks({df}, {output}, {input}, "all_of")',
    input=[],
    output=[q.good_boostedtaus_mask],
    scopes=["et", "mt", "tt"],
    subproducers=[
        boostedTauPtCut,
        boostedTauEtaCut,
        boostedTauDMCut,
        #MVAisoBoostedTauIDCut,
        #AntiEleBoostedTauIDCut,
        #AntiMuBoostedTauIDCut,
    ],
)
NumberOfGoodBoostedTaus = Producer(
    name="NumberOfGoodBoostedTaus",
    call="physicsobject::Count({df}, {output}, {input})",
    input=[q.good_boostedtaus_mask],
    output=[q.nboostedtaus],
    scopes=["mt", "et", "tt"],
)

####################
# Set of producers for quantities of good boosted taus
####################

boostedLVMu1 = Producer(
    name="boostedLVMu1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.boosteddileptonpair,
    ],
    output=[q.boosted_p4_1],
    scopes=["mt", "mm"],
)
boostedLVMu1_uncorrected = Producer(
    name="boostedLVMu1_uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.Muon_pt,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_mass,
        q.boosteddileptonpair,
    ],
    output=[q.boosted_p4_1_uncorrected],
    scopes=["mt", "mm"],
)
boostedLVEl1 = Producer(
    name="boostedLVEl1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.Electron_pt_corrected,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.boosteddileptonpair,
    ],
    output=[q.boosted_p4_1],
    scopes=["et", "ee"],
)
boostedLVEl1_uncorrected = Producer(
    name="boostedLVEl1_uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.Electron_pt,
        nanoAOD.Electron_eta,
        nanoAOD.Electron_phi,
        nanoAOD.Electron_mass,
        q.boosteddileptonpair,
    ],
    output=[q.boosted_p4_1_uncorrected],
    scopes=["et", "ee"],
)
boostedLVTau1 = Producer(
    name="boostedLVTau1",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        q.boostedTau_pt_corrected,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_phi,
        q.boostedTau_mass_corrected,
        q.boosteddileptonpair,
    ],
    output=[q.boosted_p4_1],
    scopes=["tt"],
)
boostedLVTau1_uncorrected = Producer(
    name="boostedLVTau1_uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 0)",
    input=[
        nanoAOD.boostedTau_pt,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_phi,
        nanoAOD.boostedTau_mass,
        q.boosteddileptonpair,
    ],
    output=[q.boosted_p4_1_uncorrected],
    scopes=["tt"],
)
boostedLVTau2 = Producer(
    name="boostedLVTau2",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        q.boostedTau_pt_corrected,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_phi,
        q.boostedTau_mass_corrected,
        q.boosteddileptonpair,
    ],
    output=[q.boosted_p4_2],
    scopes=["mt", "et", "tt"],
)
boostedLVTau2_uncorrected = Producer(
    name="boostedLVTau2_uncorrected",
    call="lorentzvector::Build({df}, {output}, {input}, 1)",
    input=[
        nanoAOD.boostedTau_pt,
        nanoAOD.boostedTau_eta,
        nanoAOD.boostedTau_phi,
        nanoAOD.boostedTau_mass,
        q.boosteddileptonpair,
    ],
    output=[q.boosted_p4_2_uncorrected],
    scopes=["mt", "et", "tt"],
)

boosted_pt_1 = Producer(
    name="boosted_pt_1",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.boosted_p4_1],
    output=[q.boosted_pt_1],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_pt_2 = Producer(
    name="boosted_pt_2",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.boosted_p4_2],
    output=[q.boosted_pt_2],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_eta_1 = Producer(
    name="boosted_eta_1",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.boosted_p4_1],
    output=[q.boosted_eta_1],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_eta_2 = Producer(
    name="boosted_eta_2",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.boosted_p4_2],
    output=[q.boosted_eta_2],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_phi_1 = Producer(
    name="boosted_phi_1",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.boosted_p4_1],
    output=[q.boosted_phi_1],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_phi_2 = Producer(
    name="boosted_phi_2",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.boosted_p4_2],
    output=[q.boosted_phi_2],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_mass_1 = Producer(
    name="boosted_mass_1",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.boosted_p4_1],
    output=[q.boosted_mass_1],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_mass_2 = Producer(
    name="boosted_mass_2",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.boosted_p4_2],
    output=[q.boosted_mass_2],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)

boosted_muon_dxy_1 = Producer(
    name="boosted_muon_dxy_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Muon_dxy, q.boosteddileptonpair],
    output=[q.boosted_dxy_1],
    scopes=["mt", "mm"],
)
boosted_muon_dz_1 = Producer(
    name="boosted_muon_dz_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Muon_dz, q.boosteddileptonpair],
    output=[q.boosted_dz_1],
    scopes=["mt", "mm"],
)
boosted_muon_q_1 = Producer(
    name="boosted_muon_q_1",
    call="event::quantity::Get<int>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Muon_charge, q.boosteddileptonpair],
    output=[q.boosted_q_1],
    scopes=["mt", "mm"],
)
boosted_muon_iso_1 = Producer(
    name="boosted_muon_iso_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Muon_pfRelIso04_all, q.boosteddileptonpair],
    output=[q.boosted_iso_1],
    scopes=["mt", "mm"],
)
boosted_muon_is_global_1 = Producer(
    name="boosted_muon_is_global_1",
    call="event::quantity::Get<bool>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Muon_isGlobal, q.boosteddileptonpair],
    output=[q.boosted_is_global_1],
    scopes=["mt", "mm"],
)
boosted_tau_decaymode_1_notau = Producer(
    name="boosted_tau_decaymode_1_notau",
    call="event::quantity::Define({df}, {output}, -1)",
    input=[],
    output=[q.boosted_tau_decaymode_1],
    scopes=["et", "mt", "em", "ee", "mm"],
)

boosted_electron_dxy_1 = Producer(
    name="boosted_electron_dxy_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Electron_dxy, q.boosteddileptonpair],
    output=[q.boosted_dxy_1],
    scopes=["et", "ee"],
)
boosted_electron_dz_1 = Producer(
    name="boosted_electron_dz_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Electron_dz, q.boosteddileptonpair],
    output=[q.boosted_dz_1],
    scopes=["et", "ee"],
)
boosted_electron_q_1 = Producer(
    name="boosted_electron_q_1",
    call="event::quantity::Get<int>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Electron_charge, q.boosteddileptonpair],
    output=[q.boosted_q_1],
    scopes=["et", "ee"],
)
boosted_electron_iso_1 = Producer(
    name="boosted_electron_iso_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[nanoAOD.Electron_pfRelIso03_all, q.boosteddileptonpair],
    output=[q.boosted_iso_1],
    scopes=["et", "ee"],
)

boosted_tau_q_1 = Producer(
    name="boosted_tau_q_1",
    call="event::quantity::Get<int>({df}, {output}, {input}, 0)",
    input=[nanoAOD.boostedTau_charge, q.boosteddileptonpair],
    output=[q.boosted_q_1],
    scopes=["tt"],
)
boosted_tau_iso_1 = Producer(
    name="boosted_tau_iso_1",
    call="event::quantity::Get<float>({df}, {output}, {input}, 0)",
    input=[nanoAOD.boostedTau_rawMVAoldDM2017v2, q.boosteddileptonpair],
    output=[q.boosted_iso_1],
    scopes=["tt"],
)
boosted_tau_decaymode_1 = Producer(
    name="boosted_taudecaymode_1",
    call="event::quantity::Get<int>({df}, {output}, {input}, 0)",
    input=[nanoAOD.boostedTau_decayMode, q.boosteddileptonpair],
    output=[q.boosted_tau_decaymode_1],
    scopes=["tt"],
)
isoTauIDFlag_1 = ExtendedVectorProducer(
    name="isoTauIDFlag_1",
    call="""physicsobject::tau::quantity::IDFlag_v12(
        {df},
        {output},
        {input},
        0,
        {iso_boostedtau_id_WPbit})
        """,
    input=[nanoAOD.boostedTau_idMVAoldDM2017v2, q.boosteddileptonpair],
    output="boostedtau_1_iso_id_outputname",
    scopes=["tt"],
    vec_config="iso_boostedtau_id",
)
antiEleTauIDFlag_1 = ExtendedVectorProducer(
    name="antiEleTauIDFlag_1",
    call="""physicsobject::tau::quantity::IDFlag_v12(
        {df},
        {output},
        {input},
        0,
        {antiele_boostedtau_id_WPbit})
        """,
    input=[nanoAOD.boostedTau_idAntiEle2018, q.boosteddileptonpair],
    output="boostedtau_1_antiele_id_outputname",
    scopes=["tt"],
    vec_config="antiele_boostedtau_id",
)
antiMuTauIDFlag_1 = ExtendedVectorProducer(
    name="antiMuTauIDFlag_1",
    call="""physicsobject::tau::quantity::IDFlag_v12(
        {df},
        {output},
        {input},
        0,
        {antimu_boostedtau_id_WPbit})
        """,
    input=[nanoAOD.boostedTau_idAntiMu, q.boosteddileptonpair],
    output="boostedtau_1_antimu_id_outputname",
    scopes=["tt"],
    vec_config="antimu_boostedtau_id",
)
boosted_tau_q_2 = Producer(
    name="boosted_tau_q_2",
    call="event::quantity::Get<int>({df}, {output}, {input}, 1)",
    input=[nanoAOD.boostedTau_charge, q.boosteddileptonpair],
    output=[q.boosted_q_2],
    scopes=["mt", "et", "tt"],
)
boosted_tau_iso_2 = Producer(
    name="boosted_tau_iso_2",
    call="event::quantity::Get<float>({df}, {output}, {input}, 1)",
    input=[nanoAOD.boostedTau_rawMVAoldDM2017v2, q.boosteddileptonpair],
    output=[q.boosted_iso_2],
    scopes=["mt", "et", "tt"],
)
boosted_tau_decaymode_2 = Producer(
    name="boosted_taudecaymode_2",
    call="event::quantity::Get<int>({df}, {output}, {input}, 1)",
    input=[nanoAOD.boostedTau_decayMode, q.boosteddileptonpair],
    output=[q.boosted_tau_decaymode_2],
    scopes=["mt", "et", "tt"],
)
isoTauIDFlag_2 = ExtendedVectorProducer(
    name="isoTauIDFlag_2",
    call="""physicsobject::tau::quantity::IDFlag_v12(
        {df},
        {output},
        {input},
        1,
        {iso_boostedtau_id_WPbit})
        """,
    input=[nanoAOD.boostedTau_idMVAoldDM2017v2, q.boosteddileptonpair],
    output="boostedtau_2_iso_id_outputname",
    scopes=["et", "mt", "tt"],
    vec_config="iso_boostedtau_id",
)
antiEleTauIDFlag_2 = ExtendedVectorProducer(
    name="antiEleTauIDFlag_2",
    call="""physicsobject::tau::quantity::IDFlag_v12(
        {df},
        {output},
        {input},
        1,
        {antiele_boostedtau_id_WPbit})
        """,
    input=[nanoAOD.boostedTau_idAntiEle2018, q.boosteddileptonpair],
    output="boostedtau_2_antiele_id_outputname",
    scopes=["et", "mt", "tt"],
    vec_config="antiele_boostedtau_id",
)
antiMuTauIDFlag_2 = ExtendedVectorProducer(
    name="antiMuTauIDFlag_2",
    call="""physicsobject::tau::quantity::IDFlag_v12(
        {df},
        {output},
        {input},
        1,
        {antimu_boostedtau_id_WPbit})
        """,
    input=[nanoAOD.boostedTau_idAntiMu, q.boosteddileptonpair],
    output="boostedtau_2_antimu_id_outputname",
    scopes=["et", "mt", "tt"],
    vec_config="antimu_boostedtau_id",
)

boosted_p4_vis = Producer(
    name="boosted_p4_vis",
    call="lorentzvector::Sum({df}, {output}, {input})",
    input=[q.boosted_p4_1, q.boosted_p4_2],
    output=[q.boosted_p4_vis],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_m_vis = Producer(
    name="boosted_m_vis",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.boosted_p4_vis],
    output=[q.boosted_m_vis],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_pt_vis = Producer(
    name="boosted_pt_vis",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.boosted_p4_vis],
    output=[q.boosted_pt_vis],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_deltaR_ditaupair = Producer(
    name="boosted_deltaR_ditaupair",
    call="quantities::DeltaR({df}, {output}, {input})",
    input=[q.boosted_p4_1, q.boosted_p4_2],
    output=[q.boosted_deltaR_ditaupair],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_mt_1 = Producer(
    name="boosted_mt_1",
    call="quantities::TransverseMass({df}, {output}, {input})",
    input=[q.boosted_p4_1, q.met_p4_recoilcorrected],
    output=[q.boosted_mt_1],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_mt_2 = Producer(
    name="boosted_mt_2",
    call="quantities::TransverseMass({df}, {output}, {input})",
    input=[q.boosted_p4_2, q.met_p4_recoilcorrected],
    output=[q.boosted_mt_2],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)

boosted_p4_tautaubb = Producer(
    name="boosted_p4_tautaubb",
    call="lorentzvector::Sum({df}, {output}, {input})",
    input=[q.boosted_p4_1, q.boosted_p4_2, q.bpair_p4_1_boosted, q.bpair_p4_2_boosted, q.met_p4_boosted_recoilcorrected],
    output=[q.boosted_p4_tautaubb],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_pt_tautaubb = Producer(
    name="boosted_pt_tautaubb",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.boosted_p4_tautaubb],
    output=[q.boosted_pt_tautaubb],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_mass_tautaubb = Producer(
    name="boosted_mass_tautaubb",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.boosted_p4_tautaubb],
    output=[q.boosted_mass_tautaubb],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)

boosted_pt_add = Producer(
    name="boosted_pt_add",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.boosted_p4_add],
    output=[q.boosted_pt_add],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_eta_add = Producer(
    name="boosted_eta_add",
    call="lorentzvector::GetEta({df}, {output}, {input})",
    input=[q.boosted_p4_add],
    output=[q.boosted_eta_add],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_phi_add = Producer(
    name="boosted_phi_add",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.boosted_p4_add],
    output=[q.boosted_phi_add],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)
boosted_mass_add = Producer(
    name="boosted_mass_add",
    call="lorentzvector::GetMass({df}, {output}, {input})",
    input=[q.boosted_p4_add],
    output=[q.boosted_mass_add],
    scopes=["mt", "et", "tt", "em", "ee", "mm"],
)

UnrollboostedMuLV1 = ProducerGroup(
    name="UnrollboostedMuLV1",
    call=None,
    input=None,
    output=None,
    scopes=["mt", "mm"],
    subproducers=[
        boosted_pt_1,
        boosted_eta_1,
        boosted_phi_1,
        boosted_mass_1,
        boosted_muon_dxy_1,
        boosted_muon_dz_1,
        boosted_muon_q_1,
        boosted_muon_iso_1,
        # boosted_muon_is_global_1,
    ],
)
UnrollboostedElLV1 = ProducerGroup(
    name="UnrollboostedElLV1",
    call=None,
    input=None,
    output=None,
    scopes=["et", "ee"],
    subproducers=[
        boosted_pt_1,
        boosted_eta_1,
        boosted_phi_1,
        boosted_mass_1,
        boosted_electron_dxy_1,
        boosted_electron_dz_1,
        boosted_electron_q_1,
        boosted_electron_iso_1,
    ],
)
UnrollboostedTauLV1 = ProducerGroup(
    name="UnrollboostedTauLV1",
    call=None,
    input=None,
    output=None,
    scopes=["tt"],
    subproducers=[
        boosted_pt_1,
        boosted_eta_1,
        boosted_phi_1,
        boosted_mass_1,
        boosted_tau_q_1,
        boosted_tau_iso_1,
        boosted_tau_decaymode_1,
        isoTauIDFlag_1,
        antiEleTauIDFlag_1,
        antiMuTauIDFlag_1,
    ],
)
UnrollboostedTauLV2 = ProducerGroup(
    name="UnrollboostedTauLV2",
    call=None,
    input=None,
    output=None,
    scopes=["et", "mt", "tt"],
    subproducers=[
        boosted_pt_2,
        boosted_eta_2,
        boosted_phi_2,
        boosted_mass_2,
        boosted_tau_q_2,
        boosted_tau_iso_2,
        boosted_tau_decaymode_2,
        isoTauIDFlag_2,
        antiEleTauIDFlag_2,
        antiMuTauIDFlag_2,
    ],
)
boostedMTDiTauPairQuantities = ProducerGroup(
    name="boostedMTDiTauPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=["mt"],
    subproducers=[
        UnrollboostedMuLV1,
        UnrollboostedTauLV2,
        boosted_tau_decaymode_1_notau,
        boosted_p4_vis,
        boosted_m_vis,
        boosted_pt_vis,
        boosted_deltaR_ditaupair,
        boosted_mt_1,
        boosted_mt_2,
        boosted_p4_tautaubb,
        boosted_pt_tautaubb,
        boosted_mass_tautaubb,
        # boosted_pt_add,
        # boosted_eta_add,
        # boosted_phi_add,
        # boosted_mass_add,
    ],
)
boostedETDiTauPairQuantities = ProducerGroup(
    name="boostedETDiTauPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=["et"],
    subproducers=[
        UnrollboostedElLV1,
        UnrollboostedTauLV2,
        boosted_tau_decaymode_1_notau,
        boosted_p4_vis,
        boosted_m_vis,
        boosted_pt_vis,
        boosted_deltaR_ditaupair,
        boosted_mt_1,
        boosted_mt_2,
        boosted_p4_tautaubb,
        boosted_pt_tautaubb,
        boosted_mass_tautaubb,
        # boosted_pt_add,
        # boosted_eta_add,
        # boosted_phi_add,
        # boosted_mass_add,
    ],
)
boostedTTDiTauPairQuantities = ProducerGroup(
    name="boostedTTDiTauPairQuantities",
    call=None,
    input=None,
    output=None,
    scopes=["tt"],
    subproducers=[
        UnrollboostedTauLV1,
        UnrollboostedTauLV2,
        boosted_p4_vis,
        boosted_m_vis,
        boosted_pt_vis,
        boosted_deltaR_ditaupair,
        boosted_mt_1,
        boosted_mt_2,
        boosted_p4_tautaubb,
        boosted_pt_tautaubb,
        boosted_mass_tautaubb,
    ],
)