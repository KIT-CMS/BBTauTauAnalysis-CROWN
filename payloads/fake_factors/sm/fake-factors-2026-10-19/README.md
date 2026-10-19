# SM fake factors QCD + ttbar, 2026-10-19

`2016/`, `2017/` and `2018/` hold the six fake-factor payloads per payload era of the SM HH &rightarrow; bb&tau;&tau;
analysis that `sm_fake_factors.py` reads (`PAYLOADS`, friend `ff_v7b`, v7 spec E18, 5.5, P5), measured with ShapeSmith on the v7b
production. 2016preVFP and 2016postVFP both read `2016/` (`sm_fake_factors.PAYLOAD_ERAS`), which is one measurement of
both halves (each sample from the n-tuples of its half, normalised to its luminosity).

| | |
|---|---|
| Source | `shapesmith measure -c configs/ff_smrun2_binned_v7b.yaml -s era=<2016, 2017, 2018>`, output `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/output/fake_factors/<era>/`; copied byte for byte |
| Code | ShapeSmith core `b6e35b4` (`feat/v7-run2`), BBTauTauAnalysis-ShapeSmith `5201a1c` (`bbtautau_shapesmith.ff_measurement:build`, tables `ff_tables.py` + `ff_edges.py`) |
| Written | 2016 2026-10-19 04:49 UTC, 2017 2026-10-19 04:49 UTC, 2018 2026-10-19 04:49 UTC |
| Sample database | KingMaker_sample_database `49d2b7b` |
| Input n-tuples | data `smrun2_binned_v7` (`sm_<era>_binned.txt`), MC and embedding `smrun2_binned_v7b` (`sm_<era>_binned.txt`, `sm_<era>_embedding.txt`; MET fix, POG muon trigger SF on MC, re-measured embedding tau ID/ES and tt-trigger payloads, CROWN bbtautau f69a50b) |
| Switches | `embedding: [et, mt, tt]` (genuine &tau;<sub>h</sub> subtracted with the embedding, E33), `dy_correction: njets_btag` (the v7b DY tables; 2016 the luminosity-weighted mean of both halves), `tt_fraction_region: application` (each leg's fractions where its fake factor is applied, v6), `ff_processes: [QCD, ttbar]` |
| Selection | the v7 analysis selection per era (spec 6.2: trigger of the era, lt \|&eta;<sub>1</sub>\| < 2.1, 2018 HEM veto, prefiring weight) |
| Method | jvoss's TauFakeFactors method (fake factors, fractions, orthogonal DR&rightarrow;SR, compound non-closure) |
| Model | QCD + ttbar; the fractions carry the processes `QCD`, `ttbar` (keys `frac_QCD`, `frac_ttbar_J`) |
| Binning | per era (`ff_edges.py`): `--suggest-binning` edges with the bin counts of the statistics review (median relative stat error per bin &le; 0.30); 2018 keeps jvoss's QCD and ttbar tables except the reviewed quantities; the mt lepton-pT non-closures start at the trigger threshold of the era; the et/mt ttbar fake factors are smoothed with 6 GeV (jvoss 26/12 GeV) |

| File | md5 | sha256 |
|---|---|---|
| `2016/fake_factors_et.json.gz` | `d438556533da817af943c35ce84f5e6d` | `8ae1ace8e3eb372534a7a47846c2b78fe476e518871b443b929a7cfd00b3d4b8` |
| `2016/fake_factors_mt.json.gz` | `9ebdd433186a7f0302ebd029887eff1c` | `703f27e9393cde9150817ecad7f245d5e8db00c1809e3f2c25130d63e01145d7` |
| `2016/fake_factors_tt.json.gz` | `7387419ba93da6cffa5e6a7a12730ffe` | `db9bcbaf4994354d051a41d74e64668484760adec3603df14cd8b48be814ed7b` |
| `2016/FF_corrections_et.json.gz` | `f9ae071caaf4f6f6c8a5543bbb23a207` | `980646c1fbd12900c290e8710c4763ae8de4db756da6d0f2f10f8c7c4eff02fb` |
| `2016/FF_corrections_mt.json.gz` | `80b7ba9bad10b71587f108059742a8c3` | `4b5a47f2aa1035e2189794baf13b8dc63c64120e808ce85188633cc2cb4473ec` |
| `2016/FF_corrections_tt.json.gz` | `3747a3c1c125446e7ed04140d0a72c3f` | `95c8d8b7a66480a4fe4d3b739645f7934920d009851cf3938b3b603bfb530826` |
| `2017/fake_factors_et.json.gz` | `b289b6e5faf932c05c46557ebc7202c1` | `fff70b48e2d1cc93bcfb22d01ebc567f02f109ee9dc2d83ea1d8d3b6682565ec` |
| `2017/fake_factors_mt.json.gz` | `f54255665f2f7d2c64daf2a862da16e3` | `c16dbfdc6f71ab9ba6e933b5413a347e95b9633e42ded647a395c853d928daa8` |
| `2017/fake_factors_tt.json.gz` | `d7e566bb7ada64760526dfb9eab8cef2` | `b6d105ebf7bc0f01e45893d57972f84fc5c3d8386b0f13a51a3691a14ce4119f` |
| `2017/FF_corrections_et.json.gz` | `9aa85ffb2c06266f75346a29373a76db` | `5d222219ce2b97a0e69e473080ca89d53ce19b57f05012a4af9d95a72656aab4` |
| `2017/FF_corrections_mt.json.gz` | `099524bb1e6a85474037d8bfb48dc3c7` | `5f588e025c0a33f1f56d593550665af5675ed5be6130f42be32c30e5b08b36d9` |
| `2017/FF_corrections_tt.json.gz` | `99430921eec79e15dd6e75609273bfb9` | `da300a4df5b16cd1d04be774c631c7b10f892d3570aef51a78939a659a7b6da7` |
| `2018/fake_factors_et.json.gz` | `a7f2a4a91e5089f6a6cb87891825c2c0` | `8d5ee6153b858521311a24c6d3def951eb414ecf7aad72cb1bed154011a3b1e1` |
| `2018/fake_factors_mt.json.gz` | `eee37c699f5bf538ab44fda9db109fab` | `924b10c9a67f52349bfe50e6a35b395d0d99d042c808347b59d934c221ae1ef2` |
| `2018/fake_factors_tt.json.gz` | `23ae4cbd5525033d94fdb7749342a957` | `ba54367bad24210553b01dbb7105c959902fd1f620f5fcaef12c3a2ed5b11691` |
| `2018/FF_corrections_et.json.gz` | `13d2563c75d291d59345c18ef1e87201` | `2fedae768a761cbf7c4e56d7564d7ef39008b3df88ed0013e32766f15ec6fc55` |
| `2018/FF_corrections_mt.json.gz` | `cbef6e9d3c41cdba5b2e5012030e8e45` | `8cd5a9f94299126e731efe98dc4ee5551f0ac1e283530413bcc6ad0b7638e08f` |
| `2018/FF_corrections_tt.json.gz` | `ae4298e4ca45b3d620fbf4919216f4ab` | `67f4a01e1d1d59db7105091953ea4881fa8d9c6495fde890f4f34b021ee106c9` |

## Notes

- Measurement record, plots and validation next to the ShapeSmith output of each era (`measurement_<ch>.json`,
  `plots/<ch>/`, `validation.json` of `scripts/ff_validation.py`). Summary (German):
  `/ceph/sdaigler/v7_results/ff_v7b_summary.md`.
- Mean corrected fake factor on the data application region (per b-tag 1 / >= 2 and n_jets 2 / >= 3): et 0.079-0.085,
  mt 0.079-0.085, tt 0.15-0.24 in every era. With W+jets against without: 0.98-1.003 (W share of the prediction 10-13 %
  with <= 2 jets, 2-3 % with >= 3); the QCD and ttbar corrections of both variants are identical, only the fractions
  differ. 2018 against the v6 payload on the same events: 0.988-1.014.
- DR closure of the fully corrected fake factor (every table variable): QCD and W+jets close in every era except the
  decay mode of the tt QCD (2016 subleading, 2018 leading tau, up to 20 %); the ttbar MC closes within 3-5 % except in
  the decay mode of mt and tt (DM 1 about -5 %, DM 11 +15 to +29 %), which the mass non-closures after the
  decay-mode one bend again (measuring the decay mode last moves it into the mass, +-7 %).
- The ttbar data/MC factor (et 0.16-0.69, mt 0.81-2.03, tt 0.26-1.74) cancels in the corrected fake factor (the
  first, binwise non-closure absorbs it); it shows only in `fake_factor_raw`.
- The QCD DR->SR correction of et and mt has 2 bins and is dominated by the subtracted MC (median stat error 0.3-0.7
  per bin); it is set to 1 where compatible with 1, everywhere but 2018 et (0.49-0.96). The W+jets DR->SR correction
  (W MC, 2 bins in mt_1, 3 in 2016 mt) is compatible with 1 in every era and set to 1 with its statistical band.
- 2016: one measurement of both halves; a measurement per half with the same tables differs in the mean corrected
  fake factor by -3 to +3 % (et, mt) and -10 to +4 % (tt), and the 2016 payload closes on each half like on both.

KingMaker packs the CROWN sources (payloads included) once per production tag into the build job tarball, so a
friend with a new payload on an existing production needs a new `--friend-tag` **and** `force_repack_tarball = True`
under `[CROWNBuildFriend]` in the luigi cfg.
