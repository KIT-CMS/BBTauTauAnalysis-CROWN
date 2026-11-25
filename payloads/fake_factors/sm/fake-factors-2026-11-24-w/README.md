# SM fake factors QCD + W+jets + ttbar, 2026-11-24 (v7c)

`2016/`, `2017/` and `2018/` hold the six fake-factor payloads per payload era of the SM HH &rightarrow; bb&tau;&tau;
analysis that `sm_fake_factors_w.py` reads (`PAYLOADS`, friend `ff_v8_w` of the shift production, v8 spec 5.2, V14, V33), the
measurement "v7c": the v7b measurement of `fake-factors-2026-10-19-w` repeated with two changes (below). 2016preVFP and
2016postVFP both read `2016/` (`sm_fake_factors.PAYLOAD_ERAS`), one measurement of both halves.

| | |
|---|---|
| Source | `shapesmith measure -c configs/ff_smrun2_binned_v7c_w.yaml -s era=<2016, 2017, 2018>`, output `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/output/ff_v7c/fake_factors_w/<era>/`; copied byte for byte |
| Code | BBTauTauAnalysis-ShapeSmith `8c60aae` (`feat/nn-export`; `bbtautau_shapesmith.ff_measurement:build`, tables `ff_tables.py` + `ff_edges.py`), ShapeSmith core `2146f73`. The provenance inside the payload files names `ccfd384`, the parent of `8c60aae` and the checked-out commit when the measurement ran: the change of `8c60aae` (`ff_tables.FIT_OVERRIDES` of mt) was in the working tree and was committed four minutes after the last file was written |
| Written | 2016 2026-11-24 16:27–16:31 UTC, 2017 2026-11-24 16:27–16:31 UTC, 2018 2026-11-24 16:27–16:32 UTC (payload files, from their provenance) |
| Sample database | KingMaker_sample_database `49d2b7b` |
| Input n-tuples | as `fake-factors-2026-10-19-w`: data `smrun2_binned_v7`, MC and embedding `smrun2_binned_v7b` (`sm_<era>_binned.txt`, `sm_<era>_embedding.txt`); own skims `skims/ff_measurement_v7c/<era>` |
| Switches | as `fake-factors-2026-10-19-w`: `embedding: [et, mt]`, `dy_correction: njets_btag`, `tt_fraction_region: application`, `ff_processes: [QCD, Wjets, ttbar]` |
| Selection, method, binning | as `fake-factors-2026-10-19-w` (see its README) |
| Model | QCD + W+jets + ttbar; the fractions carry the processes `QCD`, `Wjets`, `ttbar` in et and mt (keys `frac_QCD`, `frac_Wjets`, `frac_ttbar_J`); tt has no W+jets fake factor and keeps `QCD`, `ttbar` |

## Changes against `fake-factors-2026-10-19-w`

1. **Data and embedding are read without repeated events** (`event_key` = run, lumi, event; the first row of an event
   is kept). Only the 2018D mutau embedding has repeated events, 244 of 147 416 rows (`repeated_events.json` next to
   the source). In the 2018 payload this changes the fractions, the ttbar and W+jets fake factors and the ttbar and
   W+jets non-closures of mt (the W+jets fake factor by at most 0.5 %, its pt_1 non-closure by at most 0.3 % and its
   met non-closure by at most 1.6 %, 0.14 % on average).
2. **The QCD isolation non-closure of mt is smoothed like that of et** (v8 decision V33):
   `Fit("smoothed", 0.02, binwise_left=1)` in place of the binwise fit, in every era; a correction compatible with 1 is
   set to 1. `QCD_non_closure_iso_1_correction` of `FF_corrections_mt.json.gz` changes in every era, by 14 to 24 % at
   the bin centres on average; weighted with the fake-factor prediction its mean stays at 1.00 (2018), 0.985 (2016)
   and 1.015 (2017). The statistical shift of the correction in 2018 drops from &plusmn;26 % to &plusmn;4 %.

Compared correction by correction (the JSON content without the provenance description), nothing else differs: the et
and tt payloads of every era and the mt fake factors and fractions of 2016 and 2017 hold the values of
`fake-factors-2026-10-19-w`. The NN score shape of the jet fakes moves by at most 0.13 (M3) and 0.16 (AB_NV1) of its
statistical uncertainty per bin (check N8 of the v8 spec, 2026-11-24).

| File | md5 | sha256 |
|---|---|---|
| `2016/fake_factors_et.json.gz` | `6b5388c29b40c90217dbf022cc0b61f5` | `78dd345fac55ec27f38a5dfad639fc22b8bd348cde4dac040d01e0d75216fd9f` |
| `2016/fake_factors_mt.json.gz` | `933d16f149e928b86b4cbf29650a0b20` | `dc7535fd56bf2ef6e0c44bdc6b24e2b0fd7aa91613f3595bd0beb963a3dfca96` |
| `2016/fake_factors_tt.json.gz` | `7f5e8a96ee0b80780528df10052cf33a` | `0ef05a671b53dce14b27abecc6e8fb3f062c8fd2d84fc7f63b6c6e6a0068625c` |
| `2016/FF_corrections_et.json.gz` | `16faecc3f4bf59fbb7c4caa896637119` | `10759e430c6c59c66646923b45477fbe22d9c305c75453f7f1ba1dc6f2b6a89a` |
| `2016/FF_corrections_mt.json.gz` | `c13e9268032074a3e64a4c3b64cbb324` | `0ee40ac39d1e3e5e78cf3670a82d2c9ec8761564e4a645fd399920134d8f817d` |
| `2016/FF_corrections_tt.json.gz` | `f6185be143b0a78a92aa203ec38c32f3` | `99bdc138cd81c27528d54fcb5f13609f14abbf72ae2331487bce527fe27cb04a` |
| `2017/fake_factors_et.json.gz` | `73b52164b637f8e3fd5f71d1ea43466e` | `a02318647671558782c9ded055cddbef8ad73530549d559c2aabc683a9340cb0` |
| `2017/fake_factors_mt.json.gz` | `7a8390184acaa96a5782f8bb72aa2f71` | `feec681e28d327eb7d46dd89b0ffccaf90fd4a002a4c96dda02e8893ec6580b1` |
| `2017/fake_factors_tt.json.gz` | `516d757d60b346d6c9c494526531b761` | `c1281a6d7f95d54c7cd602cd257d337821446bca691dfb7a4ba4c581dc14dcf5` |
| `2017/FF_corrections_et.json.gz` | `b9d00c81f5941abd4bfe44edf62b8e9a` | `044ebd41e07d9448adc4edbab3f0fcd5c5c49675b23cf79e6c9b0274cb18edc6` |
| `2017/FF_corrections_mt.json.gz` | `5c30fcce80bbf8140df71930c8d82741` | `6c97cb4b379d7d535e3879349eb507d3a1d560eb8a0b6076e0c1c05504392271` |
| `2017/FF_corrections_tt.json.gz` | `1737f1902547de02c0b27b6cb2652a6c` | `838dea232dc5732a3956621de24d074ae459ca0781567c53f2f491b19df187f4` |
| `2018/fake_factors_et.json.gz` | `0ed550099c756cf219775689abea28b8` | `ba9692d5f62b88c3cb9a6c5988ba24ca6609a195dbba10c29de0fc3ab926e6a4` |
| `2018/fake_factors_mt.json.gz` | `1cc40649033f6f60534a1634bf11d541` | `0e0b31b6dfecba60b54793115d77b7d81b6117a6ed5703dc761e7b12742fb0c8` |
| `2018/fake_factors_tt.json.gz` | `00262c3f5e3db684818c13dad0af1671` | `36485a8b481de968fd4bacc9238c79cb410dd334340fb57096336e0452c9b0b1` |
| `2018/FF_corrections_et.json.gz` | `f1df51ed3c185260a6edcbc44638c702` | `dda83c180b48425bcf76b0ec5fd6597454818e500c90ff3646d696dfaf218168` |
| `2018/FF_corrections_mt.json.gz` | `7462d614b3586d2dcbefedd3f46b30c6` | `647743f7114f57c56b77bb46aa962fc370e678ab58f845bc0b5d47ab31b32abc` |
| `2018/FF_corrections_tt.json.gz` | `77a4ff71a502eaa3a5822a36d05055a3` | `18c88ec158aa9d42dd5f3c4c5dba66dc9b867c085fcd63a98f4375104bda3461` |

KingMaker packs the CROWN sources (the payloads the friend module names included) once per friend tag into the build
job tarball, so a friend with a new payload on an existing production needs a new `--friend-tag` and
`force_repack_tarball = True` under `[CROWNBuildFriend]` in the luigi cfg.
