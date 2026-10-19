"""Build canonical exact-sequence-safe CDBProm, CNNProm, and GraphPro datasets."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from capsprom.data.dataset_builders import (
    build_group_safe_intra_dataset_csvs_with_audit,
    crop_fasta_directory,
    group_promoter_pairs,
)
from capsprom.data.sequences import read_fasta
from capsprom.experiment import sha256_file


INPUT_FASTA = Path("data/interim/fasta")
CROPPED_FASTA = Path("data/interim/cropped_fasta_regenerated_v3")
STRICT_CSV = Path("data/processed/assembled_datasets/intra_regenerated_v3_strict_dna")
REPORT_DIR = Path("data/processed/audits/real_negative_regenerated_v3")
REPORT_PATH = REPORT_DIR / "build_report.json"
FILTERING_MANIFEST_JSON = REPORT_DIR / "filtering_manifest.json"
FILTERING_MANIFEST_CSV = REPORT_DIR / "filtering_manifest.csv"


def main() -> None:
    for output_dir in (CROPPED_FASTA, STRICT_CSV, REPORT_DIR):
        if output_dir.exists() and any(output_dir.iterdir()):
            raise ValueError(f"refusing to mix regenerated data with existing files: {output_dir}")

    cropped = crop_fasta_directory(INPUT_FASTA, CROPPED_FASTA)
    build = build_group_safe_intra_dataset_csvs_with_audit(CROPPED_FASTA, STRICT_CSV, random_seed=42)
    source_pairs = group_promoter_pairs(sorted(INPUT_FASTA.glob("*.fa")))

    filtering_records = []
    for audit in build.filter_audits:
        source_paths = source_pairs[(audit.study, audit.organism_type, audit.dataset)]
        prefix = f"{audit.study}-{audit.organism_type}-{audit.dataset}-"
        dataset_outputs = [result for result in build.outputs if result.output.name.startswith(prefix)]
        train_output = next(result for result in dataset_outputs if result.output.name.endswith("-train.csv"))
        test_output = next(result for result in dataset_outputs if result.output.name.endswith("-test.csv"))
        record = asdict(audit)
        record.update(
            {
                "positive_rows_before_crop": len(read_fasta(source_paths["p"])),
                "negative_rows_before_crop": len(read_fasta(source_paths["n"])),
                "positive_source_sha256": sha256_file(source_paths["p"]),
                "negative_source_sha256": sha256_file(source_paths["n"]),
                "train_output_sha256": sha256_file(train_output.output),
                "test_output_sha256": sha256_file(test_output.output),
            }
        )
        filtering_records.append(record)

    report = {
        "pipeline_version": "real-negative-regenerated-v3",
        "input_directory": INPUT_FASTA.as_posix(),
        "cropped_directory": CROPPED_FASTA.as_posix(),
        "strict_directory": STRICT_CSV.as_posix(),
        "crop_mode": "overwrite",
        "cross_label_collision_policy": "remove_all_after_crop",
        "same_label_duplicate_policy": "keep_first_normalized_sequence",
        "partition_policy": "deterministic_stratified_unique_sequence_groups",
        "filter_order": [
            "crop",
            "remove_cross_label_collisions",
            "deduplicate_within_class",
            "strict_dna",
            "group_safe_split",
        ],
        "split_seed": 42,
        "test_fraction": 0.2,
        "cropped_fasta_count": len(cropped),
        "processed_csv_count": len(build.outputs),
        "strict_csv_count": len(build.outputs),
        "filtering_manifest_json": FILTERING_MANIFEST_JSON.as_posix(),
        "filtering_manifest_csv": FILTERING_MANIFEST_CSV.as_posix(),
        "cropped_fastas": [
            {"path": path.as_posix(), "sha256": sha256_file(path)} for path in sorted(cropped)
        ],
        "strict_csvs": [
            {
                "path": result.output.as_posix(),
                "rows": result.rows,
                "positive": result.positives,
                "negative": result.negatives,
                "sha256": sha256_file(result.output),
            }
            for result in build.outputs
        ],
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FILTERING_MANIFEST_JSON.write_text(
        json.dumps(filtering_records, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with FILTERING_MANIFEST_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(filtering_records[0]))
        writer.writeheader()
        writer.writerows(filtering_records)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Generated {len(cropped)} cropped FASTAs and {len(build.outputs)} strict CSVs; "
        f"report: {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()
