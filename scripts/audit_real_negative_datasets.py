"""Audit canonical CDBProm, CNNProm, and GraphPro strict-DNA dataset pairs."""

from pathlib import Path

from capsprom.data.batch_audit import audit_dataset_directory


if __name__ == "__main__":
    result = audit_dataset_directory(
        Path("data/processed/assembled_datasets/intra_regenerated_v3_strict_dna"),
        Path("data/processed/audits/real_negative_regenerated_v3"),
    )
    print(f"Audit {result['audit_id']}: {result['eligible_count']}/{result['pair_count']} pairs eligible")
