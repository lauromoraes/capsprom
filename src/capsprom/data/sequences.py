"""Sequence utilities for CapsProm dataset construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DNA_ALPHABET = frozenset("ACGT")


@dataclass(frozen=True)
class SequenceRecord:
    """Minimal FASTA-like sequence record used by the data builders."""

    identifier: str
    sequence: str
    description: str = ""


def normalize_sequence(sequence: str) -> str:
    """Return an uppercase sequence with surrounding whitespace removed."""

    return sequence.strip().upper()


def is_strict_dna(sequence: str) -> bool:
    """Return true when a sequence contains only A, C, G, and T."""

    normalized = normalize_sequence(sequence)
    return bool(normalized) and set(normalized) <= DNA_ALPHABET


def invalid_symbols(sequence: str) -> set[str]:
    """Return symbols outside the strict DNA alphabet."""

    return set(normalize_sequence(sequence)) - DNA_ALPHABET


def crop_sequence(sequence: str, tss_position: int, upstream_length: int = 60, downstream_length: int = 20) -> str:
    """Crop a sequence around a zero-based transcription start site position.

    The resulting sequence spans `upstream_length` bases before the TSS, the TSS
    base itself, and `downstream_length` bases after the TSS. With the project
    defaults this yields 81 bp.
    """

    normalized = normalize_sequence(sequence)
    start = tss_position - upstream_length
    end = tss_position + downstream_length + 1
    if start < 0 or end > len(normalized):
        raise ValueError(
            f"cannot crop sequence of length {len(normalized)} with TSS={tss_position}, "
            f"upstream={upstream_length}, downstream={downstream_length}"
        )
    return normalized[start:end]


def crop_record(record: SequenceRecord, tss_position: int, upstream_length: int = 60, downstream_length: int = 20) -> SequenceRecord:
    """Return a cropped copy of a sequence record."""

    return SequenceRecord(
        identifier=record.identifier,
        sequence=crop_sequence(record.sequence, tss_position, upstream_length, downstream_length),
        description=record.description,
    )


def read_fasta(path: Path) -> list[SequenceRecord]:
    """Read a FASTA file without requiring Biopython."""

    records: list[SequenceRecord] = []
    identifier: str | None = None
    description = ""
    chunks: list[str] = []

    def flush() -> None:
        nonlocal identifier, description, chunks
        if identifier is None:
            return
        records.append(SequenceRecord(identifier, normalize_sequence("".join(chunks)), description))
        identifier = None
        description = ""
        chunks = []

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                flush()
                header = line[1:]
                parts = header.split(maxsplit=1)
                identifier = parts[0] if parts else str(len(records))
                description = parts[1] if len(parts) > 1 else ""
            else:
                chunks.append(line)
        flush()
    return records


def write_fasta(records: Iterable[SequenceRecord], path: Path, line_width: int = 80) -> None:
    """Write records to FASTA format."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            header = record.identifier if not record.description else f"{record.identifier} {record.description}"
            handle.write(f">{header}\n")
            seq = normalize_sequence(record.sequence)
            for i in range(0, len(seq), line_width):
                handle.write(seq[i : i + line_width] + "\n")


def keep_most_common_length(records: Sequence[SequenceRecord]) -> list[SequenceRecord]:
    """Keep only records whose sequence length is the most common length."""

    if not records:
        return []
    counts: dict[int, int] = {}
    for record in records:
        counts[len(record.sequence)] = counts.get(len(record.sequence), 0) + 1
    target = max(counts.items(), key=lambda item: item[1])[0]
    return [record for record in records if len(record.sequence) == target]


def normalize_to_min_length(records: Sequence[SequenceRecord], pad_symbol: str = "N") -> list[SequenceRecord]:
    """Pad or truncate records to the minimum observed sequence length."""

    if not records:
        return []
    target = min(len(record.sequence) for record in records)
    normalized: list[SequenceRecord] = []
    for record in records:
        seq = record.sequence
        if len(seq) < target:
            seq = seq + pad_symbol * (target - len(seq))
        else:
            seq = seq[:target]
        normalized.append(SequenceRecord(record.identifier, seq, record.description))
    return normalized
