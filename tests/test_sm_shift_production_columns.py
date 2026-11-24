"""The columns the SM shift production adds to the n-tuples (v8 spec C23-C27, C40).

One block per item: the columns, the scopes and sample types that carry them, and the
parameters and producers behind them. That the additions change no column that was there is
the subject of test_nominal_freeze.py (the generated calls and columns of every surface), how
the shifts reach the new columns that of test_shift_inventory.py, and the C++ behind them is
exercised in test_cpp_runtime.py.
"""

import pytest

from analysis_configurations.bbtautau.analysis_profiles import (
    NMSSM_PROFILE,
    SM_BTAG_EFFICIENCY_PROFILE,
    SM_PROFILE,
    SM_TAU_ID_MEASUREMENT_PROFILE,
)
from analysis_configurations.bbtautau.constants import ERAS_RUN2, SCOPES
from analysis_configurations.bbtautau.producers import jets
from analysis_configurations.bbtautau.quantities import output as q
from analysis_configurations.bbtautau.tests.helpers import (
    build,
    find_producer,
    generate_code,
    generated_calls,
    output_names,
    producer_names,
)

ALL_SCOPES = tuple(SCOPES)
TAU_SCOPES = ("et", "mt", "tt")
LIGHT_SCOPES = ("em", "ee", "mm")
TAU_LEGS = {"et": (2,), "mt": (2,), "tt": (1, 2)}
SLOTS = range(1, 9)
# sample types by what they carry: simulation, the signal among it, and the rest
SIMULATED = ("ttbar", "dyjets", "diboson", "hh2b2tau")
NOT_SIMULATED = ("data", "embedding")


def scopes_of(sample):
    return TAU_SCOPES if sample == "embedding" else ALL_SCOPES


def sm_config(sample, era, shifts=("none",)):
    return build("sm_config", sample, era=era, scopes=scopes_of(sample), shifts=shifts)


def shifts_of(config, scope):
    return {name.removeprefix("__"): change for name, change in config.shifts.get(scope, {}).items()}


def test_only_the_sm_analysis_has_the_columns_of_the_shift_production():
    assert SM_PROFILE.shifts.parton_shower
    assert SM_PROFILE.lhe_pdf_weight_samples == ("hh2b2tau",)
    assert SM_PROFILE.stage_b_columns and SM_PROFILE.tau_id_vs_jet_high_pt_columns
    # the flag of the jets from H -> bb is written for the samples with a bb truth mother
    assert set(SM_PROFILE.bb_truegen_mother_pdgid) == {"hh2b2tau"}
    for profile in (NMSSM_PROFILE, SM_BTAG_EFFICIENCY_PROFILE, SM_TAU_ID_MEASUREMENT_PROFILE):
        assert not profile.shifts.parton_shower, profile.name
        assert profile.lhe_pdf_weight_samples == (), profile.name
        assert not profile.stage_b_columns and not profile.tau_id_vs_jet_high_pt_columns, profile.name


# --- C23: parton shower ---------------------------------------------------------

PS_SHIFTS = {
    "ps_isrUp": {"ps_isr_variation": 2.0},
    "ps_isrDown": {"ps_isr_variation": 0.5},
    "ps_fsrUp": {"ps_fsr_variation": 2.0},
    "ps_fsrDown": {"ps_fsr_variation": 0.5},
}


@pytest.mark.parametrize("sample", SIMULATED)
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_parton_shower_weight_and_shifts_of_simulated_samples(era, sample):
    """ps_weight in every scope, 1 in the nominal, and the four shifts with the factor of the
    ISR or of the FSR scale: Up is the scale times 2, Down the scale times 0.5."""
    config = sm_config(sample, era, shifts=("ps_isr", "ps_fsr"))
    nominal = config.config_parameters["global"]["nominal"]
    assert (nominal["ps_isr_variation"], nominal["ps_fsr_variation"]) == (1.0, 1.0)
    assert nominal["ps_weight_sizes"] == "4"
    assert {"PSWeightChecked", "PartonShowerWeight"} <= producer_names(config, "global")
    weight = find_producer(config, "global", "PartonShowerWeight")
    # the weight reads the checked copy, so that a file with another length stops the job
    assert [quantity.name for quantity in weight.input["global"]] == ["PSWeight_checked"]
    assert [quantity.name for quantity in find_producer(config, "global", "PSWeightChecked").input["global"]] == ["PSWeight"]
    for scope in ("global", *ALL_SCOPES):
        assert shifts_of(config, scope) == PS_SHIFTS, scope
    for scope in ALL_SCOPES:
        assert "ps_weight" in output_names(config, scope)
        assert set(q.ps_weight.get_shifts(scope)) == {f"__{name}" for name in PS_SHIFTS}, scope


def test_parton_shower_shifts_evaluate_the_weight_at_their_scale_factor():
    """In the generated code the shifted weights call the core function with (ISR, FSR) =
    (2, 1), (0.5, 1), (1, 2), (1, 0.5): PSWeight[0], [2], [1], [3]
    (tests/cpp/test_theory_weights.cxx pins the index of each)."""
    generated = generate_code("sm_config", "ttbar", era="2018", scopes=("mt",), shifts=("ps_isr", "ps_fsr"))
    calls = [call for call in generated_calls(generated)["global"] if "PartonShower" in call]
    arguments = {"": "1.0, 1.0", "__ps_isrUp": "2.0, 1.0", "__ps_isrDown": "0.5, 1.0",
                 "__ps_fsrUp": "1.0, 2.0", "__ps_fsrDown": "1.0, 0.5"}
    assert sorted(calls) == sorted(
        f'event::reweighting::PartonShower(df, "ps_weight{suffix}", "PSWeight_checked", {values})'
        for suffix, values in arguments.items()
    )
    # one check of the length serves the nominal and every shift
    checks = [call for call in generated_calls(generated)["global"] if "CheckedSize" in call]
    assert checks == ['xyh::theory_weights::CheckedSize(df, "PSWeight_checked", "PSWeight", {4})']
    assert {name for name in generated.outputs["mt"] if "__" in name} == {
        f"ps_weight__{name}" for name in PS_SHIFTS
    }


@pytest.mark.parametrize("sample", NOT_SIMULATED)
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_data_and_embedding_have_no_parton_shower_weight(era, sample):
    config = sm_config(sample, era, shifts=("all",))
    assert not {"PSWeightChecked", "PartonShowerWeight"} & producer_names(config, "global")
    for scope in scopes_of(sample):
        assert "ps_weight" not in output_names(config, scope)
        assert not [name for name in shifts_of(config, scope) if name.startswith("ps_")]


@pytest.mark.parametrize(
    "module,sample,era,scopes",
    [
        ("nmssm_config", "ttbar", "2024", ("mt",)),
        ("sm_tau_id_measurement_config", "dyjets", "2018", ("mt", "mm")),
        ("sm_btag_efficiency_config", "ttbar", "2018", ("mt",)),
    ],
)
def test_the_other_configurations_have_no_parton_shower_shifts(module, sample, era, scopes):
    config = build(module, sample, era=era, scopes=scopes, shifts=("all",))
    for scope in scopes:
        assert "ps_weight" not in output_names(config, scope)
        assert not [name for name in shifts_of(config, scope) if name.startswith("ps_")]


# --- C24: PDF weights of the signal ---------------------------------------------

PDF_COLUMNS = {f"lhe_pdf_weight_{member}" for member in range(1, 101)}


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_the_signal_writes_the_weights_of_the_pdf_eigenvectors(era):
    """lhe_pdf_weight_<i> for the members 1 to 100 in every scope, read at index i from the
    weights with a checked length (101 or 103 entries); no column for the central member 0
    and the two alpha_s members, no combination per event and no shift."""
    config = sm_config("hh2b2tau", era, shifts=("all",))
    assert config.config_parameters["global"]["nominal"]["lhe_pdf_weight_sizes"] == "101, 103"
    group = find_producer(config, "global", "LHEPdfWeights")
    members = group.producers["global"]
    assert [producer.name for producer in members] == ["LHEPdfWeightChecked"] + [
        f"lhe_pdf_weight_{member}" for member in range(1, 101)
    ]
    for member, producer in enumerate(members[1:], start=1):
        assert producer.call == f"event::quantity::Get<float>({{df}}, {{output}}, {{input}}, {member})"
        assert [quantity.name for quantity in producer.input["global"]] == ["LHEPdfWeight_checked"]
        assert [quantity.name for quantity in producer.output] == [f"lhe_pdf_weight_{member}"]
    for scope in ALL_SCOPES:
        columns = {name for name in output_names(config, scope) if name.startswith("lhe_pdf")}
        assert columns == PDF_COLUMNS, scope
        assert not any(q.lhe_pdf_weight(member).get_shifts(scope) for member in q.LHE_PDF_MEMBERS), scope


@pytest.mark.parametrize("sample", ["ttbar", "dyjets", "diboson", "data", "embedding"])
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_no_other_sample_has_pdf_columns(era, sample):
    config = sm_config(sample, era)
    assert "LHEPdfWeights" not in producer_names(config, "global")
    for scope in scopes_of(sample):
        assert not [name for name in output_names(config, scope) if "pdf" in name.lower()], scope


# --- C25: jet slots -------------------------------------------------------------

SLOT_QUANTITIES = ("jpt", "jeta", "jphi", "jmass", "jtag_value", "jtag_cvb", "jtag_cvl", "jtag_qvg")
# the columns of the two leading jets that every scope had before
LEADING_JET_COLUMNS = {f"{name}_{slot}" for name in ("jpt", "jeta", "jphi", "jtag_value") for slot in (1, 2)}
LEADING_JET_FLAVOURS = {"jet_hadronFlavour_1", "jet_hadronFlavour_2"}


def slot_columns(config, scope):
    prefixes = (*SLOT_QUANTITIES, "jet_hadronFlavour", "jet_from_hbb")
    return {
        name for name in output_names(config, scope)
        if name.rsplit("_", 1)[0] in prefixes and name.rsplit("_", 1)[1].isdigit()
    }


@pytest.mark.parametrize("sample", ["data", "embedding", "ttbar", "hh2b2tau"])
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_jet_slot_columns_per_sample_and_scope(era, sample):
    """et, mt and tt: eight slots with pT, eta, phi, mass and the UParT B, CvB, CvL and QvG
    scores in every sample, the hadron flavour in simulation and the H -> bb flag in the
    signal; em, ee and mm keep the columns of the two leading jets."""
    config = sm_config(sample, era)
    simulated = sample not in NOT_SIMULATED
    expected = {f"{name}_{slot}" for name in SLOT_QUANTITIES for slot in SLOTS}
    if simulated:
        expected |= {f"jet_hadronFlavour_{slot}" for slot in SLOTS}
    if sample == "hh2b2tau":
        expected |= {f"jet_from_hbb_{slot}" for slot in SLOTS}
    for scope in scopes_of(sample):
        if scope in TAU_SCOPES:
            assert slot_columns(config, scope) == expected, (scope, sorted(slot_columns(config, scope) ^ expected))
        else:
            assert slot_columns(config, scope) == LEADING_JET_COLUMNS | (LEADING_JET_FLAVOURS if simulated else set()), scope
            assert not [name for name in producer_names(config, scope) if name.startswith("JetSlot")], scope
    for scope in TAU_SCOPES:
        # one producer group per slot, so that no generated source file holds all slots
        groups = {name for name in producer_names(config, scope) if name.startswith("JetSlot")}
        expected_groups = {f"JetSlot{slot}" for slot in SLOTS}
        if simulated:
            expected_groups |= {f"JetSlotHadronFlavour{slot}" for slot in range(3, 9)}
        if sample == "hh2b2tau":
            expected_groups.add("JetSlotHbbFlags")
        assert groups == expected_groups, scope


def test_jet_slots_read_the_collection_of_n_jets_in_order():
    """Slot i is position i - 1 of good_jet_collection, the pT-ordered collection that n_jets
    counts; the two leading slots are the producers the configuration had, and the further
    slots call the same functions on the same columns."""
    assert [quantity.name for quantity in jets.NumberOfJets.input[TAU_SCOPES[0]]] == ["good_jet_collection"]
    assert jets.JetCollection.call.startswith("physicsobject::OrderByPt(")
    leading = {"jet_p4": (jets.LVJet1, jets.LVJet2), "jpt": (jets.jpt_1, jets.jpt_2),
               "jeta": (jets.jeta_1, jets.jeta_2), "jphi": (jets.jphi_1, jets.jphi_2),
               "jtag_value": (jets.jtag_value_1, jets.jtag_value_2),
               "jet_hadronFlavour": (jets.jet_hadronFlavour_1, jets.jet_hadronFlavour_2)}
    for name, (first, second) in leading.items():
        assert jets.JET_SLOT_PRODUCERS[name, 1] is first and jets.JET_SLOT_PRODUCERS[name, 2] is second
        for slot in range(3, 9):
            producer = jets.JET_SLOT_PRODUCERS[name, slot]
            # the call of the leading jet at the position of the slot
            assert producer.call == second.call.replace(", 1)", f", {slot - 1})"), (name, slot)
            inputs = [quantity.name for quantity in producer.input["mt"]]
            expected = [quantity.name for quantity in second.input["mt"]]
            assert inputs == [name.replace("jet_p4_2", f"jet_p4_{slot}") for name in expected], (name, slot)
            assert [quantity.name for quantity in producer.output] == [f"{name}_{slot}"]
    for name, branch in (("jtag_cvb", "Jet_btagUParTAK4CvB"), ("jtag_cvl", "Jet_btagUParTAK4CvL"),
                         ("jtag_qvg", "Jet_btagUParTAK4QvG")):
        for slot in SLOTS:
            producer = jets.JET_SLOT_PRODUCERS[name, slot]
            assert producer.call == f"event::quantity::Get<float>({{df}}, {{output}}, {{input}}, {slot - 1})"
            assert [quantity.name for quantity in producer.input["mt"]] == [branch, "good_jet_collection"]
    for slot in SLOTS:
        producer = jets.JET_SLOT_PRODUCERS["jmass", slot]
        assert producer.call == "lorentzvector::GetMass({df}, {output}, {input})"
        assert [quantity.name for quantity in producer.input["mt"]] == [f"jet_p4_{slot}"]


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_the_hbb_flag_matches_the_b_quarks_of_the_higgs_boson_within_0p4(era):
    config = sm_config("hh2b2tau", era)
    for scope in TAU_SCOPES:
        nominal = config.config_parameters[scope]["nominal"]
        assert nominal["bb_truegen_mother_pdgid"] == 25 and nominal["bb_truegen_daughter_1_pdgid"] == 5
        assert nominal["hbb_jet_match_delta_r"] == 0.4
        matching = find_producer(config, scope, "JetsFromHbb")
        assert matching.call.split("(")[0].strip() == "xyh::genmatching::JetsFromBosonDecay"
        assert [quantity.name for quantity in matching.input[scope]][-3:] == ["Jet_eta", "Jet_phi", "good_jet_collection"]
        for slot in SLOTS:
            flag = find_producer(config, scope, f"jet_from_hbb_{slot}")
            assert flag.call == f"event::quantity::Get<int>({{df}}, {{output}}, {{input}}, {slot - 1})"
            assert [quantity.name for quantity in flag.input[scope]] == ["jets_from_hbb"]


# --- C26, C27: raw tau scores and genTtbarId ------------------------------------


@pytest.mark.parametrize("sample", ["data", "embedding", "ttbar", "hh2b2tau"])
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_raw_tau_scores_of_the_tau_legs_and_gen_ttbar_id(era, sample):
    """The raw DeepTau scores against electrons and muons for the tau legs of et, mt (leg 2)
    and tt (both), in every sample, and no raw score against jets under such a name;
    genTtbarId in every scope of simulated samples only."""
    config = sm_config(sample, era)
    for scope in scopes_of(sample):
        names = output_names(config, scope)
        raw = {name for name in names if "rawdeeptau" in name.lower()}
        expected = {
            f"rawDeepTau2018v2p5{against}_{leg}" for against in ("VSe", "VSmu") for leg in TAU_LEGS.get(scope, ())
        }
        assert raw == expected, scope
        assert ("genTtbarId" in names) is (sample not in NOT_SIMULATED), scope
    for scope in TAU_SCOPES:
        for leg in TAU_LEGS[scope]:
            for against, branch in (("ele", "Tau_rawDeepTau2018v2p5VSe"), ("mu", "Tau_rawDeepTau2018v2p5VSmu")):
                producer = find_producer(config, scope, f"tau_raw_vs_{against}_{leg}")
                assert producer.call == f"event::quantity::Get<Float_t>({{df}}, {{output}}, {{input}}, {leg - 1})"
                assert [quantity.name for quantity in producer.input[scope]] == [branch, "dileptonpair"]


# --- C40: pT-binned vsJet SF ----------------------------------------------------


def high_pt_columns(sample, era, scope):
    """The columns of the pT-binned SF in the generated code (the outputs of vector
    producers get their names there)."""
    generated = generate_code("sm_config", sample, era=era, scopes=scopes_of(sample))
    return {name for name in generated.outputs[scope] if "highpt" in name}


@pytest.mark.parametrize("sample", SIMULATED)
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_high_pt_vs_jet_sf_columns_of_simulated_taus(era, sample):
    """Three columns per tau leg and working point of the DM-binned SF column: the nominal,
    up and down of the pT-binned set, evaluated on the TAU payload and with the vsEle working
    point of the DM-binned SF. They are columns of the nominal tree: no shift sets their
    parameters, and the DM-binned configuration is untouched."""
    config = sm_config(sample, era, shifts=("all",))
    for scope in ALL_SCOPES:
        if scope not in TAU_SCOPES:
            assert not high_pt_columns(sample, era, scope), scope
            continue
        nominal = config.config_parameters[scope]["nominal"]
        dm_binned = nominal["vsjet_tau_id_sf"]
        assert [entry["vsjet_wp"] for entry in dm_binned] == ["Medium"]
        assert nominal["tau_id_sf_vsjet_sf_dependence"] == "dm" and nominal["tau_id_sf_vsjet_variation"] == "nom"
        entries = nominal["vsjet_tau_id_sf_high_pt"]
        assert [(entry["vsjet_wp"], entry["high_pt_member"]) for entry in entries] == [
            (wp["vsjet_wp"], member) for wp in dm_binned for member in ("nom", "up", "down")
        ]
        for entry in entries:
            suffix = "" if entry["high_pt_member"] == "nom" else "_" + entry["high_pt_member"]
            assert entry["discriminator"] == dm_binned[0]["discriminator"] == "DeepTau2018v2p5VSjet"
            for leg in (1, 2):
                assert entry[f"tau{leg}_output_name"] == f"id_wgt_tau_vsJet_{entry['vsjet_wp']}_highpt{suffix}_{leg}"
        assert high_pt_columns(sample, era, scope) == {
            f"id_wgt_tau_vsJet_Medium_highpt{suffix}_{leg}" for suffix in ("", "_up", "_down") for leg in TAU_LEGS[scope]
        }, scope
        for leg in TAU_LEGS[scope]:
            producer = find_producer(config, scope, f"TauIDVsJetHighPtSF{leg}")
            assert producer.call.split("(")[0].strip() == "xyh::scalefactor::tau_id_vsjet_pt_binned"
            assert '"{tau_vsjet_es_sf_file}"' in producer.call and '"{tau_ides_sf_vsele_wp}"' in producer.call
            assert [quantity.name for quantity in producer.input[scope]] == [
                f"pt_{leg}", f"tau_decaymode_{leg}", f"gen_match_{leg}"
            ]
        # the DM-binned SF and the pT-binned columns read the same payload
        assert nominal["tau_vsjet_es_sf_file"] == nominal["tau_ides_sf_file"]
        for name, change in shifts_of(config, scope).items():
            assert not {"vsjet_tau_id_sf_high_pt", "vsjet_tau_id_sf"} & set(change), name


@pytest.mark.parametrize("sample", NOT_SIMULATED)
@pytest.mark.parametrize("era", ERAS_RUN2)
def test_data_and_embedding_have_no_high_pt_vs_jet_sf_columns(era, sample):
    """The embedding has its own tau-ID measurement (binned in the decay mode)."""
    config = sm_config(sample, era)
    for scope in TAU_SCOPES:
        assert not high_pt_columns(sample, era, scope), scope
        assert "vsjet_tau_id_sf_high_pt" not in config.config_parameters[scope]["nominal"]
        assert "TauIDVsJetHighPtSF" not in producer_names(config, scope)
