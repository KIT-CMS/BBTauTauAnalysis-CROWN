"""SM HH fake-factor friend-tree entry point with W, QCD + W + ttbar (friend ff_v7_w;
v7 spec E18, C15, P5). It differs from sm_fake_factors only in its payloads, so that
both friends build side by side from one checkout."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .friend_common import build_fake_factor_friend
from .sm_fake_factors import PAYLOAD_ERAS, payload_dirs  # noqa: F401  (PAYLOAD_ERAS: same eras)

# The processes the payloads of this entry point sum (read from their fractions)
PROCESSES = ("QCD", "Wjets", "ttbar")
# The QCD + W + ttbar payload of each payload era, relative to the analysis
# directory; all four follow from the v7 fake-factor measurement (6.8).
PAYLOADS = {}
# Payload directory per era
SM_PAYLOAD_DIRS = payload_dirs(PAYLOADS)
AVAILABLE_ERAS = list(SM_PAYLOAD_DIRS)


def build_config(era, *args, **kwargs):
    return build_fake_factor_friend(
        SM_PAYLOAD_DIRS[era], era, *args, processes=PROCESSES, **kwargs
    )
