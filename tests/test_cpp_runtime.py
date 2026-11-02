"""C++ fixtures of the analysis addons, compiled against ROOT and correctionlib.

Skipped without a toolchain (root-config, g++, correctionlib with headers, spdlog).
Both the LCG view and the CROWN container work: correctionlib and spdlog are looked
up next to root-config when the Python module ships no headers, and fmt is used
header-only because LCG's spdlog bundles fmt v11.
"""

import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from analysis_configurations.bbtautau.constants import ERAS_RUN2
from analysis_configurations.bbtautau.tests.helpers import build

ANALYSIS = Path(__file__).resolve().parents[1]
CROWN = ANALYSIS.parents[1]
CPP, ADDONS, FIXTURES = (
    ANALYSIS / "tests/cpp",
    ANALYSIS / "cpp_addons",
    ANALYSIS / "tests/fixtures",
)
CORRECTION_MANAGER = CROWN / "src/utility/CorrectionManager.cxx"
EGM_ROOT = Path("/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM")
# The pinned official EGM payloads of the category layouts the reconstruction
# weight handles: Run 2 UL (split at 20 GeV, every era), Run 3 (splits at 20 and
# 75 GeV), and the 2023 payloads that take phi as a further input.
ELECTRON_RECO_PAYLOADS = {
    **{
        era: (f"Run2-{era}-UL-NanoAODv15/2025-12-05", "UL-Electron-ID-SF")
        for era in ("2016preVFP", "2016postVFP", "2017", "2018")
    },
    "2022Re-recoBCD": (
        "Run3-22CDSep23-Summer22-NanoAODv12/2025-12-15",
        "Electron-ID-SF",
    ),
    "2023PromptC": ("Run3-23CSep23-Summer23-NanoAODv12/2025-12-15", "Electron-ID-SF"),
}
RUN2_ERAS = tuple(ERAS_RUN2)
# The Tau Embedding group's lepton payloads of the embedding SFs per era
EMBEDDING_PAYLOADS = {
    era: [CROWN / f"data/embedding/{flavour}_{era}UL.json.gz" for flavour in ("muon", "electron")]
    for era in RUN2_ERAS
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


def onnxruntime_flags():
    """Include and link flags of the ONNX Runtime C++ API next to root-config (LCG view:
    include/onnxruntime and lib64; CROWN container: include/onnxruntime/core/session and lib)."""
    root_config = shutil.which("root-config")
    if not root_config:
        pytest.skip("ROOT and a C++ compiler are required")
    view = Path(root_config).parent.parent
    headers = [view / "include/onnxruntime", view / "include/onnxruntime/core/session"]
    header = next((d for d in headers if (d / "onnxruntime_cxx_api.h").is_file()), None)
    library = next((d for d in (view / "lib64", view / "lib") if (d / "libonnxruntime.so").is_file()), None)
    if header is None or library is None:
        pytest.skip("the ONNX Runtime C++ API is required")
    return [f"-I{header}", f"-L{library}", "-lonnxruntime", f"-Wl,-rpath,{library}"]


def compile_fixture(directory, name, sources, defines=(), correctionlib=False, libraries=()):
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
    command += list(libraries)
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


@pytest.fixture(scope="module")
def embedding_iso_binary(tmp_path_factory):
    return compile_fixture(
        tmp_path_factory.mktemp("embedding_iso_binned"),
        "embedding_iso_binned",
        [
            CPP / "test_embedding_iso_binned.cxx",
            ADDONS / "src/embedding_iso.cxx",
            CORRECTION_MANAGER,
        ],
        correctionlib=True,
    )


@pytest.mark.parametrize("era", RUN2_ERAS)
def test_embedding_iso_binned_sf_follows_the_iso_bin_and_eta_convention(
    embedding_iso_binary, era
):
    """The iso-binned embedding SF takes the correction of the lepton's iso bin and
    evaluates muons with |eta| and electrons with signed eta, like the core
    functions, in the payloads of every Run-2 era."""
    payloads = EMBEDDING_PAYLOADS[era]
    if not all(payload.is_file() for payload in payloads):
        pytest.skip("The CROWN data/embedding payloads are required")
    subprocess.run([str(embedding_iso_binary), *map(str, payloads)], check=True)


@pytest.fixture(scope="module")
def pog_muon_trigger_binary(tmp_path_factory):
    return compile_fixture(
        tmp_path_factory.mktemp("pog_muon_trigger_sf"),
        "pog_muon_trigger_sf",
        [
            CPP / "test_pog_muon_trigger_sf.cxx",
            ADDONS / "src/pog_muon_trigger_sf.cxx",
            CORRECTION_MANAGER,
        ],
        correctionlib=True,
    )


@pytest.mark.parametrize("era", RUN2_ERAS)
def test_pog_muon_trigger_sf_clamped_to_the_payload_range(pog_muon_trigger_binary, era):
    """The POG single-muon trigger SF of MC (v7 decision 2026-10-18) is the
    payload value at the muon inside the range of the era's muon_Z correction,
    and the value at the clamped (pT, |eta|) below its lowest pT edge (2016:
    the IsoMu22 family from 24 GeV, payload from 26 GeV) and from |eta| 2.4 on,
    where the payload (flow "error") throws; times the extrapolation factor."""
    params = build("sm_config", "ttbar", era=era).config_parameters["mt"]["nominal"]
    payload = Path(params["muon_sf_file"])
    if not payload.is_file():
        pytest.skip("The MUO payloads on /cvmfs are required")
    (entry,) = params["singlemuon_trigger_sf_mc"]
    correction = entry["mc_trigger_sf"]
    min_pt, max_abs_eta = entry["mc_trigger_sf_min_pt"], entry["mc_trigger_sf_max_abs_eta"]
    subprocess.run(
        [str(pog_muon_trigger_binary), str(payload), correction, str(min_pt), str(max_abs_eta)],
        check=True,
    )


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


def test_hem_veto_flag(tmp_path):
    """C20: the 2018 HEM flag at the region edges (eta, phi, pT), with the
    TightLeptonVeto ID, from run 319077 on in data and embedding, and for the
    luminosity fraction of these runs in MC (deterministic per event)."""
    binary = compile_fixture(
        tmp_path,
        "hem_veto",
        [CPP / "test_hem_veto.cxx", ADDONS / "src/hem_veto.cxx"],
    )
    subprocess.run([str(binary)], check=True)


def test_checked_met_covariance(tmp_path):
    """The Run-2 v15 MET covariance: the PuppiMET matrix if finite, positive
    definite and within sumEt^2, else the PF MET matrix, else a diagonal one;
    metcov_source records the choice."""
    binary = compile_fixture(
        tmp_path,
        "met_covariance",
        [CPP / "test_met_covariance.cxx", ADDONS / "src/met_covariance.cxx"],
    )
    subprocess.run([str(binary)], check=True)


@pytest.fixture(scope="module")
def electron_supercluster_binary(tmp_path_factory):
    return compile_fixture(
        tmp_path_factory.mktemp("electron_supercluster"),
        "electron_supercluster",
        [
            CPP / "test_electron_supercluster_eta.cxx",
            CROWN / "src/electrons.cxx",
            ADDONS / "src/electron_reco.cxx",
            CORRECTION_MANAGER,
        ],
        correctionlib=True,
    )


@pytest.mark.parametrize("era", ["2016preVFP", "2016postVFP", "2017", "2018"])
def test_electron_sfs_at_the_supercluster_eta(electron_supercluster_binary, era):
    """C22: an electron with eta just below 1.444 (1.566) and supercluster eta just
    above takes the ID and reco SF of the bin above, in the official EGM payload of
    every era."""
    folder, cset = ELECTRON_RECO_PAYLOADS[era]
    payload = EGM_ROOT / folder / "electron.json.gz"
    if not payload.is_file():
        pytest.skip("Pinned official EGM payload requires CVMFS")
    subprocess.run(
        [str(electron_supercluster_binary), str(payload), cset, era, "wp90iso"], check=True
    )


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


def test_fastmtt_producer_passes_leptonic_decay_types(tmp_path):
    """The core quantities::FastMtt behind the FastMTT friends hands a light
    lepton to FastMTT as a leptonic tau decay, in mt, et and em."""
    binary = compile_fixture(
        tmp_path,
        "fastmtt_decay_types",
        [
            CPP / "test_fastmtt_decay_types.cxx",
            CROWN / "src/quantities.cxx",
            *sorted((CROWN / "src/SVFit").glob("*.cxx")),
        ],
    )
    subprocess.run([str(binary)], check=True)


@pytest.fixture(scope="module")
def jer_smearing_binary(tmp_path_factory):
    return compile_fixture(
        tmp_path_factory.mktemp("jer_smearing"),
        "jer_smearing",
        [CPP / "test_jer_smearing.cxx", ADDONS / "src/jets.cxx", CORRECTION_MANAGER],
        correctionlib=True,
    )


def jec_settings(era):
    """The JME payload, JER and JES tags the SM configuration of ``era`` evaluates."""
    from analysis_configurations.bbtautau.tests.helpers import build

    nominal = build("sm_config", "ttbar", era=era).config_parameters["global"]["nominal"]
    return nominal["ak4jet_jec_file"], nominal["ak4jet_jer_tag"], nominal["ak4jet_jes_tag_mc"]


# reapply_jes: 1 is the production setting, 0 takes the input pt as JES-corrected
@pytest.mark.parametrize("era", RUN2_ERAS)
@pytest.mark.parametrize("reapply_jes", ["1", "0"])
def test_jer_hybrid_smearing_matches_gen_jets_and_draws_per_jet(
    jer_smearing_binary, reapply_jes, era
):
    """The JEC chain scales gen-matched jets with the closest passing gen jet,
    draws one independent standard-normal number per unmatched jet, which
    neither the matching of other jets nor the JER variation changes, and the
    HEM variation scales every tight-ID jet in the HEM region; with the pinned
    JME payload and tags of every Run-2 era."""
    payload, jer_tag, jes_tag = jec_settings(era)
    if not Path(payload).is_file():
        pytest.skip("Pinned official JME payload requires CVMFS")
    subprocess.run(
        [str(jer_smearing_binary), payload, reapply_jes, jer_tag, jes_tag, era], check=True
    )


def test_matched_trigger_object_quantity(tmp_path):
    """trigger::MatchedObjectQuantity (trgobj_*_2 of the tau-ID measurement): the
    nearest trigger object in Delta R with the ID and all filter bits wins, -1
    without one, on the v15 types (UShort_t IDs, ULong64_t filter bits)."""
    binary = compile_fixture(
        tmp_path,
        "trigger_matched_object",
        [CPP / "test_trigger_matched_object.cxx"],
    )
    subprocess.run([str(binary)], check=True)


# --- fake factor summed over the processes of the payload (v7 spec C15) ---------

FF_PAYLOADS = ANALYSIS / "payloads/fake_factors"
# legs whose fake factor the frozen two-process reference must reproduce bit for
# bit: (label, payload directory, scopes)
FF_REFERENCE_LEGS = [
    ("sm2018", FF_PAYLOADS / "sm/fake-factors-2026-10-09/2018", ("et", "mt", "tt")),
    ("nmssm2023postBPix", FF_PAYLOADS / "fake-factors-2026-06-10/2023postBPix", ("mt",)),
    ("nmssm2025", FF_PAYLOADS / "fake-factors-2026-09-26/2025", ("mt",)),
]
# the v7b payloads of every SM payload era (2026-10-19): QCD + ttbar against the frozen
# reference, QCD + W + ttbar as the three-process sum in et and mt, whose tt legs (no
# W+jets in tt) are two-process again: (label, payload directory, scopes, reference)
V7B_PAYLOAD_ERAS = ("2016", "2017", "2018")
V7B_LEGS = [
    (f"sm{era}v7b", FF_PAYLOADS / f"sm/fake-factors-2026-10-19/{era}", ("et", "mt", "tt"), True)
    for era in V7B_PAYLOAD_ERAS
] + [
    (f"sm{era}v7bw", FF_PAYLOADS / f"sm/fake-factors-2026-10-19-w/{era}", scopes, reference)
    for era in V7B_PAYLOAD_ERAS
    for scopes, reference in ((("et", "mt"), False), (("tt",), True))
]


def _binning_centres(node, name, values):
    """Collect the bin centres of every binning on input ``name`` below ``node``."""
    if isinstance(node, dict):
        if node.get("nodetype") == "binning" and node.get("input") == name:
            edges = node["edges"]
            if isinstance(edges, dict):  # uniform binning
                width = (edges["high"] - edges["low"]) / edges["n"]
                edges = [edges["low"] + i * width for i in range(edges["n"] + 1)]
            values.update(0.5 * (lo + hi) for lo, hi in zip(edges, edges[1:]))
        for value in node.values():
            _binning_centres(value, name, values)
    elif isinstance(node, list):
        for value in node:
            _binning_centres(value, name, values)


def fake_factor_plan(label, payload_dir, scopes, reference):
    """Plan lines of tests/cpp/test_fake_factor_sum.cxx for the legs of
    ``scopes``: files, processes, corrections, the bin centres of every input as
    candidates, and the syst keys the friend shifts."""
    from analysis_configurations.bbtautau import ff_payloads

    lines = []
    for scope in scopes:
        payloads = {}
        for leg in ff_payloads.read_legs(str(payload_dir), scope):
            slots = [leg.fractions, *leg.fake_factors, *leg.process_corrections]
            lines += [
                f"leg {label}_{scope}_{leg.name} {int(reference)}",
                f"ff_file {leg.fractions.file}",
                f"corr_file {leg.process_corrections[0].file}",
                f"fraction {leg.fractions.name}",
            ]
            lines += [f"process {c.process} {c.name}" for c in leg.fake_factors]
            lines += [
                f"correction {c.process} {c.name} {int(c.compound)}"
                for c in leg.process_corrections
            ]
            for slot, correction in enumerate(slots):
                if correction.file not in payloads:
                    with gzip.open(correction.file, "rt") as handle:
                        payloads[correction.file] = json.load(handle)
                payload = payloads[correction.file]
                plain = {c["name"]: c for c in payload["corrections"]}
                if correction.compound:
                    (compound,) = [
                        c for c in payload["compound_corrections"]
                        if c["name"] == correction.name
                    ]
                    nodes, inputs = [plain[m] for m in compound["stack"]], compound["inputs"]
                else:
                    nodes, inputs = [plain[correction.name]], plain[correction.name]["inputs"]
                for name in [i["name"] for i in inputs if i["name"] not in ("process", "syst")]:
                    values = set()
                    _binning_centres([n["data"] for n in nodes], name, values)
                    assert values, (correction.name, name)
                    lines.append(
                        f"values {slot} {len(values)} " + " ".join(repr(v) for v in sorted(values))
                    )
                lines += [f"variation {slot} {key}" for key in correction.shift_keys]
    return lines


def test_fake_factor_sum_over_the_payload_processes(tmp_path):
    """C15: fakefactors::xyh::FakeFactor sums f_p * FF_p * corrections_p over the
    processes of the payload. On the measured two-process payloads (SM 2018 et,
    mt, tt; NMSSM 2023postBPix, 2025 mt; the v7b QCD + ttbar payloads of 2016, 2017
    and 2018 and the tt legs of the v7b W variant) it reproduces the friend before C15 bit
    for bit, raw and corrected, nominal and with every syst key the friend
    shifts; on a QCD + W + ttbar payload (derived from SM 2018 et and mt, and the
    measured v7b ones of every era) it gives the three-process sum, with a W term. Every leg gives that sum in the
    float arithmetic of the friend (in payload order) bit for bit, which fixes
    the values of the three-process legs as well.

    The friend is built in the CROWN container with ROOT's -march=nocona, which
    has no fused multiply-add, so every product is rounded before it is summed.
    The fixture is built with -ffp-contract=off to keep that arithmetic: GCC fuses
    a * b + c in C++ wherever the target has an FMA (LCG_110's GCC 16 defaults to
    x86-64-v3), and the fused reference differs from the friend in the last bit."""
    sys.path.insert(0, str(FIXTURES))
    try:
        import make_wjets_fake_factor_payload as wjets
    finally:
        sys.path.remove(str(FIXTURES))
    reference = FF_REFERENCE_LEGS[0][1]
    wjets_dir = wjets.make(reference, tmp_path / "wjets")
    lines = []
    for label, directory, scopes in FF_REFERENCE_LEGS:
        lines += fake_factor_plan(label, directory, scopes, reference=True)
    lines += fake_factor_plan("sm2018wjets", wjets_dir, ("et", "mt"), reference=False)
    for label, directory, scopes, reference_leg in V7B_LEGS:
        lines += fake_factor_plan(label, directory, scopes, reference=reference_leg)
    plan = tmp_path / "plan.txt"
    plan.write_text("\n".join(lines) + "\n")
    binary = compile_fixture(
        tmp_path,
        "fake_factor_sum",
        [CPP / "test_fake_factor_sum.cxx", ADDONS / "src/fakefactors.cxx", CORRECTION_MANAGER],
        defines=["-O2", "-ffp-contract=off"],
        correctionlib=True,
    )
    result = subprocess.run([str(binary), str(plan)], capture_output=True, text=True)
    summary = [line for line in result.stdout.splitlines() if line.startswith(("PASS", "FAIL"))]
    assert result.returncode == 0, "\n".join(summary) + result.stderr[-3000:]
    legs = 8 + 3 * 4 + 3 * 4  # + per v7b payload era: et, mt, tt leading and subleading, in both variants
    assert len(summary) == legs and all(line.startswith("PASS") for line in summary), summary


# --- NN classifier friend (nn spec 3.3, 3.4) ------------------------------------


def test_sm_classifier_scores_every_event_with_the_model_of_its_residue(tmp_path):
    """sm_nn_classifier on the toy models of tests/fixtures/nn_classifier (two and four
    folds, probabilities, logits, a binary head): the model of residue r scores exactly
    the events with event % n == r, on unsigned 64-bit event numbers at 2^24, 2^31, 2^32
    and 2^63, and reproduces onnxruntime's scores of that model; outside the gate every
    output is -1; dynamic dimensions, other shapes, inputs of another length and NaN
    inputs throw; the gate flag reads its columns by index (shifted columns); the
    constants of a manifest (k2_constants) are float columns that enter the input vector
    of fakefactors::BuildFloatVector at their position."""
    binary = compile_fixture(
        tmp_path,
        "sm_classifier",
        [
            CPP / "test_sm_classifier.cxx",
            ADDONS / "src/sm_classifier.cxx",
            ADDONS / "src/fakefactors.cxx",
            CROWN / "src/utility/OnnxSessionManager.cxx",
            CORRECTION_MANAGER,
        ],
        defines=["-O2"],
        correctionlib=True,
        libraries=onnxruntime_flags(),
    )
    result = subprocess.run(
        [str(binary), str(FIXTURES / "nn_classifier")], capture_output=True, text=True
    )
    summary = [line for line in result.stdout.splitlines() if line.startswith(("PASS", "FAIL"))]
    assert result.returncode == 0, "\n".join(summary) + result.stderr[-3000:]
    assert len(summary) == 3 * 5 + 7 + 3 + 3 and all(line.startswith("PASS") for line in summary), summary
