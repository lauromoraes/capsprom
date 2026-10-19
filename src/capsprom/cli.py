"""Command-line interface for the minimum viable CapsProm pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .config import load_experiment_config
from .data.batch_audit import audit_dataset_directory
from .experiment import audit_dataset_pair, run_experiment, validate_dataset
from .project_status import collect_project_status, write_status_snapshot


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="capsprom", description="Run reproducible CapsProm experiments.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate-config", "validate-data", "audit-data", "run"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("config", type=Path)
    batch_audit = subparsers.add_parser("audit-datasets")
    batch_audit.add_argument("input_dir", type=Path)
    batch_audit.add_argument("output_dir", type=Path)
    batch_audit.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="Source prefix to include; repeat for multiple sources",
    )
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--write", type=Path, help="Write a compact JSON snapshot")
    args = parser.parse_args(argv)

    try:
        if args.command == "status":
            report = write_status_snapshot(args.write) if args.write else collect_project_status()
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "audit-datasets":
            sources = tuple(args.sources or ("cdbprom", "cnnprom", "graphpro"))
            report = audit_dataset_directory(args.input_dir, args.output_dir, sources=sources)
            print(json.dumps(report, indent=2))
            return 0
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
