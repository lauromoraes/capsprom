"""Deterministic random-access GC-matched controls for EPD TSS coordinates."""

from __future__ import annotations

from bisect import bisect_left, insort
import hashlib
import math
import random
from typing import Mapping, Protocol, Sequence

from .downstream_control import strand_invariant_key
from .epd_resolution import EpdCoordinate, epd_tss_zero_based, oriented_interval
from .graphpro_reconstruction import ReconstructedPair, TssLocus, reverse_complement
from .sequences import SequenceRecord, is_strict_dna


class RandomAccessGenome(Protocol):
    def sequence_size(self, name: str) -> int: ...

    def fetch(
        self, name: str, start: int, end: int, *, reverse_complement: bool = False
    ) -> str: ...


def reconstruct_epd_gc_matched_controls(
    genome: RandomAccessGenome,
    positive_coordinates: Sequence[EpdCoordinate],
    known_tss: Mapping[str, Sequence[tuple[int, str]]],
    *,
    external_positive_sequences: Sequence[str] = (),
    upstream: int = 60,
    downstream: int = 20,
    exclusion_margin: int = 100,
    maximum_gc_count_difference: int = 0,
    seed: int = 20261022,
    max_attempts_per_positive: int = 100_000,
    exhaustive_fallback_on_random_exhaustion: bool = False,
    exhaustive_chunk_size: int = 1_000_000,
) -> list[ReconstructedPair]:
    """Create one same-contig, same-strand genomic control for each EPD TSS."""

    if exclusion_margin < 0 or maximum_gc_count_difference < 0:
        raise ValueError("margins and GC-count tolerance must be non-negative")
    coordinates = _deduplicate_coordinates(positive_coordinates)
    positives = []
    for coordinate in coordinates:
        start, end = oriented_interval(coordinate, -upstream, downstream + 1)
        sequence = genome.fetch(
            coordinate.chromosome,
            start,
            end,
            reverse_complement=coordinate.strand == "-",
        ).upper()
        if not is_strict_dna(sequence):
            raise ValueError(f"positive window for {coordinate.identifier} is not strict DNA")
        positives.append((coordinate, sequence))

    forbidden_identities = {
        strand_invariant_key(sequence)
        for _, sequence in positives
    } | {strand_invariant_key(sequence) for sequence in external_positive_sequences}
    selected_identities: set[str] = set()
    selected_intervals: dict[str, list[tuple[int, int]]] = {}
    tss_positions = {
        chromosome: tuple(position for position, _ in entries)
        for chromosome, entries in known_tss.items()
    }
    window_length = upstream + downstream + 1
    pairs = []
    for coordinate, positive_sequence in positives:
        chromosome = coordinate.chromosome
        candidate_count = genome.sequence_size(chromosome) - window_length + 1
        if candidate_count <= 0:
            raise ValueError(f"reference {chromosome!r} is shorter than the requested window")
        generator = random.Random(_pair_seed(seed, coordinate))
        offset = generator.randrange(candidate_count)
        step = generator.randrange(1, candidate_count + 1)
        while math.gcd(step, candidate_count) != 1:
            step = generator.randrange(1, candidate_count + 1)
        positive_gc_count = _gc_count(positive_sequence)
        rejected = {
            "tss_overlap": 0,
            "control_overlap": 0,
            "invalid_dna": 0,
            "sequence_identity": 0,
            "gc_distance": 0,
        }
        chosen = None
        for attempt in range(1, min(candidate_count, max_attempts_per_positive) + 1):
            start = (offset + (attempt - 1) * step) % candidate_count
            end = start + window_length
            if _contains_nearby_tss(
                start, end, tss_positions.get(chromosome, ()), exclusion_margin
            ):
                rejected["tss_overlap"] += 1
                continue
            if _overlaps_sorted(start, end, selected_intervals.get(chromosome, ())):
                rejected["control_overlap"] += 1
                continue
            sequence = genome.fetch(
                chromosome,
                start,
                end,
                reverse_complement=coordinate.strand == "-",
            ).upper()
            if not is_strict_dna(sequence):
                rejected["invalid_dna"] += 1
                continue
            identity = strand_invariant_key(sequence)
            if identity in forbidden_identities or identity in selected_identities:
                rejected["sequence_identity"] += 1
                continue
            negative_gc_count = _gc_count(sequence)
            if abs(positive_gc_count - negative_gc_count) > maximum_gc_count_difference:
                rejected["gc_distance"] += 1
                continue
            chosen = (start, end, sequence, negative_gc_count, attempt, identity)
            break
        search_mode = "random"
        exhaustive_windows_scanned = 0
        if chosen is None and exhaustive_fallback_on_random_exhaustion:
            fallback_choice, exhaustive_windows_scanned = _exhaustive_gc_matched_control(
                genome,
                chromosome,
                coordinate.strand,
                candidate_count,
                window_length,
                positive_gc_count,
                maximum_gc_count_difference,
                tss_positions.get(chromosome, ()),
                exclusion_margin,
                selected_intervals.get(chromosome, ()),
                forbidden_identities,
                selected_identities,
                random.Random(_pair_seed(seed + 1, coordinate)),
                rejected,
                chunk_size=exhaustive_chunk_size,
            )
            if fallback_choice is not None:
                start, end, sequence, negative_gc_count, _, identity = fallback_choice
                chosen = (
                    start,
                    end,
                    sequence,
                    negative_gc_count,
                    min(candidate_count, max_attempts_per_positive),
                    identity,
                )
                search_mode = "exhaustive_fallback"
        if chosen is None:
            raise ValueError(
                f"no eligible control found for {coordinate.identifier} after "
                f"{min(candidate_count, max_attempts_per_positive)} attempts"
            )
        start, end, sequence, negative_gc_count, attempts, identity = chosen
        insort(selected_intervals.setdefault(chromosome, []), (start, end))
        selected_identities.add(identity)
        locus = TssLocus(
            coordinate.identifier,
            chromosome,
            epd_tss_zero_based(coordinate),
            coordinate.strand,
        )
        positive = SequenceRecord(
            coordinate.identifier,
            positive_sequence,
            f"contig={chromosome} tss={locus.tss} strand={coordinate.strand} pair_id={coordinate.identifier}",
        )
        negative = SequenceRecord(
            f"{coordinate.identifier}|gc-matched-control",
            sequence,
            f"contig={chromosome} start={start} end={end} strand={coordinate.strand} pair_id={coordinate.identifier}",
        )
        pairs.append(
            ReconstructedPair(
                positive=positive,
                negative=negative,
                positive_locus=locus,
                negative_start=start,
                negative_end=end,
                negative_strand=coordinate.strand,
                positive_gc=positive_gc_count / window_length,
                negative_gc=negative_gc_count / window_length,
                sampling_attempts=attempts,
                rejected_tss_overlap=rejected["tss_overlap"],
                rejected_control_overlap=rejected["control_overlap"],
                rejected_invalid_dna=rejected["invalid_dna"],
                rejected_sequence_identity=rejected["sequence_identity"],
                rejected_gc_distance=rejected["gc_distance"],
                search_mode=search_mode,
                exhaustive_windows_scanned=exhaustive_windows_scanned,
            )
        )
    return pairs


def _exhaustive_gc_matched_control(
    genome: RandomAccessGenome,
    chromosome: str,
    strand: str,
    candidate_count: int,
    window_length: int,
    positive_gc_count: int,
    maximum_gc_count_difference: int,
    tss_positions: Sequence[int],
    exclusion_margin: int,
    selected_intervals: Sequence[tuple[int, int]],
    forbidden_identities: set[str],
    selected_identities: set[str],
    generator: random.Random,
    rejected: dict[str, int],
    *,
    chunk_size: int,
) -> tuple[tuple[int, int, str, int, int, str] | None, int]:
    """Scan every genomic window and reservoir-sample eligible controls.

    This bounded-memory fallback is intended for extreme-GC positives for which
    uniform random probing is unlikely to observe any comparable window.
    """

    if chunk_size <= 0:
        raise ValueError("exhaustive chunk size must be positive")
    chosen = None
    eligible_count = 0
    scanned = 0
    valid_bases = {"A", "C", "G", "T"}
    for chunk_start in range(0, candidate_count, chunk_size):
        starts_in_chunk = min(chunk_size, candidate_count - chunk_start)
        block = genome.fetch(
            chromosome,
            chunk_start,
            chunk_start + starts_in_chunk + window_length - 1,
        ).upper()
        window = block[:window_length]
        gc_count = window.count("G") + window.count("C")
        invalid_count = sum(base not in valid_bases for base in window)
        for local_start in range(starts_in_chunk):
            start = chunk_start + local_start
            end = start + window_length
            scanned += 1
            if invalid_count:
                rejected["invalid_dna"] += 1
            elif abs(positive_gc_count - gc_count) > maximum_gc_count_difference:
                rejected["gc_distance"] += 1
            elif _contains_nearby_tss(start, end, tss_positions, exclusion_margin):
                rejected["tss_overlap"] += 1
            elif _overlaps_sorted(start, end, selected_intervals):
                rejected["control_overlap"] += 1
            else:
                sequence = block[local_start : local_start + window_length]
                if strand == "-":
                    sequence = reverse_complement(sequence)
                identity = strand_invariant_key(sequence)
                if identity in forbidden_identities or identity in selected_identities:
                    rejected["sequence_identity"] += 1
                else:
                    eligible_count += 1
                    if generator.randrange(eligible_count) == 0:
                        chosen = (start, end, sequence, gc_count, scanned, identity)
            if local_start + window_length < len(block):
                outgoing = block[local_start]
                incoming = block[local_start + window_length]
                gc_count += int(incoming in "GC") - int(outgoing in "GC")
                invalid_count += int(incoming not in valid_bases) - int(
                    outgoing not in valid_bases
                )
    return chosen, scanned


def _deduplicate_coordinates(
    coordinates: Sequence[EpdCoordinate],
) -> list[EpdCoordinate]:
    retained = []
    seen: set[tuple[str, int, str]] = set()
    for coordinate in coordinates:
        key = (coordinate.chromosome, epd_tss_zero_based(coordinate), coordinate.strand)
        if key not in seen:
            retained.append(coordinate)
            seen.add(key)
    return retained


def _pair_seed(seed: int, coordinate: EpdCoordinate) -> int:
    material = (
        f"{seed}:{coordinate.chromosome}:{epd_tss_zero_based(coordinate)}:"
        f"{coordinate.strand}:{coordinate.identifier}"
    )
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big")


def _contains_nearby_tss(
    start: int, end: int, positions: Sequence[int], margin: int
) -> bool:
    left = bisect_left(positions, max(0, start - margin))
    return left < len(positions) and positions[left] < end + margin


def _overlaps_sorted(start: int, end: int, intervals: Sequence[tuple[int, int]]) -> bool:
    insertion = bisect_left(intervals, (start, -1))
    if insertion and intervals[insertion - 1][1] > start:
        return True
    return insertion < len(intervals) and intervals[insertion][0] < end


def _gc_count(sequence: str) -> int:
    return sequence.count("G") + sequence.count("C")
