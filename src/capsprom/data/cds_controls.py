"""RefSeq CDS eligibility and candidate windows for CDS-derived negative controls.

Implements the annotation and window rules of
``specs/cds_negative_control_protocol.md``.  Coordinates are zero-based and
half-open.  A window is 81 nt on the CDS sense strand; its frame is its offset
from the first base of the start codon modulo three.  Nothing here samples a
control; the functions enumerate every admissible window so that feasibility
can be inventoried before any construction.
"""

from __future__ import annotations

import collections
import gzip
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np

# Feature types that block a control window on either strand, besides CDS.
RNA_FEATURE_TYPES = frozenset(
    {
        "tRNA",
        "rRNA",
        "tmRNA",
        "ncRNA",
        "SRP_RNA",
        "RNase_P_RNA",
        "antisense_RNA",
        "misc_RNA",
    }
)
_EXCEPTION_KEYS = ("exception", "transl_except", "ribosomal_slippage")
_COMPLEMENT = str.maketrans("ACGT", "TGCA")


@dataclass(frozen=True)
class GffFeature:
    seqid: str
    feature_type: str
    start: int
    end: int
    strand: str
    attributes: Mapping[str, str]


@dataclass(frozen=True)
class CdsFeature:
    identifier: str
    seqid: str
    start: int
    end: int
    strand: str

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class WindowTable:
    """Every admissible control window of one replicon, one row per window."""

    genomic_start: np.ndarray
    strand: np.ndarray
    frame: np.ndarray
    gc_count: np.ndarray
    cds_index: np.ndarray

    def __len__(self) -> int:
        return len(self.genomic_start)


def read_gff(path: Path) -> list[GffFeature]:
    """Read GFF3 feature rows (plain or gzip), converting to zero-based starts."""

    opener = gzip.open if Path(path).suffix == ".gz" else open
    features = []
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9:
                raise ValueError(f"malformed GFF row: {line[:80]!r}")
            attributes = {}
            for item in fields[8].split(";"):
                if "=" in item:
                    key, value = item.split("=", 1)
                    attributes[key] = urllib.parse.unquote(value)
            features.append(
                GffFeature(fields[0], fields[2], int(fields[3]) - 1, int(fields[4]), fields[6], attributes)
            )
    return features


def eligible_cds(
    features: Sequence[GffFeature], *, min_length: int = 201
) -> tuple[list[CdsFeature], collections.Counter[str]]:
    """Return eligible CDS and the count of excluded CDS by first failing rule.

    Rules are checked in a fixed order: multi-segment, pseudo, partial,
    exception or frameshift, too short.  A CDS counts as pseudo when it carries
    ``pseudo=true`` or its parent is a pseudogene, which covers submitter
    annotations that mark only the gene.
    """

    pseudo_parents = {
        feature.attributes.get("ID")
        for feature in features
        if feature.feature_type == "pseudogene"
        or feature.attributes.get("gene_biotype") == "pseudogene"
    }
    rows: dict[str, list[GffFeature]] = collections.defaultdict(list)
    for feature in features:
        if feature.feature_type == "CDS":
            rows[feature.attributes.get("ID", f"{feature.seqid}:{feature.start}")].append(feature)
    eligible, excluded = [], collections.Counter()
    for identifier, segments in rows.items():
        first = segments[0]
        attributes = first.attributes
        note = attributes.get("Note", "").lower()
        if len(segments) > 1:
            excluded["multi_segment"] += 1
        elif attributes.get("pseudo") == "true" or attributes.get("Parent") in pseudo_parents:
            excluded["pseudo"] += 1
        elif (
            attributes.get("partial") == "true"
            or "start_range" in attributes
            or "end_range" in attributes
        ):
            excluded["partial"] += 1
        elif any(key in attributes for key in _EXCEPTION_KEYS) or "frameshift" in note:
            excluded["exception_or_frameshift"] += 1
        elif first.end - first.start < min_length:
            excluded["too_short"] += 1
        else:
            eligible.append(CdsFeature(identifier, first.seqid, first.start, first.end, first.strand))
    return eligible, excluded


def blocking_intervals(features: Iterable[GffFeature], seqid: str) -> list[tuple[int, int]]:
    """CDS rows (of any eligibility) and RNA features that a control may not touch."""

    return [
        (feature.start, feature.end)
        for feature in features
        if feature.seqid == seqid
        and (feature.feature_type == "CDS" or feature.feature_type in RNA_FEATURE_TYPES)
    ]


def enumerate_windows(
    sequence: str,
    cds: Sequence[CdsFeature],
    blocking: Sequence[tuple[int, int]],
    tss_positions: Iterable[int],
    *,
    length: int = 81,
    end_margin: int = 60,
    tss_radius: int = 100,
) -> WindowTable:
    """List every window that satisfies the position and exclusion rules.

    A window [s, s + length) is admissible inside its host CDS when it starts at
    least ``end_margin`` nt after the start-codon base and ends at least
    ``end_margin`` nt before the stop-codon base; no known TSS (either strand)
    lies in [s - tss_radius, s + length + tss_radius); no other blocking
    feature overlaps it; and it is strict DNA.  Exact-identity and selected-
    control exclusions depend on sampling and are not applied here.
    """

    sequence = sequence.upper()
    size = len(sequence)
    codes = np.frombuffer(sequence.encode("ascii"), dtype=np.uint8)
    gc = np.concatenate(([0], np.cumsum((codes == ord("G")) | (codes == ord("C")))))
    strict = np.isin(codes, np.frombuffer(b"ACGT", dtype=np.uint8))
    bad = np.concatenate(([0], np.cumsum(~strict)))
    coverage = np.zeros(size + 1, dtype=np.int32)
    for start, end in blocking:
        coverage[max(0, start)] += 1
        coverage[min(size, end)] -= 1
    covered = np.cumsum(coverage[:size])
    tss = np.zeros(size, dtype=np.int64)
    for position in tss_positions:
        if 0 <= position < size:
            tss[position] += 1
    tss_prefix = np.concatenate(([0], np.cumsum(tss)))

    columns: dict[str, list[np.ndarray]] = collections.defaultdict(list)
    for index, feature in enumerate(cds):
        # Sense offsets o run from end_margin to cds length - end_margin - length.
        last_offset = feature.length - end_margin - length
        if last_offset < end_margin:
            continue
        offsets = np.arange(end_margin, last_offset + 1)
        if feature.strand == "+":
            starts = feature.start + offsets
        else:
            starts = feature.end - length - offsets
        ends = starts + length
        # Windows lie inside the host, which covers them once; more cover is another feature.
        local = np.concatenate(([0], np.cumsum(covered[feature.start : feature.end] > 1)))
        local_starts, local_ends = starts - feature.start, ends - feature.start
        low = np.clip(starts - tss_radius, 0, size)
        high = np.clip(ends + tss_radius, 0, size)
        keep = (
            (local[local_ends] - local[local_starts] == 0)
            & (bad[ends] - bad[starts] == 0)
            & (tss_prefix[high] - tss_prefix[low] == 0)
        )
        columns["genomic_start"].append(starts[keep])
        columns["strand"].append(np.full(int(keep.sum()), feature.strand))
        columns["frame"].append(offsets[keep] % 3)
        columns["gc_count"].append((gc[ends] - gc[starts])[keep])
        columns["cds_index"].append(np.full(int(keep.sum()), index))

    def stack(name: str, dtype: object) -> np.ndarray:
        return np.concatenate(columns[name]) if columns[name] else np.array([], dtype=dtype)

    return WindowTable(
        stack("genomic_start", np.int64),
        stack("strand", "<U1"),
        stack("frame", np.int64),
        stack("gc_count", np.int64),
        stack("cds_index", np.int64),
    )


def window_sequence(sequence: str, genomic_start: int, strand: str, length: int = 81) -> str:
    """Return a window oriented on its sense strand."""

    window = sequence[genomic_start : genomic_start + length].upper()
    return window.translate(_COMPLEMENT)[::-1] if strand == "-" else window


def gc_histogram(table: WindowTable, length: int = 81) -> np.ndarray:
    """Count admissible windows by frame (rows 0-2) and GC count (columns)."""

    histogram = np.zeros((3, length + 1), dtype=np.int64)
    np.add.at(histogram, (table.frame, table.gc_count), 1)
    return histogram


def matched_candidates(histogram: np.ndarray, gc_count: int, frame: int, caliper: int = 4) -> int:
    """Windows of one frame whose GC count is within ``caliper`` bases of a positive."""

    low, high = max(0, gc_count - caliper), min(histogram.shape[1] - 1, gc_count + caliper)
    return int(histogram[frame, low : high + 1].sum())
