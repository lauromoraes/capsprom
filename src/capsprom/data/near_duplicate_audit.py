"""Near-duplicate sensitivity auditing for fixed-length DNA train/test pairs."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .batch_audit import DatasetFile, discover_dataset_pairs


@dataclass(frozen=True)
class NearDuplicatePairAudit:
    dataset_id: str
    source: str
    domain: str
    dataset: str
    train_rows: int
    test_rows: int
    max_distance: int
    candidate_comparisons: int
    test_with_neighbor_d1: int
    test_with_neighbor_d2: int
    test_with_neighbor_d4: int
    test_with_neighbor_d8: int
    test_with_same_label_neighbor_d8: int
    test_with_different_label_neighbor_d8: int


def hamming_distance(left: str, right: str) -> int:
    """Return Hamming distance for equal-length sequences."""

    if len(left) != len(right):
        raise ValueError("Hamming distance requires equal-length sequences")
    return sum(a != b for a, b in zip(left, right, strict=True))


def _read_rows(path: Path) -> list[tuple[str, int]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [((row.get("sequence") or "").strip().upper(), int(row["label"])) for row in reader]


def _blocks(sequence_length: int, max_distance: int) -> list[tuple[int, int]]:
    block_count = max_distance + 1
    base, extra = divmod(sequence_length, block_count)
    bounds = []
    start = 0
    for index in range(block_count):
        end = start + base + (index < extra)
        bounds.append((start, end))
        start = end
    return bounds


def audit_near_duplicate_pair(
    train_file: DatasetFile,
    test_file: DatasetFile,
    sequence_length: int = 81,
    thresholds: tuple[int, ...] = (1, 2, 4, 8),
) -> NearDuplicatePairAudit:
    """Count test sequences with train neighbors at predeclared distances.

    A pigeonhole block index is exact for the largest threshold: any pair with
    Hamming distance at most ``k`` must share one of ``k + 1`` aligned blocks.
    """

    if not thresholds or thresholds != tuple(sorted(set(thresholds))):
        raise ValueError("thresholds must be non-empty, unique, and sorted")
    max_distance = thresholds[-1]
    if max_distance >= sequence_length:
        raise ValueError("maximum distance must be smaller than sequence length")

    train = _read_rows(train_file.path)
    test = _read_rows(test_file.path)
    if any(len(sequence) != sequence_length for sequence, _ in train + test):
        raise ValueError("all sequences must match the declared sequence length")

    bounds = _blocks(sequence_length, max_distance)
    index: dict[tuple[int, str], list[int]] = defaultdict(list)
    for row_index, (sequence, _) in enumerate(train):
        for block_index, (start, end) in enumerate(bounds):
            index[(block_index, sequence[start:end])].append(row_index)

    counts = {threshold: 0 for threshold in thresholds}
    same_label_max = 0
    different_label_max = 0
    comparisons = 0
    for test_sequence, test_label in test:
        candidates: set[int] = set()
        for block_index, (start, end) in enumerate(bounds):
            candidates.update(index.get((block_index, test_sequence[start:end]), ()))
        neighbor_distances: list[tuple[int, int]] = []
        for row_index in candidates:
            train_sequence, train_label = train[row_index]
            distance = hamming_distance(train_sequence, test_sequence)
            comparisons += 1
            if distance <= max_distance:
                neighbor_distances.append((distance, train_label))
        for threshold in thresholds:
            if any(distance <= threshold for distance, _ in neighbor_distances):
                counts[threshold] += 1
        if any(distance <= max_distance and label == test_label for distance, label in neighbor_distances):
            same_label_max += 1
        if any(distance <= max_distance and label != test_label for distance, label in neighbor_distances):
            different_label_max += 1

    expected = (1, 2, 4, 8)
    if thresholds != expected:
        raise ValueError(f"report schema requires thresholds={expected}")
    return NearDuplicatePairAudit(
        dataset_id=train_file.identity,
        source=train_file.source,
        domain=train_file.domain,
        dataset=train_file.dataset,
        train_rows=len(train),
        test_rows=len(test),
        max_distance=max_distance,
        candidate_comparisons=comparisons,
        test_with_neighbor_d1=counts[1],
        test_with_neighbor_d2=counts[2],
        test_with_neighbor_d4=counts[4],
        test_with_neighbor_d8=counts[8],
        test_with_same_label_neighbor_d8=same_label_max,
        test_with_different_label_neighbor_d8=different_label_max,
    )


def audit_near_duplicate_directory(
    input_dir: Path,
    output_dir: Path,
    sources: tuple[str, ...] = ("cdbprom", "cnnprom", "graphpro"),
    sequence_length: int = 81,
) -> dict[str, object]:
    """Audit all dataset pairs and persist JSON, CSV, and Markdown reports."""

    pairs = discover_dataset_pairs(input_dir, sources)
    audits = [audit_near_duplicate_pair(train, test, sequence_length) for train, test in pairs]
    digest = hashlib.sha256()
    digest.update(f"sequence_length={sequence_length};thresholds=1,2,4,8\n".encode())
    for train, test in pairs:
        digest.update(train.path.read_bytes())
        digest.update(test.path.read_bytes())
    report: dict[str, object] = {
        "audit_id": digest.hexdigest(),
        "input_directory": input_dir.resolve().as_posix(),
        "sequence_length": sequence_length,
        "distance": "hamming",
        "thresholds": [1, 2, 4, 8],
        "pair_count": len(audits),
        "pairs": [asdict(audit) for audit in audits],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "near_duplicate_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    rows = [asdict(audit) for audit in audits]
    with (output_dir / "near_duplicate_audit.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    _write_markdown(output_dir / "near_duplicate_audit.md", report, audits)
    return report


def _write_markdown(
    path: Path,
    report: dict[str, object],
    audits: list[NearDuplicatePairAudit],
) -> None:
    lines = [
        "# Near-Duplicate Train/Test Sensitivity Audit",
        "",
        "This report counts test sequences with at least one training neighbor at",
        "Hamming-distance thresholds 1, 2, 4, and 8. It is descriptive and does",
        "not remove records automatically.",
        "",
        f"Audit identifier: `{report['audit_id']}`.",
        "",
        "| Dataset | Test rows | d<=1 | d<=2 | d<=4 | d<=8 | Same label d<=8 | Different label d<=8 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for audit in audits:
        lines.append(
            f"| {audit.dataset_id} | {audit.test_rows} | {audit.test_with_neighbor_d1} | "
            f"{audit.test_with_neighbor_d2} | {audit.test_with_neighbor_d4} | "
            f"{audit.test_with_neighbor_d8} | {audit.test_with_same_label_neighbor_d8} | "
            f"{audit.test_with_different_label_neighbor_d8} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
