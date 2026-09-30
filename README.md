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
  Run-2 NanoAOD-v15 inputs, UParTAK4 b-tagging, `AVAILABLE_ERAS = ["2018"]`, tau embedding in et, mt
  and tt (see [Tau embedding](#tau-embedding)).
* `sm_btag_efficiency_config.py` (`SM_BTAG_EFFICIENCY_PROFILE`, a `dataclasses.replace(SM_PROFILE,
  ...)`) - The same selection, MC only and without b-tag scale factors, plus the probe-jet collection
  the UParT b-tag MC efficiency is measured from downstream in `TauFakeFactors`. Being
  payload-independent, it never depends on the payload it exists to produce.
* `sm_tau_id_measurement_config.py` (`SM_TAU_ID_MEASUREMENT_PROFILE`, `tau_id_measurement.py`) - The
  n-tuples of the tau-ID SF and energy scale measurement for embedding, 2018, mt and mm (see
  [Tau-ID measurement](#tau-id-measurement)).

## Available Friend Configurations

The friend entries are thin wrappers around the shared `FriendTreeConfiguration` bodies in
`friend_common.py`: `build_friend_config` (FastMTT, resolved kinematic fit) and
`build_fake_factor_friend` (fake factors).

* `nmssm_fastmtt.py` / `sm_fastmtt.py` - Produce FastMTT friends (`m/pt/eta/phi_fastmtt`); the SM
  module re-exports the NMSSM builder and only adds `AVAILABLE_ERAS = ["2018"]`.
* `nmssm_kinfit_resolved.py` / `nmssm_kinfit_boosted.py` - HH/YH kinematic fit over the NMSSM Y-mass
  hypotheses, resolved and boosted.
* `sm_kinfit_resolved.py` - Fixed 125/125 GeV HH kinematic fit, 2018 only; outputs
  `kinfit_convergence`, `kinfit_chi2`, `kinfit_prob`, `kinfit_mHH`.
* `fake_factors_friend_config.py` / `sm_fake_factors.py` - Fake-factor friends, NMSSM (Run 3,
  `NMSSM_PAYLOAD_DIRS`) and SM (2018, `SM_PAYLOAD_DIRS`); see [Fake-factor friends](#fake-factor-friends).
* `xyh_classifier_friend_config.py` - Produce PNN classifier friends for the NMSSM analysis.

### Fake-factor friends

Each friend reads the two payload files of its scope, `fake_factors_<ch>.json.gz` and
`FF_corrections_<ch>.json.gz` (TauFakeFactors layout; `FF_corrections_<ch>_default.json.gz` where the
corrections file carries the name of its corrections configuration), at configuration time with `ff_payloads.py`
(standard library only), and takes the correction inputs and the shifts from them, so a new payload
needs no code change. The C++ (`cpp_addons/src/fakefactors.cxx`) evaluates the QCD + ttbar model per
leg: `frac_QCD * max(FF_QCD * DR->SR_QCD * closure_QCD, 0) + frac_ttbar * max(FF_ttbar * closure_ttbar, 0)`,
the raw fake factor without the corrections.

| Scope | Legs (correction suffix) | Outputs |
|---|---|---|
| et, mt | `lt` (none) | `fake_factor_raw`, `fake_factor` |
| tt | `leading` (none), `subleading` (`_subleading`) | `fake_factor_{1,2}_raw`, `fake_factor_{1,2}` |

The payload conventions are checked when the configuration is built (a `ValueError` names the file and
the correction): every correction has a `syst` category with a default (the nominal) at the top, the
inputs are `[process] + real ... + syst` (`process` only in the fractions, whose processes are exactly
QCD and ttbar), every input is a quantity of `quantities/output.py` (`njets`/`nbtag` are aliases of
`n_jets`/`n_bjets`), every syst key is `nominal`, `<correction>nominal` or ends in Up/Down/_up/_down
with its partner, and the global non-closure keys are in every member of a compound closure.

Shifts: every Up/Down key of the leg's corrections except `SystBandHigh`/`SystBandLow` (the same
smoothing band as `SystBandAsym`) and the per-variable non-closure keys (only the global, coarse ones
are kept). The shift name is the payload key with `_up`/`_down` written `Up`/`Down`, e.g.
`process_fractionsfrac_QCDUp` sets `ff_fraction_variation` to `process_fractionsfrac_QCD_up`; fake-factor
and fraction shifts act on both outputs of the leg, DR->SR and closure shifts only on the corrected
one. That is 17 pairs per leg for the SM 2018 payload and 14 for the NMSSM ones. The NMSSM shift names
therefore follow the payload keys (2025: `QCDStatShift...`, `process_fractionsfrac_QCD...`; 2022-2024:
`fracTTbarUnc`), which the hardwired lists before got wrong, evaluating those shifts as nominal.
Friends keep `--shifts all|none`.

The build needs a quantities map that lists every input column of the scope. A missing nominal
column fails at configuration time; a shifted variant is used where the map has it, otherwise the
input stays nominal under that shift (info log only).

Payloads: the NMSSM Run-3 ones stay at `payloads/fake_factors/<version>/<era>/` (2022 and 2023:
`fake-factors-2026-06-10`, 2024 and 2025: `fake-factors-2026-09-26`, which has no 2024 tt payload), new ones go to
`payloads/fake_factors/<analysis>/<version>/<era>/`. The SM payload is the commissioning payload
`payloads/fake_factors/sm/fake-factors-2026-09-22/2018/` (see its README; its shifts are for wiring
checks only). A new payload goes into a new dated directory, and only the entry in `SM_PAYLOAD_DIRS` /
`NMSSM_PAYLOAD_DIRS` changes. Friend tarballs and outputs are keyed by production and friend tag
only, so producing friends with a new payload on an existing production needs a new `--friend-tag`.

## Building

Per-era wrapper scripts in `build_scripts/`, run from the CROWN repo root. All arguments are
positional and optional: `$1` samples, `$2` scopes, `$3` debug, `$4` steps
(`build` | `run_binary` | `all`), `$5` config (default `nmssm_config`).

```bash
bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh
bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh hh2b2tau et,mt,tt false build sm_config
```

Each script configures and compiles in `<CROWN>/build_<era>[_<config>]/` -- the `_<config>` suffix is
appended whenever `$5` is not `nmssm_config`, so builds for one era do not clobber each other -- and
installs binaries `<config>_<sample>_<era>` into its `bin/`. `run_binary` runs each binary on a
hard-coded remote NanoAOD test file and needs a valid grid proxy.

The scripts pass `-DSHIFTS=none`. `-DSHIFTS` selects which of the *registered* CROWN shifts get
compiled into an executable, matched by **case-insensitive substring containment** against the shift
names (`Configuration._is_valid_shift`): `jes` selects every `jesUnc*` shift, `btag` every b-tag one.
`all` and `none` are specials.

## Run-2 NanoAOD-v15 inputs

Both SM profiles set `use_run2_v15_inputs = True`. Only 2018 is enabled so far; the other Run-2 eras
are meant to follow on the same code path, which is why nothing on it is named after an era. Relative
to the legacy Run-2 path NMSSM keeps using:

- **Jet ID** -- v15 ships no usable `Jet_jetId`, so the AK4-PUPPI ID is evaluated from the composition
  branches by `producers/jets.py`'s `JetIDFromCorrectionlib` (the same producer 2024/2025 use), reading
  `payloads/jetid/Run2-<era>-UL-NanoAODv15/jetid.json.gz`. JME does not publish that file for Run 2 UL;
  it is generated by the `jetid-payloads` repository (see `payloads/jetid/README.md`), 2018 only so far.
- **Electron scale and smearing** -- v15 carries the Run-3-style scale+smear inputs, so this path uses
  the Run-3 `ElectronPtCorrectionMC` producer against the era's pinned `EGM/Run2-<era>-UL-NanoAODv15`
  payload.
- **MET covariance** -- v15 drops `MET_covXX/XY/YY`, so the covariance comes from `PuppiMET` through
  `met.met_global(overrides)`.
- **b-tagging** -- UParTAK4. `btag_payloads.py` reads the pinned per-era BTV payload
  (`BTV/Run2-<era>-UL-NanoAODv15/2026-06-18/btagging.json.gz`) with `btv_upart_payload`,
  `load_upart_wps` (working points) and `discover_upart_variations` (variation keys); MC efficiencies
  are committed at `payloads/btagging_efficiencies/upart/2018/btag_efficiency_{et,mt,tt}.json.gz`
  (`SM_PROFILE.btag_payload_dir = "payloads/btagging_efficiencies/upart/{era}"`). The
  multi-working-point event weight comes from the strict consumer
  `xyh::scalefactor::btagging_strict::multi_wp_event_weight` (`cpp_addons/*/btag_sf_strict.*`), which
  takes the five WP thresholds from the SF payload's own `UParTAK4_wp_values` correction and throws
  instead of clamping -- on thresholds that are not strictly decreasing, an efficiency that is
  non-finite / &le; 0 / > 1, a non-monotonic efficiency pair, |&eta;| outside [0, 2.4), an unknown
  jet flavour, or any correctionlib failure.
- **Probe jets** -- with `enable_probe_jet_collection`, `jets.BtagProbeJetVectors` masks the jets with
  `CombineMasks(base_bjets_mask, jet_overlap_veto_mask)` and exports
  `btag_probe_jet_{pt,eta,hadron_flavour,upart}` via `xyh::btag_probe::masked_vector` -- the columns
  the downstream efficiency measurement reads.

All `/cvmfs/cms-griddata.cern.ch` pins are dated CAT-metadata snapshots, never the rolling `latest`
symlink; after changing one, rerun the tests.

## Tau embedding

`sm_config` builds the 2018 &mu;&rarr;&tau; embedded samples (sample type `embedding`, list
`sample_list/sm_2018_embedding.txt`) through `embedding_run2_v15.setup`; NMSSM keeps the legacy
`tau_embedding_settings.setup_embedding`. `build_config` dispatches on `use_run2_v15_inputs`. Three
profile fields steer the module: `embedding_scopes` (SM: et, mt, tt; any other scope or an era other
than 2018 raises `ValueError`; the tau-ID measurement: mt and the &mu;&rarr;&mu; embedding in mm),
`embedding_tau_corrections` (false: no payload tau energy scale, no vsJet SF, no tau shifts) and
`embedding_min_tau_pt` (a lower `tight_tau_min_pt` for embedding).

Embedded events are data apart from the simulated tau decays: golden JSON, data JEC, no pileup,
b-tag, LHE-scale or top-pT weight, no JER. The MET filters drop `Flag_BadPFMuonDzFilter`, which the
v15 embedding files lack; `EmbeddingGenPair` (Z &rarr; &tau;&tau;) replaces the MC generator pair, and
the generator-jet quantities are dropped (no `GenJet_*` in the files). The corrections keep the MC
column names and working points:

| | et | mt | tt |
|---|---|---|---|
| Selection | `emb_triggersel_wgt`, `emb_idsel_wgt_1/2` (`embeddingselection_2018UL`, on the generator taus) | same | same |
| Lepton ID | KIT `ID90_pt_eta_bins` (`id_wgt_ele_1`), replaces the POG `wp90iso` SF | KIT `ID_pt_eta_bins` (`id_wgt_mu_1`) | &ndash; |
| Lepton iso | `iso_wgt_ele_1`: `Iso_pt_eta_bins` below 0.15, `AIso_pt_eta_bins` above | `iso_wgt_mu_1`: `Iso`, `AIso1` (0.15&ndash;0.25), `AIso2` (above) | &ndash; |
| Trigger | `Trg32_Iso_pt_eta_bins`, type `emb`, all iso values | `Trg_IsoMu24_pt_eta_bins`, all iso values | `tau_trigger2018_UL` `tauTriggerSF` |
| Tau ES, vsJet SF | embedding payload, Medium / vsEle Tight | Medium / vsEle VVLoose | Medium / vsEle VVLoose |
| Tau vsE, vsMu SF | POG, as MC | same | same |

The iso SFs take the correction of the lepton's `iso_1` bin (`xyh::scalefactor::embedding_iso_binned`,
|&eta;| for muons, signed &eta; for electrons, like the core functions). The tau payload is preliminary,
see `payloads/tau_embedding/README.md`. Electrons keep the EGM MC scale and smearing. The tt trigger
flags keep their four MC names, but match both taus to the embedding di-tau filter bit 23 without an
HLT path (`triggers.TauTauTriggerFlagsEmbedding`), since the ditau paths do not fire in embedding.

Shifts (all others exclude embedding), defined in `variations/taus.py`, without channel in the name:

- `CMS_scale_t_emb_DeepTau2018v2p5_DM{0,1,10,11}_2018{Up,Down}`: tau energy scale per decay mode, both
  pT bins of a decay mode together;
- `CMS_eff_t_emb_DeepTau2018v2p5_VSjet_DM{0,1,10,11}_pt{20to40,40toInf}_2018{Up,Down}`: vsJet SF per
  decay mode and pT bin; tt, which selects taus above 40 GeV, has only `pt40toInf`.

The payload fills DM11 with the fitted 3-prong category of DM10, but a shift varies one decay mode:
DM10 and DM11 are separate shifts, to be correlated downstream.

Downstream contract:

- routing like the data streams: mutau &rarr; mt, eltau &rarr; et, tautau &rarr; tt;
- event weight: the SF columns above &times; `emb_genweight` &times; `emb_triggersel_wgt` &times;
  `emb_idsel_wgt_1` &times; `emb_idsel_wgt_2`, no cross section or luminosity, trigger flag
  required; `genWeight` is written too and equals `emb_genweight`;
- embedding enters only with genuine &tau;&tau; ("T": et `gen_match_1 == 3 && gen_match_2 == 5`, mt
  `gen_match_1 == 4 && gen_match_2 == 5`, tt both `== 5`), and MC events with T are removed from DY,
  TT, ST, VV, TTV and EWK; W, H and HH stay;
- the FastMTT and fake-factor friends run on the embedding n-tuples like on data and MC.

The embedding production runs under the same production tag as its data/MC production, see
`sample_list/README.md`.

## Tau-ID measurement

`sm_tau_id_measurement_config` builds the n-tuples of the DeepTau2018v2p5 vsJet SF and tau energy
scale measurement for embedding (ShapeSmith measurement `tau_id_es`): 2018, mt (the &mu;&tau;<sub>h</sub>
tag and probe) and mm (the Z &rarr; &mu;&mu; control region), for data (SingleMuon), MC (`dyjets`,
`wjets`, `ttbar`, `singletop`, `diboson`) and embedding (mutau in mt, muemb in mm); sample list
`sample_list/sm_2018_tau_id_measurement.txt`. Other eras and scopes raise `ValueError`. The profile
keeps the SM selection and sets `tau_id_measurement`, which replaces the corrections and the trigger
below and drops the MC vsJet and POG muon SF shifts (`tau_id_measurement.setup`, called at the end of
`build_config`).

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
| Trigger (data, MC, embedding; mt, mm) | `trg_single_mu24` &#124;&#124; `trg_single_mu27`: HLT_IsoMu24/27, p<sub>T</sub> > 25/28 GeV, &#124;&eta;&#124; < 2.5, filter bit 3 | NanoAOD trigger objects | same (`MTGenerateSingleMuonTriggerFlags`) | IsoMu24 only (bit 1, 26 GeV, &#124;&eta;&#124; < 2.4), plus Mu50/Mu100 |
| Muon trigger SF, MC | `trg_wgt_single_mu24`, `_mu27`, `_mu24ormu27` of the first muon, type `mc`, evaluated at every p<sub>T</sub> (`_mu27` is meaningful above 28 GeV only, as the predecessor's weight uses it) | KIT `data/embedding/muon_2018UL.json.gz`: `Trg_IsoMu24`, `Trg_IsoMu27`, `Trg_IsoMu27_or_IsoMu24_pt_eta_bins` | `MTGenerateSingleMuonTriggerSF_MC` | POG `NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight` |
| Muon trigger SF, embedding | the same three, type `emb` | same payload | `MTGenerateSingleMuonTriggerSF` (mt, mm) | `Trg_IsoMu24` only (mt) |
| Muon ID/iso SF, MC | `ID_pt_eta_bins`, `Iso_pt_eta_bins`, type `mc`, first muon (mt), both (mm) | KIT `muon_2018UL` | `PrivateMuonIDSF/IsoSF_{1,2}_MC` | POG `NUM_MediumID_DEN_TrackerMuons`, `NUM_TightRelIso_DEN_MediumID` |
| Muon ID/iso SF, embedding | mt: ID + iso-binned (Part A), mm: `ID`, `Iso_pt_eta_bins` of both muons, type `emb` | KIT `muon_2018UL` | `TauEmbeddingMuonIDSF/IsoSF_{1,2}` (mt: `Iso` only, equal below iso 0.15) | &ndash; |
| Embedding selection SF, generator pair | `embeddingselection_2018UL` in mt and mm; `EmbeddingGenPair` Z&rarr;&tau;&tau; (mt), Z&rarr;&mu;&mu; 23/13/13 (mm) | KIT | `TauEmbeddingSelectionSF`, `EmbeddingGenPair` | mt as Part A |
| Tau ES, MC | POG `tau_energy_scale`, vsJet Loose, vsEle VVLoose | POG TAU `Run2-2018-UL-NanoAODv15/2025-11-27` | `TauEnergyCorrection_ES_dm_binned_v15` (Loose, VVLoose) | Medium, VVLoose |
| Tau ES, embedding | by value, 1.0 per decay mode | &ndash; | `TauEnergyCorrection_Embedding` (1.0) | embedding payload |
| vsJet SF, MC | `id_wgt_tau_vsJet_{Medium,Tight}_2`, wp_VSe VVLoose, `dm` | POG | Loose, Medium, Tight, VVLoose, `dm` | Medium |
| vsJet SF, embedding | none | &ndash; | none | embedding payload |
| vsEle / vsMu SF | `id_wgt_tau_vsEle_{VVLoose,Tight}_2`; `id_wgt_tau_vsMu_Tight_2` for both vsEle WPs (the v15 payload has no vsEle input) | POG | the same values, one vsMu column per vsEle WP | same |
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
| `CMS_scale_j_<source>` (28 sources), `CMS_scale_j_HEMIssue_Run2018` | the reduced set of the regrouped sources, `CMS_scale_j_{Absolute,BBEC1,EC2,HF}{,_2018}`, `CMS_scale_j_FlavorQCD`, `CMS_scale_j_RelativeBal`, `CMS_scale_j_RelativeSample_2018`, and `CMS_HEM_2018`; the individual sources are not produced | jets, b-tag weights, `n_jets`, `n_bjets`, `met`, `metphi`, `mt_1`, `pt_tautau`, `mt_tot`, ... |
| `CMS_PileUp` | `CMS_pileup_2018` | `puweight` |
| `CMS_scale_met_unclustered_energy_Run2018` | `CMS_scale_met_unclustered_energy_2018` | `met`, `metphi`, `mt_1`, `pt_tautau`, `mt_tot`, ... |
| `CMS_res_met_Run2018`, `CMS_scale_met_Run2018` | `CMS_res_met_RecoilCalibration_2018`, `CMS_scale_met_RecoilCalibration_2018` (`dyjets`, `wjets`) | as above |
| `CMS_scale_t_dm{0,1,10,11}_Run2018` | `CMS_scale_t_DeepTau2018v2p5_DM<dm>_pt{20to40,40to60,60toInf}_genTau_2018`, decorrelated in p<sub>T</sub> as well | tau four-vector, `m_vis`, `mt_1`, `met`, tau ID flags and SFs, pair columns |
| `CMS_eff_t_dm{0,1,10,11}_Run2018` | none, the measured SF (the predecessor's up/down evaluated the nominal SF) | &ndash; |
| `CMS_fake_m_WH{1..5}_Run2018` | `CMS_fake_t_DeepTau2018v2p5_VSmu_wheel{1..5}_2018` | `id_wgt_tau_vsMu_Tight_2` |
| `CMS_scale_fake_m_Run2018` | `CMS_scale_t_DeepTau2018v2p5_genMuon_wheel{1..5}_2018`, decorrelated in the muon wheels | tau four-vector and pair columns, as the genuine-tau shifts |
| `CMS_eff_m_trigger_Run2018` | `CMS_eff_m_trigger_2018`: KIT MC trigger SFs &times; 1.02 / 0.98, mt | `trg_wgt_single_mu24`, `_mu27`, `_mu24ormu27` |
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

The C++ fixtures under `tests/cpp/` (strict UParT b-tag consumer, SM HH kinematic fit, electron
reconstruction weight, embedding iso-binned SF, FastMTT decay types, JER smearing) run inside the
same pytest session (`tests/test_cpp_runtime.py`) and are skipped without `root-config`, `g++`,
correctionlib and spdlog headers. `tests.helpers.generate_code` emits the C++ code of a configuration in a
subprocess, once per session; the embedding tests use it with a committed branch list of one v15
embedding file (`tests/fixtures/nanoaod_v15_embedding_2018_branches.txt`). The synthetic b-tag fixtures
(gitignored) are regenerated by the test from `tests/fixtures/make_btag_sf_strict_fixtures.py`.

## 2018 control production

See [control production](docs_control_production.md) for `ee/em/mm`, the calibration-first UParT workflow, and the et/mt light-lepton isolation sideband kept up to 0.5.
