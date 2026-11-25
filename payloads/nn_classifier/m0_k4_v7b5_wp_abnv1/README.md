# m0_k4_v7b5_wp_abnv1

NN classifier payload of the friend `sm_nn_classifier` (nn spec 3.3, 3.4), installed with `bbtautau-nn install` on 2026-11-09 22:10:59 UTC (bbtautau-nn `0c8a5752e96d` (uncommitted changes)).

| | |
|---|---|
| Eras | 2016preVFP, 2016postVFP, 2017, 2018 |
| Scopes | et, mt, tt |
| Classes (output order) | HH2B2Tau, tautau, Top, jetFakes, Other |
| Output | probabilities |
| Folds | 4: `model_k<n>_r<r>.onnx` scores the events with `event % n == r` |

The ONNX files of an export are stored once under `onnx/<source>/`; the manifest of every era and scope refers to them by a path relative to itself.

## Source `et`: et

- export: `/ceph/sdaigler/nn/ladder/AB_NV1/export/et/rep00`, `manifest.json` sha256 `4ab6fae582af8771c8705c5475604a86d835684b34a5fedb84d1f25ea6493ea7`
- run `m0_k4_v7b5_wp_abnv1`, repetition 0, training commit `90cdd5cb99a3` (uncommitted changes)
- onnxruntime closure: max |p_torch - p_ort| = 5.96e-07 (onnxruntime 1.25.0)
- training data: `v7b` `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/ml/v7b5`, ['2016preVFP', '2016postVFP', '2017', '2018']
  - `2016preVFP`: profile `v7b5`, classes.json sha256 `50c11603bc8dfd8ac2124e15318c09ae72e13f53200482d5431c00a843be25b8`, ShapeSmith core/analysis 33960fc/65deb42
  - `2016postVFP`: profile `v7b5`, classes.json sha256 `4ce51663225fbe8448927b358ff6e15a0bf06bd4cf823f2f8eb45f773c0673d1`, ShapeSmith core/analysis 33960fc/65deb42
  - `2017`: profile `v7b5`, classes.json sha256 `1ba2b36ada1a5b2cfb4ac099fc94b58af425307abc271a862dd430d70c89d2be`, ShapeSmith core/analysis 33960fc/65deb42
  - `2018`: profile `v7b5`, classes.json sha256 `68eff2ad9887c352cd5c4b95921b721964f92fb9de2d5f53b44f23aad7cc9c1b`, ShapeSmith core/analysis 33960fc/65deb42
- inputs (27): `bpair_btag_value_1`, `bpair_btag_value_2`, `bpair_deltaR`, `bpair_m_inv`, `bpair_pt_1`, `bpair_pt_dijet`, `deltaR_ditaupair`, `jpt_1`, `m_fastmtt`, `mjj`, `n_bjets`, `pt_fastmtt`, `m_vis`, `mt_tot`, `jpt_2`, `pt_1`, `pt_dijet`, `pt_vis`, `eta_1`, `phi_1`, `mass_1`, `pt_2`, `eta_2`, `phi_2`, `met`, `metphi`, `era_index`
- constants per era and scope:
  - `2016preVFP/et`: {"era_index": 0}
  - `2016postVFP/et`: {"era_index": 1}
  - `2017/et`: {"era_index": 2}
  - `2018/et`: {"era_index": 3}
- files:
  - `onnx/et/model_k4_r0.onnx`: sha256 `b1e43bfb0125ed9a4c7848bc9d9395ddcb384ec001ef35d56b7dec8718639650`
  - `onnx/et/model_k4_r1.onnx`: sha256 `c420208aaf9087e030eec1b9c3b8dada3c0e0f377960dda33c12982f7f125d28`
  - `onnx/et/model_k4_r2.onnx`: sha256 `036b31cbb1d60cbff99198a1aaa12859835b0702f51bfcdc8cb01be9d4e3eab8`
  - `onnx/et/model_k4_r3.onnx`: sha256 `23630c3e302ca06de60295d54bc71086490d12f9fccec4716062cf5bf8795785`

## Source `mt`: mt

- export: `/ceph/sdaigler/nn/ladder/AB_NV1/export/mt/rep00`, `manifest.json` sha256 `798418ec1f46771b15084aca9ff9d3021a1177de418d303bbb9c35c2c05d3bb6`
- run `m0_k4_v7b5_wp_abnv1`, repetition 0, training commit `90cdd5cb99a3` (uncommitted changes)
- onnxruntime closure: max |p_torch - p_ort| = 4.17e-07 (onnxruntime 1.25.0)
- training data: `v7b` `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/ml/v7b5`, ['2016preVFP', '2016postVFP', '2017', '2018']
  - `2016preVFP`: profile `v7b5`, classes.json sha256 `50c11603bc8dfd8ac2124e15318c09ae72e13f53200482d5431c00a843be25b8`, ShapeSmith core/analysis 33960fc/65deb42
  - `2016postVFP`: profile `v7b5`, classes.json sha256 `4ce51663225fbe8448927b358ff6e15a0bf06bd4cf823f2f8eb45f773c0673d1`, ShapeSmith core/analysis 33960fc/65deb42
  - `2017`: profile `v7b5`, classes.json sha256 `1ba2b36ada1a5b2cfb4ac099fc94b58af425307abc271a862dd430d70c89d2be`, ShapeSmith core/analysis 33960fc/65deb42
  - `2018`: profile `v7b5`, classes.json sha256 `68eff2ad9887c352cd5c4b95921b721964f92fb9de2d5f53b44f23aad7cc9c1b`, ShapeSmith core/analysis 33960fc/65deb42
- inputs (27): `bpair_btag_value_1`, `bpair_btag_value_2`, `bpair_deltaR`, `bpair_m_inv`, `bpair_pt_1`, `bpair_pt_dijet`, `deltaR_ditaupair`, `jpt_1`, `m_fastmtt`, `mjj`, `n_bjets`, `pt_fastmtt`, `m_vis`, `mt_tot`, `jpt_2`, `pt_1`, `pt_dijet`, `pt_vis`, `eta_1`, `phi_1`, `mass_1`, `pt_2`, `eta_2`, `phi_2`, `met`, `metphi`, `era_index`
- constants per era and scope:
  - `2016preVFP/mt`: {"era_index": 0}
  - `2016postVFP/mt`: {"era_index": 1}
  - `2017/mt`: {"era_index": 2}
  - `2018/mt`: {"era_index": 3}
- files:
  - `onnx/mt/model_k4_r0.onnx`: sha256 `d56b4f57735a4873c92afacb4a39b470b62486acffab27813f25c98c3b512bcb`
  - `onnx/mt/model_k4_r1.onnx`: sha256 `a7f85ac9a1641b1ab63a766bc0bcc39130419508e347f16a8b7408cdc1f78b52`
  - `onnx/mt/model_k4_r2.onnx`: sha256 `a8aa4ca940889fe9363eaf1c739f05eba95c6f998311c24a0816cec1c364c8b5`
  - `onnx/mt/model_k4_r3.onnx`: sha256 `910b4057efec11534c9757fc04c686665ceb9395cdec21222737655da12c1781`

## Source `tt`: tt

- export: `/ceph/sdaigler/nn/ladder/AB_NV1/export/tt/rep00`, `manifest.json` sha256 `4324643a0188c8a834c9cbb96c475f653a6da21cf4c52a139e7d1f37959a79aa`
- run `m0_k4_v7b5_wp_abnv1`, repetition 0, training commit `90cdd5cb99a3` (uncommitted changes)
- onnxruntime closure: max |p_torch - p_ort| = 4.17e-07 (onnxruntime 1.25.0)
- training data: `v7b` `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/ml/v7b5`, ['2016preVFP', '2016postVFP', '2017', '2018']
  - `2016preVFP`: profile `v7b5`, classes.json sha256 `50c11603bc8dfd8ac2124e15318c09ae72e13f53200482d5431c00a843be25b8`, ShapeSmith core/analysis 33960fc/65deb42
  - `2016postVFP`: profile `v7b5`, classes.json sha256 `4ce51663225fbe8448927b358ff6e15a0bf06bd4cf823f2f8eb45f773c0673d1`, ShapeSmith core/analysis 33960fc/65deb42
  - `2017`: profile `v7b5`, classes.json sha256 `1ba2b36ada1a5b2cfb4ac099fc94b58af425307abc271a862dd430d70c89d2be`, ShapeSmith core/analysis 33960fc/65deb42
  - `2018`: profile `v7b5`, classes.json sha256 `68eff2ad9887c352cd5c4b95921b721964f92fb9de2d5f53b44f23aad7cc9c1b`, ShapeSmith core/analysis 33960fc/65deb42
- inputs (27): `bpair_btag_value_1`, `bpair_btag_value_2`, `bpair_deltaR`, `bpair_m_inv`, `bpair_pt_1`, `bpair_pt_dijet`, `deltaR_ditaupair`, `jpt_1`, `m_fastmtt`, `mjj`, `n_bjets`, `pt_fastmtt`, `m_vis`, `mt_tot`, `jpt_2`, `pt_1`, `pt_dijet`, `pt_vis`, `eta_1`, `phi_1`, `mass_1`, `pt_2`, `eta_2`, `phi_2`, `met`, `metphi`, `era_index`
- constants per era and scope:
  - `2016preVFP/tt`: {"era_index": 0}
  - `2016postVFP/tt`: {"era_index": 1}
  - `2017/tt`: {"era_index": 2}
  - `2018/tt`: {"era_index": 3}
- files:
  - `onnx/tt/model_k4_r0.onnx`: sha256 `6a12473afac181a3d8df1d1a03d9b697065c6162e363d16527ca1a79d7ef8cb8`
  - `onnx/tt/model_k4_r1.onnx`: sha256 `a930d0878612441f8301a9d31d20c4f71af4dcfe983f2088e980a3cda6f67f53`
  - `onnx/tt/model_k4_r2.onnx`: sha256 `67cbcbb31327087ebd20cf2a0ccffd0eb5a30d92b7a997c5071a808dcceee028`
  - `onnx/tt/model_k4_r3.onnx`: sha256 `8d19cd095776da21b009e5eb7892758ec184c553882e5048642e43a0e5921d16`

## Run configuration


```json
{
 "name": "m0_k4_v7b5_wp_abnv1",
 "output_dir": "/ceph/sdaigler/nn",
 "channels": [
  "et",
  "mt",
  "tt"
 ],
 "repetitions": 10,
 "folds": {
  "n": 4,
  "validation": "residue",
  "inner": 5,
  "salt": 0
 },
 "data": {
  "source": "v7b",
  "path": "/ceph/sdaigler/shapesmith/smrun2_binned_v7b/ml/v7b5",
  "eras": [
   "2016preVFP",
   "2016postVFP",
   "2017",
   "2018"
  ],
  "inputs": [
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
   "pt_fastmtt",
   "mtt_coll_approx",
   "m_vis",
   "mt_tot",
   "jpt_2",
   "pt_1",
   "pt_dijet",
   "pt_vis"
  ],
  "computed": [
   "mtt_coll_approx"
  ],
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
  "btag_wp": [
   [
    "2016preVFP",
    [
     0.1847,
     0.5467
    ]
   ],
   [
    "2016postVFP",
    [
     0.1898,
     0.5538
    ]
   ],
   [
    "2017",
    [
     0.1776,
     0.5755
    ]
   ],
   [
    "2018",
    [
     0.161,
     0.5405
    ]
   ]
  ],
  "struck": [
   "mass_2",
   "n_jets"
  ]
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
  "struck": [],
  "btag_wp": null
 },
 "model": {
  "type": "thesis_mlp",
  "hidden": [
   50,
   50
  ],
  "batch_norm": true,
  "dropout": 0.2
 },
 "training": {
  "recipe": "thesis",
  "weights": "balanced",
  "loss": "thesis_nll",
  "learning_rate": 0.0001,
  "weight_decay": 0.001,
  "max_epochs": 10000,
  "patience": 150,
  "checkpoint": "best"
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
