"""Command-line interface for the minimum viable CapsProm pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .config import load_experiment_config
from .experiment import audit_dataset_pair, run_experiment, validate_dataset


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="capsprom", description="Run reproducible CapsProm experiments.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate-config", "validate-data", "audit-data", "run"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("config", type=Path)
    args = parser.parse_args(argv)

    try:
        config = load_experiment_config(args.config)
        if args.command == "validate-config":
            print(f"Valid configuration: {config.path}")
        elif args.command == "validate-data":
            reports = [
                validate_dataset(config.data.train_csv, config.data),
                validate_dataset(config.data.test_csv, config.data),
            ]
            print(json.dumps(reports, indent=2))
        elif args.command == "audit-data":
            print(json.dumps(audit_dataset_pair(config.data), indent=2))
        else:
            result = run_experiment(config)
            print(json.dumps({"run_id": result.run_id, "output_dir": str(result.output_dir), "metrics": result.metrics}, indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0
