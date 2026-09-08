#!/usr/bin/env bash
# Test runner for
# xyh::scalefactor::btagging_strict::multi_wp_event_weight.
#
# Regenerates the synthetic correctionlib fixtures, then compiles
# tests/cpp/test_btag_sf_strict.cxx together with
# cpp_addons/src/btag_sf_strict.cxx and the core
# src/utility/CorrectionManager.cxx, links correctionlib + ROOT, and runs the
# resulting binary. The binary prints one PASS/FAIL line per case and exits
# nonzero if any case fails.
#
# Everything the test touches is synthetic, so no /cvmfs and no container is
# required: any environment with ROOT, g++, a correctionlib install and the
# spdlog headers works. Point the script at a non-default toolchain with:
#
#   ROOT_CONFIG           root-config to use          (default: root-config)
#   PYTHON                python for the fixtures     (default: python3)
#   CORRECTIONLIB_BASE    correctionlib install root  (default: ask PYTHON)
#   SPDLOG_INCLUDE_DIR    dir containing spdlog/      (default: CROWN build*)
#   TMPDIR                where the binary is written (default: /tmp)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CROWN_ROOT="$(cd "${ANALYSIS_DIR}/../.." && pwd)"

ROOT_CONFIG="${ROOT_CONFIG:-root-config}"
PYTHON="${PYTHON:-python3}"

TEST_CXX="${SCRIPT_DIR}/test_btag_sf_strict.cxx"
BTAG_CXX="${ANALYSIS_DIR}/cpp_addons/src/btag_sf_strict.cxx"
CM_CXX="${CROWN_ROOT}/src/utility/CorrectionManager.cxx"
INCLUDE_DIR="${ANALYSIS_DIR}/cpp_addons/include"
CROWN_INCLUDE_DIR="${CROWN_ROOT}/include"
FIXTURE_DIR="${ANALYSIS_DIR}/tests/fixtures"
MAKE_FIXTURES="${FIXTURE_DIR}/make_btag_sf_strict_fixtures.py"
FIXTURE_SF="${FIXTURE_DIR}/btag_sf_strict_sf.json"
FIXTURE_EFF="${FIXTURE_DIR}/btag_sf_strict_eff.json"
OUT_BIN="${TMPDIR:-/tmp}/test_btag_sf_strict"

# The fixtures are generated, not committed (see .gitignore) -- always rebuild
# them so they cannot drift from the generator the test comments quote.
echo "[run_btag_sf_test] generating fixtures"
"${PYTHON}" "${MAKE_FIXTURES}"

# spdlog headers (Logger.hxx dependency) are fetched by CMake's
# AddLogging.cmake into a CROWN build dir's install prefix, not shipped by the
# container -- reuse whichever build dir already has them.
if [[ -z "${SPDLOG_INCLUDE_DIR:-}" ]]; then
    for candidate in "${CROWN_ROOT}"/build*/include; do
        if [[ -d "${candidate}/spdlog" ]]; then
            SPDLOG_INCLUDE_DIR="${candidate}"
            break
        fi
    done
fi
if [[ -z "${SPDLOG_INCLUDE_DIR:-}" || ! -d "${SPDLOG_INCLUDE_DIR}/spdlog" ]]; then
    echo "[run_btag_sf_test] no spdlog headers found under" \
         "${CROWN_ROOT}/build*/include -- configure/build CROWN once" \
         "(e.g. bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh)" \
         "so spdlog is fetched, or set SPDLOG_INCLUDE_DIR to a directory" \
         "containing spdlog/, then re-run this script." >&2
    exit 1
fi
echo "[run_btag_sf_test] using spdlog headers from ${SPDLOG_INCLUDE_DIR}"

# correctionlib include + library, by default discovered from the active Python
# install (same package CROWN's AddCorrectionlib.cmake resolves).
CORR_BASE="${CORRECTIONLIB_BASE:-$("${PYTHON}" -c 'import correctionlib, os; print(os.path.dirname(correctionlib.__file__))')}"
CORR_INCLUDE_DIR="${CORR_BASE}/include"
CORR_LIB="${CORR_BASE}/lib/libcorrectionlib.so"
if [[ ! -f "${CORR_INCLUDE_DIR}/correction.h" || ! -f "${CORR_LIB}" ]]; then
    echo "[run_btag_sf_test] correctionlib headers/lib not found under" \
         "${CORR_BASE} -- set CORRECTIONLIB_BASE (or point PYTHON at an" \
         "interpreter whose correctionlib ships include/ and lib/)." >&2
    exit 1
fi
echo "[run_btag_sf_test] using correctionlib from ${CORR_BASE}"

echo "[run_btag_sf_test] compiling"
g++ -std=c++17 $("${ROOT_CONFIG}" --cflags --libs) \
    -I "${INCLUDE_DIR}" \
    -I "${CROWN_INCLUDE_DIR}" \
    -I "${CORR_INCLUDE_DIR}" \
    -I "${SPDLOG_INCLUDE_DIR}" \
    -DBTAG_FIXTURE_SF="\"${FIXTURE_SF}\"" \
    -DBTAG_FIXTURE_EFF="\"${FIXTURE_EFF}\"" \
    "${BTAG_CXX}" "${CM_CXX}" "${TEST_CXX}" \
    "${CORR_LIB}" -lz -lpthread \
    -Wl,-rpath,"${CORR_BASE}/lib" \
    -o "${OUT_BIN}"

echo "[run_btag_sf_test] running"
LD_LIBRARY_PATH="${CORR_BASE}/lib:${LD_LIBRARY_PATH:-}" "${OUT_BIN}"
