# Tau embedding payloads

`Run2-<era>-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding<era>UL.json.gz` (era 2016preVFP,
2016postVFP, 2017, 2018) holds the DeepTau2018v2p5 corrections of genuine hadronic taus in the
&mu;&tau;-embedded events of one Run-2 era (NanoAOD v15): the vsJet scale factor and the tau energy
scale, measured per era and per 2016 half (v7 spec E16, 5.4). The TAU POG provides no embedding file
for NanoAOD v15, and the CROWN `data/embedding/tau_id_es_embedding<era>UL.json.gz` are for
DeepTau2017v2p1. `embedding_run2_v15.py` reads the file of its era through `tau_vsjet_es_sf_file`
(`TAU_EMBEDDING_ID_ES_PAYLOADS[era]`) for the tau energy scale (`taus.TauPtCorrectionMC`) and the
vsJet SF (`scalefactors.TauIDVsJetSF1/2`). The 2018 file replaces jvoss's preliminary measurement
(md5 `7c684587c67674402dac1e3a871f4a3d`, copied from `dev_2018_bbtautau` 1cc7bd2; see the git
history of this README).

| | |
|---|---|
| Input | KingMaker production `smrun2_tau_id_v1` (v7 spec P1; `sm_tau_id_measurement_config`, bbtautau `feat-v7-run2` e44c2f2 with CROWN core bf01115, sample lists `sm_<era>_tau_id_measurement.txt`): mt and mm, MC with all shifts, &mu;&tau; and &mu;&mu; embedding nominal and without tau corrections |
| Measurement | ShapeSmith `tau_id_es` (`configs/smrun2_tau_id_v1_id_es.yaml`, `shapesmith skim`, `measure` per working-point combination, `measure --merge`), 2026-10-18; core `fix/tau-id-profile-resolution` 7052214 (on `feat/v7-run2` 0614e7d), analysis `feat/v7-run2` abd7657 (histograms with 901b75f; the two differ only in the DY tables of the SM runs), sample database 49d2b7b |
| Selection | tag and probe Z&rarr;&tau;&tau;&rarr;&mu;&tau;<sub>h</sub>: the single-muon trigger of the era (2016 IsoMu22 family from 24 GeV, 2017 IsoMu27 from 29 GeV, 2018 IsoMu24 or IsoMu27 from 25 GeV) with its KIT SF, \|&eta;<sub>&mu;</sub>\| < 2.1, iso < 0.15, m<sub>T</sub> < 65 GeV, OS, lepton vetoes; tau p<sub>T</sub> > 20 GeV, \|&eta;\| < 2.5, vsMu Tight, decay modes 0, 1, 10, 11; HEM veto in 2018; prefiring weight on all MC |
| Model | mt: embedded genuine taus (signal), ZL/ZJ, TTL/TTJ, STL/STJ, VVL/VVJ and W from MC (W in 0J/1J/2J amcatnlo, E17), QCD from same-sign data, 10 % ttbar contamination of the embedding (TTT); mm (Z&rarr;&mu;&mu;, 70-110 GeV, &mu;&mu; embedding) fixes the embedding normalisation through the common `r_DY_incl_<category>`, so the SF is the data/embedding ratio of the tau ID; MC shape uncertainties of the P1 shifts (E34 exception) |
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
| 2016preVFP | Medium / VVLoose (mt, tt) | 0 | 1.017 <sup>+0.035</sup><sub>-0.031</sub> | -1.17 <sup>+1.02</sup><sub>-0.94</sub> |
| 2016preVFP | Medium / VVLoose (mt, tt) | 1 | 1.197 <sup>+0.030</sup><sub>-0.033</sub> | -0.59 <sup>+0.37</sup><sub>-0.43</sub> |
| 2016preVFP | Medium / VVLoose (mt, tt) | 10, 11 | 0.971 <sup>+0.031</sup><sub>-0.039</sub> | -0.56 <sup>+0.72</sup><sub>-0.48</sub> |
| 2016preVFP | Medium / Tight (et) | 0 | 0.896 <sup>+0.025</sup><sub>-0.030</sub> | -1.77 <sup>+0.88</sup><sub>-0.70</sub> |
| 2016preVFP | Medium / Tight (et) | 1 | 1.074 <sup>+0.029</sup><sub>-0.029</sub> | -0.23 <sup>+0.39</sup><sub>-0.44</sub> |
| 2016preVFP | Medium / Tight (et) | 10, 11 | 0.967 <sup>+0.032</sup><sub>-0.038</sub> | -0.30 <sup>+0.52</sup><sub>-0.77</sub> |
| 2016postVFP | Medium / VVLoose (mt, tt) | 0 | 1.025 <sup>+0.026</sup><sub>-0.028</sub> | -1.64 <sup>+0.75</sup><sub>-0.70</sub> |
| 2016postVFP | Medium / VVLoose (mt, tt) | 1 | 1.173 <sup>+0.031</sup><sub>-0.029</sub> | -1.62 <sup>+0.36</sup><sub>-0.60</sub> |
| 2016postVFP | Medium / VVLoose (mt, tt) | 10, 11 | 1.019 <sup>+0.033</sup><sub>-0.037</sub> | -0.73 <sup>+0.67</sup><sub>-0.44</sub> |
| 2016postVFP | Medium / Tight (et) | 0 | 0.914 <sup>+0.037</sup><sub>-0.024</sub> | -2.96 <sup>+0.93</sup><sub>-0.79</sub> |
| 2016postVFP | Medium / Tight (et) | 1 | 1.077 <sup>+0.025</sup><sub>-0.037</sub> | -1.23 <sup>+0.52</sup><sub>-0.56</sub> |
| 2016postVFP | Medium / Tight (et) | 10, 11 | 1.016 <sup>+0.033</sup><sub>-0.038</sub> | -0.69 <sup>+0.42</sup><sub>-0.50</sub> |
| 2017 | Medium / VVLoose (mt, tt) | 0 | 0.991 <sup>+0.027</sup><sub>-0.028</sub> | -0.65 <sup>+0.88</sup><sub>-0.84</sub> |
| 2017 | Medium / VVLoose (mt, tt) | 1 | 1.185 <sup>+0.038</sup><sub>-0.027</sub> | -2.52 <sup>+0.36</sup><sub>-0.56</sub> |
| 2017 | Medium / VVLoose (mt, tt) | 10, 11 | 1.024 <sup>+0.050</sup><sub>-0.025</sub> | -0.63 <sup>+0.56</sup><sub>-0.60</sub> |
| 2017 | Medium / Tight (et) | 0 | 0.860 <sup>+0.025</sup><sub>-0.020</sub> | -0.49 <sup>+0.87</sup><sub>-1.02</sub> |
| 2017 | Medium / Tight (et) | 1 | 1.081 <sup>+0.027</sup><sub>-0.035</sub> | -2.08 <sup>+0.44</sup><sub>-0.53</sub> |
| 2017 | Medium / Tight (et) | 10, 11 | 1.048 <sup>+0.024</sup><sub>-0.050</sub> | -0.60 <sup>+0.57</sup><sub>-0.49</sub> |
| 2018 | Medium / VVLoose (mt, tt) | 0 | 0.935 <sup>+0.024</sup><sub>-0.025</sub> | -1.22 <sup>+0.55</sup><sub>-0.61</sub> |
| 2018 | Medium / VVLoose (mt, tt) | 1 | 1.088 <sup>+0.024</sup><sub>-0.027</sub> | -1.34 <sup>+0.34</sup><sub>-0.34</sub> |
| 2018 | Medium / VVLoose (mt, tt) | 10, 11 | 0.972 <sup>+0.024</sup><sub>-0.025</sub> | 0.22 <sup>+0.45</sup><sub>-0.41</sub> |
| 2018 | Medium / Tight (et) | 0 | 0.803 <sup>+0.023</sup><sub>-0.021</sub> | -1.59 <sup>+0.76</sup><sub>-0.69</sub> |
| 2018 | Medium / Tight (et) | 1 | 0.995 <sup>+0.022</sup><sub>-0.021</sub> | -1.12 <sup>+0.36</sup><sub>-0.47</sub> |
| 2018 | Medium / Tight (et) | 10, 11 | 0.966 <sup>+0.025</sup><sub>-0.023</sub> | 0.27 <sup>+0.43</sup><sub>-0.48</sub> |

The interval of the scale factor includes the uncertainty of the embedding normalisation from the mm
region and the MC shape uncertainties; the energy scale is in percent of the tau four-momentum.

## Files

| File | md5 | sha256 |
|---|---|---|
| `Run2-2016preVFP-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2016preVFPUL.json.gz` | `41a980dd820964fe1130dbe6990b3bf9` | `c12d61d3fb9ee422b42634d8447736f47343b9e1fd9150e42d52754eaf051006` |
| `Run2-2016postVFP-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2016postVFPUL.json.gz` | `e9acd4a672841c4ac3b4fa93f9596607` | `55427a7bda30f6e7c765bd632a830148896a50e1025d8727c4a220f8b17ea158` |
| `Run2-2017-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2017UL.json.gz` | `b34248dd206b34fedab2cd119ac0ef68` | `c7c717e2f7149d295e0959836d694cf532b0387a5b274b97ba9d28d5fb4b46f8` |
| `Run2-2018-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2018UL.json.gz` | `c5d1b87928a14c1a747559edf1204fa7` | `6ab4751c600ab6995b1328b8cd88f3974a63999854b43e9a89a7c21154e7b07b` |

KingMaker's framework-tarball hash does not cover `payloads/`: set `force_repack_tarball` after
replacing these files, and produce under a new tag.
