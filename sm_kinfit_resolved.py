"""SM fixed-mass HH kinematic-fit friend-tree entry point (resolved).

Produces the Standard-Model non-resonant HH -> bb tautau kinematic fit with a
single, fixed mass hypothesis m(H->bb) = 125 GeV, m(H->tautau) = 125 GeV. It
reuses the SAME vendored fit engine as the NMSSM kinematic fit
(`nmssm_kinfit_resolved.py` / `hhkinfit::YHKinFit`), but runs it with a single
hypothesis pair instead of the NMSSM Y-mass scan, and exposes only the four
SM-named outputs (no mX/mY, no YToBB/YToTauTau split, no boosted variant):

  * kinfit_convergence
  * kinfit_chi2
  * kinfit_prob
  * kinfit_mHH

The friend build surface for the SM profile is currently 2018-only (mirroring
`sm_fastmtt.py`, Task 20). This is enforced by two independent gates:

  1. `AVAILABLE_ERAS` below is read by `generate_friends.py` BEFORE
     `build_config` is ever invoked.
  2. The explicit check as the first statement of `build_config` here, so that
     calling this module's `build_config` directly (bypassing
     `generate_friends.py`) is equally protected. It fires before
     `quantities_map` is touched.
"""
from __future__ import annotations  # needed for type annotations in > python 3.7
from typing import List, Union

from .producers import hhkinfit as hhkinfit
from .quantities import output as q
from code_generation.friend_trees import FriendTreeConfiguration

AVAILABLE_ERAS = ["2018"]


def build_config(
    era: str,
    sample: str,
    scopes: List[str],
    shifts: List[str],
    available_sample_types: List[str],
    available_eras: List[str],
    available_scopes: List[str],
    quantities_map: Union[str, None] = None,
):
    if era not in AVAILABLE_ERAS:
        raise ValueError(
            f"Config 'sm_kinfit_resolved' does not support era '{era}' "
            f"(supported: {AVAILABLE_ERAS})."
        )

    configuration = FriendTreeConfiguration(
        era,
        sample,
        scopes,
        shifts,
        available_sample_types,
        available_eras,
        available_scopes,
        quantities_map,
    )

    configuration.add_producers(
        ["mt", "et", "tt"],
        [
            hhkinfit.SMHHKinFit,
        ],
    )

    configuration.add_outputs(
        ["mt", "et", "tt"],
        [
            q.kinfit_convergence,
            q.kinfit_chi2,
            q.kinfit_prob,
            q.kinfit_mHH,
        ],
    )

    #########################
    # Finalize and validate the configuration
    #########################
    configuration.optimize()
    configuration.validate()
    configuration.report()
    return configuration.expanded_configuration()
