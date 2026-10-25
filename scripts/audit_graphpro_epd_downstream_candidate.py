"""Audit treated EPD downstream controls for distribution and dependencies."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile

import numpy as np
from scipy.stats import ks_2samp, mannwhitneyu
import yaml

from capsprom.data.dependency import audit_named_sequence_dependencies
from capsprom.data.distribution_audit import (
    maximum_positional_total_variation,
    summarize_class_distribution,
)
from capsprom.data.loading import sha256_file
from capsprom.data.sequences import read_fasta
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/graphpro_epd_downstream_candidate_audit_v1.yaml"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")

    candidates = _load_candidates(config["inputs"])
    distributions = []
    for dataset_id, labels in candidates.items():
        positive = sorted(labels[1])
        negative = sorted(labels[0])
        positive_gc = _gc(positive)
        negative_gc = _gc(negative)
        position, distance = maximum_positional_total_variation(positive, negative)
        mann_whitney = mannwhitneyu(positive_gc, negative_gc, alternative="two-sided")
        ks = ks_2samp(positive_gc, negative_gc, alternative="two-sided")
        distributions.append(
            {
                "dataset_id": dataset_id,
                "positive": asdict(summarize_class_distribution(positive)),
                "negative": asdict(summarize_class_distribution(negative)),
                "gc_mean_difference_positive_minus_negative": float(
                    positive_gc.mean() - negative_gc.mean()
                ),
                "mann_whitney_p": float(mann_whitney.pvalue),
                "ks_statistic": float(ks.statistic),
                "ks_p": float(ks.pvalue),
                "maximum_positional_total_variation_position": position,
                "maximum_positional_total_variation": distance,
            }
        )
    _add_holm(distributions, "mann_whitney_p", "mann_whitney_holm_p")
    _add_holm(distributions, "ks_p", "ks_holm_p")

    all_datasets = _load_confirmatory(config["inputs"])
    all_datasets.update(candidates)
    dependency = audit_named_sequence_dependencies(all_datasets)
    candidate_ids = set(candidates)
    candidate_overlaps = [
        row
        for row in dependency["overlaps"]
        if row["left_dataset_id"] in candidate_ids or row["right_dataset_id"] in candidate_ids
    ]

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent
    ) as temporary:
        staging = Path(temporary) / args.output_dir.name
        staging.mkdir()
        write_json_atomic(staging / "distribution_summary.json", {"datasets": distributions})
        write_json_atomic(
            staging / "dependency_audit.json",
            {**dependency, "overlaps_involving_downstream_candidates": candidate_overlaps},
        )
        write_json_atomic(
            staging / "audit_manifest.json",
            {
                "schema_version": 1,
                "audit_identity": config["audit"]["name"],
                "config_sha256": sha256_file(args.config),
                "candidate_dataset_count": len(candidates),
                "dependency_dataset_count": dependency["dataset_count"],
                "candidate_overlap_pair_count": len(candidate_overlaps),
                "outputs": {
                    path.name: sha256_file(path)
                    for path in staging.iterdir()
                    if path.name != "audit_manifest.json"
                },
                "split_generation_enabled": False,
                "model_training_enabled": False,
                "confirmatory_use_enabled": False,
            },
        )
        os.replace(staging, args.output_dir)
    print(json.dumps({"distributions": distributions, "overlaps": candidate_overlaps}, indent=2))


def _load_candidates(inputs: dict[str, object]) -> dict[str, dict[int, set[str]]]:
    root = Path(str(inputs["treated_root"]))
    identity_prefix = str(inputs.get("candidate_dataset_identity", "graphpro-epd-downstream-treated-v1"))
    datasets = {}
    for item in inputs["datasets"]:
        organism = item["organism"]
        positive_path = root / organism / "positive.fa"
        negative_path = root / organism / "negative.fa"
        _verify_hash(positive_path, item["positive_sha256"])
        _verify_hash(negative_path, item["negative_sha256"])
        datasets[f"{identity_prefix}-{organism}"] = {
            1: {record.sequence for record in read_fasta(positive_path)},
            0: {record.sequence for record in read_fasta(negative_path)},
        }
    return datasets


def _load_confirmatory(inputs: dict[str, object]) -> dict[str, dict[int, set[str]]]:
    manifest = yaml.safe_load(Path(str(inputs["dependency_manifest"])).read_text(encoding="utf-8"))
    root = Path(str(inputs["confirmatory_root"]))
    datasets = {}
    for item in manifest["datasets"]:
        dataset_id = item["dataset_id"]
        paths = sorted(root.glob(f"{dataset_id}-p-*-n-*-*.csv"))
        if len(paths) != 2:
            raise ValueError(f"expected train and test files for {dataset_id}")
        labels = {0: set(), 1: set()}
        for path in paths:
            with path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    labels[int(row["label"])].add(row["sequence"].strip().upper())
        datasets[dataset_id] = labels
    return datasets


def _gc(sequences: list[str]) -> np.ndarray:
    return np.asarray(
        [(sequence.count("G") + sequence.count("C")) / len(sequence) for sequence in sequences]
    )


def _add_holm(rows: list[dict[str, object]], source: str, target: str) -> None:
    ordered = sorted(enumerate(rows), key=lambda item: float(item[1][source]))
    adjusted = [0.0] * len(rows)
    running = 0.0
    for rank, (index, row) in enumerate(ordered):
        running = max(running, min(1.0, float(row[source]) * (len(rows) - rank)))
        adjusted[index] = running
    for row, value in zip(rows, adjusted, strict=True):
        row[target] = value


def _verify_hash(path: Path, expected: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: expected {expected}, observed {observed}")


if __name__ == "__main__":
    main()
