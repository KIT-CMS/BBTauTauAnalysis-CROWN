"""SM HH kinematic-fit friend-tree entry point (resolved, fixed 125/125 GeV, Run-2 v15 eras)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .constants import ERAS_RUN2
from .friend_common import build_friend_config
from .producers import hhkinfit
from .quantities import output as q

AVAILABLE_ERAS = list(ERAS_RUN2)


def build_config(*args, **kwargs):
    return build_friend_config(
        [hhkinfit.SMHHKinFit],
        [q.kinfit_convergence, q.kinfit_chi2, q.kinfit_prob, q.kinfit_mHH],
        *args,
        **kwargs,
    )
