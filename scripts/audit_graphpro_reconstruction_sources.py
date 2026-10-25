"""Audit and hash candidate Promotech sources for GraphPro reconstruction."""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

import yaml

from capsprom.data.graphpro_reconstruction import audit_promotech_source
from capsprom.data.loading import sha256_file
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument(
        "--registry", type=Path, default=Path("configs/graphpro_source_registry_v1.yaml")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    registry = yaml.safe_load(args.registry.read_text(encoding="utf-8"))
    results = []
    for source in registry["sources"]:
        audit = audit_promotech_source(
            source_key=source["source_key"],
            reference_fasta=args.checkout / source["reference_fasta"],
            tss_bed=args.checkout / source["tss_bed"],
            processed_positive_bed=args.checkout / source["processed_positive_bed"],
            processed_positive_fasta=args.checkout / source["processed_positive_fasta"],
        )
        item = dataclasses.asdict(audit)
        observed_hashes = {
            "reference_fasta": audit.reference_sha256,
            "tss_bed": audit.tss_sha256,
            "processed_positive_bed": audit.processed_positive_bed_sha256,
            "processed_positive_fasta": audit.processed_positive_fasta_sha256,
        }
        hashes_match = observed_hashes == source["expected_sha256"]
        item.update(
            {
                "dataset_id": source["dataset_id"],
                "expected_accession": source["expected_accession"],
                "accession_matches": audit.accession == source["expected_accession"],
                "hashes_match": hashes_match,
                "passed": (
                    audit.passed
                    and audit.accession == source["expected_accession"]
                    and hashes_match
                ),
            }
        )
        results.append(item)
    payload = {
        "schema_version": 1,
        "registry": str(args.registry),
        "registry_sha256": sha256_file(args.registry),
        "repository_url": registry["registry"]["repository_url"],
        "repository_commit": registry["registry"]["repository_commit"],
        "all_sources_passed": all(item["passed"] for item in results),
        "sources": results,
    }
    write_json_atomic(args.output, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
