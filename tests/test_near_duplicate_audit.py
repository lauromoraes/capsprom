import csv
from pathlib import Path

from capsprom.data.batch_audit import DatasetFile
from capsprom.data.near_duplicate_audit import audit_near_duplicate_pair, hamming_distance



def _write(path: Path, rows: list[tuple[str, int]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sequence", "label"])
        writer.writerows(rows)


def test_hamming_distance():
    assert hamming_distance("AAAAAAAA", "AAAAAAAC") == 1


def test_near_duplicate_pair_counts_neighbors_by_threshold(tmp_path: Path):
    train = tmp_path / "cnnprom-prokaryotic-near-p-1-n-1-train.csv"
    test = tmp_path / "cnnprom-prokaryotic-near-p-2-n-1-test.csv"
    _write(train, [("AAAAAAAAA", 1), ("CCCCCCCCC", 0)])
    _write(test, [("AAAAAAAAC", 1), ("CCCCCCCAA", 1), ("GGGGGGGGC", 0)])
    train_file = DatasetFile("cnnprom", "prokaryotic", "near", "train", 1, 1, train)
    test_file = DatasetFile("cnnprom", "prokaryotic", "near", "test", 2, 1, test)

    audit = audit_near_duplicate_pair(train_file, test_file, sequence_length=9)

    assert audit.test_with_neighbor_d1 == 1
    assert audit.test_with_neighbor_d2 == 2
    assert audit.test_with_neighbor_d4 == 2
    assert audit.test_with_neighbor_d8 == 3
    assert audit.test_with_same_label_neighbor_d8 == 3
    assert audit.test_with_different_label_neighbor_d8 == 2
