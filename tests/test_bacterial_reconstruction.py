import random

import pytest

from capsprom.data.bacterial_reconstruction import (
    InMemoryGenome,
    exclusion_loci,
    grouping_records,
    positive_window,
    reconstruct_bacterial_controls,
    select_positive_loci,
)
from capsprom.data.graphpro_reconstruction import TssLocus


def _genome(seed: int, length: int, alphabet: str = "ACGT") -> str:
    rng = random.Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(length))


def _gc(sequence: str) -> int:
    return sequence.count("G") + sequence.count("C")


def test_positive_selection_keeps_p_or_s_in_stable_order_with_zero_based_tss():
    classes = {
        (500, "-"): {"primary", "internal"},
        (300, "+"): {"secondary"},
        (300, "-"): {"antisense"},
        (100, "+"): {"internal"},
    }

    loci = select_positive_loci("chr", classes, "ds")
    known = exclusion_loci("chr", classes)

    assert [(locus.tss, locus.strand) for locus in loci] == [(299, "+"), (499, "-")]
    assert loci[0].identifier == "ds:chr:299:+"
    assert len(known) == 4 and {locus.tss for locus in known} == {99, 299, 499}


def test_controls_avoid_every_known_tss_keep_strand_gc_and_are_deterministic():
    sequence = _genome(1, 20_000)
    genome = InMemoryGenome({"chr": sequence})
    classes = {(position, strand): {"primary"} for position, strand in ((1_001, "+"), (5_001, "-"), (9_001, "+"))}
    classes.update({(position, "-"): {"internal"} for position in range(2_000, 20_000, 700)})
    loci = select_positive_loci("chr", classes, "ds")
    known = exclusion_loci("chr", classes)

    pairs, failures = reconstruct_bacterial_controls(genome, loci, known)
    again, _ = reconstruct_bacterial_controls(genome, loci, known)

    assert not failures
    assert [(p.negative_start, p.negative.sequence) for p in pairs] == [(p.negative_start, p.negative.sequence) for p in again]
    for pair in pairs:
        assert pair.negative_strand == pair.positive_locus.strand
        assert abs(_gc(pair.positive.sequence) - _gc(pair.negative.sequence)) <= 4
        assert all(not (pair.negative_start - 100 <= locus.tss < pair.negative_end + 100) for locus in known)
    intervals = sorted((p.negative_start, p.negative_end) for p in pairs)
    assert all(left_end <= right_start for (_, left_end), (right_start, _) in zip(intervals, intervals[1:]))


def test_exhaustive_scan_finds_a_rare_gc_match_after_random_probes_fail():
    at_rich = _genome(2, 30_000, "AT")
    gc_island = _genome(3, 81, "GC")
    sequence = at_rich[:10_000] + gc_island + at_rich[10_081:20_000] + gc_island[::-1] + at_rich[20_081:]
    genome = InMemoryGenome({"chr": sequence})
    locus = TssLocus("ds:chr:10060:+", "chr", 10_060, "+")
    other = TssLocus("decoy", "chr", 25_000, "+")

    pairs, failures = reconstruct_bacterial_controls(
        genome, [locus], [locus, other], max_attempts_per_positive=5, maximum_gc_count_difference=0
    )

    assert not failures
    assert pairs[0].search_mode == "exhaustive_fallback"
    assert pairs[0].negative_start == 20_000
    assert pairs[0].exhaustive_windows_scanned == len(sequence) - 80


def test_positive_without_admissible_control_is_recorded_not_raised():
    sequence = _genome(4, 5_000, "AT")
    sequence = sequence[:2_000] + _genome(5, 81, "GC") + sequence[2_081:]
    genome = InMemoryGenome({"chr": sequence})
    locus = TssLocus("ds:chr:2060:+", "chr", 2_060, "+")

    pairs, failures = reconstruct_bacterial_controls(genome, [locus], [locus], max_attempts_per_positive=10)

    assert pairs == []
    assert failures[0].locus == locus
    assert failures[0].positive_gc_count == 81
    assert failures[0].exhaustive_windows_scanned == 5_000 - 80


def test_external_positive_identity_blocks_the_only_matching_window():
    at_rich = _genome(6, 30_000, "AT")
    island, other_island = _genome(7, 81, "GC"), _genome(8, 81, "GC")
    sequence = at_rich[:10_000] + island + at_rich[10_081:20_000] + other_island + at_rich[20_081:]
    genome = InMemoryGenome({"chr": sequence})
    locus = TssLocus("ds:chr:10060:+", "chr", 10_060, "+")

    pairs, failures = reconstruct_bacterial_controls(
        genome,
        [locus],
        [locus],
        external_positive_sequences=[other_island],
        max_attempts_per_positive=5,
        maximum_gc_count_difference=0,
    )

    assert pairs == [] and len(failures) == 1


def test_positive_missing_from_known_set_is_refused():
    genome = InMemoryGenome({"chr": _genome(9, 2_000)})
    locus = TssLocus("ds:chr:500:+", "chr", 500, "+")

    with pytest.raises(ValueError, match="known TSS"):
        reconstruct_bacterial_controls(genome, [locus], [])


def test_grouping_records_carry_pair_unit_and_genomic_windows():
    sequence = _genome(10, 20_000)
    genome = InMemoryGenome({"chr": sequence})
    plus, minus = TssLocus("a", "chr", 3_000, "+"), TssLocus("b", "chr", 8_000, "-")
    pairs, _ = reconstruct_bacterial_controls(genome, [plus, minus], [plus, minus])

    records = grouping_records(pairs)

    assert [(r.unit, r.label, r.start, r.end) for r in records[:2]] == [
        ("a", 1, 2_940, 3_021),
        ("a", 0, pairs[0].negative_start, pairs[0].negative_end),
    ]
    assert (records[2].start, records[2].end) == (7_980, 8_061)
    assert positive_window(genome, minus, 60, 20)[2] == records[2].sequence
