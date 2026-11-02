#!/usr/bin/env bash
# Compile check of the generated C++ code (v7 spec C17): one MC configuration per
# production in every Run-2 era. Code generation alone (pytest, the dry run) never
# compiles, so a changed core signature only shows in the build; run this after every
# CROWN pin change and before a production.
#
# Usage: scripts/compile_check.sh <build dir> [jobs] [shifts]
#
#   build dir  an empty directory outside the CROWN tree (one sub-directory per build)
#   jobs       make jobs (default 8)
#   shifts     -DSHIFTS of the tau-ID measurement build (default none; P1 uses all)
#
# The builds run in the CROWN container (crown:V0.1 from /cvmfs/unpacked.cern.ch)
# through apptainer; with CROWN_IN_CONTAINER=1 they run in the current environment.
# SPDLOG_PREBUILT_LIB/SPDLOG_PREBUILT_INCLUDE are passed on if set (otherwise CMake
# fetches spdlog). The builds are -DOPTIMIZED=false and are not run.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    sed -n '2,17p' "$0"
    exit 2
fi

this_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
analysis_root="$(dirname "${this_dir}")"
crown_root="$(cd "${analysis_root}/../.." && pwd)"
build_root="$(mkdir -p "$1" && cd "$1" && pwd)"
jobs="${2:-8}"
tm_shifts="${3:-none}"
image="/cvmfs/unpacked.cern.ch/registry.hub.docker.com/kingmakerimages/crown:V0.1"
eras="2016preVFP,2016postVFP,2017,2018"

# eras whose embedding tau ID/ES payload exists (sm_config builds their embedding)
embedding_eras="$(cd "${crown_root}" && python3 -c '
from analysis_configurations.bbtautau.embedding_run2_v15 import TAU_EMBEDDING_ID_ES_PAYLOADS
print("eras=" + ",".join(sorted(TAU_EMBEDDING_ID_ES_PAYLOADS)))' 2>/dev/null \
    | sed -n 's/^eras=//p' || true)"
embedding_eras="${embedding_eras:-2018}"

# name config eras samples scopes shifts
builds=(
    "sm_config_ttbar sm_config ${eras} ttbar et,mt,tt,em,ee,mm none"
    "sm_btag_efficiency_config_ttbar sm_btag_efficiency_config ${eras} ttbar et,mt,tt,em,ee,mm none"
    "sm_tau_id_measurement_config_dyjets sm_tau_id_measurement_config ${eras} dyjets mt,mm ${tm_shifts}"
    "sm_config_embedding sm_config ${embedding_eras} embedding et,mt,tt none"
)

spdlog=()
binds=(-B /cvmfs -B "${crown_root}" -B "${build_root}")
if [[ -n "${SPDLOG_PREBUILT_LIB:-}" ]]; then
    spdlog=(-DSPDLOG_PREBUILT_LIB="${SPDLOG_PREBUILT_LIB}"
            -DSPDLOG_PREBUILT_INCLUDE="${SPDLOG_PREBUILT_INCLUDE}")
    binds+=(-B "$(dirname "${SPDLOG_PREBUILT_LIB}")" -B "${SPDLOG_PREBUILT_INCLUDE}")
fi

run() {
    if [[ "${CROWN_IN_CONTAINER:-0}" == "1" ]]; then
        bash -c "$1"
    else
        apptainer exec "${binds[@]}" "${image}" bash -c "$1"
    fi
}

failed=0
for build in "${builds[@]}"; do
    read -r name config build_eras samples scopes shifts <<< "${build}"
    directory="${build_root}/${name}"
    mkdir -p "${directory}"
    command="cmake -S '${crown_root}' -B '${directory}' -DANALYSIS=bbtautau \
        -DCONFIG=${config} -DERAS=${build_eras} -DSAMPLES=${samples} -DSCOPES=${scopes} \
        -DSHIFTS=${shifts} -DTHREADS=1 -DOPTIMIZED=false -DDEBUG=false ${spdlog[*]} \
        > '${directory}/cmake.log' 2>&1 \
        && make -C '${directory}' -j ${jobs} > '${directory}/make.log' 2>&1"
    if run "${command}"; then
        echo "OK     ${name} (${build_eras})"
    else
        echo "FAILED ${name} (${build_eras}): ${directory}/cmake.log, make.log"
        grep -m 5 "error" "${directory}/make.log" "${directory}/cmake.log" || true
        failed=1
    fi
done
exit "${failed}"
