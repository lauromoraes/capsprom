"""Audit near-duplicate components in reconstructed positive-control pairs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from capsprom.data.loading import sha256_file
from capsprom.data.similarity_groups import audit_paired_sequence_similarity
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for dataset_dir in sorted(path for path in args.input_dir.iterdir() if path.is_dir()):
        ledger = dataset_dir / "pair_ledger.csv"
        with ledger.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        pairs = [(row["positive_sequence"], row["negative_sequence"]) for row in rows]
        audit = audit_paired_sequence_similarity(pairs)
        report = {
            "dataset": dataset_dir.name,
            "pair_ledger": str(ledger),
            "pair_ledger_sha256": sha256_file(ledger),
            **audit.as_dict(),
        }
        write_json_atomic(args.output_dir / f"{dataset_dir.name}.json", report)
        reports.append(report)
        print(json.dumps(report, indent=2))
    write_json_atomic(
        args.output_dir / "similarity_audit_summary.json",
        {
            "schema_version": 1,
            "distance": "minimum_hamming_over_forward_and_reverse_complement",
            "pair_is_indivisible": True,
            "thresholds": [1, 2, 4, 8],
            "dataset_count": len(reports),
            "datasets": reports,
        },
    )


if __name__ == "__main__":
    main()
