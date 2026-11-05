"""CNNProm E. coli genomic-control pilot: positive placement and TSS support.

Implements the positive policy of
``configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml``.  Positives keep their
label and window; they are placed on the target contig by exact both-strand
search, multiple loci are resolved by promoter name and header coordinate, and
TSS support is classed against the RegulonDB union.  Controls are selected
nearest GC first under a hard caliper (``select_nearest_gc_controls``), unlike
the first-accepted sampling of the v3 bacterial panels.
"""

from __future__ import annotations

import bisect
import csv
import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from .downstream_control import strand_invariant_key
from .exact_mapping import find_exact, reverse_complement
from .graphpro_reconstruction import ReconstructedPair, TssLocus
from .sequences import SequenceRecord

TSS_INDEX = 60
WINDOW = 81

ACTIONS = {
    "exact": "keep_both_panels",
    "near": "keep_both_panels_record_distance",
    "shifted": "keep_both_panels_record_distance_exclude_from_positional_analyses",
    "none": "keep_native_panel_only_exclude_from_genomic_panel_and_count",
}
GENOMIC_PANEL_CLASSES = frozenset({"exact", "near", "shifted"})


@dataclass(frozen=True)
class NamedTss:
    """One curated PromoterSet TSS, zero-based."""

    name: str
    tss: int
    strand: str


@dataclass(frozen=True)
class RegulonUnion:
    """RegulonDB TSS union on one contig: every (zero-based TSS, strand) pair."""

    positions: frozenset[tuple[int, str]]
    promoters: tuple[NamedTss, ...]
    out_of_range_rows: int
    per_source: Mapping[str, int]

    def sorted_by_strand(self) -> dict[str, list[int]]:
        result: dict[str, list[int]] = {"+": [], "-": []}
        for tss, strand in self.positions:
            result[strand].append(tss)
        return {strand: sorted(values) for strand, values in result.items()}


@dataclass(frozen=True)
class CnnpromHeader:
    promoter: str
    strand: str
    coordinate: int


@dataclass(frozen=True)
class Placement:
    """Placement, resolution, and TSS support of one positive record."""

    record_id: str
    promoter: str
    header_strand: str
    header_coordinate: int
    all_loci: tuple[tuple[int, str], ...]
    status: str
    tss: int | None
    strand: str | None
    resolution_evidence: str
    support_class: str | None
    support_distance_nt: int | None
    support_reference: str

    @property
    def in_genomic_panel(self) -> bool:
        return self.tss is not None and self.support_class in GENOMIC_PANEL_CLASSES

    @property
    def action(self) -> str:
        if self.status in {"multiple_unresolved", "unplaced"}:
            return "exclude_from_genomic_panel_and_count"
        return ACTIONS[self.support_class or "none"]


def parse_cnnprom_header(header: str) -> CnnpromHeader:
    """Parse ``ECK...__name__forward__N``; N is the 1-based TSS on NC_000913.2 (F-098)."""

    parts = header.strip().split("__")
    if len(parts) != 4 or parts[2] not in {"forward", "reverse"} or not parts[3].isdigit():
        raise ValueError(f"unexpected CNNProm positive header: {header!r}")
    return CnnpromHeader(parts[1], "+" if parts[2] == "forward" else "-", int(parts[3]))


def locus_tss(start: int, end: int, strand: str) -> int:
    """Zero-based TSS of an 81-nt window with the TSS at index 60."""

    if end - start != WINDOW:
        raise ValueError("window length differs from 81 nt")
    return start + TSS_INDEX if strand == "+" else end - TSS_INDEX - 1


def regulondb_union(
    ht_rows: Mapping[str, Iterable[Mapping[str, object]]],
    promoter_set_content: str,
    contig: str,
    length: int,
) -> RegulonUnion:
    """Union of RegulonDB HT TSS rows and the curated PromoterSet on ``contig``.

    HT rows whose ``pos_1`` lies outside ``[1, length]`` are dropped and counted,
    never wrapped (same rule as ``configs/ecoli_control_capacity_v1.yaml``).
    """

    positions: set[tuple[int, str]] = set()
    per_source: dict[str, int] = {}
    out_of_range = 0
    for dataset, rows in ht_rows.items():
        keys = set()
        for row in rows:
            position = row.get("pos_1")
            if position is None:
                continue
            if not 1 <= int(position) <= length:
                out_of_range += 1
            elif row["chromosome"] == contig:
                keys.add((int(position) - 1, str(row["strand"])))
        per_source[dataset] = len(keys)
        positions |= keys
    promoters = []
    for line in promoter_set_content.splitlines()[1:]:
        columns = line.rstrip(" ").split("\t")
        if len(columns) < 6 or not columns[3].strip().isdigit():
            continue
        strand = "+" if columns[2] == "forward" else "-"
        promoters.append(NamedTss(columns[1].strip(), int(columns[3]) - 1, strand))
    per_source["PromoterSet"] = len({(p.tss, p.strand) for p in promoters})
    positions |= {(p.tss, p.strand) for p in promoters}
    return RegulonUnion(frozenset(positions), tuple(promoters), out_of_range, per_source)


def read_regulondb_acquisition(root: Path, datasets: Sequence[str]) -> tuple[dict[str, list[dict]], str]:
    """Read the stored GraphQL pages of ``configs/regulondb_tss_acquisition_v1.yaml``."""

    rows = {}
    for dataset in datasets:
        pages = sorted((root / "ht_tss" / dataset).glob("page_*.json"))
        if not pages:
            raise FileNotFoundError(f"no pages for {dataset}")
        rows[dataset] = [row for page in pages for row in json.loads(page.read_bytes())["data"]["getAllTSSOfDataset"]]
    content = json.loads((root / "files" / "PromoterSet.json").read_bytes())["data"]["getDataOfFile"]["content"]
    return rows, content


def header_offset_anchors(placements: Iterable[Placement]) -> list[tuple[int, int]]:
    """(header coordinate, target 1-based TSS - header) of single-locus, same-strand positives."""

    anchors = {
        (p.header_coordinate, p.tss + 1 - p.header_coordinate)
        for p in placements
        if p.status == "single" and p.tss is not None and p.strand == p.header_strand
    }
    return sorted(anchors)


def local_offset(anchors: Sequence[tuple[int, int]], coordinate: int) -> tuple[int, int]:
    """Offset of the anchor nearest ``coordinate`` (ties: lower coordinate), and its distance."""

    if not anchors:
        raise ValueError("no offset anchors")
    index = bisect.bisect_left(anchors, (coordinate, -(10**12)))
    candidates = [anchors[i] for i in (index - 1, index) if 0 <= i < len(anchors)]
    anchor = min(candidates, key=lambda item: (abs(item[0] - coordinate), item[0]))
    return anchor[1], abs(anchor[0] - coordinate)


def classify_support(
    tss: int, strand: str, promoter: str, union: RegulonUnion, tolerance: int, by_strand: Mapping[str, list[int]] | None = None
) -> tuple[str, int | None, str]:
    """Class TSS support as exact, near, shifted, or none.

    The signed distance is ``reference - record`` in transcription direction, so a
    negative value places the reference TSS upstream of the record TSS.
    """

    if (tss, strand) in union.positions:
        return "exact", 0, "regulondb_union"
    by_strand = by_strand or union.sorted_by_strand()
    values = by_strand[strand]
    index = bisect.bisect_left(values, tss - tolerance)
    near = [value for value in values[index:] if value <= tss + tolerance]
    if near:
        nearest = min(near, key=lambda value: (abs(value - tss), value))
        return "near", _oriented(nearest - tss, strand), "regulondb_union"
    named = [p.tss for p in union.promoters if p.name == promoter and p.strand == strand]
    if named:
        nearest = min(named, key=lambda value: (abs(value - tss), value))
        return "shifted", _oriented(nearest - tss, strand), "promoterset_same_name"
    return "none", None, ""


def place_positive(
    record_id: str,
    header: CnnpromHeader,
    sequence: str,
    contigs: Mapping[str, str],
) -> Placement:
    """Exact both-strand placement; status ``single``, ``multiple``, or ``unplaced``."""

    loci = find_exact(sequence, contigs)
    keyed = tuple(
        sorted((locus_tss(locus.start, locus.end, locus.strand), locus.strand) for locus in loci if locus.strand in "+-")
    )
    if not keyed or len(keyed) != len(loci):
        status = "unplaced"  # no locus, or a palindromic locus without a strand
    else:
        status = "single" if len(keyed) == 1 else "multiple"
    tss, strand = keyed[0] if status == "single" else (None, None)
    return Placement(
        record_id, header.promoter, header.strand, header.coordinate, keyed, status, tss, strand, "", None, None, ""
    )


def resolve_multiple(
    placement: Placement, union: RegulonUnion, anchors: Sequence[tuple[int, int]], tolerance: int
) -> Placement:
    """Resolve a multi-locus positive by PromoterSet name and header coordinate.

    A locus qualifies when its (TSS, strand) is a PromoterSet TSS named as the
    header promoter and its 1-based TSS is within ``tolerance`` of the header
    coordinate shifted by the nearest single-locus offset anchor.  Exactly one
    qualifying locus resolves the record; otherwise it is unresolved.
    """

    named = {(p.tss, p.strand) for p in union.promoters if p.name == placement.promoter}
    offset, anchor_distance = local_offset(anchors, placement.header_coordinate)
    expected = placement.header_coordinate + offset
    qualifying = [
        (tss, strand)
        for tss, strand in placement.all_loci
        if (tss, strand) in named and strand == placement.header_strand and abs(tss + 1 - expected) <= tolerance
    ]
    evidence = (
        f"named_loci={sum(key in named for key in placement.all_loci)};offset={offset};"
        f"anchor_distance={anchor_distance};expected_tss_1based={expected};qualifying={len(qualifying)}"
    )
    if len(qualifying) == 1:
        tss, strand = qualifying[0]
        return replace(placement, status="multiple_resolved", tss=tss, strand=strand, resolution_evidence=evidence)
    return replace(placement, status="multiple_unresolved", resolution_evidence=evidence)


def place_all(
    positives: Sequence[tuple[str, str, str]],
    contigs: Mapping[str, str],
    union: RegulonUnion,
    tolerance: int,
    header_tolerance: int,
) -> list[Placement]:
    """Place, resolve, and class every ``(record_id, header, sequence)`` in order."""

    placed = [place_positive(record_id, parse_cnnprom_header(header), sequence, contigs) for record_id, header, sequence in positives]
    anchors = header_offset_anchors(placed)
    by_strand = union.sorted_by_strand()
    result = []
    for placement in placed:
        if placement.status == "multiple":
            placement = resolve_multiple(placement, union, anchors, header_tolerance)
        if placement.tss is not None and placement.strand is not None:
            support, distance, reference = classify_support(
                placement.tss, placement.strand, placement.promoter, union, tolerance, by_strand
            )
            placement = replace(placement, support_class=support, support_distance_nt=distance, support_reference=reference)
        result.append(placement)
    return result


def exclusion_positions(union: RegulonUnion, placements: Iterable[Placement]) -> list[tuple[int, str]]:
    """Union TSSs plus every locus of every positive, resolved or not."""

    keys = set(union.positions)
    for placement in placements:
        keys.update(placement.all_loci)
    return sorted(keys)


def native_negative_intervals(sequences: Iterable[str], contigs: Mapping[str, str]) -> tuple[dict[str, list[tuple[int, int]]], dict[str, int]]:
    """Every exact locus of every native negative, per contig, with locus-count tallies."""

    intervals: dict[str, set[tuple[int, int]]] = {}
    counts = {"single": 0, "multiple": 0, "unplaced": 0}
    for sequence in sequences:
        loci = find_exact(sequence, contigs)
        counts["unplaced" if not loci else "single" if len(loci) == 1 else "multiple"] += 1
        for locus in loci:
            intervals.setdefault(locus.contig, set()).add((locus.start, locus.end))
    return {contig: sorted(values) for contig, values in intervals.items()}, counts


@dataclass(frozen=True)
class AdmissibleWindows:
    """Window starts that pass every static rule, indexed by GC count.

    Static rules: strict DNA, no known TSS within ``radius`` of the window on
    either strand, and no overlap with a blocked interval.  Overlap with other
    selected controls and sequence identity are checked during selection.
    """

    contig: str
    window: int
    starts_by_gc: Mapping[int, np.ndarray]
    excluded: Mapping[str, int]


@dataclass(frozen=True)
class ControlSelection:
    pair: ReconstructedPair
    gc_distance: int
    candidates_at_distance: int


def admissible_windows(
    contig: str,
    sequence: str,
    tss_positions: Iterable[int],
    radius: int,
    blocked: Iterable[tuple[int, int]] = (),
    window: int = WINDOW,
) -> AdmissibleWindows:
    """Index admissible starts by GC count.

    A TSS ``t`` excludes a window ``[s, s + w)`` when ``s - r <= t < s + w + r``,
    the rule of ``_contains_nearby_tss``; a blocked ``[a, b)`` excludes it when
    the two intervals overlap.
    """

    data = np.frombuffer(sequence.upper().encode("ascii"), dtype=np.uint8)
    starts = len(data) - window + 1
    if starts <= 0:
        raise ValueError("contig shorter than the window")

    def window_sums(flags: np.ndarray) -> np.ndarray:
        total = np.concatenate(([0], np.cumsum(flags, dtype=np.int64)))
        return total[window:] - total[:starts]

    def covered(spans: Iterable[tuple[int, int]]) -> np.ndarray:
        delta = np.zeros(starts + 1, dtype=np.int64)
        for low, high in spans:  # inclusive range of excluded starts
            low, high = max(0, low), min(starts - 1, high)
            if low <= high:
                delta[low] += 1
                delta[high + 1] -= 1
        return np.cumsum(delta[:-1]) > 0

    gc = window_sums(np.isin(data, np.frombuffer(b"GC", np.uint8)))
    invalid = window_sums(~np.isin(data, np.frombuffer(b"ACGT", np.uint8))) > 0
    near_tss = covered((t - window - radius + 1, t + radius) for t in tss_positions)
    blocked_mask = covered((a - window + 1, b - 1) for a, b in blocked)
    ok = ~(invalid | near_tss | blocked_mask)
    by_gc = {int(value): np.flatnonzero(ok & (gc == value)) for value in np.unique(gc[ok])}
    excluded = {
        "invalid_dna": int(invalid.sum()),
        "tss_overlap": int((near_tss & ~invalid).sum()),
        "blocked_overlap": int((blocked_mask & ~invalid & ~near_tss).sum()),
        "admissible": int(ok.sum()),
    }
    return AdmissibleWindows(contig, window, by_gc, excluded)


def select_nearest_gc_controls(
    sequence: str,
    loci: Sequence[TssLocus],
    windows: AdmissibleWindows,
    *,
    seed: int,
    maximum_gc_count_difference: int,
    forbidden_sequences: Iterable[str] = (),
    upstream: int = 60,
    downstream: int = 20,
) -> tuple[list[ControlSelection], list[TssLocus]]:
    """One same-strand control per positive, nearest GC count first.

    For each positive, in the given order, admissible windows are tried at GC
    distance 0, 1, ... up to the ceiling; within one distance they are tried in
    a permutation seeded by ``seed`` and the positive locus.  A window is
    accepted unless it overlaps an already selected control or its
    strand-invariant identity equals a positive, a forbidden sequence, or a
    selected control.  A positive with no acceptable window is a failure.
    """

    sequence = sequence.upper()
    length = upstream + downstream + 1
    if length != windows.window:
        raise ValueError("window length differs from the admissible index")
    positives = []
    for locus in loci:
        if locus.contig != windows.contig:
            raise ValueError(f"{locus.identifier} is not on {windows.contig}")
        start = locus.tss - upstream if locus.strand == "+" else locus.tss - downstream
        raw = sequence[start : start + length]
        positives.append((locus, raw if locus.strand == "+" else reverse_complement(raw)))
    forbidden = {strand_invariant_key(s) for _, s in positives} | {strand_invariant_key(s.upper()) for s in forbidden_sequences}
    selected: list[tuple[int, int]] = []
    chosen: list[ControlSelection] = []
    failures: list[TssLocus] = []
    empty = np.array([], dtype=np.int64)
    for locus, positive in positives:
        target = positive.count("G") + positive.count("C")
        rng = np.random.default_rng(_pair_seed(seed, locus))
        rejected = {"control_overlap": 0, "sequence_identity": 0}
        examined, found = 0, None
        for distance in range(maximum_gc_count_difference + 1):
            values = sorted({target - distance, target + distance})
            candidates = np.sort(np.concatenate([windows.starts_by_gc.get(v, empty) for v in values]))
            for index in rng.permutation(len(candidates)):
                start = int(candidates[index])
                examined += 1
                if _overlaps(selected, start, start + length):
                    rejected["control_overlap"] += 1
                    continue
                raw = sequence[start : start + length]
                control = raw if locus.strand == "+" else reverse_complement(raw)
                identity = strand_invariant_key(control)
                if identity in forbidden:
                    rejected["sequence_identity"] += 1
                    continue
                found = (start, control, identity, distance, len(candidates))
                break
            if found:
                break
        if found is None:
            failures.append(locus)
            continue
        start, control, identity, distance, pool = found
        bisect.insort(selected, (start, start + length))
        forbidden.add(identity)
        pair = ReconstructedPair(
            positive=SequenceRecord(locus.identifier, positive, f"contig={locus.contig} tss={locus.tss} strand={locus.strand}"),
            negative=SequenceRecord(
                f"{locus.identifier}|genomic-control",
                control,
                f"contig={locus.contig} start={start} end={start + length} strand={locus.strand} pair_id={locus.identifier}",
            ),
            positive_locus=locus,
            negative_start=start,
            negative_end=start + length,
            negative_strand=locus.strand,
            positive_gc=target / length,
            negative_gc=(control.count("G") + control.count("C")) / length,
            sampling_attempts=examined,
            rejected_tss_overlap=0,
            rejected_control_overlap=rejected["control_overlap"],
            rejected_invalid_dna=0,
            rejected_sequence_identity=rejected["sequence_identity"],
            rejected_gc_distance=0,
            search_mode="nearest_gc_first",
        )
        chosen.append(ControlSelection(pair, distance, pool))
    return chosen, failures


def blocked_violations(selections: Iterable[ControlSelection], blocked: Sequence[tuple[int, int]]) -> list[str]:
    """Independently list controls that overlap a blocked interval."""

    ordered = sorted(blocked)
    return [s.pair.negative.identifier for s in selections if _overlaps(ordered, s.pair.negative_start, s.pair.negative_end)]


def nearest_gc_capacity(windows: AdmissibleWindows, sequences: Iterable[str]) -> dict[int, int]:
    """Count positives by the smallest GC count distance any admissible window offers.

    A static check: it ignores competition between positives and identity rejection.
    """

    available = np.array(sorted(windows.starts_by_gc), dtype=np.int64)
    counts: dict[int, int] = {}
    for sequence in sequences:
        target = sequence.count("G") + sequence.count("C")
        distance = int(np.abs(available - target).min()) if len(available) else -1
        counts[distance] = counts.get(distance, 0) + 1
    return dict(sorted(counts.items()))


def forbidden_admissible_windows(sequence: str, windows: AdmissibleWindows, forbidden: Iterable[str]) -> int:
    """Number of admissible windows whose strand-invariant identity is forbidden."""

    sequence = sequence.upper()
    keys = {s.upper() for s in forbidden if len(s) == windows.window}
    keys |= {reverse_complement(s) for s in keys}
    return sum(
        sequence[start : start + windows.window] in keys for starts in windows.starts_by_gc.values() for start in starts.tolist()
    )


def read_active_positives(path: Path, window: int = WINDOW) -> set[str]:
    """Positive sequences of one active dataset file that can equal a ``window``-nt control.

    Grouped dataset tables carry ``label`` and ``sequence``; reconstructed pair
    ledgers carry ``positive_sequence``.
    """

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if "positive_sequence" in (reader.fieldnames or ()):
            values = (row["positive_sequence"] for row in reader)
        else:
            values = (row["sequence"] for row in reader if int(row["label"]) == 1)
        return {s.strip().upper() for s in values if len(s.strip()) == window}


@dataclass(frozen=True)
class NativeAssignment:
    record_id: str
    group: str
    partition: str


def native_assignments(source_rows: Sequence[Mapping[str, str]], grouped_rows: Sequence[Mapping[str, str]]) -> dict[str, NativeAssignment]:
    """Map each source record to its grouped-build record by (label, sequence), one to one.

    Raises ``ValueError`` unless every source record matches exactly one grouped
    record and every grouped record is matched.
    """

    def keyed(rows, name):
        result = {}
        for row in rows:
            key = (str(row["label"]), row["sequence"].strip().upper())
            if key in result:
                raise ValueError(f"duplicate (label, sequence) in the {name} records")
            result[key] = row
        return result

    source, grouped = keyed(source_rows, "source"), keyed(grouped_rows, "grouped")
    if source.keys() != grouped.keys():
        raise ValueError(
            f"source and grouped records differ: {len(source.keys() - grouped.keys())} source-only, "
            f"{len(grouped.keys() - source.keys())} grouped-only"
        )
    return {
        row["record_id"]: NativeAssignment(grouped[key]["record_id"], grouped[key]["group"], grouped[key]["partition"])
        for key, row in source.items()
    }


def cross_partition_links(partition: Mapping[str, str], controls: Iterable[str], edges: Iterable[tuple[str, str]]) -> dict[str, list[str]]:
    """Controls with an edge to a record of another partition, with the partitions reached.

    ``partition`` covers native records and controls; a control carries its
    positive's partition.
    """

    neighbours: dict[str, set[str]] = {}
    for left, right in edges:
        neighbours.setdefault(left, set()).add(right)
        neighbours.setdefault(right, set()).add(left)
    links = {}
    for control in controls:
        reached = sorted({partition[n] for n in neighbours.get(control, ())} - {partition[control]})
        if reached:
            links[control] = reached
    return links


def _overlaps(intervals: Sequence[tuple[int, int]], start: int, end: int) -> bool:
    index = bisect.bisect_left(intervals, (start, -1))
    if index and intervals[index - 1][1] > start:
        return True
    return index < len(intervals) and intervals[index][0] < end


def _pair_seed(seed: int, locus: TssLocus) -> int:
    material = f"{seed}:{locus.contig}:{locus.tss}:{locus.strand}"
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big")


def _oriented(delta: int, strand: str) -> int:
    return delta if strand == "+" else -delta
