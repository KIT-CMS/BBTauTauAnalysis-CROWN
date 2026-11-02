"""SM HH fake-factor friend-tree entry point with W, QCD + W + ttbar (friend ff_v7b_w;
v7 spec E18, C15, P5). It differs from sm_fake_factors only in its payloads and in the
processes of et and mt, so that both friends build side by side from one checkout."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .friend_common import build_fake_factor_friend
from .sm_fake_factors import PAYLOAD_ERAS, payload_dirs  # noqa: F401  (PAYLOAD_ERAS: same eras)

# The processes the payloads of this entry point sum (read from their fractions):
# QCD + W + ttbar in et and mt; tt has no W+jets fake factor (v7 spec 6.8), so its
# legs sum QCD + ttbar as in sm_fake_factors, and ff_v7b_w of tt is built from them.
PROCESSES = ("QCD", "Wjets", "ttbar")
SCOPE_PROCESSES = {"et": PROCESSES, "mt": PROCESSES, "tt": ("QCD", "ttbar")}
# The QCD + W + ttbar payload of each payload era, relative to the analysis
# directory: the v7b measurement (6.8; payloads/fake_factors/sm/
# fake-factors-2026-10-19-w/README.md).
PAYLOADS = {
    era: f"payloads/fake_factors/sm/fake-factors-2026-10-19-w/{era}"
    for era in ("2016", "2017", "2018")
}
# Payload directory per era
SM_PAYLOAD_DIRS = payload_dirs(PAYLOADS)
AVAILABLE_ERAS = list(SM_PAYLOAD_DIRS)


def build_config(era, sample, scopes, *args, **kwargs):
    (scope,) = scopes  # a fake-factor friend has a single scope
    return build_fake_factor_friend(
        SM_PAYLOAD_DIRS[era], era, sample, scopes, *args,
        processes=SCOPE_PROCESSES[scope], **kwargs
    )
