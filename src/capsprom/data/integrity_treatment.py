"""Traceable label-agnostic integrity treatment for released sequence pairs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Sequence

from .sequences import SequenceRecord, is_strict_dna


@dataclass(frozen=True)
class RemovedSequence:
    """One source record removed by an explicitly declared integrity rule."""

    dataset: str
    organism: str
    class_name: str
    source_index: int
    identifier: str
    description: str
    sequence_sha256: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class IntegrityTreatmentResult:
    """Filtered class records and their complete removal ledger."""

    positive: list[SequenceRecord]
    negative: list[SequenceRecord]
    removed: list[RemovedSequence]


def treat_labeled_sequences(
    positive: Sequence[SequenceRecord],
    negative: Sequence[SequenceRecord],
    *,
    dataset: str,
    organism: str,
    sequence_length: int = 81,
) -> IntegrityTreatmentResult:
    """Apply collision, duplicate, and strict-DNA rules without inferring labels."""

    collisions = {record.sequence for record in positive} & {
        record.sequence for record in negative
    }
    kept: dict[str, list[SequenceRecord]] = {"positive": [], "negative": []}
    removed: list[RemovedSequence] = []
    for class_name, records in (("positive", positive), ("negative", negative)):
        seen: set[str] = set()
        for source_index, record in enumerate(records):
            reason = None
            if record.sequence in collisions:
                reason = "cross_label_exact_collision_bilateral_removal"
            elif record.sequence in seen:
                reason = "within_class_exact_duplicate_after_first"
            elif len(record.sequence) != sequence_length:
                reason = f"sequence_length_not_{sequence_length}"
            elif not is_strict_dna(record.sequence):
                reason = "non_strict_dna"
            if reason is None:
                kept[class_name].append(record)
                seen.add(record.sequence)
            else:
                removed.append(
                    RemovedSequence(
                        dataset=dataset,
                        organism=organism,
                        class_name=class_name,
                        source_index=source_index,
                        identifier=record.identifier,
                        description=record.description,
                        sequence_sha256=hashlib.sha256(
                            record.sequence.encode("ascii")
                        ).hexdigest(),
                        reason=reason,
                    )
                )
    return IntegrityTreatmentResult(
        positive=kept["positive"], negative=kept["negative"], removed=removed
    )
