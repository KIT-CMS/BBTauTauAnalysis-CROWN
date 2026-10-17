# XYHBBTauTauAnalysis-CROWN

This repository has been forked from [KIT-CMS/TauAnalysis-CROWN](https://github.com/KIT-CMS/TauAnalysis-CROWN).

The repository holding the CROWN configuration of the NMSSM X &rightarrow; YH &rightarrow; bb&tau;&tau;
analysis and of the SM (non-resonant) HH &rightarrow; bb&tau;&tau; analysis.

Every top-level configuration is a thin wrapper: it picks an `AnalysisProfile` (`analysis_profiles.py`,
a frozen dataclass) and calls `common_config.build_config(PROFILE, era, sample, scopes, shifts, ...)`,
which holds the whole configuration body. The profile carries the axes the analyses differ on --
bb/&tau;&tau; truth-mother PDG IDs, the LHE-scale-weight sample lists, `use_run2_v15_inputs`, the
b-jet |&eta;| override, the b-tag algorithm and efficiency-payload directory, and the
efficiency-ntuple switches (`mc_only`, `enable_btag_sf`, `enable_probe_jet_collection`) -- so a new
variant is one more profile instance plus one more thin module, not a fork of `common_config.py`.
A config module may also declare `AVAILABLE_ERAS` and/or `AVAILABLE_SAMPLES`; `generate.py` and
`generate_friends.py` reject an era or sample outside them before `build_config` runs, but the
`Configuration` itself is always built against `constants.LEGACY_AVAILABLE_SAMPLES`.

## Available Configurations

* `nmssm_config.py` (`NMSSM_PROFILE`) - The main configuration to be used for the
  X &rightarrow; YH &rightarrow; bb&tau;&tau; search. All eras, legacy (v9 / Run-3) inputs.
* `sm_config.py` (`SM_PROFILE`) - The SM HH &rightarrow; bb&tau;&tau; production configuration:
  Run-2 NanoAOD-v15 inputs, UParTAK4 b-tagging, `AVAILABLE_ERAS = ERAS_RUN2` (2016preVFP, 2016postVFP,
  2017, 2018), tau embedding in et, mt and tt (see [Tau embedding](#tau-embedding); built where the
  era's embedding tau payload exists, 2018 so far). Sample lists per era in `sample_list/` (see its
  `README.md`).
* `sm_btag_efficiency_config.py` (`SM_BTAG_EFFICIENCY_PROFILE`, a `dataclasses.replace(SM_PROFILE,
  ...)`) - The same selection, MC only and without b-tag scale factors, plus the probe-jet collection
  the UParT b-tag MC efficiency is measured from downstream in `TauFakeFactors`. Being
  payload-independent, it never depends on the payload it exists to produce.
* `sm_tau_id_measurement_config.py` (`SM_TAU_ID_MEASUREMENT_PROFILE`, `tau_id_measurement.py`) - The
  n-tuples of the tau-ID SF and energy scale measurement for embedding, mt and mm, in every Run-2 era,
  with the columns of the tt-trigger tau-leg measurement (see [Tau-ID measurement](#tau-id-measurement)).

## Available Friend Configurations

The friend entries are thin wrappers around the shared `FriendTreeConfiguration` bodies in
`friend_common.py`: `build_friend_config` (FastMTT, resolved kinematic fit) and
`build_fake_factor_friend` (fake factors).

* `nmssm_fastmtt.py` / `sm_fastmtt.py` - Produce FastMTT friends (`m/pt/eta/phi_fastmtt`); the SM
  module re-exports the NMSSM builder and only adds `AVAILABLE_ERAS = ERAS_RUN2`.
* `nmssm_kinfit_resolved.py` / `nmssm_kinfit_boosted.py` - HH/YH kinematic fit over the NMSSM Y-mass
  hypotheses, resolved and boosted.
* `sm_kinfit_resolved.py` - Fixed 125/125 GeV HH kinematic fit, Run-2 eras; outputs
  `kinfit_convergence`, `kinfit_chi2`, `kinfit_prob`, `kinfit_mHH`.
* `fake_factors_friend_config.py` / `sm_fake_factors.py` / `sm_fake_factors_w.py` - Fake-factor
  friends, NMSSM (Run 3, `NMSSM_PAYLOAD_DIRS`) and SM (the Run-2 eras with a payload,
  `SM_PAYLOAD_DIRS`): `sm_fake_factors` sums QCD + ttbar (friend `ff_v7`), `sm_fake_factors_w`
  QCD + W + ttbar (friend `ff_v7_w`, v7 spec E18, P5), each from its own `PAYLOADS` table with the
  shared 2016 mapping, and each rejects a payload of the other variant (`PROCESSES`). See
  [Fake-factor friends](#fake-factor-friends).
* `xyh_classifier_friend_config.py` - Produce PNN classifier friends for the NMSSM analysis.

### Fake-factor friends

Each friend reads the two payload files of its scope, `fake_factors_<ch>.json.gz` and
`FF_corrections_<ch>.json.gz` (TauFakeFactors layout; `FF_corrections_<ch>_default.json.gz` where the
corrections file carries the name of its corrections configuration), at configuration time with `ff_payloads.py`
(standard library only), and takes the correction inputs and the shifts from them, so a new payload
needs no code change. The processes of a leg are the process categories of its fractions, QCD +
ttbar or QCD + W + ttbar (v7 spec E18, C15; `ff_payloads.FRACTION_PROCESS_SETS`), so both fake-factor
models of v7 run on the same code. The C++ (`fakefactors::xyh::FakeFactor` in
`cpp_addons/src/fakefactors.cxx`) sums over them in the order QCD, W, ttbar:
`sum_p frac_p * max(FF_p * corrections_p, 0)`, with the DR->SR correction and the closure of QCD, the
DR->SR correction (where the measurement provides it) and the closure of W, and the closure of ttbar;
the raw fake factor is the same sum without the corrections. It computes in float as the two-process
function before, so a QCD + ttbar payload gives the former friend bit for bit
(`tests/test_cpp_runtime.py::test_fake_factor_sum_over_the_payload_processes` compares it with a frozen
copy, `tests/cpp/reference/fakefactors_two_process.hxx`, on the SM 2018 and two NMSSM payloads, nominal
and with every shift, built with `-ffp-contract=off` because the friend is built with ROOT's
`-march=nocona`, which has no fused multiply-add; a W payload derived from the SM one, `tests/fixtures/make_wjets_fake_factor_payload.py`,
checks the three-process sum, which every leg has to give in float, in payload order, bit for bit).

| Scope | Legs (correction suffix) | Outputs |
|---|---|---|
| et, mt | `lt` (none) | `fake_factor_raw`, `fake_factor` |
| tt | `leading` (none), `subleading` (`_subleading`) | `fake_factor_{1,2}_raw`, `fake_factor_{1,2}` |

The payload conventions are checked when the configuration is built (a `ValueError` names the file and
the correction): every correction has a `syst` category with a default (the nominal) at the top, the
inputs are `[process] + real ... + syst` (`process` only in the fractions, whose process categories
are the same everywhere and QCD + ttbar or QCD + Wjets + ttbar), every process has its
`{p}{s}_fake_factors` and `{p}{s}_compound_correction` (and QCD its `QCD{s}_DR_SR_correction`), every input is a quantity of `quantities/output.py` (`njets`/`nbtag` are aliases of
`n_jets`/`n_bjets`), every syst key is `nominal`, `<correction>nominal` or ends in Up/Down/_up/_down
with its partner, and the global non-closure keys are in every member of a compound closure.

Shifts: every Up/Down key of the leg's corrections except `SystBandHigh`/`SystBandLow` (the same
smoothing band as `SystBandAsym`) and the per-variable non-closure keys (only the global, coarse ones
are kept). The shift name is the payload key with `_up`/`_down` written `Up`/`Down`, e.g.
`process_fractionsfrac_QCDUp` sets `ff_fraction_variation` to `process_fractionsfrac_QCD_up`; fake-factor
and fraction shifts act on both outputs of the leg, DR->SR and closure shifts only on the corrected
one. That is 17 pairs per leg for the SM 2018 payload and 14 for the NMSSM ones; W adds its fake
factor, DR->SR and closure keys (`Wjets...`) and the `frac_Wjets` fraction keys. The NMSSM shift names
therefore follow the payload keys (2025: `QCDStatShift...`, `process_fractionsfrac_QCD...`; 2022-2024:
`fracTTbarUnc`), which the hardwired lists before got wrong, evaluating those shifts as nominal.
Friends keep `--shifts all|none`.

The build needs a quantities map that lists every input column of the scope. A missing nominal
column fails at configuration time; a shifted variant is used where the map has it, otherwise the
input stays nominal under that shift (info log only).

Payloads: the NMSSM Run-3 ones stay at `payloads/fake_factors/<version>/<era>/` (2022 and 2023:
`fake-factors-2026-06-10`, 2024 and 2025: `fake-factors-2026-09-26`, which has no 2024 tt payload), new ones go to
`payloads/fake_factors/<analysis>/<version>/<era>/`. The SM payload is
`payloads/fake_factors/sm/fake-factors-2026-10-09/2018/`, measured with ShapeSmith on `sm2018_binned_v6`
with embedding in et and mt (see its README; the v5 payload `fake-factors-2026-10-03` stays for reference);
jvoss's `fake-factors-2026-09-22` stays as the base of the edited test payloads. A new payload goes into a new
dated directory, and only the entry in `SM_PAYLOAD_DIRS` / `NMSSM_PAYLOAD_DIRS` changes. Friend tarballs and
outputs are keyed by production and friend tag only, and KingMaker packs the CROWN sources once per tag, so
producing friends with a new payload on an existing production needs a new `--friend-tag` and
`--CROWNBuildFriend-force-repack-tarball`.

The SM payloads are keyed by payload era (`sm_fake_factors.PAYLOAD_ERAS`): 2016preVFP and 2016postVFP share
one 2016 payload, measured on both halves together. `PAYLOADS` maps a payload era to its directory, and
`SM_PAYLOAD_DIRS` / `AVAILABLE_ERAS` hold the eras whose payload era has one (2018 so far); a new 2016
payload is one entry, `"2016": ".../<version>/2016"`.

## Building

Per-era wrapper scripts in `build_scripts/`, run from the CROWN repo root. All arguments are
positional and optional: `$1` samples, `$2` scopes, `$3` debug, `$4` steps
(`build` | `run_binary` | `all`), `$5` config (default `nmssm_config`).

```bash
bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh
bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh hh2b2tau et,mt,tt false build sm_config
bash analysis_configurations/bbtautau/build_scripts/test_build_2016preVFP.sh data,ttbar,dyjets mt false all sm_config
```

There is one script per era: `test_build_{2016preVFP,2016postVFP,2017,2018}.sh` for Run 2 (test files:
NanoAOD v15 SingleMuon, `TTTo2L2Nu` and `DYJetsToLL_LHEFilterPtZ-0To50` of the era) and one per Run-3 era.

Each script configures and compiles in `<CROWN>/build_<era>[_<config>]/` -- the `_<config>` suffix is
appended whenever `$5` is not `nmssm_config`, so builds for one era do not clobber each other -- and
installs binaries `<config>_<sample>_<era>` into its `bin/`. `run_binary` runs each binary on a
hard-coded remote NanoAOD test file and needs a valid grid proxy.

The scripts pass `-DSHIFTS=none`. `-DSHIFTS` selects which of the *registered* CROWN shifts get
compiled into an executable, matched by **case-insensitive substring containment** against the shift
names (`Configuration._is_valid_shift`): `jes` selects every `jesUnc*` shift, `btag` every b-tag one.
`all` and `none` are specials.

## Run-2 NanoAOD-v15 inputs

Both SM profiles set `use_run2_v15_inputs = True`, for all four Run-2 eras (2016preVFP, 2016postVFP,
2017, 2018) on one code path, which is why nothing on it is named after an era; genuinely era-specific
choices are era-keyed parameters. The tau-ID measurement builds in every era; the embedding of
`sm_config` needs the embedding tau payload of its era, which exists for 2018 only so far. Relative to
the legacy Run-2 path NMSSM keeps using:

- **Jet ID** -- v15 ships no usable `Jet_jetId`, so the AK4-PUPPI ID is evaluated from the composition
  branches by `producers/jets.py`'s `JetIDFromCorrectionlib` (the same producer 2024/2025 use), reading
  `payloads/jetid/Run2-<era>-UL-NanoAODv15/jetid.json.gz`. JME does not publish that file for Run 2 UL;
  it is generated by the `jetid-payloads` repository for every era (see `payloads/jetid/README.md`;
  2016 with the UL16 PUPPI cuts of JetID13TeVUL, `neMultiplicity` &ge; 1 at 2.7 < \|&eta;\| &le; 3.0).
- **JEC and JER** -- the v15 AK4-PUPPI JERC payload of each era (`JME/Run2-<era>-UL-NanoAODv15/2026-06-05`)
  with its tags: JES `Summer20UL16APVNanoV15_V1`, `Summer20UL16NanoV15_V1`, `Summer20UL17NanoV15_V1`,
  `Summer20UL18NanoV15_V1` (data and MC); JER `Summer20UL16APV_JRV5`, `Summer20UL16_JRV5`,
  `Summer19UL17_JRV4`, `Summer19UL18_JRV3`. No jet veto maps (not mandatory in Run 2); the
  &eta;-&phi; occupancy of jets and b jets is validated in data/MC instead.
- **MET filters** -- the UL recommendation: 2016 without, 2017 and 2018 with `Flag_ecalBadCalibFilter`.
- **Electron scale and smearing** -- v15 electrons come without scale and smearing (v9 had them
  applied) but carry the Run-3-style inputs, so this path uses the Run-3 `ElectronPtCorrectionMC`
  (`SmearAndSyst`) and `ElectronPtCorrectionData` (`Scale`) producers against the era's pinned
  `EGM/Run2-<era>-UL-NanoAODv15` payload; embedding keeps its own electron energy scale.
- **MET covariance** -- v15 drops `MET_covXX/XY/YY`, so the covariance comes from `PuppiMET` through
  `met.met_global(overrides)`, checked by `met.MetCovPuppiChecked` (`xyh::met_covariance::Checked`,
  `cpp_addons/*/met_covariance.*`): a matrix that is not finite, not positive definite or has a
  variance above sumEt<sup>2</sup> (the physical bound: no object resolution exceeds its
  p<sub>T</sub>) is replaced by the PF MET covariance (`PFMET_covXX/XY/YY`, the matrix the Run-2
  v9/v12 configurations used for all events), and if that fails too by a diagonal matrix at the bound
  (no MET constraint). `metcov_source` (0 PuppiMET, 1 PF MET, 2 diagonal) is written in every scope.
  The v15 PuppiMET covariance of 2016 is broken in about 1 % of the events (NaN, non-positive
  determinants, values up to 1e14 GeV<sup>2</sup>; NanoAOD skims: DY 2016preVFP 1.3 %, data
  2016preVFP 1.1 %, ttbar 2016postVFP 0.7 %, embedding 2016preVFP 0.4 %; selected events of the test
  runs: ttbar 2016preVFP 0.3-1.5 % per channel, 2016postVFP 0.3-1.0 %, DY 2016preVFP mm 0.9 %), which
  made `m_fastmtt` NaN or noise; 2017 and 2018 pass the check (the large 2017 values are below the bound and agree with the
  PF MET ones). The handling is to be confirmed by the user; `metcov_source` allows a veto instead.
- **MET** -- the re-calibrated jets are propagated to the PuppiMET in data, MC and embedding alike
  (`propagate_jets_to_met` true for every sample type; v7 spec E28, C19), so that the JEC (and in MC
  the JER smearing) act on the MET as on the jets; CROWN shifts the jets of data and MC equally (v6:
  -4/-2/-1 %). The embedded events get the data calibration of the jets of the recorded event
  (`JetEnergyCorrectionData`, same JES tag), which is the condition for propagating there. The
  propagation is the CROWN difference method (`physicsobject::PropagateToMET`): the change of every
  jet with re-calibrated p<sub>T</sub> > 15 GeV (`t1jet_min_pt`; the Run-2 producer applies no
  &#124;&eta;&#124; or EM-fraction cut) is subtracted from the MET. The low-p<sub>T</sub> jets of
  `CorrT1METJet` are not in it, which matters only for jets that cross 15 GeV with the new JEC (JME
  recommends recomputing type-1 MET from all jets; the difference method is the CROWN standard and the
  KIT precedent, TauAnalysis-CROWN `propagateJets`, which also applies the p<sub>T</sub> cut only).
  This deviates from v7 spec C19, which lists &#124;&eta;&#124; < 5.2 and an EM fraction < 0.9 as
  well (`t1jet_max_abs_eta`, `t1jet_max_em_ef` are set but only the Run-3 `met::Type1Correction`
  reads them); to be confirmed by the user or added to the core propagation. The Run-2 recoil
  correction of DY and W counts the jets of the HTT recipe (p<sub>T</sub> > 30 GeV, |&eta;| < 4.7,
  jet ID, &Delta;R > 0.5 to both pair objects, `met.MetScopesWithRecoilJets`; +1 for W) instead of
  all NanoAOD jets, and reads the legacy PuppiMET files of CROWN,
  `data/recoil_corrections/Type1_PuppiMET_<year>.root` (the 2016 file for both halves). Their
  `ZPtBinsH` had the edges 0-5 instead of the 0/10/20/30/50/1000 GeV its labels name, so every event
  with a generator Z p<sub>T</sub> above 4 GeV got the `PtGt50` correction; CROWN 27262f4 fixed the
  edges, and the CROWN pin must contain it (`tests/test_sm_main_config.py` checks the edges per era).
- **b-tagging** -- UParTAK4. `btag_payloads.py` reads the pinned per-era BTV payload
  (`BTV/Run2-<era>-UL-NanoAODv15/2026-06-18/btagging.json.gz`) with `btv_upart_payload`,
  `load_upart_wps` (working points) and `discover_upart_variations` (variation keys); MC efficiencies
  are committed per era and channel at
  `payloads/btagging_efficiencies/upart/<era>/btag_efficiency_<channel>.json.gz`
  (`SM_PROFILE.btag_payload_dir = "payloads/btagging_efficiencies/upart/{era}"`; all four Run-2 eras,
  measured on `smrun2_btag_eff_v1`, provenance and sha256 in
  [`payloads/btagging_efficiencies/upart/README.md`](payloads/btagging_efficiencies/upart/README.md)). The
  multi-working-point event weight comes from the strict consumer
  `xyh::scalefactor::btagging_strict::multi_wp_event_weight` (`cpp_addons/*/btag_sf_strict.*`) with
  the working points of the profile, `btag_sf_working_points = ("T", "M")` (v7 spec E14, C14; parameter
  `bjet_sf_working_points`, checked against the payload by `btag_payloads.check_working_points`). It
  takes their thresholds from the SF payload's own `UParTAK4_wp_values` correction and throws instead
  of clamping -- on thresholds that are not strictly decreasing, an efficiency that is non-finite /
  &le; 0 / > 1, a non-monotonic efficiency pair, |&eta;| outside [0, 2.4), an unknown jet flavour, or
  any correctionlib failure. The one exception is the BTV rule for a negative numerator of an
  intermediate factor, SF(M)&epsilon;(M) - SF(T)&epsilon;(T) < 0 ("set these intermediate factors to
  unity", K1): the factor is 1 and the event's count of such jets is written next to the weight
  (`btag_unity_jets_upart[_<variation>]`). The weight columns are the nominal `btag_weight_upart` and the
  eight variations of the fixed-WP nuisances,
  `btag_weight_upart_{up,down}_{bc,light}_{correlated,uncorrelated}`: b/c jets (`UParTAK4_comb`) or light
  jets (`UParTAK4_light`) varied by the payload key `<direction>_<correlation>`, the other group central.
  With [T, M] the L/XT/XXT anomalies of the payload (SF(L) 1.058, SF(XT) > SF(T), SF&middot;&epsilon; > 1) do not
  enter; they matter again for a later return to more working points. The variation columns can still
  break the strict check outside 2018: above 300 GeV the M SF of b jets is 1.037 in 2016preVFP, its
  `up_uncorrelated` value 1.154 (2016postVFP 1.099, 2017 1.035, 2018 1.032), so an efficiency
  &epsilon;(M) above 0.867 (2016postVFP 0.910) gives an untagged b jet a negative factor and the job
  throws. A 2016preVFP test run with the 2018 efficiencies as stand-in (&epsilon;(M) = 0.889 at 463 GeV)
  stopped there. The measured payloads pass `check_btag_payload.py --sf-check` in every era; the
  smallest margin is 0.011 in 2016preVFP (&epsilon;(M) = 0.856 above 300 GeV, held by the 300 GeV b
  edge). The `UParTAK4_comb` SFs of b/c jets are calibrated from
  30 GeV (`load_upart_comb_min_pt`, parameter `bjet_sf_bc_min_pt`), and the payload's p<sub>T</sub>
  flow would give the jets below the SF of the highest bin; following the BTV convention, they take
  the SF at 30 GeV with twice its deviation for the variations, and the efficiency at their own
  p<sub>T</sub>.
- **Probe jets** -- with `enable_probe_jet_collection`, `jets.BtagProbeJetVectors` masks the jets with
  `CombineMasks(base_bjets_mask, jet_overlap_veto_mask)` and exports
  `btag_probe_jet_{pt,eta,hadron_flavour,upart}` via `xyh::btag_probe::masked_vector` -- the columns
  the downstream efficiency measurement reads.
- **Diagnostic columns** -- `npv_good` (`PV_npvsGood`) and `rho` (`Rho_fixedGridRhoFastjetAll`) in
  every sample, and in MC the hadron flavour of the two leading jets (`jet_hadronFlavour_1/2`) and
  of the b-pair jets (`bpair_hadronFlavour_1/2`), in all six scopes.
- **Prefiring** (profile field `prefiring_weight_columns`; v7 spec E11, C11) -- MC of every era carries
  `prefiring_wgt` (NanoAOD `L1PreFiringWeight_Nom`; 2018: the muon prefiring, about 0.5 %) and the
  plain columns `L1PreFiringWeight_Up`, `L1PreFiringWeight_Dn`, from which the nominal-only datacards
  take `CMS_prefiring` as lnN (E34); data and embedding carry none. The SM productions have no
  prefiring shifts; the tau-ID measurement adds `CMS_ecal_prefiring_<year>` for 2016-2018. NMSSM keeps
  the weight on every sample of 2016 and 2017 with its shifts.
- **HEM 15/16** (profile field `hem_veto_flag`; v7 spec E29, C20) -- in 2018 only (the era is the
  guard, the failure exists there only), `event.HemVetoFlag` (`xyh::vetoes::hem_veto`,
  `cpp_addons/*/hem_veto.*`) writes `hem_veto`, true if a loose jet (re-calibrated p<sub>T</sub> >
  15 GeV, TightLeptonVeto ID, before the lepton cleaning) lies in -3.0 < &eta; < -1.3,
  -1.57 < &phi; < -0.87 and the event belongs to the affected period: data and embedding from run
  319077 on, MC with the probability 0.647719, the luminosity fraction of these runs (38.75 of
  59.82 fb<sup>-1</sup> of the Legacy 2018 golden JSON, recorded luminosity per lumisection from the UL
  pileup JSON; `common_config.HEM_AFFECTED_LUMI_FRACTION_2018`), decided per event from run,
  luminosity block and event number (a hash, so that equal event numbers of different generator jobs
  fall independently). ShapeSmith vetoes the flagged events (JME recipe for UL); the `CMS_HEM_2018` jet
  energy scale shift is gone. Under the jet shifts of the tau-ID measurement the flag follows the
  shifted jets. NMSSM keeps the HEM shift and has no flag. Two details differ from v7 spec C20 and
  are to be confirmed by the user: MC is selected by a hash of run, luminosity block and event number
  (the spec names the event number), and the shifted jets of P1 give shifted `hem_veto` columns (the
  spec names nominal jets). Measured flag rates: 2018 ttbar MC about 5 %, 2018D embedding 3.8 %.
- **Electron SFs** (profile field `electron_sf_supercluster_eta`; v7 spec K7, C22) -- the EGM
  reconstruction and ID SFs are binned in the supercluster &eta;, so `EleID_SF_ScEta` evaluates them at
  `sc_eta_1/2` = `Electron_eta + Electron_deltaEtaSC` of the pair electrons
  (`xyh::electron::supercluster_eta`; columns in et, em, ee, `sc_eta_2` in ee) instead of `eta_1/2`;
  this changes electrons near the edges 1.444 and 1.566 only. The KIT electron SFs keep the electron
  &eta;.

- **Triggers** (`tau_triggersetup.py`, profile field `kit_single_lepton_triggers`) -- the
  single-lepton flags are the analysis triggers the KIT (Tau Embedding group) trigger SFs describe,
  matched to their trigger object within &Delta;R < 0.1 like the KIT tag and probe the SFs come from
  (TauAnalysis-CROWN `tauembedding_tagandprobe.py`, `max_deltaR_triggermatch: 0.1`; MUO recommends
  0.1 as well; the tau legs keep 0.4):

  | Era | Muon (mt, mm, em) | Electron (et, ee) | KIT SF (`data/embedding/{muon,electron}_<era>UL.json.gz`) |
  |---|---|---|---|
  | 2016preVFP, 2016postVFP | IsoMu22 &#124;&#124; IsoTkMu22 &#124;&#124; IsoMu22_eta2p1 &#124;&#124; IsoTkMu22_eta2p1 (bit 1 IsoMu, 3 IsoTkMu), p<sub>T</sub> > 24 GeV | Ele25_eta2p1_WPTight, p<sub>T</sub> > 27 GeV, &#124;&eta;&#124; < 2.1 | `Trg_pt_eta_bins` (the OR) &rarr; `trg_wgt_single_mu22`; `Trg25_Iso_pt_eta_bins` &rarr; `trg_wgt_single_ele25` |
  | 2017 | IsoMu27, p<sub>T</sub> > 29 GeV (IsoMu24 is prescaled) | Ele32 (> 34 GeV) and Ele35 (> 37 GeV), no emulation | `Trg_IsoMu27_pt_eta_bins`; `Trg32_Iso`, `Trg35_Iso` &rarr; `trg_wgt_single_ele32/35` |
  | 2018 | IsoMu24, p<sub>T</sub> > 26 GeV | Ele32, p<sub>T</sub> > 34 GeV | `Trg_IsoMu24_pt_eta_bins`; `Trg32_Iso_pt_eta_bins` |

  The flags keep the trigger's &#124;&eta;&#124; (2.4 for muons); the &#124;&eta;&#124; < 2.1 of the
  triggering lepton is cut downstream. The SFs are evaluated at every p<sub>T</sub> and isolation
  (`scalefactors.KitSingleMuonTriggerSF` in mt, mm and em, `ETGenerateSingleElectronTriggerSF_MC` in et
  and ee); the flags select downstream. The KIT muon trigger SF replaces the POG one because its
  denominator (medium ID, iso < 0.15) is the SM selection, as in TauAnalysis v9, jvoss's v15
  production and smhtt_ul; MUO asks to "stick to centrally provided SFs" whenever possible, so the
  choice is to be presented to MUO before the approval. One MC bin is defective: in
  `muon_2016preVFPUL` `Trg_pt_eta_bins` holds 2.756 for type `mc` at p<sub>T</sub> &ge; 200 GeV and
  &#124;&eta;&#124; < 0.9 (impossible, SF &times; &epsilon;<sub>MC</sub> > 1; 0.933 at 100-200 GeV,
  0.885 for embedding, 0.926 in 2016postVFP). `KitSingleMuonTriggerSF`
  (`xyh::scalefactor::kit_muon_trigger`) therefore evaluates the muons above 199.9 GeV with
  &#124;&eta;&#124; < 0.9 at 199.9 GeV in 2016preVFP (`tau_triggersetup.KIT_MUON_TRIGGER_SF_MC_MAX_PT`,
  entries `mc_trigger_sf_max_pt[_max_abs_eta]`); every other era and bin is evaluated as it is. The
  precedents evaluate the payload as it is, so this is to be confirmed by the user.
  `tests/test_run2_eras.py` checks every KIT trigger SF where its flag fires (0.5-1.5, on the first
  3 GeV of the turn-on 0-1.5); the 2017 Ele32 SF of embedding fails it (1.8-3.2 at 34-36 GeV and
  1.57 < &#124;&eta;&#124; < 2.1, 0.47 at 42-50 GeV above &#124;&eta;&#124; 2.1) and is reported, not
  changed (strict xfail). The KIT files carry no uncertainties:
  `CMS_eff_m_trigger_<era>` and `CMS_eff_e_trigger_<era>` scale the SFs by 1.02 / 0.98, the TauAnalysis
  convention. The EGM `Electron-HLT-SF` exists only in the Run-3 payloads, so every Run-2
  configuration, NMSSM included, evaluates the KIT electron SF. Di-tau (tt): 2016
  DoubleMediumIsoPFTau35 and DoubleMediumCombinedIsoPFTau35 (filter bits 1 Medium(Comb)Iso and 8 Dz of
  the 2016 scheme; CombinedIso exists in the data from 2016H on, downstream the MC takes the Iso path
  only), 2017 the three and 2018 the four paths of TauTrigger (bit 6), each with the POG di-tau SF
  (WP Medium) per leg, `trg_wgt<flag without "trg">_leg<n>`. The SM has no e-&tau; and &mu;-&tau;
  cross triggers (`lepton_tau_cross_triggers`). The HLT branches and the `TrigObj_filterBits` doc
  strings of the eras' files are test fixtures (`tests/fixtures/make_hlt_fixtures.py`), against which
  `tests/test_triggers.py` checks every path and bit.
- **Hadronic taus** -- the TAU POG v15 payload `TAU/Run2-<era>-UL-NanoAODv15/2025-11-27` (no newer
  snapshot as of 2026-10-16; re-pin when one appears). Some of its corrections are placeholders,
  byte-identical copies of 2018 (`tests/test_run2_eras.py` checks the list): `DeepTau2018v2p5VSe` in
  2016preVFP and 2016postVFP, `DeepTau2018v2p5VSmu` in 2016preVFP, 2016postVFP and 2017, and the
  e &rarr; &tau; energy scale (`tau_energy_scale`, genmatch 1) in 2016preVFP and 2016postVFP. Their
  uncertainties are correlated with 2018 downstream. The vsJet SF calls the core
  `experimental::Id_vsJet` with the vsMu working point `tau_ides_sf_vsmu_wp` (core 14f82c1 and
  later, so every pin with 27262f4), a C++ string literal because CROWN drops empty parameters: `""`
  for every pinned payload, whose `DeepTau2018v2p5VSjet` takes pt, dm, genmatch, wp, wp_VSe, syst,
  flag (`tests/test_run2_v15_configuration.py` checks the call against the core header and the
  payload inputs per era).

The SM profiles also set `kit_sf_lepton_ids`: they keep the lepton IDs the lepton SFs of the Tau
Embedding group (KIT, used by the embedding) are measured for, as the legacy SM analysis did -- MVA
WP90 electrons with the isolation pre-cuts 0.25 (loose) and 0.4 (tight), medium-ID muons, the POG SFs
`wp90iso`, `NUM_MediumID_DEN_TrackerMuons` and `NUM_TightRelIso_DEN_MediumID`, and no low-p<sub>T</sub>
muon ID SF column -- in place of the NMSSM object defaults (MVA WP80 electrons without isolation
pre-cut, tight-ID muons). The electron reconstruction SF is written in et, em and ee for both
analyses (`xyh::scalefactor::electron_reco`), and the muon p<sub>T</sub> calibration applies in Run 3
only. The KIT lepton SF files of MC are those of the era, `data/embedding/{electron,muon}_<era>UL.json.gz`
(`mc_electron_sf_file`, `mc_muon_sf_file`).

The light dilepton control channels ee, em and mm (`sm_light_controls`) exist in every Run-2 v15 era:
15 GeV lepton legs, no lepton SFs on data, em without the electron trigger, and ee with the
single-electron trigger SF of et.

All `/cvmfs/cms-griddata.cern.ch` pins are dated CAT-metadata snapshots, never the rolling `latest`
symlink; after changing one, rerun the tests.

## Systematic shifts

Every shift is defined in the `variations/` package, one module per object (`taus`, `jec`,
`bjet_tagging`, `electrons`, `muons`, `met`, `pileup_prefiring`, `triggers`, `theory`), and named after
its datacard nuisance (`CMS_scale_t_DeepTau2018v2p5_DM0_pt20to40_genTau_2018Up`,
`CMS_eff_m_trigger_2018Down`, `CMS_scale_j_AbsoluteUp`, ...). `common_config.build_config` registers
them for NMSSM and SM alike. The SM specifics use the same helpers:

- the single-lepton trigger SFs of the Tau Embedding group (et and ee; mt, mm and em with
  `kit_single_lepton_triggers`) have the shifts `CMS_eff_e_trigger_<era>` and `CMS_eff_m_trigger_<era>`,
  which scale them by 1.02 / 0.98 (`add_single_{electron,muon}_trigger_extrapolation_shifts`);
- the strict UParTAK4 b-tag weight writes its variations as weight columns, so the SM has no b-tag
  shifts; likewise the prefiring weight its Up/Dn columns (no prefiring shifts in the SM productions,
  the tau-ID measurement has them), and the 2018 HEM flag replaces the `CMS_HEM_2018` shift;
- the embedding and the tau-ID measurement add their own shifts (sections below).

`tests/test_shift_parameters.py` checks that every shifted parameter is read by a producer of its
scope and that the nominal parameters select the nominal corrections. `-DSHIFTS` selects shifts by
case-insensitive substring, e.g. `CMS_scale_t` for all tau energy scale shifts.

## Tau embedding

`sm_config` builds the &mu;&rarr;&tau; embedded samples of the Run-2 eras (sample type `embedding`,
lists `sample_list/sm_<era>_embedding.txt`) through `embedding_run2_v15.setup`; NMSSM keeps the legacy
`tau_embedding_settings.setup_embedding`. `build_config` dispatches on `use_run2_v15_inputs`. Four
profile fields steer the module: `embedding_scopes` (SM: et, mt, tt; any other scope or a non-Run-2
era raises `ValueError`; the tau-ID measurement: mt and the &mu;&rarr;&mu; embedding in mm),
`embedding_tau_corrections` (false: no payload tau energy scale, no vsJet SF, no tau shifts),
`embedding_min_tau_pt` (a lower `tight_tau_min_pt` for embedding) and `tt_embedding_trigger` (below).

The inputs of an era are entries of three tables, so nothing else in the module names an era:
`KIT_EMBEDDING_PAYLOADS[era]` (the selection, muon and electron files of the Tau Embedding group,
`data/embedding/{embeddingselection,muon,electron}_<era>UL.json.gz`, the trigger SFs of the analysis
triggers of the era, and the MET filters the era's files lack), `TAU_EMBEDDING_ID_ES_PAYLOADS[era]` (the
measured tau energy scale and vsJet SF, `payloads/tau_embedding/Run2-<era>-UL-NanoAODv15/`) and
`TT_EMBEDDING_TRIGGER_EFFICIENCIES[era]`. The tau payload exists for 2018 only so far (2016 and 2017
follow from the tau-ID measurement, v7 spec 5.4): an `sm_config` embedding build of another era raises
`ValueError`, while the tau-ID measurement, which leaves the embedded taus uncorrected, builds in every
era.

Embedded events are data apart from the simulated tau decays: golden JSON, data JEC, no pileup,
b-tag, LHE-scale or top-pT weight, no JER. The MET filters drop `Flag_BadPFMuonDzFilter` in 2018, whose
v15 embedding files lack it (2016 and 2017 keep it); `EmbeddingGenPair` (Z &rarr; &tau;&tau;) replaces
the MC generator pair, and the generator-jet quantities are dropped (no `GenJet_*` in the files). The
corrections keep the MC column names and working points:

| | et | mt | tt |
|---|---|---|---|
| Selection | `emb_triggersel_wgt`, `emb_idsel_wgt_1/2` (`embeddingselection_<era>UL`, on the generator taus) | same | same |
| Lepton ID | KIT `ID90_pt_eta_bins` (`id_wgt_ele_1`), replaces the POG `wp90iso` SF | KIT `ID_pt_eta_bins` (`id_wgt_mu_1`) | &ndash; |
| Lepton iso | `iso_wgt_ele_1`: `Iso_pt_eta_bins` below 0.15, `AIso_pt_eta_bins` above | `iso_wgt_mu_1`: `Iso`, `AIso1` (0.15&ndash;0.25), `AIso2` (above) | &ndash; |
| Trigger | the KIT SF of the era's analysis trigger (2016 `Trg25_Iso`, 2017 `Trg32_Iso` and `Trg35_Iso`, 2018 `Trg32_Iso`), type `emb`, all iso values | the same for muons (2016 `Trg_pt_eta_bins`, 2017 `Trg_IsoMu27`, 2018 `Trg_IsoMu24`) | no requirement; `trg_effdata_emb_{Medium,AntiMedium}_{1,2}`, see below |
| Tau ES, vsJet SF | embedding payload, binned in the decay mode, Medium / vsEle Tight | Medium / vsEle VVLoose | Medium / vsEle VVLoose |
| Tau vsE, vsMu SF | POG, as MC | same | same |

The iso SFs take the correction of the lepton's `iso_1` bin (`xyh::scalefactor::embedding_iso_binned`,
|&eta;| for muons, signed &eta; for electrons, like the core functions). The tau payload is preliminary,
see `payloads/tau_embedding/README.md`. Electrons keep the EGM MC scale and smearing.

The di-tau paths do not fire in embedding, and the efficiency of their tau leg in embedding cannot be
measured in the &mu;&tau;<sub>h</sub> embedding (the di-tau filters need two taus). The tt embedding
therefore has no trigger requirement and is weighted with the data efficiency of the di-tau leg of
each tau (v7 spec E33, variant A; `tt_embedding_trigger = "eff_data"`, the only implemented value):
`trg_effdata_emb_Medium_<leg>` for taus that pass vsJet Medium and `trg_effdata_emb_AntiMedium_<leg>`
for the anti-isolated ones of the fake-factor application region, both written for both taus; the
event weight takes the class of each tau downstream. Until ShapeSmith's own measurement of the tau leg
on the tau-ID production exists, the efficiencies are the POG v15 `tau_trigger` `eff_data` of the era
(DeepTau2018v2p5, `ditau`): Medium for the isolated class and VVVLoose, the closest POG working point,
for the anti-isolated one (`TT_EMBEDDING_TRIGGER_EFFICIENCIES`; the own payload brings
`VVVLoose_not_Medium`). The AntiMedium value is a stopgap: VVVLoose contains the Medium taus, while
the class is VVVLoose and not Medium (doc 12.6), so the datacards need an lnN for it until the own
payload replaces it. Below the first p<sub>T</sub> edge of the POG payload (39.6 GeV, flow "error")
the core evaluation catches the error and returns 1.0 (taus are selected from 20 GeV; the tt trigger
p<sub>T</sub> cut of 40 GeV is applied downstream). They have no shifts yet (v7 is nominal only, E34). The flags of the MC names stay
as diagnostic columns, matched to the filter bits of TauEmbeddingSamplesUL without an HLT path
(`triggers.TauTauTriggerFlagsEmbedding`): 2016 the final filter (bits 1 and 8), 2017 and 2018 the
embedding di-tau L2 filter bit 23. The KIT file `tau_trigger<era>_UL` (DeepTau2017v2p1) is no longer
used.

Shifts (all others exclude embedding), defined in `variations/taus.py`, without channel in the name:

- `CMS_scale_t_emb_DeepTau2018v2p5_DM{0,1,10,11}_2018{Up,Down}`: tau energy scale per decay mode;
- `CMS_eff_t_emb_DeepTau2018v2p5_VSjet_DM{0,1,10,11}_2018{Up,Down}`: vsJet SF per decay mode.

The payload fills DM11 with the fitted 3-prong category of DM10, but a shift varies one decay mode:
DM10 and DM11 are separate shifts, to be correlated downstream.

Downstream contract:

- routing like the data streams: mutau &rarr; mt, eltau &rarr; et, tautau &rarr; tt;
- event weight: the SF columns above &times; `emb_genweight` &times; `emb_triggersel_wgt` &times;
  `emb_idsel_wgt_1` &times; `emb_idsel_wgt_2`, no cross section or luminosity, trigger flag
  required in et and mt; in tt no trigger flag and the `trg_effdata_emb` weight of each tau's class;
  `genWeight` is written too and equals `emb_genweight`;
- embedding enters only with genuine &tau;&tau; ("T": et `gen_match_1 == 3 && gen_match_2 == 5`, mt
  `gen_match_1 == 4 && gen_match_2 == 5`, tt both `== 5`), and MC events with T are removed from DY,
  TT, ST, VV, TTV and EWK; W, H and HH stay;
- the FastMTT and fake-factor friends run on the embedding n-tuples like on data and MC.

The embedding production runs under the same production tag as its data/MC production, see
`sample_list/README.md`.

## Tau-ID measurement

`sm_tau_id_measurement_config` builds the n-tuples of the DeepTau2018v2p5 vsJet SF and tau energy
scale measurement for embedding (ShapeSmith measurement `tau_id_es`): every Run-2 era, mt (the
&mu;&tau;<sub>h</sub> tag and probe) and mm (the Z &rarr; &mu;&mu; control region), for data
(SingleMuon), MC (`dyjets`, `wjets`, `ttbar`, `singletop`, `diboson`) and embedding (mutau in mt, muemb
in mm); sample lists `sample_list/sm_<era>_tau_id_measurement.txt`. Other eras and scopes raise
`ValueError`. The profile keeps the SM selection and sets `tau_id_measurement`, which replaces the
corrections and the trigger below and drops the MC vsJet and POG muon SF shifts
(`tau_id_measurement.setup`, called at the end of `build_config`). The per-era choices are the tables
`TM_SINGLE_MUON_TRIGGERS` and `TM_KIT_TRIGGER_SFS`: 2016 and 2017 take the analysis triggers and their
KIT SFs (the IsoMu22 family with `Trg_pt_eta_bins`, IsoMu27 with `Trg_IsoMu27_pt_eta_bins`), 2018 the
triggers of the precedent below. All are matched within &Delta;R < 0.1. MC carries the L1 prefiring
weight `prefiring_wgt` with its Up/Dn columns in every era (2018: the muon prefiring) and the shift
`CMS_ecal_prefiring_<year>`; the measurement production keeps its MC shifts, the exception of v7 spec
E34. In 2018 every sample writes the HEM flag `hem_veto`, which replaces the HEM shift.

In mt the measurement also writes the columns of the efficiency measurement of the tau leg of the
di-tau trigger for the tt embedding (v7 spec E33, `docs/v7_tt_emb_trigger_2026-10-16.md` 12.4), in data,
MC and embedding (`tau_triggersetup.TAU_LEG_*`): the monitoring flags of the tau h, true if the
&mu;&tau; monitoring path fired and the tau matches a trigger object with all bits of the tau leg
within &Delta;R < 0.4 (`trg_mon_mu19tau32_{mediso,medcombiso}_2` in 2016, bits 1, 5, 7;
`trg_mon_mu24tau35_{tightiso_tightid,mediumiso_tightid,tightiso}_2` in 2017 and 2018, bits 2/1, 4, 9,
17; `trg_mon_mu24tau35_mediumiso_hps_2` in 2018, bits 1, 5, 9, 17), the p<sub>T</sub>, L1 p<sub>T</sub>
and L1 isolation of the nearest such trigger object (`trgobj_{pt,l1pt,l1iso}_2`, -1 without one; addon
`trigger::MatchedObjectQuantity`, bits 1, 5, 7 in 2016 and 9, 17 in 2017/2018), and the di-tau
filters of the embedding as diagnostics (`trg_emb_ditau_l2_2`: bit 12 in 2016, 23 in 2017/2018;
`trg_emb_ditau_final_2`: bits 1, 8 in 2016, 6 in 2017/2018). All have p<sub>T</sub> > 20 GeV and
&#124;&eta;&#124; < 2.5; the tt acceptance is cut downstream. The 2018 data before run 317509 have the
non-HPS monitoring paths, the 2018 MC and embedding the HPS one only.

The energy scale grid is not produced in CROWN: the embedded taus stay uncorrected (energy scale 1,
no vsJet SF, no tau shifts) and are selected from 20/1.2 GeV on, so that ShapeSmith can scale their
kinematics per grid point, up to +20 %, and still cut at 20 GeV. NanoAOD stores taus from 18 GeV on,
so grid points above +11 % miss the taus that would enter from below 18 GeV; the precedent's grid,
produced in CROWN from the same NanoAOD, missed them as well. The MC tau energy scale shifts are the
only shifts whose name contains `CMS_scale_t`, so this substring selects them and nothing else.

### Corrections and their precedent

The precedent is jvoss's measurement production `SFs_EMB_Run2_04_08_26` (TauAnalysis
`config_run2_v15`, generated code under `KingMaker_v15_Run2/build/SFs_EMB_Run2_04_08_26__nom`);
everything not listed is the `sm_config` one.

| Correction | This configuration | Source | Precedent | `sm_config` |
|---|---|---|---|---|
| Trigger (data, MC, embedding; mt, mm), 2018 | `trg_single_mu24` &#124;&#124; `trg_single_mu27`: HLT_IsoMu24/27, p<sub>T</sub> > 25/28 GeV, &#124;&eta;&#124; < 2.5, filter bit 3, &Delta;R < 0.1 | NanoAOD trigger objects | same (`MTGenerateSingleMuonTriggerFlags`, &Delta;R < 0.4) | IsoMu24 only (bit 1, 26 GeV, &#124;&eta;&#124; < 2.4) |
| Muon trigger SF, MC, 2018 | `trg_wgt_single_mu24`, `_mu27`, `_mu24ormu27` of the first muon, type `mc`, evaluated at every p<sub>T</sub> (`_mu27` is meaningful above 28 GeV only, as the predecessor's weight uses it) | KIT `data/embedding/muon_2018UL.json.gz`: `Trg_IsoMu24`, `Trg_IsoMu27`, `Trg_IsoMu27_or_IsoMu24_pt_eta_bins` | `MTGenerateSingleMuonTriggerSF_MC` | KIT `Trg_IsoMu24_pt_eta_bins` |
| Muon trigger SF, embedding | the same three, type `emb` | same payload | `MTGenerateSingleMuonTriggerSF` (mt, mm) | `Trg_IsoMu24` only (mt) |
| Trigger and SFs, 2016 and 2017 | the analysis triggers and KIT SFs of `sm_config` (Run-2 v15 section) | KIT `muon_<era>UL` | &ndash; | same |
| Prefiring weight, MC | `prefiring_wgt` in every era | NanoAOD `L1PreFiringWeight_Nom` | &ndash; | same, with the Up/Dn columns and without shifts |
| Muon ID/iso SF, MC | `ID_pt_eta_bins`, `Iso_pt_eta_bins`, type `mc`, first muon (mt), both (mm) | KIT `muon_2018UL` | `PrivateMuonIDSF/IsoSF_{1,2}_MC` | POG `NUM_MediumID_DEN_TrackerMuons`, `NUM_TightRelIso_DEN_MediumID` |
| Muon ID/iso SF, embedding | mt: ID + iso-binned (Part A), mm: `ID`, `Iso_pt_eta_bins` of both muons, type `emb` | KIT `muon_2018UL` | `TauEmbeddingMuonIDSF/IsoSF_{1,2}` (mt: `Iso` only, equal below iso 0.15) | &ndash; |
| Embedding selection SF, generator pair | `embeddingselection_2018UL` in mt and mm; `EmbeddingGenPair` Z&rarr;&tau;&tau; (mt), Z&rarr;&mu;&mu; 23/13/13 (mm) | KIT | `TauEmbeddingSelectionSF`, `EmbeddingGenPair` | mt as Part A |
| Tau ES, MC | POG `tau_energy_scale`, vsJet Loose, vsEle VVLoose | POG TAU `Run2-2018-UL-NanoAODv15/2025-11-27` | `TauEnergyCorrection_ES_dm_binned_v15` (Loose, VVLoose) | Medium, VVLoose |
| Tau ES, embedding | by value, 1.0 per decay mode | &ndash; | `TauEnergyCorrection_Embedding` (1.0) | embedding payload |
| vsJet SF, MC | `id_wgt_tau_vsJet_{Medium,Tight}_2`, wp_VSe VVLoose, `dm` | POG | Loose, Medium, Tight, VVLoose, `dm` | Medium |
| vsJet SF, embedding | none | &ndash; | none | embedding payload |
| vsEle / vsMu SF | `id_wgt_tau_vsEle_{VVLoose,Tight}_2`; `id_wgt_tau_vsMu_Tight_2` for both vsEle WPs (the v15 payload has no vsEle input) | POG | the same values, one vsMu column per vsEle WP | same |
| MET recoil correction | DY and W (`dyjets`, `wjets`), jets of the HTT recipe | CROWN `data/recoil_corrections/Type1_PuppiMET_2018.root` (Z p<sub>T</sub> edges fixed in 27262f4) | DY and W (`MetCorrections_Run2`) | same |
| b-tag SF | none | &ndash; | none | strict UParTAK4 weight |
| Embedding tau p<sub>T</sub> threshold | 20/1.2 GeV | grid applied in ShapeSmith | 20 GeV, grid in CROWN | 20 GeV |

The predecessor's MC also computed a Z p<sub>T</sub> reweighting that its shapes did not use; 2018
v15 has none. Its sample list additionally held the madgraphMLM `WJetsToLNu`, which its shapes did not
use either (a generator alternative, see `sample_list/README.md`).

### Shape systematics

The MC shifts are the common ones of `build_config` (`variations/`), except for the vsJet SF shifts,
since the measurement measures that SF, and the POG muon ID/iso and trigger SF shifts, since it
replaces those SFs; its KIT trigger SF has a shift of its own. The table maps the shape systematics
of the predecessor (jvoss's synced shapes of `SFs_EMB_Run2_04_08_26__full`) to them.
`tests/test_sm_tau_id_measurement_config.py` holds the same map (`PREDECESSOR_SHIFTS`) and checks
that every listed shift exists in mt and, for the families mm carries, in mm.

| Datacard family | CROWN shifts (`Up`/`Down`) or weight | Affected columns |
|---|---|---|
| `CMS_scale_j_<source>` (28 sources) | the reduced set of the regrouped sources, `CMS_scale_j_{Absolute,BBEC1,EC2,HF}{,_2018}`, `CMS_scale_j_FlavorQCD`, `CMS_scale_j_RelativeBal`, `CMS_scale_j_RelativeSample_2018`; the individual sources are not produced | jets, b-tag weights, `n_jets`, `n_bjets`, `met`, `metphi`, `mt_1`, `pt_tautau`, `mt_tot`, ... |
| `CMS_scale_j_HEMIssue_Run2018` | none: the HEM flag `hem_veto` vetoes the affected events (v7 spec E29) | `hem_veto` |
| `CMS_PileUp` | `CMS_pileup_2018` | `puweight` |
| `CMS_scale_met_unclustered_energy_Run2018` | `CMS_scale_met_unclustered_energy_2018` | `met`, `metphi`, `mt_1`, `pt_tautau`, `mt_tot`, ... |
| `CMS_res_met_Run2018`, `CMS_scale_met_Run2018` | `CMS_res_met_RecoilCalibration_2018`, `CMS_scale_met_RecoilCalibration_2018` (`dyjets`, `wjets`) | as above |
| `CMS_scale_t_dm{0,1,10,11}_Run2018` | `CMS_scale_t_DeepTau2018v2p5_DM<dm>_pt{20to40,40to60,60toInf}_genTau_2018`, decorrelated in p<sub>T</sub> as well | tau four-vector, `m_vis`, `mt_1`, `met`, tau ID flags and SFs, pair columns |
| `CMS_eff_t_dm{0,1,10,11}_Run2018` | none, the measured SF (the predecessor's up/down evaluated the nominal SF) | &ndash; |
| `CMS_fake_m_WH{1..5}_Run2018` | `CMS_fake_t_DeepTau2018v2p5_VSmu_wheel{1..5}_2018` | `id_wgt_tau_vsMu_Tight_2` |
| `CMS_scale_fake_m_Run2018` | `CMS_scale_t_DeepTau2018v2p5_genMuon_wheel{1..5}_2018`, decorrelated in the muon wheels | tau four-vector and pair columns, as the genuine-tau shifts |
| `CMS_eff_m_trigger_Run2018` | `CMS_eff_m_trigger_2018`: KIT MC trigger SFs &times; 1.02 / 0.98, mt | `trg_wgt_single_mu24`, `_mu27`, `_mu24ormu27` |
| (new, E11) | `CMS_ecal_prefiring_<year>`: `L1PreFiringWeight_Up/Dn` in place of `_Nom`, 2016-2018 | `prefiring_wgt` |
| no predecessor family | `CMS_res_j_2018`, `CMS_scale_e_2018`, `CMS_res_e_2018`, `QCDscale_{ren,fac}`, `CMS_fake_t_DeepTau2018v2p5_VSe_DM<dm>_{barrel,endcap}_2018`, `CMS_scale_t_DeepTau2018v2p5_DM<dm>_genElectron_{barrel,endcap}_2018` | |
| `CMS_htt_ttbarShape` | weight: `topPtReweightWeight` squared (up), removed (down) | `topPtReweightWeight` (nominal) |
| `CMS_fake_j_Run2018` | weight: `max(1-0.002 pt_2, 0.6)` (up), `min(1+0.002 pt_2, 1.4)` (down) | `pt_2` (nominal) |
| `CMS_emb_ttbar_contamination_Run2018` | built downstream from TTT for every EMB grid point | &ndash; |

## Tests

The Python tests build the configurations and assert their surfaces; paths below are relative to the
CROWN repo root. `source analysis_configurations/bbtautau/scripts/setup_tests.sh` sets up the LCG
stack and `PYTHONPATH`. They read the pinned BTV payload, so `/cvmfs/cms-griddata.cern.ch` must be
mounted.

```bash
python -m pytest analysis_configurations/bbtautau/tests
```

The C++ fixtures under `tests/cpp/` (strict UParT b-tag consumer with all five and with the [T, M]
working points and the K1 rule, SM HH kinematic fit, electron reconstruction weight, electron SFs at
the supercluster eta, embedding iso-binned SF and JER smearing with the payloads of every Run-2 era,
FastMTT decay types, matched trigger object, HEM flag, fake factor summed over the payload processes,
checked MET covariance, KIT muon trigger SF with its p<sub>T</sub> cap) run inside the same pytest session (`tests/test_cpp_runtime.py`) and are skipped without
`root-config`, `g++`, correctionlib and spdlog headers. `tests/test_run2_eras.py` checks the per-era
inputs (MET filters, jet ID, KIT lepton and trigger SF names, b-tag efficiency and embedding tau
payloads, TAU POG placeholders), `tests/test_triggers.py` the trigger flags and SFs per era against
the HLT branches and filter-bit doc strings of the eras' v15 files (`tests/fixtures/*_hlt.txt`,
`nanoaod_v15_trigobj_filterbits.json`, written by `tests/fixtures/make_hlt_fixtures.py`),
`tests/test_v7_corrections.py` the prefiring columns, the MET propagation, the HEM flag and the electron
SFs at the supercluster eta per era. Cases of an
era that need a payload not measured yet are strict xfails listed in `tests.helpers.PENDING`: they
turn into failures once the payload exists, and the entry goes. `tests.helpers.generate_code` emits the C++ code of a configuration in a
subprocess, once per session; the embedding tests use it with a committed branch list of one v15
embedding file (`tests/fixtures/nanoaod_v15_embedding_2018_branches.txt`). The synthetic b-tag fixtures
(gitignored) are regenerated by the test from `tests/fixtures/make_btag_sf_strict_fixtures.py`.
`tests.helpers.build` and `generate_code` take the era without a default, so every test names it;
the SM tests run in every Run-2 era, NMSSM in 2018.

Neither pytest nor a code-generation dry run compiles the generated code, so a changed core signature
(e.g. the vsMu working point of `experimental::Id_vsJet` from core 14f82c1 on) shows only in the
build. `scripts/compile_check.sh <build dir> [jobs]` compiles one MC configuration per production in
every Run-2 era in the CROWN container (`sm_config` ttbar in six scopes, `sm_btag_efficiency_config`
ttbar, `sm_tau_id_measurement_config` dyjets in mt and mm, and the `sm_config` embedding of the eras
with an embedding tau payload); run it after every core pin change and before a production.

## 2018 control production

See [control production](docs_control_production.md) for `ee/em/mm`, the calibration-first UParT workflow, and the et/mt light-lepton isolation sideband kept up to 0.5.
