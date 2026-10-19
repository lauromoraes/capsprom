"""Reusable dataset construction functions for CapsProm processed CSV files."""

from __future__ import annotations

import csv
import hashlib
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .sequences import crop_record, invalid_symbols, is_strict_dna, read_fasta, write_fasta

FILENAME_RE = re.compile(
    r"^(?P<class_name>prom|nonprom)-(?P<study>[^-]+)-(?P<organism_type>[^-]+)-(?P<dataset>.+)-(?P<count>\d+)-(?P<length>\d+)\.fa$"
)
COUNT_RE = re.compile(r"-p-(?P<p>\d+)-n-(?P<n>\d+)-(?P<partition>[^./]+)\.csv$", re.IGNORECASE)

DEFAULT_TSS_POSITIONS = {
    "graphpro": {81: 60},
    "cnnprom": {81: 60, 251: 200},
    "cdbprom": {100: 60, 1001: 500},
    "bhandari": {1000: 700},
}


@dataclass(frozen=True)
class FastaInfo:
    class_name: str
    study: str
    organism_type: str
    dataset: str
    count: int
    length: int
    path: Path


@dataclass(frozen=True)
class CsvBuildResult:
    output: Path
    positives: int
    negatives: int
    rows: int


@dataclass(frozen=True)
class CollisionFilterAudit:
    study: str
    organism_type: str
    dataset: str
    positive_rows_after_crop: int
    negative_rows_after_crop: int
    positive_unique_after_crop: int
    negative_unique_after_crop: int
    cross_label_collision_sequences: int
    positive_rows_removed_as_collisions: int
    negative_rows_removed_as_collisions: int
    positive_rows_after_collision_filter: int
    negative_rows_after_collision_filter: int
    train_positive: int
    train_negative: int
    test_positive: int
    test_negative: int


@dataclass(frozen=True)
class IntraDatasetBuildReport:
    outputs: tuple[CsvBuildResult, ...]
    collision_audits: tuple[CollisionFilterAudit, ...]


@dataclass(frozen=True)
class GroupSafeFilterAudit:
    """Stage counts for one canonical source-negative dataset build."""

    study: str
    organism_type: str
    dataset: str
    positive_rows_after_crop: int
    negative_rows_after_crop: int
    positive_unique_after_crop: int
    negative_unique_after_crop: int
    cross_label_collision_sequences: int
    positive_rows_removed_as_collisions: int
    negative_rows_removed_as_collisions: int
    positive_rows_after_collision_filter: int
    negative_rows_after_collision_filter: int
    positive_duplicate_rows_removed: int
    negative_duplicate_rows_removed: int
    positive_rows_after_deduplication: int
    negative_rows_after_deduplication: int
    positive_invalid_dna_rows_removed: int
    negative_invalid_dna_rows_removed: int
    positive_rows_before_split: int
    negative_rows_before_split: int
    train_positive: int
    train_negative: int
    test_positive: int
    test_negative: int


@dataclass(frozen=True)
class GroupSafeDatasetBuildReport:
    """Outputs and stage audits from the canonical group-safe builder."""

    outputs: tuple[CsvBuildResult, ...]
    filter_audits: tuple[GroupSafeFilterAudit, ...]


@dataclass(frozen=True)
class CleanCsvResult:
    source: Path
    output: Path
    rows_in: int
    rows_out: int
    removed_rows: int
    original_positive: int
    original_negative: int
    cleaned_positive: int
    cleaned_negative: int
    invalid_symbols: Counter[str]


def parse_fasta_name(path: Path) -> FastaInfo:
    """Parse the common CapsProm FASTA naming scheme."""

    match = FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(f"invalid CapsProm FASTA filename: {path.name}")
    groups = match.groupdict()
    return FastaInfo(
        class_name=groups["class_name"],
        study=groups["study"],
        organism_type=groups["organism_type"],
        dataset=groups["dataset"],
        count=int(groups["count"]),
        length=int(groups["length"]),
        path=path,
    )


def crop_fasta_directory(
    input_dir: Path,
    output_dir: Path,
    tss_positions: dict[str, dict[int, int]] | None = None,
    upstream_length: int = 60,
    downstream_length: int = 20,
) -> list[Path]:
    """Crop common-format FASTA files to fixed windows around the TSS."""

    tss_positions = tss_positions or DEFAULT_TSS_POSITIONS
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    new_length = upstream_length + downstream_length + 1

    for path in sorted(input_dir.glob("*.fa")):
        info = parse_fasta_name(path)
        study_positions = tss_positions.get(info.study)
        if not study_positions or info.length not in study_positions:
            continue
        tss = study_positions[info.length]
        records = [crop_record(record, tss, upstream_length, downstream_length) for record in read_fasta(path)]
        output_name = path.name.replace(f"-{info.length}.fa", f"-{new_length}.fa")
        output_path = output_dir / output_name
        write_fasta(records, output_path)
        outputs.append(output_path)
    return outputs


def group_promoter_pairs(fasta_files: Iterable[Path]) -> dict[tuple[str, str, str], dict[str, Path]]:
    """Group cropped FASTA files into promoter/non-promoter pairs."""

    grouped: dict[tuple[str, str, str], dict[str, Path]] = defaultdict(dict)
    for path in fasta_files:
        info = parse_fasta_name(path)
        key = (info.study, info.organism_type, info.dataset)
        grouped[key]["p" if info.class_name == "prom" else "n"] = path
    return dict(grouped)


def fasta_to_labeled_rows(path: Path, label: int, strict_dna_only: bool = False) -> list[dict[str, str | int]]:
    """Read FASTA records as `sequence,label` rows."""

    rows = []
    for record in read_fasta(path):
        sequence = record.sequence.upper()
        if strict_dna_only and not is_strict_dna(sequence):
            continue
        rows.append({"sequence": sequence, "label": label})
    return rows


def write_labeled_csv(rows: list[dict[str, str | int]], output: Path) -> None:
    """Write sequence-label rows to CSV."""

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sequence", "label"])
        writer.writeheader()
        writer.writerows(rows)


def build_intra_dataset_csvs(
    cropped_fasta_dir: Path,
    output_dir: Path,
    test_fraction: float = 0.2,
    random_seed: int = 42,
    strict_dna_only: bool = False,
) -> list[CsvBuildResult]:
    """Build CSVs after mandatorily removing post-crop cross-label collisions."""

    return list(
        build_intra_dataset_csvs_with_audit(
            cropped_fasta_dir,
            output_dir,
            test_fraction=test_fraction,
            random_seed=random_seed,
            strict_dna_only=strict_dna_only,
        ).outputs
    )


def build_intra_dataset_csvs_with_audit(
    cropped_fasta_dir: Path,
    output_dir: Path,
    test_fraction: float = 0.2,
    random_seed: int = 42,
    strict_dna_only: bool = False,
) -> IntraDatasetBuildReport:
    """Build train/test CSVs and report every post-crop collision removal."""

    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(random_seed)
    results: list[CsvBuildResult] = []
    audits: list[CollisionFilterAudit] = []

    pairs = group_promoter_pairs(sorted(cropped_fasta_dir.glob("*.fa")))
    for (study, organism_type, dataset), paths in sorted(pairs.items()):
        if "p" not in paths or "n" not in paths:
            continue
        positive_rows = fasta_to_labeled_rows(paths["p"], 1, strict_dna_only=strict_dna_only)
        negative_rows = fasta_to_labeled_rows(paths["n"], 0, strict_dna_only=strict_dna_only)
        positive_sequences = Counter(str(row["sequence"]) for row in positive_rows)
        negative_sequences = Counter(str(row["sequence"]) for row in negative_rows)
        collisions = set(positive_sequences) & set(negative_sequences)
        positive_removed = sum(positive_sequences[sequence] for sequence in collisions)
        negative_removed = sum(negative_sequences[sequence] for sequence in collisions)
        positive_rows = [row for row in positive_rows if row["sequence"] not in collisions]
        negative_rows = [row for row in negative_rows if row["sequence"] not in collisions]
        for rows in (positive_rows, negative_rows):
            rng.shuffle(rows)
        p_test = int(round(len(positive_rows) * test_fraction))
        n_test = int(round(len(negative_rows) * test_fraction))
        partitions = {
            "train": positive_rows[p_test:] + negative_rows[n_test:],
            "test": positive_rows[:p_test] + negative_rows[:n_test],
        }
        audits.append(
            CollisionFilterAudit(
                study=study,
                organism_type=organism_type,
                dataset=dataset,
                positive_rows_after_crop=sum(positive_sequences.values()),
                negative_rows_after_crop=sum(negative_sequences.values()),
                positive_unique_after_crop=len(positive_sequences),
                negative_unique_after_crop=len(negative_sequences),
                cross_label_collision_sequences=len(collisions),
                positive_rows_removed_as_collisions=positive_removed,
                negative_rows_removed_as_collisions=negative_removed,
                positive_rows_after_collision_filter=len(positive_rows),
                negative_rows_after_collision_filter=len(negative_rows),
                train_positive=len(positive_rows) - p_test,
                train_negative=len(negative_rows) - n_test,
                test_positive=p_test,
                test_negative=n_test,
            )
        )
        for partition, rows in partitions.items():
            rng.shuffle(rows)
            positives = sum(1 for row in rows if row["label"] == 1)
            negatives = sum(1 for row in rows if row["label"] == 0)
            output = output_dir / f"{study}-{organism_type}-{dataset}-p-{positives}-n-{negatives}-{partition}.csv"
            write_labeled_csv(rows, output)
            results.append(CsvBuildResult(output, positives, negatives, len(rows)))
    return IntraDatasetBuildReport(tuple(results), tuple(audits))


def _deduplicate_labeled_rows(rows: list[dict[str, str | int]]) -> tuple[list[dict[str, str | int]], int]:
    """Keep the first row for each normalized sequence and count removals."""

    unique: dict[str, dict[str, str | int]] = {}
    for row in rows:
        unique.setdefault(str(row["sequence"]), row)
    return list(unique.values()), len(rows) - len(unique)


def _dataset_rng(seed: int, study: str, organism_type: str, dataset: str) -> random.Random:
    """Return an order-independent deterministic RNG for one dataset."""

    identity = f"{seed}:{study}:{organism_type}:{dataset}".encode()
    derived_seed = int.from_bytes(hashlib.sha256(identity).digest()[:8], "big")
    return random.Random(derived_seed)


def _test_size(row_count: int, test_fraction: float) -> int:
    """Return a non-empty test size when both partitions can be formed."""

    if row_count < 2:
        raise ValueError("each class must contain at least two unique strict-DNA sequences")
    return min(row_count - 1, max(1, int(round(row_count * test_fraction))))


def build_group_safe_intra_dataset_csvs_with_audit(
    cropped_fasta_dir: Path,
    output_dir: Path,
    test_fraction: float = 0.2,
    random_seed: int = 42,
) -> GroupSafeDatasetBuildReport:
    """Build canonical exact-sequence-safe train/test datasets.

    The fixed order is collision removal, within-class deduplication, strict-DNA
    filtering, and deterministic class-stratified assignment of unique sequence
    groups. Consequently, no exact identity can occur twice or cross the split.
    """

    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[CsvBuildResult] = []
    audits: list[GroupSafeFilterAudit] = []

    pairs = group_promoter_pairs(sorted(cropped_fasta_dir.glob("*.fa")))
    for (study, organism_type, dataset), paths in sorted(pairs.items()):
        if "p" not in paths or "n" not in paths:
            continue
        positive_rows = fasta_to_labeled_rows(paths["p"], 1)
        negative_rows = fasta_to_labeled_rows(paths["n"], 0)
        positive_sequences = Counter(str(row["sequence"]) for row in positive_rows)
        negative_sequences = Counter(str(row["sequence"]) for row in negative_rows)

        collisions = set(positive_sequences) & set(negative_sequences)
        positive_collision_removed = sum(positive_sequences[sequence] for sequence in collisions)
        negative_collision_removed = sum(negative_sequences[sequence] for sequence in collisions)
        positive_rows = [row for row in positive_rows if row["sequence"] not in collisions]
        negative_rows = [row for row in negative_rows if row["sequence"] not in collisions]
        positive_after_collision = len(positive_rows)
        negative_after_collision = len(negative_rows)

        positive_rows, positive_duplicates_removed = _deduplicate_labeled_rows(positive_rows)
        negative_rows, negative_duplicates_removed = _deduplicate_labeled_rows(negative_rows)
        positive_after_deduplication = len(positive_rows)
        negative_after_deduplication = len(negative_rows)

        positive_invalid_removed = sum(not is_strict_dna(str(row["sequence"])) for row in positive_rows)
        negative_invalid_removed = sum(not is_strict_dna(str(row["sequence"])) for row in negative_rows)
        positive_rows = [row for row in positive_rows if is_strict_dna(str(row["sequence"]))]
        negative_rows = [row for row in negative_rows if is_strict_dna(str(row["sequence"]))]

        rng = _dataset_rng(random_seed, study, organism_type, dataset)
        rng.shuffle(positive_rows)
        rng.shuffle(negative_rows)
        p_test = _test_size(len(positive_rows), test_fraction)
        n_test = _test_size(len(negative_rows), test_fraction)
        partitions = {
            "train": positive_rows[p_test:] + negative_rows[n_test:],
            "test": positive_rows[:p_test] + negative_rows[:n_test],
        }
        audits.append(
            GroupSafeFilterAudit(
                study=study,
                organism_type=organism_type,
                dataset=dataset,
                positive_rows_after_crop=sum(positive_sequences.values()),
                negative_rows_after_crop=sum(negative_sequences.values()),
                positive_unique_after_crop=len(positive_sequences),
                negative_unique_after_crop=len(negative_sequences),
                cross_label_collision_sequences=len(collisions),
                positive_rows_removed_as_collisions=positive_collision_removed,
                negative_rows_removed_as_collisions=negative_collision_removed,
                positive_rows_after_collision_filter=positive_after_collision,
                negative_rows_after_collision_filter=negative_after_collision,
                positive_duplicate_rows_removed=positive_duplicates_removed,
                negative_duplicate_rows_removed=negative_duplicates_removed,
                positive_rows_after_deduplication=positive_after_deduplication,
                negative_rows_after_deduplication=negative_after_deduplication,
                positive_invalid_dna_rows_removed=positive_invalid_removed,
                negative_invalid_dna_rows_removed=negative_invalid_removed,
                positive_rows_before_split=len(positive_rows),
                negative_rows_before_split=len(negative_rows),
                train_positive=len(positive_rows) - p_test,
                train_negative=len(negative_rows) - n_test,
                test_positive=p_test,
                test_negative=n_test,
            )
        )
        for partition, rows in partitions.items():
            rng.shuffle(rows)
            positives = sum(1 for row in rows if row["label"] == 1)
            negatives = sum(1 for row in rows if row["label"] == 0)
            output = output_dir / f"{study}-{organism_type}-{dataset}-p-{positives}-n-{negatives}-{partition}.csv"
            write_labeled_csv(rows, output)
            results.append(CsvBuildResult(output, positives, negatives, len(rows)))
    return GroupSafeDatasetBuildReport(tuple(results), tuple(audits))


def cleaned_csv_name(source: Path, positive: int, negative: int) -> str:
    """Return a filename with updated positive and negative counts."""

    match = COUNT_RE.search(source.name)
    if not match:
        return source.name
    return COUNT_RE.sub(f"-p-{positive}-n-{negative}-{match.group('partition')}.csv", source.name)


def clean_processed_csv(source: Path, output_dir: Path) -> CleanCsvResult:
    """Copy a processed CSV while removing only rows with non-strict DNA symbols."""

    output_dir.mkdir(parents=True, exist_ok=True)
    invalid: Counter[str] = Counter()
    rows_in = 0
    rows_out = 0
    removed = 0
    original_labels: Counter[str] = Counter()
    cleaned_labels: Counter[str] = Counter()
    cleaned_rows: list[dict[str, str]] = []

    with source.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "sequence" not in reader.fieldnames or "label" not in reader.fieldnames:
            raise ValueError(f"processed CSV must include sequence and label columns: {source}")
        fieldnames = reader.fieldnames
        for row in reader:
            rows_in += 1
            sequence = (row.get("sequence") or "").strip().upper()
            label = (row.get("label") or "").strip()
            original_labels[label] += 1
            bad_symbols = invalid_symbols(sequence)
            if bad_symbols:
                invalid.update(bad_symbols)
                removed += 1
                continue
            row["sequence"] = sequence
            cleaned_rows.append(row)
            cleaned_labels[label] += 1
            rows_out += 1

    output = output_dir / cleaned_csv_name(source, cleaned_labels.get("1", 0), cleaned_labels.get("0", 0))
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    return CleanCsvResult(
        source=source,
        output=output,
        rows_in=rows_in,
        rows_out=rows_out,
        removed_rows=removed,
        original_positive=original_labels.get("1", 0),
        original_negative=original_labels.get("0", 0),
        cleaned_positive=cleaned_labels.get("1", 0),
        cleaned_negative=cleaned_labels.get("0", 0),
        invalid_symbols=invalid,
    )


def clean_processed_directory(source_dir: Path, output_dir: Path) -> list[CleanCsvResult]:
    """Clean every processed CSV in a directory."""

    return [clean_processed_csv(path, output_dir) for path in sorted(source_dir.glob("*.csv"))]
