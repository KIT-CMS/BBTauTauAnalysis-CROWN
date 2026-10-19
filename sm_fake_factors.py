"""SM HH fake-factor friend-tree entry point, QCD + ttbar (friend ff_v7b; the Run-2 eras
with a measured payload). The QCD + W + ttbar variant is sm_fake_factors_w (v7 spec
E18, C15, P5)."""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .constants import ERAS_RUN2
from .friend_common import build_fake_factor_friend

# The payload era of each era: 2016preVFP and 2016postVFP share one payload,
# measured on both halves together.
PAYLOAD_ERAS = {"2016preVFP": "2016", "2016postVFP": "2016", "2017": "2017", "2018": "2018"}


def payload_dirs(payloads):
    """Payload directory per era, for the eras whose payload era is in ``payloads``."""
    return {era: payloads[PAYLOAD_ERAS[era]] for era in ERAS_RUN2 if PAYLOAD_ERAS[era] in payloads}


# The processes the payloads of this entry point sum (read from their fractions)
PROCESSES = ("QCD", "ttbar")
# The measured payload of each payload era, relative to the analysis directory:
# the v7b measurement (smrun2_binned_v7 data, smrun2_binned_v7b MC and embedding;
# payloads/fake_factors/sm/fake-factors-2026-10-19/README.md). The v6 2018 payload
# fake-factors-2026-10-09 stays for reference.
PAYLOADS = {
    era: f"payloads/fake_factors/sm/fake-factors-2026-10-19/{era}"
    for era in ("2016", "2017", "2018")
}
# Payload directory per era
SM_PAYLOAD_DIRS = payload_dirs(PAYLOADS)
AVAILABLE_ERAS = list(SM_PAYLOAD_DIRS)


def build_config(era, *args, **kwargs):
    return build_fake_factor_friend(
        SM_PAYLOAD_DIRS[era], era, *args, processes=PROCESSES, **kwargs
    )
