"""Build deterministic similarity-grouped splits for reconstructed datasets."""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from pathlib import Path

import yaml

from capsprom.data.loading import sha256_file
from capsprom.data.similarity_groups import (
    assign_components_to_partitions,
    similarity_components,
)
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/graphpro_reconstructed_split_v1.yaml")
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    split = config["split"]
    grouping = config["grouping"]
    partition = config["partition"]
    input_root = Path(split["input_root"])
    _verify_hash(input_root / "build_summary.json", split["input_build_summary_sha256"])
    _verify_hash(Path(split["reconstruction_contract"]), split["reconstruction_contract_sha256"])
    _verify_hash(Path(split["source_registry"]), split["source_registry_sha256"])
    _verify_hash(Path(grouping["similarity_audit"]), grouping["similarity_audit_sha256"])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for dataset_dir in sorted(path for path in input_root.iterdir() if path.is_dir()):
        final_dir = args.output_dir / dataset_dir.name
        if final_dir.exists():
            raise FileExistsError(f"refusing to overwrite existing split {final_dir}")
        ledger_path = dataset_dir / "pair_ledger.csv"
        with ledger_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        pairs = [(row["positive_sequence"], row["negative_sequence"]) for row in rows]
        components = similarity_components(pairs, int(grouping["hamming_threshold"]))
        assignments = assign_components_to_partitions(
            components,
            pair_count=len(pairs),
            test_fraction=float(partition["test_fraction"]),
            seed=int(partition["seed"]),
            dataset_id=dataset_dir.name,
        )
        group_by_pair = {
            pair_index: f"similarity-{component[0]:06d}"
            for component in components
            for pair_index in component
        }
        with tempfile.TemporaryDirectory(prefix=f".{dataset_dir.name}.", dir=args.output_dir) as temporary:
            staging = Path(temporary) / dataset_dir.name
            staging.mkdir()
            output_paths = {}
            for partition_name, pair_indices in assignments.items():
                output_path = staging / f"{partition_name}.csv"
                _write_partition(output_path, rows, pair_indices, group_by_pair, dataset_dir.name)
                output_paths[partition_name] = output_path
            train_groups = {group_by_pair[index] for index in assignments["train"]}
            test_groups = {group_by_pair[index] for index in assignments["test"]}
            if train_groups & test_groups:
                raise AssertionError("similarity component crossed the partition boundary")
            manifest = {
                "schema_version": 1,
                "dataset": dataset_dir.name,
                "split_config_sha256": sha256_file(args.config),
                "pair_ledger_sha256": sha256_file(ledger_path),
                "pair_count": len(pairs),
                "similarity_threshold": int(grouping["hamming_threshold"]),
                "component_count": len(components),
                "largest_component_pairs": max(map(len, components)),
                "train_pairs": len(assignments["train"]),
                "test_pairs": len(assignments["test"]),
                "train_rows": 2 * len(assignments["train"]),
                "test_rows": 2 * len(assignments["test"]),
                "train_test_group_overlap": len(train_groups & test_groups),
                "outputs": {name: sha256_file(path) for name, path in output_paths.items()},
            }
            write_json_atomic(staging / "split_manifest.json", manifest)
            os.replace(staging, final_dir)
        summaries.append(manifest)
        print(json.dumps(manifest, indent=2))
    write_json_atomic(
        args.output_dir / "split_summary.json",
        {
            "schema_version": 1,
            "split_config": str(args.config),
            "split_config_sha256": sha256_file(args.config),
            "dataset_count": len(summaries),
            "total_pairs": sum(item["pair_count"] for item in summaries),
            "total_train_rows": sum(item["train_rows"] for item in summaries),
            "total_test_rows": sum(item["test_rows"] for item in summaries),
            "datasets": summaries,
        },
    )


def _write_partition(
    path: Path,
    source_rows: list[dict[str, str]],
    pair_indices: list[int],
    group_by_pair: dict[int, str],
    dataset: str,
) -> None:
    fields = ["row_id", "pair_id", "similarity_group_id", "sequence", "label"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for pair_index in pair_indices:
            source = source_rows[pair_index]
            pair_id = f"{dataset}-pair-{pair_index:06d}"
            for label, key in ((1, "positive_sequence"), (0, "negative_sequence")):
                writer.writerow(
                    {
                        "row_id": f"{pair_id}-label-{label}",
                        "pair_id": pair_id,
                        "similarity_group_id": group_by_pair[pair_index],
                        "sequence": source[key],
                        "label": label,
                    }
                )


def _verify_hash(path: Path, expected: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"hash mismatch for {path}: expected {expected}, observed {observed}")


if __name__ == "__main__":
    main()
