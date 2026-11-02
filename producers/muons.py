"""
Producers for muon object selections and vetoes.
"""

from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from code_generation.producer import Producer

from ..constants import ERAS_RUN2, ERAS_RUN3, MM_SCOPES, MT_SCOPES, MUON_SCOPES, GLOBAL_SCOPES, SCOPES



#
# ENERGY SCALE CORRECTIONS
#

# Muon pt correction on data and MC events
MuonPtCorrection = {
    # The Run 2 payloads provide no muon scale and resolution correction
    tuple(ERAS_RUN2): Producer(
        name="MuonPtCorrection",
        call="event::quantity::Rename<ROOT::RVec<float>>({df}, {output}, {input})",
        input=[nanoAOD.Muon_pt],
        output=[q.Muon_pt_corrected],
        scopes=GLOBAL_SCOPES,
    ),
    tuple(ERAS_RUN3): Producer(
        name="MuonPtCorrection",
        call='physicsobject::muon::PtCorrection({df}, correctionManager, {output}, {input}, 20.0, "{muon_es_file}", "{muon_es_variation}", {is_data})',
        input=[
            nanoAOD.Muon_pt,
            nanoAOD.Muon_eta,
            nanoAOD.Muon_phi,
            nanoAOD.Muon_charge,
            nanoAOD.Muon_nTrackerLayers,
            nanoAOD.luminosityBlock,
            nanoAOD.event,
        ],
        output=[q.Muon_pt_corrected],
        scopes=GLOBAL_SCOPES,
    ),
}


#
# OBJECT SELECTION
#


# loose muons (mainly used to evaluate veto masks)
BaseMuons = Producer(
    name="BaseMuons",
    call="xyh::object_selection::muon({df}, {output}, {input}, \"{loose_muon_id}\", {loose_muon_min_pt}, {loose_muon_max_abs_eta}, {loose_muon_max_abs_dxy}, {loose_muon_max_abs_dz}, {loose_muon_max_iso})",
    input=[
        q.Muon_pt_corrected,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_dxy,
        nanoAOD.Muon_dz,
        nanoAOD.Muon_pfRelIso04_all,
    ],
    output=[q.base_muons_mask],
    scopes=GLOBAL_SCOPES,
)

# tight muons (final state tau candidates)
GoodMuons = Producer(
    name="GoodMuons",
    call="xyh::object_selection::muon({df}, {output}, {input}, \"{tight_muon_id}\", {tight_muon_min_pt}, {tight_muon_max_abs_eta}, {tight_muon_max_abs_dxy}, {tight_muon_max_abs_dz}, {tight_muon_max_iso})",
    input=[
        q.Muon_pt_corrected,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_dxy,
        nanoAOD.Muon_dz,
        nanoAOD.Muon_pfRelIso04_all,
    ],
    output=[q.good_muons_mask],
    scopes=MUON_SCOPES,
)

# count number of selected muons
NumberOfGoodMuons = Producer(
    name="NumberOfGoodMuons",
    call="physicsobject::Count({df}, {output}, {input})",
    input=[q.good_muons_mask],
    output=[q.nmuons],
    scopes=MUON_SCOPES,
)


#
# EXTRA-MUON VETO
#


# mask for veto muons, excluding the selected muon from the di-tau pair for the resolved selection
VetoMuons = Producer(
    name="VetoMuons",
    call="physicsobject::VetoSingleObject({df}, {output}, {input}, {muon_index_in_pair})",
    input=[q.base_muons_mask, q.dileptonpair],
    output=[q.veto_muons_mask],
    scopes=MUON_SCOPES,
)

# mask for veto muons, excluding the selected muon from the di-tau pair for the boosted selection
VetoMuons_boosted = Producer(
    name="VetoMuons_boosted",
    call="physicsobject::VetoSingleObject({df}, {output}, {input}, {muon_index_in_pair})",
    input=[q.base_muons_mask, q.boosteddileptonpair],
    output=[q.veto_muons_boosted_mask],
    scopes=MUON_SCOPES,
)

# mask for veto muons, excluding the selected muons from the di-tau pair (mumu) for the boosted selection
VetoSecondMuon = Producer(
    name="VetoSecondMuon",
    call="physicsobject::VetoSingleObject({df}, {output}, {input}, {second_muon_index_in_pair})",
    input=[q.veto_muons_mask, q.dileptonpair],
    output=[q.veto_muons_mask_2],
    scopes=MM_SCOPES,
)

# extra-muon veto for the different channels for the resolved selection
ExtraMuonsVeto = Producer(
    name="ExtraMuonsVeto",
    call="physicsobject::Veto({df}, {output}, {input})",
    input={
        "et": [q.base_muons_mask],
        "mt": [q.veto_muons_mask],
        "tt": [q.base_muons_mask],
        "ee": [q.base_muons_mask],
        "mm": [q.veto_muons_mask_2],
        "em": [q.veto_muons_mask],
    },
    output=[q.muon_veto_flag],
    scopes=SCOPES,
)

# extra-muon veto for the different channels for the boosted selection
BoostedExtraMuonsVeto = Producer(
    name="BoostedExtraMuonsVeto",
    call="physicsobject::Veto({df}, {output}, {input})",
    input={
        "mt": [q.veto_muons_boosted_mask],
    },
    output=[q.boosted_muon_veto_flag],
    scopes=MT_SCOPES,
)


#
# DI-MUON VETO
#

DiMuonVeto = Producer(
    name="DiMuonVeto",
    call="xyh::vetoes::dimuon({df}, {output}, {input}, {dimu_muon_min_pt}, {dimu_muon_max_abs_eta}, {dimu_muon_max_iso}, {dimu_muon_max_abs_dxy}, {dimu_muon_max_abs_dz}, {dimu_muon_min_delta_r})",
    input=[
        q.Muon_pt_corrected,
        nanoAOD.Muon_eta,
        nanoAOD.Muon_phi,
        nanoAOD.Muon_pfRelIso04_all,
        nanoAOD.Muon_dxy,
        nanoAOD.Muon_dz,
        nanoAOD.Muon_isPFcand,
        nanoAOD.Muon_isTracker,
        nanoAOD.Muon_isGlobal,
        nanoAOD.Muon_charge,
    ],
    output=[q.dimuon_veto],
    scopes=GLOBAL_SCOPES,
)
