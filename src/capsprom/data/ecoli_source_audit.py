"""Identity checks for the Promotech E. coli/pAA coordinate source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from Bio.Seq import Seq

from .primary_tss_audit import TssBedRow


@dataclass(frozen=True)
class PublishedPaaRow:
    """One row of Scientific Reports Supplementary Dataset S1."""

    position_1based: int
    strand: str
    locus_tag: str
    upstream_50_plus_tss: str
    source_row: int


def expected_source_window(reference: str, position_1based: int, strand: str) -> str:
    """Return the published 50-upstream-plus-TSS window in transcript orientation."""

    reference = reference.upper()
    if strand == "+":
        window = reference[position_1based - 51 : position_1based]
    elif strand == "-":
        window = str(
            Seq(reference[position_1based - 1 : position_1based + 50]).reverse_complement()
        )
    else:
        raise ValueError(f"invalid strand {strand!r}")
    if len(window) != 51:
        raise ValueError("source window crosses the linear reference boundary")
    return window


def compare_promotech_bed_to_paa_source(
    bed_rows: Iterable[TssBedRow],
    source_rows: Iterable[PublishedPaaRow],
    *,
    paa_reference: str,
    expected_paa_accession: str,
) -> list[dict[str, object]]:
    """Compare ordered Promotech BED rows with the pAA publication supplement."""

    bed = list(bed_rows)
    source = list(source_rows)
    if len(bed) != len(source):
        raise ValueError(f"row-count mismatch: BED={len(bed)}, source={len(source)}")
    ledger = []
    for bed_row, source_row in zip(bed, source, strict=True):
        coordinate_match = bed_row.start + 1 == source_row.position_1based
        strand_match = bed_row.strand == source_row.strand
        locus_match = bed_row.name == source_row.locus_tag
        sequence_match = (
            expected_source_window(
                paa_reference, source_row.position_1based, source_row.strand
            )
            == source_row.upstream_50_plus_tss.upper()
        )
        ledger.append(
            {
                "bed_source_row": bed_row.source_row,
                "published_source_row": source_row.source_row,
                "bed_contig": bed_row.contig,
                "expected_contig": expected_paa_accession,
                "bed_start_0based": bed_row.start,
                "published_position_1based": source_row.position_1based,
                "strand": bed_row.strand,
                "bed_locus_tag": bed_row.name,
                "published_locus_tag": source_row.locus_tag,
                "coordinate_match": coordinate_match,
                "strand_match": strand_match,
                "locus_match": locus_match,
                "published_sequence_matches_paa": sequence_match,
                "contig_match": bed_row.contig == expected_paa_accession,
            }
        )
    return ledger
