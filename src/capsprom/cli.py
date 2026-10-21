"""Command-line interface for the minimum viable CapsProm pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .config import load_experiment_config
from .canonical_neural import (
    prepare_canonical_neural_plan,
    refresh_canonical_final_fit_readiness,
    run_canonical_external_inference_job,
    run_canonical_final_fit_job,
    run_canonical_inner_fold_job,
)
from .data.batch_audit import audit_dataset_directory
from .experiment import audit_dataset_pair, run_experiment, validate_dataset
from .project_status import collect_project_status, write_status_snapshot
from .neural_experiment import load_neural_experiment_config, run_tracked_neural_training
from .feasibility import run_feasibility_suite


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
    neural_parser = subparsers.add_parser("train-neural")
    neural_parser.add_argument("config", type=Path)
    canonical_parser = subparsers.add_parser("prepare-neural-canonical")
    canonical_parser.add_argument("config", type=Path)
    canonical_parser.add_argument("output_dir", type=Path)
    fold_parser = subparsers.add_parser("run-neural-canonical-fold")
    fold_parser.add_argument("config", type=Path)
    fold_parser.add_argument("output_dir", type=Path)
    fold_parser.add_argument("dataset_id")
    fold_parser.add_argument("seed", type=int)
    fold_parser.add_argument("fold", type=int)
    readiness_parser = subparsers.add_parser("refresh-neural-canonical-readiness")
    readiness_parser.add_argument("config", type=Path)
    readiness_parser.add_argument("output_dir", type=Path)
    final_fit_parser = subparsers.add_parser("run-neural-canonical-final-fit")
    final_fit_parser.add_argument("config", type=Path)
    final_fit_parser.add_argument("output_dir", type=Path)
    final_fit_parser.add_argument("dataset_id")
    final_fit_parser.add_argument("seed", type=int)
    external_parser = subparsers.add_parser("run-neural-canonical-external-inference")
    external_parser.add_argument("config", type=Path)
    external_parser.add_argument("output_dir", type=Path)
    external_parser.add_argument("dataset_id")
    external_parser.add_argument("seed", type=int)
    external_parser.add_argument("evaluation_csv", type=Path)
    feasibility_parser = subparsers.add_parser("measure-neural-feasibility")
    feasibility_parser.add_argument("config", type=Path)
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
        if args.command == "train-neural":
            result = run_tracked_neural_training(load_neural_experiment_config(args.config))
            print(json.dumps({
                "run_id": result.run_id,
                "best_epoch": result.training.best_epoch,
                "best_inner_validation_mcc": result.training.best_validation_mcc,
            }, indent=2))
            return 0
        if args.command == "prepare-neural-canonical":
            report = prepare_canonical_neural_plan(args.config, args.output_dir)
            print(
                json.dumps(
                    {
                        "protocol_sha256": report["protocol_sha256"],
                        "phase": report["phase"],
                        "external_test_accessed": report["external_test_accessed"],
                        "dataset_count": report["dataset_count"],
                        "seed_count": report["seed_count"],
                        "fold_count": report["fold_count"],
                        "total_jobs": report["total_jobs"],
                        "completed_jobs": report["completed_jobs"],
                    },
                    indent=2,
                )
            )
            return 0
        if args.command == "run-neural-canonical-fold":
            report = run_canonical_inner_fold_job(
                args.config, args.output_dir, args.dataset_id, args.seed, args.fold
            )
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "refresh-neural-canonical-readiness":
            report = refresh_canonical_final_fit_readiness(
                args.config, args.output_dir
            )
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "run-neural-canonical-final-fit":
            report = run_canonical_final_fit_job(
                args.config, args.output_dir, args.dataset_id, args.seed
            )
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "run-neural-canonical-external-inference":
            report = run_canonical_external_inference_job(
                args.config,
                args.output_dir,
                args.dataset_id,
                args.seed,
                args.evaluation_csv,
            )
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "measure-neural-feasibility":
            report = run_feasibility_suite(args.config)
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
