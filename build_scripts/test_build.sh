#!/usr/bin/env bash

# Usage: bash test_build.sh ERA [samples [channels [debug [steps [config]]]]]
main() {
    local era="${1:-}"
    local default_samples
    local -A test_files
    case "$era" in
        2016postVFP)
            default_samples="data,ttbar,dyjets"
            test_files[data]="root://xrootd-cms.infn.it///store/data/Run2016G/SingleMuon/NANOAOD/UL2016_NanoAODv15-v1/140000/9df281fe-0689-40a5-a554-22554faea8d1.root"
            test_files[ttbar]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL16NanoAODv15/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/150X_mcRun2_asymptotic_v1-v2/2810000/c598b84a-69bc-4ff4-a2c4-fe43f5c3c934.root"
            test_files[dyjets]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL16NanoAODv15/DYJetsToLL_LHEFilterPtZ-0To50_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/150X_mcRun2_asymptotic_v1-v1/2810000/fcf08e70-3356-49f9-b8ef-4eb890414799.root"
            ;;
        2016preVFP)
            default_samples="data,ttbar,dyjets"
            test_files[data]="root://xrootd-cms.infn.it///store/data/Run2016C/SingleMuon/NANOAOD/HIPM_UL2016_NanoAODv15-v1/110000/e43c6b89-599b-4ee5-95f1-23cc443abbf0.root"
            test_files[ttbar]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL16NanoAODAPVv15/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/150X_mcRun2_asymptotic_preVFP_v1-v2/130000/72cf9bbd-577b-47fc-b559-1a105be8d763.root"
            test_files[dyjets]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL16NanoAODAPVv15/DYJetsToLL_LHEFilterPtZ-0To50_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/150X_mcRun2_asymptotic_preVFP_v1-v1/2810000/031a422c-02eb-4f32-8154-f8d9418249e1.root"
            ;;
        2017)
            default_samples="data,ttbar,dyjets"
            test_files[data]="root://xrootd-cms.infn.it///store/data/Run2017B/SingleMuon/NANOAOD/UL2017_NanoAODv15-v1/2520000/b79487bf-8b58-43e5-86a5-c11fce8e2c04.root"
            test_files[ttbar]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL17NanoAODv15/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/150X_mc2017_realistic_v1-v2/2560000/fadbd501-3c37-43dd-a6b0-00057ded824e.root"
            test_files[dyjets]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL17NanoAODv15/DYJetsToLL_LHEFilterPtZ-0To50_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/150X_mc2017_realistic_v1-v1/130000/22e4168b-3392-43a2-96b2-9b4db9aebeb3.root"
            ;;
        2018)
            default_samples="data,ttbar,dyjets"
            test_files[data]="root://xrootd-cms.infn.it///store/data/Run2018A/SingleMuon/NANOAOD/UL2018_NanoAODv15-v2/2520000/b29840f2-a936-4cea-be5a-a0d78e2b307e.root"
            test_files[ttbar]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL18NanoAODv15/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/150X_mc2018_realistic_v1-v2/2810000/3ecaec0b-69a7-4502-904e-0f0b19be96a3.root"
            test_files[dyjets]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL18NanoAODv15/DYJetsToLL_LHEFilterPtZ-0To50_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/150X_mc2018_realistic_v1-v1/2810000/3aaff2df-d67e-4c87-b09c-26515fe4ad7c.root"
            ;;
        2022postEE)
            default_samples="data,nmssm_Ybb,ttbar,dyjets_amcatnlo_ll"
            test_files[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2022E/Muon/NANOAOD/22Sep2023-v1/40000/cb3afe1f-699f-4be6-a1ed-dd6fd0b2ca81.root"
            test_files[nmssm_Ybb]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer22EENanoAODv12/NMSSM_XtoYHto2B2Tau_MX-1000_MY-100_TuneCP5_13p6TeV_madgraph-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_postEE_v6-v2/2830000/da15832e-6657-4d0c-bfb3-7641b5b6bc9e.root"
            test_files[ttbar]="root://xrootd-cms.infn.it//store/mc/Run3Summer22EENanoAODv12/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_postEE_v6_ext1-v2/50000/fce23976-3083-4220-ab86-abfde0dc2c2f.root"
            test_files[dyjets_amcatnlo_ll]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer22EENanoAODv12/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_postEE_v6-v2/40000/ffcd4b23-808d-43e5-9b08-46506cbccc75.root"
            ;;
        2022preEE)
            default_samples="ttbar,data,dyjets_amcatnlo_ll"
            test_files[ttbar]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer22NanoAODv12/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_v5-v2/2520000/66b834d6-61f7-4109-b5ae-54a150d4814b.root"
            test_files[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2022C/EGamma/NANOAOD/22Sep2023-v1/2530000/009621ee-c6b2-4043-99c3-7cb4ab2c7264.root"
            test_files[dyjets_amcatnlo_ll]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer22NanoAODv12/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_v5-v2/2520000/1e9fd5a7-16b9-4dfc-92a1-1b2b03631dde.root"
            ;;
        2023postBPix)
            default_samples="data,nmssm_Ybb,ttbar,dyjets_amcatnlo_ll"
            test_files[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2023D/Muon0/NANOAOD/22Sep2023_v1-v1/30000/cb3be378-82f5-4585-aa67-d0e9f430b0ea.root"
            test_files[ttbar]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer23BPixNanoAODv12/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/130X_mcRun3_2023_realistic_postBPix_v2-v3/2560000/edcc614d-8bbe-4cd5-91b8-d5c2e82bb1fc.root"
            test_files[dyjets_amcatnlo_ll]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer23BPixNanoAODv12/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/130X_mcRun3_2023_realistic_postBPix_v2-v3/2820000/6f09e67e-04a8-46cb-a85f-b430d84e71e1.root"
            ;;
        2023preBPix)
            default_samples="data,nmssm_Ybb,ttbar,dyjets_amcatnlo_ll"
            test_files[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2023C/Muon0/NANOAOD/22Sep2023_v1-v1/30000/0ceac210-9c0b-49a3-baea-ea57c85de9d4.root"
            test_files[ttbar]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer23NanoAODv12/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/130X_mcRun3_2023_realistic_v14-v2/70000/428c6754-4ad2-4c2f-8ec6-4f2b5dc60758.root"
            test_files[dyjets_amcatnlo_ll]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer23NanoAODv12/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/130X_mcRun3_2023_realistic_v14-v3/2820000/21ad2859-37a5-436b-82f9-51b55cf93ba0.root"
            ;;
        2024)
            default_samples="data,nmssm_Ybb,ttbar,dyjets_amcatnlo"
            test_files[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2024C/Muon0/NANOAOD/MINIv6NANOv15-v1/2530000/677e3bb0-8199-4ffb-83af-165410a7b7a6.root"
            test_files[nmssm_Ybb]="root://xrootd-cms.infn.it///store/mc/RunIII2024Summer24NanoAODv15/NMSSM-XtoYHto2B2Tau_Par-MX-1200-MY-800_TuneCP5_13p6TeV_madgraph-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v2/2540000/31703286-9c3f-4a8d-8265-b99c8e0ec2ed.root"
            test_files[ttbar]="root://xrootd-cms.infn.it//store/mc/RunIII2024Summer24NanoAODv15/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v3/2810000/f60b4a6c-2801-43b0-b542-6d933a71a396.root"
            test_files[dyjets_amcatnlo]="root://xrootd-cms.infn.it//store/mc/RunIII2024Summer24NanoAODv15/DYto2Tau-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v4/130000/12ae785f-14fc-4685-a6c2-4241ac503bc9.root"
            test_files[rem_ttbar]="root://cmsdcache-kit-disk.gridka.de//store/mc/RunIII2024Summer24NanoAODv15/TTLL_Bin-MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v2/2810000/8185b69c-f54a-41d7-8bb3-07ea00cbb0ee.root"
            test_files[triboson]="root://cmsdcache-kit-disk.gridka.de//store/mc/RunIII2024Summer24NanoAODv15/WWZ-4F_TuneCP5_13p6TeV_amcatnlo-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v2/100000/bfedeaeb-cf7c-4027-a295-9962aed73a4a.root"
            ;;
        2025)
            default_samples="data,nmssm_Ybb,ttbar,dyjets_amcatnlo"
            test_files[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2025C/Muon0/NANOAOD/PromptReco-v1/000/392/295/00000/5f01b0be-3b57-49bc-bd9c-b2489dd21a29.root"
            test_files[nmssm_Ybb]="root://cmsdcache-kit-disk.gridka.de//store/mc/RunIII2024Summer24NanoAODv15/NMSSM-XtoYHto2B2Tau_Par-MX-1200-MY-800_TuneCP5_13p6TeV_madgraph-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v2/2540000/31703286-9c3f-4a8d-8265-b99c8e0ec2ed.root"
            test_files[ttbar]="root://cmsdcache-kit-disk.gridka.de//store/mc/RunIII2024Summer24NanoAODv15/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v3/2810000/f60b4a6c-2801-43b0-b542-6d933a71a396.root"
            test_files[dyjets_amcatnlo]="root://cmsdcache-kit-disk.gridka.de//store/mc/RunIII2024Summer24NanoAODv15/DYto2Tau-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v4/130000/12ae785f-14fc-4685-a6c2-4241ac503bc9.root"
            ;;
        *)
            echo "Unsupported test-build era '$era'." >&2
            return 2
            ;;
    esac
    shift
    local samples="${1:-all}"
    local channels="${2:-all}"
    local debug="${3:-false}"
    local steps="${4:-all}"
    local config="${5:-nmssm_config}"
    local threads=4
    if [[ "$samples" == all ]]; then samples="$default_samples"; fi
    if [[ "$channels" == all ]]; then channels="et,mt,tt"; fi
    if [[ "$debug" == true ]]; then threads=1; fi

    local crown_dir build_dir
    crown_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd) || return 1
    build_dir="$crown_dir/build_$era"
    if [[ "$config" != nmssm_config ]]; then build_dir+="_$config"; fi
    mkdir -p "$build_dir" || return 1

    if [[ "$steps" == build || "$steps" == all ]]; then
        (
            cd "$build_dir" &&
            cmake .. -DANALYSIS=bbtautau -DCONFIG="$config" -DERAS="$era" -DSAMPLES="$samples" \
                -DSCOPES="$channels" -DSHIFTS=none -DTHREADS="$threads" -DDEBUG="$debug" &&
            make -j 16 &&
            make install
        ) || return $?
    fi

    if [[ "$steps" == run_binary || "$steps" == all ]]; then
        local -a samples_list
        local sample
        IFS=, read -ra samples_list <<< "$samples"
        for sample in "${samples_list[@]}"; do
            if [[ -n "${test_files[$sample]}" ]]; then
                (
                    cd "$build_dir/bin" &&
                    "./${config}_${sample}_${era}" "output_${sample}.root" "${test_files[$sample]}"
                ) || return $?
            fi
        done
    fi
}

main "$@"
