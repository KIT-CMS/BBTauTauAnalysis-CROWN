#!/usr/bin/env python3
"""Pass fraction of the gate of the NN classifier friend (nn_gate.py, nn spec 3.4 and 9) on the n-tuples of a
production, one file per era, sample type and tau scope (data and embedding: of the scope's stream or channel), read
over xrootd, and the check that the gate contains the selections of the ShapeSmith tau skims.

Every file is read once with RDataFrame: the gate flag of the C++ translation the friend evaluates
(``nn_gate.cpp_expression``) and the columns of the cuts, on which the gate and the tau_ff skim selection are evaluated
with pandas.eval as in ShapeSmith (the sample-kind flags of the n-tuple stand in for ShapeSmith's own; the tau_control
selection is the gate's, cut by cut). Fails if the C++ and the pandas gate differ in an event or an event of the tau_ff
selection fails the gate. Prints one line per file and the totals per scope.

    source /cvmfs/sft.cern.ch/lcg/views/LCG_110/x86_64-el9-gcc16-opt/setup.sh
    export X509_USER_PROXY=...  PYTHONPATH=<CROWN root>
    python3 analysis_configurations/bbtautau/scripts/nn_gate_pass_fraction.py \\
        --base data=/store/user/sdaigler/CROWN/ntuples/smrun2_binned_v7/CROWNRun \\
        --base mc=/store/user/sdaigler/CROWN/ntuples/smrun2_binned_v7b/CROWNRun \\
        --database <KingMaker_sample_database>/nanoAOD_v15/datasets.json

With ``--skims <skim dir> ...`` (ShapeSmith skim directories, ``<dir>/<era>/<scope>/<nick>/*.parquet``) it checks
instead that every skimmed event passes the gate, with the gate columns the skims keep.
"""
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
import ROOT

from analysis_configurations.bbtautau import nn_gate
from analysis_configurations.bbtautau.constants import ERAS_RUN2


# the data and embedding n-tuples of a scope: its trigger stream or embedding channel
SCOPE_NICKS = {
    "et": ("EGamma_", "SingleElectron_", "_eltau_"),
    "mt": ("SingleMuon_", "_mutau_"),
    "tt": ("Tau_", "_tautau_"),
}


def nicks_by_type(server, base, database, era, data):
    """The n-tuple directories (sorted) of every sample type of ``era`` under ``base``: data only, or no data."""
    listing = subprocess.run(["xrdfs", server, "ls", f"{base}/{era}"], capture_output=True, text=True, check=True)
    nicks = defaultdict(list)
    for path in sorted(listing.stdout.split()):
        nick = path.rsplit("/", 1)[-1]
        sample_type = database.get(nick, {}).get("sample_type")
        if sample_type is not None and (sample_type == "data") == data:
            nicks[sample_type].append(nick)
    return nicks


def scope_nick(sample_type, nicks, scope):
    """The first nick, for data and embedding the first of the scope's stream or channel."""
    if sample_type in ("data", "embedding"):
        nicks = [nick for nick in nicks if any(key in nick for key in SCOPE_NICKS[scope])]
    return nicks[0] if nicks else None


def evaluate(cuts, frame):
    flags = np.ones(len(frame), dtype=bool)
    for cut in cuts.values():
        flags &= pd.eval(cut, resolvers=(frame,)).to_numpy(dtype=bool)
    return flags


def check_skim(args):
    """Events of one skim file and how many of them fail the gate."""
    path, era, scope = args
    import pyarrow.parquet as pq

    cuts = nn_gate.skim_cuts(scope, era)
    _, columns = nn_gate.cpp_expression(cuts)
    events = pq.read_table(path, columns=columns).to_pandas()
    return era, scope, len(events), int((~evaluate(cuts, events)).sum())


def check_skims(directories, eras, scopes, workers):
    from concurrent.futures import ProcessPoolExecutor
    from pathlib import Path

    jobs = [
        (str(path), era, scope)
        for directory in directories
        for era in eras
        for scope in scopes
        for path in sorted(Path(directory, era, scope).glob("*/*.parquet"))
    ]
    totals = defaultdict(lambda: np.zeros(2, dtype=np.int64))
    with ProcessPoolExecutor(workers) as pool:
        for era, scope, n, failed in pool.map(check_skim, jobs, chunksize=16):
            totals[(era, scope)] += (n, failed)
    for (era, scope), (n, failed) in sorted(totals.items()):
        print(f"{era:12} {scope}  skimmed events {n:9d}  failing the gate {failed}")
    print(f"{len(jobs)} skim files, {sum(t[0] for t in totals.values())} events, "
          f"{sum(t[1] for t in totals.values())} failing the gate")
    return all(t[1] == 0 for t in totals.values()) and bool(jobs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server", default="root://cmsdcache-kit-disk.gridka.de")
    parser.add_argument("--base", action="append", help="data=<path> and mc=<path> (MC and embedding)")
    parser.add_argument("--database", help="KingMaker sample database datasets.json")
    parser.add_argument("--skims", nargs="+", help="check these ShapeSmith skim directories instead")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--eras", nargs="+", default=list(ERAS_RUN2))
    parser.add_argument("--scopes", nargs="+", default=["et", "mt", "tt"])
    parser.add_argument("--json", help="write the counts to this file")
    args = parser.parse_args()
    if args.skims:
        sys.exit(0 if check_skims(args.skims, args.eras, args.scopes, args.workers) else 1)
    bases = dict(item.split("=", 1) for item in args.base)
    with open(args.database) as handle:
        database = json.load(handle)
    totals, rows, failures = defaultdict(lambda: np.zeros(4, dtype=np.int64)), [], []
    for era in args.eras:
        for kind, base in bases.items():
            for sample_type, nicks in sorted(nicks_by_type(args.server, base, database, era, kind == "data").items()):
                for scope in args.scopes:
                    nick = scope_nick(sample_type, nicks, scope)
                    if nick is None:
                        continue
                    url = f"{args.server}/{base}/{era}/{nick}/{scope}/{nick}_0.root"
                    gate = nn_gate.skim_cuts(scope, era)
                    expression, columns = nn_gate.cpp_expression(gate)
                    code = re.sub(r"\$(\d+)", lambda match: columns[int(match[1])], expression)
                    names = sorted(set(columns) | ({"mt_1"} if scope != "tt" else set()))  # mt_1: tau_ff only
                    frame = ROOT.RDataFrame("ntuple", url)
                    arrays = frame.Define("nn_gate_cpp", f"static_cast<bool>({code})").AsNumpy(
                        [*names, "nn_gate_cpp"]
                    )
                    cpp = arrays.pop("nn_gate_cpp").astype(bool)
                    events = pd.DataFrame({name: np.asarray(values) for name, values in arrays.items()})
                    passed = evaluate(gate, events)
                    tau_ff = evaluate(nn_gate.tau_ff_cuts(scope, era), events)
                    counts = np.array([len(events), passed.sum(), passed.sum(), tau_ff.sum()])
                    problems = []
                    if (cpp != passed).any():
                        problems.append(f"C++ and pandas gate differ in {(cpp != passed).sum()} events")
                    if (tau_ff & ~passed).any():
                        problems.append(f"{(tau_ff & ~passed).sum()} tau_ff events fail the gate")
                    failures += [f"{era} {sample_type} {scope}: {problem}" for problem in problems]
                    totals[scope] += counts
                    rows.append(dict(era=era, sample_type=sample_type, scope=scope, nick=nick, n_in=int(counts[0]),
                                     gate=int(counts[1]), tau_control=int(counts[2]), tau_ff=int(counts[3])))
                    fraction = counts[1] / max(counts[0], 1)
                    print(f"{era:12} {sample_type:18} {scope}  n_in {counts[0]:8d}  gate {counts[1]:7d} "
                          f"({fraction:6.2%})  tau_ff {counts[3]:7d}  {'; '.join(problems) or 'ok'}", flush=True)
    for scope, counts in totals.items():
        print(f"total {scope}: n_in {counts[0]}, gate {counts[1]} ({counts[1] / max(counts[0], 1):.2%}), "
              f"tau_ff {counts[3]} ({counts[3] / max(counts[0], 1):.2%})")
    if args.json:
        with open(args.json, "w") as handle:
            json.dump(rows, handle, indent=1)
    if failures:
        print("FAILED:\n" + "\n".join(failures))
        sys.exit(1)


if __name__ == "__main__":
    main()
