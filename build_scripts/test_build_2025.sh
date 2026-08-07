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
    local crown_build_dir="${crown_dir}/build_2025"
    local crown_bin_dir="${crown_build_dir}/bin"

    # create the build directory if it does not exist
    if [[ ! -d "${crown_build_dir}" ]]; then
        mkdir -p "${crown_build_dir}"
    fi

    # define fixed parameters of the compilation process
    local analysis="bbtautau"
    local config="nmssm_config"
    local era="2025"
    local shifts="none"
    local threads="$( [[ "${debug}" == true ]] && echo "1" || echo "4" )"
    local cores="16"

    # split the samples string into an array
    if [[ "${samples}" == "all" ]]; then
        samples="data,nmssm_Ybb,ttbar,dyjets_amcatnlo"
    fi
    declare -a samples_list
    IFS="," read -ra samples_list <<< "${samples}"

    # set scopes if 'all' is specified
    if [[ "${channels}" == "all" ]]; then
        channels="et,mt,tt"
    fi

    # build associative array of test files for different sample types
    declare -A test_files_list
    test_files_list[data]="root://cmsdcache-kit-disk.gridka.de//store/data/Run2025C/Muon0/NANOAOD/PromptReco-v1/000/392/295/00000/5f01b0be-3b57-49bc-bd9c-b2489dd21a29.root"
    test_files_list[nmssm_Ybb]="root://cmsdcache-kit-disk.gridka.de//store/mc/RunIII2024Summer24NanoAODv15/NMSSM-XtoYHto2B2Tau_Par-MX-1200-MY-800_TuneCP5_13p6TeV_madgraph-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v2/2540000/31703286-9c3f-4a8d-8265-b99c8e0ec2ed.root"
    test_files_list[ttbar]="root://cmsdcache-kit-disk.gridka.de//store/mc/RunIII2024Summer24NanoAODv15/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v3/2810000/f60b4a6c-2801-43b0-b542-6d933a71a396.root"
    test_files_list[dyjets_amcatnlo]="root://cmsdcache-kit-disk.gridka.de//store/mc/RunIII2024Summer24NanoAODv15/DYto2Tau-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v4/130000/12ae785f-14fc-4685-a6c2-4241ac503bc9.root"

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
