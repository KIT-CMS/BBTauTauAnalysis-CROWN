# Sample lists

Flat KingMaker `--sample-list` files. Each nick is resolved against
`KingMaker/sample_database/nanoAOD_<version>/datasets.json`, which is where the era and `sample_type`
driving the CROWN build come from (there is no `--era` option; the era follows from the nicks).

```bash
law run ProduceNtuples --analysis bbtautau --config sm_btag_efficiency_config \
    --sample-list <CROWN>/analysis_configurations/bbtautau/sample_list/sm_2018_binned_mc.txt \
    --scopes et,mt,tt,em,ee,mm --shifts None --production-tag <tag> --workers 100
```

## The lists

One set per Run-2 era (`<era>` = `2016preVFP`, `2016postVFP`, `2017`, `2018`), all NanoAOD v15:

| List | Content | Use with |
|---|---|---|
| `sm_<era>_binned.txt` | data and MC, binned W and DY | `sm_config` |
| `sm_<era>_binned_mc.txt` | the same without data | `sm_btag_efficiency_config` |
| `sm_<era>_embedding.txt` | et/mt/tt tau embedding | `sm_config` |
| `sm_<era>_tau_id_measurement.txt` | SingleMuon data, MC, mutau and muemb embedding | `sm_tau_id_measurement_config` |
| `sm_2018_inclusive.txt`, `sm_2018_inclusive_mc.txt` | 2018 only: the binned lists with inclusive W | `sm_config`, `sm_btag_efficiency_config` |

Nicks per era (data / MC / embedding):

| Era | `binned` | `binned_mc` | `embedding` | `tau_id_measurement` |
|---|---|---|---|---|
| 2016preVFP | 84 (15 / 69) | 69 | 15 | 30 (5 / 15 / 10) |
| 2016postVFP | 75 (9 / 66) | 66 | 9 | 24 (3 / 15 / 6) |
| 2017 | 84 (15 / 69) | 69 | 15 | 30 (5 / 15 / 10) |
| 2018 | 81 (12 / 69) | 69 | 12 | 27 (4 / 15 / 8) |

Every list is sorted with Python `sorted()`, one nick per line, with a trailing newline, and holds the
nicks of one era only. The ShapeSmith inventories are byte-identical copies.

## Rules per era

**Data.** `SingleMuon` (mt, em, mm), `SingleElectron` (et, ee; `EGamma` in 2018) and `Tau` (tt), every
run of the era: 2016preVFP B-F (HIPM, B as `_v2-v1`), 2016postVFP F-H, 2017 B-F, 2018 A-D. Not listed:
`SingleMuon_Run2016B-HIPM_UL2016_NanoAODv15-v1` (B ver1, no golden lumisection); 2017 G and H are not
registered (5-TeV and low-pileup runs). The `_mc` lists are their full lists without the data nicks;
`sm_btag_efficiency_config` is MC only (`mc_only=True`), and a data nick aborts its build.

**MC of the binned lists**, one nick per entry in every era, by `sample_type`:

| `sample_type` | Samples |
|---|---|
| `dyjets` | the six `DYJetsToLL_LHEFilterPtZ-*_MatchEWPDG20` bins, the inclusive `DYJetsToLL_M-50` (`npartons == 0` only, below), `DYJetsToLL_M-10to50` |
| `wjets` | `WJetsToLNu_{0J,1J,2J}` |
| `ttbar` | `TTTo2L2Nu`, `TTToHadronic`, `TTToSemiLeptonic` |
| `singletop` | `ST_tW_{top,antitop}_5f`, `ST_s-channel_4f_{hadronic,lepton}Decays`, `ST_t-channel_{top,antitop}_5f` |
| `diboson` | `WWTo{1L1Nu2Q,2L2Nu,4Q}`, `WZTo{1L1Nu2Q,1L3Nu,2Q2L,2Q2Nu,3LNu,4Q}`, `ZZTo{2L2Nu,2Q2L,4L,4Q}` and the ZZ &rarr; 2&nu;2q sample of the era: `ZZTo2Nu2Q_5f` in 2016 and 2017, `ZZTo2Q2Nu` in 2018 (amcatnlo exists in UL18 only) |
| `electroweak_boson` | `EWKW{Plus,Minus}2Jets_WToLNu`, `EWKZ2Jets_ZTo{LL,NuNu}`, `EWKW{plus,minus}2Jets_WToQQ`, `EWKZ2Jets_ZToQQ` |
| `rem_ttbar` | `TTWJetsTo{LNu,QQ}`, `TTZToLLNuNu_M-10`, `TTZToLL_M-1to10`, `TTZToQQ`, `TTWW`, `TTWZ`, `TTZZ`, `TTWH`, `TTZH` |
| `ggh_htautau`, `vbf_htautau` | `GluGluHToTauTau_M125`, `VBFHToTauTau_M125` |
| `vbf_hbb`, `rem_hbb`, `rem_higgs` | `VBFHToBB_M-125`; `W{plus,minus}H_HToBB_WToLNu`, `{,gg}ZH_HToBB_ZTo{LL,NuNu,QQ}`, `ttHTobb`; `ttHToNonbb` |
| `rem_htautau` | `ZHToTauTau_M125`, `W{plus,minus}HToTauTau_M125`; none in 2016postVFP (no UL16 sample, ShapeSmith borrows the 2016preVFP n-tuples) |
| `hh2b2tau` | the signal `GluGluToHHTo2B2T_kl-1p00` (powheg) and its cross-check `GluGluToHHTo2B2Tau_..._node_SM` (madgraph) |

The two HH samples are alternatives for the same process: consumers keep them in separate groups and
never add them. The &kappa;<sub>&lambda;</sub> = 0, 2.45, 5 powheg samples are registered but not listed.

**Embedding.** The lists follow one rule, which the tests recompute: every nick of `datasets.json` with
`sample_type` `embedding`, the era and the final-state token `_eltau_`, `_mutau_` or `_tautau_` (no
`muemb`), without the 2016 B ver1 nicks (`_B_ver1_`, no golden lumisection):

```python
nicks = sorted(
    nick for nick, entry in datasets.items()
    if entry["sample_type"] == "embedding" and entry["era"] == era and "_B_ver1_" not in nick
    and any(token in nick for token in ("_eltau_", "_mutau_", "_tautau_"))
)
```

Embedding is built for et, mt and tt only; any other scope aborts the build. It runs as a second
`ProduceNtuples` call under the same (fresh) production tag as the data/MC production it is combined
with, with the same analysis, CROWN and KingMaker commits and payloads. The embedding executable is
built although the tag exists, because KingMaker builds per sample type and era. Never rerun that tag
with other scopes: a reused tag does not rebuild an existing sample type, and new scopes come out
empty.

**Tau-ID measurement.** The `SingleMuon` data of the era, the `_mutau_` (mt) and `_muemb_` (mm)
embedding nicks (without B ver1), and the MC of the precedent `SFs_EMB_Run2_04_08_26` (jvoss,
`KingMaker_v15_Run2/samples_run2_SFs_v15.txt`): the inclusive `DYJetsToLL_M-10to50` and `DYJetsToLL_M-50`
amcatnloFXFX (no PtZ bins, so no `npartons` cut), `ST_tW_{top,antitop}_5f`,
`ST_t-channel_{top,antitop}_4f` (powheg-madspin), the three `TTTo*`, `WW`, `WZ`, `ZZ` (pythia8), and W in
jet bins, `WJetsToLNu_{0J,1J,2J}`, instead of the precedent's inclusive amcatnloFXFX `WJetsToLNu`
(spec E17). It is produced with `--scopes mt,mm`, MC with `--shifts all`, under a fresh production tag.

## The DY partition

The W partition is complete, so plain per-sample cross-section weighting is correct for it. The DY
partition is **not**: the `LHEFilterPtZ-*` bins contain no event with zero LHE partons
(`LHE_Njets == 0`, i.e. `LHE_Vpt == 0`), which is 69% of the `DYJetsToLL_M-50` cross section in 2018
(0To50 = 1404.8 pb = 0.231 &times; 6077.22 pb; the six bins sum to 1877 pb). The binned lists therefore
also carry the inclusive `DYJetsToLL_M-50` nick in every era, and every consumer must take **only its
`npartons == 0` events** (CROWN writes `npartons` = `LHE_Njets` for `dyjets`) at the full inclusive
normalisation. The PtZ bins always have `npartons >= 1`, so the two sets are disjoint and a hard cut
suffices, no stitching weights. CROWN itself cannot apply the cut (the inclusive and the binned samples
share the `dyjets` executable); ShapeSmith does it through a per-sample cut, the TauFakeFactors
preselection through `sample_cuts`. Using the inclusive nick without that cut counts every
`npartons >= 1` DY event twice.

The 2018 `inclusive` lists replace the W and DY partitions by the inclusive `WJetsToLNu` and
`DYJetsToLL_M-50` amcatnloFXFX samples; v7 does not use them.

## Format

`KingMaker/processor/tasks/CROWNBase.py::parse_samplelist` turns every line into a nick **verbatim** --
no comment stripping, no blank-line skipping, no whitespace trimming -- and an unresolvable line
aborts the run. Therefore:

- one nick per line, nothing else;
- no comments, no blank lines, no trailing blank line;
- the filename must end in `.txt`, or `parse_samplelist` treats the path string itself as one nick;
- keep explanatory prose in this README, never in the list files.

## Invariants

`tests/test_sm_main_config.py`, `tests/test_embedding_run2_v15_config.py` and
`tests/test_sm_tau_id_measurement_config.py` check the lists against the sample database: lengths and
data counts per era, one era per list, the `sample_type` set, the `_mc` relation, the sort order, the
embedding rule and the phase-space rules below. Beyond that:

- **Never mix binning or generator schemes.** Pick exactly one strategy per phase space. The HT-binned
  `*_HT-*` madgraphMLM sets and `WJetsToLNu_Pt-*_MatchEWPDG20` are two further, mutually exclusive
  schemes; adding either on top of the NJet/PtZ partition double counts. The same holds for the
  madgraphMLM inclusive W/DY samples (a generator alternative, not an addition) and for
  `TuneCP5up`/`TuneCP5down` and `hdamp` datasets, which are systematic variations, not extra statistics.
- **Never add a sample whose phase space another one already covers.** The lists take ttZ from
  `TTZToLLNuNu_M-10`, `TTZToQQ` and `TTZToLL_M-1to10` and ttW from `TTWJetsTo{LNu,QQ}`; the inclusive LO
  `ttZJets` and `ttWJets` madgraphMLM and `TTZToNuNu` (contained in `TTZToLLNuNu_M-10`) would count them
  twice. One ZZ &rarr; 2&nu;2q sample per era: `ZZTo2Nu2Q_5f` and `ZZTo2Q2Nu` are the same process.
  `{,gg}ZH_HToBB_ZToQQ` contain Z &rarr; bb (21 % of their decays, cross section with
  B(Z &rarr; hadrons)), so the `ZToBB` samples are not listed.
- **Keep every MC category populated.** Each `sample_type` in a list must exist on the `sample_type`
  axis of the era's b-tag efficiency payload, or its runtime lookup cannot succeed.
- **New era or new sample.** Filter `datasets.json` by `era` and `sample_type` for candidate nicks,
  extend the tables above, regenerate the lists sorted, and copy them to the ShapeSmith inventory.

## Known gaps

`ttHToTauTau` has no v15 sample in any era (`ttHToNonbb` covers it), and VBF HH is missing in UL18, so
neither is listed. `ggZZ` and `triboson` are absent from `constants.LEGACY_AVAILABLE_SAMPLES`, so a
nick of either type fails in `generate.py` before `build_config` is reached.
