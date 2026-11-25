# m3_abnv1_20261113

NN classifier payload of the friend `sm_nn_classifier` (nn spec 3.3, 3.4), installed with `bbtautau-nn install` on 2026-11-18 04:54:28 UTC (bbtautau-nn `22326e261895`).

| | |
|---|---|
| Eras | 2016preVFP, 2016postVFP, 2017, 2018 |
| Scopes | et, mt, tt |
| Classes (output order) | HH2B2Tau, tautau, Top, jetFakes, Other |
| Output | probabilities |
| Folds | 4: `model_k<n>_r<r>.onnx` scores the events with `event % n == r` |

The ONNX files of an export are stored once under `onnx/<source>/`; the manifest of every era and scope refers to them by a path relative to itself.

## Source `joint`: et, mt, tt

- export: `/ceph/sdaigler/nn/ladder/S2_M3_20261113/export/rep04`, `manifest.json` sha256 `114065f5fd95d6b620ee1fe89f05231377536520875da60c3d9a8e22dc7f8b85`
- run `m3_abnv1_20261113`, repetition 4, training commit `3c999bbfde23`
- onnxruntime closure: max |p_torch - p_ort| = 4.17e-07 (onnxruntime 1.25.0)
- training data: `v7b` `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/ml/v7b5_dedupe`, ['2016preVFP', '2016postVFP', '2017', '2018']
  - `2016preVFP`: profile `v7b5`, classes.json sha256 `50c11603bc8dfd8ac2124e15318c09ae72e13f53200482d5431c00a843be25b8`, ShapeSmith core/analysis fa3e7d1/cdb1c6b
  - `2016postVFP`: profile `v7b5`, classes.json sha256 `4ce51663225fbe8448927b358ff6e15a0bf06bd4cf823f2f8eb45f773c0673d1`, ShapeSmith core/analysis fa3e7d1/cdb1c6b
  - `2017`: profile `v7b5`, classes.json sha256 `1ba2b36ada1a5b2cfb4ac099fc94b58af425307abc271a862dd430d70c89d2be`, ShapeSmith core/analysis fa3e7d1/cdb1c6b
  - `2018`: profile `v7b5`, classes.json sha256 `68eff2ad9887c352cd5c4b95921b721964f92fb9de2d5f53b44f23aad7cc9c1b`, ShapeSmith core/analysis fa3e7d1/cdb1c6b
- inputs (49): `pt_1`, `eta_1`, `phi_1`, `mass_1`, `tau_decaymode_1`, `pt_2`, `eta_2`, `phi_2`, `tau_decaymode_2`, `bpair_pt_1`, `bpair_eta_1`, `bpair_phi_1`, `bpair_mass_1`, `bpair_btag_value_1`, `bpair_pt_2`, `bpair_eta_2`, `bpair_phi_2`, `bpair_mass_2`, `bpair_btag_value_2`, `jpt_1`, `jeta_1`, `jphi_1`, `jtag_value_1`, `jpt_2`, `jeta_2`, `jphi_2`, `jtag_value_2`, `met`, `metphi`, `pt_fastmtt`, `eta_fastmtt`, `phi_fastmtt`, `m_fastmtt`, `bpair_deltaR`, `bpair_m_inv`, `bpair_pt_dijet`, `deltaR_ditaupair`, `mjj`, `n_bjets`, `m_vis`, `mt_tot`, `pt_dijet`, `pt_vis`, `mt_1`, `mt_2`, `pzetamissvis`, `mass_tautaubb`, `era_index`, `channel_index`
- constants per era and scope:
  - `2016preVFP/et`: {"era_index": 0, "channel_index": 0, "tau_decaymode_1": -1.0}
  - `2016preVFP/mt`: {"era_index": 0, "channel_index": 1, "tau_decaymode_1": -1.0}
  - `2016preVFP/tt`: {"era_index": 0, "channel_index": 2}
  - `2016postVFP/et`: {"era_index": 1, "channel_index": 0, "tau_decaymode_1": -1.0}
  - `2016postVFP/mt`: {"era_index": 1, "channel_index": 1, "tau_decaymode_1": -1.0}
  - `2016postVFP/tt`: {"era_index": 1, "channel_index": 2}
  - `2017/et`: {"era_index": 2, "channel_index": 0, "tau_decaymode_1": -1.0}
  - `2017/mt`: {"era_index": 2, "channel_index": 1, "tau_decaymode_1": -1.0}
  - `2017/tt`: {"era_index": 2, "channel_index": 2}
  - `2018/et`: {"era_index": 3, "channel_index": 0, "tau_decaymode_1": -1.0}
  - `2018/mt`: {"era_index": 3, "channel_index": 1, "tau_decaymode_1": -1.0}
  - `2018/tt`: {"era_index": 3, "channel_index": 2}
- files:
  - `onnx/joint/model_k4_r0.onnx`: sha256 `edeacc90c3071e0368f14fdab9f7b6fbfb0dc200137ce8fabc6dd591a3c40171`
  - `onnx/joint/model_k4_r1.onnx`: sha256 `7aadd3e334a572d259d4caafaea3fb0af2033de82f9f6da0efcbd2a5130600eb`
  - `onnx/joint/model_k4_r2.onnx`: sha256 `10d714201fa625299a34818597e55939614aeaa9fe0eaba4732187e9b2ea8d3c`
  - `onnx/joint/model_k4_r3.onnx`: sha256 `d0e688ba0d647f444ed642363725864d5683750a034bfa6bdb6f2f768ba68428`

## Run configuration


```json
{
 "name": "m3_abnv1_20261113",
 "output_dir": "/ceph/sdaigler/nn/step2_20261113",
 "channels": [
  "et",
  "mt",
  "tt"
 ],
 "repetitions": 5,
 "folds": {
  "n": 4,
  "validation": "inner",
  "inner": 5,
  "salt": 0
 },
 "data": {
  "source": "v7b",
  "path": "/ceph/sdaigler/shapesmith/smrun2_binned_v7b/ml/v7b5_dedupe",
  "eras": [
   "2016preVFP",
   "2016postVFP",
   "2017",
   "2018"
  ],
  "inputs": [],
  "computed": [],
  "classes": [
   {
    "name": "HH2B2Tau",
    "processes": []
   },
   {
    "name": "tautau",
    "processes": []
   },
   {
    "name": "Top",
    "processes": []
   },
   {
    "name": "jetFakes",
    "processes": []
   },
   {
    "name": "Other",
    "processes": []
   }
  ],
  "subtraction": "drop",
  "ignore_labels": [],
  "columns": [],
  "btag_wp": null,
  "struck": []
 },
 "schema": {
  "tokens": [
   "leg1",
   "leg2",
   "b1",
   "b2",
   "j1",
   "j2",
   "met",
   "tautau"
  ],
  "hl": [
   "bpair_btag_value_1",
   "bpair_btag_value_2",
   "bpair_deltaR",
   "bpair_m_inv",
   "bpair_pt_1",
   "bpair_pt_dijet",
   "deltaR_ditaupair",
   "jpt_1",
   "m_fastmtt",
   "mjj",
   "n_bjets",
   "n_jets",
   "pt_fastmtt",
   "mtt_coll_approx",
   "m_vis",
   "mt_tot",
   "jpt_2",
   "pt_1",
   "pt_dijet",
   "pt_vis",
   "mt_1",
   "mt_2",
   "pzetamissvis",
   "mass_tautaubb",
   "pt_tautaubb"
  ],
  "missing": [],
  "struck": [
   "iso_1",
   "metSumEt",
   "pt_tautaubb",
   "mass_2",
   "n_jets"
  ],
  "btag_wp": {
   "2016preVFP": [
    0.1847,
    0.5467
   ],
   "2016postVFP": [
    0.1898,
    0.5538
   ],
   "2017": [
    0.1776,
    0.5755
   ],
   "2018": [
    0.161,
    0.5405
   ]
  }
 },
 "model": {
  "type": "evt",
  "dim": 96,
  "heads": 8,
  "particle_blocks": 2,
  "class_blocks": 1,
  "ffn_ratio": 4,
  "dropout": 0.0015749196020336184,
  "attention_dropout": 0.05,
  "pair_bias": true,
  "pair_hidden": 32,
  "hl_injection": true,
  "era_embedding": 8,
  "channel_embedding": 4,
  "binary_head": false
 },
 "training": {
  "recipe": "modern",
  "members": 5,
  "weights": "abs",
  "temperature": 1.0,
  "bce_lambda": 1.0,
  "label_smoothing": 0.02,
  "learning_rate": 0.0027498389745183884,
  "betas": [
   0.9,
   0.98
  ],
  "weight_decay": 0.07847178439275464,
  "warmup_epochs": 3,
  "epochs": 40,
  "final_lr": 0.01,
  "batch_size": 2048,
  "grad_clip": 1.0,
  "bf16": true,
  "ema": 0.999,
  "eta_flip": 0.5,
  "patience": 8
 },
 "evaluation": {
  "hh_bins": [
   0.0,
   0.2,
   0.3,
   0.35,
   0.4,
   0.45,
   0.5,
   0.55,
   0.6,
   0.65,
   0.7,
   0.75,
   0.8,
   0.82,
   0.84,
   0.86,
   0.88,
   0.9,
   0.92,
   0.94,
   0.96,
   0.98,
   1.0
  ]
 },
 "reference": null,
 "hpsearch": {
  "trials": 40,
  "epochs": 20,
  "prune_after": 5,
  "seed": 0,
  "latency_budget_us": 150.0,
  "latency_scale": 1.03,
  "latency_core": null
 },
 "parity": null,
 "proxy": {
  "categories": "k1",
  "binning": "data_blind",
  "systematics": "stat",
  "blinding": true,
  "replicas": 100,
  "replica_salt": 0,
  "cmssw_dir": "/work/sdaigler/smhtt_ul/CMSSW_14_1_9",
  "scram_arch": "el9_amd64_gcc12",
  "r_range": [
   -40.0,
   40.0
  ],
  "timeout": 7200.0
 }
}
```
