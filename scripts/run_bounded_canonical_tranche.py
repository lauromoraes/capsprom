"""Run exactly the inner folds authorized by a bounded campaign release."""

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
    gates = release["execution_gates"]
    folds = [int(fold) for fold in scope["folds"]]
    seeds = [int(seed) for seed in scope.get("seeds", [scope.get("seed")])]
    if len(set(seeds)) != len(seeds):
        raise ValueError("release repeats a seed")
    if scope["maximum_new_inner_fits"] != len(folds) * len(seeds):
        raise ValueError("released fold count differs from the bounded maximum")
    if not gates["authorized_inner_folds_enabled"]:
        raise ValueError("bounded inner-fold execution is disabled")
    if any(
        gates[name]
        for name in (
            "additional_inner_folds_enabled",
            "final_fits_enabled",
            "external_test_enabled",
            "embedding_jobs_enabled",
        )
    ):
        raise ValueError("release opens a gate outside the bounded inner folds")

    command_prefix = [
        sys.executable,
        "-m",
        "capsprom",
        "run-neural-canonical-fold",
        str(args.contract),
        str(args.output_dir),
        str(scope["dataset_id"]),
    ]
    exit_code = 0
    try:
        for seed in seeds:
            for fold in folds:
                subprocess.run([*command_prefix, str(seed), str(fold)], check=True)
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
