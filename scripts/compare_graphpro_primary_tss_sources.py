#!/usr/bin/env python3
"""Compare the frozen GraphPro TSS sample with acquired primary supplements."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import yaml

from capsprom.data.primary_tss_audit import (
    compare_sample_to_primary,
    read_frozen_sample,
    read_primary_tss_xlsx,
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/graphpro_primary_tss_source_comparison_v1.yaml"),
    )
    args = parser.parse_args()
    contract = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    sample_path = Path(contract["audit"]["frozen_sample"])
    if file_hash(sample_path) != contract["audit"]["frozen_sample_sha256"]:
        raise SystemExit("frozen sample hash does not match the contract")
    sample = read_frozen_sample(sample_path)
    all_rows: list[dict[str, object]] = []
    summaries = []
    source_hashes = {}
    for dataset_id, source in contract["sources"].items():
        if source["status"] != "acquired":
            summaries.append({"dataset_id": dataset_id, "status": source["status"]})
            continue
        source_path = Path(source["path"])
        actual_hash = file_hash(source_path)
        if actual_hash != source["sha256"]:
            raise SystemExit(f"source hash mismatch for {dataset_id}")
        source_hashes[dataset_id] = actual_hash
        primary = read_primary_tss_xlsx(
            source_path,
            sheets=source["sheets"],
            position_column=source["position_column"],
            strand_column=source["strand_column"],
        )
        selected = [row for row in sample if row["dataset_id"] == dataset_id]
        ledger = compare_sample_to_primary(selected, primary)
        for row in ledger:
            row["source_sha256"] = actual_hash
        all_rows.extend(ledger)
        matched = sum(row["status"] == "match" for row in ledger)
        summaries.append(
            {
                "dataset_id": dataset_id,
                "status": "pass" if matched == len(selected) else "fail",
                "sampled_rows": len(selected),
                "matched_rows": matched,
                "primary_rows": len(primary),
                "unique_primary_coordinate_strand_pairs": len(
                    {(row.position_1based, row.strand) for row in primary}
                ),
            }
        )
    output = Path(contract["outputs"]["directory"])
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / contract["outputs"]["row_ledger"]
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    summary_path = output / contract["outputs"]["summary"]
    summary_path.write_text(
        json.dumps({"datasets": summaries}, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "contract": str(args.config),
        "contract_sha256": file_hash(args.config),
        "frozen_sample_sha256": file_hash(sample_path),
        "source_sha256": source_hashes,
        "row_ledger_sha256": file_hash(ledger_path),
        "summary_sha256": file_hash(summary_path),
    }
    (output / contract["outputs"]["manifest"]).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
