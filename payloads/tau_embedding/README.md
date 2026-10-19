# Tau embedding payloads

`Run2-<era>-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding<era>UL.json.gz` (era 2016preVFP,
2016postVFP, 2017, 2018) holds the DeepTau2018v2p5 corrections of genuine hadronic taus in the
&mu;&tau;-embedded events of one Run-2 era (NanoAOD v15): the vsJet scale factor and the tau energy
scale, measured per era and per 2016 half (v7 spec E16, 5.4). The TAU POG provides no embedding file
for NanoAOD v15, and the CROWN `data/embedding/tau_id_es_embedding<era>UL.json.gz` are for
DeepTau2017v2p1. `embedding_run2_v15.py` reads the file of its era through `tau_vsjet_es_sf_file`
(`TAU_EMBEDDING_ID_ES_PAYLOADS[era]`) for the tau energy scale (`taus.TauPtCorrectionMC`) and the
vsJet SF (`scalefactors.TauIDVsJetSF1/2`). These files are the re-measurement on `smrun2_tau_id_v2`
(2026-10-19), whose MC has the MET fix of DY and W and the POG single-muon trigger SF; they replace the
measurement on `smrun2_tau_id_v1` (md5 `41a980dd…`, `e9acd4a6…`, `b34248dd…`, `c5d1b879…` for
2016preVFP, 2016postVFP, 2017, 2018), which had replaced jvoss's preliminary 2018 file (md5
`7c684587c67674402dac1e3a871f4a3d`, copied from `dev_2018_bbtautau` 1cc7bd2; see the git history of this
README). The two measurements differ by at most 0.61&sigma; (of the `smrun2_tau_id_v1` interval) in every era,
working point and category.

| | |
|---|---|
| Input | KingMaker productions (v7 spec P1; `sm_tau_id_measurement_config`, sample lists `sm_<era>_tau_id_measurement.txt`, CROWN core bf01115): the MC from `smrun2_tau_id_v2` (P1b, bbtautau `feat-v7-run2` da1bc77: DY and W recoil-corrected in 2018 only, on the NanoAOD PuppiMET with the leptons and then the JES delta, without recoil in 2016 and 2017; the POG `muon_Z` single-muon trigger SF), data and embedding from `smrun2_tau_id_v1` (bbtautau e44c2f2): mt and mm, MC with all shifts, &mu;&tau; and &mu;&mu; embedding nominal and without tau corrections |
| Measurement | ShapeSmith `tau_id_es` (`configs/smrun2_tau_id_v2_id_es.yaml`, `shapesmith skim`, `measure` per working-point combination, `measure --merge`), 2026-10-19; core `feat/v7-run2` b6e35b4, analysis `feat/v7-run2` 213db98, sample database 49d2b7b |
| Selection | tag and probe Z&rarr;&tau;&tau;&rarr;&mu;&tau;<sub>h</sub>: the single-muon trigger of the era (2016 IsoMu22 family from 24 GeV, 2017 IsoMu27 from 29 GeV, 2018 IsoMu24 or IsoMu27 from 25 GeV) with the POG `muon_Z` SF on MC and the KIT SF on the embedding, \|&eta;<sub>&mu;</sub>\| < 2.1, iso < 0.15, m<sub>T</sub> < 65 GeV, OS, lepton vetoes; tau p<sub>T</sub> > 20 GeV, \|&eta;\| < 2.5, vsMu Tight, decay modes 0, 1, 10, 11; HEM veto in 2018; prefiring weight on all MC |
| Model | mt: embedded genuine taus (signal), ZL/ZJ, TTL/TTJ, STL/STJ, VVL/VVJ and W from MC (W in 0J/1J/2J amcatnlo, E17), QCD from same-sign data, 10 % ttbar contamination of the embedding (TTT); mm (Z&rarr;&mu;&mu;, 70-110 GeV, &mu;&mu; embedding) fixes the embedding normalisation through the common `r_DY_incl_<category>`, so the SF is the data/embedding ratio of the tau ID; MC shape uncertainties of the P1 shifts (E34 exception), the recoil shifts of DY and W in 2018 only |
| Fit | per working-point combination (vsJet Medium, Tight &times; vsEle VVLoose, Tight) and category (DM0, DM1, DM10+11, each inclusive, 20-40 and 40-200 GeV): m<sub>vis</sub> in 10 bins of equal data count in 30-160 GeV; MorphingTauID2017 (TauIDSFMeasurement `tauID_ES` 84095dd + `patches/TauIDSFMeasurement-tauID_ES.patch` of BBTauTauAnalysis-ShapeSmith, CMSSW_14_1_0_pre4, combine v10.0.2) with ES morphed between 200 templates of &plusmn;20 % in 0.2 % steps |
| Intervals | U11: best value and 1&sigma; interval of each POI from its profile (ES: 1D scan with r profiled; r: envelope of a 2D grid with both POIs fixed), &Delta;NLL = 0.5 crossings interpolated, rescans on a widened range for an open side and on a narrower range for an interval with fewer than five scan points; `singles` as cross-check |
| Checks | `--merge`: no problem in any category and no interval at its fit range; the payload values equal the fitted intervals; the corrected p<sub>T</sub> p<sub>T</sub>&middot;ES(p<sub>T</sub>) of the p<sub>T</sub>-binned energy scale increases continuously over 20-200 GeV for every working point, decay mode and syst (no 36-42 GeV hole) |

## Content

Three corrections, as in the predecessor's `create_xpog_json_v15.py`, each returning 1.0 for every
`genmatch` other than 5, with the provenance (commits, configuration hashes, the run of every
working-point combination) as JSON in the description of the correction set:

| Correction | Inputs | Used |
|---|---|---|
| `DeepTau2018v2p5VSjet` | pt, dm, genmatch, wp, wp_VSe, syst, flag | yes, `flag = "dm"` (the decay-mode-inclusive fit, flat in p<sub>T</sub> from 20 GeV) in et, mt and tt; `"pt"` has the bins 20-40 and 40-200 GeV (clamped) |
| `tau_energy_scale` | pt, eta, dm, genmatch, id, wp, wp_VSe, syst | no; the 20-40 and 40-200 GeV fits, changing linearly across 36-42 GeV |
| `tau_energy_scale_dm_binned` | same | yes (`tau_ES_json_name`), flat in p<sub>T</sub> |

Axes: `wp` Medium, Tight; `wp_VSe` VVLoose, Tight; `syst` nom, up, down (the ends of the 1&sigma;
interval); \|&eta;\| < 2.5. DM11 equals DM10, because the measurement fits one 3-prong category
(DM1011); the embedding shifts vary DM10 and DM11 separately (one decay mode per shift, see
`variations/taus.py`), so the two are to be correlated downstream. The values the analysis reads
(Medium, decay-mode binned):

| Era | vsJet / vsEle (scopes) | DM | vsJet SF | ES [%] |
|---|---|---|---|---|
| 2016preVFP | Medium / VVLoose (mt, tt) | 0 | 1.035 <sup>+0.031</sup><sub>-0.040</sub> | -1.29 <sup>+0.81</sup><sub>-0.94</sub> |
| 2016preVFP | Medium / VVLoose (mt, tt) | 1 | 1.204 <sup>+0.029</sup><sub>-0.035</sub> | -0.60 <sup>+0.35</sup><sub>-0.45</sub> |
| 2016preVFP | Medium / VVLoose (mt, tt) | 10, 11 | 0.977 <sup>+0.028</sup><sub>-0.044</sub> | -0.56 <sup>+0.77</sup><sub>-0.46</sub> |
| 2016preVFP | Medium / Tight (et) | 0 | 0.895 <sup>+0.025</sup><sub>-0.026</sub> | -1.70 <sup>+0.94</sup><sub>-0.75</sub> |
| 2016preVFP | Medium / Tight (et) | 1 | 1.081 <sup>+0.031</sup><sub>-0.042</sub> | -0.21 <sup>+0.40</sup><sub>-0.44</sub> |
| 2016preVFP | Medium / Tight (et) | 10, 11 | 0.970 <sup>+0.030</sup><sub>-0.041</sub> | -0.30 <sup>+0.52</sup><sub>-0.78</sub> |
| 2016postVFP | Medium / VVLoose (mt, tt) | 0 | 1.031 <sup>+0.028</sup><sub>-0.032</sub> | -1.67 <sup>+0.78</sup><sub>-0.70</sub> |
| 2016postVFP | Medium / VVLoose (mt, tt) | 1 | 1.174 <sup>+0.031</sup><sub>-0.028</sub> | -1.62 <sup>+0.36</sup><sub>-0.62</sub> |
| 2016postVFP | Medium / VVLoose (mt, tt) | 10, 11 | 1.019 <sup>+0.033</sup><sub>-0.038</sub> | -0.69 <sup>+0.70</sup><sub>-0.46</sub> |
| 2016postVFP | Medium / Tight (et) | 0 | 0.925 <sup>+0.023</sup><sub>-0.036</sub> | -2.99 <sup>+0.92</sup><sub>-0.83</sub> |
| 2016postVFP | Medium / Tight (et) | 1 | 1.077 <sup>+0.024</sup><sub>-0.037</sub> | -1.25 <sup>+0.57</sup><sub>-0.52</sub> |
| 2016postVFP | Medium / Tight (et) | 10, 11 | 1.015 <sup>+0.033</sup><sub>-0.038</sub> | -0.67 <sup>+0.45</sup><sub>-0.49</sub> |
| 2017 | Medium / VVLoose (mt, tt) | 0 | 0.994 <sup>+0.024</sup><sub>-0.033</sub> | -0.71 <sup>+0.75</sup><sub>-0.93</sub> |
| 2017 | Medium / VVLoose (mt, tt) | 1 | 1.196 <sup>+0.032</sup><sub>-0.035</sub> | -2.60 <sup>+0.40</sup><sub>-0.45</sub> |
| 2017 | Medium / VVLoose (mt, tt) | 10, 11 | 1.045 <sup>+0.027</sup><sub>-0.048</sub> | -0.67 <sup>+0.64</sup><sub>-0.50</sub> |
| 2017 | Medium / Tight (et) | 0 | 0.864 <sup>+0.018</sup><sub>-0.030</sub> | -0.52 <sup>+0.87</sup><sub>-1.05</sub> |
| 2017 | Medium / Tight (et) | 1 | 1.078 <sup>+0.029</sup><sub>-0.044</sub> | -1.99 <sup>+0.40</sup><sub>-0.49</sub> |
| 2017 | Medium / Tight (et) | 10, 11 | 1.043 <sup>+0.024</sup><sub>-0.042</sub> | -0.55 <sup>+0.58</sup><sub>-0.49</sub> |
| 2018 | Medium / VVLoose (mt, tt) | 0 | 0.939 <sup>+0.024</sup><sub>-0.025</sub> | -1.25 <sup>+0.57</sup><sub>-0.61</sub> |
| 2018 | Medium / VVLoose (mt, tt) | 1 | 1.088 <sup>+0.024</sup><sub>-0.023</sub> | -1.29 <sup>+0.29</sup><sub>-0.33</sub> |
| 2018 | Medium / VVLoose (mt, tt) | 10, 11 | 0.967 <sup>+0.027</sup><sub>-0.024</sub> | 0.22 <sup>+0.44</sup><sub>-0.43</sub> |
| 2018 | Medium / Tight (et) | 0 | 0.805 <sup>+0.022</sup><sub>-0.015</sub> | -1.61 <sup>+0.76</sup><sub>-0.65</sub> |
| 2018 | Medium / Tight (et) | 1 | 0.997 <sup>+0.022</sup><sub>-0.022</sub> | -1.14 <sup>+0.40</sup><sub>-0.38</sub> |
| 2018 | Medium / Tight (et) | 10, 11 | 0.963 <sup>+0.025</sup><sub>-0.032</sub> | 0.21 <sup>+0.45</sup><sub>-0.43</sub> |

The interval of the scale factor includes the uncertainty of the embedding normalisation from the mm
region and the MC shape uncertainties; the energy scale is in percent of the tau four-momentum.

## Files

| File | md5 | sha256 |
|---|---|---|
| `Run2-2016preVFP-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2016preVFPUL.json.gz` | `3433ff611585d6c75eb3f868260b8c3a` | `8e76c9569d6350096b95134c7a65d188d273a0f3cd41c3775eea7eaf1711995d` |
| `Run2-2016postVFP-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2016postVFPUL.json.gz` | `7c60c26e15247730cf7153541340d98e` | `1dbf0d573ac34cfa0e0d35b8efe9b424484a553ee46112bb2c787d8950f7d45c` |
| `Run2-2017-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2017UL.json.gz` | `214089dd0f3854bcd11092106a71223f` | `90e39184123c17acc232791eb45a36c98a12db9e3b759ba1050e808fd02a9f29` |
| `Run2-2018-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2018UL.json.gz` | `42156154af825162a35d074f6952ee64` | `614b47946f5a68188a1af017e9cec872b95de24e9d14a89d91d59f60b2f13777` |

KingMaker's framework-tarball hash does not cover `payloads/`: set `force_repack_tarball` after
replacing these files, and produce under a new tag.
