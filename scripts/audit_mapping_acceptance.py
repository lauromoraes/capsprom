"""Acceptance audit of reference coordinate mapping v3 (criteria 1-3 recount, B1, B3 input, sample)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml

from capsprom.data.mapping_acceptance import (
    b1_cnnprom_ecoli,
    b3_input,
    coverage_and_consistency,
    declared_integer,
    read_csv_gz,
    stratified_sample,
)
from capsprom.state import write_json_atomic

SAMPLE_COLUMNS = (
    "record_id", "collection_id", "label", "status", "status_reason", "assembly_accession",
    "contig_accession", "start", "end", "strand", "declared_coordinate_text",
    "check_locus_in_ncbi", "check_assembly_matches_source", "reviewer_notes",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/reference_coordinate_mapping_v3_acceptance_v1.yaml"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))["acceptance"]
    if _sha256(Path(config["mapping_config"])) != config["mapping_config_sha256"]:
        raise SystemExit("mapping config hash mismatch")
    root = Path(config["mapping_output_dir"])
    summary: dict = {"acceptance_config_sha256": _sha256(args.config), "collections": {}}
    records_by_collection: dict[str, list[dict[str, str]]] = {}
    loci_by_record: dict[str, dict[str, str]] = {}
    for record_path in sorted((root / "records").glob("*.csv.gz")):
        collection = record_path.name.removesuffix(".csv.gz")
        records = read_csv_gz(record_path)
        loci = read_csv_gz(root / "loci" / record_path.name)
        records_by_collection[collection] = records
        loci_by_record.update({row["record_id"]: row for row in loci if row["locus_rank"] == "1"})
        entry = coverage_and_consistency(records, loci)
        entry["b3_input_records"] = b3_input(records)
        entry["records_sha256"] = _sha256(record_path)
        if config["b1_rules"].get(collection) == "cnnprom_ecoli_f098":
            entry["b1"] = b1_cnnprom_ecoli(records, loci)
        if config["b1_probes"].get(collection) == "plus_strand_start_plus_60":
            probe: Counter[str] = Counter()
            for row in records:
                if row["label"] != "0" or row["status"] != "verified":
                    continue
                value = declared_integer(row["declared_coordinate_text"])
                locus = loci_by_record[row["record_id"]]
                if value is None:
                    probe["unparsed"] += 1
                elif locus["strand"] == "+" and value == int(locus["start"]) + 60:
                    probe["plus_match"] += 1
                else:
                    probe[f"{locus['strand']}_other"] += 1
            entry["b1_probe"] = {"rule": "plus_strand_start_plus_60", "counts": dict(sorted(probe.items()))}
        summary["collections"][collection] = entry
    sample = stratified_sample(records_by_collection, int(config["sample_per_stratum"]))
    sample_path = Path(config["sample_output"])
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    with sample_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SAMPLE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in sample:
            locus = loci_by_record.get(row["record_id"], {})
            writer.writerow({
                **{key: row.get(key, "") for key in SAMPLE_COLUMNS},
                **{key: locus.get(key, "") for key in ("contig_accession", "start", "end", "strand")},
                "check_locus_in_ncbi": "", "check_assembly_matches_source": "", "reviewer_notes": "",
            })
    summary["sample"] = {"path": str(sample_path).replace("\\", "/"), "rows": len(sample), "sha256": _sha256(sample_path)}
    write_json_atomic(Path(config["summary_output"]), summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "collections"}, indent=2))
    for name, entry in summary["collections"].items():
        print(name, entry["status_counts"], entry["violations"], entry.get("b1", {}).get("counts"), entry.get("b1_probe"))


if __name__ == "__main__":
    main()
