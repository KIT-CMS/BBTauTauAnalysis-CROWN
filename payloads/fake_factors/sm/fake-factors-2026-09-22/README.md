# SM 2018 fake factors, 2026-09-22 (commissioning only)

`2018/` holds the six TauFakeFactors payloads of the SM HH &rightarrow; bb&tau;&tau; analysis that
`sm_fake_factors.py` reads (`SM_PAYLOAD_DIRS`). They are for commissioning the fake-factor friend:
the results are not final, and **the shifts must not be used as uncertainties in datacards**; they
serve only to check that the friend is wired up correctly (see the defects below). A payload derived
with ShapeSmith on the embedding production replaces them, in a new dated directory.

| | |
|---|---|
| Source | jvoss, branch `dev_2018_bbtautau`, commit `1570b43`, `payloads/fake_factors/sm/2018/`; copied byte for byte with `git show 1570b43:payloads/fake_factors/sm/2018/<file>` (the TauFakeFactors workdir copy of `FF_corrections_mt.json.gz` was rewritten on 2026-09-29: same content, other gzip bytes) |
| Derivation | 2026-09-22, TauFakeFactors copy `/work/jvoss/FF_Updated`, configuration `configs/non_res_HH/2018` (not a git repository), workdir `ff_upart_17_09_26_sda_nom_emb` |
| Input n-tuples | `upart_17_09_26_sda_nom` (jvoss), `use_embedding: true` |
| Model | QCD + ttbar; the fractions carry the processes `QCD` and `ttbar` (keys `frac_QCD`, `frac_ttbar_J`) |
| Regions | SR `id_tau_vsJet_Medium`, AR `id_tau_vsJet_VVVLoose && !id_tau_vsJet_Medium` (as ShapeSmith `TAU_VS_JET_WP`, `TAU_VS_JET_LOOSE_WP`) |
| Non-closure | coarse: 17 shift pairs per leg are selected (6 fake factor, 2 fraction, 3 DR&rightarrow;SR, 6 closure) |

| File | md5 | sha256 |
|---|---|---|
| `fake_factors_et.json.gz` | `9a5233ccb76d4b89fb2a7e8aaf29097a` | `df0b3aa2e740e77bc2858881f227f26f6a38ea3809b1cdea36e897eeddf094d9` |
| `fake_factors_mt.json.gz` | `8ae08beb17d708d6727a95c8c19365f4` | `2977a4ff6b58e8d35c6d3b3a17362523e3a03e0a558f547a88def5c088a91b09` |
| `fake_factors_tt.json.gz` | `701e7da5772d274b59e7bdaabdb6a183` | `da6d211ae128a1fddf3cd2b815fd19f4dc353df220320d751a766c822306e4db` |
| `FF_corrections_et.json.gz` | `8ae21b81e20fe91f01d86b2115786d06` | `ce685108ea8236f0f7db59e01a78549cc5f45d5dc4a9c4763f0a8b9bceb070cd` |
| `FF_corrections_mt.json.gz` | `d59c3fb578f7580c3f7206d70756da4b` | `98eb9e144a733d2600cc5588ab4864caab4e66981065f200bf18f377318f2f8f` |
| `FF_corrections_tt.json.gz` | `5af0ad7661d3a7de06bf465c9897881e` | `6564ba237d6393d46615a93370719f765437737777b55c4cbf13d2a89781d507` |

## Known defects

- Derived with the embedding before the SM 2018 embedding rework (wrong et vsEle working point, tau
  energy-scale working point and tt trigger bits) and on n-tuples without the JER, JES and FastMTT
  fixes.
- QCD `SystMCShift` outliers (review of 2026-09-30): mt `iso_1` closure up to 170x nominal
  (`iso_1` 0.038-0.055), et DR&rightarrow;SR up to 465x (`pt_tautau` 110-120 GeV), et `mt_tot`
  closure 20x, mt `pt_1` closure Down 20x, mt DR&rightarrow;SR 7.8x.
- The global QCD non-closure shifts move all stack members together (coarse): at typical mt points
  `CorrStatShiftUp` is x4 to x20, `CorrStatShiftDown` about 0.
- `ttbarSystMCShift` (fake factor) and `ttbar{,_subleading}_non_closure_CorrSystMCShift` equal the
  nominal in et, mt and tt: TauFakeFactors has no MC-subtraction variation for ttbar.
- Friend commissioning (2026-09-30, one Run2018A data file per channel of `sm2018_binned_v4`),
  shifted/nominal maximum: mt `QCD_non_closure_CorrSystMCShiftUp` 2370, `..._CorrStatShiftUp` 20,
  `QCD_DR_SR_CorrSystMCShiftUp` 5.6; et `QCD_DR_SR_CorrSystMCShiftUp` 256,
  `QCD_non_closure_CorrStatShiftUp` 103 (median 4.7), `QCD_non_closure_CorrSystMCShiftUp` 65. All tt
  shifts stay within 0.63-1.53.

KingMaker's framework-tarball hash does not cover `payloads/`, and friend outputs are keyed by
production and friend tag only: friends made with a new payload need `force_repack_tarball` and a
new `--friend-tag`.
