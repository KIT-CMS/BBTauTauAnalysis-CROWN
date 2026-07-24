# XYHBBTauTauAnalysis-CROWN

This repository has been forked from [KIT-CMS/TauAnalysis-CROWN](https://github.com/KIT-CMS/TauAnalysis-CROWN).

The repository holding the CROWN configuration of the NMSSM X &rightarrow; YH &rightarrow; bb&tau;&tau; analysis.


## Available Configurations

* `nmssm_config.py` - The main configuration to be used for the X &rightarrow; YH &rightarrow; bb&tau;&tau; search.


## Available Friend Configurations

* `nmssm_fastmtt.py` - Produce FastMTT friends

* `fake_factors_friend_config.py` - Produce fake factor friends for the NMSSM analysis


## SM (non-resonant HH) and NMSSM: parallel entry points, and the 2018 UParT efficiency chain

The section above predates the SM (non-resonant HH &rarr; bb &tau;&tau;)
program added alongside NMSSM in this repo; it is kept as-is for history.
This section documents the current, full picture -- **read this section**,
not just the one above, for anything touching the SM profile.

### Parallel SM / NMSSM entry points

Both analyses now share one framework (`common_config.py`) behind thin,
per-analysis top-level configs. Each top-level config module does nothing
but pick an **`AnalysisProfile`** (`analysis_profiles.py`, a frozen
dataclass) and call `common_config.build_config(PROFILE, era, sample,
scopes, shifts, ...)`:

| Config module | Profile | Purpose |
|---|---|---|
| `nmssm_config.py` | `NMSSM_PROFILE` | The X &rightarrow; YH &rightarrow; bb&tau;&tau; resonance search (all eras, unchanged physics). |
| `sm_config.py` | `SM_PROFILE` | SM non-resonant HH &rightarrow; bb&tau;&tau; production analysis (2018 UL v15 only). |
| `sm_btag_efficiency_config.py` | `SM_BTAG_EFFICIENCY_PROFILE` | Payload-**independent** probe-jet ntuple profile (2018, MC only) used to *measure* that same efficiency payload -- see the workflow doc linked below. |

An `AnalysisProfile` carries every axis the three configs differ on: allowed
eras, signal sample(s), truth-mother PDG IDs, the LHE-scale-weight sample
lists, whether the isolated 2018-v15 jet path is active
(`use_2018_v15_jet_path`), the b-jet |&eta;| acceptance override, which b-tag
algorithm/payload directory to use, and the efficiency-profile-only switches (`mc_only`,
`enable_btag_sf`, `enable_probe_jet_collection`). Adding a new analysis
variant that only needs a different combination of these switches means
adding a new `AnalysisProfile` instance and a new thin config module -- not
forking `common_config.py`.

### 2018-v15-only input contract for SM

`SM_PROFILE` and `SM_BTAG_EFFICIENCY_PROFILE` both set `allowed_eras =
("2018",)` and `use_2018_v15_jet_path = True`: the SM path only runs against
2018 UL **NanoAOD v15**, and takes three inputs from an isolated code path
that differs from the legacy (v9/Run-3) one NMSSM keeps using:

- **Jet ID recompute** -- v15 drops the precomputed `Jet_jetId` branch, so
  the tight AK4-PUPPI jet ID is recomputed from composition branches
  (`Jet_chHEF`, `Jet_neEmEF`, ...) per the pinned formula
  `jetid_2018UL_puppi_tight_v1`. Full derivation, sources, and the
  boundary-case fixture: `docs/jetid_2018UL_puppi_v15.md` +
  `tests/fixtures/jetid_2018UL_puppi_tight_v1.json`. `common_config.py`
  refuses to build the SM 2018-v15 path at all if the fixture's
  `formula_version` doesn't match the producer's
  (`jets.JETID_V15_FORMULA_VERSION`).
- **EGM electron path** -- v15 ships the Run-3-style scale+smear inputs
  (`Electron_deltaEtaSC`, `Electron_r9`, ...) instead of the v9
  `Electron_dEscale*`/`dEsigma*` branches, so the SM 2018-v15 path switches
  to the Run-3 electron-correction producer, pointed at the pinned
  2018-UL-v15 EGM payload.
- **PuppiMET covariance** -- v15 2018 UL renames the PF MET collection and
  drops the `MET_covXX/XY/YY` branches the legacy `MetCov` producer reads,
  so the SM path takes the MET covariance from `PuppiMET` instead
  (`met.MetGlobalSM2018V15`).

All three pin a **dated** `cvmfs/cms-griddata.cern.ch` snapshot (never the
rolling "latest" symlink), verified against this task's code:

| Payload | Pinned snapshot date | Path (under `/cvmfs/cms-griddata.cern.ch/cat/metadata/`) |
|---|---|---|
| BTV UParTAK4 (working points + SF) | 2026-06-18 | `BTV/Run2-2018-UL-NanoAODv15/2026-06-18/btagging.json.gz` |
| JME JEC/JER (2018-v15 branch) | 2026-06-05 | `JME/Run2-2018-UL-NanoAODv15/2026-06-05/jet_jerc.json.gz` |
| EGM electron scale+smear (2018-v15) | 2025-12-05 | `EGM/Run2-2018-UL-NanoAODv15/2025-12-05/electronSS_EtDependent.json.gz` |

Working points and systematic variations are read directly from the dated BTV
payload. After changing a pin, rerun the configuration and numerical tests.

### `-DSHIFTS=none` milestone semantics

Every build script in `build_scripts/` defaults `-DSHIFTS` to `none`, and the
worked examples in this README and in
`docs/sm_2018_efficiency_workflow.md` all pass it explicitly. This is a
**milestone choice, not a statement that the SM path has no systematics**:
`-DSHIFTS` only controls which of the *already-registered* CROWN shifts get
built into a given executable (case-insensitive substring match against
shift names, see `Configuration._is_valid_shift`); it says nothing about
which systematic *sources* the analysis is aware of or plans to eventually
produce. That full inventory is tracked completely separately, in
`systematics_sm_2018.yaml` (next section) -- do not read "`-DSHIFTS=none`
everywhere" as "systematics are not planned"; read it as "this milestone
does not yet build any of them".

### `systematics_sm_2018.yaml`: location, status semantics, validator

`systematics_sm_2018.yaml` (repo root) is the **machine-readable systematics
inventory** for the SM 2018 v15 path -- milestone 1: it enumerates every
systematic source the SM configuration surface is aware of, whether or not
it has been produced into ntuples yet, and classifies each entry by:

- **`execution_class`** -- how CROWN represents it: `nominal_column`
  (dispatched as ordinary weight columns alongside the nominal event, e.g.
  the UParTAK4 SF components), `crown_shift` (a registered
  `SystematicShift`, selected via `-DSHIFTS`), `alternative_sample`
  (estimated from a differently-generated MC sample, not a CROWN shift at
  all), or `downstream` (not produced by CROWN -- luminosity, MC stats,
  efficiency-measurement uncertainties, applied at the limit-setting stage).
- **`production_status`** -- `produced`, `registered_not_produced`,
  `planned`, ...
- **`final_disposition`** -- `propagate`, `pending_review`, or an
  `"excluded: <reason>"` string.

Validate it with `scripts/validate_systematics_inventory.py`:

```bash
python scripts/validate_systematics_inventory.py
python scripts/validate_systematics_inventory.py --final-inference
```

The **default mode** checks schema completeness plus coverage: every SM
`crown_shift` name the framework actually registers (built with
`shifts={"all"}`) must be matched by exactly one entry's
`shift_name_patterns` (the "single-owner rule" -- never zero, never more
than one), and every declared pattern must match at least one real shift
name. This mode passes today.

**`--final-inference`** additionally rejects any entry still
`pending_review`, and any non-`produced` entry without an `"excluded:
..."` disposition -- a deliberately strict gate for paper/limit-ready
inference. **This mode is expected to fail at the current milestone**
(several sources are still `pending_review` or
`registered_not_produced`/`planned` without an `excluded:` disposition by
design); a failing `--final-inference` run today is not a bug, it is the
inventory honestly reporting that the SM systematic program is incomplete.

### Efficiency entry point and the full TauFakeFactors workflow

`sm_btag_efficiency_config.py` (`SM_BTAG_EFFICIENCY_PROFILE`) is the CROWN
entry point that produces the **input ntuples** the SM UParT b-tag
efficiency is measured from downstream in `TauFakeFactors`
(`btag_efficiency.py`). It is deliberately payload-independent (`mc_only =
True`, `enable_btag_sf = False`, `enable_probe_jet_collection = True`) so it
never depends on the payload it exists to help produce.

**The full five-step, three-repository workflow -- the committed
`sample_list/` lists through `law run ProduceNtuples`, `TauFakeFactors`
`preselection.py`/`btag_efficiency.py`, and installing the generated payload
into this repo -- is documented end-to-end, with copy-pasteable commands, in
[`docs/sm_2018_efficiency_workflow.md`](docs/sm_2018_efficiency_workflow.md).**
Read that document rather than re-deriving the chain from the scripts.

### Efficiency payload and the explicit legacy alias

`SM_PROFILE.btag_payload_dir` points to
`"payloads/btagging_efficiencies/upart/2018"`. Configuration building only
constructs the per-channel `btag_efficiency_<scope>.json.gz` path; the payload
is opened by the runtime b-tag weight consumer. No separate manifest or
provenance file is required.

Separately, `common_config._resolve_legacy_btag_efficiency_alias` implements
a narrow, **opt-in-only** escape hatch
(`AnalysisProfile.legacy_btag_efficiency_alias`) for keying an efficiency
lookup on a different (legacy) `sample_type` name than the sample's own --
e.g. a hypothetical `{"hh2b2tau": "ggh_htautau"}` mapping to reuse an
efficiency measured under the old NMSSM sample-type name. **None of the
three shipped profiles set this field** (it is `None` on all of them), so it
is inactive by default; it exists purely as a documented, tested escape
hatch for an approximation. Activating it logs a prominent `WARNING` naming
the exact alias mapping every time it fires.

### Phase-1 embedding exclusion and the Phase-2 activation checklist

**Phase 1 (today): embedding is fully excluded.**
no `sample_list/*.txt` file lists an `Embedding`-nick dataset, and
`SM_PROFILE`/`SM_BTAG_EFFICIENCY_PROFILE` keep `embedding`/`embedding_mc`
out of `DEFAULT_SAMPLES` -- they remain buildable only as explicitly-named
commissioning builds (`AVAILABLE_SAMPLES` includes them, `DEFAULT_SAMPLES`
does not), and `embedding_mc` is explicitly exempted from the validated
b-tag-payload gate (it never evaluates a b-tag MC efficiency SF).

**Phase 2 (future): activation is a review checklist, not an automated gate.**
There is no script that checks embedding activation -- whoever activates
embedding owns these points, and the code-level exclusion is only the
`DEFAULT_SAMPLES`/sample-list one above:

- which channels are enabled, and complete 2018 Run A-D coverage for each of
  them. The sample database's **registered** 2018 embedding inventory is
  **MuTau-final-state only**, so `et`/`tt` cannot be activated at all until
  channel-specific embedding datasets are registered there;
- which genuine-tau MC component each embedding component replaces, and that
  the mapping is exclusive -- no MC process may be replaced by more than one
  embedding component, or the genuine-tau contribution is double counted;
- closure tests and embedding-weight validation for every enabled channel;
- the corresponding `DEFAULT_SAMPLES` update on the SM profiles, plus adding
  the embedding nicks to every `sample_list/*.txt` file.

### Absent SM ML payload

Unlike the NMSSM resonance search, whose classifier friend
(`xyh_classifier_friend_config.py`) conditions on the resonance masses, the
SM profile has no mass-point model to evaluate at all -- it needs no
resonance-mass conditioning. `sm_ml.py` is a **Phase-1
gated stub**: it validates a small activation manifest
(`payloads/ml/sm/2018/activation.yaml`, schema: a `channels` mapping, each
entry declaring `model_file`, `transformation_file`, `fold_count`,
`event_to_fold_rule`) and, only past that gate, raises `NotImplementedError`
(no inference producer chain exists yet). **`payloads/ml/sm/2018/` does not
exist in this repo today**, so `sm_ml.py`'s `build_config` fails immediately
with a `FileNotFoundError` naming the manifest path -- this is the expected,
honest state until a trained SM ONNX model and its activation manifest are
produced and installed.

### `TauFakeFactors` path-override environment variables

`preselection.py` and `btag_efficiency.py` (both in `TauFakeFactors`)
resolve their path-like config keys with CLI-argument > environment-variable
> config-file precedence (`helper.functions.resolve_path_setting`):
`TFF_NTUPLE_PATH`, `TFF_OUTPUT_PATH`, `TFF_FILE_PATH`. **Caveat**:
`TFF_OUTPUT_PATH` is read by *both* scripts but means something different in
each -- `preselection.py`'s own output root vs. `btag_efficiency.py`'s own
(unrelated) output root and atomic-install staging area -- so exporting it
once for a whole pipeline run silently double-duties across both meanings.
See the environment-variable table and worked example in
[`docs/sm_2018_efficiency_workflow.md`](docs/sm_2018_efficiency_workflow.md)
for the full explanation and the correct way to chain the two scripts
(`--file-path`/`TFF_FILE_PATH`, not `TFF_OUTPUT_PATH`, connects them).
