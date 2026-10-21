# Jet ID payloads

`Run2-<era>-UL-NanoAODv15/jetid.json.gz` is the correctionlib jet ID for the
Ultra Legacy PUPPI jets of one Run-2 era as stored in NanoAOD v15, in the
layout of the JME POG Run 3 `jetid.json.gz` files: corrections
`AK4PUPPI_Tight`, `AK4PUPPI_TightLeptonVeto`, `AK8PUPPI_Tight`,
`AK8PUPPI_TightLeptonVeto`, nine inputs (`eta`, `chHEF`, `neHEF`, `chEmEF`,
`neEmEF`, `muEF`, `chMultiplicity`, `neMultiplicity`, `multiplicity`), output
1 or 0. It is consumed by `producers/jets.py:JetIDFromCorrectionlib` through
`ak4jet_id_file` on the Run-2 NanoAOD-v15 input path (one campaign directory
per era), yielding the usual 0/2/6 jet ID.

| Campaign | Cut set | Payload version | sha256 |
|---|---|---|---|
| `Run2-2016preVFP-UL-NanoAODv15` | `RUN2UL16PUPPI` | 0.2.0 | `6a39e561d9a6c658ccc73ac0d226479ad15c0132e45fbbf2f122e1d5ff759f22` |
| `Run2-2016postVFP-UL-NanoAODv15` | `RUN2UL16PUPPI` | 0.2.0 | `5c85477d44142350dde373d88e470494ba72804fb9c49a361db425bcf1eaa650` |
| `Run2-2017-UL-NanoAODv15` | `RUN2ULPUPPI` | 0.2.0 | `b9fca0a10c139a51dd24a657a0225c73fe3f031aee7a37843c90de4f8a206d80` |
| `Run2-2018-UL-NanoAODv15` | `RUN2ULPUPPI` | 0.1.0 | `06d59fda684e3919effb7be07f441e5f67a4722cf53e58e1b01b7c19fcca417c` |

| | |
|---|---|
| Generator | https://gitlab.etp.kit.edu/hh-nonresonant/jetid-payloads, jetid-payloads 0.2.0 (branch `feat-v7-run2`, commit `cbdaf82`); the 2018 file is byte-identical to the one of jetid-payloads 0.1.0 |
| `RUN2ULPUPPI` (2017, 2018) | CMSSW_10_6_29 `PFJetIDSelectionFunctor`, version `RUN2ULPUPPI`, qualities TIGHT and TIGHTLEPVETO |
| `RUN2UL16PUPPI` (2016) | JetID13TeVUL (r22) and JMAR "2016 AK4 PUPPI", Tight and TightLeptonVeto: charged cuts up to \|&eta;\| &le; 2.4; 2.4 < \|&eta;\| &le; 2.7 NHF < 0.98 and NEF < 0.99 without lepton-veto cuts; 2.7 < \|&eta;\| &le; 3.0 `neMultiplicity` &ge; 1; \|&eta;\| > 3.0 NEF < 0.90 and `neMultiplicity` > 2 |
| Deviation from CMSSW | 2016, 2.7 < \|&eta;\| &le; 3.0: `neMultiplicity` &ge; 1 as the JME recipe for v15, where CMSSW_10_6_29 has > 1 (18 % of the jets in that region of 2016B data have exactly one neutral) |
| Consumer requirement | correctionlib >= 2.6 (binning on integer inputs) |

The cut tables, the encoding of strict inequalities in correctionlib's
half-open binning, and the tests live in the generator repository. To verify
these copies, run `python3 -m jetid_payloads --check --output-dir <dir>` there
with `<dir>` pointing at this directory. Once JME publishes an official Run-2
v15 `jetid.json.gz`, switch to it.

KingMaker's framework-tarball hash does not cover `payloads/`: set
`force_repack_tarball` after adding or replacing these files.
