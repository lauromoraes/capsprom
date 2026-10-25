"""Build GraphPro downstream-treatment v2 with external-positive exclusions."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile

import yaml

from capsprom.data.downstream_control import (
    filter_controls_matching_external_positives,
    strand_invariant_key,
)
from capsprom.data.loading import sha256_file
from capsprom.data.sequences import read_fasta, write_fasta
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/graphpro_epd_downstream_treatment_v2.yaml"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")

    outputs = []
    removals = []
    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent
    ) as temporary:
        staging = Path(temporary) / args.output_dir.name
        staging.mkdir()
        for dataset in config["datasets"]:
            organism = dataset["organism"]
            positive = _load_hashed_fasta(dataset["positive"])
            negative = _load_hashed_fasta(dataset["negative"])
            retained_negative = list(negative)
            organism_removals = []
            for source in dataset["external_positive_sources"]:
                external_positives = _load_external_positives(source)
                retained_negative, source_removals = filter_controls_matching_external_positives(
                    retained_negative,
                    organism=organism,
                    external_positive_sequences=external_positives,
                    external_dataset_id=source["dataset_id"],
                )
                organism_removals.extend(source_removals)
            _assert_integrity(positive, retained_negative)
            removals.extend(organism_removals)
            organism_dir = staging / organism
            write_fasta(positive, organism_dir / "positive.fa")
            write_fasta(retained_negative, organism_dir / "negative.fa")
            outputs.append(
                {
                    "organism": organism,
                    "input": {"positive": len(positive), "negative": len(negative)},
                    "removed_external_positive_identity": len(organism_removals),
                    "final": {"positive": len(positive), "negative": len(retained_negative)},
                    "balance_difference_after": abs(len(positive) - len(retained_negative)),
                    "outputs": {
                        "positive_sha256": sha256_file(organism_dir / "positive.fa"),
                        "negative_sha256": sha256_file(organism_dir / "negative.fa"),
                    },
                }
            )

        expected_count = int(config["policy"]["expected_removed_count"])
        expected_identifiers = set(config["policy"]["expected_removed_identifiers"])
        observed_identifiers = {item.identifier for item in removals}
        if len(removals) != expected_count or observed_identifiers != expected_identifiers:
            raise AssertionError(
                "external exclusion did not match the frozen expected count and identifiers"
            )
        _write_ledger(staging / "external_exclusion_ledger.csv", removals)
        write_json_atomic(
            staging / "treatment_summary.json",
            {
                "schema_version": 1,
                "dataset_identity": config["treatment"]["name"],
                "config": args.config.as_posix(),
                "config_sha256": sha256_file(args.config),
                "upstream_treatment_identity": config["policy"]["input_stage"],
                "datasets": outputs,
                "external_exclusion_ledger_sha256": sha256_file(
                    staging / "external_exclusion_ledger.csv"
                ),
                "split_generation_enabled": False,
                "model_training_enabled": False,
                "confirmatory_use_enabled": False,
            },
        )
        os.replace(staging, args.output_dir)
    print(json.dumps({"datasets": outputs, "removals": [asdict(item) for item in removals]}, indent=2))


def _load_hashed_fasta(spec: dict[str, str]):
    path = Path(spec["path"])
    _verify_hash(path, spec["sha256"])
    return read_fasta(path)


def _load_external_positives(source: dict[str, object]) -> list[str]:
    sequences = []
    for spec in source["files"]:
        path = Path(spec["path"])
        _verify_hash(path, spec["sha256"])
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if int(row["label"]) == 1:
                    sequences.append(row["sequence"].strip().upper())
    return sequences


def _assert_integrity(positive, negative) -> None:
    positive_keys = [strand_invariant_key(record.sequence) for record in positive]
    negative_keys = [strand_invariant_key(record.sequence) for record in negative]
    if len(positive_keys) != len(set(positive_keys)):
        raise AssertionError("positive strand-invariant duplicates remain")
    if len(negative_keys) != len(set(negative_keys)):
        raise AssertionError("negative strand-invariant duplicates remain")
    if set(positive_keys) & set(negative_keys):
        raise AssertionError("strand-invariant cross-label collisions remain")


def _verify_hash(path: Path, expected: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: expected {expected}, observed {observed}")


def _write_ledger(path: Path, removals) -> None:
    rows = [asdict(item) for item in removals]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
