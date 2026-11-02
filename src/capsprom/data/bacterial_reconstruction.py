"""Reconstructed bacterial positives and GC-matched genomic controls (contract v3).

Positives are P-or-S TSSs of a verified primary table; controls are sampled
by deterministic random probes, then by an exhaustive replicon scan with
reservoir sampling, under the complete-table TSS exclusion.  A positive with
no admissible control is dropped and recorded instead of failing the build.
The probe, scan, and exclusion helpers are shared with the EPD builder.
"""

from __future__ import annotations

import hashlib
import math
import random
from bisect import insort
from dataclasses import dataclass
from typing import Mapping, Sequence

from .downstream_control import strand_invariant_key
from .epd_genomic_controls import (
    _contains_nearby_tss,
    _exhaustive_gc_matched_control,
    _gc_count,
    _overlaps_sorted,
)
from .graphpro_reconstruction import (
    ReconstructedPair,
    TssLocus,
    find_control_exclusion_violations,
)
from .homology_grouping import GroupingRecord
from .sequences import SequenceRecord, is_strict_dna

POSITIVE_CLASSES = frozenset({"primary", "secondary"})


class InMemoryGenome:
    """Random-access view of uppercase reference sequences."""

    def __init__(self, sequences: Mapping[str, str]) -> None:
        self._sequences = {name: sequence.upper() for name, sequence in sequences.items()}

    def sequence_size(self, name: str) -> int:
        return len(self._sequences[name])

    def fetch(self, name: str, start: int, end: int, *, reverse_complement: bool = False) -> str:
        sequence = self._sequences[name][start:end]
        if reverse_complement:
            return sequence.translate(str.maketrans("ACGTN", "TGCAN"))[::-1]
        return sequence


@dataclass(frozen=True)
class ControlFailure:
    locus: TssLocus
    positive_gc_count: int
    random_probes: int
    exhaustive_windows_scanned: int


def select_positive_loci(
    contig: str,
    classes: Mapping[tuple[int, str], set[str]],
    dataset: str,
    positive_classes: frozenset[str] = POSITIVE_CLASSES,
) -> list[TssLocus]:
    """Return P-or-S loci in stable source order: zero-based TSS, then strand."""

    keys = sorted(
        ((position - 1, strand) for (position, strand), names in classes.items() if names & positive_classes)
    )
    return [TssLocus(f"{dataset}:{contig}:{tss}:{strand}", contig, tss, strand) for tss, strand in keys]


def exclusion_loci(contig: str, classes: Mapping[tuple[int, str], set[str]]) -> list[TssLocus]:
    """Every TSS of the complete table, any class, as zero-based loci."""

    return [
        TssLocus(f"tss:{contig}:{position - 1}:{strand}", contig, position - 1, strand)
        for position, strand in sorted(classes)
    ]


def positive_window(genome: InMemoryGenome, locus: TssLocus, upstream: int, downstream: int) -> tuple[int, int, str] | None:
    """Return the genomic interval and oriented sequence, or None if out of bounds."""

    if locus.strand == "+":
        start, end = locus.tss - upstream, locus.tss + downstream + 1
    else:
        start, end = locus.tss - downstream, locus.tss + upstream + 1
    if start < 0 or end > genome.sequence_size(locus.contig):
        return None
    return start, end, genome.fetch(locus.contig, start, end, reverse_complement=locus.strand == "-")


def reconstruct_bacterial_controls(
    genome: InMemoryGenome,
    loci: Sequence[TssLocus],
    known_loci: Sequence[TssLocus],
    *,
    external_positive_sequences: Sequence[str] = (),
    upstream: int = 60,
    downstream: int = 20,
    exclusion_radius: int = 100,
    maximum_gc_count_difference: int = 4,
    seed: int = 20261021,
    max_attempts_per_positive: int = 100_000,
    exhaustive_chunk_size: int = 1_000_000,
) -> tuple[list[ReconstructedPair], list[ControlFailure]]:
    """Pair each strict-DNA positive with one same-contig, same-strand control.

    ``known_loci`` must contain every positive.  Controls avoid every known TSS
    by ``exclusion_radius`` on both strands, every selected control, every
    positive or external positive identity (either orientation), and differ
    from their positive by at most ``maximum_gc_count_difference`` G/C bases.
    Accepted controls are re-verified independently before returning.
    """

    known = {(locus.contig, locus.tss, locus.strand) for locus in known_loci}
    if any((locus.contig, locus.tss, locus.strand) not in known for locus in loci):
        raise ValueError("every positive must be in the known TSS set")
    positions: dict[str, list[int]] = {}
    for locus in known_loci:
        positions.setdefault(locus.contig, []).append(locus.tss)
    positions = {contig: sorted(values) for contig, values in positions.items()}
    windows = []
    for locus in loci:
        window = positive_window(genome, locus, upstream, downstream)
        if window is None or not is_strict_dna(window[2]):
            raise ValueError(f"positive {locus.identifier} has no strict-DNA window; screen first")
        windows.append((locus, window))
    forbidden = {strand_invariant_key(window[2]) for _, window in windows} | {
        strand_invariant_key(sequence.upper()) for sequence in external_positive_sequences
    }
    selected_identities: set[str] = set()
    selected_intervals: dict[str, list[tuple[int, int]]] = {}
    length = upstream + downstream + 1
    pairs: list[ReconstructedPair] = []
    failures: list[ControlFailure] = []
    for locus, (_, _, positive_sequence) in windows:
        contig = locus.contig
        candidate_count = genome.sequence_size(contig) - length + 1
        generator = random.Random(_pair_seed(seed, locus))
        offset = generator.randrange(candidate_count)
        step = generator.randrange(1, candidate_count + 1)
        while math.gcd(step, candidate_count) != 1:
            step = generator.randrange(1, candidate_count + 1)
        positive_gc = _gc_count(positive_sequence)
        rejected = dict.fromkeys(
            ("tss_overlap", "control_overlap", "invalid_dna", "sequence_identity", "gc_distance"), 0
        )
        limit = min(candidate_count, max_attempts_per_positive)
        chosen = None
        for attempt in range(1, limit + 1):
            start = (offset + (attempt - 1) * step) % candidate_count
            end = start + length
            if _contains_nearby_tss(start, end, positions.get(contig, ()), exclusion_radius):
                rejected["tss_overlap"] += 1
                continue
            if _overlaps_sorted(start, end, selected_intervals.get(contig, ())):
                rejected["control_overlap"] += 1
                continue
            sequence = genome.fetch(contig, start, end, reverse_complement=locus.strand == "-")
            if not is_strict_dna(sequence):
                rejected["invalid_dna"] += 1
                continue
            identity = strand_invariant_key(sequence)
            if identity in forbidden or identity in selected_identities:
                rejected["sequence_identity"] += 1
                continue
            if abs(positive_gc - _gc_count(sequence)) > maximum_gc_count_difference:
                rejected["gc_distance"] += 1
                continue
            chosen = (start, end, sequence, identity, attempt)
            break
        mode, scanned = "random", 0
        if chosen is None:
            fallback, scanned = _exhaustive_gc_matched_control(
                genome,
                contig,
                locus.strand,
                candidate_count,
                length,
                positive_gc,
                maximum_gc_count_difference,
                positions.get(contig, ()),
                exclusion_radius,
                selected_intervals.get(contig, ()),
                forbidden,
                selected_identities,
                random.Random(_pair_seed(seed + 1, locus)),
                rejected,
                chunk_size=exhaustive_chunk_size,
            )
            if fallback is None:
                failures.append(ControlFailure(locus, positive_gc, limit, scanned))
                continue
            start, end, sequence, _, _, identity = fallback
            chosen, mode = (start, end, sequence, identity, limit), "exhaustive_fallback"
        start, end, sequence, identity, attempts = chosen
        insort(selected_intervals.setdefault(contig, []), (start, end))
        selected_identities.add(identity)
        pairs.append(
            ReconstructedPair(
                positive=SequenceRecord(locus.identifier, positive_sequence, f"contig={contig} tss={locus.tss} strand={locus.strand}"),
                negative=SequenceRecord(
                    f"{locus.identifier}|genomic-control",
                    sequence,
                    f"contig={contig} start={start} end={end} strand={locus.strand} pair_id={locus.identifier}",
                ),
                positive_locus=locus,
                negative_start=start,
                negative_end=end,
                negative_strand=locus.strand,
                positive_gc=positive_gc / length,
                negative_gc=_gc_count(sequence) / length,
                sampling_attempts=attempts,
                rejected_tss_overlap=rejected["tss_overlap"],
                rejected_control_overlap=rejected["control_overlap"],
                rejected_invalid_dna=rejected["invalid_dna"],
                rejected_sequence_identity=rejected["sequence_identity"],
                rejected_gc_distance=rejected["gc_distance"],
                search_mode=mode,
                exhaustive_windows_scanned=scanned,
            )
        )
    violations = find_control_exclusion_violations(pairs, known_loci, exclusion_radius)
    if violations:
        raise AssertionError(f"accepted controls violate TSS exclusions: {violations[:5]}")
    return pairs, failures


def grouping_records(pairs: Sequence[ReconstructedPair], upstream: int = 60, downstream: int = 20) -> list[GroupingRecord]:
    """Positive and control records with their genomic windows; each pair is one unit."""

    records = []
    for pair in pairs:
        locus = pair.positive_locus
        if locus.strand == "+":
            start, end = locus.tss - upstream, locus.tss + downstream + 1
        else:
            start, end = locus.tss - downstream, locus.tss + upstream + 1
        records.append(GroupingRecord(pair.positive.identifier, pair.positive.sequence, 1, locus.identifier, locus.contig, start, end))
        records.append(
            GroupingRecord(pair.negative.identifier, pair.negative.sequence, 0, locus.identifier, locus.contig, pair.negative_start, pair.negative_end)
        )
    return records


def _pair_seed(seed: int, locus: TssLocus) -> int:
    material = f"{seed}:{locus.contig}:{locus.tss}:{locus.strand}"
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big")
