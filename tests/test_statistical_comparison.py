import numpy as np
import pytest

from capsprom.statistical_comparison import (
    PairedSeedMcc,
    aggregate_dependency_clusters,
    aggregate_paired_seed_mcc,
    holm_adjust,
    paired_stratified_bootstrap_mcc,
    summarize_cluster_effects,
)


SEEDS = (13, 29, 42, 71, 101, 137, 173, 211, 251, 293)


def _records(dataset: str, cluster: str, effect: float) -> list[PairedSeedMcc]:
    return [
        PairedSeedMcc(dataset, cluster, seed, 0.5 + effect, 0.5) for seed in SEEDS
    ]


def test_seed_then_cluster_aggregation_prevents_pseudoreplication() -> None:
    records = _records("related-a", "shared", 0.2)
    records += _records("related-b", "shared", 0.4)
    records += sum(
        (_records(f"independent-{index}", f"cluster-{index}", 0.1) for index in range(9)),
        [],
    )

    datasets = aggregate_paired_seed_mcc(records, SEEDS)
    clusters = aggregate_dependency_clusters(datasets)
    summary = summarize_cluster_effects(clusters)

    assert len(datasets) == 11
    assert len(clusters) == 10
    shared = next(item for item in clusters if item.dependency_cluster_id == "shared")
    assert shared.median_effect == pytest.approx(0.3)
    assert summary["cluster_count"] == 10
    assert summary["wilcoxon_performed"] is True
    assert summary["wins"] == 10


def test_seed_aggregation_rejects_incomplete_or_duplicate_pairs() -> None:
    with pytest.raises(ValueError, match="seed mismatch"):
        aggregate_paired_seed_mcc(_records("dataset", "cluster", 0.1)[:-1], SEEDS)

    duplicate = _records("dataset", "cluster", 0.1)
    duplicate.append(duplicate[0])
    with pytest.raises(ValueError, match="duplicate seed"):
        aggregate_paired_seed_mcc(duplicate, SEEDS)


def test_wilcoxon_is_not_run_below_minimum_cluster_count() -> None:
    datasets = aggregate_paired_seed_mcc(_records("dataset", "cluster", 0.1), SEEDS)
    summary = summarize_cluster_effects(aggregate_dependency_clusters(datasets))

    assert summary["cluster_count"] == 1
    assert summary["wilcoxon_performed"] is False
    assert summary["wilcoxon_two_sided_p"] is None


def test_paired_bootstrap_is_reproducible_and_uses_seed_aggregated_effect() -> None:
    labels = [0, 0, 0, 0, 1, 1, 1, 1]
    predictions_a = {
        13: [0, 0, 0, 1, 1, 1, 1, 1],
        29: [0, 0, 0, 0, 0, 1, 1, 1],
    }
    predictions_b = {
        13: [0, 1, 1, 1, 1, 1, 1, 1],
        29: [0, 0, 1, 1, 0, 0, 1, 1],
    }

    first = paired_stratified_bootstrap_mcc(
        labels, predictions_a, predictions_b, resamples=50, random_seed=20260715
    )
    second = paired_stratified_bootstrap_mcc(
        labels, predictions_a, predictions_b, resamples=50, random_seed=20260715
    )

    assert first == second
    assert first["median_paired_seed_effect"] > 0
    assert first["bootstrap_resamples"] == 50


def test_holm_adjustment_is_monotone_in_sorted_p_values() -> None:
    adjusted = holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03})

    assert adjusted == pytest.approx({"a": 0.03, "b": 0.06, "c": 0.06})


def _clustered_panel():
    # 20 groups of 10 identical records: errors are perfectly correlated within a group.
    rng = np.random.default_rng(7)
    labels, a, b, groups = [], [], [], []
    for group in range(20):
        label = group % 2
        hit_a = rng.random() < 0.8
        hit_b = rng.random() < 0.6
        for _ in range(10):
            labels.append(label)
            a.append(label if hit_a else 1 - label)
            b.append(label if hit_b else 1 - label)
            groups.append(f"g{group}")
    return labels, {13: a}, {13: b}, groups


def test_group_bootstrap_widens_the_interval_when_errors_cluster() -> None:
    labels, a, b, groups = _clustered_panel()

    record = paired_stratified_bootstrap_mcc(labels, a, b, resamples=2000, random_seed=20260715)
    grouped = paired_stratified_bootstrap_mcc(labels, a, b, resamples=2000, random_seed=20260715, groups=groups)

    def width(result):
        return result["bootstrap_interval"][1] - result["bootstrap_interval"][0]

    assert record["bootstrap_unit"] == "record_within_class"
    assert grouped["bootstrap_unit"] == "group"
    assert grouped["median_paired_seed_effect"] == record["median_paired_seed_effect"]
    assert width(grouped) > 2 * width(record)


def test_group_bootstrap_with_singleton_groups_is_reproducible_and_valid() -> None:
    labels = [0, 0, 0, 0, 1, 1, 1, 1]
    a = {13: [0, 0, 0, 1, 1, 1, 1, 1], 29: [0, 0, 0, 0, 0, 1, 1, 1]}
    b = {13: [0, 1, 1, 1, 1, 1, 1, 1], 29: [0, 0, 1, 1, 0, 0, 1, 1]}
    groups = list(range(8))

    first = paired_stratified_bootstrap_mcc(labels, a, b, resamples=200, random_seed=1, groups=groups)
    second = paired_stratified_bootstrap_mcc(labels, a, b, resamples=200, random_seed=1, groups=groups)

    assert first == second
    low, high = first["bootstrap_interval"]
    assert -2.0 <= low <= high <= 2.0


def test_group_bootstrap_rejects_mismatched_group_vector() -> None:
    with pytest.raises(ValueError, match="one identifier per record"):
        paired_stratified_bootstrap_mcc([0, 1], {13: [0, 1]}, {13: [0, 1]}, resamples=5, random_seed=1, groups=["g"])
