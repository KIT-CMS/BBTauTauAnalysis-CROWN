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
    local crown_build_dir="${crown_dir}/build_2016postVFP$( [[ "${config}" != "nmssm_config" ]] && echo "_${config}" )"
    local crown_bin_dir="${crown_build_dir}/bin"

    # create the build directory if it does not exist
    if [[ ! -d "${crown_build_dir}" ]]; then
        mkdir -p "${crown_build_dir}"
    fi

    # define fixed parameters of the compilation process
    local analysis="bbtautau"
    local era="2016postVFP"
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
    test_files_list[data]="root://xrootd-cms.infn.it///store/data/Run2016G/SingleMuon/NANOAOD/UL2016_NanoAODv15-v1/140000/9df281fe-0689-40a5-a554-22554faea8d1.root"
    #test_files_list[nmssm_Ybb]=""
    test_files_list[ttbar]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL16NanoAODv15/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/150X_mcRun2_asymptotic_v1-v2/2810000/c598b84a-69bc-4ff4-a2c4-fe43f5c3c934.root"
    test_files_list[dyjets]="root://xrootd-cms.infn.it///store/mc/RunIISummer20UL16NanoAODv15/DYJetsToLL_LHEFilterPtZ-0To50_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/150X_mcRun2_asymptotic_v1-v1/2810000/fcf08e70-3356-49f9-b8ef-4eb890414799.root"

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
