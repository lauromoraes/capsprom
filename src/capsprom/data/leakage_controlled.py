"""Build leakage-controlled promoter datasets from raw positive sequences."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from .sequences import crop_sequence, is_strict_dna, read_fasta


@dataclass(frozen=True)
class LeakageControlledBuildResult:
    source: Path
    output_dir: Path
    train_csv: Path
    test_csv: Path
    manifest_csv: Path
    report_json: Path
    raw_records: int
    retained_source_records: int
    unique_positive_sequences: int
    removed_duplicate_positive_records: int
    train_pairs: int
    test_pairs: int


def build_bhandari_shuffled_dataset(
    source_fasta: Path,
    output_dir: Path,
    *,
    source_length: int = 1000,
    tss_position: int = 700,
    upstream_length: int = 60,
    downstream_length: int = 20,
    test_fraction: float = 0.2,
    seed: int = 42,
) -> LeakageControlledBuildResult:
    """Create a deduplicated split with one shuffled negative per positive.

    Exact positive windows are deduplicated before negative generation. Each
    positive and its composition-preserving mononucleotide shuffle form one
    group, and the whole group is assigned to a single partition.
    """

    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between 0 and 1")
    records = read_fasta(source_fasta)
    positive_counts: Counter[str] = Counter()
    invalid_windows = 0
    retained_source_records = 0
    for record in records:
        if len(record.sequence) != source_length:
            continue
        retained_source_records += 1
        window = crop_sequence(record.sequence, tss_position, upstream_length, downstream_length)
        if not is_strict_dna(window):
            invalid_windows += 1
            continue
        positive_counts[window] += 1

    positives = sorted(positive_counts)
    if len(positives) < 2:
        raise ValueError("at least two unique strict-DNA positive windows are required")
    negatives = generate_unique_mononucleotide_shuffles(positives, seed=seed)

    group_indices = list(range(len(positives)))
    random.Random(seed).shuffle(group_indices)
    test_groups = set(group_indices[: int(round(len(group_indices) * test_fraction))])
    partitions = ["test" if index in test_groups else "train" for index in range(len(positives))]

    output_dir.mkdir(parents=True, exist_ok=True)
    train_pairs = partitions.count("train")
    test_pairs = partitions.count("test")
    train_csv = output_dir / _dataset_name("train", train_pairs)
    test_csv = output_dir / _dataset_name("test", test_pairs)
    manifest_csv = output_dir / "group_manifest.csv"
    report_json = output_dir / "build_report.json"

    _write_partition(train_csv, positives, negatives, partitions, "train", seed)
    _write_partition(test_csv, positives, negatives, partitions, "test", seed)
    _write_manifest(manifest_csv, positives, negatives, positive_counts, partitions)

    result = LeakageControlledBuildResult(
        source=source_fasta.resolve(),
        output_dir=output_dir.resolve(),
        train_csv=train_csv.resolve(),
        test_csv=test_csv.resolve(),
        manifest_csv=manifest_csv.resolve(),
        report_json=report_json.resolve(),
        raw_records=len(records),
        retained_source_records=retained_source_records,
        unique_positive_sequences=len(positives),
        removed_duplicate_positive_records=sum(positive_counts.values()) - len(positives),
        train_pairs=train_pairs,
        test_pairs=test_pairs,
    )
    report = {
        **{key: str(value) if isinstance(value, Path) else value for key, value in asdict(result).items()},
        "method_version": "bhandari-deduplicated-mononucleotide-shuffle-v1",
        "source_sha256": _sha256_file(source_fasta),
        "source_length": source_length,
        "tss_position": tss_position,
        "window_length": upstream_length + downstream_length + 1,
        "invalid_windows_removed": invalid_windows,
        "negative_generation": "one deterministic mononucleotide shuffle per unique positive window",
        "split_unit": "positive-negative pair",
        "test_fraction": test_fraction,
        "seed": seed,
        "train_sha256": _sha256_file(train_csv),
        "test_sha256": _sha256_file(test_csv),
        "manifest_sha256": _sha256_file(manifest_csv),
        "acceptance": {
            "duplicate_sequences": 0,
            "train_test_exact_overlap": 0,
            "conflicting_labels": 0,
        },
    }
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return result


def generate_unique_mononucleotide_shuffles(
    positives: list[str], *, seed: int, max_attempts: int = 1000
) -> list[str]:
    """Generate one deterministic, globally unique shuffle per positive."""

    forbidden = set(positives)
    negatives: list[str] = []
    for positive in positives:
        sequence_seed = int.from_bytes(
            hashlib.sha256(f"{seed}:{positive}".encode("ascii")).digest()[:8], "big"
        )
        rng = random.Random(sequence_seed)
        symbols = list(positive)
        for _ in range(max_attempts):
            rng.shuffle(symbols)
            candidate = "".join(symbols)
            if candidate not in forbidden:
                negatives.append(candidate)
                forbidden.add(candidate)
                break
        else:
            raise ValueError(
                "could not generate a unique shuffled negative; "
                f"the sequence may have insufficient symbol diversity: {positive!r}"
            )
    return negatives


def _write_partition(
    path: Path,
    positives: list[str],
    negatives: list[str],
    partitions: list[str],
    selected_partition: str,
    seed: int,
) -> None:
    rows = [
        {"sequence": sequence, "label": label}
        for positive, negative, partition in zip(positives, negatives, partitions, strict=True)
        if partition == selected_partition
        for sequence, label in ((positive, 1), (negative, 0))
    ]
    random.Random(f"{seed}:{selected_partition}").shuffle(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sequence", "label"])
        writer.writeheader()
        writer.writerows(rows)


def _write_manifest(
    path: Path,
    positives: list[str],
    negatives: list[str],
    positive_counts: Counter[str],
    partitions: list[str],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "group_id",
                "partition",
                "raw_positive_multiplicity",
                "positive_sha256",
                "negative_sha256",
            ],
        )
        writer.writeheader()
        for positive, negative, partition in zip(positives, negatives, partitions, strict=True):
            positive_hash = hashlib.sha256(positive.encode("ascii")).hexdigest()
            writer.writerow(
                {
                    "group_id": positive_hash[:16],
                    "partition": partition,
                    "raw_positive_multiplicity": positive_counts[positive],
                    "positive_sha256": positive_hash,
                    "negative_sha256": hashlib.sha256(negative.encode("ascii")).hexdigest(),
                }
            )


def _dataset_name(partition: str, pairs: int) -> str:
    return f"bhandari-eukaryotic-Human_promoter_deduplicated_shuffle_v1-p-{pairs}-n-{pairs}-{partition}.csv"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
