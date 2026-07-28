#!/usr/bin/env python3

import ROOT
import argparse
from pathlib import Path
import json
import os


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-file",
        "-i",
        type=lambda x: Path(x).resolve(),
        required=True,
        help="The input NTuple file",
    )
    parser.add_argument(
        "--output-file",
        "-o",
        type=lambda x: Path(x).resolve(),
        required=True,
        help="The output quantities map file",
    )
    parser.add_argument(
        "--lib-dir",
        "-l",
        type=str,
        required=True,
        help="The directory with compiled library files",
    )
    parser.add_argument(
        "--era",
        "-e",
        type=str,
        required=True,
        help="The data-taking era",
    )
    parser.add_argument(
        "--sample-type",
        "-s",
        type=str,
        required=True,
        help="The sample type of the processed file",
    )
    parser.add_argument(
        "--scope",
        "-c",
        type=str,
        required=True,
        help="The scope/analysis channel for which the sample has been processed",
    )
    args = parser.parse_args()
    return args

def extract_quantities_map(input_file, lib_dir):
    print(f"Reading quantities Map from {input_file}")
    # Load dict parsing lib
    lib_path = os.path.abspath(os.path.join(lib_dir, "libMyDicts.so"))
    # Physical file check
    if not os.path.exists(lib_path):
        raise FileNotFoundError(f"Missing library: {lib_path}")
    # Evaluate ROOT-specific return codes
    result = ROOT.gSystem.Load(lib_path)
    if result < 0:
        err_type = (
            "Version mismatch" if result == -2 else "Linker error/Missing dependency"
        )
        raise ImportError(f"Load failed ({result}): {err_type} for {lib_path}")

    f = ROOT.TFile.Open(str(input_file))
    name = "shift_quantities_map"
    m = f.Get(name)
    data = {}
    for shift, quantities in m:
        data[str(shift)] = sorted([str(quantity) for quantity in quantities])
    metadata = json.loads(f.Get("metadata").GetString().Data())["metadata"]
    f.Close()
    print(f"Successfully read quantities map from {input_file}")
    return data, metadata


def read_quantities_map(input_file, era, sample_type, scope, output_file, lib_dir):
    data, metadata = extract_quantities_map(input_file, lib_dir)
    if not (era == metadata["era"] and sample_type == metadata["sample_type"]):
        raise ValueError(
            f"Input file {input_file} does not match requested era {era}/{metadata['era']} or sample_type {sample_type}/{metadata['sample_type']}."
        )
    output = {"quantities": {era: {sample_type: {scope: data}}}, "metadata": metadata}
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output, f, indent=4)


def main():
    # Parse arguments
    args = parse_arguments()
    input_file = args.input_file
    output_file = args.output_file
    lib_dir = args.lib_dir
    era = args.era
    sample_type = args.sample_type
    scope = args.scope

    # Write the quantity map
    read_quantities_map(input_file, era, sample_type, scope, output_file, lib_dir)


if __name__ == "__main__":
    main()