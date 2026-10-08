# Recoil correction payloads

`Type1_PuppiMET_2018_zptbins.root` is the 2018 PuppiMET recoil correction of the Run-2
NanoAOD-v15 inputs (`recoil_correction_file`, `met::RecoilCorrection`). There is no UL or v15
recoil correction for Run 2, so it is the legacy file with one histogram fixed.

| | |
|---|---|
| Copied from | CROWN `data/recoil_corrections/Type1_PuppiMET_2018.root` (added in `98d41e9`, identical to KIT-CMS/RecoilCorrections), md5 `bccc19c42c55680351bb7b746e0d8857` |
| Fixed | `ZPtBinsH`: bin edges 0, 10, 20, 30, 50, 1000 GeV instead of 0, 1, 2, 3, 4, 5, as its labels `Pt0to10` ... `PtGt50` and the original HTT file `TypeI-PFMet_Run2018.root` have them; `RecoilCorrector` reads the edges, so every event with a generator Z pT of 4 GeV or more got the `PtGt50` correction |
| Unchanged | all other 122 objects (the `recoilZParal/Perp` functions and histograms, `projH`, `nJetBinsH`) |
| md5 | `77815669430f98830c3d4b2ec65efb67` |

The copy was made in ROOT `UPDATE` mode, replacing only `ZPtBinsH`:

```python
new = ROOT.TH1D("ZPtBinsH", "", 5, array("d", [0, 10, 20, 30, 50, 1000]))
for i, label in enumerate(["Pt0to10", "Pt10to20", "Pt20to30", "Pt30to50", "PtGt50"], 1):
    new.GetXaxis().SetBinLabel(i, label)
new.Write("ZPtBinsH", ROOT.TObject.kOverwrite)
```

The 2016 and 2017 files in `data/recoil_corrections/` have the same defect.

KingMaker's framework-tarball hash does not cover `payloads/`: set `force_repack_tarball` after
adding or replacing this file.
