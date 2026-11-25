"""SM HH NN classifier friend-tree entry point (nn spec 3.4, N1, N21, N28): the scores of the models of a production
in the Run-2 eras, et, mt and tt, from the main n-tuple and the FastMTT friend (KingMaker friend mapping
``sm_nn_classifier: {friend_tag: <tag>, requires: [sm_fastmtt]}``, ``sm_fastmtt: {friend_tag: fastmtt}``).

Every model is a payload directory with one manifest per era and scope (payloads/nn_classifier/README.md) and the
prefix of its columns ``<prefix>predicted_class``, ``<prefix>predicted_max_value`` and ``<prefix>nn_score_<class>``
(-1 outside the gate, nn_gate.py). A missing era or scope of a model fails the configuration.
"""
from code_generation.friend_trees import FriendTreeConfiguration  # noqa: F401  (dispatcher check)

from .constants import ERAS_RUN2
from .friend_common import build_nn_classifier_friend
from .nn_payloads import NNModel  # noqa: F401  (the type of the entries of MODELS)

# The models of the production, with a new friend tag whenever the list or a payload changes. The shift production
# (v8 spec C28, V15, 5.3) evaluates the deployed model M3 (repetition 4) and the baseline AB_NV1 (repetition 0),
# both trained on v7b, installed by `bbtautau-nn install` (the README of each directory has the provenance). The
# prefixes are those of the ShapeSmith runs.
MODELS = (
    NNModel("payloads/nn_classifier/m3_abnv1_20261113", "nn_m3abnv1_"),
    NNModel("payloads/nn_classifier/m0_k4_v7b5_wp_abnv1", "nn_m0k4abnv1_"),
)
AVAILABLE_ERAS = list(ERAS_RUN2)


def build_config(*args, **kwargs):
    return build_nn_classifier_friend(MODELS, *args, **kwargs)
