"""C++ fixtures of the analysis addons, compiled against ROOT and correctionlib.

Skipped without a toolchain (root-config, g++, correctionlib with headers, spdlog).
Both the LCG view and the CROWN container work: correctionlib and spdlog are looked
up next to root-config when the Python module ships no headers, and fmt is used
header-only because LCG's spdlog bundles fmt v11.
"""

from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ANALYSIS = Path(__file__).resolve().parents[1]
CROWN = ANALYSIS.parents[1]
CPP, ADDONS, FIXTURES = (
    ANALYSIS / "tests/cpp",
    ANALYSIS / "cpp_addons",
    ANALYSIS / "tests/fixtures",
)
CORRECTION_MANAGER = CROWN / "src/utility/CorrectionManager.cxx"
EGM_ROOT = Path("/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM")
# One pinned official EGM payload per category layout the reconstruction weight
# handles: Run 2 UL (split at 20 GeV), Run 3 (splits at 20 and 75 GeV), and the
# 2023 payloads that take phi as a further input.
ELECTRON_RECO_PAYLOADS = {
    "2018": ("Run2-2018-UL-NanoAODv15/2025-12-05", "UL-Electron-ID-SF"),
    "2022Re-recoBCD": (
        "Run3-22CDSep23-Summer22-NanoAODv12/2025-12-15",
        "Electron-ID-SF",
    ),
    "2023PromptC": ("Run3-23CSep23-Summer23-NanoAODv12/2025-12-15", "Electron-ID-SF"),
}


def toolchain():
    root_config, compiler = shutil.which("root-config"), shutil.which("g++")
    if not root_config or not compiler:
        pytest.skip("ROOT and a C++ compiler are required")
    view = Path(root_config).parent.parent
    try:
        import correctionlib

        corr = Path(correctionlib.__file__).parent
    except ImportError:
        corr = view
    if not (corr / "include/correction.h").is_file():
        corr = view  # LCG separates the Python module from the C++ installation
    if not (corr / "lib/libcorrectionlib.so").is_file():
        pytest.skip("correctionlib headers and library are required")
    candidates = [view / "include", *CROWN.glob("build*/include")]
    spdlog = next((d for d in candidates if (d / "spdlog").is_dir()), None)
    if spdlog is None:
        pytest.skip("spdlog headers are required")
    flags = subprocess.check_output(
        [root_config, "--cflags", "--libs"], text=True
    ).split()
    return compiler, flags, corr, spdlog


def compile_fixture(directory, name, sources, defines=(), correctionlib=False):
    compiler, flags, corr, spdlog = toolchain()
    includes = [ADDONS / "include", CROWN / "include", spdlog, corr / "include"]
    command = [
        compiler,
        "-std=c++17",
        "-DFMT_HEADER_ONLY",
        *defines,
        *map(str, sources),
    ]
    command += [f"-I{d}" for d in includes] + flags
    if correctionlib:
        command += [
            str(corr / "lib/libcorrectionlib.so"),
            f"-Wl,-rpath,{corr / 'lib'}",
            "-lz",
            "-lpthread",
        ]
    binary = Path(directory) / name
    result = subprocess.run(
        [*command, "-o", str(binary)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return binary


@pytest.fixture(scope="module")
def electron_reco_binary(tmp_path_factory):
    return compile_fixture(
        tmp_path_factory.mktemp("electron_reco"),
        "electron_reco",
        [
            CPP / "test_control_electron_reco.cxx",
            ADDONS / "src/electron_reco.cxx",
            CORRECTION_MANAGER,
        ],
        correctionlib=True,
    )


@pytest.mark.parametrize("era", sorted(ELECTRON_RECO_PAYLOADS))
def test_electron_reco_official_payload_pt_categories(electron_reco_binary, era):
    folder, cset = ELECTRON_RECO_PAYLOADS[era]
    payload = EGM_ROOT / folder / "electron.json.gz"
    if not payload.is_file():
        pytest.skip("Pinned official EGM payload requires CVMFS")
    subprocess.run([str(electron_reco_binary), str(payload), cset, era], check=True)


def test_strict_upart_btag_weight_consumer(tmp_path):
    """Synthetic SF/efficiency payloads (gitignored, regenerated here) drive the
    strict multi-WP consumer through its throw and weight cases."""
    subprocess.run(
        [sys.executable, str(FIXTURES / "make_btag_sf_strict_fixtures.py")],
        check=True,
        capture_output=True,
    )
    binary = compile_fixture(
        tmp_path,
        "btag_sf_strict",
        [
            CPP / "test_btag_sf_strict.cxx",
            ADDONS / "src/btag_sf_strict.cxx",
            CORRECTION_MANAGER,
        ],
        defines=[
            f'-DBTAG_FIXTURE_SF="{FIXTURES / "btag_sf_strict_sf.json"}"',
            f'-DBTAG_FIXTURE_EFF="{FIXTURES / "btag_sf_strict_eff.json"}"',
        ],
        correctionlib=True,
    )
    subprocess.run([str(binary)], check=True)


def test_sm_hh_kinfit_compiles_and_converges(tmp_path):
    binary = compile_fixture(
        tmp_path,
        "sm_hh_kinfit",
        [
            CPP / "test_sm_hh_kinfit.cxx",
            ADDONS / "src/hhkinfit.cxx",
            ADDONS / "src/HHKinFit/YHKinFitMaster.cxx",
            ADDONS / "src/HHKinFit/PSFit.cxx",
        ],
    )
    subprocess.run([str(binary)], check=True)
