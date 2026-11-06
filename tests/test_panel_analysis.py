import numpy as np

from capsprom.eda import panel_analysis as pa


def test_kmer_frequencies_sum_to_one_and_count_correctly() -> None:
    frequencies = pa.kmer_frequencies(pa.encode(["AAAC"]), 2)
    names = pa.kmer_names(2)
    assert frequencies.sum() == 1
    assert frequencies[0, names.index("AA")] == 2 / 3
    assert frequencies[0, names.index("AC")] == 1 / 3


def test_composition_features() -> None:
    codes = pa.encode(["GGGC", "ACGT"])
    assert np.allclose(pa.gc_fraction(codes), [1.0, 0.5])
    assert np.allclose(pa.gc_skew(codes), [0.5, 0.0])
    assert np.allclose(pa.shannon_entropy(pa.encode(["ACGT", "AAAA"])), [2.0, 0.0])


def test_periodicity_scores_a_period_three_sequence_above_a_period_two_one() -> None:
    codes = pa.encode(["ACG" * 27, "AC" * 40 + "A"])
    scores = pa.periodicity_3(codes)
    assert scores[0] > 0 > scores[1]


def test_total_variation_is_one_for_disjoint_positions() -> None:
    first = pa.position_frequencies(pa.encode(["A", "A"]))
    second = pa.position_frequencies(pa.encode(["C", "C"]))
    assert pa.total_variation(first, second)[0] == 1


def test_relative_entropy_is_zero_at_background() -> None:
    background = np.full(4, 0.25)
    assert pa.relative_entropy_to_background(background[None, :], background)[0] == 0


def test_standardized_mean_difference_handles_constant_columns() -> None:
    first = np.array([[1.0, 2.0], [3.0, 2.0]])
    second = np.array([[0.0, 2.0], [2.0, 2.0]])
    assert np.allclose(pa.standardized_mean_difference(first, second), [1 / np.sqrt(2), 0])


def test_best_motif_mismatches_scans_the_declared_span() -> None:
    codes = pa.encode(["CCCTATAATCCC", "CCCCCCCCCCCC"])
    assert list(pa.best_motif_mismatches(codes, "TATAAT", 0, 11)) == [0, 6]
    assert pa.best_motif_mismatches(codes, "TATAAT", 6, 11)[0] > 0


def test_nearest_identity_sees_the_reverse_strand_and_can_skip_self() -> None:
    sequences = ["AAAACCCC", "GGGGTTTT", "ACACACAC"]
    codes = pa.encode(sequences)
    identity = pa.nearest_identity(codes, codes, exclude_self=True)
    assert identity[0] == 1 and identity[1] == 1 and identity[2] < 1


def test_same_group_fraction_detects_separated_groups() -> None:
    points = np.concatenate([np.zeros((5, 2)) + np.arange(5)[:, None] * 0.01, np.ones((5, 2)) * 10])
    groups = np.array(["a"] * 5 + ["b"] * 5)
    assert pa.same_group_neighbor_fraction(points, groups, 2) == 1


def test_neighbor_overlap_is_one_for_identical_spaces() -> None:
    points = np.random.default_rng(1).normal(size=(20, 3))
    assert pa.neighbor_overlap(points, points, 3) == 1
