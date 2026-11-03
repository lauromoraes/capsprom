"""Build homology-grouped, domain-window partitions of the 18 eligible datasets.

Prokaryotic datasets pool the v3 filtered records of train and test; eukaryotic
datasets are rebuilt from canonical collections at the native 251-nt window
through the v3 filter stages.  Every dataset is grouped by MMseqs2 alignment
and exact Hamming edges (homology grouping v1), partitioned by whole groups,
and written once, atomically.  Datasets already written are skipped, so the
run can resume.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import tempfile
from pathlib import Path

import yaml

from capsprom.data.grouped_builds import filter_canonical_rows
from capsprom.data.homology_grouping import (
    GroupingRecord,
    SearchSettings,
    alignment_edges,
    connected_groups,
    cross_partition_edges,
    grouping_report,
    hamming_edges,
    partition_groups,
    run_mmseqs_search,
)
from capsprom.data.loading import sha256_file
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/grouped_domain_window_build_v1.yaml"))
    parser.add_argument("--mmseqs", type=Path, required=True)
    parser.add_argument("--dataset", action="append", help="restrict to a dataset_id (repeatable)")
    parser.add_argument("--threads", type=int, default=None)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    grouping = config["grouping"]
    if not config["execution_gates"]["build_enabled"]:
        raise SystemExit("build gate is closed")
    if sha256_file(args.mmseqs) != grouping["mmseqs2_binary_sha256"]:
        raise SystemExit("MMseqs2 binary hash differs from the contract")
    for key, path in (("protocol_sha256", grouping["protocol"]),):
        if sha256_file(Path(path)) != grouping[key]:
            raise ValueError(f"hash mismatch: {path}")
    if sha256_file(Path(config["build"]["evaluation_protocol"])) != config["build"]["evaluation_protocol_sha256"]:
        raise ValueError("evaluation protocol hash mismatch")
    protocol = yaml.safe_load(Path(grouping["protocol"]).read_text(encoding="utf-8"))
    settings = SearchSettings.from_config(protocol["search"])
    if args.threads:
        settings = SearchSettings(**{**settings.__dict__, "threads": args.threads})
    root = Path(config["output_root"])
    root.mkdir(parents=True, exist_ok=True)
    config_sha256 = sha256_file(args.config)
    for dataset in config["datasets"]:
        if args.dataset and dataset["dataset_id"] not in args.dataset:
            continue
        target = root / dataset["dataset_id"]
        if target.exists():
            print(json.dumps({dataset["dataset_id"]: "already_built"}))
            continue
        result = _build(dataset, config, protocol, settings, args.mmseqs, root, target, config_sha256)
        print(json.dumps({dataset["dataset_id"]: result}), flush=True)


def _records(dataset: dict) -> tuple[list[GroupingRecord], dict[str, str], dict]:
    source = dataset["source"]
    v3_partition: dict[str, str] = {}
    records = []
    if dataset["derivation"] == "native":
        path = Path(source["path"])
        if sha256_file(path) != source["sha256"]:
            raise ValueError(f"canonical hash mismatch: {path}")
        kept, counts = filter_canonical_rows(csv.DictReader(gzip.open(path, "rt", encoding="utf-8")))
        lengths = {len(row["sequence"]) for row in kept}
        if lengths != {dataset["window_nt"]}:
            raise ValueError(f"{dataset['dataset_id']}: lengths {lengths} differ from the domain window")
        records = [GroupingRecord(row["record_id"], row["sequence"], int(row["label"]), row["record_id"]) for row in kept]
        return records, v3_partition, counts
    for entry in source["files"]:
        path = Path(entry["path"])
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"v3 file hash mismatch: {path}")
        split = "test" if path.name.endswith("-test.csv") else "train"
        for index, row in enumerate(csv.DictReader(path.open(encoding="utf-8"))):
            record_id = f"{dataset['dataset_id']}:v3-{split}:{index:06d}"
            v3_partition[record_id] = split
            records.append(GroupingRecord(record_id, row["sequence"].strip().upper(), int(row["label"]), record_id))
    if {len(r.sequence) for r in records} != {dataset["window_nt"]}:
        raise ValueError(f"{dataset['dataset_id']}: v3 records are not {dataset['window_nt']} nt")
    return records, v3_partition, {"input": len(records), "kept": len(records)}


def _build(dataset, config, protocol, settings, mmseqs, root, target, config_sha256) -> dict:
    grouping = config["grouping"]
    records, v3_partition, filter_counts = _records(dataset)
    staging = Path(tempfile.mkdtemp(prefix=f".{dataset['dataset_id']}-", dir=root))
    try:
        search = run_mmseqs_search(records, staging / "mmseqs", mmseqs, settings)
        shutil.rmtree(staging / "mmseqs" / "tmp", ignore_errors=True)
        edges = {
            "alignment": alignment_edges(Path(search["hits"]), settings),
            "hamming": hamming_edges(records, protocol["grouping"]["hamming_edge"]["max_mismatch_fraction"]),
        }
        groups = connected_groups(records, edges)
        report = grouping_report(records, groups, protocol["grouping"]["max_component_fraction"])
        if report["oversized"]:
            raise RuntimeError(f"{dataset['dataset_id']}: largest group exceeds the review limit; not partitioned")
        assignment = partition_groups(
            records,
            groups,
            test_fraction=grouping["test_fraction"],
            seed=grouping["assignment_seed"],
            folds=grouping["inner_folds"],
            fold_seed=grouping["inner_fold_seed"],
        )
        crossing = cross_partition_edges(groups, assignment)
        if any(crossing.values()):
            raise AssertionError(f"cross-partition edges remain: {crossing}")
        with (staging / "records.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["record_id", "label", "sequence", "group", "partition", "v3_partition"])
            for record in records:
                writer.writerow([record.record_id, record.label, record.sequence, groups.group_of[record.record_id], assignment[record.record_id], v3_partition.get(record.record_id, "")])
        test = [r for r in records if assignment[r.record_id] == "test"]
        result = {
            "dataset_id": dataset["dataset_id"],
            "identity": f"{dataset['dataset_id']}.orig-grouped-v1",
            "domain": dataset["domain"],
            "window_nt": dataset["window_nt"],
            "filter_counts": filter_counts,
            "records": len(records),
            "test_records_by_label": {str(label): sum(r.label == label for r in test) for label in (0, 1)},
            "grouping": {**report, "cross_partition_edges": crossing},
            "mmseqs": {k: search[k] for k in ("binary_sha256", "version", "command_line", "hits_sha256")},
            "config_sha256": config_sha256,
        }
        result["outputs"] = {"records.csv": sha256_file(staging / "records.csv")}
        write_json_atomic(staging / "build_manifest.json", result)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {k: result[k] for k in ("records", "test_records_by_label")} | {"groups": report["groups"], "largest_group": report["largest_group"], "largest_fraction": round(report["largest_group_fraction"], 4)}


if __name__ == "__main__":
    main()
