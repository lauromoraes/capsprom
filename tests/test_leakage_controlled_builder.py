import csv
from collections import Counter
from pathlib import Path

from capsprom.data.leakage_controlled import build_bhandari_shuffled_dataset


def _write_fasta(path: Path) -> None:
    sequences = [
        "AACCGGTTAACC",
        "AACCGGTTAACC",
        "TTGGCCAATTGG",
        "ACGTACGTACGT",
        "GATTACAGATTA",
        "CCGTAACCGTAA",
    ]
    path.write_text(
        "".join(f">record-{index}\n{sequence}\n" for index, sequence in enumerate(sequences)),
        encoding="utf-8",
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_builder_deduplicates_and_prevents_partition_overlap(tmp_path):
    source = tmp_path / "source.fa"
    output = tmp_path / "output"
    _write_fasta(source)

    result = build_bhandari_shuffled_dataset(
        source,
        output,
        source_length=12,
        tss_position=6,
        upstream_length=2,
        downstream_length=2,
        test_fraction=0.4,
        seed=7,
    )
    train = _read_rows(result.train_csv)
    test = _read_rows(result.test_csv)
    train_sequences = {row["sequence"] for row in train}
    test_sequences = {row["sequence"] for row in test}
    all_rows = train + test

    assert train_sequences.isdisjoint(test_sequences)
    assert len(train_sequences) == len(train)
    assert len(test_sequences) == len(test)
    assert result.removed_duplicate_positive_records == 1
    assert Counter(row["label"] for row in train)["0"] == Counter(row["label"] for row in train)["1"]
    assert Counter(row["label"] for row in test)["0"] == Counter(row["label"] for row in test)["1"]

    positive_compositions = Counter(
        tuple(row["sequence"].count(base) for base in "ACGT") for row in all_rows if row["label"] == "1"
    )
    negative_compositions = Counter(
        tuple(row["sequence"].count(base) for base in "ACGT") for row in all_rows if row["label"] == "0"
    )
    assert positive_compositions == negative_compositions


def test_builder_is_byte_reproducible(tmp_path):
    source = tmp_path / "source.fa"
    _write_fasta(source)
    first = build_bhandari_shuffled_dataset(
        source,
        tmp_path / "first",
        source_length=12,
        tss_position=6,
        upstream_length=2,
        downstream_length=2,
        seed=11,
    )
    second = build_bhandari_shuffled_dataset(
        source,
        tmp_path / "second",
        source_length=12,
        tss_position=6,
        upstream_length=2,
        downstream_length=2,
        seed=11,
    )

    assert first.train_csv.read_bytes() == second.train_csv.read_bytes()
    assert first.test_csv.read_bytes() == second.test_csv.read_bytes()
    assert first.manifest_csv.read_bytes() == second.manifest_csv.read_bytes()
