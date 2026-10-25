"""Recreate every released GraphPro Human/Mouse sequence from EPD and UCSC."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import tempfile

import yaml

from capsprom.data.epd_resolution import (
    epd_tss_zero_based,
    load_epd_bed,
    oriented_interval,
    parse_graphpro_header,
)
from capsprom.data.twobit import TwoBitGenome
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/graphpro_epd_sequence_recreation_v1.yaml")
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")

    policy = config["policy"]
    rows: list[dict[str, object]] = []
    summaries = []
    for organism in config["organisms"]:
        bed_path = Path(organism["primary_bed"])
        _verify_sha256(bed_path, organism["primary_bed_sha256"])
        coordinates = load_epd_bed(bed_path, bed_path.stem)
        twobit_path = Path(organism["twobit"]["path"])
        _verify_size_and_md5(
            twobit_path, organism["twobit"]["size_bytes"], organism["twobit"]["md5"]
        )
        counts: dict[str, dict[str, int]] = {}
        with TwoBitGenome(twobit_path) as genome:
            for released_class in ("positive", "negative"):
                source_path = Path(organism[f"released_{released_class}"])
                _verify_sha256(source_path, organism[f"released_{released_class}_sha256"])
                records = _read_records(source_path)
                expected_label = 1 if released_class == "positive" else 0
                start_relative = int(policy[f"expected_{released_class}_start_relative_to_tss"])
                end_relative = int(
                    policy[f"expected_{released_class}_end_relative_to_tss_exclusive"]
                )
                class_counts = {"records": len(records), "sequence_matches": 0, "label_matches": 0}
                for index, (header, observed) in enumerate(records):
                    coordinate = coordinates[header.epd_identifier]
                    start, end = oriented_interval(coordinate, start_relative, end_relative)
                    recreated = genome.fetch(
                        coordinate.chromosome,
                        start,
                        end,
                        reverse_complement=coordinate.strand == "-",
                    ).upper()
                    sequence_match = observed.upper() == recreated
                    label_match = header.embedded_label == expected_label
                    class_counts["sequence_matches"] += int(sequence_match)
                    class_counts["label_matches"] += int(label_match)
                    rows.append(
                        {
                            "organism": organism["organism"],
                            "released_class": released_class,
                            "source_index": index,
                            "source_identifier": header.source_identifier,
                            "epd_identifier": header.epd_identifier,
                            "embedded_label": header.embedded_label,
                            "chromosome": coordinate.chromosome,
                            "tss_zero_based": epd_tss_zero_based(coordinate),
                            "strand": coordinate.strand,
                            "relative_start": start_relative,
                            "relative_end_exclusive": end_relative,
                            "genomic_start": start,
                            "genomic_end": end,
                            "observed_sha256": hashlib.sha256(observed.upper().encode()).hexdigest(),
                            "recreated_sha256": hashlib.sha256(recreated.encode()).hexdigest(),
                            "sequence_match": sequence_match,
                            "embedded_label_matches_file": label_match,
                        }
                    )
                counts[released_class] = class_counts
        summaries.append(
            {
                "organism": organism["organism"],
                "assembly": organism["assembly"],
                "classes": counts,
                "all_sequences_match": all(
                    item["sequence_matches"] == item["records"] for item in counts.values()
                ),
                "all_embedded_labels_match_files": all(
                    item["label_matches"] == item["records"] for item in counts.values()
                ),
            }
        )

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent
    ) as temporary:
        staging = Path(temporary) / args.output_dir.name
        staging.mkdir()
        _write_rows(staging / "sequence_recreation_ledger.csv", rows)
        write_json_atomic(staging / "sequence_recreation_summary.json", {"organisms": summaries})
        write_json_atomic(
            staging / "audit_manifest.json",
            {
                "schema_version": 1,
                "audit_identity": config["audit"]["name"],
                "config_sha256": _sha256_file(args.config),
                "row_count": len(rows),
                "outputs": {
                    path.name: _sha256_file(path)
                    for path in staging.iterdir()
                    if path.name != "audit_manifest.json"
                },
                "reconstructed_dataset_generation_enabled": False,
                "model_training_enabled": False,
                "confirmatory_use_enabled": False,
            },
        )
        os.replace(staging, args.output_dir)
    print(json.dumps({"organisms": summaries}, indent=2))


def _read_records(path: Path):
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) % 2:
        raise ValueError(f"expected alternating header/sequence lines in {path}")
    records = []
    for index in range(0, len(lines), 2):
        records.append((parse_graphpro_header(lines[index]), lines[index + 1]))
    return records


def _verify_sha256(path: Path, expected: str) -> None:
    observed = _sha256_file(path)
    if observed != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: expected {expected}, observed {observed}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_size_and_md5(path: Path, expected_size: int, expected_md5: str) -> None:
    if path.stat().st_size != expected_size:
        raise ValueError(f"size mismatch for {path}")
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != expected_md5:
        raise ValueError(f"MD5 mismatch for {path}")


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
