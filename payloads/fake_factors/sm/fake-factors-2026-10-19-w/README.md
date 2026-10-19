# SM fake factors QCD + W+jets + ttbar, 2026-10-19

`2016/`, `2017/` and `2018/` hold the six fake-factor payloads per payload era of the SM HH &rightarrow; bb&tau;&tau;
analysis that `sm_fake_factors_w.py` reads (`PAYLOADS`, friend `ff_v7b_w`, v7 spec E18, 5.5, P5), measured with ShapeSmith on the v7b
production. 2016preVFP and 2016postVFP both read `2016/` (`sm_fake_factors.PAYLOAD_ERAS`), which is one measurement of
both halves (each sample from the n-tuples of its half, normalised to its luminosity).

| | |
|---|---|
| Source | `shapesmith measure -c configs/ff_smrun2_binned_v7b_w.yaml -s era=<2016, 2017, 2018>`, output `/ceph/sdaigler/shapesmith/smrun2_binned_v7b/output/fake_factors_w/<era>/`; copied byte for byte |
| Code | ShapeSmith core `b6e35b4` (`feat/v7-run2`), BBTauTauAnalysis-ShapeSmith `5201a1c` (`bbtautau_shapesmith.ff_measurement:build`, tables `ff_tables.py` + `ff_edges.py`) |
| Written | 2016 2026-10-19 04:49 UTC, 2017 2026-10-19 04:49 UTC, 2018 2026-10-19 04:53 UTC |
| Sample database | KingMaker_sample_database `49d2b7b` |
| Input n-tuples | data `smrun2_binned_v7` (`sm_<era>_binned.txt`), MC and embedding `smrun2_binned_v7b` (`sm_<era>_binned.txt`, `sm_<era>_embedding.txt`; MET fix, POG muon trigger SF on MC, re-measured embedding tau ID/ES and tt-trigger payloads, CROWN bbtautau f69a50b) |
| Switches | `embedding: [et, mt, tt]` (genuine &tau;<sub>h</sub> subtracted with the embedding, E33), `dy_correction: njets_btag` (the v7b DY tables; 2016 the luminosity-weighted mean of both halves), `tt_fraction_region: application` (each leg's fractions where its fake factor is applied, v6), `ff_processes: [QCD, Wjets, ttbar]` |
| Selection | the v7 analysis selection per era (spec 6.2: trigger of the era, lt \|&eta;<sub>1</sub>\| < 2.1, 2018 HEM veto, prefiring weight) |
| Method | jvoss's TauFakeFactors method (fake factors, fractions, orthogonal DR&rightarrow;SR, compound non-closure) |
| Model | QCD + W+jets + ttbar; the fractions carry the processes `QCD`, `Wjets`, `ttbar` in et and mt (keys `frac_QCD`, `frac_Wjets`, `frac_ttbar_J`); tt has no W+jets fake factor and keeps `QCD`, `ttbar` |
| Binning | per era (`ff_edges.py`): `--suggest-binning` edges with the bin counts of the statistics review (median relative stat error per bin &le; 0.30); 2018 keeps jvoss's QCD and ttbar tables except the reviewed quantities; the mt lepton-pT non-closures start at the trigger threshold of the era; the et/mt ttbar fake factors are smoothed with 6 GeV (jvoss 26/12 GeV) |

| File | md5 | sha256 |
|---|---|---|
| `2016/fake_factors_et.json.gz` | `24ed3ba308f491d93274af63eccf59df` | `2dd9949fca2fdd84cb2ced6b7f31a156e44789e8ee60b38f8ba4fa4352cb8f4c` |
| `2016/fake_factors_mt.json.gz` | `cfa6af2978edb3f90a6e6a80e3f84b98` | `734d55b4969b2d39a95de45d8a2ad5a9d395878d35f1b174feb7c4680ed72c44` |
| `2016/fake_factors_tt.json.gz` | `5c928c5dfde52345ee71733a509ddcb9` | `32f93b5fcca83cf8a249d2634f331aa2579d42df4238f1b819c4319ca7f42407` |
| `2016/FF_corrections_et.json.gz` | `ef3f9359d6686f90b547328e15258122` | `91be0666df92d93252adf480fafd7265aeffe851edeff331fd528b69d9c3c192` |
| `2016/FF_corrections_mt.json.gz` | `55d933ffff57a92cd1979b0145838c7f` | `d0ec0f8925cbe77caebaddde0faf43b72ea0d8788ac90bd5b8d310fb6187365b` |
| `2016/FF_corrections_tt.json.gz` | `eef033ff97f042b7e861ecc3399bcb8b` | `4d677e7f74375382b00017c71a326dff55f0e47aef0b7190a0034bc291802adc` |
| `2017/fake_factors_et.json.gz` | `a4771f78bc9a60a5fe27f11eed5a5a0c` | `cb2e546594aa0515ed6381bb9565a0d3088395c26aed25da4e2062ce64c13db7` |
| `2017/fake_factors_mt.json.gz` | `4a9c21473d9801eaee69650343841b7e` | `ed4125517699dfc7cc3090ae2ad6de9118d0fd473fb70f7aa11c8365268ade50` |
| `2017/fake_factors_tt.json.gz` | `926aa0a6c0e04b88b7bf8ea404ca17b2` | `30f7010f511c0b5a38ff1221207eeb5543eb19b2308327583228e3c0881464c3` |
| `2017/FF_corrections_et.json.gz` | `cac7a67a0e64fa7da6dd11ae22cdea42` | `386c62cda2065622715b15455953b61f3b79febd71ee938afd3f0009c2678d12` |
| `2017/FF_corrections_mt.json.gz` | `1970be34d73abda8419a6cae886aaf5e` | `6c63dd9f7136c23272c29cfa53d91dcdf9e886b3e8292ed62a45874354346beb` |
| `2017/FF_corrections_tt.json.gz` | `e2452812ad07643053924f320c40f821` | `aaff2c2721e8d6f3f8064bc48ea402d5aa5aef55dc0bc164d89877ae5d172338` |
| `2018/fake_factors_et.json.gz` | `47910aa4abb060fb03b58eec83b682b3` | `69250caed26d7e30290d87fe6264bae1c76a1e257066c748ad54fa44cf27f78b` |
| `2018/fake_factors_mt.json.gz` | `11fc8fa86d23898f1cf9228252a508cb` | `1c01b4866bcb71bc6f4183cf96bbdf5db9bc640569b8cdda154eded36ee500b3` |
| `2018/fake_factors_tt.json.gz` | `80f0673dcbdc3d67ba853aeeba175592` | `ccd5af2363323c02af612d15f25b65a7ea981d18038dde0c79d66b3e57a40d55` |
| `2018/FF_corrections_et.json.gz` | `b47a268363575d3df3a9f03ffe0fe444` | `70be0a9221bc93c023dcecfb17cd51a15755aa287e7554983da93f4e9ca328a4` |
| `2018/FF_corrections_mt.json.gz` | `5111140eb3e216042bef77cdd9809eff` | `3645f1eb6c1cff01d52e9bb9b9938dcf77cea2707184f29cf2bc41c4c3e00a30` |
| `2018/FF_corrections_tt.json.gz` | `87d313da93e906ec74d453f9fb48b9db` | `bffb78e4f4611b7b3da154b3e194052d3a55fc64b734d811b9d712fda2675225` |

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
