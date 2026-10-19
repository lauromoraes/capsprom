import csv
from pathlib import Path

from capsprom.data.dataset_builders import (
    build_group_safe_intra_dataset_csvs_with_audit,
    build_intra_dataset_csvs_with_audit,
    crop_fasta_directory,
)
from capsprom.data.sequences import SequenceRecord, read_fasta, write_fasta


def test_cropping_overwrites_output_instead_of_appending(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    source = input_dir / "prom-cnnprom-prokaryotic-fixture-2-81.fa"
    records = [
        SequenceRecord("first", "A" * 81),
        SequenceRecord("second", "C" * 81),
    ]
    write_fasta(records, source)

    first = crop_fasta_directory(input_dir, output_dir)
    second = crop_fasta_directory(input_dir, output_dir)

    assert first == second
    assert len(read_fasta(first[0])) == 2


def test_cross_label_collisions_are_always_removed_and_audited(tmp_path: Path):
    input_dir = tmp_path / "cropped"
    output_dir = tmp_path / "processed"
    input_dir.mkdir()
    collision = "A" * 81
    write_fasta(
        [SequenceRecord("p-collision", collision), SequenceRecord("p-unique", "C" * 81)],
        input_dir / "prom-cnnprom-prokaryotic-fixture-2-81.fa",
    )
    write_fasta(
        [SequenceRecord("n-collision", collision), SequenceRecord("n-unique", "G" * 81)],
        input_dir / "nonprom-cnnprom-prokaryotic-fixture-2-81.fa",
    )

    report = build_intra_dataset_csvs_with_audit(input_dir, output_dir, test_fraction=0.5)
    rows = []
    for result in report.outputs:
        with result.output.open(encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle))

    assert {row["sequence"] for row in rows} == {"C" * 81, "G" * 81}
    audit = report.collision_audits[0]
    assert audit.cross_label_collision_sequences == 1
    assert audit.positive_rows_removed_as_collisions == 1
    assert audit.negative_rows_removed_as_collisions == 1
    assert audit.positive_rows_after_collision_filter == 1
    assert audit.negative_rows_after_collision_filter == 1


def test_group_safe_builder_filters_deduplicates_and_prevents_overlap(tmp_path: Path):
    input_dir = tmp_path / "cropped"
    output_dir = tmp_path / "processed"
    input_dir.mkdir()
    collision = "A" * 81
    positive_duplicate = "C" * 81
    negative_duplicate = "G" * 81
    write_fasta(
        [
            SequenceRecord("p-collision", collision),
            SequenceRecord("p-duplicate-1", positive_duplicate),
            SequenceRecord("p-duplicate-2", positive_duplicate),
            SequenceRecord("p-unique", "T" * 81),
            SequenceRecord("p-invalid", "N" * 81),
        ],
        input_dir / "prom-cnnprom-prokaryotic-fixture-5-81.fa",
    )
    write_fasta(
        [
            SequenceRecord("n-collision", collision),
            SequenceRecord("n-duplicate-1", negative_duplicate),
            SequenceRecord("n-duplicate-2", negative_duplicate),
            SequenceRecord("n-unique", "AC" * 40 + "A"),
            SequenceRecord("n-invalid", "R" * 81),
        ],
        input_dir / "nonprom-cnnprom-prokaryotic-fixture-5-81.fa",
    )

    report = build_group_safe_intra_dataset_csvs_with_audit(
        input_dir,
        output_dir,
        test_fraction=0.5,
    )
    partitions: dict[str, list[dict[str, str]]] = {}
    for result in report.outputs:
        with result.output.open(encoding="utf-8", newline="") as handle:
            partitions[result.output.stem.rsplit("-", 1)[-1]] = list(csv.DictReader(handle))

    train_sequences = {row["sequence"] for row in partitions["train"]}
    test_sequences = {row["sequence"] for row in partitions["test"]}
    assert train_sequences.isdisjoint(test_sequences)
    assert len(train_sequences | test_sequences) == 4
    assert sum(map(len, partitions.values())) == 4

    audit = report.filter_audits[0]
    assert audit.positive_rows_removed_as_collisions == 1
    assert audit.negative_rows_removed_as_collisions == 1
    assert audit.positive_duplicate_rows_removed == 1
    assert audit.negative_duplicate_rows_removed == 1
    assert audit.positive_invalid_dna_rows_removed == 1
    assert audit.negative_invalid_dna_rows_removed == 1
    assert audit.positive_rows_before_split == 2
    assert audit.negative_rows_before_split == 2


def test_group_safe_split_is_independent_of_unrelated_dataset_order(tmp_path: Path):
    first_input = tmp_path / "first-input"
    second_input = tmp_path / "second-input"
    first_output = tmp_path / "first-output"
    second_output = tmp_path / "second-output"
    first_input.mkdir()
    second_input.mkdir()

    positive = [SequenceRecord(f"p-{index}", f"{index:081b}".replace("0", "A").replace("1", "C")) for index in range(10)]
    negative = [SequenceRecord(f"n-{index}", f"{index:081b}".replace("0", "G").replace("1", "T")) for index in range(10)]
    for directory in (first_input, second_input):
        write_fasta(positive, directory / "prom-cnnprom-prokaryotic-target-10-81.fa")
        write_fasta(negative, directory / "nonprom-cnnprom-prokaryotic-target-10-81.fa")
    write_fasta(positive, second_input / "prom-cnnprom-prokaryotic-earlier-10-81.fa")
    write_fasta(negative, second_input / "nonprom-cnnprom-prokaryotic-earlier-10-81.fa")

    build_group_safe_intra_dataset_csvs_with_audit(first_input, first_output)
    build_group_safe_intra_dataset_csvs_with_audit(second_input, second_output)

    first_target = sorted(first_output.glob("*target*-test.csv"))[0].read_text()
    second_target = sorted(second_output.glob("*target*-test.csv"))[0].read_text()
    assert first_target == second_target
