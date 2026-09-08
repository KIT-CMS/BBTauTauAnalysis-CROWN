"""NMSSM HH/YH kinematic-fit friend-tree entry point (resolved, Y-mass scan)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .friend_common import build_friend_config
from .producers import hhkinfit
from .quantities import output as q


def build_config(*args, **kwargs):
    return build_friend_config(
        [hhkinfit.YHKinFit],
        [
            q.kinfit_convergence_YToBB,
            q.kinfit_mX_YToBB,
            q.kinfit_mY_YToBB,
            q.kinfit_mh_YToBB,
            q.kinfit_chi2_YToBB,
            q.kinfit_prob_YToBB,
            q.kinfit_convergence_YToTauTau,
            q.kinfit_mX_YToTauTau,
            q.kinfit_mY_YToTauTau,
            q.kinfit_mh_YToTauTau,
            q.kinfit_chi2_YToTauTau,
            q.kinfit_prob_YToTauTau,
            q.kinfit_convergence,
            q.kinfit_mX,
            q.kinfit_mY,
            q.kinfit_mh,
            q.kinfit_chi2,
            q.kinfit_prob,
        ],
        *args,
        **kwargs,
    )
