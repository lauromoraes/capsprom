"""Independently audit reconstructed GraphPro train--test splits."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path

from capsprom.data.loading import sha256_file
from capsprom.data.similarity_groups import audit_cross_partition_similarity
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    datasets = []
    for dataset_dir in sorted(path for path in args.input_dir.iterdir() if path.is_dir()):
        train_path = dataset_dir / "train.csv"
        test_path = dataset_dir / "test.csv"
        train_rows = _read_rows(train_path)
        test_rows = _read_rows(test_path)
        audits = audit_cross_partition_similarity(
            [(row["sequence"], int(row["label"])) for row in train_rows],
            [(row["sequence"], int(row["label"])) for row in test_rows],
        )
        train_pairs = {row["pair_id"] for row in train_rows}
        test_pairs = {row["pair_id"] for row in test_rows}
        train_groups = {row["similarity_group_id"] for row in train_rows}
        test_groups = {row["similarity_group_id"] for row in test_rows}
        class_counts = {
            partition: {
                str(label): sum(int(row["label"]) == label for row in rows)
                for label in (0, 1)
            }
            for partition, rows in (("train", train_rows), ("test", test_rows))
        }
        datasets.append(
            {
                "dataset": dataset_dir.name,
                "train_sha256": sha256_file(train_path),
                "test_sha256": sha256_file(test_path),
                "train_rows": len(train_rows),
                "test_rows": len(test_rows),
                "class_counts": class_counts,
                "pair_overlap": len(train_pairs & test_pairs),
                "similarity_group_overlap": len(train_groups & test_groups),
                "cross_partition_similarity": [asdict(item) for item in audits],
            }
        )

    summary = {
        "schema_version": 1,
        "input_dir": str(args.input_dir),
        "split_summary_sha256": sha256_file(args.input_dir / "split_summary.json"),
        "dataset_count": len(datasets),
        "total_train_rows": sum(item["train_rows"] for item in datasets),
        "total_test_rows": sum(item["test_rows"] for item in datasets),
        "all_balanced": all(
            item["class_counts"][partition]["0"]
            == item["class_counts"][partition]["1"]
            for item in datasets
            for partition in ("train", "test")
        ),
        "total_pair_overlap": sum(item["pair_overlap"] for item in datasets),
        "total_similarity_group_overlap": sum(
            item["similarity_group_overlap"] for item in datasets
        ),
        "total_cross_partition_edges_at_8": sum(
            item["cross_partition_similarity"][-1]["neighbor_edges"]
            for item in datasets
        ),
        "datasets": datasets,
    }
    write_json_atomic(args.output, summary)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    main()
