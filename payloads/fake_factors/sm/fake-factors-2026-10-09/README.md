# SM 2018 fake factors, 2026-10-09

`2018/` holds the six fake-factor payloads of the SM HH &rightarrow; bb&tau;&tau; analysis that
`sm_fake_factors.py` reads (`SM_PAYLOAD_DIRS`), measured with ShapeSmith on the v6 production. They replace
`fake-factors-2026-10-03` (v5). One mixed payload: the genuine &tau;<sub>h</sub> of the measurement regions are
subtracted with the embedding in et and mt and with MC in tt, as the analysis models them.

| | |
|---|---|
| Source | `shapesmith measure -c configs/ff_sm2018_binned_v6.yaml`, output `output/ff_sm2018_binned_v6/fake_factors/2018/`; copied byte for byte |
| Code | ShapeSmith core `31e5bc4` (`feat/v6`), BBTauTauAnalysis-ShapeSmith `9955a03` (`bbtautau_shapesmith.ff_measurement:build`), run configuration sha256 `583febd0...04ff8312c9` |
| Sample database | KingMaker_sample_database `33c257b` |
| Input n-tuples | `sm2018_binned_v6` (data/MC: `sm_2018_binned.txt`, 77 nicks; embedding: `sm_2018_embedding.txt`) |
| Switches | `embedding: [et, mt]`, `dy_correction: njets_btag` (the v6 DY table), `tt_fraction_region: application` (the tt fractions of each leg where its fake factor is applied) |
| Method | jvoss's TauFakeFactors method (QCD + ttbar, fractions, orthogonal DR&rightarrow;SR, compound non-closure), binning and fits from `ff_tables.py` |
| Model | QCD + ttbar; the fractions carry the processes `QCD` and `ttbar` (keys `frac_QCD`, `frac_ttbar_J`) |
| Shifts | unchanged keys: 17 shift pairs per leg, equal to ShapeSmith `constants.FF_SHIFTS_LT/TT` |

| File | md5 | sha256 |
|---|---|---|
| `fake_factors_et.json.gz` | `92eaf07dd1c90a935459d22ceb772b5c` | `f7f8aff50452d4d888e2f26d4f45ef99fd35c9777364bf2c305ff0869f5dc0bf` |
| `fake_factors_mt.json.gz` | `82a242532bb64c5123ab4335dd75fda7` | `e85b910816d83602fd0df9a6ed5d757eaa6cf479d1602cd3858ef80c1bcc4704` |
| `fake_factors_tt.json.gz` | `98d8ffae660dc1919f24d956b6b06ba3` | `74f6fd97c6aa0b9f077fe12e6d63de18d674391a9b674579e7e4d092280c33cc` |
| `FF_corrections_et.json.gz` | `951aeb3034e88fa5d72409b450c21488` | `e980348d8653053849001974325f55b26a95adb525359290ec047d7ebbafe73e` |
| `FF_corrections_mt.json.gz` | `545d89f18c77f0ce41700494fbf88fc4` | `6a96d80c50719012045e2e8483278785de0e0697a6c20c30d48d24d2432297d7` |
| `FF_corrections_tt.json.gz` | `65ee644a82b16f14891d54f77ebc1368` | `8a66965ab1db872f50120e81ea8da85ad6a6c6a930025f35f3115099b33aac0f` |

## Notes

- Cross-check without embedding (`ff_sm2018_binned_v6_noemb.yaml`): the corrected fake factor differs by at most
  0.6 % in et and mt; tt is the same measurement.
- The global ttbar data/MC factor (et 0.61, mt 1.27, tt 1.18 / 2.25) cancels in the applied fake factor: the first
  ttbar non-closure (decay mode, binwise) absorbs 1/sf. The raw columns (`fake_factor_raw`) still carry it.
- `ttbarSystMCShift` and `ttbar{,_subleading}_non_closure_CorrSystMCShift` equal the nominal (MC-only ttbar).
- The embedding still uses the preliminary tau ID/ES payload (`payloads/tau_embedding/README.md`, now binned in the
  decay mode only).

KingMaker packs the CROWN sources (payloads included) once per production tag into the build job tarball, so a
friend with a new payload on an existing production needs a new `--friend-tag` **and**
`--CROWNBuildFriend-force-repack-tarball`.
