# SM fake factors QCD + ttbar, 2026-11-24 (v7c)

`2016/`, `2017/` and `2018/` hold the six fake-factor payloads per payload era of the SM HH &rightarrow; bb&tau;&tau;
analysis that `sm_fake_factors.py` reads (`PAYLOADS`, friend `ff_v8` of the shift production, v8 spec 5.2, V14, V33), the
measurement "v7c": the v7b measurement of `fake-factors-2026-10-19` repeated with two changes (below). 2016preVFP and
2016postVFP both read `2016/` (`sm_fake_factors.PAYLOAD_ERAS`), one measurement of both halves.

| | |
|---|---|
| Source | `shapesmith measure -c configs/ff_smrun2_binned_v7c.yaml -s era=<2016, 2017, 2018>`, output `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/output/ff_v7c/fake_factors/<era>/`; copied byte for byte |
| Code | BBTauTauAnalysis-ShapeSmith `8c60aae` (`feat/nn-export`; `bbtautau_shapesmith.ff_measurement:build`, tables `ff_tables.py` + `ff_edges.py`), ShapeSmith core `2146f73`. The provenance inside the payload files names `ccfd384`, the parent of `8c60aae` and the checked-out commit when the measurement ran: the change of `8c60aae` (`ff_tables.FIT_OVERRIDES` of mt) was in the working tree and was committed four minutes after the last file was written |
| Written | 2016 2026-11-24 16:27–16:31 UTC, 2017 2026-11-24 16:27–16:30 UTC, 2018 2026-11-24 16:27–16:31 UTC (payload files, from their provenance) |
| Sample database | KingMaker_sample_database `49d2b7b` |
| Input n-tuples | as `fake-factors-2026-10-19`: data `smrun2_binned_v7`, MC and embedding `smrun2_binned_v7b` (`sm_<era>_binned.txt`, `sm_<era>_embedding.txt`); own skims `skims/ff_measurement_v7c/<era>` |
| Switches | as `fake-factors-2026-10-19`: `embedding: [et, mt]`, `dy_correction: njets_btag`, `tt_fraction_region: application`, `ff_processes: [QCD, ttbar]` |
| Selection, method, binning | as `fake-factors-2026-10-19` (see its README) |
| Model | QCD + ttbar; the fractions carry the processes `QCD`, `ttbar` (keys `frac_QCD`, `frac_ttbar_J`) |

## Changes against `fake-factors-2026-10-19`

1. **Data and embedding are read without repeated events** (`event_key` = run, lumi, event; the first row of an event
   is kept). Only the 2018D mutau embedding has repeated events, 244 of 147 416 rows (`repeated_events.json` next to
   the source). In the 2018 payload this changes the fractions, the ttbar fake factor and the ttbar non-closures of mt
   (the ttbar fake factor and the decay-mode non-closure by 0.07 %, the fractions by at most 0.11 %).
2. **The QCD isolation non-closure of mt is smoothed like that of et** (v8 decision V33):
   `Fit("smoothed", 0.02, binwise_left=1)` in place of the binwise fit, in every era; a correction compatible with 1 is
   set to 1. `QCD_non_closure_iso_1_correction` of `FF_corrections_mt.json.gz` changes in every era, by 14 to 24 % at
   the bin centres on average; weighted with the fake-factor prediction its mean stays at 1.00 (2018), 0.985 (2016)
   and 1.015 (2017). The statistical shift of the correction in 2018 drops from &plusmn;26 % to &plusmn;4 %.

Compared correction by correction (the JSON content without the provenance description), nothing else differs: the et
and tt payloads of every era and the mt fake factors and fractions of 2016 and 2017 hold the values of
`fake-factors-2026-10-19`. The NN score shape of the jet fakes moves by at most 0.13 (M3) and 0.16 (AB_NV1) of its
statistical uncertainty per bin (check N8 of the v8 spec, 2026-11-24).

| File | md5 | sha256 |
|---|---|---|
| `2016/fake_factors_et.json.gz` | `591380061575aba164d042482413f3d0` | `124c962af44a3284a8b29628ab79a8d8ff11cb44a7a7e42bb983529d64e5d908` |
| `2016/fake_factors_mt.json.gz` | `5c64b2ad4dd3c74965c0d082de5a119f` | `5fb701d2fde7a43f72e00c43fae5aee1417d36f698b2de2647566075c12ff1ff` |
| `2016/fake_factors_tt.json.gz` | `adf1f0f7e44fe01c706d92b3151b1110` | `192cb7b1ead91b7444a84e3f4d2e628a58fdb3d8adff21c1da18c21845798842` |
| `2016/FF_corrections_et.json.gz` | `19224577e61162a44bcaf6ec712c4ac1` | `da2876fb81abe9d2f1b8ad332db54ff2fc614cea4e9e514c818425beca15e221` |
| `2016/FF_corrections_mt.json.gz` | `8e2418bd8af05e363619b15855962dae` | `0ce6a246b111a003b327efff4e53a504d7fcd72887424c03501225a958d686eb` |
| `2016/FF_corrections_tt.json.gz` | `9137a109db23f6c74f40a15db27f429b` | `e0dd76882569a7859e9b981cb9e6b8465ff695d47b4a65949425aaa93e74a4ce` |
| `2017/fake_factors_et.json.gz` | `7eca2b80e7340faa55127025cb7f9395` | `6f9568e11b79c6aa35ac561c1f8df73b09581bdddbecd184a375881cb47c5e7c` |
| `2017/fake_factors_mt.json.gz` | `c7bf3b82d13024e4832055cc8e27ce85` | `104f2d3b99c87dedf57aa38cd3f38846b8f769cd1d330d33e660ef2208a71ecc` |
| `2017/fake_factors_tt.json.gz` | `8f1f370561d50f557b0aeebeefea6add` | `69b4e94fb8ade82893b63231690f8bbc17754466a4605e7871474d393dab895c` |
| `2017/FF_corrections_et.json.gz` | `6a14df3f3976c8afac25a88bdc3fdf88` | `06d9e8a3ab1fbd3f9d98fa5fe732faf6ef43a5ad5780c894571f9688ce6d265c` |
| `2017/FF_corrections_mt.json.gz` | `cb628669ebbcfb27606f98f1ffbc55b2` | `934c07ce6f3e54f64ccf0153a98e9fb01e47f1bce881ab6d0c35669bccf25730` |
| `2017/FF_corrections_tt.json.gz` | `cb2fb547f678aa5b4af445c688ddd445` | `e9b36620540ede8bced72ee6b5310fcc4ad46e4dfdd8269087770b5f22f2678e` |
| `2018/fake_factors_et.json.gz` | `79da29e66ab4a816fec361b65cba075e` | `21cb09ba02dd0b48d89da35e138459d83d049d9c3d017074aea01ff6617e63ac` |
| `2018/fake_factors_mt.json.gz` | `d22c6e504bea0cb3b347094c90a75102` | `a2ea7e98d780e14668bc736c1a9fd00fc14a6dc9be7b7fdab2ca39d532076f58` |
| `2018/fake_factors_tt.json.gz` | `2c5cddc6c566321a55b62cfa00fd0cca` | `092a015ca5890254c214b7993dfa034a08c38159cba3a650d83cd91627379fe4` |
| `2018/FF_corrections_et.json.gz` | `0a9f72807f82d423e8e1b5f3bc553828` | `3c43a579042386dc18340e7513cc48fe894da62311e4d27add4ae9cf039b9999` |
| `2018/FF_corrections_mt.json.gz` | `75d00e4c81c69aa3d6af27bb2b17adc2` | `96d2aa6ce00ecec05238beed4b40d7da1c394b1d92fe736c9feac452e900d2dd` |
| `2018/FF_corrections_tt.json.gz` | `110028bcfd16cb6497a8d95ecdfc3c5a` | `f4d88bd5ba538e87dfc661ce799004d60da2e153ace9b500545d990a8c5f9160` |

KingMaker packs the CROWN sources (the payloads the friend module names included) once per friend tag into the build
job tarball, so a friend with a new payload on an existing production needs a new `--friend-tag` and
`force_repack_tarball = True` under `[CROWNBuildFriend]` in the luigi cfg.
