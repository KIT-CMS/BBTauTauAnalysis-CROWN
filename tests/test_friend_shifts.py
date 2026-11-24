"""The friends of the SM shift production follow the shifts of the main n-tuple (v8 spec C31).

A friend recomputes a producer under a shift only if one of its inputs is listed as shifted
in the quantities map of the n-tuple; otherwise the producer stays nominal and the build
only logs an info (code_generation/friend_trees.py, _shift_producer_inputs). A shift of the
main tree that a friend misses would therefore go unnoticed: the datacards would read the
nominal friend column under it.

The quantities maps of these tests are not written by hand: they are the output columns of
the code generated for sm_config with all shifts, in every Run-2 era, which is what the
executable writes into its files (helpers.quantities_map), and for the NN classifier the
map of the FastMTT friend generated on top of them. On these maps, sm_fastmtt,
sm_fake_factors, sm_fake_factors_w and sm_nn_classifier (the models of the production) are
generated with all shifts, and their output columns must carry

- every kinematic shift of the main tree in the era, sample type and scope (the families of
  test_shift_inventory.py that are not weights), both directions. The one exception is
  spelled out in UNREAD: outside et the energy scale and resolution of simulated electrons
  move nothing but the veto of further electrons, which only the gate of the NN classifier
  reads;
- no weight shift of the main tree, which changes no input of a friend;
- for the fake factors, the shifts of their own payload on top.
"""

import pytest

from analysis_configurations.bbtautau import sm_fake_factors, sm_fake_factors_w, sm_fastmtt, sm_nn_classifier
from analysis_configurations.bbtautau.constants import ERAS_RUN2, RUN2_V15_RECOIL_CORRECTION_ERAS
from analysis_configurations.bbtautau.tests import test_shift_inventory as inventory
from analysis_configurations.bbtautau.tests.helpers import (
    generate_code,
    generate_friend_code,
    quantities_map,
)

TAU_SCOPES = ("et", "mt", "tt")
FASTMTT_COLUMNS = {"m_fastmtt", "pt_fastmtt", "eta_fastmtt", "phi_fastmtt"}
FF_COLUMNS = {
    "et": ({"fake_factor_raw"}, {"fake_factor"}),
    "mt": ({"fake_factor_raw"}, {"fake_factor"}),
    "tt": ({"fake_factor_1_raw", "fake_factor_2_raw"}, {"fake_factor_1", "fake_factor_2"}),
}
NN_CLASSES = ("HH2B2Tau", "tautau", "Top", "jetFakes", "Other")
NN_COLUMNS = {
    f"{model.prefix}{name}"
    for model in sm_nn_classifier.MODELS
    for name in ("predicted_class", "predicted_max_value", *(f"nn_score_{c}" for c in NN_CLASSES))
}

# The sample types whose shifts differ: simulation, the recoil-corrected DY (2018), the
# embedding, and data without any shift
SURFACES = [
    pytest.param(era, sample, id=f"{era}-{sample}")
    for era in ERAS_RUN2
    for sample in ("ttbar", "embedding", "data", *(["dyjets"] if era in RUN2_V15_RECOIL_CORRECTION_ERAS else []))
]


def main_tree_shifts(era, sample, scope):
    """(kinematic, weight) shift names of the main tree, both directions."""
    families = inventory.expected_pairs(era, sample, scope)
    kinematic, weight = set(), set()
    for family in inventory.FAMILIES:
        names = inventory.both_directions(families.get(family.name, ()))
        (weight if family.weights else kinematic).update(names)
    return kinematic, weight


def unread(era, sample, scope):
    """The kinematic shifts of the main tree that change no input of FastMTT and of the fake
    factors: in mt and tt the electron energy scale and resolution of simulation, whose only
    shifted columns there belong to the veto of further electrons (the pair has no electron)."""
    if scope == "et" or sample in ("data", "embedding"):
        return set()
    return inventory.both_directions({f"CMS_scale_e_{era}", f"CMS_res_e_{era}"})


def shifts_of(columns, outputs):
    """Column -> the shifts it has among the output columns ``outputs``."""
    found = {column: set() for column in columns}
    for name in outputs:
        column, _, shift = name.partition("__")
        if shift and column in found:
            found[column].add(shift)
    return found


def test_the_friends_of_the_production_are_available_in_every_run2_era():
    for module in (sm_fastmtt, sm_fake_factors, sm_fake_factors_w, sm_nn_classifier):
        assert list(module.AVAILABLE_ERAS) == list(ERAS_RUN2), module.__name__
    assert [model.prefix for model in sm_nn_classifier.MODELS] == ["nn_m3abnv1_", "nn_m0k4abnv1_"]


@pytest.mark.parametrize("era,sample", SURFACES)
def test_friends_carry_every_kinematic_shift_of_the_main_tree(era, sample, tmp_path):
    main = generate_code("sm_config", sample, era=era, scopes=TAU_SCOPES, shifts=("all",))
    main_map = quantities_map(main.outputs, era, sample, "sm_config", tmp_path / "main.json")
    for scope in TAU_SCOPES:
        kinematic, weight = main_tree_shifts(era, sample, scope)
        # the map is the all-shifts surface the inventory lists
        in_map = {name.partition("__")[2] for name in main.outputs[scope] if "__" in name}
        assert in_map == kinematic | weight, scope
        assert bool(kinematic) is (sample != "data"), scope

        # the electron shifts outside et: nothing but the electron veto in the map
        without_effect = unread(era, sample, scope)
        assert without_effect <= kinematic, scope
        for shift in without_effect:
            moved = {name.partition("__")[0] for name in main.outputs[scope] if name.endswith(f"__{shift}")}
            assert moved and all("veto" in column for column in moved), (scope, shift, sorted(moved))
        followed = kinematic - without_effect

        # FastMTT: the di-tau mass moves with the legs and with the MET
        fastmtt = generate_friend_code("sm_fastmtt", sample, era, scope, [main_map])
        assert {name.partition("__")[0] for name in fastmtt.outputs[scope]} == FASTMTT_COLUMNS, scope
        for column, shifts in shifts_of(FASTMTT_COLUMNS, fastmtt.outputs[scope]).items():
            assert shifts == followed, (scope, column, sorted(shifts ^ followed)[:5])

        # fake factors, both variants: every kinematic shift reaches the corrected fake factor
        # (its corrections read the tau, the lepton, the jets and the MET) next to the shifts
        # of the payload; no weight shift of the main tree does
        for module in ("sm_fake_factors", "sm_fake_factors_w"):
            friend = generate_friend_code(module, sample, era, scope, [main_map])
            raw, corrected = FF_COLUMNS[scope]
            assert {name.partition("__")[0] for name in friend.outputs[scope]} == raw | corrected, (module, scope)
            found = shifts_of(raw | corrected, friend.outputs[scope])
            for column in corrected:
                payload_shifts = found[column] - kinematic
                assert found[column] & kinematic == followed, (
                    module, scope, column, sorted((found[column] & kinematic) ^ followed)[:5],
                )
                assert not found[column] & weight, (module, scope, column)
                # the shifts of the payload: named after its keys, never after a shift of the main tree
                assert payload_shifts and not payload_shifts & in_map, (module, scope, column)
            for column in raw:
                assert not found[column] & weight, (module, scope, column)
                # the raw fake factor has the fake-factor and fraction shifts of the payload only
                assert found[column] - kinematic <= found[column.replace("_raw", "")], (module, scope, column)

        # NN classifier, on the main tree and the FastMTT friend: the gate and every score
        fastmtt_map = quantities_map(
            fastmtt.outputs, era, sample, "sm_fastmtt", tmp_path / f"fastmtt_{scope}.json"
        )
        nn = generate_friend_code("sm_nn_classifier", sample, era, scope, [main_map, fastmtt_map])
        assert {name.partition("__")[0] for name in nn.outputs[scope]} == NN_COLUMNS, scope
        # every kinematic shift, the electron shifts outside et through the gate
        for column, shifts in shifts_of(NN_COLUMNS, nn.outputs[scope]).items():
            assert shifts == kinematic, (scope, column, sorted(shifts ^ kinematic)[:5])
        # the scores read the di-tau mass from the FastMTT friend, whose map has to carry
        # the shifts for the chain to hand them on
        assert {name.partition("__")[2] for name in fastmtt.outputs[scope] if "__" in name} == followed


@pytest.mark.parametrize("era", ERAS_RUN2)
def test_raw_fake_factor_follows_the_shifts_of_its_inputs(era, tmp_path):
    """The uncorrected fake factor reads the tau pT, the jet multiplicities and the inputs of
    the fractions: it follows the tau energy scale and the jet shifts of the main tree."""
    main = generate_code("sm_config", "ttbar", era=era, scopes=TAU_SCOPES, shifts=("all",))
    main_map = quantities_map(main.outputs, era, "ttbar", "sm_config", tmp_path / "main.json")
    for scope in TAU_SCOPES:
        friend = generate_friend_code("sm_fake_factors", "ttbar", era, scope, [main_map])
        raw, _ = FF_COLUMNS[scope]
        for column, shifts in shifts_of(raw, friend.outputs[scope]).items():
            expected = {
                f"CMS_scale_t_DeepTau2018v2p5_DM{dm}_genTau_{era}{direction}"
                for dm in (0, 1, 10, 11)
                for direction in ("Up", "Down")
            } | {"CMS_scale_j_AbsoluteUp", "CMS_scale_j_AbsoluteDown", f"CMS_res_j_eta0to1p93_{era}Up"}
            assert expected <= shifts, (scope, column, sorted(expected - shifts))
