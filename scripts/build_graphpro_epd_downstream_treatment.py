"""Build the traceable GraphPro EPD downstream-control treatment view."""

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
    filter_controls_near_known_tss,
    index_known_tss,
    strand_invariant_key,
    treat_strand_invariant_pair,
)
from capsprom.data.epd_resolution import load_epd_bed
from capsprom.data.loading import sha256_file
from capsprom.data.sequences import read_fasta, write_fasta
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/graphpro_epd_downstream_treatment_v1.yaml")
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")

    policy = config["policy"]
    outputs = []
    all_removals = []
    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent
    ) as temporary:
        staging = Path(temporary) / args.output_dir.name
        staging.mkdir()
        for organism_config in config["organisms"]:
            organism = organism_config["organism"]
            positive = _load_hashed_fasta(organism_config["positive"])
            negative = _load_hashed_fasta(organism_config["negative"])
            primary_spec = organism_config["primary_bed"]
            _verify_hash(Path(primary_spec["path"]), primary_spec["sha256"])
            primary = load_epd_bed(Path(primary_spec["path"]), primary_spec["collection"])
            collections = []
            for bed_spec in organism_config["known_tss_beds"]:
                _verify_hash(Path(bed_spec["path"]), bed_spec["sha256"])
                collections.append(
                    load_epd_bed(Path(bed_spec["path"]), bed_spec["collection"])
                )
            known_tss = index_known_tss(collections)

            positive_after_strand, negative_after_strand, strand_removals = (
                treat_strand_invariant_pair(positive, negative, organism=organism)
            )
            negative_after_tss, tss_removals = filter_controls_near_known_tss(
                negative_after_strand,
                organism=organism,
                primary_coordinates=primary,
                known_tss=known_tss,
                relative_start=int(policy["downstream_relative_start"]),
                relative_end=int(policy["downstream_relative_end_exclusive"]),
                exclusion_margin=int(policy["known_tss_exclusion_margin_nt"]),
            )
            removals = strand_removals + tss_removals
            all_removals.extend(removals)
            remaining_controls, remaining_tss_violations = filter_controls_near_known_tss(
                negative_after_tss,
                organism=organism,
                primary_coordinates=primary,
                known_tss=known_tss,
                relative_start=int(policy["downstream_relative_start"]),
                relative_end=int(policy["downstream_relative_end_exclusive"]),
                exclusion_margin=int(policy["known_tss_exclusion_margin_nt"]),
            )
            if remaining_tss_violations or len(remaining_controls) != len(negative_after_tss):
                raise AssertionError("TSS exclusion postcondition failed")
            positive_keys = [strand_invariant_key(record.sequence) for record in positive_after_strand]
            negative_keys = [strand_invariant_key(record.sequence) for record in negative_after_tss]
            if len(set(positive_keys)) != len(positive_keys):
                raise AssertionError("positive strand-invariant duplicates remain")
            if len(set(negative_keys)) != len(negative_keys):
                raise AssertionError("negative strand-invariant duplicates remain")
            if set(positive_keys) & set(negative_keys):
                raise AssertionError("strand-invariant cross-label collisions remain")
            positive_epd = {_epd_identifier(record.identifier) for record in positive_after_strand}
            negative_epd = {_epd_identifier(record.identifier) for record in negative_after_tss}
            organism_dir = staging / organism
            write_fasta(positive_after_strand, organism_dir / "positive.fa")
            write_fasta(negative_after_tss, organism_dir / "negative.fa")
            reason_counts: dict[str, int] = {}
            for removal in removals:
                reason_counts[removal.reason] = reason_counts.get(removal.reason, 0) + 1
            outputs.append(
                {
                    "organism": organism,
                    "input": {"positive": len(positive), "negative": len(negative)},
                    "after_strand_invariant_integrity": {
                        "positive": len(positive_after_strand),
                        "negative": len(negative_after_strand),
                    },
                    "after_tss_exclusion": {
                        "positive": len(positive_after_strand),
                        "negative": len(negative_after_tss),
                    },
                    "removed": {
                        "positive": sum(item.class_name == "positive" for item in removals),
                        "negative": sum(item.class_name == "negative" for item in removals),
                    },
                    "tss_exclusion": {
                        "total": len(tss_removals),
                        "exact_overlap": sum(item.exact_tss_overlap is True for item in tss_removals),
                        "margin_only": sum(item.exact_tss_overlap is False for item in tss_removals),
                    },
                    "reason_counts": reason_counts,
                    "balance_difference_after": abs(
                        len(positive_after_strand) - len(negative_after_tss)
                    ),
                    "final_integrity": {
                        "within_positive_strand_invariant_duplicates": 0,
                        "within_negative_strand_invariant_duplicates": 0,
                        "cross_label_strand_invariant_collisions": 0,
                        "known_tss_margin_violations": 0,
                        "shared_epd_identifier_groups": len(positive_epd & negative_epd),
                        "positive_only_epd_identifier_groups": len(positive_epd - negative_epd),
                        "negative_only_epd_identifier_groups": len(negative_epd - positive_epd),
                    },
                    "outputs": {
                        "positive_sha256": sha256_file(organism_dir / "positive.fa"),
                        "negative_sha256": sha256_file(organism_dir / "negative.fa"),
                    },
                }
            )
        _write_ledger(staging / "exclusion_ledger.csv", all_removals)
        write_json_atomic(
            staging / "treatment_summary.json",
            {
                "schema_version": 1,
                "dataset_identity": config["treatment"]["name"],
                "config": args.config.as_posix(),
                "config_sha256": sha256_file(args.config),
                "upstream_integrity_identity": policy["input_integrity_stage"],
                "datasets": outputs,
                "exclusion_ledger_sha256": sha256_file(staging / "exclusion_ledger.csv"),
                "split_generation_enabled": False,
                "model_training_enabled": False,
                "confirmatory_use_enabled": False,
            },
        )
        os.replace(staging, args.output_dir)
    print(json.dumps({"datasets": outputs}, indent=2))


def _load_hashed_fasta(spec: dict[str, str]):
    path = Path(spec["path"])
    _verify_hash(path, spec["sha256"])
    return read_fasta(path)


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


def _epd_identifier(identifier: str) -> str:
    return identifier.split("|", maxsplit=1)[1]


if __name__ == "__main__":
    main()
