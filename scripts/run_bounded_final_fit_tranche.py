"""Run exactly the final fits authorized by a bounded final-fit release."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--exit-code-path", type=Path, required=True)
    args = parser.parse_args()

    release = yaml.safe_load(args.release.read_text(encoding="utf-8"))
    scope = release["scope"]
    dataset_ids = [str(item) for item in scope["dataset_ids"]]
    seeds = [int(seed) for seed in scope["seeds"]]
    if len(set(dataset_ids)) != len(dataset_ids) or len(set(seeds)) != len(seeds):
        raise ValueError("release repeats a dataset or seed")
    if scope["maximum_new_final_fits"] != len(dataset_ids) * len(seeds):
        raise ValueError("released final-fit count differs from the bounded maximum")
    # Each final fit rechecks the release gates, scope, and contract hash itself.

    command_prefix = [
        sys.executable,
        "-m",
        "capsprom",
        "run-neural-canonical-final-fit",
        str(args.contract),
        str(args.output_dir),
    ]
    exit_code = 0
    try:
        for dataset_id in dataset_ids:
            for seed in seeds:
                subprocess.run(
                    [*command_prefix, dataset_id, str(seed), "--release", str(args.release)],
                    check=True,
                )
    except subprocess.CalledProcessError as exc:
        exit_code = int(exc.returncode)
    finally:
        args.exit_code_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.exit_code_path.with_suffix(args.exit_code_path.suffix + ".tmp")
        temporary.write_text(f"{exit_code}\n", encoding="utf-8")
        os.replace(temporary, args.exit_code_path)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
