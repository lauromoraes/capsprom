"""Model-ready training conditions of the CNNProm E. coli genomic pilot.

Partitions and homology groups come from the grouped native build, so one
fold manifest per condition replaces the record-level stratified folds.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class PanelRecord:
    record_id: str
    sequence: str
    label: int
    group: str
    partition: str
    negative_family: str


def native_records(grouped_rows: Iterable[Mapping[str, str]]) -> list[PanelRecord]:
    return [
        PanelRecord(
            row["record_id"],
            row["sequence"].upper(),
            int(row["label"]),
            row["group"],
            row["partition"],
            "positive" if int(row["label"]) == 1 else "native_cds",
        )
        for row in grouped_rows
    ]


def genomic_records(
    ledger_rows: Iterable[Mapping[str, str]], native: Sequence[PanelRecord]
) -> list[PanelRecord]:
    """Pair each ledger control with its positive; a mismatch stops the build."""

    by_id = {record.record_id: record for record in native}
    records: list[PanelRecord] = []
    for row in ledger_rows:
        positive = by_id.get(row["native_record_id"])
        if (
            positive is None
            or positive.label != 1
            or positive.sequence != row["positive_sequence"].upper()
            or positive.group != row["group"]
            or positive.partition != row["partition"]
        ):
            raise ValueError(f"ledger row differs from the native build: {row['record_id']}")
        records.append(positive)
        records.append(
            PanelRecord(
                f"{positive.record_id}|genomic-control",
                row["negative_sequence"].upper(),
                0,
                positive.group,
                positive.partition,
                "genomic_gc_matched",
            )
        )
    return records


def check_group_safety(records: Sequence[PanelRecord]) -> None:
    partitions: dict[str, set[str]] = {}
    for record in records:
        partitions.setdefault(record.group, set()).add(record.partition)
    crossing = sorted(group for group, values in partitions.items() if len(values) > 1)
    if crossing:
        raise ValueError(f"homology groups span partitions: {crossing[:5]}")


def training_records(records: Sequence[PanelRecord]) -> list[PanelRecord]:
    """Return training rows only; analyses of sequence content must start here."""

    return [record for record in records if record.partition.startswith("train:")]


def write_condition(records: Sequence[PanelRecord], output_dir: Path, dataset_id: str) -> dict[str, str]:
    """Write train and test CSV files plus the fold manifest the runner reads."""

    check_group_safety(records)
    train = training_records(records)
    test = [record for record in records if record.partition == "test"]
    if len(train) + len(test) != len(records):
        raise ValueError("every record must be in a training fold or in test")
    for name, rows in (("train", train), ("test", test)):
        if {record.label for record in rows} != {0, 1}:
            raise ValueError(f"{name} must contain both labels")
    if output_dir.exists():
        raise FileExistsError(f"{output_dir} exists; condition builds are immutable")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    names = {}
    try:
        for name, rows in (("train", train), ("test", test)):
            positives = sum(record.label for record in rows)
            filename = f"{dataset_id}-p-{positives}-n-{len(rows) - positives}-{name}.csv"
            names[name] = filename
            with (staging / filename).open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["record_id", "sequence", "label", "group", "negative_family"])
                writer.writerows(
                    (r.record_id, r.sequence, r.label, r.group, r.negative_family) for r in rows
                )
        # row-NNN matches read_dataset, which numbers data rows from one.
        names["fold_manifest"] = f"{dataset_id}.folds.csv"
        with (staging / names["fold_manifest"]).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["row_id", "label", "fold"])
            writer.writerows(
                (f"row-{index:09d}", record.label, int(record.partition.split(":")[1]))
                for index, record in enumerate(train, start=1)
            )
        staging.rename(output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return names
