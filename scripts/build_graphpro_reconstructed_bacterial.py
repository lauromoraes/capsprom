"""Build atomic bacterial graphpro-reconstructed-v1 candidate datasets."""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import os
import tempfile
from pathlib import Path

import yaml

from capsprom.data.graphpro_reconstruction import (
    audit_promotech_source,
    deduplicate_tss_loci,
    filter_reconstructed_pairs,
    read_bed_tss,
    reconstruct_genomic_controls,
    screen_tss_loci,
)
from capsprom.data.loading import sha256_file
from capsprom.data.sequences import read_fasta, write_fasta
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument(
        "--registry", type=Path, default=Path("configs/graphpro_source_registry_v1.yaml")
    )
    parser.add_argument(
        "--contract", type=Path, default=Path("configs/graphpro_reconstruction_v1.yaml")
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    registry = yaml.safe_load(args.registry.read_text(encoding="utf-8"))
    contract = yaml.safe_load(args.contract.read_text(encoding="utf-8"))
    window = contract["window"]
    negative_policy = contract["negative_policy"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for source in registry["sources"]:
        final_dir = args.output_dir / source["source_key"]
        if final_dir.exists():
            raise FileExistsError(f"refusing to overwrite existing candidate {final_dir}")
        source_paths = {
            key: args.checkout / source[key]
            for key in (
                "reference_fasta",
                "tss_bed",
                "processed_positive_bed",
                "processed_positive_fasta",
            )
        }
        audit = audit_promotech_source(source_key=source["source_key"], **source_paths)
        observed_hashes = {
            "reference_fasta": audit.reference_sha256,
            "tss_bed": audit.tss_sha256,
            "processed_positive_bed": audit.processed_positive_bed_sha256,
            "processed_positive_fasta": audit.processed_positive_fasta_sha256,
        }
        if not audit.passed or audit.accession != source["expected_accession"]:
            raise ValueError(f"source integrity audit failed for {source['source_key']}")
        if observed_hashes != source["expected_sha256"]:
            raise ValueError(f"source hash mismatch for {source['source_key']}")

        reference_records = read_fasta(source_paths["reference_fasta"])
        references = {record.identifier: record.sequence for record in reference_records}
        source_loci = read_bed_tss(source_paths["tss_bed"])
        unique_loci = deduplicate_tss_loci(source_loci)
        eligible_loci, rejected_loci = screen_tss_loci(
            references,
            unique_loci,
            upstream=int(window["upstream"]),
            downstream=int(window["downstream"]),
        )
        pairs = reconstruct_genomic_controls(
            references,
            eligible_loci,
            exclusion_loci=unique_loci,
            upstream=int(window["upstream"]),
            downstream=int(window["downstream"]),
            exclusion_radius=int(negative_policy["exclusion_radius_nt"]),
            gc_tolerance=float(negative_policy["absolute_gc_tolerance"]),
            seed=int(negative_policy["sampling_seed"]),
            max_attempts_per_locus=int(negative_policy["max_attempts_per_positive"]),
        )
        generated_pair_count = len(pairs)
        pair_filter = contract.get("post_generation_filter", {})
        pair_filter_counts = {
            "cross_label_pairs_removed": 0,
            "positive_duplicate_pairs_removed": 0,
            "negative_duplicate_pairs_removed": 0,
        }
        if pair_filter.get("enabled", False):
            filtered = filter_reconstructed_pairs(pairs)
            pairs = filtered.pairs
            pair_filter_counts = {
                "cross_label_pairs_removed": filtered.cross_label_pairs_removed,
                "positive_duplicate_pairs_removed": filtered.positive_duplicate_pairs_removed,
                "negative_duplicate_pairs_removed": filtered.negative_duplicate_pairs_removed,
            }

        with tempfile.TemporaryDirectory(prefix=f".{source['source_key']}.", dir=args.output_dir) as temporary:
            staging = Path(temporary) / source["source_key"]
            staging.mkdir()
            positive_path = staging / "positive.fa"
            negative_path = staging / "negative.fa"
            pair_ledger_path = staging / "pair_ledger.csv"
            rejected_path = staging / "rejected_tss.csv"
            write_fasta((pair.positive for pair in pairs), positive_path)
            write_fasta((pair.negative for pair in pairs), negative_path)
            _write_pair_ledger(pair_ledger_path, pairs)
            _write_rejected_ledger(rejected_path, rejected_loci)
            manifest = {
                "schema_version": 1,
                "dataset_id": source["dataset_id"],
                "source_key": source["source_key"],
                "source_repository_commit": registry["registry"]["repository_commit"],
                "registry_sha256": sha256_file(args.registry),
                "contract_sha256": sha256_file(args.contract),
                "source_hashes": observed_hashes,
                "source_rows": len(source_loci),
                "duplicate_source_tss_rows": len(source_loci) - len(unique_loci),
                "unique_tss_groups": len(unique_loci),
                "eligible_positive_windows": len(eligible_loci),
                "rejected_tss_windows": len(rejected_loci),
                "rejected_tss_reasons": _reason_counts(rejected_loci),
                "pairs_before_post_generation_filter": generated_pair_count,
                "post_generation_filter": pair_filter_counts,
                "generated_pairs": len(pairs),
                "parameters": {
                    "upstream": int(window["upstream"]),
                    "downstream": int(window["downstream"]),
                    "exclusion_radius_nt": int(negative_policy["exclusion_radius_nt"]),
                    "maximum_gc_count_difference": int(
                        negative_policy["maximum_gc_count_difference"]
                    ),
                    "absolute_gc_tolerance": float(negative_policy["absolute_gc_tolerance"]),
                    "sampling_seed": int(negative_policy["sampling_seed"]),
                },
                "outputs": {
                    path.name: sha256_file(path)
                    for path in (positive_path, negative_path, pair_ledger_path, rejected_path)
                },
            }
            write_json_atomic(staging / "build_manifest.json", manifest)
            os.replace(staging, final_dir)
        summaries.append(manifest)
        print(json.dumps(manifest, indent=2))

    write_json_atomic(
        args.output_dir / "build_summary.json",
        {
            "schema_version": 1,
            "dataset_family": contract["reconstruction"]["name"],
            "registry_sha256": sha256_file(args.registry),
            "contract_sha256": sha256_file(args.contract),
            "dataset_count": len(summaries),
            "total_pairs": sum(item["generated_pairs"] for item in summaries),
            "datasets": summaries,
        },
    )


def _write_pair_ledger(path: Path, pairs: list[object]) -> None:
    rows = []
    for pair in pairs:
        row = dataclasses.asdict(pair)
        row["positive_identifier"] = pair.positive.identifier
        row["positive_sequence"] = pair.positive.sequence
        row["negative_identifier"] = pair.negative.identifier
        row["negative_sequence"] = pair.negative.sequence
        row["contig"] = pair.positive_locus.contig
        row["tss"] = pair.positive_locus.tss
        row["positive_strand"] = pair.positive_locus.strand
        for nested in ("positive", "negative", "positive_locus"):
            row.pop(nested)
        rows.append(row)
    _write_csv(path, rows)


def _write_rejected_ledger(path: Path, rejected: list[object]) -> None:
    rows = [
        {
            "identifier": item.locus.identifier,
            "contig": item.locus.contig,
            "tss": item.locus.tss,
            "strand": item.locus.strand,
            "reason": item.reason,
        }
        for item in rejected
    ]
    _write_csv(path, rows, fallback_fields=["identifier", "contig", "tss", "strand", "reason"])


def _write_csv(path: Path, rows: list[dict[str, object]], fallback_fields: list[str] | None = None) -> None:
    fields = list(rows[0]) if rows else (fallback_fields or [])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _reason_counts(rejected: list[object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in rejected:
        counts[item.reason] = counts.get(item.reason, 0) + 1
    return counts


if __name__ == "__main__":
    main()
