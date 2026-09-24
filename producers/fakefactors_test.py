from ..quantities import nanoAOD as nanoAOD
from ..quantities import output as q
from code_generation.producer import Producer, ProducerGroup
from code_generation.helpers import defaults

with defaults(scopes=["et", "mt", "tt", "em", "mm", "ee"]):
    with defaults(call='utility::Cast<float, int>({df}, {output}, "float", {input}).first'):
        ConversionToFloatCollection = [
            n_jets_Float := Producer(input=[q.n_jets], output=[q.n_jets_float]),
            n_bjets_Float := Producer(input=[q.n_bjets], output=[q.n_bjets_float]),
            tau_decaymode_2_Float := Producer(input=[q.tau_decaymode_2], output=[q.tau_decaymode_2_float]),
            tau_decaymode_1_Float := Producer(input=[q.tau_decaymode_1], output=[q.tau_decaymode_1_float]),
        ]

    with defaults(call='utility::Cast<float, double>({df}, {output}, "float", {input}).first'):
        ConversionToFloatCollection += [
            pzetamissvis_Float := Producer(input=[q.pzetamissvis], output=[q.pzetamissvis_float]),
        ]

    VariableConversionToFloatProducerGroup = ProducerGroup(subproducers=ConversionToFloatCollection)

    with defaults(call='ml_sm::EventParity({df}, {output}, {input})'):
        event_parity_Float = Producer(input=[nanoAOD.event], output=[q.event_parity_float])

with defaults(scopes=["mt", "et"]):
    with defaults(call='''fakefactors::build_model_input_column({df}, {output}, {input_vec})'''):
        with defaults(input=[q.pt_2, q.n_jets_float]):
            FFInput_QCD_2018_mt = Producer(output=[q.ff_sm_qcd_model_input_2])
            FFInput_ttbar_2018_mt = Producer(output=[q.ff_sm_ttbar_model_input_2])
            # FFInput_Wjets_2018_mt = Producer(output=[q.ff_sm_wjets_model_input_2])
        with defaults(input=[q.mt_1, q.n_jets_float]):
            FFInput_fractions_2018_mt = Producer(output=[q.ff_sm_fractions_model_input_2])
        with defaults(input=[q.pt_tautau, q.n_jets_float]):
            FFInput_DR_QCD_2018_mt = Producer(output=[q.ff_sm_dr_qcd_model_input_2])
            # FFInput_DR_Wjets_2018_mt = Producer(output=[q.ff_sm_dr_wjets_model_input_2])
        with defaults(
            input=[
                q.tau_decaymode_2_float,
                q.pt_1,
                q.jpt_1,
                q.mass_2,
                q.met,
                q.mt_tot,
                q.iso_1,
                q.n_jets_float,
            ],
        ):
            FFInput_NC_QCD_2018_mt = Producer(output=[q.ff_sm_nc_qcd_model_input_2_mt])
            # FFInput_NC_Wjets_2018_mt = Producer(output=[q.ff_sm_nc_wjets_model_input_2_mt])
            FFInput_NC_ttbar_2018_mt = Producer(output=[q.ff_sm_nc_ttbar_model_input_2_mt])
        with defaults(
            input=[
                q.tau_decaymode_2_float,
                q.pt_1,
                # q.mass_2,
                q.met,
                q.mt_tot,
                q.iso_1,
                q.n_jets_float,
            ],
        ):
            FFInput_NC_QCD_2018_et = Producer(output=[q.ff_sm_nc_qcd_model_input_2_et])
            # FFInput_NC_Wjets_2018_et = Producer(output=[q.ff_sm_nc_wjets_model_input_2_et])
            FFInput_NC_ttbar_2018_et = Producer(output=[q.ff_sm_nc_ttbar_model_input_2_et])

    RawFakeFactors_sm_2018_mt = Producer(
        call='''fakefactors::sm::raw_fakefactor_lt(
            {df},
            correctionManager,
            {output},
            {input},
            "{fraction_variation}",
            "{QCD_variation}",
            "{ttbar_variation}",
            "{file}")''',
        input=[
            q.pt_2,
            q.ff_sm_qcd_model_input_2,
            # q.ff_sm_wjets_model_input_2,
            q.ff_sm_ttbar_model_input_2,
            q.ff_sm_fractions_model_input_2,
        ],
        output=[q.raw_fake_factor_2],
    )
    # taken out: "{Wjets_variation}",
    with defaults(
        call='''fakefactors::sm::fakefactor_lt(
                {df},
                correctionManager,
                {output_vec},
                {input},
                "{fraction_variation}",
                "{QCD_variation}",
                "{ttbar_variation}",
                "{QCD_DR_SR_correction}",
                "{QCD_non_closure_correction}",
                "{ttbar_non_closure_correction}",
                "{file}",
                "{corr_file}",
                false)''',
        output=[q.fake_factor_2],
    ):
        FakeFactors_sm_mt = Producer(
            input=[
                q.pt_2,
                q.ff_sm_qcd_model_input_2,
                # q.ff_sm_wjets_model_input_2,
                q.ff_sm_ttbar_model_input_2,
                q.ff_sm_fractions_model_input_2,
                q.ff_sm_dr_qcd_model_input_2,
                # q.ff_sm_dr_wjets_model_input_2,
                q.ff_sm_nc_qcd_model_input_2_mt,
                # q.ff_sm_nc_wjets_model_input_2_mt,
                q.ff_sm_nc_ttbar_model_input_2_mt,
            ],
        )
        FakeFactors_sm_et = Producer(
            input=[
                q.pt_2,
                q.ff_sm_qcd_model_input_2,
                # q.ff_sm_wjets_model_input_2,
                q.ff_sm_ttbar_model_input_2,
                q.ff_sm_fractions_model_input_2,
                q.ff_sm_dr_qcd_model_input_2,
                # q.ff_sm_dr_wjets_model_input_2,
                q.ff_sm_nc_qcd_model_input_2_et,
                # q.ff_sm_nc_wjets_model_input_2_et,
                q.ff_sm_nc_ttbar_model_input_2_et,
            ],
        )
        # taken out: "{Wjets_variation}","{Wjets_DR_SR_correction}","{Wjets_non_closure_correction}",
    
    
    with defaults(
        call='''fakefactors::sm::fakefactor_lt(
            {df},
            correctionManager,
            {output_vec},
            {input},
            "{fraction_variation}",
            "{QCD_variation}",
            "{ttbar_variation}",
            "{QCD_DR_SR_correction}",
            "{QCD_non_closure_correction}",
            "{ttbar_non_closure_correction}",
            "{file}",
            "{corr_file}",
            true)''',
        output=[
            q.raw_qcd_fake_factor_2,
            # q.raw_wjets_fake_factor_2,
            q.raw_ttbar_fake_factor_2,
            # ---
            q.qcd_fake_factor_fraction_2,
            # q.wjets_fake_factor_fraction_2,
            q.ttbar_fake_factor_fraction_2,
            # ---
            q.qcd_DR_SR_correction_2,
            # q.wjets_DR_SR_correction_2,
            q.ttbar_DR_SR_correction_2,
            # ---
            q.qcd_correction_wo_DR_SR_2,
            # q.wjets_correction_wo_DR_SR_2,
            q.ttbar_correction_wo_DR_SR_2,
            # ---
            q.qcd_fake_factor_correction_2,
            # q.wjets_fake_factor_correction_2,
            q.ttbar_fake_factor_correction_2,
            # ---
            q.qcd_fake_factor_2,
            # q.wjets_fake_factor_2,
            q.ttbar_fake_factor_2,
        ],
    ):
        FakeFactors_sm_mt_split_info = Producer(
            input=[
                q.pt_2,
                q.ff_sm_qcd_model_input_2,
                # q.ff_sm_wjets_model_input_2,
                q.ff_sm_ttbar_model_input_2,
                q.ff_sm_fractions_model_input_2,
                q.ff_sm_dr_qcd_model_input_2,
                # q.ff_sm_dr_wjets_model_input_2,
                q.ff_sm_nc_qcd_model_input_2_mt,
                # q.ff_sm_nc_wjets_model_input_2_mt,
                q.ff_sm_nc_ttbar_model_input_2_mt,
            ],
        )
        FakeFactors_sm_et_split_info = Producer(
            input=[
                q.pt_2,
                q.ff_sm_qcd_model_input_2,
                # q.ff_sm_wjets_model_input_2,
                q.ff_sm_ttbar_model_input_2,
                q.ff_sm_fractions_model_input_2,
                q.ff_sm_dr_qcd_model_input_2,
                # q.ff_sm_dr_wjets_model_input_2,
                q.ff_sm_nc_qcd_model_input_2_et,
                # q.ff_sm_nc_wjets_model_input_2_et,
                q.ff_sm_nc_ttbar_model_input_2_et,
            ],
        )
        # taken out: "{Wjets_variation}","{Wjets_DR_SR_correction}","{Wjets_non_closure_correction}",

with defaults(scopes=["tt"]):
    RawFakeFactors_sm_tt_1 = Producer(
        call='''fakefactors::sm::raw_fakefactor_tt(
            {df},
            correctionManager,
            {output},
            0,
            {input},
            "{QCD_variation}",
            "{ttbar_variation}",
            "{fraction_variation}",
            "{file}")''',
        input=[
            q.pt_1,
            q.pt_2,
            q.m_vis,
            q.n_jets_float,
        ],
        output=[q.raw_fake_factor_1],
    )
    RawFakeFactors_sm_tt_2 = Producer(
        call='''fakefactors::sm::raw_fakefactor_tt(
            {df},
            correctionManager,
            {output},
            1,
            {input},
            "{QCD_subleading_variation}",
            "{ttbar_subleading_variation}",
            "{fraction_variation_subleading}",
            "{file}")''',
        input=[
            q.pt_1,
            q.pt_2,
            q.m_vis,
            q.n_jets_float,
        ],
        output=[q.raw_fake_factor_2],
    )

    FakeFactors_sm_tt_1 = Producer(
        call='''fakefactors::sm::fakefactor_tt({df},
        correctionManager,
        {output},
        0,
        {input},
        "{QCD_variation}",
        "{ttbar_variation}",
        "{fraction_variation}",
        "{QCD_non_closure_correction}",
        "{QCD_DR_SR_correction}",
        "{ttbar_non_closure_correction}",
        "{file}",
        "{corr_file}")''',
        input=[
            q.tau_decaymode_1_float,
            q.tau_decaymode_2_float,
            q.pt_1,
            q.pt_2,
            q.met,
            q.mt_tot,
            q.pt_tautau,
            q.mass_1,
            q.mass_2,
            q.m_vis,
            q.n_jets_float,
        ],
        output=[q.fake_factor_1],
    )
    FakeFactors_sm_tt_2 = Producer(
        call='''fakefactors::sm::fakefactor_tt(
            {df},
            correctionManager,
            {output},
            1,
            {input},
            "{QCD_subleading_variation}",
            "{ttbar_subleading_variation}",
            "{fraction_variation_subleading}",
            "{QCD_subleading_non_closure_correction}",
            "{QCD_subleading_DR_SR_correction}",
            "{ttbar_subleading_non_closure_correction}",
            "{file}",
            "{corr_file}")''',
        input=[
            q.tau_decaymode_1_float,
            q.tau_decaymode_2_float,
            q.pt_1,
            q.pt_2,
            q.met,
            q.mt_tot,
            q.pt_tautau,
            q.mass_1,
            q.mass_2,
            q.m_vis,
            q.n_jets_float,
        ],
        output=[q.fake_factor_2],
    )
