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
    local crown_build_dir="${crown_dir}/build_2023preBPix$( [[ "${config}" != "nmssm_config" ]] && echo "_${config}" )"
    local crown_bin_dir="${crown_build_dir}/bin"

    # create the build directory if it does not exist
    if [[ ! -d "${crown_build_dir}" ]]; then
        mkdir -p "${crown_build_dir}"
    fi

    # define fixed parameters of the compilation process
    local analysis="bbtautau"
    local era="2023preBPix"
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
    test_files_list[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2023C/Muon0/NANOAOD/22Sep2023_v1-v1/30000/0ceac210-9c0b-49a3-baea-ea57c85de9d4.root"
    #test_files_list[nmssm_Ybb]=""
    test_files_list[ttbar]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer23NanoAODv12/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/130X_mcRun3_2023_realistic_v14-v2/70000/428c6754-4ad2-4c2f-8ec6-4f2b5dc60758.root"
    test_files_list[dyjets_amcatnlo_ll]="root://cmsdcache-kit-disk.gridka.de//store/mc/Run3Summer23NanoAODv12/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/130X_mcRun3_2023_realistic_v14-v3/2820000/21ad2859-37a5-436b-82f9-51b55cf93ba0.root"

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
