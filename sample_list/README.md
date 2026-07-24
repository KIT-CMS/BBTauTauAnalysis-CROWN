# Sample lists

Flat, per-era sample lists consumed by KingMaker's `ProduceNtuples`:

```bash
law run ProduceNtuples --analysis bbtautau --config sm_btag_efficiency_config \
    --sample-list <CROWN>/analysis_configurations/bbtautau/sample_list/sm_2018_binned_mc.txt \
    --nanoAOD-version v15 --era 2018 --scopes et,mt,tt --shifts None \
    --production-tag <tag> --workers 100
```

Four lists exist, spanning two independent axes -- **inclusive vs binned**
(how much MC statistics) and **with vs without data** (which config accepts
it). All four are era 2018 / NanoAOD v15.

| List | Nicks | Files | Events | MC strategy | Use with |
|---|---|---|---|---|---|
| `sm_2018_inclusive.txt` | 72 | 4770 | 4.92G | inclusive | `sm_config` |
| `sm_2018_inclusive_mc.txt` | 60 | 2594 | 2.24G | inclusive | `sm_btag_efficiency_config` |
| `sm_2018_binned.txt` | 79 | 5380 | 5.58G | binned (max. statistics) | `sm_config` |
| `sm_2018_binned_mc.txt` | 67 | 3204 | 2.90G | binned (max. statistics) | `sm_btag_efficiency_config` |

## Are comments or blank lines allowed? No.

KingMaker parses these files in `processor/tasks/CROWNBase.py::parse_samplelist`:

```python
if str(sample_list).endswith(".txt"):
    with open(str(sample_list)) as file:
        samples = [nick.replace("\n", "") for nick in file.readlines()]
```

Every line becomes a sample nick **verbatim** -- no comment stripping, no
blank-line skipping, no whitespace trimming. `set_sample_data` then looks each
one up in the sample database and, for anything it cannot find, raises

```
Exception: Sample not found in DB: <the line>
```

so a `#`-comment or a blank line does not get skipped -- it aborts the run
(loudly, at least, rather than silently producing a partial dataset). Rules:

- one nick per line, nothing else;
- **no comments, no blank lines**, including no trailing blank line;
- the filename **must end in `.txt`** -- with any other extension (`.yaml`,
  `.list`, no suffix) `parse_samplelist` skips the file branch entirely and
  treats the path string itself as one literal sample nick.

Keep all explanatory prose in this README, never in the list files.

Nicks resolve against
`KingMaker/sample_database/nanoAOD_<version>/datasets.json` (and the per-sample
`nanoAOD_<version>/<era>/<sample_type>/<nick>.json`), which is where the era
and `sample_type` driving the CROWN build come from.

## Axis 1: with or without data -- this is not a preference

Passing a list containing data nicks to `sm_btag_efficiency_config` **fails the
build**:

- that config declares no `data` in its `AVAILABLE_SAMPLES`, and its profile
  sets `mc_only=True`. `ProduceNtuples` derives the `sample_types` to build
  from the nicks in the list (`KingMaker/processor/tasks/CROWNMain.py`, passed
  on as `-DSAMPLES`), so a data nick reaches `generate.py --sample data` and
  dies with `ValueError: Configuration profile 'sm_btag_efficiency' accepts MC
  only, got 'data'`;
- `sm_config` *does* include `data` in `DEFAULT_SAMPLES` -- the production
  entry point needs the data nicks.

The `_mc` lists are their non-`_mc` counterpart minus the same 12 data nicks
(Tau/SingleMuon/EGamma &times; Run2018A-D, 2176 files / 2.7G events -- roughly
half the production).

## Axis 2: inclusive or binned

**The `inclusive` lists really are inclusive** -- that is a deliberate physics
choice, not an accident of what was available:

- `wjets`: the single **inclusive** `WJetsToLNu` amcatnloFXFX sample;
- `dyjets`: the **inclusive** `DYJetsToLL_M-50` and `M-10to50` amcatnloFXFX
  samples.

They are cheap (28 and 163 files) but statistically thin, especially W+jets at
29.1M events. The `binned` lists replace exactly those two picks with a
**complete, non-overlapping partition of the same phase space, from the same
generator and tune**:

| Category | inclusive | binned | Gain |
|---|---|---|---|
| `wjets` | `WJetsToLNu` (1 sample, 29.1M ev) | `WJetsToLNu_{0J,1J,2J}` (3, 451.5M ev) | &times;15.5 |
| `dyjets` M-50 | `DYJetsToLL_M-50` (1, 196.6M ev) | `DYJetsToLL_LHEFilterPtZ-{0To50,50To100,100To250,250To400,400To650,650ToInf}` (6, 433.2M ev) | &times;2.2 |

Nothing else differs between an inclusive and a binned list. Both partitions
cover their full phase space (0/1/&ge;2 jets; PtZ 0&rarr;&infin;) with no gaps
and no overlap, so the standard per-sample cross-section weighting is correct
as-is -- **no stitching, no overlap removal, no LHE filter cut is required**.
That is precisely why these two partitions were chosen over the alternatives
below.

`dyjets` `M-10to50` gains nothing from binning (its only alternative is a
madgraphMLM sample of the same size, in the same phase space), so it is
identical in all four lists.

### What is deliberately *not* in the binned lists

Adding any of these on top of what is already listed is a physics bug, not
extra statistics:

- **the HT-binned `WJetsToLNu_HT-*` / `DYJetsToLL_M-50_HT-*` madgraphMLM sets**
  -- a *different, competing* binning scheme. Using them together with the
  NJet/PtZ partition double counts, and they only start at HT&gt;70, so on
  their own they need the inclusive sample stitched in to cover HT&lt;70;
- **the `WJetsToLNu_Pt-*_MatchEWPDG20` set** -- a third competing scheme
  (more raw events than NJet, but only Pt&gt;100, so it needs stitching plus
  overlap handling against the inclusive remainder);
- **the `madgraphMLM` inclusive W/DY samples** -- a different generator for the
  same phase space, i.e. an alternative to the amcatnloFXFX pick, not an
  addition to it;
- **the inclusive-pythia8 `diboson` samples** -- the lists already take the
  exclusive decay-channel amcatnlo/powheg samples per boson pair, which carry
  9.5&times; the statistics (257M vs 27M events). The inclusive ones are the
  *lower*-statistics alternative here, and mixing generators would change the
  jet-flavour composition the efficiency map is measured from;
- **the 4-flavour-scheme `singletop` t-channel samples** -- alternative scheme
  to the selected 5FS ones, same phase space;
- **`TuneCP5up`/`TuneCP5down` datasets** -- parton-shower-tune *systematic
  variations*. They are not additional statistics for the nominal sample under
  any circumstances;
- **the `WToTauNu_M-*` high-mass samples** -- a separate high-mass tail whose
  phase space the inclusive W sample already covers; adding them double counts
  that tail;
- **every `Embedding` dataset** -- Phase-1 embedding exclusion, see the repo
  `README.md`.

## Contents

72 (or 79) nicks: full 2018 data coverage plus one or more samples for each of
the 13 SM MC `sample_type` categories, i.e. exactly
`sm_config.DEFAULT_SAMPLES`. The `_mc` variants' 13 `sample_type`s match
`sm_btag_efficiency_config.AVAILABLE_SAMPLES` exactly.

| Category | incl. | binned | Category | incl. | binned |
|---|---|---|---|---|---|
| `data` (Tau/SingleMuon/EGamma &times; Run2018A-D) | 12 | 12 | `rem_ttbar` | 11 | 11 |
| `diboson` | 14 | 14 | `singletop` | 6 | 6 |
| `electroweak_boson` | 7 | 7 | `ttbar` | 3 | 3 |
| `rem_hbb` | 11 | 11 | `dyjets` | 2 | 7 |
| `wjets` | 1 | 3 | `ggh_htautau` | 1 | 1 |
| `hh2b2tau` (`node_SM`) | 1 | 1 | `rem_higgs` | 1 | 1 |
| `vbf_hbb` | 1 | 1 | `vbf_htautau` | 1 | 1 |

Selected against `sample_database` commit `1bba58ed`.

## Coverage: what the 2018 database holds and what the lists take

The sample database registers **131** nicks for era 2018 / NanoAOD v15
(`nanoAOD_v15/2018/*/*.json`, 17 `sample_type` directories). The widest list
(`sm_2018_binned.txt`) takes 79 of them. Expected event counts below are
`xsec * 59.83/fb`, i.e. produced events before any selection -- a scale
indicator, not a signal-region yield.

| `sample_type` | in | out | Out: what and why |
|---|---|---|---|
| `data` | 12 | 0 | complete |
| `ggh_htautau`, `vbf_htautau`, `vbf_hbb`, `rem_hbb`, `rem_higgs` | 15 | **0** | **single Higgs is complete** -- see below |
| `electroweak_boson` | 7 | 0 | complete |
| `hh2b2tau` | 1 | 0 | the `node_SM` signal |
| `rem_ttbar` | 11 | 0 | complete |
| `ttbar` | 3 | 1 | `TuneCP5up` shower-tune systematic |
| `singletop` | 6 | 2 | 4FS t-channel alternative to the selected 5FS |
| `diboson` | 14 | 4 | inclusive-pythia8 `WW`/`WZ`/`ZZ` + the `ZZTo4L_M-1toInf` variant, all alternatives |
| `dyjets` | 7 | 11 | competing binning schemes / madgraphMLM alternatives |
| `wjets` | 3 | 22 | competing schemes + the 9 `WToTauNu_M-*` high-mass samples |
| `embedding` | 0 | 8 | Phase-1 embedding exclusion (repo `README.md`) |
| `ggZZ` | **0** | 3 | see below |
| `triboson` | **0** | 1 | see below |

### Single Higgs: complete, and wider in the code than in the database

All 15 registered single-Higgs samples are listed: ggH&rarr;&tau;&tau;,
VBF&rarr;&tau;&tau;, VBF&rarr;bb, W&plusmn;H&rarr;bb, ZH&rarr;bb (all four Z
decay modes), ggZH&rarr;bb (all four), ttH&rarr;bb and ttH&rarr;non-bb (which is
what carries ttH&rarr;&tau;&tau;). Nothing is left out.

What is genuinely missing is missing from the **database**, not from these
lists: `constants.py`'s `LEGACY_AVAILABLE_SAMPLES` still names `ggh_hbb`,
`rem_htautau`, `rem_hww` and `rem_hzz`, but **no 2018 v15 dataset is registered
under any of them** -- there is no dedicated VH&rarr;&tau;&tau; or
ggH&rarr;bb sample to select. Adding one means registering it in
`sample_database` first, and (for `rem_htautau`) also adding the category to
`sm_config.DEFAULT_SAMPLES` and producing its b-tag efficiency.

### `ggZZ` and `triboson`: negligible, and blocked in code

Neither category is selectable at all today, by design:

- `ggZZ` -- 3 mcfm701 gg&rarr;ZZ continuum samples (`2e2tau`, `2mu2tau`,
  `4tau`; 0.0082 pb combined, ~491 produced events). They do make
  &tau;&tau;, but they contain no b quarks, so a two-b-tag selection has
  almost no acceptance for them.
- `triboson` -- only `ZZZ` is registered (0.0148 pb, ~883 events). `WWW`,
  `WWZ` and `WZZ` are **not in the database at all**, so this category could
  not be made complete even if it were wanted.

Together that is ~1.4k produced events against ~5e9 for the listed background
(&sim;3e-7), or ~1.4e-4 of the `diboson` category they would join -- far below
any systematic. The comparison against the 134 produced signal events is
superficially less flattering, but signal has two real b jets and two real
taus while these have neither, so their signal-region acceptance is smaller by
orders of magnitude.

They are blocked at the code level, not merely omitted from a list: neither
name appears in `constants.py`'s `LEGACY_AVAILABLE_SAMPLES` nor in either SM
config's `AVAILABLE_SAMPLES`, and
`tests/test_generator_interface.py::test_sm_surface_includes_signal_and_excludes_forbidden`
**asserts** that they stay out. Putting such a nick in a list therefore fails
in `generate.py` with `ValueError: Config '<name>' does not accept sample
'ggZZ'`. Enabling either one is a code change (sample surface + the relevant
`SampleModifier`/rule wiring in `common_config.py` + that test), not a list
edit.

### Confirmed against the previous (private-production) sample list

An earlier iteration of this analysis ran on **privately produced NanoAOD**
(USER tier, `<dataset>_<user>-mc_2018UL_<campaign>_<timestamp>-<hash>` nicks
from `aakhmets`/`sdaigler` campaigns). None of those nicks work against the
central database -- the registration here is
`<dataset>_RunIISummer20UL18NanoAODv15-150X` -- but mapping that list's 103
entries (83 distinct datasets, the rest `Ext1`/`Ext2` extensions of a base) onto
NanoAOD v15 pins down what the v15 registration is actually missing:

| Missing from `nanoAOD_v15/2018`, used before | Note |
|---|---|
| `WWW_4F`, `WWZ_4F`, `WWZJetsTo4L2Nu_4F`, `WZZ` | 4 of the 5 triboson datasets; only `ZZZ` is registered |
| `WminusHToTauTau`, `WplusHToTauTau`, `ZHToTauTau`, `ttHToTauTau` | the whole `rem_htautau` (VH/ttH &rarr; &tau;&tau;) group |
| `TTWJetsToLNu`, `TTWJetsToQQ` (amcatnloFXFX-madspin) | superseded: v15 registers `ttWJets` (madgraphMLM) instead |
| `WJetsToLNu_HT-2500ToInf` | v15 has only 7 HT bins (70To100 &hellip; 1200To2500) |
| `WZTo4Q` | v15 registers `WZTo2Q2Nu` instead |

The first two rows are the substantive ones: for a &tau;&tau; final state,
VH/ttH&rarr;&tau;&tau; is a genuine background and the triboson set is
incomplete. Both need a **`sample_database` registration request**, not a list
edit -- and `rem_htautau` additionally needs the category added to
`sm_config.DEFAULT_SAMPLES` and to the b-tag efficiency measurement.

Conversely, the lists here cover 26 datasets that the old production did not,
mostly the b-associated Higgs and hadronic EWK/diboson modes a bb&tau;&tau;
selection cares about: all four ggZH&rarr;bb, W&plusmn;H&rarr;bb,
ZH&rarr;bb(ZToBB/ZToNuNu), VBFH&rarr;bb, the `WToQQ`/`ZToNuNu`/`ZToQQ` EWK
samples, both ST s-channel samples, `TTZToNuNu`, `TTZToLL_M-1to10`, `ttWJets`,
`ttZJets`, `ZZTo4Q`, `ZZTo2Nu2Q` and `WZTo2Q2Nu`.

**Do not copy the old list as a selection.** It is a *production* list: it
carries the madgraphMLM inclusive DY *and* the HT-binned madgraphMLM set *and*
the amcatnloFXFX `LHEFilterPtZ` set simultaneously (likewise inclusive plus
HT-binned W). That is legitimate for producing ntuples -- `constants.py` keeps
`dyjets_madgraph`, `dyjets_amcatnlo`, `dyjets_powheg` as separate sample groups
precisely so one gets chosen afterwards -- but using it as-is in one analysis
double counts DY and W several times over.

## Editing, or adding an era

Nothing validates these files -- there is no manifest or validator layer any
more -- so the invariants are yours to keep:

- **do not double count.** Pick exactly one strategy per phase space, per the
  section above;
- **keep the four lists consistent.** They differ only along the two documented
  axes; a nick added to one belongs in the others too, unless it is data (then
  only the non-`_mc` pair) ;
- **keep every category populated.** Every process used by the analysis needs
  an entry on the correctionlib `sample_type` axis of the efficiency payload;
  otherwise its runtime lookup cannot succeed.

`docs/sm_2018_efficiency_workflow.md` Step 1 carries a copy-pasteable check for
the first and second of those, plus a database-resolution check for every nick.

For a new era, add `sm_<era>_*.txt` next to this file, list it in the table
above, and pass the matching `--era`/`--nanoAOD-version` to `ProduceNtuples`
(the file name is not parsed -- KingMaker takes the era from the CLI and the
database, not from the list).
