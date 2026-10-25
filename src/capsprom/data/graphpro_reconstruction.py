"""Auditing and reconstruction primitives for the released GraphPro datasets.

The released class labels are never interpreted as verified biology here.  The
audit describes them, while reconstruction creates a distinct dataset from
independently supplied reference sequences and transcription start sites.
"""

from __future__ import annotations

import hashlib
import math
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .sequences import SequenceRecord, is_strict_dna, normalize_sequence, read_fasta

_STRAND_PATTERN = re.compile(r"\(([+-])\)\s*$")
_EPD_PATTERN = re.compile(r"^FP\d+\|")


@dataclass(frozen=True)
class GraphProClassAudit:
    """Descriptive evidence for one released GraphPro class file."""

    path: str
    records: int
    plus_strand_records: int
    minus_strand_records: int
    epd_identifier_records: int
    header_label_zero_records: int
    header_label_one_records: int
    unique_sequences: int


@dataclass(frozen=True)
class GraphProDatasetAudit:
    """Audit of a released positive/negative file pair."""

    folder: str
    positive: GraphProClassAudit
    negative: GraphProClassAudit
    exact_cross_label_sequences: int
    exact_cross_label_full_records: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TssLocus:
    """An independently verified, zero-based TSS on a reference contig."""

    identifier: str
    contig: str
    tss: int
    strand: str

    def __post_init__(self) -> None:
        if self.tss < 0:
            raise ValueError("TSS must be zero-based and non-negative")
        if self.strand not in {"+", "-"}:
            raise ValueError("strand must be '+' or '-'")


@dataclass(frozen=True)
class ReconstructedPair:
    """A promoter and its independently sampled genomic control."""

    positive: SequenceRecord
    negative: SequenceRecord
    positive_locus: TssLocus
    negative_start: int
    negative_end: int
    negative_strand: str
    positive_gc: float
    negative_gc: float
    sampling_attempts: int
    rejected_tss_overlap: int
    rejected_control_overlap: int
    rejected_invalid_dna: int
    rejected_sequence_identity: int
    rejected_gc_distance: int
    search_mode: str = "random"
    exhaustive_windows_scanned: int = 0


@dataclass(frozen=True)
class RejectedTssLocus:
    """A source TSS that cannot produce the configured strict-DNA window."""

    locus: TssLocus
    reason: str


@dataclass(frozen=True)
class PromotechSourceAudit:
    """Integrity and coordinate-convention audit for one Promotech source."""

    source_key: str
    accession: str
    reference_length: int
    reference_sha256: str
    tss_sha256: str
    tss_records: int
    plus_tss_records: int
    minus_tss_records: int
    duplicate_tss_records: int
    invalid_point_features: int
    contig_mismatches: int
    out_of_bounds_tss: int
    processed_positive_records: int
    processed_positive_bed_sha256: str
    processed_positive_fasta_sha256: str
    processed_sequence_mismatches: int
    processed_coordinate_mismatches: int

    @property
    def passed(self) -> bool:
        return not any(
            (
                self.invalid_point_features,
                self.contig_mismatches,
                self.out_of_bounds_tss,
                self.processed_sequence_mismatches,
                self.processed_coordinate_mismatches,
            )
        )


@dataclass(frozen=True)
class PairFilterResult:
    """Post-generation integrity result that preserves positive-control pairing."""

    pairs: list[ReconstructedPair]
    cross_label_pairs_removed: int
    positive_duplicate_pairs_removed: int
    negative_duplicate_pairs_removed: int


def audit_graphpro_pair(folder: Path) -> GraphProDatasetAudit:
    """Describe a released GraphPro pair without endorsing either label."""

    positive_records = read_fasta(folder / "positive")
    negative_records = read_fasta(folder / "negative")
    positive_full = {(r.identifier, r.description, r.sequence) for r in positive_records}
    negative_full = {(r.identifier, r.description, r.sequence) for r in negative_records}
    return GraphProDatasetAudit(
        folder=folder.name,
        positive=_audit_class(folder / "positive", positive_records),
        negative=_audit_class(folder / "negative", negative_records),
        exact_cross_label_sequences=len(
            {r.sequence for r in positive_records} & {r.sequence for r in negative_records}
        ),
        exact_cross_label_full_records=len(positive_full & negative_full),
    )


def audit_promotech_source(
    *,
    source_key: str,
    reference_fasta: Path,
    tss_bed: Path,
    processed_positive_bed: Path,
    processed_positive_fasta: Path,
) -> PromotechSourceAudit:
    """Verify source hashes, BED point semantics, and strand-aware extraction."""

    references = read_fasta(reference_fasta)
    if len(references) != 1:
        raise ValueError(f"{reference_fasta} must contain exactly one reference sequence")
    reference = references[0]
    raw_tss = _read_bed6(tss_bed)
    point_tss = [(contig, start, strand) for contig, start, end, _, strand in raw_tss if end - start == 1]
    unique_tss = set(point_tss)
    processed_bed = _read_bed6(processed_positive_bed)
    processed_fasta = read_fasta(processed_positive_fasta)
    sequence_mismatches = abs(len(processed_bed) - len(processed_fasta))
    coordinate_mismatches = 0
    expected_intervals = {
        (contig, max(0, start - 39), min(len(reference.sequence), start + 1), "+")
        if strand == "+"
        else (contig, max(0, start), min(len(reference.sequence), start + 40), "-")
        for contig, start, strand in unique_tss
    }
    for index, (contig, start, end, _, strand) in enumerate(processed_bed):
        if (contig, start, end, strand) not in expected_intervals:
            coordinate_mismatches += 1
        if index >= len(processed_fasta) or contig != reference.identifier or start < 0 or end > len(reference.sequence):
            sequence_mismatches += 1
            continue
        sequence = reference.sequence[start:end]
        if strand == "-":
            sequence = _reverse_complement_iupac(sequence)
        if processed_fasta[index].sequence != sequence:
            sequence_mismatches += 1
    return PromotechSourceAudit(
        source_key=source_key,
        accession=reference.identifier,
        reference_length=len(reference.sequence),
        reference_sha256=_sha256_file(reference_fasta),
        tss_sha256=_sha256_file(tss_bed),
        tss_records=len(raw_tss),
        plus_tss_records=sum(row[4] == "+" for row in raw_tss),
        minus_tss_records=sum(row[4] == "-" for row in raw_tss),
        duplicate_tss_records=len(point_tss) - len(unique_tss),
        invalid_point_features=sum(row[2] - row[1] != 1 for row in raw_tss),
        contig_mismatches=sum(row[0] != reference.identifier for row in raw_tss),
        out_of_bounds_tss=sum(row[1] < 0 or row[2] > len(reference.sequence) for row in raw_tss),
        processed_positive_records=len(processed_fasta),
        processed_positive_bed_sha256=_sha256_file(processed_positive_bed),
        processed_positive_fasta_sha256=_sha256_file(processed_positive_fasta),
        processed_sequence_mismatches=sequence_mismatches,
        processed_coordinate_mismatches=coordinate_mismatches,
    )


def reconstruct_genomic_controls(
    references: Mapping[str, str],
    loci: Sequence[TssLocus],
    *,
    upstream: int = 60,
    downstream: int = 20,
    exclusion_radius: int = 100,
    gc_tolerance: float = 0.05,
    seed: int = 20261021,
    max_attempts_per_locus: int = 100_000,
    exclusion_loci: Sequence[TssLocus] | None = None,
) -> list[ReconstructedPair]:
    """Build TSS windows and deterministic, GC-matched genomic controls.

    Each control has the same length and strand as its paired positive.  Its
    genomic interval cannot overlap any known TSS exclusion interval or an
    already selected control, and its oriented sequence cannot equal any
    positive or previously selected control.  Coordinates are zero-based,
    half-open in the returned metadata.
    """

    if exclusion_radius < 0 or not 0 <= gc_tolerance <= 1:
        raise ValueError("invalid exclusion radius or GC tolerance")
    normalized = {name: normalize_sequence(sequence) for name, sequence in references.items()}
    positives = [(locus, _extract_tss_window(normalized, locus, upstream, downstream)) for locus in loci]
    for locus, positive in positives:
        if not is_strict_dna(positive.sequence):
            raise ValueError(f"positive window for {locus.identifier} is not strict DNA")
    positive_sequences = {record.sequence for _, record in positives}
    forbidden_sequences = positive_sequences | {
        reverse_complement(sequence) for sequence in positive_sequences
    }
    forbidden = _tss_exclusions(exclusion_loci if exclusion_loci is not None else loci, exclusion_radius)
    selected_intervals: dict[str, list[tuple[int, int]]] = {}
    selected_sequences: set[str] = set()
    results: list[ReconstructedPair] = []
    window_length = upstream + downstream + 1

    for locus, positive in positives:
        reference = normalized[locus.contig]
        if len(reference) < window_length:
            raise ValueError(f"reference {locus.contig!r} is shorter than the requested window")
        pair_seed = int.from_bytes(
            hashlib.sha256(f"{seed}:{locus.identifier}".encode("utf-8")).digest()[:8], "big"
        )
        generator = random.Random(pair_seed)
        candidate_count = len(reference) - window_length + 1
        offset = generator.randrange(candidate_count)
        step = generator.randrange(1, candidate_count + 1)
        while math.gcd(step, candidate_count) != 1:
            step = generator.randrange(1, candidate_count + 1)
        positive_gc = _gc_fraction(positive.sequence)
        chosen: tuple[int, SequenceRecord, float, int] | None = None
        rejection_counts = {
            "tss_overlap": 0,
            "control_overlap": 0,
            "invalid_dna": 0,
            "sequence_identity": 0,
            "gc_distance": 0,
        }
        attempt_limit = min(candidate_count, max_attempts_per_locus)
        for attempt in range(1, attempt_limit + 1):
            start = (offset + (attempt - 1) * step) % candidate_count
            end = start + window_length
            if _overlaps_any(start, end, forbidden.get(locus.contig, ())):
                rejection_counts["tss_overlap"] += 1
                continue
            if _overlaps_any(start, end, selected_intervals.get(locus.contig, ())):
                rejection_counts["control_overlap"] += 1
                continue
            sequence = reference[start:end]
            if not is_strict_dna(sequence):
                rejection_counts["invalid_dna"] += 1
                continue
            if locus.strand == "-":
                sequence = reverse_complement(sequence)
            if sequence in forbidden_sequences or sequence in selected_sequences:
                rejection_counts["sequence_identity"] += 1
                continue
            negative_gc = _gc_fraction(sequence)
            if abs(positive_gc - negative_gc) > gc_tolerance:
                rejection_counts["gc_distance"] += 1
                continue
            identifier = f"{locus.identifier}|genomic-control"
            description = (
                f"contig={locus.contig} start={start} end={end} strand={locus.strand} "
                f"paired_positive={locus.identifier}"
            )
            chosen = (start, SequenceRecord(identifier, sequence, description), negative_gc, attempt)
            break
        if chosen is None:
            raise ValueError(
                f"no eligible control found for {locus.identifier} after "
                f"{attempt_limit} attempts"
            )
        start, negative, negative_gc, attempts = chosen
        end = start + window_length
        selected_intervals.setdefault(locus.contig, []).append((start, end))
        selected_sequences.update(
            {negative.sequence, reverse_complement(negative.sequence)}
        )
        results.append(
            ReconstructedPair(
                positive=positive,
                negative=negative,
                positive_locus=locus,
                negative_start=start,
                negative_end=end,
                negative_strand=locus.strand,
                positive_gc=positive_gc,
                negative_gc=negative_gc,
                sampling_attempts=attempts,
                rejected_tss_overlap=rejection_counts["tss_overlap"],
                rejected_control_overlap=rejection_counts["control_overlap"],
                rejected_invalid_dna=rejection_counts["invalid_dna"],
                rejected_sequence_identity=rejection_counts["sequence_identity"],
                rejected_gc_distance=rejection_counts["gc_distance"],
            )
        )
    return results


def filter_reconstructed_pairs(pairs: Sequence[ReconstructedPair]) -> PairFilterResult:
    """Remove collisions bilaterally, then retain one pair per class identity.

    Sequence identity is strand-invariant: a sequence and its reverse complement
    share one canonical identity. Removing a record always removes its paired
    control or positive so that class balance and group membership are retained.
    """

    positive_identities = {_canonical_dna_identity(pair.positive.sequence) for pair in pairs}
    negative_identities = {_canonical_dna_identity(pair.negative.sequence) for pair in pairs}
    collisions = positive_identities & negative_identities
    collision_filtered = [
        pair
        for pair in pairs
        if _canonical_dna_identity(pair.positive.sequence) not in collisions
        and _canonical_dna_identity(pair.negative.sequence) not in collisions
    ]
    seen_positive: set[str] = set()
    seen_negative: set[str] = set()
    retained: list[ReconstructedPair] = []
    positive_duplicates = 0
    negative_duplicates = 0
    for pair in collision_filtered:
        positive_identity = _canonical_dna_identity(pair.positive.sequence)
        negative_identity = _canonical_dna_identity(pair.negative.sequence)
        if positive_identity in seen_positive:
            positive_duplicates += 1
            continue
        if negative_identity in seen_negative:
            negative_duplicates += 1
            continue
        seen_positive.add(positive_identity)
        seen_negative.add(negative_identity)
        retained.append(pair)
    return PairFilterResult(
        pairs=retained,
        cross_label_pairs_removed=len(pairs) - len(collision_filtered),
        positive_duplicate_pairs_removed=positive_duplicates,
        negative_duplicate_pairs_removed=negative_duplicates,
    )


def read_bed_tss(path: Path) -> list[TssLocus]:
    """Read BED6 point features as independently sourced TSS loci."""

    loci: list[TssLocus] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 6:
            raise ValueError(f"{path}:{line_number}: expected BED6")
        contig, start_text, end_text, name, _, strand = fields[:6]
        start, end = int(start_text), int(end_text)
        if end - start != 1:
            raise ValueError(f"{path}:{line_number}: TSS BED feature must have length one")
        identifier = name if name and name != "." else f"{contig}:{start}:{strand}"
        loci.append(TssLocus(identifier, contig, start, strand))
    return loci


def deduplicate_tss_loci(loci: Sequence[TssLocus]) -> list[TssLocus]:
    """Keep one biological group per contig, coordinate, and strand."""

    unique: list[TssLocus] = []
    seen: set[tuple[str, int, str]] = set()
    for locus in loci:
        identity = (locus.contig, locus.tss, locus.strand)
        if identity not in seen:
            seen.add(identity)
            unique.append(locus)
    return unique


def screen_tss_loci(
    references: Mapping[str, str],
    loci: Sequence[TssLocus],
    *,
    upstream: int = 60,
    downstream: int = 20,
) -> tuple[list[TssLocus], list[RejectedTssLocus]]:
    """Separate reconstructable TSS loci while preserving rejection reasons."""

    normalized = {name: normalize_sequence(sequence) for name, sequence in references.items()}
    eligible: list[TssLocus] = []
    rejected: list[RejectedTssLocus] = []
    for locus in loci:
        if locus.contig not in normalized:
            rejected.append(RejectedTssLocus(locus, "missing_reference_contig"))
            continue
        try:
            record = _extract_tss_window(normalized, locus, upstream, downstream)
        except ValueError:
            rejected.append(RejectedTssLocus(locus, "window_out_of_reference_bounds"))
            continue
        if not is_strict_dna(record.sequence):
            rejected.append(RejectedTssLocus(locus, "window_contains_ambiguous_dna"))
            continue
        eligible.append(locus)
    return eligible, rejected


def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of a strict DNA sequence."""

    normalized = normalize_sequence(sequence)
    if set(normalized) - set("ACGT"):
        raise ValueError("reverse complement requires strict DNA")
    return normalized.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def _audit_class(path: Path, records: Iterable[SequenceRecord]) -> GraphProClassAudit:
    materialized = list(records)
    strands = [_header_strand(record.description) for record in materialized]
    labels = [record.description.rsplit(maxsplit=1)[-1] if record.description else "" for record in materialized]
    return GraphProClassAudit(
        path=str(path),
        records=len(materialized),
        plus_strand_records=strands.count("+"),
        minus_strand_records=strands.count("-"),
        epd_identifier_records=sum(bool(_EPD_PATTERN.match(record.identifier)) for record in materialized),
        header_label_zero_records=labels.count("0"),
        header_label_one_records=labels.count("1"),
        unique_sequences=len({record.sequence for record in materialized}),
    )


def _header_strand(description: str) -> str | None:
    match = _STRAND_PATTERN.search(description)
    return match.group(1) if match else None


def _extract_tss_window(
    references: Mapping[str, str], locus: TssLocus, upstream: int, downstream: int
) -> SequenceRecord:
    if locus.contig not in references:
        raise ValueError(f"missing reference contig {locus.contig!r}")
    reference = references[locus.contig]
    if locus.strand == "+":
        start, end = locus.tss - upstream, locus.tss + downstream + 1
    else:
        start, end = locus.tss - downstream, locus.tss + upstream + 1
    if start < 0 or end > len(reference):
        raise ValueError(f"TSS window for {locus.identifier} exceeds reference bounds")
    sequence = reference[start:end]
    if locus.strand == "-":
        sequence = reverse_complement(sequence)
    description = (
        f"contig={locus.contig} tss={locus.tss} strand={locus.strand} "
        f"upstream={upstream} downstream={downstream}"
    )
    return SequenceRecord(locus.identifier, sequence, description)


def _tss_exclusions(
    loci: Sequence[TssLocus], radius: int
) -> dict[str, list[tuple[int, int]]]:
    exclusions: dict[str, list[tuple[int, int]]] = {}
    for locus in loci:
        exclusions.setdefault(locus.contig, []).append(
            (max(0, locus.tss - radius), locus.tss + radius + 1)
        )
    return exclusions


def _overlaps_any(start: int, end: int, intervals: Iterable[tuple[int, int]]) -> bool:
    return any(start < other_end and other_start < end for other_start, other_end in intervals)


def _gc_fraction(sequence: str) -> float:
    return (sequence.count("G") + sequence.count("C")) / len(sequence)


def _canonical_dna_identity(sequence: str) -> str:
    normalized = normalize_sequence(sequence)
    reverse = reverse_complement(normalized)
    return min(normalized, reverse)


def _reverse_complement_iupac(sequence: str) -> str:
    """Reverse-complement common IUPAC DNA symbols for source verification."""

    translation = str.maketrans("ACGTRYSWKMBDHVN", "TGCAYRSWMKVHDBN")
    return normalize_sequence(sequence).translate(translation)[::-1]


def _read_bed6(path: Path) -> list[tuple[str, int, int, str, str]]:
    records: list[tuple[str, int, int, str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 6:
            raise ValueError(f"{path}:{line_number}: expected BED6")
        records.append((fields[0], int(fields[1]), int(fields[2]), fields[3], fields[5]))
    return records


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
