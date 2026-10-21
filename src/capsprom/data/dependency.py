"""Cross-dataset sequence-dependency auditing."""

from __future__ import annotations

import csv
import re
from itertools import combinations
from pathlib import Path


def audit_cross_dataset_dependency(dataset_dir: Path) -> dict[str, object]:
    """Return deterministic pairwise overlap counts by source label."""

    datasets: dict[str, dict[int, set[str]]] = {}
    for train_path in sorted(dataset_dir.glob("*-train.csv")):
        dataset_id = re.sub(r"-p-\d+-n-\d+-train$", "", train_path.stem)
        test_paths = sorted(dataset_dir.glob(f"{dataset_id}-p-*-n-*-test.csv"))
        if len(test_paths) != 1:
            raise ValueError(f"{dataset_id} must have exactly one test partition")
        labels = {0: set(), 1: set()}
        for path in (train_path, test_paths[0]):
            with path.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    labels[int(row["label"])].add(row["sequence"].strip().upper())
        datasets[dataset_id] = labels

    overlaps = []
    for left, right in combinations(sorted(datasets), 2):
        counts = {
            "same_label_0": len(datasets[left][0] & datasets[right][0]),
            "same_label_1": len(datasets[left][1] & datasets[right][1]),
            "left_0_right_1": len(datasets[left][0] & datasets[right][1]),
            "left_1_right_0": len(datasets[left][1] & datasets[right][0]),
        }
        total = sum(counts.values())
        if total:
            overlaps.append(
                {"left_dataset_id": left, "right_dataset_id": right, "total": total, **counts}
            )
    return {
        "schema_version": 1,
        "dataset_count": len(datasets),
        "overlapping_pair_count": len(overlaps),
        "overlaps": overlaps,
    }
