# Tau trigger payloads of the tt embedding

`Run2-<era>-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding<era>UL.json.gz` (era 2016preVFP,
2016postVFP, 2017, 2018) holds the efficiency in data of the tau leg of the di-tau trigger of one Run-2 era
(NanoAOD v15), DeepTau2018v2p5, in two isolation classes of the tau. The tt embedding has no trigger
requirement and is weighted with this efficiency per tau (v7 spec E33, variant A; docs v7_tt_emb_trigger
12.6): `embedding_run2_v15.py` reads the file of its era through `tt_embedding_trigger_eff_file`
(`TT_EMBEDDING_TRIGGER_EFFICIENCIES[era]`) into `trg_effdata_emb_Medium_<leg>` (wp `Medium`) and
`trg_effdata_emb_AntiMedium_<leg>` (wp `VVVLoose_not_Medium`). They replace the POG v15 eff_data
(Medium, and VVVLoose for the anti-isolated class) used until this measurement; the KIT file
`data/embedding/tau_trigger<era>_UL.json.gz` (DeepTau2017v2p1) is not used. These files are the
re-measurement on `smrun2_tau_id_v2` (2026-10-19), whose MC has the MET fix of DY and W and the POG
single-muon trigger SF, with the embedding energy scale re-measured on the same production; they replace the
measurement on `smrun2_tau_id_v1` (md5 `fab61b22…`, `705642cc…`, `c546d891…`, `1258d92e…` for 2016preVFP,
2016postVFP, 2017, 2018; see the git history of this README). The two differ by at most 0.56&sigma; of the
`smrun2_tau_id_v1` fit interval (0.033 in &epsilon;) in every era, class and bin, with the same bins.

| | |
|---|---|
| Input | KingMaker productions (v7 spec P1; `sm_tau_id_measurement_config`, CROWN core bf01115): the MC from `smrun2_tau_id_v2` (P1b, bbtautau `feat-v7-run2` da1bc77: DY and W recoil-corrected in 2018 only, without recoil in 2016 and 2017; the POG `muon_Z` single-muon trigger SF), data (SingleMuon) and &mu;&tau; embedding from `smrun2_tau_id_v1` (bbtautau e44c2f2): mt; the monitoring columns `trg_mon_*_2`, `trgobj_pt_2`, `trgobj_l1pt_2` (C13, doc 12.4) |
| Measurement | ShapeSmith `tau_trigger` (`configs/smrun2_tau_id_v2_trigger.yaml`: `shapesmith skim`, `measure` per class and variant, `measure --merge`), 2026-10-19; core `feat/v7-run2` b6e35b4, analysis `feat/v7-run2` 213db98, sample database 49d2b7b; combine v10.0.2 in CMSSW_14_1_0_pre4; the embedding energy scale of `payloads/tau_embedding` (`smrun2_tau_id_v2`) |
| Tag and probe | tag: the single-muon trigger of the era with &mu; p<sub>T</sub> > 24 / 29 / 28 GeV (2016 / 2017 / 2018), iso < 0.15, \|&eta;<sub>&mu;</sub>\| < 2.1; probe: &tau;<sub>h</sub> p<sub>T</sub> &ge; 40 GeV, \|&eta;\| < 2.1, DM 0, 1, 10, 11, vsMu Tight, vsEle VVLoose, in its class; OS, m<sub>T</sub> < 65 GeV, lepton vetoes, HEM veto in 2018 |
| Pass | the &mu;&tau; monitoring path of the era fired with the probe matched (&Delta;R < 0.4) to its tau-leg filter bits, mirroring the tt paths leg by leg: 2016 MediumIso (data also MediumCombinedIso) with the matched object above 35 GeV; 2017 Tight35_TightID or (Medium35_TightID or Tight35) above 40 GeV with L1 &ge; 32 GeV; 2018 data before run 317509 the 2017 legs without the L1 cut, data from run 317509 on the HPS path (the di-tau trigger of the data) |
| Fit | per (DM, p<sub>T</sub>) bin and class a pass and a fail category in m<sub>vis</sub> (10 bins of equal data count in 30-160 GeV); signal: the embedded genuine taus with one shape in pass and fail and the rates &epsilon;&middot;r&middot;N / (1-&epsilon;)&middot;r&middot;N, their energy scale from `payloads/tau_embedding` (&plusmn;1&sigma; as shape) and a 10 % ttbar contamination shape; ZL/ZJ, TT, ST, VV and W from MC, QCD from same-sign data, lnN normalisations and a pass/fail anti-correlated &plusmn;10 % on the trigger efficiency of fakes; &epsilon; from a 1D profile scan (&Delta;NLL = 0.5 crossings) |
| Bins | from `measure --suggest-binning` on [40, 45, 50, 60, 80, 120, &infin;): merged from the top until the statistical error of &epsilon;<sub>data</sub>, counted with m<sub>T</sub> < 30 GeV and 40 < m<sub>vis</sub> < 90 GeV, is at most 0.03 (`TRIGGER_PT_EDGES`, suggested on `smrun2_tau_id_v1` and kept); the anti-isolated class reaches that in no bin and is one bin per decay mode |
| Uncertainty | up/down: the fit interval plus, in quadrature, the change of the variants (the MC genuine taus with their own pass and fail shapes as signal, weight 1; the tag muon 3 GeV harder, m<sub>T</sub> < 30 GeV, 2016 without the object-p<sub>T</sub> and 2017 without the L1 cut, weight 0.5 each) and a fit-counting difference beyond their combined error |
| Checks | `--merge`: no problem in any bin of the nominal runs; 0 < &epsilon; &le; 1 with down &le; nom &le; up in and beyond the p<sub>T</sub> range; every combination of both classes, every DM (also -1) and syst evaluates; every payload value equals the merged result |

## Content

One correction `tau_trigger` in the schema of the KIT/POG files, inputs `pt` (real, **flow clamp**: the
first and last bin continue beyond the edges), `dm` (-1 all, 0, 1, 10, 11; the consumer passes -1 for
other decay modes), `trigtype` (`ditau`), `wp` (`Medium`, `VVVLoose_not_Medium`), `corrtype`
(`eff_data`, read by CROWN; `eff_mc`, the own count on MC genuine taus, for validation) and `syst`
(`nom`, `up`, `down`). The provenance (commits, configuration hashes, the run of every class and variant)
is JSON in the description of the correction set. The p<sub>T</sub> edges differ per era, class and
decay mode. The values CROWN reads (eff_data):
2016preVFP:

| DM | p<sub>T</sub> bins [GeV]: Medium eff_data <sup>+up</sup><sub>-down</sub> | VVVLoose_not_Medium (p<sub>T</sub> > 40 GeV) |
|---|---|---|
| -1 | 40-45: 0.540 <sup>+0.010</sup><sub>-0.010</sub>; 45-50: 0.658 <sup>+0.019</sup><sub>-0.019</sub>; 50-60: 0.739 <sup>+0.036</sup><sub>-0.036</sub>; 60-80: 0.868 <sup>+0.038</sup><sub>-0.037</sub>; 80-120: 0.887 <sup>+0.053</sup><sub>-0.052</sub>; &ge; 120: 0.916 <sup>+0.021</sup><sub>-0.023</sub> | 0.503 <sup>+0.130</sup><sub>-0.129</sub> |
| 0 | 40-50: 0.586 <sup>+0.022</sup><sub>-0.021</sub>; 50-80: 0.729 <sup>+0.055</sup><sub>-0.055</sub>; &ge; 80: 0.873 <sup>+0.125</sup><sub>-0.126</sub> | 0.427 <sup>+0.128</sup><sub>-0.118</sub> |
| 1 | 40-45: 0.654 <sup>+0.012</sup><sub>-0.012</sub>; 45-50: 0.723 <sup>+0.021</sup><sub>-0.021</sub>; 50-60: 0.781 <sup>+0.036</sup><sub>-0.035</sub>; 60-80: 0.864 <sup>+0.043</sup><sub>-0.042</sub>; &ge; 80: 0.861 <sup>+0.071</sup><sub>-0.071</sub> | 0.582 <sup>+0.160</sup><sub>-0.156</sub> |
| 10 | 40-45: 0.337 <sup>+0.015</sup><sub>-0.015</sub>; 45-50: 0.553 <sup>+0.052</sup><sub>-0.051</sub>; 50-60: 0.702 <sup>+0.047</sup><sub>-0.045</sub>; &ge; 60: 0.928 <sup>+0.037</sup><sub>-0.032</sub> | 0.466 <sup>+0.200</sup><sub>-0.190</sub> |
| 11 | 40-60: 0.468 <sup>+0.037</sup><sub>-0.037</sub>; &ge; 60: 0.909 <sup>+0.045</sup><sub>-0.044</sub> | 0.453 <sup>+0.106</sup><sub>-0.098</sub> |

2016postVFP:

| DM | p<sub>T</sub> bins [GeV]: Medium eff_data <sup>+up</sup><sub>-down</sub> | VVVLoose_not_Medium (p<sub>T</sub> > 40 GeV) |
|---|---|---|
| -1 | 40-45: 0.528 <sup>+0.010</sup><sub>-0.010</sub>; 45-50: 0.637 <sup>+0.043</sup><sub>-0.042</sub>; 50-60: 0.760 <sup>+0.052</sup><sub>-0.051</sub>; 60-80: 0.882 <sup>+0.066</sup><sub>-0.066</sub>; 80-120: 0.945 <sup>+0.055</sup><sub>-0.099</sub>; &ge; 120: 0.926 <sup>+0.055</sup><sub>-0.056</sub> | 0.487 <sup>+0.097</sup><sub>-0.096</sub> |
| 0 | 40-50: 0.562 <sup>+0.024</sup><sub>-0.024</sub>; 50-80: 0.758 <sup>+0.088</sup><sub>-0.087</sub>; &ge; 80: 0.895 <sup>+0.105</sup><sub>-0.129</sub> | 0.549 <sup>+0.170</sup><sub>-0.129</sub> |
| 1 | 40-45: 0.638 <sup>+0.013</sup><sub>-0.013</sub>; 45-50: 0.689 <sup>+0.027</sup><sub>-0.026</sub>; 50-60: 0.801 <sup>+0.045</sup><sub>-0.044</sub>; 60-80: 0.899 <sup>+0.058</sup><sub>-0.058</sub>; &ge; 80: 0.944 <sup>+0.036</sup><sub>-0.037</sub> | 0.510 <sup>+0.085</sup><sub>-0.080</sub> |
| 10 | 40-45: 0.344 <sup>+0.018</sup><sub>-0.018</sub>; 45-50: 0.482 <sup>+0.041</sup><sub>-0.040</sub>; 50-60: 0.648 <sup>+0.039</sup><sub>-0.039</sub>; &ge; 60: 0.886 <sup>+0.092</sup><sub>-0.090</sub> | 0.432 <sup>+0.079</sup><sub>-0.073</sub> |
| 11 | 40-45: 0.393 <sup>+0.035</sup><sub>-0.035</sub>; 45-80: 0.659 <sup>+0.058</sup><sub>-0.057</sub>; &ge; 80: 0.957 <sup>+0.043</sup><sub>-0.049</sub> | 0.477 <sup>+0.181</sup><sub>-0.175</sub> |

2017:

| DM | p<sub>T</sub> bins [GeV]: Medium eff_data <sup>+up</sup><sub>-down</sub> | VVVLoose_not_Medium (p<sub>T</sub> > 40 GeV) |
|---|---|---|
| -1 | 40-45: 0.440 <sup>+0.023</sup><sub>-0.023</sub>; 45-50: 0.564 <sup>+0.025</sup><sub>-0.025</sub>; 50-60: 0.661 <sup>+0.070</sup><sub>-0.069</sub>; 60-80: 0.787 <sup>+0.068</sup><sub>-0.068</sub>; 80-120: 0.856 <sup>+0.072</sup><sub>-0.071</sub>; &ge; 120: 0.837 <sup>+0.027</sup><sub>-0.028</sub> | 0.402 <sup>+0.107</sup><sub>-0.106</sub> |
| 0 | 40-45: 0.479 <sup>+0.059</sup><sub>-0.060</sub>; &ge; 45: 0.706 <sup>+0.100</sup><sub>-0.099</sub> | 0.248 <sup>+0.095</sup><sub>-0.099</sub> |
| 1 | 40-45: 0.526 <sup>+0.015</sup><sub>-0.015</sub>; 45-50: 0.615 <sup>+0.023</sup><sub>-0.023</sub>; 50-60: 0.681 <sup>+0.082</sup><sub>-0.082</sub>; 60-80: 0.818 <sup>+0.058</sup><sub>-0.056</sub>; &ge; 80: 0.833 <sup>+0.044</sup><sub>-0.044</sub> | 0.425 <sup>+0.213</sup><sub>-0.211</sub> |
| 10 | 40-45: 0.294 <sup>+0.020</sup><sub>-0.020</sub>; 45-50: 0.457 <sup>+0.040</sup><sub>-0.039</sub>; 50-80: 0.638 <sup>+0.062</sup><sub>-0.062</sub>; &ge; 80: 0.880 <sup>+0.047</sup><sub>-0.048</sub> | 0.477 <sup>+0.133</sup><sub>-0.112</sub> |
| 11 | 40-50: 0.347 <sup>+0.051</sup><sub>-0.051</sub>; &ge; 50: 0.753 <sup>+0.091</sup><sub>-0.087</sub> | 0.375 <sup>+0.076</sup><sub>-0.071</sub> |

2018:

| DM | p<sub>T</sub> bins [GeV]: Medium eff_data <sup>+up</sup><sub>-down</sub> | VVVLoose_not_Medium (p<sub>T</sub> > 40 GeV) |
|---|---|---|
| -1 | 40-45: 0.437 <sup>+0.018</sup><sub>-0.018</sub>; 45-50: 0.573 <sup>+0.031</sup><sub>-0.030</sub>; 50-60: 0.697 <sup>+0.060</sup><sub>-0.060</sub>; 60-80: 0.783 <sup>+0.075</sup><sub>-0.075</sub>; 80-120: 0.862 <sup>+0.031</sup><sub>-0.031</sub>; &ge; 120: 0.850 <sup>+0.015</sup><sub>-0.016</sub> | 0.337 <sup>+0.048</sup><sub>-0.047</sub> |
| 0 | 40-45: 0.497 <sup>+0.028</sup><sub>-0.028</sub>; 45-80: 0.692 <sup>+0.107</sup><sub>-0.107</sub>; &ge; 80: 0.852 <sup>+0.085</sup><sub>-0.085</sub> | 0.350 <sup>+0.159</sup><sub>-0.151</sub> |
| 1 | 40-45: 0.514 <sup>+0.015</sup><sub>-0.015</sub>; 45-50: 0.661 <sup>+0.067</sup><sub>-0.066</sub>; 50-60: 0.771 <sup>+0.090</sup><sub>-0.089</sub>; 60-80: 0.801 <sup>+0.044</sup><sub>-0.042</sub>; 80-120: 0.877 <sup>+0.090</sup><sub>-0.090</sub>; &ge; 120: 0.827 <sup>+0.065</sup><sub>-0.066</sub> | 0.413 <sup>+0.177</sup><sub>-0.175</sub> |
| 10 | 40-45: 0.292 <sup>+0.017</sup><sub>-0.017</sub>; 45-50: 0.454 <sup>+0.034</sup><sub>-0.035</sub>; 50-80: 0.617 <sup>+0.064</sup><sub>-0.065</sub>; 80-120: 0.885 <sup>+0.048</sup><sub>-0.045</sub>; &ge; 120: 0.955 <sup>+0.045</sup><sub>-0.050</sub> | 0.311 <sup>+0.088</sup><sub>-0.088</sub> |
| 11 | 40-50: 0.320 <sup>+0.037</sup><sub>-0.037</sub>; &ge; 50: 0.666 <sup>+0.061</sup><sub>-0.063</sub> | 0.269 <sup>+0.126</sup><sub>-0.131</sub> |


Known limitations: the method closure on MC with
the common signal shape deviates by up to 3.7&sigma; of the fit at p<sub>T</sub> > 50 GeV (with separate
pass and fail shapes it closes within 0.52&sigma;); the bias stays inside the payload uncertainty in 75 of
the 79 Medium bins with a closure interval (at most 1.16 times it). The anti-isolated class is flat in
p<sub>T</sub> above 40 GeV. 2018 data before run 317509 have a lower efficiency near threshold than later data
(DM-inclusive 40-45 GeV: 0.401 against 0.455); the payload is their luminosity-weighted mean, as in the data.

## Files

| File | md5 | sha256 |
|---|---|---|
| `Run2-2016preVFP-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding2016preVFPUL.json.gz` | `79310ecbb3135350bb3e13fb2280b491` | `12a951ffd4787154975e101f153db1697f87abedb95964b55ef5438a3c41982b` |
| `Run2-2016postVFP-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding2016postVFPUL.json.gz` | `393991ecb6c709a60e99ec237c0a171a` | `857d3d4f89e0b9839a02077dd248ae264b5c0f9fc16bc851c8ed6c3af19244f5` |
| `Run2-2017-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding2017UL.json.gz` | `7b45d2a8835d3c39e51a4b951aaf439c` | `1180a3e532b1b809a9b847003af4680ea1fb86228f07763e4c4268dbf6640fce` |
| `Run2-2018-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding2018UL.json.gz` | `2317012694bfcd892539a4e13ea090f3` | `13f0ae02389aeb8aae5dc43a50e689dfe40754e82f2bb1cc713a78061f493c05` |

KingMaker's framework-tarball hash does not cover `payloads/`: set `force_repack_tarball` after
replacing these files, and produce under a new tag.
