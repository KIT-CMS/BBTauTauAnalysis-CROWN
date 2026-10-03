# SM 2018 fake factors, 2026-10-03 (commissioning)

`2018/` holds the six fake-factor payloads of the SM HH &rightarrow; bb&tau;&tau; analysis that
`sm_fake_factors.py` reads (`SM_PAYLOAD_DIRS`). They are the first payloads measured with ShapeSmith on
the embedding production. They commission the fake-factor friend and the `jet_fakes: ff` analysis; they
are not final, because the embedding still uses the preliminary tau ID/ES payload
(`payloads/tau_embedding/README.md`), whose measured successor needs a new production and a new
fake-factor measurement.

| | |
|---|---|
| Source | `shapesmith measure -c configs/ff_sm2018_binned_v5.yaml`, output `output/ff_sm2018_binned_v5/fake_factors/2018/`; copied byte for byte |
| Code | ShapeSmith core `ddd3f16` (`feat/logging`), BBTauTauAnalysis-ShapeSmith `27036d4` (`bbtautau_shapesmith.ff_measurement:build`), run configuration sha256 `20b29539...98d00b8` |
| Sample database | KingMaker_sample_database `33c257b` (corrected mutau 2018D event count) |
| Input n-tuples | `sm2018_binned_v5` (data/MC: sample list `sm_2018_binned.txt` with the inclusive DY `npartons == 0` part; embedding: `sm_2018_embedding.txt`), `embedding: true` |
| Method | jvoss's TauFakeFactors method (QCD + ttbar, fractions, orthogonal DR&rightarrow;SR, compound non-closure), binning and fits from `ff_tables.py`; the differences to his configuration are listed in the `ff_measurement.py` docstring |
| Model | QCD + ttbar; the fractions carry the processes `QCD` and `ttbar` (keys `frac_QCD`, `frac_ttbar_J`) |
| Shifts | unchanged keys: 17 shift pairs per leg are selected (as for 2026-09-22), equal to ShapeSmith `constants.FF_SHIFTS_LT/TT` |

| File | md5 | sha256 |
|---|---|---|
| `fake_factors_et.json.gz` | `d7d85398fca40668e7dcc6d39caf66e3` | `b3908134e9c632878fd65a46c5c6e4edc9597b295fa9539741aca0df97da003e` |
| `fake_factors_mt.json.gz` | `f897f439cee520ab760166054dc977dc` | `7a851380c20f698d003c6ca33d168eb1ae0dbc6ae92a45d4eae7be9d5e49a957` |
| `fake_factors_tt.json.gz` | `0b2dd0be768fcef232643713b0ea09b3` | `99948b464475035b85d8c249aac2a7fcef9030b8ab8e98eaec03b7442167de08` |
| `FF_corrections_et.json.gz` | `99e12d04564654e7d80c067c39c3d72d` | `1dc17187e6f9c0790bd2aa641adaa697f0af946978a2ec8c8b69baa9e5b2092a` |
| `FF_corrections_mt.json.gz` | `ee0d896c9db0c8162ad0806e0d90a895` | `cf36bd76e3e9534b1254e7e0fe5910a462436651e73eee6809a673b7779fa9c4` |
| `FF_corrections_tt.json.gz` | `5d0cead92cc0d8760f214f68cffe57c7` | `7040cf222df2c2fc6b0ed277584e4097088380ed5e085caf5a1b996eb759bfb6` |

## Known limitations (review of 2026-10-03)

- The global ttbar data/MC factor (et 0.70, mt 1.15, tt 0.39 / 0.89) is not significant (tt: 10.7 &plusmn; 11.8
  events after subtracting the embedding) and cancels in the applied fake factor: the first ttbar
  non-closure (decay mode, binwise) absorbs 1/sf. The raw columns (`fake_factor_raw`) still carry it.
- The et/mt QCD DR&rightarrow;SR correction comes from a region where data minus MC is 0.2-0.5 % of the data.
- The et/mt ttbar fake factor smoothing leaves coherent residuals of 6-12 % (low tau pT) and 5-8 % (45-65 GeV).
- The tt fractions come from the region with both taus anti-isolated (as jvoss), with 3-5x less ttbar
  than the application region.
- `ttbarSystMCShift` and `ttbar{,_subleading}_non_closure_CorrSystMCShift` equal the nominal (MC-only
  ttbar), as in 2026-09-22.
- Summed corrected fake factor on the v5 data application region, relative to 2026-09-22: mt 0.97,
  tt 0.97 / 0.97, et 0.54 (jvoss cut mt_1 < 70 only in his et ttbar application region).

KingMaker reuses an existing friend tarball (`crown_friends_<analysis>_<friend tag>_<type>_<era>`), so
friends made with a new payload need a new `--friend-tag`; `force_repack_tarball` does not help, since
the framework tarball holds no payloads.
