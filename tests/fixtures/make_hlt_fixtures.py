"""Write the HLT and trigger-object fixtures of the Run-2 v15 trigger tests.

For every nick of the era's lists (sm_<era>_binned.txt, _embedding.txt,
_tau_id_measurement.txt) of the sample types data, dyjets, ttbar and embedding, the
first file of the nick is opened over xrootd and

- its HLT_* branch names are collected per era and kind (data, mc, embedding) into
  nanoaod_v15_<era>_<kind>_hlt.txt (the union over the files: data paths change
  between run periods);
- the muon, electron and tau parts of the TrigObj_filterBits doc string are parsed
  into nanoaod_v15_trigobj_filterbits.json, {era: {kind: {object: {bit: meaning}}}}
  (the bit schemes differ between 2016 and 2017/2018, and embedding adds its own
  bits).

Requires a grid proxy and uproot:

    python3 make_hlt_fixtures.py <KingMaker/sample_database/nanoAOD_v15> [workers]
"""
import concurrent.futures
import json
import re
import sys
from pathlib import Path

import uproot

HERE = Path(__file__).resolve().parent
LISTS = HERE.parents[1] / "sample_list"
ERAS = ("2016preVFP", "2016postVFP", "2017", "2018")
KINDS = {"data": "data", "dyjets": "mc", "ttbar": "mc", "embedding": "embedding"}
REDIRECTOR = "root://cms-xrd-global.cern.ch//"


def first_file(database, nick, entry):
    path = database / str(entry["era"]) / entry["sample_type"] / f"{nick}.json"
    url = json.loads(path.read_text())["filelist"][0]
    return re.sub(r"^root://[^/]+//+", REDIRECTOR, url)


def filter_bits(title):
    """{object: {bit: meaning}} of the muon, electron and tau parts of the doc string."""
    parts = {}
    for part in title.split(";"):
        match = re.match(r"(.*) for (Muon|Electron|Tau)$", part.strip(), re.S)
        if match:
            items = re.split(r",\s*(?=\d+ =>)", match.group(1))
            parts[match.group(2)] = {
                int(item.split("=>")[0]): item.split("=>", 1)[1].strip() for item in items
            }
    return parts


def read(url):
    with uproot.open(url, timeout=180) as file:
        events = file["Events"]
        hlt = {name for name in events.keys() if name.startswith("HLT_")}
        return hlt, filter_bits(events["TrigObj_filterBits"].title)


def main():
    database = Path(sys.argv[1])
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    datasets = json.loads((database / "datasets.json").read_text())
    jobs = set()
    for era in ERAS:
        for name in ("binned", "embedding", "tau_id_measurement"):
            for nick in (LISTS / f"sm_{era}_{name}.txt").read_text().split():
                entry = datasets[nick]
                if entry["sample_type"] in KINDS:
                    jobs.add((era, KINDS[entry["sample_type"]], first_file(database, nick, entry)))
    jobs = sorted(jobs)
    hlt, bits = {}, {}
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        for (era, kind, url), (paths, meanings) in zip(jobs, pool.map(lambda job: read(job[2]), jobs)):
            hlt.setdefault((era, kind), set()).update(paths)
            previous = bits.setdefault(era, {}).setdefault(kind, meanings)
            assert previous == meanings, (era, kind, url)
    for (era, kind), paths in hlt.items():
        (HERE / f"nanoaod_v15_{era}_{kind}_hlt.txt").write_text("".join(f"{p}\n" for p in sorted(paths)))
    (HERE / "nanoaod_v15_trigobj_filterbits.json").write_text(
        json.dumps(bits, indent=1, sort_keys=True)
    )


if __name__ == "__main__":
    main()
