#!/usr/bin/env bash


main () {
    # Local path variables
    local is_zsh="$( [[ -n "${ZSH_VERSION}" ]] && echo "true" || echo "false" )"
    local this_file="$( [[ "${is_zsh}" ]] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]:-$0}" )"
    local this_dir="$( cd "$( dirname "${this_file}" )" && pwd )"
    local crown_root="$( dirname "$( dirname "$(dirname "${this_dir}" )" )" )"
    local analysis_root="$(dirname "${this_dir}" )"

    # Set up LCG stack environment
    source "${crown_root}/init.sh" -c "lcg"

    # Add CROWN root directory to PYTHONPATH
    export PYTHONPATH="${crown_root}:${PYTHONPATH}"
}


main "${@}"
