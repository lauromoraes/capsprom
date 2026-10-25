"""Treatment helpers for source-defined downstream genomic controls."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import asdict, dataclass
import hashlib
from typing import Mapping, Sequence

from .epd_resolution import EpdCoordinate, epd_tss_zero_based, oriented_interval
from .sequences import SequenceRecord


_COMPLEMENT = str.maketrans("ACGT", "TGCA")


@dataclass(frozen=True)
class ControlExclusion:
    organism: str
    class_name: str
    input_index: int
    identifier: str
    epd_identifier: str
    sequence_sha256: str
    reason: str
    control_start: int | None = None
    control_end: int | None = None
    exact_tss_overlap: bool | None = None
    nearby_tss_count: int | None = None
    closest_tss_distance: int | None = None
    nearby_tss_identifiers: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalPositiveIdentityExclusion:
    organism: str
    class_name: str
    input_index: int
    identifier: str
    epd_identifier: str
    sequence_sha256: str
    reason: str
    external_dataset_id: str
    external_label: int
    match_orientation: str


def strand_invariant_key(sequence: str) -> str:
    reverse = sequence.translate(_COMPLEMENT)[::-1]
    return min(sequence, reverse)


def filter_controls_matching_external_positives(
    records: Sequence[SequenceRecord],
    *,
    organism: str,
    external_positive_sequences: Sequence[str],
    external_dataset_id: str,
) -> tuple[list[SequenceRecord], list[ExternalPositiveIdentityExclusion]]:
    """Remove controls with an exact/RC identity in a declared positive source."""

    external_keys = {strand_invariant_key(sequence) for sequence in external_positive_sequences}
    external_forward = set(external_positive_sequences)
    kept = []
    removed = []
    for index, record in enumerate(records):
        if strand_invariant_key(record.sequence) not in external_keys:
            kept.append(record)
            continue
        orientation = "forward" if record.sequence in external_forward else "reverse_complement"
        removed.append(
            ExternalPositiveIdentityExclusion(
                organism=organism,
                class_name="negative",
                input_index=index,
                identifier=record.identifier,
                epd_identifier=_epd_identifier(record.identifier),
                sequence_sha256=hashlib.sha256(record.sequence.encode()).hexdigest(),
                reason="external_positive_strand_invariant_identity",
                external_dataset_id=external_dataset_id,
                external_label=1,
                match_orientation=orientation,
            )
        )
    return kept, removed


def filter_strand_invariant_duplicates(
    records: Sequence[SequenceRecord], *, organism: str, class_name: str
) -> tuple[list[SequenceRecord], list[ControlExclusion]]:
    """Retain the first record for each sequence/reverse-complement identity."""

    seen: set[str] = set()
    kept = []
    removed = []
    for index, record in enumerate(records):
        key = strand_invariant_key(record.sequence)
        if key in seen:
            removed.append(
                ControlExclusion(
                    organism=organism,
                    class_name=class_name,
                    input_index=index,
                    identifier=record.identifier,
                    epd_identifier=_epd_identifier(record.identifier),
                    sequence_sha256=hashlib.sha256(record.sequence.encode()).hexdigest(),
                    reason="within_class_reverse_complement_duplicate_after_first",
                )
            )
        else:
            kept.append(record)
            seen.add(key)
    return kept, removed


def treat_strand_invariant_pair(
    positive: Sequence[SequenceRecord],
    negative: Sequence[SequenceRecord],
    *,
    organism: str,
) -> tuple[list[SequenceRecord], list[SequenceRecord], list[ControlExclusion]]:
    """Remove bilateral cross-class identities, then within-class duplicates."""

    positive_keys = {strand_invariant_key(record.sequence) for record in positive}
    negative_keys = {strand_invariant_key(record.sequence) for record in negative}
    collisions = positive_keys & negative_keys
    kept_by_class: dict[str, list[SequenceRecord]] = {}
    removed: list[ControlExclusion] = []
    for class_name, records in (("positive", positive), ("negative", negative)):
        after_collision = []
        for index, record in enumerate(records):
            if strand_invariant_key(record.sequence) not in collisions:
                after_collision.append(record)
                continue
            removed.append(
                ControlExclusion(
                    organism=organism,
                    class_name=class_name,
                    input_index=index,
                    identifier=record.identifier,
                    epd_identifier=_epd_identifier(record.identifier),
                    sequence_sha256=hashlib.sha256(record.sequence.encode()).hexdigest(),
                    reason="cross_label_reverse_complement_collision_bilateral_removal",
                )
            )
        deduplicated, duplicate_removals = filter_strand_invariant_duplicates(
            after_collision, organism=organism, class_name=class_name
        )
        kept_by_class[class_name] = deduplicated
        removed.extend(duplicate_removals)
    return kept_by_class["positive"], kept_by_class["negative"], removed


def filter_controls_near_known_tss(
    records: Sequence[SequenceRecord],
    *,
    organism: str,
    primary_coordinates: Mapping[str, EpdCoordinate],
    known_tss: Mapping[str, Sequence[tuple[int, str]]],
    relative_start: int,
    relative_end: int,
    exclusion_margin: int,
) -> tuple[list[SequenceRecord], list[ControlExclusion]]:
    """Remove controls whose interval plus margin contains any known TSS."""

    kept = []
    removed = []
    position_index = {
        chromosome: tuple(position for position, _ in entries)
        for chromosome, entries in known_tss.items()
    }
    for index, record in enumerate(records):
        epd_identifier = _epd_identifier(record.identifier)
        coordinate = primary_coordinates[epd_identifier]
        start, end = oriented_interval(coordinate, relative_start, relative_end)
        entries = known_tss.get(coordinate.chromosome, ())
        positions = position_index.get(coordinate.chromosome, ())
        left = bisect_left(positions, max(0, start - exclusion_margin))
        right = bisect_left(positions, end + exclusion_margin)
        hits = entries[left:right]
        if not hits:
            kept.append(record)
            continue
        exact = [(position, identifier) for position, identifier in hits if start <= position < end]
        distances = [_distance_to_interval(position, start, end) for position, _ in hits]
        removed.append(
            ControlExclusion(
                organism=organism,
                class_name="negative",
                input_index=index,
                identifier=record.identifier,
                epd_identifier=epd_identifier,
                sequence_sha256=hashlib.sha256(record.sequence.encode()).hexdigest(),
                reason=f"known_tss_within_{exclusion_margin}nt_control_margin",
                control_start=start,
                control_end=end,
                exact_tss_overlap=bool(exact),
                nearby_tss_count=len(hits),
                closest_tss_distance=min(distances),
                nearby_tss_identifiers=";".join(identifier for _, identifier in hits),
            )
        )
    return kept, removed


def index_known_tss(
    collections: Sequence[Mapping[str, EpdCoordinate]],
) -> dict[str, tuple[tuple[int, str], ...]]:
    """Index unique coordinate/identifier pairs from multiple EPD collections."""

    by_chromosome: dict[str, set[tuple[int, str]]] = {}
    for collection in collections:
        for identifier, coordinate in collection.items():
            by_chromosome.setdefault(coordinate.chromosome, set()).add(
                (epd_tss_zero_based(coordinate), identifier)
            )
    return {
        chromosome: tuple(sorted(entries)) for chromosome, entries in by_chromosome.items()
    }


def _epd_identifier(identifier: str) -> str:
    parts = identifier.split("|", maxsplit=1)
    if len(parts) != 2 or not parts[1]:
        raise ValueError(f"identifier lacks an EPD component: {identifier}")
    return parts[1]


def _distance_to_interval(position: int, start: int, end: int) -> int:
    if position < start:
        return start - position
    if position >= end:
        return position - end + 1
    return 0
