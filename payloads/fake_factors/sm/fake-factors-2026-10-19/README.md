# SM fake factors QCD + ttbar, 2026-10-19

`2016/`, `2017/` and `2018/` hold the six fake-factor payloads per payload era of the SM HH &rightarrow; bb&tau;&tau;
analysis that `sm_fake_factors.py` reads (`PAYLOADS`, friend `ff_v7b`, v7 spec E18, 5.5, P5), measured with ShapeSmith on the v7b
production. 2016preVFP and 2016postVFP both read `2016/` (`sm_fake_factors.PAYLOAD_ERAS`), which is one measurement of
both halves (each sample from the n-tuples of its half, normalised to its luminosity).

| | |
|---|---|
| Source | `shapesmith measure -c configs/ff_smrun2_binned_v7b.yaml -s era=<2016, 2017, 2018>`, output `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/output/fake_factors/<era>/`; copied byte for byte |
| Code | ShapeSmith core `6ccdfdb` (`feat/v7-run2`), BBTauTauAnalysis-ShapeSmith `d9c8765` (`bbtautau_shapesmith.ff_measurement:build`, tables `ff_tables.py` + `ff_edges.py`) |
| Written | 2016 2026-10-19 06:22–06:25 UTC, 2017 2026-10-19 06:22–06:24 UTC, 2018 2026-10-19 06:17–06:20 UTC (payload files, from their provenance) |
| Sample database | KingMaker_sample_database `49d2b7b` |
| Input n-tuples | data `smrun2_binned_v7` (`sm_<era>_binned.txt`), MC and embedding `smrun2_binned_v7b` (`sm_<era>_binned.txt`, `sm_<era>_embedding.txt`; MET fix, POG muon trigger SF on MC, re-measured embedding tau ID/ES and tt-trigger payloads, CROWN bbtautau f69a50b) |
| Switches | `embedding: [et, mt]` (genuine &tau;<sub>h</sub> subtracted with the embedding in et and mt and with MC in tt: E33, decision of 2026-10-19 after the tt-embedding closure failed in every era; the et and mt payloads equal those measured with `[et, mt, tt]` in every value, only their provenance description differs), `dy_correction: njets_btag` (the v7b DY tables; 2016 the luminosity-weighted mean of both halves), `tt_fraction_region: application` (each leg's fractions where its fake factor is applied, v6), `ff_processes: [QCD, ttbar]` |
| Selection | the v7 analysis selection per era (spec 6.2: trigger of the era, lt \|&eta;<sub>1</sub>\| < 2.1, 2018 HEM veto, prefiring weight) |
| Method | jvoss's TauFakeFactors method (fake factors, fractions, orthogonal DR&rightarrow;SR, compound non-closure) |
| Model | QCD + ttbar; the fractions carry the processes `QCD`, `ttbar` (keys `frac_QCD`, `frac_ttbar_J`) |
| Binning | per era (`ff_edges.py`): `--suggest-binning` edges with the bin counts of the statistics review (median relative stat error per bin &le; 0.30); 2018 keeps jvoss's QCD and ttbar tables except the reviewed quantities; the mt lepton-pT non-closures start at the trigger threshold of the era; the et/mt ttbar fake factors are smoothed with 6 GeV (jvoss 26/12 GeV) |

| File | md5 | sha256 |
|---|---|---|
| `2016/fake_factors_et.json.gz` | `d7da5db59d651242e7b4b2d4e1b2f279` | `d1bd7b39bb1ec988bcb11a08cb8c5e912340ecd934808d0a469c5248d5b7bdb3` |
| `2016/fake_factors_mt.json.gz` | `59192008d84e55b58ddfc68d10a491c3` | `8aa9de3750fa5fcbc90a0ee4469b09238f7cfa97309c94cded4065473e6fb67b` |
| `2016/fake_factors_tt.json.gz` | `e9fbc244eecb1ebc2f29f33b858f3ab9` | `bf50015b63c077b215c02d9638b4a20c1767c874b1d1e2ffaa21f4d941ba3e27` |
| `2016/FF_corrections_et.json.gz` | `c6980bd9c2c7ddade7fa486f9fa1ebde` | `45a449f00c3e2aa7db2ed6e7f5305597940c9f63076e5096aa1f0a3167ae8929` |
| `2016/FF_corrections_mt.json.gz` | `fa11dcbdb3e629d06adf49a8595a5bdc` | `93c6b12a58fb259a954d1787f73d13de6db63b8f5b9949c3429852de7449dcd4` |
| `2016/FF_corrections_tt.json.gz` | `1dfc325957ab1e6845080fe6cb9d49c7` | `07d192ce8a65a329c97a22b6271bd64dae0310552bb2a69e8727462ef5f20c94` |
| `2017/fake_factors_et.json.gz` | `7a264086a7212efcdb9643cf33b8d3d0` | `8b9125e389bc35c57b4e812b11a2b7e216aee2ec0c45ee92e8d1b1da637eeedc` |
| `2017/fake_factors_mt.json.gz` | `4c8603894d53e83fe4e38693865aff28` | `2b11d477b89cc128ea638ceb77487367d024a30e0e41d34e0fd69bced11a52c6` |
| `2017/fake_factors_tt.json.gz` | `e6a9aafc7068bb8e7326e0f3744268d6` | `2857bd2994893d27e6e51b244dca52eeaf418ce6667c2cebb83974eb275a7d6d` |
| `2017/FF_corrections_et.json.gz` | `5d6e1659a4eabebf26da964b71639073` | `22636d8da859ad2a8d8d1c697be94419e3b5825d2004f84ec8b97430981756ce` |
| `2017/FF_corrections_mt.json.gz` | `0b658159c2b6078905865af01a54a302` | `2f933899015178ca79ca5e368b0940af9a5d9eb828a198f56c00d7d5c2c97d51` |
| `2017/FF_corrections_tt.json.gz` | `87b14c7f1ec91bec32d4a61912b24d5b` | `8a6277ba3c95661541f161efceacf0e762abfa816db32b0875e568dcd8d20ff3` |
| `2018/fake_factors_et.json.gz` | `bc944e5a38bfa43790975d75005c6fb1` | `cc1b43ca49fcf518ad367134b9df4da248687204c5d9520f28c8260043f8f8e2` |
| `2018/fake_factors_mt.json.gz` | `d70038a00f301721e35da01cf39b9edb` | `096cc22584412d3a006c92c70819485484544b55b985ee135bc551cdcb966a30` |
| `2018/fake_factors_tt.json.gz` | `b874d892abf88196a97eff1191c4045d` | `ce51ca39cf1c2f63e3359d0b5f47dd0173c9fb4969d9b0a18fa53c7777bdd11b` |
| `2018/FF_corrections_et.json.gz` | `9da22099621bfc623d77bba159e526da` | `b7d13d381923f06aa9ad57e71e8ce226eead08ebf5eddbd07a2488b81d0c7b69` |
| `2018/FF_corrections_mt.json.gz` | `1464b8c99e3bff351172854f87714485` | `68c1a2f4bb5b2ee00eeda07c694151d4b697ead0489e67541310dc62c108e2fc` |
| `2018/FF_corrections_tt.json.gz` | `be121fb8d35cea4bf5c8b53b05a571d2` | `27933376932b15923d32604c3796cdbc73687cf17e074fb294e8b92ca86c85b3` |

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
