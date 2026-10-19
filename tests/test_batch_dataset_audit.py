import csv
from pathlib import Path

import pytest

from capsprom.data.batch_audit import audit_dataset_directory, discover_dataset_pairs, parse_dataset_filename


def _write_dataset(path: Path, rows: list[tuple[str, int]]) -> None:
    positive = sum(label == 1 for _, label in rows)
    negative = sum(label == 0 for _, label in rows)
    assert f"-p-{positive}-n-{negative}-" in path.name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sequence", "label"])
        writer.writerows(rows)


def _pair_paths(root: Path, dataset: str, train_rows, test_rows) -> tuple[Path, Path]:
    train_p = sum(label == 1 for _, label in train_rows)
    train_n = sum(label == 0 for _, label in train_rows)
    test_p = sum(label == 1 for _, label in test_rows)
    test_n = sum(label == 0 for _, label in test_rows)
    train = root / f"cnnprom-prokaryotic-{dataset}-p-{train_p}-n-{train_n}-train.csv"
    test = root / f"cnnprom-prokaryotic-{dataset}-p-{test_p}-n-{test_n}-test.csv"
    _write_dataset(train, train_rows)
    _write_dataset(test, test_rows)
    return train, test


def test_parse_and_discover_dataset_pairs(tmp_path):
    train, _ = _pair_paths(
        tmp_path,
        "fixture",
        [("AAAAAAAA", 1), ("CCCCCCCC", 0)],
        [("GGGGGGGG", 1), ("TTTTTTTT", 0)],
    )

    parsed = parse_dataset_filename(train)
    pairs = discover_dataset_pairs(tmp_path, ("cnnprom",))

    assert parsed.identity == "cnnprom-prokaryotic-fixture"
    assert len(pairs) == 1
    assert pairs[0][0].partition == "train"
    assert pairs[0][1].partition == "test"


def test_batch_audit_classifies_eligible_and_overlap(tmp_path):
    _pair_paths(
        tmp_path,
        "eligible",
        [("AAAAAAAA", 1), ("CCCCCCCC", 0)],
        [("GGGGGGGG", 1), ("TTTTTTTT", 0)],
    )
    _pair_paths(
        tmp_path,
        "overlap",
        [("ACGTACGT", 1), ("TGCATGCA", 0), ("TGCATGCA", 0)],
        [("ACGTACGT", 1), ("AAAACCCC", 0)],
    )

    report = audit_dataset_directory(tmp_path, tmp_path / "report", sources=("cnnprom",), sequence_length=8)
    statuses = {pair["dataset"]: pair["status"] for pair in report["pairs"]}

    assert report["pair_count"] == 2
    assert report["eligible_count"] == 1
    assert statuses == {"eligible": "eligible", "overlap": "train_test_overlap"}
    assert (tmp_path / "report" / "dataset_integrity_audit.json").is_file()
    assert (tmp_path / "report" / "dataset_integrity_audit.csv").is_file()
    assert (tmp_path / "report" / "dataset_integrity_audit.md").is_file()


def test_discovery_rejects_incomplete_pair(tmp_path):
    path = tmp_path / "graphpro-prokaryotic-fixture-p-1-n-1-train.csv"
    _write_dataset(path, [("AAAAAAAA", 1), ("CCCCCCCC", 0)])

    with pytest.raises(ValueError, match="missing partitions"):
        discover_dataset_pairs(tmp_path, ("graphpro",))
