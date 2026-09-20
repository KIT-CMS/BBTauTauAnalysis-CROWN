"""Friend-tree entry points: dispatch marker, era gate, and output contracts.

The SM friend entries are thin re-exports of bodies shared with their NMSSM
counterparts, so what is worth testing are the surfaces where a mistake is silent:
the ``FriendTreeConfiguration`` marker ``generate_friends.run()`` dispatches on
(otherwise-unused ``# noqa: F401`` code an import cleanup would delete), the era
gate that must fire before ``build_config``, and the emitted leaves.
"""

import inspect
from pathlib import Path
from unittest import mock

import pytest

from analysis_configurations.bbtautau import (
    generate_friends,
    nmssm_fastmtt,
    nmssm_kinfit_resolved,
    sm_fastmtt,
    sm_kinfit_resolved,
)
from analysis_configurations.bbtautau.constants import (
    ERAS,
    LEGACY_AVAILABLE_SAMPLES,
    SCOPES,
)
from analysis_configurations.bbtautau.tests.helpers import FakeArgs, output_names

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MAP_FASTMTT, MAP_KINFIT = str(FIXTURES / "fastmtt_quantities_map.json"), str(
    FIXTURES / "kinfit_quantities_map.json"
)
ENTRY_MODULES = (nmssm_fastmtt, sm_fastmtt, sm_kinfit_resolved, nmssm_kinfit_resolved)

FASTMTT_LEAVES = {"m_fastmtt", "pt_fastmtt", "eta_fastmtt", "phi_fastmtt"}
# The SM fixed-mass (125/125) fit exposes only these four, the NMSSM fit all 18.
SM_KINFIT_LEAVES = {"kinfit_convergence", "kinfit_chi2", "kinfit_prob", "kinfit_mHH"}
NMSSM_KINFIT_LEAVES = {
    f"kinfit_{quantity}{suffix}"
    for suffix in ("_YToBB", "_YToTauTau", "")
    for quantity in ("convergence", "mX", "mY", "mh", "chi2", "prob")
}


@pytest.mark.parametrize(
    "module", ENTRY_MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1]
)
def test_friend_entry_points_expose_friendtreeconfiguration(module):
    members = [name for name, _ in inspect.getmembers(module, inspect.isclass)]
    assert "FriendTreeConfiguration" in members
    assert (
        "Configuration" not in members
    )  # both markers would make generate_friends.run() raise


@pytest.mark.parametrize(
    "name,module",
    [("sm_fastmtt", sm_fastmtt), ("sm_kinfit_resolved", sm_kinfit_resolved)],
)
def test_sm_friend_era_gates_fire_before_build_config(name, module):
    with mock.patch.object(
        module, "build_config", side_effect=AssertionError("must not be called")
    ):
        with pytest.raises(ValueError, match="2024"):
            generate_friends.run(FakeArgs(name, "2024"))


@pytest.mark.parametrize(
    "module,quantities_map,expected",
    [
        (nmssm_fastmtt, MAP_FASTMTT, FASTMTT_LEAVES),
        (sm_fastmtt, MAP_FASTMTT, FASTMTT_LEAVES),
        (sm_kinfit_resolved, MAP_KINFIT, SM_KINFIT_LEAVES),
        (nmssm_kinfit_resolved, MAP_KINFIT, NMSSM_KINFIT_LEAVES),
    ],
    ids=lambda x: x.__name__.rsplit(".", 1)[-1] if inspect.ismodule(x) else None,
)
def test_friend_output_contracts(module, quantities_map, expected):
    config = module.build_config(
        "2018",
        "ttbar",
        ["mt"],
        {"none"},
        LEGACY_AVAILABLE_SAMPLES,
        list(getattr(module, "AVAILABLE_ERAS", ERAS)),
        SCOPES,
        quantities_map,
    )
    assert output_names(config, "mt") == expected
