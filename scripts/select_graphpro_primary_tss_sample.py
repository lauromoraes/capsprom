"""Materialize the frozen GraphPro primary-TSS audit sample."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import yaml

from capsprom.data.primary_tss_audit import (
    audit_key,
    read_tss_bed,
    select_stratified_hash_sample,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")
    contract = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    sample = contract["sampling"]
    output_rows = []
    input_hashes = {}
    for dataset in contract["datasets"]:
        path = Path(dataset["promotech_bed"])
        observed_hash = sha256(path)
        if observed_hash != dataset["promotech_bed_sha256"]:
            raise ValueError(f"hash mismatch for {path}")
        input_hashes[path.as_posix()] = observed_hash
        selected = select_stratified_hash_sample(
            dataset["dataset_id"],
            read_tss_bed(path),
            sample_size=int(sample["rows_per_dataset"]),
            target_per_strand=int(sample["strand_stratification"]["target_per_strand"]),
        )
        for row, digest in selected:
            output_rows.append({
                "dataset_id": dataset["dataset_id"],
                "assembly": dataset["assembly"],
                "primary_source_pmid": dataset["primary_source_pmid"],
                "source_row": row.source_row,
                "contig": row.contig,
                "start": row.start,
                "end": row.end,
                "name": row.name,
                "score": row.score,
                "strand": row.strand,
                "canonical_key": audit_key(dataset["dataset_id"], row),
                "sha256_rank": digest,
            })

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent))
    try:
        csv_path = staging / "selected_rows.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
            writer.writeheader()
            writer.writerows(output_rows)
        manifest = {
            "contract": args.config.as_posix(),
            "contract_sha256": sha256(args.config),
            "input_hashes": input_hashes,
            "dataset_count": len(contract["datasets"]),
            "selected_row_count": len(output_rows),
            "selected_rows_sha256": sha256(csv_path),
        }
        (staging / "audit_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        staging.rename(args.output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


if __name__ == "__main__":
    main()
