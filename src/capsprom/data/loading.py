"""Strict loading and integrity audits for model-ready datasets."""

from __future__ import annotations

import csv
import hashlib
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from ..config import DataConfig


@dataclass(frozen=True)
class DatasetSplit:
    row_ids: list[str]
    sequences: list[str]
    labels: list[int]


def validate_dataset(path: Path, config: DataConfig) -> dict[str, int | str]:
    split = read_dataset(path, config, max_samples=None)
    return {
        "path": path.as_posix(),
        "rows": len(split.labels),
        "positive": sum(split.labels),
        "negative": len(split.labels) - sum(split.labels),
        "sha256": sha256_file(path),
    }


def audit_dataset_pair(config: DataConfig) -> dict[str, object]:
    train = read_dataset(config.train_csv, config, max_samples=None)
    test = read_dataset(config.test_csv, config, max_samples=None)
    train_counts = Counter(train.sequences)
    test_counts = Counter(test.sequences)
    train_labels = _labels_by_sequence(train)
    test_labels = _labels_by_sequence(test)
    overlap = set(train_counts) & set(test_counts)
    conflicting_train = {sequence for sequence, labels in train_labels.items() if len(labels) > 1}
    conflicting_test = {sequence for sequence, labels in test_labels.items() if len(labels) > 1}
    conflicting_across = {
        sequence for sequence in overlap if len(train_labels[sequence] | test_labels[sequence]) > 1
    }
    return {
        "train_rows": len(train.labels),
        "test_rows": len(test.labels),
        "train_unique_sequences": len(train_counts),
        "test_unique_sequences": len(test_counts),
        "train_duplicate_rows": sum(count - 1 for count in train_counts.values()),
        "test_duplicate_rows": sum(count - 1 for count in test_counts.values()),
        "train_conflicting_label_sequences": len(conflicting_train),
        "test_conflicting_label_sequences": len(conflicting_test),
        "train_test_overlap_unique_sequences": len(overlap),
        "train_rows_in_overlap": sum(train_counts[sequence] for sequence in overlap),
        "test_rows_in_overlap": sum(test_counts[sequence] for sequence in overlap),
        "train_test_conflicting_label_sequences": len(conflicting_across),
        "train_sha256": sha256_file(config.train_csv),
        "test_sha256": sha256_file(config.test_csv),
    }


def read_dataset(path: Path, config: DataConfig, max_samples: int | None) -> DatasetSplit:
    groups: dict[int, list[tuple[str, str]]] = {0: [], 1: []}
    alphabet = set(config.alphabet)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {config.sequence_column, config.label_column}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain columns {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            sequence = row[config.sequence_column].strip().upper()
            try:
                label = int(row[config.label_column])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{row_number} has a non-integer label") from exc
            if label not in groups:
                raise ValueError(f"{path}:{row_number} has non-binary label {label}")
            if len(sequence) != config.sequence_length:
                raise ValueError(
                    f"{path}:{row_number} has sequence length {len(sequence)}; "
                    f"expected {config.sequence_length}"
                )
            invalid = sorted(set(sequence) - alphabet)
            if invalid:
                raise ValueError(f"{path}:{row_number} has invalid sequence symbols {invalid}")
            groups[label].append((f"row-{row_number - 1:09d}", sequence))

    if not groups[0] or not groups[1]:
        raise ValueError(f"{path} must contain both binary classes")
    if max_samples is not None:
        groups = _stratified_sample(groups, max_samples, config.random_seed)

    pairs = [(row_id, sequence, label) for label, records in groups.items() for row_id, sequence in records]
    random.Random(config.random_seed).shuffle(pairs)
    return DatasetSplit(
        row_ids=[row_id for row_id, _, _ in pairs],
        sequences=[sequence for _, sequence, _ in pairs],
        labels=[label for _, _, label in pairs],
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stratified_sample(
    groups: dict[int, list[tuple[str, str]]], maximum: int, seed: int
) -> dict[int, list[tuple[str, str]]]:
    if maximum < 2:
        raise ValueError("sample limits must be at least 2 to retain both classes")
    total = sum(len(values) for values in groups.values())
    if maximum >= total:
        return groups
    rng = random.Random(seed)
    class_zero = maximum // 2
    targets = {0: min(class_zero, len(groups[0])), 1: min(maximum - class_zero, len(groups[1]))}
    unused = maximum - sum(targets.values())
    for label in (0, 1):
        addition = min(unused, len(groups[label]) - targets[label])
        targets[label] += addition
        unused -= addition
    return {label: rng.sample(values, targets[label]) for label, values in groups.items()}


def _labels_by_sequence(split: DatasetSplit) -> dict[str, set[int]]:
    labels: dict[str, set[int]] = defaultdict(set)
    for sequence, label in zip(split.sequences, split.labels, strict=True):
        labels[sequence].add(label)
    return labels
