# Sample lists

Flat KingMaker `--sample-list` files. Each nick is resolved against
`KingMaker/sample_database/nanoAOD_<version>/datasets.json`, which is where the era and `sample_type`
driving the CROWN build come from (there is no `--era` option; the era follows from the nicks).

```bash
law run ProduceNtuples --analysis bbtautau --config sm_btag_efficiency_config \
    --sample-list <CROWN>/analysis_configurations/bbtautau/sample_list/sm_2018_binned_mc.txt \
    --scopes et,mt,tt --shifts None --production-tag <tag> --workers 100
```

## The four lists

All four are era 2018 / NanoAOD v15 and differ along two independent axes.

| List | MC strategy | Use with |
|---|---|---|
| `sm_2018_inclusive.txt` | inclusive | `sm_config` |
| `sm_2018_inclusive_mc.txt` | inclusive | `sm_btag_efficiency_config` |
| `sm_2018_binned.txt` | binned (max. statistics) | `sm_config` |
| `sm_2018_binned_mc.txt` | binned (max. statistics) | `sm_btag_efficiency_config` |

**With or without data.** `sm_btag_efficiency_config` is MC only (`mc_only=True`, no `data` in its
`AVAILABLE_SAMPLES`), so a data nick reaches `generate.py --sample data` and aborts the build. Each
`_mc` list is exactly its non-`_mc` counterpart minus the same 12 data nicks (Tau / SingleMuon /
EGamma &times; Run2018A-D); `sm_config` takes the full lists.

**Inclusive or binned.** The `inclusive` lists take the inclusive `WJetsToLNu` and `DYJetsToLL_M-50`
amcatnloFXFX samples; the `binned` lists replace exactly those two with same-generator,
non-overlapping partitions of the same phase space (`WJetsToLNu_{0J,1J,2J}` and the six
`DYJetsToLL_LHEFilterPtZ-*` bins). Nothing else differs -- `DYJetsToLL_M-10to50` is identical in all
four. Both partitions are complete and gap-free, so plain per-sample cross-section weighting stays
correct: no stitching, no overlap removal.

## Format

`KingMaker/processor/tasks/CROWNBase.py::parse_samplelist` turns every line into a nick **verbatim** --
no comment stripping, no blank-line skipping, no whitespace trimming -- and an unresolvable line
aborts the run. Therefore:

- one nick per line, nothing else;
- no comments, no blank lines, no trailing blank line;
- the filename must end in `.txt`, or `parse_samplelist` treats the path string itself as one nick;
- keep explanatory prose in this README, never in the list files.

## Invariants nothing checks for you

- **Never mix binning or generator schemes.** Pick exactly one strategy per phase space. The HT-binned
  `*_HT-*` madgraphMLM sets and `WJetsToLNu_Pt-*_MatchEWPDG20` are two further, mutually exclusive
  schemes; adding either on top of the NJet/PtZ partition double counts. The same holds for the
  madgraphMLM inclusive W/DY samples (a generator alternative, not an addition) and for
  `TuneCP5up`/`TuneCP5down` datasets, which are systematic variations, not extra statistics.
- **Keep the four lists consistent** along the two axes above: a nick added to one belongs in the
  others too, unless it is data -- then only in the non-`_mc` pair.
- **Keep every MC category populated.** Each `sample_type` in a list must exist on the `sample_type`
  axis of the b-tag efficiency payload, or its runtime lookup cannot succeed.

## Checking or extending a list

Load the database JSON and look up every line: each nick must be a key with `era == "2018"`, and the
set of `sample_type` values must equal `sm_btag_efficiency_config.AVAILABLE_SAMPLES` for an `_mc` list,
plus `data` for a full one. Filtering the same JSON by `era` and `sample_type` is also how candidate
nicks for a new list or a new era are found; for a new era, add `sm_<era>_*.txt` next to this file and
pass the matching `--era`/`--nanoAOD-version` to `ProduceNtuples` (the file name itself is not parsed).

## Known gaps

`rem_htautau` (VH / ttH &rarr; &tau;&tau;) has no 2018 v15 dataset registered at all, and of the
triboson set only `ZZZ` is; closing either gap needs a `sample_database` registration request, not a
list edit. `ggZZ` and `triboson` are additionally absent from `constants.LEGACY_AVAILABLE_SAMPLES`, so
a nick of either type fails in `generate.py` before `build_config` is reached.
