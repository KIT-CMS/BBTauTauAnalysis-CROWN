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
    local config="${5:-nmssm_config}"

    # get the CROWN directories
    local crown_dir="$( cd "${this_dir}/../../.." && pwd )"
    local crown_build_dir="${crown_dir}/build_2017$( [[ "${config}" != "nmssm_config" ]] && echo "_${config}" )"
    local crown_bin_dir="${crown_build_dir}/bin"

    # create the build directory if it does not exist
    if [[ ! -d "${crown_build_dir}" ]]; then
        mkdir -p "${crown_build_dir}"
    fi

    # define fixed parameters of the compilation process
    local analysis="bbtautau"
    local era="2017"
    local shifts="none"
    local threads="$( [[ "${debug}" == true ]] && echo "1" || echo "4" )"
    local cores="16"

    # split the samples string into an array
    if [[ "${samples}" == "all" ]]; then
        samples="data,ttbar,dyjets"  # nmssm_Ybb
    fi
    declare -a samples_list
    IFS="," read -ra samples_list <<< "${samples}"

    # set scopes if 'all' is specified
    if [[ "${channels}" == "all" ]]; then
        channels="et,mt,tt"
    fi

    # build associative array of test files for different sample types
    declare -A test_files_list
    test_files_list[data]="root://xrootd-cms.infn.it///store/data/Run2017B/SingleMuon/NANOAOD/UL2017_NanoAODv15-v1/2520000/b79487bf-8b58-43e5-86a5-c11fce8e2c04.root"
    #test_files_list[nmssm_Ybb]=""
    test_files_list[ttbar]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL17NanoAODv15/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/150X_mc2017_realistic_v1-v2/2560000/fadbd501-3c37-43dd-a6b0-00057ded824e.root"
    test_files_list[dyjets]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL17NanoAODv15/DYJetsToLL_LHEFilterPtZ-0To50_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/150X_mc2017_realistic_v1-v1/130000/22e4168b-3392-43a2-96b2-9b4db9aebeb3.root"

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
