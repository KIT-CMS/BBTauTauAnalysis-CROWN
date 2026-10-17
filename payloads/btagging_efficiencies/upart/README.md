# UParT b-tag MC efficiency payloads (Run 2, v7)

`<era>/btag_efficiency_<channel>.json.gz` is the MC b-tag efficiency of one Run-2 era and one
channel (scope), read by the strict consumer
`xyh::scalefactor::btagging_strict::multi_wp_event_weight` (`cpp_addons/*/btag_sf_strict.*`) through
`SM_PROFILE.btag_payload_dir = "payloads/btagging_efficiencies/upart/{era}"`. One correction,
`btag_efficiency`, with the inputs `sample_type`, `working_point` (`M`, `T`), `jet_flavor` (5, 4, 0),
`jet_eta` (|&eta;|) and `jet_pt`, clamped at the outer edges; all 14 SM sample types of the v7
lists (`rem_htautau` included) are keys in every era.

| | |
|---|---|
| Input | KingMaker production `smrun2_btag_eff_v1` (`sm_btag_efficiency_config`, the `_mc` lists of the four eras, six scopes, `--shifts None`; v7 spec P2), probe-jet columns `btag_probe_jet_{pt,eta,hadron_flavour,upart}` |
| Measurement | TauFakeFactors `feat-btag-eff-run2-v7`, commit `2bd81c2`: `scripts/run_presel_<era>.sh`, `scripts/btag_binning_scan.py`, `scripts/run_eff_<era>.sh` with `configs/btag_efficiency/<era>/`; unweighted probe-jet counts, 2026-10-17 |
| Working points | [T, M] (v7 E14) with the thresholds of the pinned BTV payload `Run2-<era>-UL-NanoAODv15/2026-06-18`: M/T = 0.1847/0.5467 (2016preVFP), 0.1898/0.5538 (2016postVFP), 0.1776/0.5755 (2017), 0.161/0.5405 (2018) |
| Pools | vjets (dyjets, wjets, electroweak_boson), top (ttbar, singletop, rem_ttbar, rem_higgs), diboson (diboson, rem_htautau), higgs_bb (hh2b2tau, vbf_hbb, rem_hbb), higgs_tautau (ggh_htautau, vbf_htautau); in ee and mm higgs_tautau is measured on vjets. 2016postVFP has no VH&rarr;&tau;&tau; sample: its `rem_htautau` key carries the diboson measurement |
| Binning | per era, pool and flavour the finest grid of the candidate edges 20/30/50/70/100/140/200/300/1000 GeV and one or two \|&eta;\| bins (edge 1.4) whose thinnest score region (fails M, M not T, passes T) holds &ge; 5 probe jets in every channel (`btag_binning_scan.py`); the grids are in the TauFakeFactors configs |
| Check | `scripts/check_btag_payload.py --era <era> --sf-check` against the era's pinned BTV payload, all 90 SF variations: 0 violations for all 24 files, no K1 unity case on the probe grid |

The binding constraint is the SF ceiling of untagged b jets: the strict consumer needs
1 - SF(M)&middot;&epsilon;(M) > 0 for every variation, and above 300 GeV the up-varied M SF of b jets is 1.154
(2016preVFP), 1.099 (2016postVFP), 1.035 (2017) and 1.032 (2018). Smallest margin
1/SF<sub>up</sub>(M) - &epsilon;(M) of b jets over all channels and sample types:

| Era | 200-300 GeV: ceiling, margin | > 300 GeV: ceiling, margin (where) |
|---|---|---|
| 2016preVFP | 0.9127, 0.045 | 0.8666, 0.011 (et, higgs_bb, \|&eta;\| < 1.4: &epsilon;(M) = 0.856) |
| 2016postVFP | 0.9519, 0.075 | 0.9100, 0.033 (mt, diboson: 0.877) |
| 2017 | 0.9936, 0.099 | 0.9660, 0.046 (et, diboson: 0.920) |
| 2018 | 0.9889, 0.090 | 0.9688, 0.074 (tt, diboson: 0.895) |

In 2016preVFP the 300 GeV b edge holds the ceiling: &epsilon;(M) of b jets peaks between 200 and
300 GeV, so a merged [200, 1000) bin would come closer to it. The 2018 files replace the
five-working-point v2 payloads (`sm2018_binned_btag_eff_v2`, 13 sample types).

| File | sha256 |
|---|---|
| `2016preVFP/btag_efficiency_et.json.gz` | `9933b5e201158d553079aa70d4b32d6d38f7d15ad516b15eab45e35ced5d3ecd` |
| `2016preVFP/btag_efficiency_mt.json.gz` | `e1c83dc98197e3429768a176fbb79683f4979b27db22e3dcc84cc81ed5159fdd` |
| `2016preVFP/btag_efficiency_tt.json.gz` | `c5fe5ff7ccb3e67e72638014084a13fc2f6f9deb0d83e3c5c832f4350d32858c` |
| `2016preVFP/btag_efficiency_ee.json.gz` | `f8d4f24b3ebfe25ea0c8132f4b625569c1c12b5f1401ab5a2a6c8f5602c576ef` |
| `2016preVFP/btag_efficiency_em.json.gz` | `9f0b67d837c5422d60f25f2538229ff21161ed184f12cb1883f34dedcd29c522` |
| `2016preVFP/btag_efficiency_mm.json.gz` | `b56193f3b221d533224601b9b9e10121dea2bd5ca60180c7660a1bee74012964` |
| `2016postVFP/btag_efficiency_et.json.gz` | `ff7438d8c7779591a7c0b499de9c327d837822235b6e09efba7eba57634cbfcb` |
| `2016postVFP/btag_efficiency_mt.json.gz` | `f7051405c5e9e37c91c168c3744d22a64f019a73fd76112f26cb6c7e81dfcf75` |
| `2016postVFP/btag_efficiency_tt.json.gz` | `3e560a0c4d2d3eb47896af8eb04efe12c4eea9f7c9ab3751b99c767c97646f97` |
| `2016postVFP/btag_efficiency_ee.json.gz` | `6cc73f1a26672156bebc154d0e3ac4657ca190986d7655612d402f67455a594a` |
| `2016postVFP/btag_efficiency_em.json.gz` | `4873c5f4066f62d89721ddf0584dfce4493fcfd778f1c91b6f1b62bedbba11e0` |
| `2016postVFP/btag_efficiency_mm.json.gz` | `4db36c2478c97848d1ef0b05e3d2ba39dc8736197b6a6353ba9c30f2e806b784` |
| `2017/btag_efficiency_et.json.gz` | `9f6000fd20c684363f916595b491abc2ec6693026ed3f78944b9fff3a15e8274` |
| `2017/btag_efficiency_mt.json.gz` | `0a66b053273a0efeda84ee187fce6ca96daa94f77d93055af3f1270efb4d32a3` |
| `2017/btag_efficiency_tt.json.gz` | `a070430b30d385d7d3f6d05a2660847a119589db59900ee2187145729b7f0df7` |
| `2017/btag_efficiency_ee.json.gz` | `00ce70034616c2f88fc068d98b1d96933688b96e73b1f06e495136cc2a386cb8` |
| `2017/btag_efficiency_em.json.gz` | `b8ce86a3143592326b69f9468ca6350a809a32d47b8c1b6fe490a7b02142672e` |
| `2017/btag_efficiency_mm.json.gz` | `dcd320ac5047287507fa4af683bbf74636586020404600660b6b1db7e42232b9` |
| `2018/btag_efficiency_et.json.gz` | `bee722dea6d1103247036ba92442c3639422994a6f3c338d736f9c6e58b3c772` |
| `2018/btag_efficiency_mt.json.gz` | `11c9f6f0a69dae30674acbe7a177aed4d058bb6ace339d22f1f8a4a8cd4a230c` |
| `2018/btag_efficiency_tt.json.gz` | `0f5b8698d14c7b0082a072780f298d08fabf0f926a1400d67009538e348b848f` |
| `2018/btag_efficiency_ee.json.gz` | `a0d251725f337abb7acc8caabef70527db193084fc2e178c23de9ad7b7e1400f` |
| `2018/btag_efficiency_em.json.gz` | `57c4e626ee0431c64453a4993ee7e145db7c241399efe5a69f4021112ccb0e79` |
| `2018/btag_efficiency_mm.json.gz` | `2d3374e06b88bf6d300ff3888cddb3911954e200356fe739bcb47c1f521f2e4e` |

KingMaker's framework-tarball hash does not cover `payloads/`: a production that should read these
files needs a fresh tag (or `force_repack_tarball`).
