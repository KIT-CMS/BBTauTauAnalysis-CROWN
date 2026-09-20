"""Small C++ event fixtures; require a configured ROOT/compiler environment."""

from pathlib import Path
import shutil
import subprocess

import pytest

ANALYSIS = Path(__file__).resolve().parents[1]
CROWN = ANALYSIS.parents[1]
EGM_ROOT = Path("/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM")
# One pinned official EGM payload per category layout the reconstruction weight
# handles: Run 2 UL (split at 20 GeV), Run 3 (splits at 20 and 75 GeV), and the
# 2023 payloads that take phi as a further input. The other Run-2 eras share the
# 2018 layout and differ only in the era key.
ELECTRON_RECO_PAYLOADS = {
    "2018": ("Run2-2018-UL-NanoAODv15/2025-12-05", "UL-Electron-ID-SF"),
    "2022Re-recoBCD": (
        "Run3-22CDSep23-Summer22-NanoAODv12/2025-12-15",
        "Electron-ID-SF",
    ),
    "2023PromptC": ("Run3-23CSep23-Summer23-NanoAODv12/2025-12-15", "Electron-ID-SF"),
}


def compile_fixture(directory, name, sources, include_dirs=(), extra_args=()):
    """Compile ``sources`` against ROOT into ``directory/name``; skip without a toolchain."""
    root_config = shutil.which("root-config")
    compiler = shutil.which("g++")
    if not root_config or not compiler:
        pytest.skip("ROOT and a C++ compiler are required")
    flags = subprocess.check_output(
        [root_config, "--cflags", "--libs"], text=True
    ).split()
    includes = [arg for directory_ in include_dirs for arg in ("-I", str(directory_))]
    binary = Path(directory) / name
    result = subprocess.run(
        [
            compiler,
            *map(str, sources),
            *includes,
            *flags,
            *extra_args,
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return binary


@pytest.fixture(scope="module")
def electron_reco_binary(tmp_path_factory):
    import correctionlib

    corr = Path(correctionlib.__file__).parent
    if not (corr / "include/correction.h").is_file():
        # LCG separates Python modules from the C++ installation.
        corr = Path(shutil.which("root-config") or "/").parent.parent
    return compile_fixture(
        tmp_path_factory.mktemp("electron_reco"),
        "test_control_electron_reco",
        [
            ANALYSIS / "tests/cpp/test_control_electron_reco.cxx",
            ANALYSIS / "cpp_addons/src/electron_reco.cxx",
            CROWN / "src/utility/CorrectionManager.cxx",
        ],
        include_dirs=[
            ANALYSIS / "cpp_addons/include",
            CROWN / "include",
            corr / "include",
        ],
        extra_args=[
            str(corr / "lib/libcorrectionlib.so"),
            f"-Wl,-rpath,{corr / 'lib'}",
            "-DFMT_HEADER_ONLY",
        ],
    )


@pytest.mark.parametrize("era", sorted(ELECTRON_RECO_PAYLOADS))
def test_electron_reco_official_payload_pt_categories(electron_reco_binary, era):
    folder, cset = ELECTRON_RECO_PAYLOADS[era]
    payload = EGM_ROOT / folder / "electron.json.gz"
    if not payload.is_file():
        pytest.skip("Pinned official EGM payload requires CVMFS")
    subprocess.run([str(electron_reco_binary), str(payload), cset, era], check=True)
