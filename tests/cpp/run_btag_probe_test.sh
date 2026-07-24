#!/usr/bin/env bash
# Boundary + writer test runner for the payload-independent UParT probe-jet
# collection (xyh::btag_probe::probe_mask + masked_vector).
#
# Compiles tests/cpp/test_btag_probe.cxx together with
# cpp_addons/src/btag_probe.cxx, links ROOT, and runs the resulting binary;
# it prints one PASS/FAIL line per case and exits nonzero if any case fails.
#
# Run from anywhere; this script locates the analysis directory relative to
# its own location. Needs ROOT + g++ (e.g. the kingmaker_standalone
# container):
#
#   singularity exec --bind /work,/cvmfs \
#     /cvmfs/unpacked.cern.ch/registry.hub.docker.com/kingmakerimages/kingmaker_standalone:V1 \
#     bash tests/cpp/run_btag_probe_test.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CROWN_ROOT="$(cd "${ANALYSIS_DIR}/../.." && pwd)"

TEST_CXX="${SCRIPT_DIR}/test_btag_probe.cxx"
PROBE_CXX="${ANALYSIS_DIR}/cpp_addons/src/btag_probe.cxx"
INCLUDE_DIR="${ANALYSIS_DIR}/cpp_addons/include"
OUT_BIN="/tmp/test_btag_probe"

# btag_probe.cxx pulls in the framework's Logger.hxx (to match the house
# style of the other cpp_addons sources), which needs spdlog's (vendored/
# bundled fmt) headers. Those are fetched by CMake's AddLogging.cmake into a
# build directory's install prefix, not shipped by the container -- reuse
# whichever CROWN build dir has already built them rather than re-fetching
# here (same approach as run_jetid_test.sh / run_btag_sf_test.sh).
SPDLOG_INCLUDE_DIR=""
for candidate in "${CROWN_ROOT}"/build*/include; do
    if [[ -d "${candidate}/spdlog" ]]; then
        SPDLOG_INCLUDE_DIR="${candidate}"
        break
    fi
done
if [[ -z "${SPDLOG_INCLUDE_DIR}" ]]; then
    echo "[run_btag_probe_test] no built spdlog headers found under" \
         "${CROWN_ROOT}/build*/include -- configure/build CROWN once" \
         "(e.g. bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh)" \
         "so spdlog is fetched, then re-run this script." >&2
    exit 1
fi
echo "[run_btag_probe_test] using spdlog headers from ${SPDLOG_INCLUDE_DIR}"

echo "[run_btag_probe_test] compiling"
g++ -std=c++17 $(root-config --cflags --libs) \
    -I "${INCLUDE_DIR}" \
    -I "${SPDLOG_INCLUDE_DIR}" \
    "${PROBE_CXX}" "${TEST_CXX}" \
    -o "${OUT_BIN}"

echo "[run_btag_probe_test] running"
"${OUT_BIN}"
