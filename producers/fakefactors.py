from ..quantities import output as q
from ..quantities import nanoAOD as nanoAOD
from code_generation.producer import Producer

from ..constants import FH_SCOPES, SL_SCOPES

# ------------------------------------------------------------------------------
# Fake factor inputs for semileptonic channels
# ------------------------------------------------------------------------------

FakeFactorSemileptonicQCDInput = Producer(
    name="FakeFactorSemileptonicQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_2,
        q.n_jets,
    ],
    output=[q.ff_input_qcd],
    scopes=SL_SCOPES,
)

FakeFactorSemileptonicTTInput = Producer(
    name="FakeFactorSemileptonicTTInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_2,
        q.n_jets,
    ],
    output=[q.ff_input_tt],
    scopes=SL_SCOPES,
)

FakeFactorSemileptonicFractionInput = Producer(
    name="FakeFactorSemileptonicFractionInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.m_vis,
        q.n_bjets,
    ],
    output=[q.ff_input_fraction],
    scopes=SL_SCOPES,
)

FakeFactorDRSRCorrectionSemileptonicQCDInput = Producer(
    name="FakeFactorDRSRCorrectionSemileptonicQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.m_vis,
    ],
    output=[q.ff_corr_dr_sr_input_qcd],
    scopes=SL_SCOPES,
)

FakeFactorClosureCorrectionSemileptonicQCDInput = Producer(
    name="FakeFactorClosureCorrectionSemileptonicQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_1,
        q.tau_decaymode_2,
        q.mass_2,
    ],
    output=[q.ff_corr_closure_input_qcd],
    scopes=SL_SCOPES,
)

FakeFactorClosureCorrectionSemileptonicTTInput = Producer(
    name="FakeFactorClosureCorrectionSemileptonicTTInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_1,
        q.tau_decaymode_2,
        q.mass_2,
    ],
    output=[q.ff_corr_closure_input_tt],
    scopes=SL_SCOPES,
)

# ------------------------------------------------------------------------------
# Fake factor inputs for fullhadronic channel
# ------------------------------------------------------------------------------

FakeFactorFullhadronicLeadingQCDInput = Producer(
    name="FakeFactorFullhadronicLeadingQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_1,
        q.n_jets,
    ],
    output=[q.ff_1_input_qcd],
    scopes=FH_SCOPES,
)

FakeFactorFullhadronicLeadingTTInput = Producer(
    name="FakeFactorFullhadronicLeadingTTInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_1,
        q.n_jets,
    ],
    output=[q.ff_1_input_tt],
    scopes=FH_SCOPES,
)

FakeFactorFullhadronicLeadingFractionInput = Producer(
    name="FakeFactorFullhadronicLeadingFractionInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.m_vis,
        q.n_bjets,
    ],
    output=[q.ff_1_input_fraction],
    scopes=FH_SCOPES,
)

FakeFactorDRSRCorrectionFullhadronicLeadingQCDInput = Producer(
    name="FakeFactorDRSRCorrectionFullhadronicLeadingQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.m_vis,
    ],
    output=[q.ff_1_corr_dr_sr_input_qcd],
    scopes=FH_SCOPES,
)

FakeFactorClosureCorrectionFullhadronicLeadingQCDInput = Producer(
    name="FakeFactorClosureCorrectionFullhadronicLeadingQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_2,
        q.tau_decaymode_1,
        q.tau_decaymode_2,
        q.mass_1,
        q.mass_2,
    ],
    output=[q.ff_1_corr_closure_input_qcd],
    scopes=FH_SCOPES,
)

FakeFactorClosureCorrectionFullhadronicLeadingTTInput = Producer(
    name="FakeFactorClosureCorrectionFullhadronicLeadingTTInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_2,
        q.tau_decaymode_1,
        q.tau_decaymode_2,
        q.mass_1,
        q.mass_2,
    ],
    output=[q.ff_1_corr_closure_input_tt],
    scopes=FH_SCOPES,
)

FakeFactorFullhadronicSubleadingQCDInput = Producer(
    name="FakeFactorFullhadronicSubleadingQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_2,
        q.n_jets,
    ],
    output=[q.ff_2_input_qcd],
    scopes=FH_SCOPES,
)

FakeFactorFullhadronicSubleadingTTInput = Producer(
    name="FakeFactorFullhadronicSubleadingTTInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_2,
        q.n_jets,
    ],
    output=[q.ff_2_input_tt],
    scopes=FH_SCOPES,
)

FakeFactorFullhadronicSubleadingFractionInput = Producer(
    name="FakeFactorFullhadronicSubleadingFractionInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.m_vis,
        q.n_bjets,
    ],
    output=[q.ff_2_input_fraction],
    scopes=FH_SCOPES,
)

FakeFactorDRSRCorrectionFullhadronicSubleadingQCDInput = Producer(
    name="FakeFactorDRSRCorrectionFullhadronicSubleadingQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.m_vis,
    ],
    output=[q.ff_2_corr_dr_sr_input_qcd],
    scopes=FH_SCOPES,
)

FakeFactorClosureCorrectionFullhadronicSubleadingQCDInput = Producer(
    name="FakeFactorClosureCorrectionFullhadronicSubleadingQCDInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[
        q.pt_1,
        q.tau_decaymode_2,
        q.tau_decaymode_1,
        q.mass_2,
        q.mass_1,
    ],
    output=[q.ff_2_corr_closure_input_qcd],
    scopes=FH_SCOPES,
)

FakeFactorClosureCorrectionFullhadronicSubleadingTTInput = Producer(
    name="FakeFactorClosureCorrectionFullhadronicSubleadingTTInput",
    call="""
    fakefactors::BuildFloatVector(
        {df},
        {output},
        {vec_open}{input}{vec_close}
    )
    """,
    input=[

        q.pt_1,
        q.tau_decaymode_2,
        q.tau_decaymode_1,
        q.mass_2,
        q.mass_1,
    ],
    output=[q.ff_2_corr_closure_input_tt],
    scopes=FH_SCOPES,
)

# ------------------------------------------------------------------------------
# Fake factors for semileptonic channels
# ------------------------------------------------------------------------------

# Raw fake factor without any corrections applied
RawFakeFactorSemileptonic = Producer(
    name="RawFakeFactorSemileptonic",
    call="""
    fakefactors::xyh::RawFakeFactorSemileptonic(
        {df},
        correctionManager,
        {output},
        {input},
        "{ff_file}",
        "{ff_qcd_name}",
        "{ff_tt_name}",
        "{ff_fraction_name}",
        "{ff_qcd_variation}",
        "{ff_tt_variation}",
        "{ff_fraction_variation}"
    )
    """,
    input=[
        q.ff_input_qcd,
        q.ff_input_tt,
        q.ff_input_fraction,
    ],
    output=[q.fake_factor_raw],
    scopes=SL_SCOPES,
)

# Fake factor including DR/SR and closure corrections
FakeFactorSemileptonic = Producer(
    name="FakeFactorSemileptonic",
    call="""
    fakefactors::xyh::FakeFactorSemileptonic(
        {df},
        correctionManager,
        {output},
        {input},
        "{ff_file}",
        "{ff_qcd_name}",
        "{ff_tt_name}",
        "{ff_fraction_name}",
        "{ff_corr_file}",
        "{ff_corr_dr_sr_qcd_name}",
        "{ff_corr_closure_qcd_name}",
        "{ff_corr_closure_tt_name}",
        "{ff_qcd_variation}",
        "{ff_tt_variation}",
        "{ff_fraction_variation}",
        "{ff_dr_sr_corr_qcd_variation}",
        "{ff_closure_corr_qcd_variation}",
        "{ff_closure_corr_tt_variation}"
    )
    """,
    input=[
        q.ff_input_qcd,
        q.ff_input_tt,
        q.ff_input_fraction,
        q.ff_corr_dr_sr_input_qcd,
        q.ff_corr_closure_input_qcd,
        q.ff_corr_closure_input_tt,
    ],
    output=[q.fake_factor],
    scopes=SL_SCOPES,
)

# ------------------------------------------------------------------------------
# Fake factors for fullhadronic channel
# ------------------------------------------------------------------------------

# Raw fake factor of the leading tau fake without any corrections applied
RawFakeFactorFullhadronicLeading = Producer(
    name="RawFakeFactorFullhadronicLeading",
    call="""
    fakefactors::xyh::RawFakeFactorSemileptonic(
        {df},
        correctionManager,
        {output},
        {input},
        "{ff_file}",
        "{ff_1_qcd_name}",
        "{ff_1_tt_name}",
        "{ff_1_fraction_name}",
        "{ff_1_qcd_variation}",
        "{ff_1_tt_variation}",
        "{ff_1_fraction_variation}"
    )
    """,
    input=[
        q.ff_1_input_qcd,
        q.ff_1_input_tt,
        q.ff_1_input_fraction,
    ],
    output=[q.fake_factor_1_raw],
    scopes=FH_SCOPES,
)

# Fake factor of the leading tau fake including DR/SR and closure corrections
FakeFactorFullhadronicLeading = Producer(
    name="FakeFactorFullhadronicLeading",
    call="""
    fakefactors::xyh::FakeFactorSemileptonic(
        {df},
        correctionManager,
        {output},
        {input},
        "{ff_file}",
        "{ff_1_qcd_name}",
        "{ff_1_tt_name}",
        "{ff_1_fraction_name}",
        "{ff_corr_file}",
        "{ff_1_corr_dr_sr_qcd_name}",
        "{ff_1_corr_closure_qcd_name}",
        "{ff_1_corr_closure_tt_name}",
        "{ff_1_qcd_variation}",
        "{ff_1_tt_variation}",
        "{ff_1_fraction_variation}",
        "{ff_1_dr_sr_corr_qcd_variation}",
        "{ff_1_closure_corr_qcd_variation}",
        "{ff_1_closure_corr_tt_variation}"
    )
    """,
    input=[
        q.ff_1_input_qcd,
        q.ff_1_input_tt,
        q.ff_1_input_fraction,
        q.ff_1_corr_dr_sr_input_qcd,
        q.ff_1_corr_closure_input_qcd,
        q.ff_1_corr_closure_input_tt,
    ],
    output=[q.fake_factor_1],
    scopes=FH_SCOPES,
)

# Raw fake factor of the subleading tau fake without any corrections applied
RawFakeFactorFullhadronicSubleading = Producer(
    name="RawFakeFactorFullhadronicSubleading",
    call="""
    fakefactors::xyh::RawFakeFactorSemileptonic(
        {df},
        correctionManager,
        {output},
        {input},
        "{ff_file}",
        "{ff_2_qcd_name}",
        "{ff_2_tt_name}",
        "{ff_2_fraction_name}",
        "{ff_2_qcd_variation}",
        "{ff_2_tt_variation}",
        "{ff_2_fraction_variation}"
    )
    """,
    input=[
        q.ff_2_input_qcd,
        q.ff_2_input_tt,
        q.ff_2_input_fraction,
    ],
    output=[q.fake_factor_2_raw],
    scopes=FH_SCOPES,
)

# Fake factor of the subleading tau fake including DR/SR and closure corrections
FakeFactorFullhadronicSubleading = Producer(
    name="FakeFactorFullhadronicSubleading",
    call="""
    fakefactors::xyh::FakeFactorSemileptonic(
        {df},
        correctionManager,
        {output},
        {input},
        "{ff_file}",
        "{ff_2_qcd_name}",
        "{ff_2_tt_name}",
        "{ff_2_fraction_name}",
        "{ff_corr_file}",
        "{ff_2_corr_dr_sr_qcd_name}",
        "{ff_2_corr_closure_qcd_name}",
        "{ff_2_corr_closure_tt_name}",
        "{ff_2_qcd_variation}",
        "{ff_2_tt_variation}",
        "{ff_2_fraction_variation}",
        "{ff_2_dr_sr_corr_qcd_variation}",
        "{ff_2_closure_corr_qcd_variation}",
        "{ff_2_closure_corr_tt_variation}"
    )
    """,
    input=[
        q.ff_2_input_qcd,
        q.ff_2_input_tt,
        q.ff_2_input_fraction,
        q.ff_2_corr_dr_sr_input_qcd,
        q.ff_2_corr_closure_input_qcd,
        q.ff_2_corr_closure_input_tt,
    ],
    output=[q.fake_factor_2],
    scopes=FH_SCOPES,
)

# ------------------------------------------------------------------------------
# Fake factors for NMSSM analysis (old)
# ------------------------------------------------------------------------------

RawFakeFactors_nmssm_lt = Producer(
    name="RawFakeFactors_nmssm_lt",
    call='fakefactors::raw_fakefactor_nmssm_lt({df}, {output}, {input}, "{qcd_ff_variation}", "{wjets_ff_variation}", "{ttbar_ff_variation}", "{fraction_variation}", "{ff_file}")',
    input=[
        q.pt_2,
        q.n_jets,
        q.mt_1,
        q.n_bjets,
    ],
    output=[q.raw_fake_factor],
    scopes=["mt", "et"],
)
RawFakeFactors_nmssm_boosted_lt = Producer(
    name="RawFakeFactors_nmssm_boosted_lt",
    call='fakefactors::raw_fakefactor_nmssm_lt({df}, {output}, {input}, "{qcd_ff_variation}", "{wjets_ff_variation}", "{ttbar_ff_variation}", "{fraction_variation}", "{ff_file_boosted}")',
    input=[
        q.boosted_pt_2,
        q.n_jets_boosted,
        q.boosted_mt_1,
        q.n_bjets_boosted,
    ],
    output=[q.raw_fake_factor_boosted],
    scopes=["mt", "et"],
)
RawFakeFactors_nmssm_tt_1 = Producer(
    name="RawFakeFactors_nmssm_tt_1",
    call='fakefactors::raw_fakefactor_nmssm_tt({df}, {output}, 0, {input}, "{qcd_ff_variation}", "{ttbar_ff_variation}", "{fraction_variation}", "{ff_file}")',
    input=[
        q.pt_1,
        q.pt_2,
        q.n_jets,
        q.m_vis,
        q.n_bjets,
    ],
    output=[q.raw_fake_factor_1],
    scopes=["tt"],
)
RawFakeFactors_nmssm_tt_2 = Producer(
    name="RawFakeFactors_nmssm_tt_2",
    call='fakefactors::raw_fakefactor_nmssm_tt({df}, {output}, 1, {input}, "{qcd_subleading_ff_variation}", "{ttbar_subleading_ff_variation}", "{fraction_subleading_variation}", "{ff_file}")',
    input=[
        q.pt_1,
        q.pt_2,
        q.n_jets,
        q.m_vis,
        q.n_bjets,
    ],
    output=[q.raw_fake_factor_2],
    scopes=["tt"],
)
RawFakeFactors_nmssm_tt_boosted_1 = Producer(
    name="RawFakeFactors_nmssm_tt_boosted_1",
    call='fakefactors::raw_fakefactor_nmssm_tt({df}, {output}, 0, {input}, "{qcd_ff_variation}", "{ttbar_ff_variation}", "{fraction_variation}", "{ff_file_boosted}")',
    input=[
        q.boosted_pt_1,
        q.boosted_pt_2,
        q.n_jets_boosted,
        q.boosted_m_vis,
        q.n_bjets_boosted,
    ],
    output=[q.raw_fake_factor_boosted_1],
    scopes=["tt"],
)
RawFakeFactors_nmssm_tt_boosted_2 = Producer(
    name="RawFakeFactors_nmssm_tt_boosted_2",
    call='fakefactors::raw_fakefactor_nmssm_tt({df}, {output}, 1, {input}, "{qcd_subleading_ff_variation}", "{ttbar_subleading_ff_variation}", "{fraction_subleading_variation}", "{ff_file_boosted}")',
    input=[
        q.boosted_pt_1,
        q.boosted_pt_2,
        q.n_jets_boosted,
        q.boosted_m_vis,
        q.n_bjets_boosted,
    ],
    output=[q.raw_fake_factor_boosted_2],
    scopes=["tt"],
)

FakeFactors_nmssm_lt = Producer(
    name="FakeFactors_nmssm_lt",
    call='fakefactors::fakefactor_nmssm_lt({df}, {output}, {input}, "{qcd_ff_variation}", "{wjets_ff_variation}", "{ttbar_ff_variation}", "{fraction_variation}", "{qcd_ff_corr_leppt_variation}", "{qcd_ff_corr_taumass_variation}", "{qcd_ff_corr_drsr_variation}", "{wjets_ff_corr_leppt_variation}", "{wjets_ff_corr_taumass_variation}", "{wjets_ff_corr_drsr_variation}", "{ttbar_ff_corr_leppt_variation}", "{ttbar_ff_corr_taumass_variation}", "{ff_file}", "{ff_corr_file}")',
    input=[
        q.pt_2,
        q.n_jets,
        q.mt_1,
        q.n_bjets,
        q.pt_1,
        q.mass_2,
        q.m_vis,
    ],
    output=[q.fake_factor],
    scopes=["mt", "et"],
)
FakeFactors_nmssm_boosted_lt = Producer(
    name="FakeFactors_nmssm_boosted_lt",
    call='fakefactors::fakefactor_nmssm_lt({df}, {output}, {input}, "{qcd_ff_variation}", "{wjets_ff_variation}", "{ttbar_ff_variation}", "{fraction_variation}", "{qcd_ff_corr_leppt_variation}", "{qcd_ff_corr_taumass_variation}", "{qcd_ff_corr_drsr_variation}", "{wjets_ff_corr_leppt_variation}", "{wjets_ff_corr_taumass_variation}", "{wjets_ff_corr_drsr_variation}", "{ttbar_ff_corr_leppt_variation}", "{ttbar_ff_corr_taumass_variation}", "{ff_file_boosted}", "{ff_corr_file_boosted}")',
    input=[
        q.boosted_pt_2,
        q.n_jets_boosted,
        q.boosted_mt_1,
        q.n_bjets_boosted,
        q.boosted_pt_1,
        q.boosted_mass_2,
        q.boosted_m_vis,
    ],
    output=[q.fake_factor_boosted],
    scopes=["mt", "et"],
)
FakeFactors_nmssm_tt_1 = Producer(
    name="FakeFactors_nmssm_tt_1",
    call='fakefactors::fakefactor_nmssm_tt({df}, {output}, 0, {input}, "{qcd_ff_variation}", "{ttbar_ff_variation}", "{fraction_variation}", "{qcd_ff_corr_leppt_variation}", "{qcd_ff_corr_taumass_variation}", "{qcd_ff_corr_drsr_variation}", "{ttbar_ff_corr_leppt_variation}", "{ttbar_ff_corr_taumass_variation}", "{ff_file}", "{ff_corr_file}")',
    input=[
        q.pt_1,
        q.pt_2,
        q.n_jets,
        q.m_vis,
        q.n_bjets,
        q.mass_1,
        q.mass_2,
    ],
    output=[q.fake_factor_1],
    scopes=["tt"],
)
FakeFactors_nmssm_tt_2 = Producer(
    name="FakeFactors_nmssm_tt_2",
    call='fakefactors::fakefactor_nmssm_tt({df}, {output}, 1, {input}, "{qcd_subleading_ff_variation}", "{ttbar_subleading_ff_variation}", "{fraction_subleading_variation}", "{qcd_subleading_ff_corr_leppt_variation}", "{qcd_subleading_ff_corr_taumass_variation}", "{qcd_subleading_ff_corr_drsr_variation}", "{ttbar_subleading_ff_corr_leppt_variation}", "{ttbar_subleading_ff_corr_taumass_variation}", "{ff_file}", "{ff_corr_file}")',
    input=[
        q.pt_1,
        q.pt_2,
        q.n_jets,
        q.m_vis,
        q.n_bjets,
        q.mass_1,
        q.mass_2,
    ],
    output=[q.fake_factor_2],
    scopes=["tt"],
)
FakeFactors_nmssm_tt_boosted_1 = Producer(
    name="FakeFactors_nmssm_tt_boosted_1",
    call='fakefactors::fakefactor_nmssm_tt({df}, {output}, 0, {input}, "{qcd_ff_variation}", "{ttbar_ff_variation}", "{fraction_variation}", "{qcd_ff_corr_leppt_variation}", "{qcd_ff_corr_taumass_variation}", "{qcd_ff_corr_drsr_variation}", "{ttbar_ff_corr_leppt_variation}", "{ttbar_ff_corr_taumass_variation}", "{ff_file_boosted}", "{ff_corr_file_boosted}")',
    input=[
        q.boosted_pt_1,
        q.boosted_pt_2,
        q.n_jets_boosted,
        q.boosted_m_vis,
        q.n_bjets_boosted,
        q.boosted_mass_1,
        q.boosted_mass_2,
    ],
    output=[q.fake_factor_boosted_1],
    scopes=["tt"],
)
FakeFactors_nmssm_tt_boosted_2 = Producer(
    name="FakeFactors_nmssm_tt_boosted_2",
    call='fakefactors::fakefactor_nmssm_tt({df}, {output}, 1, {input}, "{qcd_subleading_ff_variation}", "{ttbar_subleading_ff_variation}", "{fraction_subleading_variation}", "{qcd_subleading_ff_corr_leppt_variation}", "{qcd_subleading_ff_corr_taumass_variation}", "{qcd_subleading_ff_corr_drsr_variation}", "{ttbar_subleading_ff_corr_leppt_variation}", "{ttbar_subleading_ff_corr_taumass_variation}", "{ff_file_boosted}", "{ff_corr_file_boosted}")',
    input=[
        q.boosted_pt_1,
        q.boosted_pt_2,
        q.n_jets_boosted,
        q.boosted_m_vis,
        q.n_bjets_boosted,
        q.boosted_mass_1,
        q.boosted_mass_2,
    ],
    output=[q.fake_factor_boosted_2],
    scopes=["tt"],
)
