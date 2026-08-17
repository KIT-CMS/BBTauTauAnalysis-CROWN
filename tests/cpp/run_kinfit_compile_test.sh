#!/usr/bin/env bash
# Compilation + smoke-test runner for hhkinfit::sm_hh_kinfit (the SM
# fixed-mass 125/125 HH kinematic fit).
#
# Since the SM kinematic-fit friend executable needs a real quantities map
# from a main CROWN run to build, this is a cheaper compilation-only proof:
# it compiles cpp_addons/src/hhkinfit.cxx together with the vendored engine
# (cpp_addons/src/HHKinFit/{YHKinFitMaster,PSFit}.cxx) and a tiny main()
# (test_sm_hh_kinfit.cxx) that calls sm_hh_kinfit on a one-event in-memory
# RDataFrame with plausible four-vectors, then asserts the outputs are finite
# with the convergence flag set.
#
# Run from anywhere; this script locates the analysis directory relative to
# its own location. Needs ROOT + g++ (e.g. the kingmaker_standalone
# container):
#
#   singularity exec --bind /work,/cvmfs \
#     /cvmfs/unpacked.cern.ch/registry.hub.docker.com/kingmakerimages/kingmaker_standalone:V1 \
#     bash tests/cpp/run_kinfit_compile_test.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CROWN_ROOT="$(cd "${ANALYSIS_DIR}/../.." && pwd)"

TEST_CXX="${SCRIPT_DIR}/test_sm_hh_kinfit.cxx"
HHKINFIT_CXX="${ANALYSIS_DIR}/cpp_addons/src/hhkinfit.cxx"
YHKINFITMASTER_CXX="${ANALYSIS_DIR}/cpp_addons/src/HHKinFit/YHKinFitMaster.cxx"
PSFIT_CXX="${ANALYSIS_DIR}/cpp_addons/src/HHKinFit/PSFit.cxx"
INCLUDE_DIR="${ANALYSIS_DIR}/cpp_addons/include"
OUT_BIN="/tmp/test_sm_hh_kinfit"

# hhkinfit.cxx (and the vendored engine) pull in the framework's Logger.hxx,
# which needs spdlog's (vendored/bundled fmt) headers. Those are fetched by
# CMake's AddLogging.cmake into a build directory's install prefix, not
# shipped by the container -- reuse whichever CROWN build dir has already
# built them rather than re-fetching here.
SPDLOG_INCLUDE_DIR=""
for candidate in "${CROWN_ROOT}"/build*/include; do
    if [[ -d "${candidate}/spdlog" ]]; then
        SPDLOG_INCLUDE_DIR="${candidate}"
        break
    fi
done
if [[ -z "${SPDLOG_INCLUDE_DIR}" ]]; then
    echo "[run_kinfit_compile_test] no built spdlog headers found under" \
         "${CROWN_ROOT}/build*/include -- configure/build CROWN once" \
         "(e.g. bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh)" \
         "so spdlog is fetched, then re-run this script." >&2
    exit 1
fi
echo "[run_kinfit_compile_test] using spdlog headers from ${SPDLOG_INCLUDE_DIR}"

echo "[run_kinfit_compile_test] compiling"
g++ -std=c++17 $(root-config --cflags --libs) \
    -I "${INCLUDE_DIR}" \
    -I "${SPDLOG_INCLUDE_DIR}" \
    "${HHKINFIT_CXX}" "${YHKINFITMASTER_CXX}" "${PSFIT_CXX}" "${TEST_CXX}" \
    -o "${OUT_BIN}"

echo "[run_kinfit_compile_test] running"
"${OUT_BIN}"
