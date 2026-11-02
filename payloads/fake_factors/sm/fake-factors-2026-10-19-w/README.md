# SM fake factors QCD + W+jets + ttbar, 2026-10-19

`2016/`, `2017/` and `2018/` hold the six fake-factor payloads per payload era of the SM HH &rightarrow; bb&tau;&tau;
analysis that `sm_fake_factors_w.py` reads (`PAYLOADS`, friend `ff_v7b_w`, v7 spec E18, 5.5, P5), measured with ShapeSmith on the v7b
production. 2016preVFP and 2016postVFP both read `2016/` (`sm_fake_factors.PAYLOAD_ERAS`), which is one measurement of
both halves (each sample from the n-tuples of its half, normalised to its luminosity).

| | |
|---|---|
| Source | `shapesmith measure -c configs/ff_smrun2_binned_v7b_w.yaml -s era=<2016, 2017, 2018>`, output `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/output/fake_factors_w/<era>/`; copied byte for byte |
| Code | ShapeSmith core `6ccdfdb` (`feat/v7-run2`), BBTauTauAnalysis-ShapeSmith `d9c8765` (`bbtautau_shapesmith.ff_measurement:build`, tables `ff_tables.py` + `ff_edges.py`) |
| Written | 2016 2026-10-19 06:22–06:25 UTC, 2017 2026-10-19 06:22–06:25 UTC, 2018 2026-10-19 06:22–06:26 UTC (payload files, from their provenance) |
| Sample database | KingMaker_sample_database `49d2b7b` |
| Input n-tuples | data `smrun2_binned_v7` (`sm_<era>_binned.txt`), MC and embedding `smrun2_binned_v7b` (`sm_<era>_binned.txt`, `sm_<era>_embedding.txt`; MET fix, POG muon trigger SF on MC, re-measured embedding tau ID/ES and tt-trigger payloads, CROWN bbtautau f69a50b) |
| Switches | `embedding: [et, mt]` (genuine &tau;<sub>h</sub> subtracted with the embedding in et and mt and with MC in tt: E33, decision of 2026-10-19 after the tt-embedding closure failed in every era; the et and mt payloads equal those measured with `[et, mt, tt]` in every value, only their provenance description differs), `dy_correction: njets_btag` (the v7b DY tables; 2016 the luminosity-weighted mean of both halves), `tt_fraction_region: application` (each leg's fractions where its fake factor is applied, v6), `ff_processes: [QCD, Wjets, ttbar]` |
| Selection | the v7 analysis selection per era (spec 6.2: trigger of the era, lt \|&eta;<sub>1</sub>\| < 2.1, 2018 HEM veto, prefiring weight) |
| Method | jvoss's TauFakeFactors method (fake factors, fractions, orthogonal DR&rightarrow;SR, compound non-closure) |
| Model | QCD + W+jets + ttbar; the fractions carry the processes `QCD`, `Wjets`, `ttbar` in et and mt (keys `frac_QCD`, `frac_Wjets`, `frac_ttbar_J`); tt has no W+jets fake factor and keeps `QCD`, `ttbar` |
| Binning | per era (`ff_edges.py`): `--suggest-binning` edges with the bin counts of the statistics review (median relative stat error per bin &le; 0.30); 2018 keeps jvoss's QCD and ttbar tables except the reviewed quantities; the mt lepton-pT non-closures start at the trigger threshold of the era; the et/mt ttbar fake factors are smoothed with 6 GeV (jvoss 26/12 GeV) |

| File | md5 | sha256 |
|---|---|---|
| `2016/fake_factors_et.json.gz` | `c1239e2e4ead113b2f1d86f771885861` | `8436a0d486d8701c7b1571599613e1d7cb7a61e39e5852e7135adb8a704448a4` |
| `2016/fake_factors_mt.json.gz` | `d2be9796a2f8f051547b22a4cfba6a5d` | `a76d54b122f54941cb962b85bce5c998956cc7286fd58cc8bb5dadac4bf8939c` |
| `2016/fake_factors_tt.json.gz` | `23e8fd411e5cefe29cfa395a0223e35a` | `13846212e729f2d0859b0a7a485148de246ae4dff8ef4c0bf797c920d5d8b36c` |
| `2016/FF_corrections_et.json.gz` | `20d8be612da875d71d20ec4a9bf0b835` | `ebec2045b8107fccc822abcc3c7e984e2f1043637c98df43e870f3fb4d8fa2d9` |
| `2016/FF_corrections_mt.json.gz` | `ccc247ce30ecd76f40eb2334098f1803` | `7f0a2a1a12b0b8df5a932d3ec5176db2d6280300045009f13c117e982e7b0ab3` |
| `2016/FF_corrections_tt.json.gz` | `09bde8499bde95aae8edc559a57a904a` | `9b6f7c45568fdffc2b7ae2ba269667fede73eab4d995dbd0793aab7edc776971` |
| `2017/fake_factors_et.json.gz` | `3c99075fe81805bb56abd4007a764a22` | `655354261ea92b9b3c054b8c6911bad405c79d74a3935900530b45add55d4a6a` |
| `2017/fake_factors_mt.json.gz` | `76ed798aa96918dba00696e7b3788794` | `56a0264a9215e722fb3fd5237434a05b2932cf554931f15ad712f4fc39abb3c4` |
| `2017/fake_factors_tt.json.gz` | `35a76a7cd162a184d0b0cd2964d4f94a` | `dbf1fa3386d706ee164d5865a26c0a2ef2378f5f7dd1a2909f095c7595060727` |
| `2017/FF_corrections_et.json.gz` | `701f4e83099473b6fbe1f8d33e398f4e` | `89de9eecc3b4e6b272e59a0b84af2b95ac1bda49c33d4a7c36c9303eb2c32906` |
| `2017/FF_corrections_mt.json.gz` | `92ee0bb3b3ed8d802485c51ed7c81a89` | `492e004a403e0720abf1216f8bc7031565548567c02d0c8d132744544a062eab` |
| `2017/FF_corrections_tt.json.gz` | `8012c80988f0b712d87f14f03d529910` | `2a0152c612a8fb394e3c55e3a3178f2e13e522cd7ebfa0c0a9b37245a72faa1e` |
| `2018/fake_factors_et.json.gz` | `c7d042b27a835183681d03068385349f` | `6e4aea3de20edc43dca37f0bc084eeb13137cdc626f161197dcbb1693adaeb2c` |
| `2018/fake_factors_mt.json.gz` | `a919e49fc19ea879228e0b7412fdaffa` | `7d0e6f1691e5b6be7f6181b3628b2f7f6411e861fc3bebf1a9b9d7971cd67099` |
| `2018/fake_factors_tt.json.gz` | `3c3e4a3a1c74f043f6b9369c15f5a1fc` | `4ac9939954e4d42556aaec8d14b3275778cc8cb9b8d59f286289804d3ad0d813` |
| `2018/FF_corrections_et.json.gz` | `7abf42d39839ee87e201120b18dd3018` | `3f39728d50e58af70849f755bc8af5b8edc8b5573aed8a3169718a61dd5ccaff` |
| `2018/FF_corrections_mt.json.gz` | `95158bd2a710bb79d7482c0947cd32dc` | `1c08b34f5b1ad49177c7ca6c64f9e9df86dfd813c2325d8b0d59248a6c02e223` |
| `2018/FF_corrections_tt.json.gz` | `cd94a7aac0ffadf7fe04db1ef10577c8` | `26daca101fd8e0e1aabb8013d946bf79ee1b6497e22faefdc786301c94964e16` |

## Notes

- Measurement record, plots and validation next to the ShapeSmith output of each era (`measurement_<ch>.json`,
  `plots/<ch>/`, `validation.json` of `scripts/ff_validation.py`). Summary (German):
  `/ceph/sdaigler/v7_results/ff_v7b_summary.md`.
- tt from MC (2026-10-19, E33): the tt-embedding closure failed in every era, so tt takes its genuine taus from MC as
  in v6 and the measurement subtracts them as MC (`embedding: [et, mt]`). These payloads replace the first v7b ones
  (`embedding: [et, mt, tt]`, commit 9115775): every et and mt value is unchanged (only the provenance description
  of the files differs); in tt the ttbar data/MC factor moves (2016 0.59/0.67 -> 1.19/1.28, 2017 0.35/0.26 ->
  0.95/0.68, 2018 0.83/1.74 -> 1.18/2.37 for tau 1/tau 2) and with it the raw ttbar fake factor, while the fractions
  change by <= 0.02, the QCD fake factors by <= 2 % and the mean corrected fake factor in the application region by
  -1.3 to +2.2 %; the DR closure of tt is the same (2/3/5 failures with p < 0.01 in 2016/2017/2018).
- Mean corrected fake factor on the data application region (per b-tag 1 / >= 2 and n_jets 2 / >= 3): et 0.079-0.085,
  mt 0.079-0.085, tt 0.155-0.243 in every era. With W+jets against without: 0.98-1.003 (W share of the prediction 10-13 %
  with <= 2 jets, 2-3 % with >= 3); the QCD and ttbar corrections of both variants are identical, only the fractions
  differ, and tt is identical in both variants. 2018 against the v6 payload on the same events: 0.988-1.015.
- DR closure of the fully corrected fake factor (every table variable): QCD and W+jets close in every era except the
  decay mode of the tt QCD (2016 subleading, 2018 leading tau, up to 20 %); the ttbar MC closes within 3-5 % except in
  the decay mode of mt and tt (DM 1 about -5 %, DM 11 +15 to +29 %), which the mass non-closures after the
  decay-mode one bend again (measuring the decay mode last moves it into the mass, +-7 %).
- The ttbar data/MC factor (et 0.16-0.69, mt 0.81-2.03, tt 0.68-2.37) cancels in the corrected fake factor (the
  first, binwise non-closure absorbs it); it shows only in `fake_factor_raw`.
- The QCD DR->SR correction of et and mt has 2 bins and is dominated by the subtracted MC (median stat error 0.3-0.7
  per bin); it is set to 1 where compatible with 1, everywhere but 2018 et (0.49-0.96). The W+jets DR->SR correction
  (W MC, 2 bins in mt_1, 3 in 2016 mt) is compatible with 1 in every era and set to 1 with its statistical band.
- Binning: the rule "2016/2017 at most the 2018 count" was applied against the round-1 2018 counts, before the 2018
  reductions, so three 2016 counts lie above the final 2018 ones (et QCD_non_closure_iso_1 5+1 vs 2+1, mt Wjets_DR_SR
  3 vs 2, mt QCD_fake_factors 6 vs 5); their statistics are within the rule (2016 median relative stat error
  0.16-0.24), so they are kept.
- 2016: one measurement of both halves; a measurement per half with the same tables differs in the mean corrected
  fake factor by -3 to +3 % (et, mt) and -11 to +4 % (tt), and the 2016 payload closes on each half like on both.

KingMaker packs the CROWN sources (payloads included) once per production tag into the build job tarball, so a
friend with a new payload on an existing production needs a new `--friend-tag` **and** `force_repack_tarball = True`
under `[CROWNBuildFriend]` in the luigi cfg.
