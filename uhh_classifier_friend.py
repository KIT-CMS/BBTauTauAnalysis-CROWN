"""
Python friend config for the UHH bbtautau classifier, evaluated by KingMaker's
PythonFriend task (see the KingMaker README, "Python (ML) friends").

The model (classifier_22_23_v3, tensorflow SavedModels) is trained with 5-fold cross
validation, one SavedModel per fold in payloads/ml/uhh_classifier/fold<i>, each an
ensemble of five trainings. It expects 49 continuous and 7 categorical features in a
fixed order, with all objects rotated such that the di-lepton system has phi = 0. The
features are built in evaluate() from the pt/eta/phi/mass quantities of the ntuples,
mapped to the model's object names via input_map. Features and preprocessing are the
same as for the UHH neutrino regression (uhh_nu_regression_friend).

Folds (model documentation): fold i is evaluated on the events with event % 5 == i, the
events its training did not see. Data and embedding use the same assignment, so every
event gets exactly one model. The training used 2022-2023, applying it to 2018 is
intended.

Missing values follow the convention of the model's authors: everything missing is set
to EMPTY_FLOAT = -99999.0 / EMPTY_INT = -99999, and these values are masked in the
preprocessing, right before the model call (mask_empty()). The model cannot take them
itself: its graph standardizes the continuous inputs without any masking, and EMPTY_INT
is no known category of its embedding lookup.

Masked values (MASK_VALUES), the padding used in the training: kinematics of missing
objects (fatjet, b-jet pair) 0, b-tag values -1.

CvsB, CvsL scores: the UParTAK4 CvB/CvL of the regressed b-jet pair
(bpair_btag_cv{b,l}_regressed_{1,2}), which only productions from 30_10_26 on contain.
HHbtag score: not in the sm_config ntuples, and never missing for existing b-jets in the
training. For existing b-jets it is therefore set to its training mean
(MISSING_SCORE_VALUES), which the normalization maps to exactly 0. The HHbtag score and
the fatjet are filled via empty_values, so the production needs --allow-empty-values.

Outputs: softmax scores of the classes HH, TT, DY (in this order, model documentation).

input_ranges/input_groups are only used by the sensitivity test (--sensitivity-test of
ProducePythonFriends). The ranges are the physically expected ones for the scope; the
test always has a b-jet pair and a fatjet, so that their features matter, and the masked
rows show what setting the HHbtag scores and the fatjet to empty_values (as in the
production) changes. The HHbtag width is a guess, the model description gives none. The
event number only selects the fold, its range covers all folds.
"""

from __future__ import annotations

import os

MODEL = "payloads/ml/uhh_classifier"
N_FOLDS = 5
EMPTY_FLOAT = -99999.0
EMPTY_INT = -99999
CHANNELS = {"mt": 0, "et": 1, "tt": 2}

CLASSES = ["hh", "tt", "dy"]
OUTPUTS = [f"uhh_dnn_{c}" for c in CLASSES]

# continuous model features, in the order the model expects them
CONTINUOUS_FEATURES = (
    ["met_px", "met_py", "met_cov00", "met_cov01", "met_cov11"]
    + [f"lep{i}_{c}" for i in (1, 2) for c in ("px", "py", "pz", "e")]
    + [
        f"bjet{i}_{c}"
        for i in (1, 2)
        for c in ("px", "py", "pz", "e", "tag_b", "tag_cvsb", "tag_cvsl", "hhbtag")
    ]
    + [f"fatjet_{c}" for c in ("px", "py", "pz", "e")]
    + [
        f"{system}_{c}"
        for system in ("htt", "hbb", "htthbb", "httfatjet")
        for c in ("e", "px", "py", "pz")
    ]
)
CATEGORICAL_FEATURES = [
    "channel",
    "dm1",
    "dm2",
    "charge1",
    "charge2",
    "is_boosted",
    "has_bjet_pair",
]

# value replacing EMPTY in the preprocessing, 0 unless given here (see the docstring)
MASK_VALUES = {
    f"bjet{i}_{tag}": -1.0
    for i in (1, 2)
    for tag in ("tag_b", "tag_cvsb", "tag_cvsl", "hhbtag")
}

# training means of the scores missing in the ntuples, used for existing b-jets only
MISSING_SCORE_VALUES = {
    "bjet1_hhbtag": 1.027,
    "bjet2_hhbtag": 0.755,
}

# model object name -> ntuple quantity
INPUT_MAP = {
    "met_pt": "met",
    "met_phi": "metphi",
    "met_cov00": "metcov00",
    "met_cov01": "metcov01",
    "met_cov11": "metcov11",
    "lep1_pt": "pt_1",
    "lep1_eta": "eta_1",
    "lep1_phi": "phi_1",
    "lep1_mass": "mass_1",
    "lep2_pt": "pt_2",
    "lep2_eta": "eta_2",
    "lep2_phi": "phi_2",
    "lep2_mass": "mass_2",
    # b-jet pair with b-jet energy regression
    "bjet1_pt": "bpair_pt_regressed_1",
    "bjet1_eta": "bpair_eta_regressed_1",
    "bjet1_phi": "bpair_phi_regressed_1",
    "bjet1_mass": "bpair_mass_regressed_1",
    "bjet1_tag_b": "bpair_btag_value_regressed_1",
    "bjet1_tag_cvsb": "bpair_btag_cvb_regressed_1",
    "bjet1_tag_cvsl": "bpair_btag_cvl_regressed_1",
    "bjet2_pt": "bpair_pt_regressed_2",
    "bjet2_eta": "bpair_eta_regressed_2",
    "bjet2_phi": "bpair_phi_regressed_2",
    "bjet2_mass": "bpair_mass_regressed_2",
    "bjet2_tag_b": "bpair_btag_value_regressed_2",
    "bjet2_tag_cvsb": "bpair_btag_cvb_regressed_2",
    "bjet2_tag_cvsl": "bpair_btag_cvl_regressed_2",
    "dm1": "tau_decaymode_1",
    "dm2": "tau_decaymode_2",
    "charge1": "q_1",
    "charge2": "q_2",
}

# not in the ntuples
EMPTY_VALUES = {
    name: EMPTY_FLOAT
    for name in [
        "bjet1_hhbtag",
        "bjet2_hhbtag",
        "fatjet_px",
        "fatjet_py",
        "fatjet_pz",
        "fatjet_e",
    ]
}

# the event number selects the fold
INPUTS = list(INPUT_MAP) + list(EMPTY_VALUES) + ["event"]

PI = 3.141592653589793
TAU_LEG = {
    "pt": {"min": 20.0, "max": 200.0},
    "eta": {"min": -2.3, "max": 2.3},
    "mass": {"min": 0.14, "max": 1.8},
    "dm": {"values": [0, 1, 10, 11]},
}
# first leg of the channel (the second one is always a hadronic tau)
FIRST_LEG = {
    "mt": {
        "pt": {"min": 20.0, "max": 200.0},
        "eta": {"min": -2.4, "max": 2.4},
        "mass": {"values": [0.10566]},
        "dm": {"values": [-1]},
    },
    "et": {
        "pt": {"min": 25.0, "max": 200.0},
        "eta": {"min": -2.5, "max": 2.5},
        "mass": {"values": [0.000511]},
        "dm": {"values": [-1]},
    },
    "tt": TAU_LEG,
}


def met_cov01(rng, n, data):
    # positive definite covariance: |cov01| < sqrt(cov00 * cov11)
    import numpy as np

    return rng.uniform(-0.8, 0.8, n) * np.sqrt(data["met_cov00"] * data["met_cov11"])


def fatjet_e(rng, n, data):
    import numpy as np

    mass = rng.uniform(60.0, 200.0, n)
    return np.sqrt(
        data["fatjet_px"] ** 2 + data["fatjet_py"] ** 2 + data["fatjet_pz"] ** 2 + mass**2
    )


def input_ranges(scope):
    ranges = {
        "met_pt": {"min": 0.0, "max": 200.0},
        "met_phi": {"min": -PI, "max": PI},
        "met_cov00": {"min": 100.0, "max": 1500.0},
        "met_cov01": met_cov01,
        "met_cov11": {"min": 100.0, "max": 1500.0},
        "fatjet_px": {"min": -500.0, "max": 500.0},
        "fatjet_py": {"min": -500.0, "max": 500.0},
        "fatjet_pz": {"min": -1000.0, "max": 1000.0},
        "fatjet_e": fatjet_e,
        "bjet1_hhbtag": {"mean": 1.027, "std": 0.3},
        "bjet2_hhbtag": {"mean": 0.755, "std": 0.3},
        # every fold gets events
        "event": {"values": list(range(N_FOLDS))},
    }
    for i, leg in ((1, FIRST_LEG[scope]), (2, TAU_LEG)):
        ranges.update(
            {
                f"lep{i}_pt": leg["pt"],
                f"lep{i}_eta": leg["eta"],
                f"lep{i}_phi": {"min": -PI, "max": PI},
                f"lep{i}_mass": leg["mass"],
                f"dm{i}": leg["dm"],
                f"charge{i}": {"values": [-1, 1]},
            }
        )
        ranges.update(
            {
                f"bjet{i}_pt": {"min": 20.0, "max": 300.0},
                f"bjet{i}_eta": {"min": -2.5, "max": 2.5},
                f"bjet{i}_phi": {"min": -PI, "max": PI},
                f"bjet{i}_mass": {"min": 4.0, "max": 40.0},
                f"bjet{i}_tag_b": {"min": 0.0, "max": 1.0},
                f"bjet{i}_tag_cvsb": {"min": 0.0, "max": 1.0},
                f"bjet{i}_tag_cvsl": {"min": 0.0, "max": 1.0},
            }
        )
    return ranges


INPUT_GROUPS = {
    "met": ["met_pt", "met_phi"],
    "met_cov": ["met_cov00", "met_cov01", "met_cov11"],
    "lep1": ["lep1_pt", "lep1_eta", "lep1_phi", "lep1_mass"],
    "lep2": ["lep2_pt", "lep2_eta", "lep2_phi", "lep2_mass"],
    "bjet1_kin": ["bjet1_pt", "bjet1_eta", "bjet1_phi", "bjet1_mass"],
    "bjet2_kin": ["bjet2_pt", "bjet2_eta", "bjet2_phi", "bjet2_mass"],
    "tag_b": ["bjet1_tag_b", "bjet2_tag_b"],
    "cvsb_cvsl": ["bjet1_tag_cvsb", "bjet1_tag_cvsl", "bjet2_tag_cvsb", "bjet2_tag_cvsl"],
    "hhbtag": ["bjet1_hhbtag", "bjet2_hhbtag"],
    "fatjet": ["fatjet_px", "fatjet_py", "fatjet_pz", "fatjet_e"],
}


def build_config(era, sample_type, scope, shifts):
    return {
        "evaluations": [
            {
                "shift": "nominal",
                "model": MODEL,
                "inputs": INPUTS,
                "outputs": OUTPUTS,
            },
        ],
        "input_map": INPUT_MAP,
        "empty_values": EMPTY_VALUES,
        "input_ranges": input_ranges(scope),
        "input_groups": INPUT_GROUPS,
        "batch_size": 50_000,
    }


def load_session(path):
    """
    Only the serving signature of a SavedModel, loaded into a TF1 session: much faster
    than tf.saved_model.load, which restores every function of the Keras object graph
    (same outputs). Returns the session, the input tensor names (continuous,
    categorical) and the output name.
    """
    import tensorflow as tf

    graph = tf.Graph()
    session = tf.compat.v1.Session(
        graph=graph,
        config=tf.compat.v1.ConfigProto(
            # stay within the cores requested from the batch system
            intra_op_parallelism_threads=int(os.environ.get("PYTHON_FRIEND_NTHREADS", 1)),
            inter_op_parallelism_threads=1,
        ),
    )
    with graph.as_default():
        meta_graph = tf.compat.v1.saved_model.loader.load(session, ["serve"], path)
    signature = meta_graph.signature_def["serving_default"]
    (output,) = signature.outputs.values()
    inputs = (signature.inputs["cont_input"].name, signature.inputs["cat_input"].name)
    return session, inputs, output.name


def load_model(path, evaluation):
    return [load_session(os.path.join(path, f"fold{i}")) for i in range(N_FOLDS)]


def p4(pt, eta, phi, mass):
    """
    Cartesian (px, py, pz, e) from pt, eta, phi, mass.
    """
    import numpy as np

    pt, eta, phi, mass = (np.asarray(x, dtype=np.float64) for x in (pt, eta, phi, mass))
    px, py, pz = pt * np.cos(phi), pt * np.sin(phi), pt * np.sinh(eta)
    return px, py, pz, np.sqrt(px**2 + py**2 + pz**2 + mass**2)


def rotate(px, py, ref_phi):
    import numpy as np

    new_phi = np.arctan2(py, px) + ref_phi
    pt = np.sqrt(px**2 + py**2)
    return pt * np.cos(new_phi), pt * np.sin(new_phi)


def mask_empty(continuous, categorical):
    """
    Preprocessing: replace EMPTY values by MASK_VALUES before the model call.
    """
    import numpy as np

    mask_values = np.array(
        [MASK_VALUES.get(name, 0.0) for name in CONTINUOUS_FEATURES], dtype=np.float32
    )
    continuous = np.where(continuous == EMPTY_FLOAT, mask_values, continuous)
    empty_categorical = (categorical == EMPTY_INT).any(axis=0)
    if empty_categorical.any():
        names = [n for n, e in zip(CATEGORICAL_FEATURES, empty_categorical) if e]
        raise ValueError(f"EMPTY_INT in categorical features {names}, cannot be masked")
    return continuous, categorical


def model_inputs(data, scope):
    """
    Continuous and categorical model features (masked), and the di-lepton phi of the
    rotation.
    """
    import numpy as np

    n = len(data["lep1_pt"])
    lep1 = p4(data["lep1_pt"], data["lep1_eta"], data["lep1_phi"], data["lep1_mass"])
    lep2 = p4(data["lep2_pt"], data["lep2_eta"], data["lep2_phi"], data["lep2_mass"])
    bjet1 = p4(
        data["bjet1_pt"], data["bjet1_eta"], data["bjet1_phi"], data["bjet1_mass"]
    )
    bjet2 = p4(
        data["bjet2_pt"], data["bjet2_eta"], data["bjet2_phi"], data["bjet2_mass"]
    )
    met = p4(data["met_pt"], np.zeros(n), data["met_phi"], np.zeros(n))
    fatjet = tuple(
        np.asarray(data[f"fatjet_{c}"], dtype=np.float64)
        for c in ("px", "py", "pz", "e")
    )
    htt = tuple(a + b for a, b in zip(lep1, lep2))
    hbb = tuple(a + b for a, b in zip(bjet1, bjet2))
    htthbb = tuple(a + b for a, b in zip(htt, hbb))
    httfatjet = tuple(a + b for a, b in zip(htt, fatjet))

    # rotate everything such that the di-lepton system has phi = 0
    dilep_phi = np.arctan2(lep1[1] + lep2[1], lep1[0] + lep2[0])

    def rotated(vector):
        px, py = rotate(vector[0], vector[1], -dilep_phi)
        return px, py, vector[2], vector[3]

    lep1, lep2, bjet1, bjet2, met, fatjet, htt, hbb, htthbb, httfatjet = (
        rotated(v)
        for v in (lep1, lep2, bjet1, bjet2, met, fatjet, htt, hbb, htthbb, httfatjet)
    )

    # missing objects are EMPTY: the ntuples store -10 for a missing b-jet pair, the
    # fatjet is EMPTY via empty_values. Set after the kinematics, so EMPTY values are
    # never rotated or summed into other features.
    has_bjet_pair = data["bjet1_pt"] > 0
    is_boosted = data["fatjet_e"] != EMPTY_FLOAT

    def where(present, values):
        return np.where(present, values, EMPTY_FLOAT)

    features = {
        "met_px": met[0],
        "met_py": met[1],
        "met_cov00": data["met_cov00"],
        "met_cov01": data["met_cov01"],
        "met_cov11": data["met_cov11"],
    }
    for name, vector, present in (
        ("lep1", lep1, True),
        ("lep2", lep2, True),
        ("bjet1", bjet1, has_bjet_pair),
        ("bjet2", bjet2, has_bjet_pair),
        ("fatjet", fatjet, is_boosted),
        ("htt", htt, True),
        ("hbb", hbb, has_bjet_pair),
        ("htthbb", htthbb, has_bjet_pair),
        ("httfatjet", httfatjet, is_boosted),
    ):
        for c, values in zip(("px", "py", "pz", "e"), vector):
            features[f"{name}_{c}"] = where(present, values)
    for i in (1, 2):
        for tag in ("tag_b", "tag_cvsb", "tag_cvsl", "hhbtag"):
            name = f"bjet{i}_{tag}"
            score = data[name]
            if name in MISSING_SCORE_VALUES:
                score = np.where(
                    score == EMPTY_FLOAT, MISSING_SCORE_VALUES[name], score
                )
            features[name] = where(has_bjet_pair, score)
    categorical = {
        "channel": np.full(n, CHANNELS[scope]),
        "dm1": data["dm1"],
        "dm2": data["dm2"],
        "charge1": data["charge1"],
        "charge2": data["charge2"],
        "is_boosted": is_boosted,
        "has_bjet_pair": has_bjet_pair,
    }
    continuous = np.stack(
        [features[name] for name in CONTINUOUS_FEATURES], axis=1
    ).astype(np.float32)
    categorical = np.stack(
        [categorical[name] for name in CATEGORICAL_FEATURES], axis=1
    ).astype(np.int32)
    continuous, categorical = mask_empty(continuous, categorical)
    return continuous, categorical, dilep_phi


def evaluate(model, data, evaluation):
    import numpy as np

    continuous, categorical, _ = model_inputs(data, evaluation["scope"])
    fold = np.asarray(data["event"]) % N_FOLDS
    scores = np.full((len(fold), len(CLASSES)), np.nan, dtype=np.float32)
    for i, (session, (cont_input, cat_input), output) in enumerate(model):
        selected = fold == i
        if not selected.any():
            continue
        scores[selected] = session.run(
            output,
            {cont_input: continuous[selected], cat_input: categorical[selected]},
        )
    return {output: scores[:, i] for i, output in enumerate(OUTPUTS)}
