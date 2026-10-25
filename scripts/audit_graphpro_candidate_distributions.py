"""Audit GraphPro candidate distributions and cross-dataset dependencies."""

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
        "--config", type=Path, default=Path("configs/graphpro_candidate_audit_v1.yaml")
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")
    _verify_inputs(config["inputs"])

    candidates = _load_candidates(config["inputs"])
    distributions = []
    for dataset_id, data in candidates.items():
        positive = sorted(data[1])
        negative = sorted(data[0])
        positive_gc = _gc(positive)
        negative_gc = _gc(negative)
        position, distance = maximum_positional_total_variation(positive, negative)
        distributions.append(
            {
                "dataset_id": dataset_id,
                "family": "reconstructed" if "reconstructed" in dataset_id else "released_integrity_view",
                "positive": asdict(summarize_class_distribution(positive)),
                "negative": asdict(summarize_class_distribution(negative)),
                "gc_mean_difference_positive_minus_negative": float(
                    positive_gc.mean() - negative_gc.mean()
                ),
                "mann_whitney_u": float(
                    mannwhitneyu(positive_gc, negative_gc, alternative="two-sided").statistic
                ),
                "mann_whitney_p": float(
                    mannwhitneyu(positive_gc, negative_gc, alternative="two-sided").pvalue
                ),
                "ks_statistic": float(
                    ks_2samp(positive_gc, negative_gc, alternative="two-sided").statistic
                ),
                "ks_p": float(
                    ks_2samp(positive_gc, negative_gc, alternative="two-sided").pvalue
                ),
                "maximum_positional_total_variation_position": position,
                "maximum_positional_total_variation": distance,
                "paired_gc_absolute_difference": _paired_gc_summary(
                    Path(config["inputs"]["bacterial_root"])
                    / dataset_id.removeprefix("graphpro-reconstructed-v2-").upper()
                    / "pair_ledger.csv"
                )
                if "reconstructed" in dataset_id
                else None,
            }
        )
    _add_holm(distributions, "mann_whitney_p", "mann_whitney_holm_p")
    _add_holm(distributions, "ks_p", "ks_holm_p")

    all_datasets = _load_confirmatory(config["inputs"])
    all_datasets.update(candidates)
    dependency = audit_named_sequence_dependencies(all_datasets)
    candidate_ids = set(candidates)
    dependency["overlaps_involving_graphpro_candidates"] = [
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
        _write_distribution_csv(staging / "distribution_summary.csv", distributions)
        write_json_atomic(staging / "distribution_summary.json", {"datasets": distributions})
        write_json_atomic(staging / "dependency_audit.json", dependency)
        write_json_atomic(
            staging / "audit_manifest.json",
            {
                "schema_version": 1,
                "audit_identity": config["audit"]["name"],
                "config_sha256": sha256_file(args.config),
                "candidate_dataset_count": len(candidates),
                "dependency_dataset_count": dependency["dataset_count"],
                "overlapping_pair_count": dependency["overlapping_pair_count"],
                "candidate_overlap_pair_count": len(
                    dependency["overlaps_involving_graphpro_candidates"]
                ),
                "outputs": {
                    path.name: sha256_file(path)
                    for path in staging.iterdir()
                    if path.name != "audit_manifest.json"
                },
                "model_training_enabled": False,
                "confirmatory_use_enabled": False,
            },
        )
        os.replace(staging, args.output_dir)
    print(
        json.dumps(
            {
                "candidate_datasets": len(candidates),
                "dependency_datasets": dependency["dataset_count"],
                "candidate_overlap_pairs": len(
                    dependency["overlaps_involving_graphpro_candidates"]
                ),
            },
            indent=2,
        )
    )


def _load_candidates(inputs: dict[str, str]) -> dict[str, dict[int, set[str]]]:
    datasets = {}
    bacterial_root = Path(inputs["bacterial_root"])
    for path in sorted(item for item in bacterial_root.iterdir() if item.is_dir()):
        datasets[f"graphpro-reconstructed-v2-{path.name.lower()}"] = {
            1: {record.sequence for record in read_fasta(path / "positive.fa")},
            0: {record.sequence for record in read_fasta(path / "negative.fa")},
        }
    eukaryotic_root = Path(inputs["eukaryotic_root"])
    for organism in ("human", "mouse"):
        datasets[f"graphpro-released-integrity-v1-{organism}"] = {
            1: {
                record.sequence
                for record in read_fasta(eukaryotic_root / organism / "positive.fa")
            },
            0: {
                record.sequence
                for record in read_fasta(eukaryotic_root / organism / "negative.fa")
            },
        }
    return datasets


def _load_confirmatory(inputs: dict[str, str]) -> dict[str, dict[int, set[str]]]:
    manifest = yaml.safe_load(Path(inputs["dependency_manifest"]).read_text(encoding="utf-8"))
    root = Path(inputs["confirmatory_root"])
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


def _paired_gc_summary(ledger_path: Path) -> dict[str, float]:
    with ledger_path.open(encoding="utf-8", newline="") as handle:
        differences = np.asarray(
            [
                abs(float(row["positive_gc"]) - float(row["negative_gc"]))
                for row in csv.DictReader(handle)
            ]
        )
    return {
        "mean": float(differences.mean()),
        "maximum": float(differences.max()),
        "q95": float(np.quantile(differences, 0.95)),
    }


def _add_holm(rows: list[dict[str, object]], source: str, target: str) -> None:
    ordered = sorted(enumerate(rows), key=lambda item: float(item[1][source]))
    adjusted = [0.0] * len(rows)
    running = 0.0
    for rank, (index, row) in enumerate(ordered):
        running = max(running, min(1.0, float(row[source]) * (len(rows) - rank)))
        adjusted[index] = running
    for row, value in zip(rows, adjusted, strict=True):
        row[target] = value


def _write_distribution_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "dataset_id",
        "family",
        "positive_count",
        "negative_count",
        "positive_gc_mean",
        "negative_gc_mean",
        "gc_mean_difference_positive_minus_negative",
        "mann_whitney_p",
        "mann_whitney_holm_p",
        "ks_statistic",
        "ks_p",
        "ks_holm_p",
        "maximum_positional_total_variation_position",
        "maximum_positional_total_variation",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{key: row[key] for key in fields if key in row},
                    "positive_count": row["positive"]["count"],
                    "negative_count": row["negative"]["count"],
                    "positive_gc_mean": row["positive"]["gc_mean"],
                    "negative_gc_mean": row["negative"]["gc_mean"],
                }
            )


def _verify_inputs(inputs: dict[str, str]) -> None:
    checks = (
        (Path(inputs["bacterial_root"]) / "build_summary.json", inputs["bacterial_summary_sha256"]),
        (Path(inputs["eukaryotic_root"]) / "treatment_summary.json", inputs["eukaryotic_summary_sha256"]),
        (Path(inputs["dependency_manifest"]), inputs["dependency_manifest_sha256"]),
    )
    for path, expected in checks:
        observed = sha256_file(path)
        if observed != expected:
            raise ValueError(f"hash mismatch for {path}: expected {expected}, observed {observed}")


if __name__ == "__main__":
    main()
