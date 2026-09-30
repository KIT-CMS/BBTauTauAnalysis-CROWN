# Tau embedding payloads

`Run2-2018-UL-NanoAODv15/DeepTau2018v2p5_id_es_embedding2018UL.json.gz` holds the
DeepTau2018v2p5 corrections of genuine hadronic taus in 2018 UL tau-embedded events
(NanoAOD v15). The TAU POG provides no embedding file for NanoAOD v15, and the CROWN
`data/embedding/tau_id_es_embedding2018UL.json.gz` is for DeepTau2017v2p1. It is read
by `embedding_run2_v15.py` through `tau_vsjet_es_sf_file`, in place of the POG file,
for the tau energy scale (`taus.TauPtCorrectionMC`) and the vsJet SF
(`scalefactors.TauIDVsJetSF1/2`).

**Status: preliminary.** Usable for commissioning and closure checks, not for
results, until its provenance questions are answered (see below).

| | |
|---|---|
| Copied from | BBTauTauAnalysis-CROWN branch `dev_2018_bbtautau` (jvoss), `payloads/Tau_ID_ES/embedding/DeepTau2018v2p5_id_es_embedding2018UL.json.gz`, added in `1cc7bd2` (2026-09-08) |
| Identical to | `smhtt_ul` branch `tauID_SFs_dev` `9c655ec`, `Tau_SFs_DT2p5/` (jvoss, 2026-08-25, "Last used changes for v15 DT2p5 SFs") |
| Measurement | `tau_id_es_measurement/emb_tau_id_sfs_ul.sh` there (driver `make_sfs_18.sh`, tag `SFs_EMB_Run2_04_08_26`): mt tag-and-probe with embedding and an mm control region, 2D fits of rEMB x ES per DM and pT category |
| md5 | `7c684587c67674402dac1e3a871f4a3d` |
| sha256 | `2a81dbe50bd2e8b8b355747f958e566e704d0da75deb035728e99e317b004065` |

## Content

Three corrections, all version 0 without description, returning 1.0 for every
`genmatch` other than 5:

| Correction | Inputs | Used |
|---|---|---|
| `DeepTau2018v2p5VSjet` | pt, dm, genmatch, wp, wp_VSe, syst, flag | yes, `flag = "pt"` (bins 20/40/200 GeV) in et, mt and tt; `"dm"` is flat in pT |
| `tau_energy_scale` | pt, eta, dm, genmatch, id, wp, wp_VSe, syst | yes (`tau_ES_json_name`), pT bins 20/40/200 GeV |
| `tau_energy_scale_dm_binned` | same | no; it pairs with the vsJet `flag = "dm"` |

Axes: `wp` Medium, Tight; `wp_VSe` VVLoose, Tight; `syst` nom, up, down; the pT
and |eta| bins clamp. The analysis reads Medium with vsEle Tight in et and VVLoose
in mt and tt. DM11 equals DM10 everywhere, because the measurement fits one 3-prong
category (DM1011); the embedding shifts vary DM10 and DM11 separately (one decay mode per
shift, see `variations/taus.py`), so the two are to be correlated downstream.

## The 40 GeV step of the energy scale

`tau_energy_scale` changes at a raw tau pT of 40 GeV, and each `CMS_scale_t_emb_*` shift
moves both pT bins of its decay mode together. For Medium/VVLoose the corrected pT has a
hole just below 40 GeV: DM0 38.9-39.3 GeV (0.972 -> 0.983), DM1 37.7-39.8 GeV
(0.943 -> 0.994), DM10 38.2-39.5 GeV (0.955 -> 0.988). For Medium/Tight (et): DM1
37.9-39.4 GeV, DM10 38.4-39.7 GeV, while DM0 overlaps (37.5-37.8 GeV, 0.946 -> 0.939).
No genuine embedded tau of that decay mode ends up in its hole; this is the
precedent of jvoss's production (user decision U1 of 2026-09-30). Check: the
tau pT distribution per decay mode between 36 and 42 GeV.

## Open questions

- Which n-tuples (v15 embedding vs v15 data) and CROWN configuration the measurement
  used, and what up/down contain (statistical, systematic, total).
- Why the Medium/VVLoose vsJet uncertainty is large: with `flag = "pt"` above 40 GeV
  DM1 is 1.056 +0.318/-0.369 and DM0 1.079 +0.091/-0.175.
- The energy scale shifts of -3 to -6 % (Medium/VVLoose: DM0 0.972/0.983, DM1
  0.943/0.994, DM10 0.955/0.988 below/above 40 GeV) with up to +-9 % uncertainty,
  against +3.7 % for DM0 below 40 GeV in the official DeepTau2017v2p1 file.

KingMaker's framework-tarball hash does not cover `payloads/`: set
`force_repack_tarball` after replacing this file, and produce under a new tag.
