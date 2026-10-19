"""Batch integrity auditing for source-provided train/test dataset pairs."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from capsprom.config import DataConfig
from capsprom.experiment import audit_dataset_pair, read_dataset

DATASET_NAME_RE = re.compile(
    r"^(?P<source>[^-]+)-(?P<domain>[^-]+)-(?P<dataset>.+)-p-(?P<positive>\d+)"
    r"-n-(?P<negative>\d+)-(?P<partition>train|test)\.csv$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DatasetFile:
    source: str
    domain: str
    dataset: str
    partition: str
    positive: int
    negative: int
    path: Path

    @property
    def identity(self) -> str:
        return f"{self.source}-{self.domain}-{self.dataset}"


@dataclass(frozen=True)
class PairAudit:
    dataset_id: str
    source: str
    domain: str
    dataset: str
    status: str
    reasons: str
    train_path: str
    test_path: str
    train_positive: int
    train_negative: int
    test_positive: int
    test_negative: int
    train_rows: int
    test_rows: int
    train_unique_sequences: int
    test_unique_sequences: int
    train_duplicate_rows: int
    test_duplicate_rows: int
    train_conflicting_label_sequences: int
    test_conflicting_label_sequences: int
    train_test_overlap_unique_sequences: int
    train_rows_in_overlap: int
    test_rows_in_overlap: int
    overlap_positive_sequences: int
    overlap_negative_sequences: int
    conflicting_label_sequences_total: int
    train_test_conflicting_label_sequences: int
    train_sha256: str
    test_sha256: str


def parse_dataset_filename(path: Path) -> DatasetFile:
    """Parse one strict-DNA dataset filename."""

    match = DATASET_NAME_RE.match(path.name)
    if match is None:
        raise ValueError(f"invalid dataset filename: {path.name}")
    values = match.groupdict()
    return DatasetFile(
        source=values["source"].lower(),
        domain=values["domain"].lower(),
        dataset=values["dataset"],
        partition=values["partition"].lower(),
        positive=int(values["positive"]),
        negative=int(values["negative"]),
        path=path.resolve(),
    )


def discover_dataset_pairs(input_dir: Path, sources: Iterable[str]) -> list[tuple[DatasetFile, DatasetFile]]:
    """Discover complete train/test pairs for the requested sources."""

    accepted_sources = {source.lower() for source in sources}
    grouped: dict[str, dict[str, DatasetFile]] = defaultdict(dict)
    for path in sorted(input_dir.glob("*.csv")):
        match = DATASET_NAME_RE.match(path.name)
        if match is None or match.group("source").lower() not in accepted_sources:
            continue
        item = parse_dataset_filename(path)
        if item.partition in grouped[item.identity]:
            raise ValueError(f"duplicate {item.partition} file for {item.identity}")
        grouped[item.identity][item.partition] = item

    pairs: list[tuple[DatasetFile, DatasetFile]] = []
    for identity, partitions in sorted(grouped.items()):
        missing = sorted({"train", "test"} - set(partitions))
        if missing:
            raise ValueError(f"dataset {identity} is missing partitions: {missing}")
        pairs.append((partitions["train"], partitions["test"]))
    if not pairs:
        raise ValueError(f"no complete dataset pairs found in {input_dir}")
    return pairs


def audit_dataset_directory(
    input_dir: Path,
    output_dir: Path,
    sources: tuple[str, ...] = ("cdbprom", "cnnprom", "graphpro"),
    sequence_length: int = 81,
) -> dict[str, object]:
    """Audit all discovered dataset pairs and persist reproducible reports."""

    pairs = discover_dataset_pairs(input_dir, sources)
    audits = [audit_pair(train, test, sequence_length=sequence_length) for train, test in pairs]
    status_counts = Counter(audit.status for audit in audits)
    audit_id = _audit_identifier(audits, sources, sequence_length)
    report: dict[str, object] = {
        "audit_id": audit_id,
        "input_directory": input_dir.resolve().as_posix(),
        "sources": list(sources),
        "sequence_length": sequence_length,
        "pair_count": len(audits),
        "eligible_count": status_counts.get("eligible", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "pairs": [asdict(audit) for audit in audits],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "dataset_integrity_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_csv(output_dir / "dataset_integrity_audit.csv", audits)
    _write_markdown(output_dir / "dataset_integrity_audit.md", report, audits)
    return report


def audit_pair(train_file: DatasetFile, test_file: DatasetFile, sequence_length: int = 81) -> PairAudit:
    """Audit one pair and assign its strict eligibility status."""

    config = DataConfig(
        train_csv=train_file.path,
        test_csv=test_file.path,
        sequence_column="sequence",
        label_column="label",
        sequence_length=sequence_length,
        alphabet=("A", "C", "G", "T"),
        max_train_samples=None,
        max_test_samples=None,
        random_seed=42,
    )
    train = read_dataset(train_file.path, config, max_samples=None)
    test = read_dataset(test_file.path, config, max_samples=None)
    if train.labels.count(1) != train_file.positive or train.labels.count(0) != train_file.negative:
        raise ValueError(f"filename class counts do not match {train_file.path}")
    if test.labels.count(1) != test_file.positive or test.labels.count(0) != test_file.negative:
        raise ValueError(f"filename class counts do not match {test_file.path}")

    base = audit_dataset_pair(config)
    train_labels = _single_labels(train.sequences, train.labels)
    test_labels = _single_labels(test.sequences, test.labels)
    overlap = set(train_labels) & set(test_labels)
    conflicting_sequences = {
        sequence for sequence, label in train_labels.items() if label is None
    } | {sequence for sequence, label in test_labels.items() if label is None}
    conflicting_sequences |= {
        sequence
        for sequence in overlap
        if train_labels[sequence] is None
        or test_labels[sequence] is None
        or train_labels[sequence] != test_labels[sequence]
    }
    agreed_overlap = {
        sequence: train_labels[sequence]
        for sequence in overlap
        if train_labels[sequence] is not None and train_labels[sequence] == test_labels[sequence]
    }
    status, reasons = _eligibility(base)
    return PairAudit(
        dataset_id=train_file.identity,
        source=train_file.source,
        domain=train_file.domain,
        dataset=train_file.dataset,
        status=status,
        reasons=",".join(reasons),
        train_path=train_file.path.as_posix(),
        test_path=test_file.path.as_posix(),
        train_positive=train_file.positive,
        train_negative=train_file.negative,
        test_positive=test_file.positive,
        test_negative=test_file.negative,
        overlap_positive_sequences=sum(label == 1 for label in agreed_overlap.values()),
        overlap_negative_sequences=sum(label == 0 for label in agreed_overlap.values()),
        conflicting_label_sequences_total=len(conflicting_sequences),
        **base,
    )


def _single_labels(sequences: list[str], labels: list[int]) -> dict[str, int | None]:
    grouped: dict[str, set[int]] = defaultdict(set)
    for sequence, label in zip(sequences, labels, strict=True):
        grouped[sequence].add(label)
    return {sequence: next(iter(values)) if len(values) == 1 else None for sequence, values in grouped.items()}


def _eligibility(audit: dict[str, object]) -> tuple[str, list[str]]:
    conflicts = sum(
        int(audit[key])
        for key in (
            "train_conflicting_label_sequences",
            "test_conflicting_label_sequences",
            "train_test_conflicting_label_sequences",
        )
    )
    duplicates = int(audit["train_duplicate_rows"]) + int(audit["test_duplicate_rows"])
    overlap = int(audit["train_test_overlap_unique_sequences"])
    if conflicts:
        return "conflicting_labels", ["conflicting_labels"]
    if overlap:
        reasons = ["train_test_overlap"]
        if duplicates:
            reasons.append("internal_duplicates")
        return "train_test_overlap", reasons
    if duplicates:
        return "internal_duplicates", ["internal_duplicates"]
    return "eligible", []


def _audit_identifier(audits: list[PairAudit], sources: Iterable[str], sequence_length: int) -> str:
    digest = hashlib.sha256()
    digest.update(f"sequence_length={sequence_length}\n".encode())
    digest.update(f"sources={','.join(sorted(sources))}\n".encode())
    for audit in audits:
        digest.update(f"{audit.dataset_id}:{audit.train_sha256}:{audit.test_sha256}\n".encode())
    return digest.hexdigest()


def _write_csv(path: Path, audits: list[PairAudit]) -> None:
    rows = [asdict(audit) for audit in audits]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, report: dict[str, object], audits: list[PairAudit]) -> None:
    lines = [
        "# Source-Provided Negative Dataset Integrity Audit",
        "",
        "## Scope",
        "",
        "This generated report audits exact duplicates, label conflicts, and train/test overlap",
        "for CDBProm, CNNProm, and GraphPro strict-DNA dataset pairs. Bhandari is excluded",
        "because its synthetic-negative workflow is audited separately.",
        "",
        f"Audit identifier: `{report['audit_id']}`.",
        "",
        "## Eligibility Summary",
        "",
        f"Table `tab:real-negative-dataset-eligibility` reports {len(audits)} train/test pairs; ",
        f"{report['eligible_count']} pass the strict zero-duplicate and zero-overlap criteria.",
        "",
        "| Source | Domain | Dataset | Status | Train duplicates | Test duplicates | Shared sequences | Label conflicts |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for audit in audits:
        lines.append(
            f"| {audit.source} | {audit.domain} | {audit.dataset} | {audit.status} | "
            f"{audit.train_duplicate_rows} | {audit.test_duplicate_rows} | "
            f"{audit.train_test_overlap_unique_sequences} | {audit.conflicting_label_sequences_total} |"
        )
    lines.extend(
        [
            "",
            "Table label: `tab:real-negative-dataset-eligibility`.",
            "",
            "Non-eligible datasets require a source-aware correction and a new immutable split manifest",
            "before confirmatory use. Counts in this report are descriptive data-integrity outcomes, not",
            "model-performance results.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
