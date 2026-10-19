"""Audit near-duplicate train/test sensitivity for canonical real-negative data."""

from pathlib import Path

from capsprom.data.near_duplicate_audit import audit_near_duplicate_directory


if __name__ == "__main__":
    result = audit_near_duplicate_directory(
        Path("data/processed/assembled_datasets/intra_regenerated_v3_strict_dna"),
        Path("data/processed/audits/real_negative_regenerated_v3"),
    )
    print(f"Near-duplicate audit {result['audit_id']}: {result['pair_count']} pairs")
