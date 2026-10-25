"""Resolve GraphPro Human/Mouse headers against frozen EPDnew coordinates."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

import yaml

from capsprom.data.epd_resolution import load_epd_bed, parse_graphpro_header
from capsprom.data.loading import sha256_file
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/graphpro_epd_identifier_resolution_v1.yaml")
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")
    license_notice = config["audit"]["license_notice"]
    _verify_hash(Path(license_notice["path"]), license_notice["sha256"])

    rows: list[dict[str, object]] = []
    summaries = []
    for organism in config["organisms"]:
        primary = organism["primary_bed"]
        _verify_hash(Path(primary["path"]), primary["sha256"])
        primary_records = load_epd_bed(Path(primary["path"]), primary["collection"])
        alternatives = {}
        for alternative in organism["alternative_beds"]:
            _verify_hash(Path(alternative["path"]), alternative["sha256"])
            alternatives[alternative["collection"]] = load_epd_bed(
                Path(alternative["path"]), alternative["collection"]
            )

        class_identifiers: dict[str, set[str]] = {}
        unresolved = set()
        for released_class in ("positive", "negative"):
            source_path = Path(organism[f"released_{released_class}"])
            _verify_hash(source_path, organism[f"released_{released_class}_sha256"])
            headers = _read_headers(source_path)
            class_identifiers[released_class] = {header.epd_identifier for header in headers}
            for index, header in enumerate(headers):
                coordinate = primary_records.get(header.epd_identifier)
                if coordinate is None:
                    unresolved.add(header.epd_identifier)
                alternative_matches = sorted(
                    name for name, records in alternatives.items() if header.epd_identifier in records
                )
                rows.append(
                    {
                        "organism": organism["organism"],
                        "released_class": released_class,
                        "source_index": index,
                        "source_identifier": header.source_identifier,
                        "epd_identifier": header.epd_identifier,
                        "embedded_label": header.embedded_label,
                        "resolution_status": "resolved_primary" if coordinate else "unresolved",
                        "primary_collection": primary["collection"] if coordinate else "",
                        "chromosome": coordinate.chromosome if coordinate else "",
                        "start": coordinate.start if coordinate else "",
                        "end": coordinate.end if coordinate else "",
                        "strand": coordinate.strand if coordinate else "",
                        "alternative_collections": ";".join(alternative_matches),
                    }
                )
        union = class_identifiers["positive"] | class_identifiers["negative"]
        summaries.append(
            {
                "organism": organism["organism"],
                "assembly": organism["assembly"],
                "primary_collection": primary["collection"],
                "primary_collection_records": len(primary_records),
                "released_positive_records": len(class_identifiers["positive"]),
                "released_negative_records": len(class_identifiers["negative"]),
                "shared_identifiers_between_released_classes": len(
                    class_identifiers["positive"] & class_identifiers["negative"]
                ),
                "union_identifiers": len(union),
                "resolved_union_identifiers": len(union & primary_records.keys()),
                "unresolved_union_identifiers": len(unresolved),
                "identifiers_with_alternative_collection_match": sum(
                    any(identifier in records for records in alternatives.values())
                    for identifier in union
                ),
            }
        )

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent
    ) as temporary:
        staging = Path(temporary) / args.output_dir.name
        staging.mkdir()
        _write_rows(staging / "identifier_resolution_ledger.csv", rows)
        write_json_atomic(staging / "identifier_resolution_summary.json", {"organisms": summaries})
        write_json_atomic(
            staging / "audit_manifest.json",
            {
                "schema_version": 1,
                "audit_identity": config["audit"]["name"],
                "config_sha256": sha256_file(args.config),
                "row_count": len(rows),
                "outputs": {
                    path.name: sha256_file(path)
                    for path in staging.iterdir()
                    if path.name != "audit_manifest.json"
                },
                "sequence_reconstruction_enabled": False,
                "model_training_enabled": False,
                "confirmatory_use_enabled": False,
            },
        )
        os.replace(staging, args.output_dir)
    print(json.dumps({"organisms": summaries}, indent=2))


def _read_headers(path: Path):
    with path.open(encoding="utf-8") as handle:
        return [parse_graphpro_header(line) for line in handle if line.startswith(">")]


def _verify_hash(path: Path, expected: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: expected {expected}, observed {observed}")


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
