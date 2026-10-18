# Tau trigger payloads of the tt embedding

`Run2-<era>-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding<era>UL.json.gz` (era 2016preVFP,
2016postVFP, 2017, 2018) holds the efficiency in data of the tau leg of the di-tau trigger of one Run-2 era
(NanoAOD v15), DeepTau2018v2p5, in two isolation classes of the tau. The tt embedding has no trigger
requirement and is weighted with this efficiency per tau (v7 spec E33, variant A; docs v7_tt_emb_trigger
12.6): `embedding_run2_v15.py` reads the file of its era through `tt_embedding_trigger_eff_file`
(`TT_EMBEDDING_TRIGGER_EFFICIENCIES[era]`) into `trg_effdata_emb_Medium_<leg>` (wp `Medium`) and
`trg_effdata_emb_AntiMedium_<leg>` (wp `VVVLoose_not_Medium`). They replace the POG v15 eff_data
(Medium, and VVVLoose for the anti-isolated class) used until this measurement; the KIT file
`data/embedding/tau_trigger<era>_UL.json.gz` (DeepTau2017v2p1) is not used.

| | |
|---|---|
| Input | KingMaker production `smrun2_tau_id_v1` (v7 spec P1; `sm_tau_id_measurement_config`, bbtautau `feat-v7-run2` e44c2f2 with CROWN core bf01115): mt, data (SingleMuon), MC, &mu;&tau; embedding; the monitoring columns `trg_mon_*_2`, `trgobj_pt_2`, `trgobj_l1pt_2` (C13, doc 12.4) |
| Measurement | ShapeSmith `tau_trigger` (`configs/smrun2_tau_id_v1_trigger.yaml`: `shapesmith skim`, `measure` per class and variant, `measure --refit`, `measure --merge`), 2026-10-18; core `feat/v7-run2` ade2155, analysis `feat/v7-run2` 7e75284, sample database 49d2b7b; combine v10.0.2 in CMSSW_14_1_0_pre4 |
| Tag and probe | tag: the single-muon trigger of the era with &mu; p<sub>T</sub> > 24 / 29 / 28 GeV (2016 / 2017 / 2018), iso < 0.15, \|&eta;<sub>&mu;</sub>\| < 2.1; probe: &tau;<sub>h</sub> p<sub>T</sub> &ge; 40 GeV, \|&eta;\| < 2.1, DM 0, 1, 10, 11, vsMu Tight, vsEle VVLoose, in its class; OS, m<sub>T</sub> < 65 GeV, lepton vetoes, HEM veto in 2018 |
| Pass | the &mu;&tau; monitoring path of the era fired with the probe matched (&Delta;R < 0.4) to its tau-leg filter bits, mirroring the tt paths leg by leg: 2016 MediumIso (data also MediumCombinedIso) with the matched object above 35 GeV; 2017 Tight35_TightID or (Medium35_TightID or Tight35) above 40 GeV with L1 &ge; 32 GeV; 2018 data before run 317509 the 2017 legs without the L1 cut, data from run 317509 on the HPS path (the di-tau trigger of the data) |
| Fit | per (DM, p<sub>T</sub>) bin and class a pass and a fail category in m<sub>vis</sub> (10 bins of equal data count in 30-160 GeV); signal: the embedded genuine taus with one shape in pass and fail and the rates &epsilon;&middot;r&middot;N / (1-&epsilon;)&middot;r&middot;N, their energy scale from `payloads/tau_embedding` (&plusmn;1&sigma; as shape) and a 10 % ttbar contamination shape; ZL/ZJ, TT, ST, VV and W from MC, QCD from same-sign data, lnN normalisations and a pass/fail anti-correlated &plusmn;10 % on the trigger efficiency of fakes; &epsilon; from a 1D profile scan (&Delta;NLL = 0.5 crossings) |
| Bins | from `measure --suggest-binning` on [40, 45, 50, 60, 80, 120, &infin;): merged from the top until the statistical error of &epsilon;<sub>data</sub>, counted with m<sub>T</sub> < 30 GeV and 40 < m<sub>vis</sub> < 90 GeV, is at most 0.03 (`TRIGGER_PT_EDGES`); the anti-isolated class reaches that in no bin and is one bin per decay mode |
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
| -1 | 40-45: 0.540 <sup>+0.010</sup><sub>-0.010</sub>; 45-50: 0.658 <sup>+0.019</sup><sub>-0.019</sub>; 50-60: 0.740 <sup>+0.037</sup><sub>-0.037</sub>; 60-80: 0.869 <sup>+0.038</sup><sub>-0.037</sub>; 80-120: 0.887 <sup>+0.053</sup><sub>-0.053</sub>; &ge; 120: 0.916 <sup>+0.023</sup><sub>-0.026</sub> | 0.495 <sup>+0.113</sup><sub>-0.112</sub> |
| 0 | 40-50: 0.585 <sup>+0.021</sup><sub>-0.021</sub>; 50-80: 0.733 <sup>+0.058</sup><sub>-0.058</sub>; &ge; 80: 0.872 <sup>+0.128</sup><sub>-0.130</sub> | 0.417 <sup>+0.121</sup><sub>-0.113</sub> |
| 1 | 40-45: 0.654 <sup>+0.012</sup><sub>-0.012</sub>; 45-50: 0.721 <sup>+0.021</sup><sub>-0.021</sub>; 50-60: 0.779 <sup>+0.035</sup><sub>-0.035</sub>; 60-80: 0.863 <sup>+0.042</sup><sub>-0.042</sub>; &ge; 80: 0.862 <sup>+0.070</sup><sub>-0.070</sub> | 0.575 <sup>+0.148</sup><sub>-0.145</sub> |
| 10 | 40-45: 0.337 <sup>+0.015</sup><sub>-0.015</sub>; 45-50: 0.554 <sup>+0.052</sup><sub>-0.052</sub>; 50-60: 0.701 <sup>+0.047</sup><sub>-0.045</sub>; &ge; 60: 0.928 <sup>+0.036</sup><sub>-0.032</sub> | 0.453 <sup>+0.169</sup><sub>-0.161</sub> |
| 11 | 40-60: 0.469 <sup>+0.038</sup><sub>-0.038</sub>; &ge; 60: 0.909 <sup>+0.044</sup><sub>-0.043</sub> | 0.447 <sup>+0.096</sup><sub>-0.089</sub> |

2016postVFP:

| DM | p<sub>T</sub> bins [GeV]: Medium eff_data <sup>+up</sup><sub>-down</sub> | VVVLoose_not_Medium (p<sub>T</sub> > 40 GeV) |
|---|---|---|
| -1 | 40-45: 0.527 <sup>+0.010</sup><sub>-0.010</sub>; 45-50: 0.636 <sup>+0.040</sup><sub>-0.040</sub>; 50-60: 0.759 <sup>+0.054</sup><sub>-0.054</sub>; 60-80: 0.880 <sup>+0.068</sup><sub>-0.067</sub>; 80-120: 0.943 <sup>+0.057</sup><sub>-0.102</sub>; &ge; 120: 0.925 <sup>+0.056</sup><sub>-0.057</sub> | 0.485 <sup>+0.092</sup><sub>-0.091</sub> |
| 0 | 40-50: 0.562 <sup>+0.024</sup><sub>-0.024</sub>; 50-80: 0.756 <sup>+0.090</sup><sub>-0.089</sub>; &ge; 80: 0.894 <sup>+0.106</sup><sub>-0.137</sub> | 0.529 <sup>+0.150</sup><sub>-0.118</sub> |
| 1 | 40-45: 0.638 <sup>+0.013</sup><sub>-0.013</sub>; 45-50: 0.690 <sup>+0.027</sup><sub>-0.027</sub>; 50-60: 0.800 <sup>+0.050</sup><sub>-0.049</sub>; 60-80: 0.901 <sup>+0.062</sup><sub>-0.061</sub>; &ge; 80: 0.939 <sup>+0.037</sup><sub>-0.037</sub> | 0.513 <sup>+0.080</sup><sub>-0.075</sub> |
| 10 | 40-45: 0.342 <sup>+0.018</sup><sub>-0.018</sub>; 45-50: 0.482 <sup>+0.040</sup><sub>-0.040</sub>; 50-60: 0.649 <sup>+0.038</sup><sub>-0.038</sub>; &ge; 60: 0.884 <sup>+0.093</sup><sub>-0.092</sub> | 0.438 <sup>+0.073</sup><sub>-0.068</sub> |
| 11 | 40-45: 0.391 <sup>+0.033</sup><sub>-0.034</sub>; 45-80: 0.660 <sup>+0.057</sup><sub>-0.056</sub>; &ge; 80: 0.957 <sup>+0.043</sup><sub>-0.051</sub> | 0.470 <sup>+0.169</sup><sub>-0.164</sub> |

2017:

| DM | p<sub>T</sub> bins [GeV]: Medium eff_data <sup>+up</sup><sub>-down</sub> | VVVLoose_not_Medium (p<sub>T</sub> > 40 GeV) |
|---|---|---|
| -1 | 40-45: 0.442 <sup>+0.024</sup><sub>-0.024</sub>; 45-50: 0.562 <sup>+0.024</sup><sub>-0.024</sub>; 50-60: 0.662 <sup>+0.070</sup><sub>-0.070</sub>; 60-80: 0.788 <sup>+0.066</sup><sub>-0.065</sub>; 80-120: 0.853 <sup>+0.069</sup><sub>-0.068</sub>; &ge; 120: 0.837 <sup>+0.028</sup><sub>-0.029</sub> | 0.402 <sup>+0.105</sup><sub>-0.104</sub> |
| 0 | 40-45: 0.483 <sup>+0.064</sup><sub>-0.064</sub>; &ge; 45: 0.706 <sup>+0.099</sup><sub>-0.099</sub> | 0.251 <sup>+0.097</sup><sub>-0.100</sub> |
| 1 | 40-45: 0.527 <sup>+0.016</sup><sub>-0.016</sub>; 45-50: 0.612 <sup>+0.023</sup><sub>-0.023</sub>; 50-60: 0.683 <sup>+0.080</sup><sub>-0.079</sub>; 60-80: 0.819 <sup>+0.058</sup><sub>-0.056</sub>; &ge; 80: 0.830 <sup>+0.045</sup><sub>-0.045</sub> | 0.425 <sup>+0.200</sup><sub>-0.197</sub> |
| 10 | 40-45: 0.293 <sup>+0.020</sup><sub>-0.020</sub>; 45-50: 0.456 <sup>+0.040</sup><sub>-0.039</sub>; 50-80: 0.638 <sup>+0.066</sup><sub>-0.065</sub>; &ge; 80: 0.880 <sup>+0.059</sup><sub>-0.059</sub> | 0.467 <sup>+0.123</sup><sub>-0.105</sub> |
| 11 | 40-50: 0.352 <sup>+0.048</sup><sub>-0.049</sub>; &ge; 50: 0.746 <sup>+0.088</sup><sub>-0.085</sub> | 0.378 <sup>+0.070</sup><sub>-0.065</sub> |

2018:

| DM | p<sub>T</sub> bins [GeV]: Medium eff_data <sup>+up</sup><sub>-down</sub> | VVVLoose_not_Medium (p<sub>T</sub> > 40 GeV) |
|---|---|---|
| -1 | 40-45: 0.436 <sup>+0.018</sup><sub>-0.018</sub>; 45-50: 0.574 <sup>+0.031</sup><sub>-0.030</sub>; 50-60: 0.697 <sup>+0.060</sup><sub>-0.060</sub>; 60-80: 0.791 <sup>+0.069</sup><sub>-0.069</sub>; 80-120: 0.862 <sup>+0.033</sup><sub>-0.033</sub>; &ge; 120: 0.853 <sup>+0.017</sup><sub>-0.017</sub> | 0.353 <sup>+0.049</sup><sub>-0.048</sub> |
| 0 | 40-45: 0.498 <sup>+0.027</sup><sub>-0.027</sub>; 45-80: 0.697 <sup>+0.107</sup><sub>-0.106</sub>; &ge; 80: 0.852 <sup>+0.094</sup><sub>-0.094</sub> | 0.340 <sup>+0.158</sup><sub>-0.152</sub> |
| 1 | 40-45: 0.511 <sup>+0.016</sup><sub>-0.016</sub>; 45-50: 0.662 <sup>+0.069</sup><sub>-0.068</sub>; 50-60: 0.772 <sup>+0.088</sup><sub>-0.087</sub>; 60-80: 0.814 <sup>+0.041</sup><sub>-0.039</sub>; 80-120: 0.875 <sup>+0.118</sup><sub>-0.118</sub>; &ge; 120: 0.827 <sup>+0.072</sup><sub>-0.072</sub> | 0.424 <sup>+0.179</sup><sub>-0.177</sub> |
| 10 | 40-45: 0.292 <sup>+0.017</sup><sub>-0.017</sub>; 45-50: 0.449 <sup>+0.033</sup><sub>-0.034</sub>; 50-80: 0.615 <sup>+0.077</sup><sub>-0.078</sub>; 80-120: 0.885 <sup>+0.048</sup><sub>-0.044</sub>; &ge; 120: 0.956 <sup>+0.044</sup><sub>-0.055</sub> | 0.333 <sup>+0.085</sup><sub>-0.084</sub> |
| 11 | 40-50: 0.319 <sup>+0.037</sup><sub>-0.037</sub>; &ge; 50: 0.670 <sup>+0.061</sup><sub>-0.062</sub> | 0.302 <sup>+0.144</sup><sub>-0.146</sub> |


Known limitations: the method closure on MC with
the common signal shape deviates by up to 3.6&sigma; of the fit at p<sub>T</sub> > 50 GeV (with separate
pass and fail shapes it closes within 0.5&sigma;); the bias stays inside the payload uncertainty in all
but 6 Medium bins (at most 1.18 times it). The anti-isolated class is flat in p<sub>T</sub> above 40 GeV.
2018 data before run 317509 have a lower efficiency near threshold than later data (DM-inclusive
40-45 GeV: 0.399 against 0.453); the payload is their luminosity-weighted mean, as in the data.

## Files

| File | md5 | sha256 |
|---|---|---|
| `Run2-2016preVFP-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding2016preVFPUL.json.gz` | `fab61b22bb192d12342738905a488915` | `ced8649c4517210436bab853a48661559f7d7c4e086e2936e6b982028d58832e` |
| `Run2-2016postVFP-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding2016postVFPUL.json.gz` | `705642cc3ba003475c2282c1e2bc8994` | `c8d8e273cdc2d55da93cef4170611036fc2fd8430ac1aa6136bae25df2e4cc53` |
| `Run2-2017-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding2017UL.json.gz` | `c546d891d761e42c5112b19c0207163d` | `87fe53dfa013540afcc6b051a3807cf5db79d02af87e5e16a3e1f3c7f332ff25` |
| `Run2-2018-UL-NanoAODv15/ditau_trigger_DeepTau2018v2p5_embedding2018UL.json.gz` | `1258d92e2936a659e99531daf2acb0b9` | `01113ff9e7c43e30d25bc5e518acb33b99d0e75bfefa3c96b53a1ae8b6c76d53` |

KingMaker's framework-tarball hash does not cover `payloads/`: set `force_repack_tarball` after
replacing these files, and produce under a new tag.
