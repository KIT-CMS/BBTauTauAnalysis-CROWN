from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from analysis_configurations.quantities import nanoAODv12_run3
from code_generation.producer import Producer, ProducerGroup

from ..constants import GLOBAL_SCOPES, SCOPES, ERAS_RUN2, ERAS_RUN3
from ..helpers import era_producer_groups, get_for_era

#
# HELPER FUNCTIONS
#


def met_cov_producers(
    name: str,
    input_quantities: dict[str, str],
    output_quantities: dict[str, str],
    scopes: list[str],
):
    """
    Generic function that generates a producer group for MET covariance matrix
    elements.

    The `input_quantities` dictionary must contain the input `NANOAOD` columns:
    - `met_cov_xx`: The $xx$ component of the MET covariance matrix.
    - `met_cov_xy`: The $xy$ component of the MET covariance matrix.
    - `met_cov_yy`: The $yy$ component of the MET covariance matrix.

    The `output_quantities` dictionary must contain the output columns in the
    NTuple:

    - `met_cov_00`: The $xx$ component of the MET covariance matrix.
    - `met_cov_01`: The $xy$ component of the MET covariance matrix.
    - `met_cov_10`: The $xy$ component of the MET covariance matrix.
    - `met_cov_11`: The $yy$ component of the MET covariance matrix.
    """

    # Get the input and output quantities
    met_cov_xx = input_quantities["met_cov_xx"]
    met_cov_xy = input_quantities["met_cov_xy"]
    met_cov_yy = input_quantities["met_cov_yy"]
    met_cov_00 = output_quantities["met_cov_00"]
    met_cov_01 = output_quantities["met_cov_01"]
    met_cov_10 = output_quantities["met_cov_10"]
    met_cov_11 = output_quantities["met_cov_11"]

    # Create the MET covariance matrix producers
    producers = []
    for input, output, subproducer_name in [
        (met_cov_xx, met_cov_00, "Cov00"),
        (met_cov_xy, met_cov_01, "Cov01"),
        (met_cov_xy, met_cov_10, "Cov10"),
        (met_cov_yy, met_cov_11, "Cov11"),
    ]:
        producers.append(
            Producer(
                name=f"{name}_{subproducer_name}",
                call="event::quantity::Rename<float>({df}, {output}, {input})",
                input=[input],
                output=[output],
                scopes=scopes,
            )
        )

    # Create a producer group for the MET covariance matrix elements
    producer_group = ProducerGroup(
        name=name,
        call=None,
        input=None,
        output=None,
        scopes=scopes,
        subproducers=producers,
    )

    return producer_group


#
# UNCORRECTED MET QUANTITIES
#

# PF MET covariance matrix elements
# - In nanoAODv12, the MET covariance matrix elements are only available for PFMET.
# - In nanoAODv15, the MET covariance matrix elements can be taken from PuppiMET.
MetCov = {
    tuple(ERAS_RUN2) + ("2022preEE", "2022postEE", "2023preBPix", "2023postBPix"): met_cov_producers(
        name="MetCov",
        input_quantities={
            "met_cov_xx": nanoAODv12_run3.MET_covXX,
            "met_cov_xy": nanoAODv12_run3.MET_covXY,
            "met_cov_yy": nanoAODv12_run3.MET_covYY,
        },
        output_quantities={
            "met_cov_00": q.metcov00,
            "met_cov_01": q.metcov01,
            "met_cov_10": q.metcov10,
            "met_cov_11": q.metcov11,
        },
        scopes=GLOBAL_SCOPES,
    ),
    ("2024", "2025"): met_cov_producers(
        name="MetCov",
        input_quantities={
            "met_cov_xx": nanoAOD.PuppiMET_covXX,
            "met_cov_xy": nanoAOD.PuppiMET_covXY,
            "met_cov_yy": nanoAOD.PuppiMET_covYY,
        },
        output_quantities={
            "met_cov_00": q.metcov00,
            "met_cov_01": q.metcov01,
            "met_cov_10": q.metcov10,
            "met_cov_11": q.metcov11,
        },
        scopes=GLOBAL_SCOPES,
    ),
}

# MET covariance for the isolated SM 2018-v15 path. NanoAOD v15 (2018 UL
# reprocessing) renames the PF MET collection MET_* -> PFMET_* and thus drops
# the v9/v12 MET_covXX/XY/YY branches the Run-2 MetCov reads; the covariance is
# instead available on PuppiMET (the collection this analysis already uses for
# the MET four-vector). Output quantities are identical to the era-selected
# MetCov -- only the input branches change -- so nothing downstream is affected.
MetCovSM2018V15 = met_cov_producers(
    name="MetCov",
    input_quantities={
        "met_cov_xx": nanoAOD.PuppiMET_covXX,
        "met_cov_xy": nanoAOD.PuppiMET_covXY,
        "met_cov_yy": nanoAOD.PuppiMET_covYY,
    },
    output_quantities={
        "met_cov_00": q.metcov00,
        "met_cov_01": q.metcov01,
        "met_cov_10": q.metcov10,
        "met_cov_11": q.metcov11,
    },
    scopes=GLOBAL_SCOPES,
)

# PuppiMET vector without recoil corrections and missing propagation of changes
# in lepton and jet energy scale
MetVectorUncorrected = Producer(
    name="MetVectorUncorrected",
    call="lorentzvector::BuildMET({df}, {output}, {input})",
    input=[nanoAOD.PuppiMET_pt, nanoAOD.PuppiMET_phi],
    output=[q.met_p4_uncorrected],
    scopes=GLOBAL_SCOPES,
)

# Scalar sum of transverse energy
MetSumEt = Producer(
    name="MetSumEt",
    call="event::quantity::Rename<float>({df}, {output}, {input})",
    input=[nanoAOD.PuppiMET_sumEt],
    output=[q.metSumEt],
    scopes=GLOBAL_SCOPES,
)

# Uncorrected PuppiMET pt
MetPtUncorrected = Producer(
    name="MetPtUncorrected",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.met_p4_uncorrected],
    output=[q.met_uncorrected],
    scopes=GLOBAL_SCOPES,
)

# Uncorrected PuppiMET phi
MetPhiUncorrected = Producer(
    name="MetPhiUncorrected",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.met_p4_uncorrected],
    output=[q.metphi_uncorrected],
    scopes=GLOBAL_SCOPES,
)

# Raw PuppiMET vector
MetVectorRaw = Producer(
    name="MetVectorRaw",
    call="lorentzvector::BuildMET({df}, {output}, {input})",
    input=[nanoAOD.RawPuppiMET_pt, nanoAOD.RawPuppiMET_phi],
    output=[q.met_p4_raw],
    scopes=GLOBAL_SCOPES,
)

# Raw scalar sum of transverse energy
MetSumEtRaw = Producer(
    name="MetSumEtRaw",
    call="event::quantity::Rename<float>({df}, {output}, {input})",
    input=[nanoAOD.RawPuppiMET_sumEt],
    output=[q.metSumEt_raw],
    scopes=GLOBAL_SCOPES,
)

# Raw PuppiMET pt
MetPtRaw = Producer(
    name="MetPtRaw",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.met_p4_raw],
    output=[q.met_raw],
    scopes=GLOBAL_SCOPES,
)

# Raw PuppiMET phi
MetPhiRaw = Producer(
    name="MetPhiRaw",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.met_p4_raw],
    output=[q.metphi_raw],
    scopes=GLOBAL_SCOPES,
)

# Propagate changes due to JEC to MET
# - In Run 2, the PuppiMET is already accounted for the changes due to JEC
#   correctly. Here, we just need to propagate changes in the JEC (e.g., due
#   to shifts) to the MET. The input to this function is the "uncorrected"
#   PuppiMET from nanoAOD.
# - In Run 3, we need to apply Type-I MET corrections to propagate the effect
#   of JEC to the raw PuppiMET.
MetJetCorrection = {
    tuple(ERAS_RUN2): Producer(
        name="MetJetCorrection",
        call="""
        physicsobject::PropagateToMET(
            {df},
            {output},
            {input},
            {propagate_jets_to_met},
            {t1jet_min_pt}
        )
        """,
        input=[
            q.met_p4_uncorrected,
            q.Jet_correctedPt,
            nanoAOD.Jet_eta,
            nanoAOD.Jet_phi,
            q.Jet_correctedMass,
            nanoAOD.Jet_pt,
            nanoAOD.Jet_eta,
            nanoAOD.Jet_phi,
            nanoAOD.Jet_mass,
        ],
        output=[q.met_p4_jetcorrected],
        scopes=GLOBAL_SCOPES,
    ),
    tuple(ERAS_RUN3): Producer(
        name="MetJetCorrection",
        call="""
        met::Type1Correction(
            {df},
            {output},
            {input},
            {t1jet_min_pt},
            {t1jet_max_abs_eta},
            {t1jet_max_em_ef}
        )
        """,
        input=[
            q.met_p4_raw,
            q.Type1Jet_l1Pt,
            q.Type1Jet_correctedPt,
            q.Type1Jet_eta,
            q.Type1Jet_phi,
            q.Type1Jet_EmEF,
        ],
        output=[q.met_p4_jetcorrected],
        scopes=GLOBAL_SCOPES,
    ),
}

# MET functions running in the global scope
MetGlobal = era_producer_groups(
    "MetGlobal",
    [
        MetCov,
        MetVectorUncorrected,
        MetPtUncorrected,
        MetPhiUncorrected,
        MetSumEt,
        MetVectorRaw,
        MetPtRaw,
        MetPhiRaw,
        MetSumEtRaw,
        MetJetCorrection,
    ],
    GLOBAL_SCOPES,
)

# MetGlobal for the isolated SM 2018-v15 path: identical to the Run-2 MetGlobal
# group (v15 ships all of its PuppiMET / RawPuppiMET inputs and the Run-2
# PropagateToMET jet correction reads only branches present in v15) except the
# covariance is taken from PuppiMET, because v15 drops the v9/v12 PFMET
# covariance branches. Selected in common_config for use_sm_2018_v15_inputs;
# NMSSM 2018 keeps the era-selected Run-2 MetGlobal.
MetGlobalSM2018V15 = ProducerGroup(
    name="MetGlobal",
    call=None,
    input=None,
    output=None,
    scopes=GLOBAL_SCOPES,
    subproducers=[
        MetCovSM2018V15,
        MetVectorUncorrected,
        MetPtUncorrected,
        MetPhiUncorrected,
        MetSumEt,
        MetVectorRaw,
        MetPtRaw,
        MetPhiRaw,
        MetSumEtRaw,
        get_for_era(MetJetCorrection, "2018"),
    ],
)

# Propagate changes in the lepton energy scales to MET
MetLeptonCorrection = Producer(
    name="MetLeptonCorrection",
    call="""
    lorentzvector::PropagateToMET(
        {df},
        {output},
        {input},
        {propagate_leptons_to_met}
    )
    """,
    input=[
        q.met_p4_jetcorrected,
        q.p4_1_uncorrected,
        q.p4_2_uncorrected,
        q.p4_1,
        q.p4_2,
    ],
    output=[q.met_p4_leptoncorrected],
    scopes=SCOPES,
)

# Recoil correction evaluation via correctionlib
MetRecoilCorrection = {
    tuple(ERAS_RUN2): Producer(
        name="RecoilCorrectionMet",
        call="""
        met::RecoilCorrection(
            {df},
            {output},
            {input},
            "{recoil_correction_file}",
            "{recoil_systematics_file}",
            {apply_recoil_correction},
            {apply_recoil_resolution_systematic},
            {apply_recoil_response_systematic},
            {recoil_systematic_shift_up},
            {recoil_systematic_shift_down},
            {is_wjets}
        )
        """,
        input=[
            q.met_p4_leptoncorrected,
            q.gen_boson_p4,
            q.gen_vis_boson_p4,
            q.Jet_correctedPt,
        ],
        output=[q.met_p4_recoilcorrected],
        scopes=SCOPES,
    ),
    tuple(ERAS_RUN3): Producer(
        name="RecoilCorrectionMet",
        call=(
            """
            met::RecoilCorrection(
                {df},
                correctionManager,
                {output},
                {input},
                "{recoil_correction_file}",
                "{recoil_correction_method}",
                "{recoil_correction_order}",
                "{recoil_correction_variation}",
                {apply_recoil_correction}
            )
            """
        ),
        input=[
            q.met_p4_leptoncorrected,
            q.gen_boson_p4,
            q.gen_vis_boson_p4,
            q.n_jets,
        ],
        output=[q.met_p4_recoilcorrected],
        scopes=SCOPES,
    ),
}

# MET functions running in the scopes
MetScopes = era_producer_groups(
    "MetScopes",
    [
        MetLeptonCorrection,
        MetRecoilCorrection,
    ],
    SCOPES,
)

# Dummy producer to rename the MET if recoil corrections are applied to the
# sample
RenameMet = Producer(
    name="RenameMet",
    call="""
    event::quantity::Rename<ROOT::Math::PtEtaPhiMVector>(
        {df},
        {output},
        {input}
    )
    """,
    input=[q.met_p4_jetcorrected],
    output=[q.met_p4_recoilcorrected],
    scopes=SCOPES,
)

# Final MET pt
MetPt = Producer(
    name="MetPt",
    call="lorentzvector::GetPt({df}, {output}, {input})",
    input=[q.met_p4_recoilcorrected],
    output=[q.met],
    scopes=SCOPES,
)

# Final MET phi
MetPhi = Producer(
    name="MetPhi",
    call="lorentzvector::GetPhi({df}, {output}, {input})",
    input=[q.met_p4_recoilcorrected],
    output=[q.metphi],
    scopes=SCOPES,
)

# Producer group for final MET quantities
MetQuantities = ProducerGroup(
    name="MetQuantities",
    call=None,
    input=None,
    output=None,
    scopes=SCOPES,
    subproducers=[
        MetPt,
        MetPhi,
    ],
)

