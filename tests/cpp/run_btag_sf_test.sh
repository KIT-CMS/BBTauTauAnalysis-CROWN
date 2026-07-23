#!/usr/bin/env bash
# Test runner for
# xyh::scalefactor::btagging_strict::multi_wp_event_weight (+ pt_clamped_njets).
#
# Compiles tests/cpp/test_btag_sf_strict.cxx together with
# cpp_addons/src/btag_sf_strict.cxx and the core
# src/utility/CorrectionManager.cxx, links correctionlib + ROOT, and runs the
# resulting binary. The binary prints one PASS/FAIL line per case and exits
# nonzero if any case fails.
#
# Case (f) evaluates the REAL pinned BTV payload on cvmfs, so this must run in
# the kingmaker_standalone container with /cvmfs (and /work) bound:
#
#   singularity exec --bind /work,/cvmfs \
#     /cvmfs/unpacked.cern.ch/registry.hub.docker.com/kingmakerimages/kingmaker_standalone:V1 \
#     bash tests/cpp/run_btag_sf_test.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CROWN_ROOT="$(cd "${ANALYSIS_DIR}/../.." && pwd)"

TEST_CXX="${SCRIPT_DIR}/test_btag_sf_strict.cxx"
BTAG_CXX="${ANALYSIS_DIR}/cpp_addons/src/btag_sf_strict.cxx"
CM_CXX="${CROWN_ROOT}/src/utility/CorrectionManager.cxx"
INCLUDE_DIR="${ANALYSIS_DIR}/cpp_addons/include"
CROWN_INCLUDE_DIR="${CROWN_ROOT}/include"
FIXTURE_SF="${ANALYSIS_DIR}/tests/fixtures/btag_sf_strict_sf.json"
FIXTURE_EFF="${ANALYSIS_DIR}/tests/fixtures/btag_sf_strict_eff.json"
REAL_SF="/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run2-2018-UL-NanoAODv15/2026-06-18/btagging.json.gz"
OUT_BIN="/tmp/test_btag_sf_strict"

# spdlog headers (Logger.hxx dependency) are fetched by CMake's
# AddLogging.cmake into a CROWN build dir's install prefix, not shipped by the
# container -- reuse whichever build dir already has them (same approach as
# run_jetid_test.sh).
SPDLOG_INCLUDE_DIR=""
for candidate in "${CROWN_ROOT}"/build*/include; do
    if [[ -d "${candidate}/spdlog" ]]; then
        SPDLOG_INCLUDE_DIR="${candidate}"
        break
    fi
done
if [[ -z "${SPDLOG_INCLUDE_DIR}" ]]; then
    echo "[run_btag_sf_test] no built spdlog headers found under" \
         "${CROWN_ROOT}/build*/include -- configure/build CROWN once" \
         "(e.g. bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh)" \
         "so spdlog is fetched, then re-run this script." >&2
    exit 1
fi
echo "[run_btag_sf_test] using spdlog headers from ${SPDLOG_INCLUDE_DIR}"

# correctionlib include + library, discovered from the active Python install
# (same package CROWN's AddCorrectionlib.cmake resolves).
CORR_BASE="$(python3 -c 'import correctionlib, os; print(os.path.dirname(correctionlib.__file__))')"
CORR_INCLUDE_DIR="${CORR_BASE}/include"
CORR_LIB="${CORR_BASE}/lib/libcorrectionlib.so"
if [[ ! -f "${CORR_INCLUDE_DIR}/correction.h" || ! -f "${CORR_LIB}" ]]; then
    echo "[run_btag_sf_test] correctionlib headers/lib not found under" \
         "${CORR_BASE} -- run inside the kingmaker_standalone container." >&2
    exit 1
fi
echo "[run_btag_sf_test] using correctionlib from ${CORR_BASE}"

if [[ ! -f "${FIXTURE_SF}" || ! -f "${FIXTURE_EFF}" ]]; then
    echo "[run_btag_sf_test] fixtures missing; regenerate with" \
         "python3 tests/fixtures/make_btag_sf_strict_fixtures.py" >&2
    exit 1
fi

echo "[run_btag_sf_test] compiling"
g++ -std=c++17 $(root-config --cflags --libs) \
    -I "${INCLUDE_DIR}" \
    -I "${CROWN_INCLUDE_DIR}" \
    -I "${CORR_INCLUDE_DIR}" \
    -I "${SPDLOG_INCLUDE_DIR}" \
    -DBTAG_FIXTURE_SF="\"${FIXTURE_SF}\"" \
    -DBTAG_FIXTURE_EFF="\"${FIXTURE_EFF}\"" \
    -DBTAG_REAL_SF="\"${REAL_SF}\"" \
    "${BTAG_CXX}" "${CM_CXX}" "${TEST_CXX}" \
    "${CORR_LIB}" -lz -lpthread \
    -Wl,-rpath,"${CORR_BASE}/lib" \
    -o "${OUT_BIN}"

echo "[run_btag_sf_test] running"
LD_LIBRARY_PATH="${CORR_BASE}/lib:${LD_LIBRARY_PATH:-}" "${OUT_BIN}"
