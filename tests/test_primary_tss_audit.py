from pathlib import Path

import pytest

from capsprom.data.primary_tss_audit import (
    PrimaryTssRow,
    TssBedRow,
    audit_key,
    compare_sample_to_primary,
    read_tss_bed,
    select_stratified_hash_sample,
)


def test_read_tss_bed_and_select_sample_are_deterministic(tmp_path: Path) -> None:
    bed = tmp_path / "source.bed"
    bed.write_text(
        "".join(
            f"chr\t{index}\t{index + 1}\trow-{index}\t0\t{strand}\n"
            for index, strand in enumerate("++++++------")
        ),
        encoding="utf-8",
    )
    rows = read_tss_bed(bed)

    first = select_stratified_hash_sample(
        "dataset", rows, sample_size=10, target_per_strand=5
    )
    second = select_stratified_hash_sample(
        "dataset", reversed(rows), sample_size=10, target_per_strand=5
    )

    assert first == second
    assert sum(row.strand == "+" for row, _ in first) == 5
    assert sum(row.strand == "-" for row, _ in first) == 5
    assert all(digest == hashlib_sha256(audit_key("dataset", row)) for row, digest in first)


def hashlib_sha256(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_read_tss_bed_rejects_non_point_features(tmp_path: Path) -> None:
    bed = tmp_path / "invalid.bed"
    bed.write_text("chr\t1\t3\trow\t0\t+\n", encoding="utf-8")

    with pytest.raises(ValueError, match="valid point TSS"):
        read_tss_bed(bed)


def test_short_strand_is_filled_from_other_strand() -> None:
    rows = [
        TssBedRow("chr", index, index + 1, "", "0", "+", index + 1)
        for index in range(10)
    ] + [TssBedRow("chr", 20, 21, "", "0", "-", 11)]

    selected = select_stratified_hash_sample(
        "dataset", rows, sample_size=10, target_per_strand=5
    )

    assert len(selected) == 10
    assert sum(row.strand == "-" for row, _ in selected) == 1


def test_compare_sample_to_primary_converts_bed0_to_one_based() -> None:
    sample = [{"dataset_id": "example", "start": "41", "strand": "+"}]
    primary = [PrimaryTssRow(42, "+", "TSS", 7)]

    ledger = compare_sample_to_primary(sample, primary)

    assert ledger[0]["status"] == "match"
    assert ledger[0]["expected_primary_position_1based"] == 42
    assert ledger[0]["primary_coordinate_match_count"] == 1
    assert ledger[0]["primary_record_count"] == 1
    assert ledger[0]["primary_locations"] == "TSS:7"


def test_compare_sample_to_primary_requires_same_strand() -> None:
    sample = [{"dataset_id": "example", "start": "41", "strand": "+"}]
    primary = [PrimaryTssRow(42, "-", "TSS", 7)]

    assert compare_sample_to_primary(sample, primary)[0]["status"] == "missing"
