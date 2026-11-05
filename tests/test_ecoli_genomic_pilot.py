import random

import pytest

from capsprom.data.ecoli_genomic_pilot import (
    NamedTss,
    RegulonUnion,
    admissible_windows,
    blocked_violations,
    classify_support,
    cross_partition_links,
    exclusion_positions,
    forbidden_admissible_windows,
    local_offset,
    native_assignments,
    native_negative_intervals,
    nearest_gc_capacity,
    parse_cnnprom_header,
    place_all,
    read_active_positives,
    regulondb_union,
    select_nearest_gc_controls,
)
from capsprom.data.exact_mapping import reverse_complement
from capsprom.data.graphpro_reconstruction import TssLocus

CONTIG = "NC_TEST"
OFFSET = 5  # target 1-based TSS minus header coordinate


def _random(seed: int, length: int) -> list[str]:
    rng = random.Random(seed)
    return [rng.choice("ACGT") for _ in range(length)]


def _window(genome: str, tss: int, strand: str) -> str:
    if strand == "+":
        return genome[tss - 60 : tss + 21]
    return reverse_complement(genome[tss - 20 : tss + 61])


def _header(name: str, strand: str, tss: int) -> str:
    return f"ECK0__{name}__{'forward' if strand == '+' else 'reverse'}__{tss + 1 - OFFSET}"


def _union(positions, promoters=()) -> RegulonUnion:
    named = tuple(NamedTss(*p) for p in promoters)
    return RegulonUnion(frozenset(positions) | {(p.tss, p.strand) for p in named}, named, 0, {})


def _fixture():
    """Genome with the five contract situations, mirrored on synthetic data.

    - ``dup``: one window copied to a second locus; only the first is a named
      PromoterSet TSS (rrsAp2/gltIp1 type);
    - ``nearp``/``nearm``: TSS 1 nt from a union TSS on + and - (serWp/rplUp);
    - ``shift``: same-name PromoterSet TSS 18 nt upstream (araCp);
    - ``orphan``: no union support at all;
    - ``a1``..``a3``: exact single-locus anchors for the header offset.
    """

    bases = _random(7, 30_000)
    copy_from, copy_to = 12_000, 20_000
    bases[copy_to - 60 : copy_to + 21] = bases[copy_from - 60 : copy_from + 21]
    genome = "".join(bases)
    sites = {"a1": (2_000, "+"), "a2": (6_000, "-"), "a3": (16_000, "+"), "dup": (copy_from, "+"),
             "nearp": (8_000, "+"), "nearm": (10_000, "-"), "shift": (14_000, "+"), "orphan": (24_000, "-")}
    union = _union(
        {(2_000, "+"), (6_000, "-"), (16_000, "+"), (copy_to, "+"), (8_001, "+"), (10_001, "-"), (14_100, "-")},
        [("dupP", copy_from, "+"), ("shiftP", 14_000 - 18, "+")],
    )
    names = {"dup": "dupP", "shift": "shiftP"}
    positives = [(key, _header(names.get(key, key), strand, tss), _window(genome, tss, strand)) for key, (tss, strand) in sites.items()]
    return genome, union, positives


def test_header_parsing_and_rejection():
    header = parse_cnnprom_header("ECK120033629__rrsAp2__forward__4033379")
    assert (header.promoter, header.strand, header.coordinate) == ("rrsAp2", "+", 4033379)
    assert parse_cnnprom_header("ECK1__gltIp1__reverse__687119").strand == "-"
    with pytest.raises(ValueError):
        parse_cnnprom_header("ECK1__x__sideways__1")


def test_regulondb_union_drops_out_of_range_rows_and_keeps_promoterset_names():
    rows = {"HT1": [{"chromosome": CONTIG, "pos_1": 10, "strand": "+"}, {"chromosome": CONTIG, "pos_1": 101, "strand": "-"},
                    {"chromosome": "other", "pos_1": 20, "strand": "+"}, {"chromosome": CONTIG, "pos_1": None, "strand": "+"}]}
    content = "header\nID1\tfooP\treverse\t50\tsigma70\tACGT\nbad line\n"
    union = regulondb_union(rows, content, CONTIG, 100)
    assert union.positions == {(9, "+"), (49, "-")}
    assert union.out_of_range_rows == 1
    assert union.promoters == (NamedTss("fooP", 49, "-"),)
    assert union.per_source == {"HT1": 1, "PromoterSet": 1}


def test_local_offset_uses_the_nearest_anchor():
    anchors = [(100, 3), (1_000, 7)]
    assert local_offset(anchors, 120) == (3, 20)
    assert local_offset(anchors, 900) == (7, 100)
    assert local_offset(anchors, 550) == (3, 450)  # tie goes to the lower coordinate
    with pytest.raises(ValueError):
        local_offset([], 1)


def test_the_five_contract_situations_are_classified_as_declared():
    genome, union, positives = _fixture()
    placements = {p.record_id: p for p in place_all(positives, {CONTIG: genome}, union, 2, 2)}

    dup = placements["dup"]
    assert dup.all_loci == ((12_000, "+"), (20_000, "+"))
    assert (dup.status, dup.tss, dup.support_class) == ("multiple_resolved", 12_000, "exact")
    assert "qualifying=1" in dup.resolution_evidence
    assert (placements["nearp"].support_class, placements["nearp"].support_distance_nt) == ("near", 1)
    # minus strand: the union TSS at 10_001 lies upstream in transcription direction
    assert (placements["nearm"].support_class, placements["nearm"].support_distance_nt) == ("near", -1)
    shift = placements["shift"]
    assert (shift.support_class, shift.support_distance_nt, shift.support_reference) == ("shifted", -18, "promoterset_same_name")
    assert shift.in_genomic_panel and "exclude_from_positional" in shift.action
    orphan = placements["orphan"]
    assert orphan.support_class == "none" and not orphan.in_genomic_panel
    assert all(placements[key].support_class == "exact" for key in ("a1", "a2", "a3"))


def test_multiple_loci_stay_unresolved_without_name_and_header_agreement():
    genome, union, positives = _fixture()
    wrong_coordinate = [(k, h.rsplit("__", 1)[0] + "__1" if k == "dup" else h, s) for k, h, s in positives]
    wrong_name = [(k, h.replace("dupP", "otherP"), s) for k, h, s in positives]
    for variant in (wrong_coordinate, wrong_name):
        dup = {p.record_id: p for p in place_all(variant, {CONTIG: genome}, union, 2, 2)}["dup"]
        assert dup.status == "multiple_unresolved" and dup.tss is None and not dup.in_genomic_panel
        assert dup.action == "exclude_from_genomic_panel_and_count"


def test_exclusion_holds_every_locus_of_every_positive():
    genome, union, positives = _fixture()
    placements = place_all(positives, {CONTIG: genome}, union, 2, 2)
    keys = set(exclusion_positions(union, placements))
    assert union.positions <= keys
    assert {(20_000, "+"), (24_000, "-"), (8_000, "+")} <= keys


def test_native_negatives_are_placed_on_every_locus():
    genome = "".join(_random(3, 12_000))
    native = [genome[1_000:1_081], reverse_complement(genome[5_000:5_081]), "A" * 81]
    blocked, counts = native_negative_intervals(native, {CONTIG: genome})
    assert counts == {"single": 2, "multiple": 0, "unplaced": 1}
    assert blocked == {CONTIG: [(1_000, 1_081), (5_000, 5_081)]}


def _brute_admissible(genome, tss, radius, blocked, window=81):
    result = {}
    for start in range(len(genome) - window + 1):
        end, text = start + window, genome[start : start + window]
        if set(text) - set("ACGT") or any(start - radius <= t < end + radius for t in tss):
            continue
        if any(a < end and start < b for a, b in blocked):
            continue
        result.setdefault(text.count("G") + text.count("C"), []).append(start)
    return result


def test_admissible_index_equals_brute_force():
    bases = _random(11, 3_000)
    bases[700:705] = "NNNNN"
    genome = "".join(bases)
    tss, blocked = [400, 1_500, 2_950], [(2_000, 2_081), (2_500, 2_600)]
    index = admissible_windows(CONTIG, genome, tss, 100, blocked)
    expected = _brute_admissible(genome, tss, 100, blocked)
    assert {gc: list(starts) for gc, starts in index.starts_by_gc.items()} == expected
    assert index.excluded["admissible"] == sum(map(len, expected.values()))


def _pilot_genome(seed=21, length=40_000):
    genome = "".join(_random(seed, length))
    loci = [TssLocus(f"p{i}", CONTIG, tss, strand) for i, (tss, strand) in enumerate([(5_000, "+"), (15_000, "-"), (30_000, "+")])]
    return genome, loci


def test_nearest_gc_first_picks_the_minimal_distance_and_respects_the_ceiling():
    genome, loci = _pilot_genome()
    index = admissible_windows(CONTIG, genome, [locus.tss for locus in loci], 100)
    selections, failures = select_nearest_gc_controls(genome, loci, index, seed=1, maximum_gc_count_difference=4)
    assert not failures and len(selections) == 3
    for selection in selections:
        pair = selection.pair
        target = round(pair.positive_gc * 81)
        available = sorted(abs(gc - target) for gc in index.starts_by_gc)
        assert selection.gc_distance == available[0] <= 4
        assert abs(round(pair.negative_gc * 81) - target) == selection.gc_distance
        assert pair.negative_strand == pair.positive_locus.strand
        raw = genome[pair.negative_start : pair.negative_end]
        assert pair.negative.sequence == (raw if pair.negative_strand == "+" else reverse_complement(raw))
    intervals = sorted((s.pair.negative_start, s.pair.negative_end) for s in selections)
    assert all(left <= right for (_, left), (right, _) in zip(intervals, intervals[1:]))
    again, _ = select_nearest_gc_controls(genome, loci, index, seed=1, maximum_gc_count_difference=4)
    other, _ = select_nearest_gc_controls(genome, loci, index, seed=2, maximum_gc_count_difference=4)
    starts = [s.pair.negative_start for s in selections]
    assert starts == [s.pair.negative_start for s in again]
    assert starts != [s.pair.negative_start for s in other]


def test_forbidden_identities_push_selection_to_the_next_distance_or_fail():
    genome, loci = _pilot_genome()
    locus = loci[0]
    index = admissible_windows(CONTIG, genome, [locus.tss], 100)
    target = sum(base in "GC" for base in _window(genome, locus.tss, "+"))
    exact = [genome[s : s + 81] for s in index.starts_by_gc.get(target, [])]
    selections, _ = select_nearest_gc_controls(genome, [locus], index, seed=1, maximum_gc_count_difference=4, forbidden_sequences=exact)
    assert exact and selections[0].gc_distance == min(abs(gc - target) for gc in index.starts_by_gc if gc != target)
    assert selections[0].pair.rejected_sequence_identity == len(exact)
    everything = [genome[s : s + 81] for starts in index.starts_by_gc.values() for s in starts]
    chosen, failures = select_nearest_gc_controls(genome, [locus], index, seed=1, maximum_gc_count_difference=4, forbidden_sequences=everything)
    assert not chosen and failures == [locus]


def test_blocked_violations_are_detected_independently():
    genome, loci = _pilot_genome()
    index = admissible_windows(CONTIG, genome, [locus.tss for locus in loci], 100, [(0, 20_000)])
    selections, _ = select_nearest_gc_controls(genome, loci, index, seed=1, maximum_gc_count_difference=4)
    assert all(s.pair.negative_start >= 20_000 for s in selections)
    assert blocked_violations(selections, [(0, 20_000)]) == []
    assert blocked_violations(selections, [(0, 40_000)]) == [s.pair.negative.identifier for s in selections]


def test_support_classification_prefers_exact_then_near_then_shifted():
    union = _union({(100, "+"), (103, "+")}, [("x", 150, "+")])
    assert classify_support(100, "+", "x", union, 2)[:2] == ("exact", 0)
    assert classify_support(101, "+", "x", union, 2)[:2] == ("near", -1)
    assert classify_support(130, "+", "x", union, 2)[:2] == ("shifted", 20)
    assert classify_support(130, "-", "x", union, 2)[0] == "none"


def test_static_capacity_reports_nearest_distance_and_forbidden_windows():
    genome, loci = _pilot_genome()
    index = admissible_windows(CONTIG, genome, [locus.tss for locus in loci], 100)
    gcs = sorted(index.starts_by_gc)
    low, high = "A" * 81, "G" * 81
    assert nearest_gc_capacity(index, [low, high]) == {gcs[0]: 1, 81 - gcs[-1]: 1}
    start = int(index.starts_by_gc[gcs[len(gcs) // 2]][0])
    window = genome[start : start + 81]
    assert forbidden_admissible_windows(genome, index, [reverse_complement(window), "ACGT"]) == genome.count(window) + genome.count(reverse_complement(window))


def test_active_positives_read_both_layouts_and_only_the_window_length(tmp_path):
    grouped = tmp_path / "records.csv"
    grouped.write_text(f"record_id,label,sequence\na,1,{'a' * 81}\nb,0,{'C' * 81}\nc,1,{'G' * 251}\n", encoding="utf-8")
    ledger = tmp_path / "pair_ledger.csv"
    ledger.write_text(f"pair_id,positive_sequence,negative_sequence\np,{'T' * 81},{'C' * 81}\n", encoding="utf-8")
    assert read_active_positives(grouped) == {"A" * 81}
    assert read_active_positives(ledger) == {"T" * 81}


def test_native_assignment_is_one_to_one_by_label_and_sequence():
    source = [{"record_id": "s1", "label": "1", "sequence": "acgt"}, {"record_id": "s2", "label": "0", "sequence": "ACGT"}]
    grouped = [
        {"record_id": "g2", "label": "0", "sequence": "ACGT", "group": "7", "partition": "train:1"},
        {"record_id": "g1", "label": "1", "sequence": "ACGT", "group": "3", "partition": "test"},
    ]
    result = native_assignments(source, grouped)
    assert (result["s1"].record_id, result["s1"].group, result["s1"].partition) == ("g1", "3", "test")
    assert result["s2"].partition == "train:1"
    with pytest.raises(ValueError, match="differ"):
        native_assignments(source, grouped[:1])
    with pytest.raises(ValueError, match="duplicate"):
        native_assignments(source + [{"record_id": "s3", "label": "1", "sequence": "ACGT"}], grouped)


def test_cross_partition_links_flag_controls_reaching_another_fold_or_test():
    partition = {"p1": "test", "p2": "train:0", "n1": "train:1", "c1": "test", "c2": "train:0", "c3": "train:0"}
    edges = [("p1", "c1"), ("c2", "n1"), ("c3", "p2"), ("c3", "c1")]
    assert cross_partition_links(partition, ["c1", "c2", "c3"], edges) == {"c1": ["train:0"], "c2": ["train:1"], "c3": ["test"]}
    assert cross_partition_links(partition, ["c1"], [("p1", "c1")]) == {}
