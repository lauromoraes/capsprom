"""Resolve released GraphPro identifiers against frozen EPD BED records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EpdCoordinate:
    collection: str
    chromosome: str
    start: int
    end: int
    identifier: str
    score: int
    strand: str


@dataclass(frozen=True)
class GraphProHeader:
    source_identifier: str
    epd_identifier: str
    embedded_label: int


def parse_graphpro_header(line: str) -> GraphProHeader:
    """Parse ``>FP000001|GENE_1 1`` without treating its label as evidence."""

    fields = line.strip().split()
    if len(fields) != 2 or not fields[0].startswith(">"):
        raise ValueError(f"invalid GraphPro header: {line!r}")
    identifiers = fields[0][1:].split("|", maxsplit=1)
    if len(identifiers) != 2 or not all(identifiers):
        raise ValueError(f"invalid GraphPro identifiers: {line!r}")
    try:
        label = int(fields[1])
    except ValueError as error:
        raise ValueError(f"invalid GraphPro embedded label: {line!r}") from error
    if label not in (0, 1):
        raise ValueError(f"invalid GraphPro embedded label: {line!r}")
    return GraphProHeader(identifiers[0], identifiers[1], label)


def load_epd_bed(path: Path, collection: str) -> dict[str, EpdCoordinate]:
    """Load a BED6 file and require one coordinate per EPD identifier."""

    records: dict[str, EpdCoordinate] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) < 6:
                raise ValueError(f"{path}:{line_number}: expected BED6")
            record = EpdCoordinate(
                collection=collection,
                chromosome=fields[0],
                start=int(fields[1]),
                end=int(fields[2]),
                identifier=fields[3],
                score=int(fields[4]),
                strand=fields[5],
            )
            if record.end <= record.start or record.strand not in ("+", "-"):
                raise ValueError(f"{path}:{line_number}: invalid coordinate or strand")
            if record.identifier in records:
                raise ValueError(f"{path}:{line_number}: duplicate identifier {record.identifier}")
            records[record.identifier] = record
    return records


def epd_tss_zero_based(coordinate: EpdCoordinate) -> int:
    """Return the TSS base encoded by an EPD 49-upstream/11-downstream BED row."""

    if coordinate.end - coordinate.start != 60:
        raise ValueError(f"expected a 60-nt EPD BED interval for {coordinate.identifier}")
    return coordinate.start + (49 if coordinate.strand == "+" else 10)


def oriented_interval(
    coordinate: EpdCoordinate, relative_start: int, relative_end: int
) -> tuple[int, int]:
    """Map a half-open transcript-oriented interval to genomic coordinates."""

    tss = epd_tss_zero_based(coordinate)
    if relative_end <= relative_start:
        raise ValueError("relative interval must be non-empty")
    if coordinate.strand == "+":
        return tss + relative_start, tss + relative_end
    return tss - relative_end + 1, tss - relative_start + 1
