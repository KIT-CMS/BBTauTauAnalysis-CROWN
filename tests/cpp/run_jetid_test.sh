#!/usr/bin/env bash
# Fixture-driven boundary-test runner for
# xyh::object_selection::tight_jet_id_2018_puppi_v15.
#
# 1. Generates tests/cpp/jetid_fixture.inc from
#    tests/fixtures/jetid_2018UL_puppi_tight_v1.json via an embedded
#    python3 script (SKIPPING boundary_cases with expected_pass=null --
#    those are out-of-scope markers, not validated criteria).
# 2. Compiles tests/cpp/test_jetid_v15.cxx together with
#    cpp_addons/src/jetid_v15.cxx.
# 3. Runs the resulting binary; it prints one PASS/FAIL line per boundary
#    case and exits nonzero if any case fails.
#
# Run from anywhere; this script locates the analysis directory relative to
# its own location. Needs ROOT + g++ (e.g. the kingmaker_standalone
# container):
#
#   singularity exec --bind /work,/cvmfs \
#     /cvmfs/unpacked.cern.ch/registry.hub.docker.com/kingmakerimages/kingmaker_standalone:V1 \
#     bash tests/cpp/run_jetid_test.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CROWN_ROOT="$(cd "${ANALYSIS_DIR}/../.." && pwd)"

FIXTURE_JSON="${ANALYSIS_DIR}/tests/fixtures/jetid_2018UL_puppi_tight_v1.json"
FIXTURE_INC="${SCRIPT_DIR}/jetid_fixture.inc"
TEST_CXX="${SCRIPT_DIR}/test_jetid_v15.cxx"
JETID_CXX="${ANALYSIS_DIR}/cpp_addons/src/jetid_v15.cxx"
INCLUDE_DIR="${ANALYSIS_DIR}/cpp_addons/include"
OUT_BIN="/tmp/test_jetid_v15"

# jetid_v15.cxx pulls in the framework's Logger.hxx (to match the house
# style of cpp_addons/src/object_selection.cxx), which needs spdlog's
# (vendored/bundled fmt) headers. Those are fetched by CMake's
# AddLogging.cmake into a build directory's install prefix, not shipped by
# the container -- reuse whichever CROWN build dir has already built them
# rather than re-fetching here.
SPDLOG_INCLUDE_DIR=""
for candidate in "${CROWN_ROOT}"/build*/include; do
    if [[ -d "${candidate}/spdlog" ]]; then
        SPDLOG_INCLUDE_DIR="${candidate}"
        break
    fi
done
if [[ -z "${SPDLOG_INCLUDE_DIR}" ]]; then
    echo "[run_jetid_test] no built spdlog headers found under" \
         "${CROWN_ROOT}/build*/include -- configure/build CROWN once" \
         "(e.g. bash analysis_configurations/bbtautau/build_scripts/test_build_2018.sh)" \
         "so spdlog is fetched, then re-run this script." >&2
    exit 1
fi
echo "[run_jetid_test] using spdlog headers from ${SPDLOG_INCLUDE_DIR}"

if [[ ! -f "${FIXTURE_JSON}" ]]; then
    echo "[run_jetid_test] fixture not found: ${FIXTURE_JSON}" >&2
    exit 1
fi

echo "[run_jetid_test] generating ${FIXTURE_INC}"
echo "[run_jetid_test]   from ${FIXTURE_JSON}"

python3 - "${FIXTURE_JSON}" "${FIXTURE_INC}" <<'PYEOF'
import json
import sys

fixture_path, out_path = sys.argv[1], sys.argv[2]

with open(fixture_path) as f:
    fixture = json.load(f)

formula_version = fixture["formula_version"]
cases = fixture["boundary_cases"]

lines = [
    "// Auto-generated from tests/fixtures/jetid_2018UL_puppi_tight_v1.json",
    "// by run_jetid_test.sh -- DO NOT EDIT BY HAND.",
    "#pragma once",
    "",
    "struct JetIDFixtureCase {",
    "    const char *name;",
    "    float eta;",
    "    float neHEF;",
    "    float neEmEF;",
    "    int nConstituents;",
    "    float chHEF;",
    "    float muEF;",
    "    float chEmEF;",
    "    int chMultiplicity;",
    "    int neMultiplicity;",
    "    int expected;",
    "};",
    "",
    'static const char *kFixtureFormulaVersion = "%s";' % formula_version,
    "",
    "static const JetIDFixtureCase kFixtureCases[] = {",
]

skipped = 0
emitted = 0
for case in cases:
    # Cases with expected_pass=null are out-of-scope markers (e.g. |eta| >
    # 2.7, beyond the region structure this fixture encodes) -- the harness
    # MUST skip them rather than assert a pass/fail value for them.
    if case.get("expected_pass") is None:
        skipped += 1
        continue

    inputs = case["inputs"]
    expected = 1 if case["expected_pass"] else 0
    lines.append(
        '    {{"{name}", {eta}f, {neHEF}f, {neEmEF}f, {nConstituents}, '
        "{chHEF}f, {muEF}f, {chEmEF}f, {chMultiplicity}, "
        "{neMultiplicity}, {expected}}},".format(
            name=case["name"],
            eta=inputs["Jet_eta"],
            neHEF=inputs["Jet_neHEF"],
            neEmEF=inputs["Jet_neEmEF"],
            nConstituents=inputs["Jet_nConstituents"],
            chHEF=inputs["Jet_chHEF"],
            muEF=inputs["Jet_muEF"],
            chEmEF=inputs["Jet_chEmEF"],
            chMultiplicity=inputs["Jet_chMultiplicity"],
            neMultiplicity=inputs["Jet_neMultiplicity"],
            expected=expected,
        )
    )
    emitted += 1

lines += [
    "};",
    "",
    "static const std::size_t kFixtureCasesCount = "
    "sizeof(kFixtureCases) / sizeof(kFixtureCases[0]);",
]

with open(out_path, "w") as f:
    f.write("\n".join(lines) + "\n")

sys.stderr.write(
    "[jetid_fixture] emitted %d case(s), skipped %d out-of-scope "
    "(expected_pass=null) case(s)\n" % (emitted, skipped)
)
PYEOF

echo "[run_jetid_test] compiling"
g++ -std=c++17 $(root-config --cflags --libs) \
    -I "${INCLUDE_DIR}" \
    -I "${SPDLOG_INCLUDE_DIR}" \
    "${JETID_CXX}" "${TEST_CXX}" \
    -o "${OUT_BIN}"

echo "[run_jetid_test] running"
"${OUT_BIN}"
