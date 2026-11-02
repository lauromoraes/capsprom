from pathlib import Path
from dataclasses import replace

import pytest

from capsprom.data.graphpro_reconstruction import (
    TssLocus,
    audit_promotech_source,
    deduplicate_tss_loci,
    filter_reconstructed_pairs,
    find_control_exclusion_violations,
    audit_graphpro_pair,
    reconstruct_genomic_controls,
    read_bed_tss,
    reverse_complement,
    screen_tss_loci,
)
from capsprom.data.sequences import SequenceRecord, write_fasta


def test_graphpro_audit_does_not_treat_epd_file_name_as_verified_label(tmp_path: Path):
    folder = tmp_path / "human"
    folder.mkdir()
    sequence = "ACGT" * 20 + "A"
    write_fasta([SequenceRecord("FP000001|GENE_1", sequence, "1")], folder / "positive")
    write_fasta(
        [
            SequenceRecord("FP000002|GENE_2", "C" * 81, "0"),
            SequenceRecord("FP000001|GENE_1", sequence, "1"),
        ],
        folder / "negative",
    )

    audit = audit_graphpro_pair(folder)

    assert audit.positive.epd_identifier_records == 1
    assert audit.negative.epd_identifier_records == 2
    assert audit.negative.header_label_zero_records == 1
    assert audit.exact_cross_label_sequences == 1
    assert audit.exact_cross_label_full_records == 1


def test_reconstruction_is_deterministic_strand_matched_and_excludes_tss_regions():
    reference = ("ACGT" * 150) + ("GGCC" * 150)
    loci = [
        TssLocus("plus", "chr", 150, "+"),
        TssLocus("minus", "chr", 950, "-"),
    ]
    kwargs = {
        "upstream": 6,
        "downstream": 2,
        "exclusion_radius": 20,
        "gc_tolerance": 0.6,
        "seed": 7,
    }

    first = reconstruct_genomic_controls({"chr": reference}, loci, exclusion_loci=loci, **kwargs)
    second = reconstruct_genomic_controls({"chr": reference}, loci, exclusion_loci=loci, **kwargs)

    assert first == second
    assert [pair.negative_strand for pair in first] == ["+", "-"]
    assert all(len(pair.positive.sequence) == 9 for pair in first)
    assert all(len(pair.negative.sequence) == 9 for pair in first)
    assert len({pair.negative.sequence for pair in first}) == 2
    for pair in first:
        for locus in loci:
            assert not (
                pair.negative_start < locus.tss + 21
                and locus.tss - 20 < pair.negative_end
            )


def test_minus_strand_tss_window_is_oriented_five_prime_to_three_prime():
    reference = "A" * 20 + "ACCGTTGCA" + "T" * 20
    locus = TssLocus("minus", "chr", 24, "-")
    pair = reconstruct_genomic_controls(
        {"chr": reference + "CG" * 100},
        [locus],
        upstream=2,
        downstream=1,
        exclusion_radius=5,
        gc_tolerance=1.0,
        seed=1,
        exclusion_loci=[locus],
    )[0]
    genomic = (reference + "CG" * 100)[23:27]
    assert pair.positive.sequence == reverse_complement(genomic)


def test_reconstruction_fails_when_no_independent_control_exists():
    only = TssLocus("only", "chr", 15, "+")
    with pytest.raises(ValueError, match="no eligible control"):
        reconstruct_genomic_controls(
            {"chr": "A" * 30},
            [only],
            upstream=2,
            downstream=2,
            exclusion_radius=30,
            gc_tolerance=1.0,
            seed=1,
            exclusion_loci=[only],
        )


def test_controls_resample_away_from_every_known_tss_class_and_strand():
    import random

    rng = random.Random(5)
    reference = "".join(rng.choice("ACGT") for _ in range(2000))
    primary = [TssLocus("P1", "chr", 300, "+"), TssLocus("P2", "chr", 1500, "-")]
    # Non-positive TSSs tile the genome except a free gap at 1701..1899.
    others = [
        TssLocus(f"{kind}{position}", "chr", position, strand)
        for position in range(0, 2000, 30)
        if not 1700 < position < 1900
        for kind, strand in (("internal", "+"), ("antisense", "-"))
    ]
    exclusion = primary + others

    pairs = reconstruct_genomic_controls(
        {"chr": reference},
        primary,
        upstream=6,
        downstream=2,
        exclusion_radius=20,
        gc_tolerance=1.0,
        seed=11,
        exclusion_loci=exclusion,
    )

    assert find_control_exclusion_violations(pairs, exclusion, 20) == []
    assert sum(pair.rejected_tss_overlap for pair in pairs) > 0
    assert all(1701 <= pair.negative_start and pair.negative_end <= 1900 for pair in pairs)


def test_violation_check_reports_control_inside_a_non_positive_tss_margin():
    primary = TssLocus("P1", "chr", 50, "+")
    pair = reconstruct_genomic_controls(
        {"chr": "ACGT" * 100},
        [primary],
        upstream=2,
        downstream=1,
        exclusion_radius=5,
        gc_tolerance=1.0,
        seed=2,
        exclusion_loci=[primary],
    )[0]
    hidden = TssLocus("orphan", "chr", pair.negative_start + 1, "-")

    assert find_control_exclusion_violations([pair], [primary, hidden], 5) == [
        (pair.negative.identifier, "orphan")
    ]


def test_reconstruction_rejects_exclusion_set_missing_a_positive():
    with pytest.raises(ValueError, match="missing from exclusion_loci"):
        reconstruct_genomic_controls(
            {"chr": "ACGT" * 100},
            [TssLocus("P1", "chr", 50, "+")],
            upstream=2,
            downstream=1,
            exclusion_loci=[],
        )


def test_bed_tss_parser_preserves_zero_based_coordinate_and_strand(tmp_path: Path):
    path = tmp_path / "source.bed"
    path.write_text("chr1\t10\t11\tTSS-1\t0\t-\n", encoding="utf-8")

    assert read_bed_tss(path) == [TssLocus("TSS-1", "chr1", 10, "-")]


def test_tss_deduplication_uses_coordinate_and_strand_as_biological_identity():
    loci = [
        TssLocus("first", "chr", 10, "+"),
        TssLocus("replicate", "chr", 10, "+"),
        TssLocus("opposite-strand", "chr", 10, "-"),
    ]

    assert deduplicate_tss_loci(loci) == [loci[0], loci[2]]


def test_tss_screen_records_bounds_and_ambiguous_dna_rejections():
    references = {"chr": "A" * 20 + "NN" + "C" * 20}
    loci = [
        TssLocus("bounds", "chr", 1, "+"),
        TssLocus("ambiguous", "chr", 21, "+"),
        TssLocus("eligible", "chr", 35, "+"),
    ]

    eligible, rejected = screen_tss_loci(references, loci, upstream=2, downstream=1)

    assert eligible == [loci[2]]
    assert [(item.locus.identifier, item.reason) for item in rejected] == [
        ("bounds", "window_out_of_reference_bounds"),
        ("ambiguous", "window_contains_ambiguous_dna"),
    ]


def test_promotech_source_audit_verifies_bed_coordinate_convention(tmp_path: Path):
    reference = tmp_path / "source.fasta"
    tss = tmp_path / "source.bed"
    positive_bed = tmp_path / "positive.bed"
    positive_fasta = tmp_path / "positive.fasta"
    sequence = "ACGT" * 30
    write_fasta([SequenceRecord("chr", sequence)], reference)
    tss.write_text("chr\t50\t51\tplus\t0\t+\nchr\t70\t71\tminus\t0\t-\n", encoding="utf-8")
    positive_bed.write_text(
        "chr\t11\t51\tplus\t0\t+\nchr\t70\t110\tminus\t0\t-\n", encoding="utf-8"
    )
    write_fasta(
        [
            SequenceRecord("plus", sequence[11:51]),
            SequenceRecord("minus", reverse_complement(sequence[70:110])),
        ],
        positive_fasta,
    )

    audit = audit_promotech_source(
        source_key="fixture",
        reference_fasta=reference,
        tss_bed=tss,
        processed_positive_bed=positive_bed,
        processed_positive_fasta=positive_fasta,
    )

    assert audit.passed
    assert audit.tss_records == 2
    assert audit.plus_tss_records == 1
    assert audit.minus_tss_records == 1
    assert audit.processed_positive_records == 2


def test_pair_filter_removes_whole_pair_for_strand_invariant_duplicates():
    pair = reconstruct_genomic_controls(
        {"chr": "A" * 50 + "ACGT" * 100 + "C" * 50},
        [TssLocus("first", "chr", 100, "+")],
        upstream=2,
        downstream=1,
        exclusion_radius=5,
        gc_tolerance=1.0,
        seed=3,
        exclusion_loci=[TssLocus("first", "chr", 100, "+")],
    )[0]
    duplicate = replace(
        pair,
        positive_locus=TssLocus("duplicate", "chr", 104, "+"),
        negative=SequenceRecord("other-negative", "GGGA"),
    )

    result = filter_reconstructed_pairs([pair, duplicate])

    assert len(result.pairs) == 1
    assert result.positive_duplicate_pairs_removed == 1
    assert result.negative_duplicate_pairs_removed == 0
    assert result.cross_label_pairs_removed == 0
