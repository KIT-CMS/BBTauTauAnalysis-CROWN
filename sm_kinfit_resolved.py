"""SM HH kinematic-fit friend-tree entry point (resolved, fixed 125/125 GeV, 2018 only)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .friend_common import build_friend_config
from .producers import hhkinfit
from .quantities import output as q

AVAILABLE_ERAS = ["2018"]


def build_config(*args, **kwargs):
    return build_friend_config(
        [hhkinfit.SMHHKinFit],
        [q.kinfit_convergence, q.kinfit_chi2, q.kinfit_prob, q.kinfit_mHH],
        *args,
        **kwargs,
    )
