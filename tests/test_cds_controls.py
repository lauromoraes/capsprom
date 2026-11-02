import gzip
from pathlib import Path

import numpy as np

from capsprom.data.cds_controls import (
    CdsFeature,
    blocking_intervals,
    eligible_cds,
    enumerate_windows,
    gc_histogram,
    matched_candidates,
    read_gff,
    window_sequence,
)


def _gff_row(seqid, kind, start, end, strand, attributes):
    return "\t".join([seqid, "RefSeq", kind, str(start), str(end), ".", strand, "0", attributes])


def _write_gff(path: Path, rows: list[str]) -> Path:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("##gff-version 3\n" + "\n".join(rows) + "\n")
    return path


def test_eligibility_excludes_each_rule_in_order(tmp_path: Path):
    rows = [
        _gff_row("c", "CDS", 1, 300, "+", "ID=cds-ok"),
        _gff_row("c", "CDS", 1, 150, "+", "ID=cds-join"),
        _gff_row("c", "CDS", 200, 400, "+", "ID=cds-join"),
        _gff_row("c", "CDS", 1, 300, "+", "ID=cds-pseudo;pseudo=true"),
        _gff_row("c", "pseudogene", 1, 300, "+", "ID=gene-p"),
        _gff_row("c", "CDS", 1, 300, "+", "ID=cds-parent;Parent=gene-p"),
        _gff_row("c", "CDS", 1, 300, "+", "ID=cds-partial;partial=true;start_range=.,1"),
        _gff_row("c", "CDS", 1, 300, "+", "ID=cds-slip;exception=ribosomal slippage"),
        _gff_row("c", "CDS", 1, 300, "+", "ID=cds-note;Note=contains a frameshift%3B sequenced twice"),
        _gff_row("c", "CDS", 1, 200, "+", "ID=cds-short"),
    ]
    features = read_gff(_write_gff(tmp_path / "a.gff.gz", rows))

    eligible, excluded = eligible_cds(features)

    assert [cds.identifier for cds in eligible] == ["cds-ok"]
    assert eligible[0].start == 0 and eligible[0].end == 300
    assert excluded == {
        "multi_segment": 1,
        "pseudo": 2,
        "partial": 1,
        "exception_or_frameshift": 2,
        "too_short": 1,
    }


def test_windows_respect_margins_and_frame_on_both_strands():
    sequence = "".join("ACGT"[i % 4] for i in range(1000))
    plus = CdsFeature("p", "c", 100, 400, "+")
    minus = CdsFeature("m", "c", 500, 800, "-")

    table = enumerate_windows(sequence, [plus, minus], [(100, 400), (500, 800)], [])

    plus_starts = table.genomic_start[table.strand == "+"]
    assert plus_starts.min() == 160 and plus_starts.max() + 81 == 340
    assert list(table.frame[table.strand == "+"][:4]) == [0, 1, 2, 0]
    minus_rows = np.flatnonzero(table.strand == "-")
    # Sense offset 60 on the minus strand ends 60 nt before the CDS end.
    assert table.genomic_start[minus_rows[0]] == 800 - 60 - 81
    assert table.frame[minus_rows[0]] == 0
    assert len(table) == 2 * (300 - 120 - 81 + 1)


def test_windows_exclude_tss_neighbourhood_other_features_and_ambiguous_bases():
    sequence = "A" * 1000
    host = CdsFeature("h", "c", 0, 1000, "+")
    tss = 500
    neighbour = (700, 720)
    sequence = sequence[:900] + "N" + sequence[901:]

    table = enumerate_windows(sequence, [host], [(0, 1000), neighbour], [tss])

    starts = table.genomic_start
    ends = starts + 81
    assert not np.any((starts - 100 <= tss) & (tss < ends + 100))
    assert not np.any((starts < neighbour[1]) & (neighbour[0] < ends))
    assert not np.any((starts <= 900) & (900 < ends))
    assert 60 in starts and 500 - 100 - 81 in starts and 500 - 100 - 80 not in starts


def test_window_sequence_orients_minus_strand_and_gc_histogram_matches():
    sequence = "AAAACCCCGGGGTTTT" * 30
    cds = CdsFeature("m", "c", 0, len(sequence), "-")
    table = enumerate_windows(sequence, [cds], [(0, len(sequence))], [])

    first = window_sequence(sequence, int(table.genomic_start[0]), "-")
    histogram = gc_histogram(table)

    assert first == window_sequence(sequence, int(table.genomic_start[0]), "+").translate(
        str.maketrans("ACGT", "TGCA")
    )[::-1]
    assert first.count("G") + first.count("C") == table.gc_count[0]
    assert histogram.sum() == len(table)
    assert matched_candidates(histogram, int(table.gc_count[0]), int(table.frame[0]), caliper=0) >= 1


def test_blocking_intervals_keep_cds_and_rna_but_not_genes(tmp_path: Path):
    rows = [
        _gff_row("c", "gene", 1, 300, "+", "ID=gene-1"),
        _gff_row("c", "CDS", 1, 300, "+", "ID=cds-1;pseudo=true"),
        _gff_row("c", "tRNA", 400, 470, "-", "ID=rna-1"),
        _gff_row("d", "rRNA", 1, 100, "+", "ID=rna-2"),
    ]
    features = read_gff(_write_gff(tmp_path / "b.gff.gz", rows))

    assert blocking_intervals(features, "c") == [(0, 300), (399, 470)]
