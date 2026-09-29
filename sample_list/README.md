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
amcatnloFXFX samples; the `binned` lists replace those with same-generator partitions
(`WJetsToLNu_{0J,1J,2J}` and the six `DYJetsToLL_LHEFilterPtZ-*` bins). `DYJetsToLL_M-10to50` is
identical in all four. The W partition is complete, so plain per-sample cross-section weighting is
correct for it.

The DY partition is **not** complete: the `LHEFilterPtZ-*` bins contain no event with zero LHE partons
(`LHE_Njets == 0`, i.e. `LHE_Vpt == 0`), which is 69% of the `DYJetsToLL_M-50` cross section
(0To50 = 1404.8 pb = 0.231 &times; 6077.22 pb; the six bins sum to 1877 pb). `sm_2018_binned.txt`
therefore also carries the inclusive `DYJetsToLL_M-50` nick (as does `sm_2018_binned_mc.txt`), and
every consumer must take **only its `npartons == 0` events** (CROWN writes `npartons` = `LHE_Njets`
for `dyjets`) at the full inclusive normalisation. The PtZ bins always have `npartons >= 1`, so the
two sets are disjoint and a hard cut suffices, no stitching weights. CROWN itself cannot apply the cut
(the inclusive and the binned samples share the `dyjets` executable); ShapeSmith does it through a
per-sample cut, the TauFakeFactors preselection through `sample_cuts`. Using the inclusive nick
without that cut counts every `npartons >= 1` DY event twice.

## The embedding list

`sm_2018_embedding.txt` is a fifth list outside the two axes: the 12 2018 tau-embedding nicks of
`sm_config` (`sample_type` `embedding`, see `embedding_run2_v15.py` and the README section "Tau
embedding"). Its content follows one rule, shared with the ShapeSmith inventory
`inventory/sm2018_embedding.txt`, which must stay byte-identical: every nick of
`KingMaker/sample_database/nanoAOD_v15/datasets.json` with `sample_type` `embedding`, `era` 2018 and
the final-state token `_eltau_`, `_mutau_` or `_tautau_` (no `muemb`), sorted with Python
`sorted()`, one nick per line, with a trailing newline.

```python
nicks = sorted(
    nick for nick, entry in datasets.items()
    if entry["sample_type"] == "embedding" and entry["era"] == "2018"
    and any(token in nick for token in ("_eltau_", "_mutau_", "_tautau_"))
)
```

Embedding is built for et, mt and tt only; any other scope aborts the build. It runs as a second
`ProduceNtuples` call under the same (fresh) production tag as the data/MC production it is combined
with, with the same analysis, CROWN and KingMaker commits and payloads, and with all shifts, which are
exactly the embedding tau shifts:

```bash
law run ProduceNtuples --analysis bbtautau --config sm_config \
    --sample-list <CROWN>/analysis_configurations/bbtautau/sample_list/sm_2018_embedding.txt \
    --scopes et,mt,tt --shifts all --production-tag <tag of the data/MC production> --workers 100
```

The embedding executable is built although the tag exists, because KingMaker builds per sample type
and era. Never rerun that tag with other scopes: a reused tag does not rebuild an existing sample type,
and new scopes come out empty.

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
