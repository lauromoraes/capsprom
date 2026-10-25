#!/usr/bin/env python3
"""Verify that nominal Promotech ECOLI rows are pAA plasmid coordinates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from Bio import SeqIO
import pandas as pd
import yaml

from capsprom.data.ecoli_source_audit import (
    PublishedPaaRow,
    compare_promotech_bed_to_paa_source,
)
from capsprom.data.primary_tss_audit import read_tss_bed


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/graphpro_ecoli_paa_source_audit_v1.yaml"),
    )
    args = parser.parse_args()
    contract = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    bed_config = contract["promotech_bed"]
    source_config = contract["primary_source"]
    bed_path = Path(bed_config["path"])
    supplement_path = Path(source_config["supplement_path"])
    reference_path = Path(source_config["reference_path"])
    for path, expected in (
        (bed_path, bed_config["sha256"]),
        (supplement_path, source_config["supplement_sha256"]),
        (reference_path, source_config["reference_sha256"]),
    ):
        if file_hash(path) != expected:
            raise SystemExit(f"hash mismatch: {path}")

    frame = pd.read_excel(
        supplement_path,
        sheet_name=source_config["worksheet"],
        header=source_config["header_row_zero_based"],
        engine="xlrd",
    )
    source_rows = []
    for offset, row in frame.iterrows():
        locus = "" if pd.isna(row.iloc[9]) else str(row.iloc[9])
        source_rows.append(
            PublishedPaaRow(
                position_1based=int(row.iloc[0]),
                strand=str(row.iloc[1]),
                locus_tag=locus,
                upstream_50_plus_tss=str(row.iloc[13]),
                source_row=int(offset) + 4,
            )
        )
    reference_records = list(SeqIO.parse(reference_path, "fasta"))
    if len(reference_records) != 1:
        raise SystemExit("pAA reference must contain exactly one record")
    reference = str(reference_records[0].seq)
    if len(reference) != source_config["reference_length"]:
        raise SystemExit("pAA reference length mismatch")
    ledger = compare_promotech_bed_to_paa_source(
        read_tss_bed(bed_path),
        source_rows,
        paa_reference=reference,
        expected_paa_accession=source_config["assembly"],
    )
    output = Path(contract["outputs"]["directory"])
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / contract["outputs"]["ledger"]
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ledger[0]))
        writer.writeheader()
        writer.writerows(ledger)
    fields = (
        "coordinate_match",
        "strand_match",
        "locus_match",
        "published_sequence_matches_paa",
        "contig_match",
    )
    counts = {field: sum(bool(row[field]) for row in ledger) for field in fields}
    summary = {
        "rows": len(ledger),
        "match_counts": counts,
        "declared_bed_contigs": sorted({str(row["bed_contig"]) for row in ledger}),
        "expected_paa_accession": source_config["assembly"],
        "status": "source_rows_verified_but_bed_contig_invalid",
        "nominal_mg1655_reconstruction_valid": False,
    }
    summary_path = output / contract["outputs"]["summary"]
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "contract": str(args.config),
        "contract_sha256": file_hash(args.config),
        "bed_sha256": file_hash(bed_path),
        "supplement_sha256": file_hash(supplement_path),
        "reference_sha256": file_hash(reference_path),
        "ledger_sha256": file_hash(ledger_path),
        "summary_sha256": file_hash(summary_path),
    }
    (output / contract["outputs"]["manifest"]).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
