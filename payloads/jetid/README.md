# Jet ID payloads

`Run2-2018-UL-NanoAODv15/jetid.json.gz` is the correctionlib jet ID for 2018
Ultra Legacy PUPPI jets as stored in NanoAOD v15, in the layout of the JME POG
Run 3 `jetid.json.gz` files: corrections `AK4PUPPI_Tight`,
`AK4PUPPI_TightLeptonVeto`, `AK8PUPPI_Tight`, `AK8PUPPI_TightLeptonVeto`,
nine inputs (`eta`, `chHEF`, `neHEF`, `chEmEF`, `neEmEF`, `muEF`,
`chMultiplicity`, `neMultiplicity`, `multiplicity`), output 1 or 0. It is
consumed by `producers/jets.py:JetIDFromCorrectionlib` through
`ak4jet_id_file` on the Run-2 NanoAOD-v15 input path (one campaign directory
per era; only 2018 is generated so far), yielding the usual 0/2/6 jet ID.

| | |
|---|---|
| Generator | https://gitlab.etp.kit.edu/hh-nonresonant/jetid-payloads, jetid-payloads 0.1.0, campaign `Run2-2018-UL-NanoAODv15` |
| Cuts | CMSSW_10_6_29 `PFJetIDSelectionFunctor`, version `RUN2ULPUPPI` (2017/2018 UL PUPPI), qualities TIGHT and TIGHTLEPVETO |
| sha256 | `06d59fda684e3919effb7be07f441e5f67a4722cf53e58e1b01b7c19fcca417c` |
| Consumer requirement | correctionlib >= 2.6 (binning on integer inputs) |

The cut table, the encoding of strict inequalities in correctionlib's
half-open binning, and the tests live in the generator repository. To verify
this copy, run `generate_jetid_payloads --check --output-dir <dir>` there with
`<dir>` containing `Run2-2018-UL-NanoAODv15/jetid.json.gz`.

KingMaker's framework-tarball hash does not cover `payloads/`: set
`force_repack_tarball` after adding or replacing this file.
