#!/usr/bin/env bash


main () {
    # get paths of the script and its directory
    local this_file="$( echo "${BASH_SOURCE[0]:-${0}}" )"
    local this_dir="$( cd "$( dirname "${this_file}" )" && pwd )"

    # get input parameters from the command line
    local samples="${1:-all}"
    local channels="${2:-all}"
    local debug="${3:-false}"
    local steps="${4:-all}"

    # get the CROWN directories
    local crown_dir="$( cd "${this_dir}/../../.." && pwd )"
    local crown_build_dir="${crown_dir}/build_2022postEE"
    local crown_bin_dir="${crown_build_dir}/bin"

    # create the build directory if it does not exist
    if [[ ! -d "${crown_build_dir}" ]]; then
        mkdir -p "${crown_build_dir}"
    fi

    # define fixed parameters of the compilation process
    local analysis="xyh_bbtautau"
    local config="nmssm_config"
    local era="2022postEE"
    local shifts="none"
    local threads="$( [[ "${debug}" == true ]] && echo "1" || echo "4" )"
    local cores="16"

    # split the samples string into an array
    if [[ "${samples}" == "all" ]]; then
        samples="data,nmssm_Ybb,ttbar,dyjets_amcatnlo_ll"
    fi
    declare -a samples_list
    IFS="," read -ra samples_list <<< "${samples}"

    # set scopes if 'all' is specified
    if [[ "${channels}" == "all" ]]; then
        channels="et,mt,tt"
    fi

    # build associative array of test files for different sample types
    declare -A test_files_list
    test_files_list[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2022E/Muon/NANOAOD/22Sep2023-v1/40000/cb3afe1f-699f-4be6-a1ed-dd6fd0b2ca81.root"
    test_files_list[nmssm_Ybb]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer22EENanoAODv12/NMSSM_XtoYHto2B2Tau_MX-1000_MY-100_TuneCP5_13p6TeV_madgraph-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_postEE_v6-v2/2830000/da15832e-6657-4d0c-bfb3-7641b5b6bc9e.root"
    test_files_list[ttbar]="root://xrootd-cms.infn.it//store/mc/Run3Summer22EENanoAODv12/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_postEE_v6_ext1-v2/50000/fce23976-3083-4220-ab86-abfde0dc2c2f.root"
    test_files_list[dyjets_amcatnlo_ll]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer22EENanoAODv12/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_postEE_v6-v2/40000/ffcd4b23-808d-43e5-9b08-46506cbccc75.root"

    # configure and compile the project
    if [[ "${steps}" == "build" || "${steps}" == "all" ]]; then
        (
            cd "${crown_build_dir}" \
            && cmake .. -DANALYSIS="${analysis}" -DCONFIG="${config}" -DERAS="${era}" -DSAMPLES="${samples}" -DSCOPES="${channels}" -DSHIFTS="${shifts}" -DTHREADS="${threads}" -DDEBUG="${debug}" \
            && make -j "${cores}" \
            && make install
        ) || return "${?}"
    fi

    # test the compiled binary with a test file for each declared sample
    if [[ "${steps}" == "run_binary" || "${steps}" == "all" ]]; then
        for sample in "${samples_list[@]}"; do
            if [[ -n "${test_files_list[${sample}]}" ]]; then
                # specify paths of the input and the output files
                test_file="${test_files_list[${sample}]}"
                output_file="output_${sample}.root"

                # test the binary
                (
                    cd "${crown_bin_dir}" \
                    && "./${config}_${sample}_${era}" "${output_file}" "${test_file}"
                ) || return "${?}"

            fi
        done
    fi
}


main "${@}"
