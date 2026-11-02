import os
import random
from pathlib import Path

import pytest

from capsprom.data.graphpro_reconstruction import reverse_complement
from capsprom.data.homology_grouping import (
    GroupingRecord,
    SearchSettings,
    alignment_edges,
    connected_groups,
    cross_partition_edges,
    genomic_overlap_edges,
    grouping_report,
    hamming_edges,
    partition_groups,
    run_mmseqs_search,
    unit_edges,
)


def _random_dna(rng: random.Random, length: int = 81) -> str:
    return "".join(rng.choice("ACGT") for _ in range(length))


def _mutate(sequence: str, positions: list[int]) -> str:
    swap = {"A": "C", "C": "G", "G": "T", "T": "A"}
    letters = list(sequence)
    for position in positions:
        letters[position] = swap[letters[position]]
    return "".join(letters)


def _record(record_id, sequence, label=1, unit=None, contig=None, start=None):
    end = None if start is None else start + len(sequence)
    return GroupingRecord(record_id, sequence, label, unit or record_id, contig, start, end)


def test_hamming_edges_use_floor_of_twenty_percent_on_either_strand():
    rng = random.Random(1)
    base = _random_dna(rng)
    records = [
        _record("a", base),
        _record("b", _mutate(base, list(range(0, 80, 5)))),  # 16 mismatches: joined
        _record("c", _mutate(base, list(range(0, 81, 5)))),  # 17 mismatches: not joined
        _record("d", reverse_complement(_mutate(base, [3, 40]))),
        _record("e", _random_dna(rng)),
    ]

    # c-d share the substitution at 40, so they differ at 16 + 1 = 17 positions.
    assert hamming_edges(records) == {("a", "b"), ("a", "d"), ("b", "c"), ("b", "d")}


def test_genomic_overlap_joins_any_strand_and_ignores_records_without_coordinates():
    records = [
        _record("p1", "A" * 81, contig="chr", start=100),
        _record("p2", "A" * 81, contig="chr", start=180),  # overlaps p1 by one base
        _record("p3", "A" * 81, contig="chr", start=261),  # touches p2 only at its end
        _record("q1", "A" * 81, contig="plasmid", start=100),
        _record("x", "A" * 81),
    ]

    assert genomic_overlap_edges(records) == {("p1", "p2")}


def test_alignment_edges_reapply_thresholds_and_drop_self_hits(tmp_path: Path):
    hits = tmp_path / "hits.m8"
    hits.write_text(
        "a\ta\t1.000\t81\t1\t81\t1\t81\t81\t81\t1e-30\t150\n"
        "a\tb\t0.850\t70\t1\t70\t12\t81\t81\t81\t1e-20\t100\n"
        "a\tc\t0.790\t81\t1\t81\t1\t81\t81\t81\t1e-20\t90\n"
        "b\tc\t0.950\t60\t1\t60\t1\t60\t81\t81\t1e-15\t80\n"
        "c\ta\t0.900\t81\t81\t1\t1\t81\t81\t81\t1e-25\t120\n",
        encoding="utf-8",
    )

    assert alignment_edges(hits, SearchSettings()) == {("a", "b"), ("a", "c")}


def test_alignment_edges_fail_when_a_query_reaches_the_hit_cap(tmp_path: Path):
    hits = tmp_path / "hits.m8"
    hits.write_text(
        "".join(f"a\tt{i}\t0.9\t81\t1\t81\t1\t81\t81\t81\t1e-20\t90\n" for i in range(3)),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="max_seqs"):
        alignment_edges(hits, SearchSettings(max_seqs=3))


def test_groups_union_sources_and_report_mixed_labels_and_oversize():
    records = [
        _record("pos1", "A" * 81, 1, "pair1"),
        _record("neg1", "C" * 81, 0, "pair1"),
        _record("pos2", "G" * 81, 1, "pair2"),
        _record("neg2", "T" * 81, 0, "pair2"),
        _record("pos3", "AC" * 40 + "A", 1, "pair3"),
    ]
    grouping = connected_groups(
        records, {"unit": unit_edges(records), "alignment": {("neg1", "pos2")}}
    )

    report = grouping_report(records, grouping, max_component_fraction=0.20)

    assert grouping.group_of == {"pos1": 0, "neg1": 0, "pos2": 0, "neg2": 0, "pos3": 1}
    assert report["groups"] == 2
    assert report["largest_group"] == 4
    assert report["oversized"] is True
    assert report["mixed_label_groups"] == 1
    assert report["edges_by_source"] == {"unit": 2, "alignment": 1, "hamming": 0, "genomic_overlap": 0}


def test_partition_keeps_groups_whole_targets_classes_and_is_deterministic():
    rng = random.Random(7)
    records = []
    for index in range(200):
        records.append(_record(f"p{index}", _random_dna(rng), 1, f"u{index}"))
        records.append(_record(f"n{index}", _random_dna(rng), 0, f"u{index}"))
    grouping = connected_groups(
        records,
        {"unit": unit_edges(records), "alignment": {("p0", "p1"), ("p1", "n5"), ("n9", "p10")}},
    )

    first = partition_groups(records, grouping, test_fraction=0.2, seed=42, folds=5, fold_seed=42)
    second = partition_groups(records, grouping, test_fraction=0.2, seed=42, folds=5, fold_seed=42)

    assert first == second
    assert cross_partition_edges(grouping, first) == {"train_test": 0, "inner_fold": 0}
    test = [record for record in records if first[record.record_id] == "test"]
    assert sum(record.label == 1 for record in test) == 40
    assert sum(record.label == 0 for record in test) == 40
    assert {value for value in first.values() if value != "test"} == {f"train:{i}" for i in range(5)}


@pytest.mark.skipif(not os.environ.get("CAPSPROM_MMSEQS"), reason="set CAPSPROM_MMSEQS to the MMseqs2 binary")
def test_mmseqs_search_recovers_shifted_and_reverse_complement_copies(tmp_path: Path):
    rng = random.Random(3)
    genome = _random_dna(rng, 2000)
    records = [
        _record("w0", genome[100:181]),
        _record("w10", genome[110:191]),  # shifted by 10 nt: 71/81 overlap
        _record("rc", reverse_complement(genome[105:186])),
        _record("far", genome[1500:1581]),
    ]

    result = run_mmseqs_search(records, tmp_path, Path(os.environ["CAPSPROM_MMSEQS"]), SearchSettings(threads=1))
    edges = alignment_edges(Path(result["hits"]), SearchSettings())

    assert {("w0", "w10"), ("rc", "w0"), ("rc", "w10")} <= edges
    assert not any("far" in edge for edge in edges)
    assert result["binary_sha256"] and "easy-search" in result["command_line"]


def test_search_settings_load_from_the_frozen_contract():
    import yaml

    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "configs/homology_grouping_v1.yaml").read_text(encoding="utf-8"))

    settings = SearchSettings.from_config(config["search"])

    assert (settings.min_seq_id, settings.coverage, settings.kmer_size, settings.max_seqs) == (0.8, 0.8, 9, 1000)
