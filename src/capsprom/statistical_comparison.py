"""Statistical comparison primitives for the confirmatory protocol."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class PairedSeedMcc:
    """One predeclared seed comparison for two models on one test panel."""

    dataset_id: str
    dependency_cluster_id: str
    seed: int
    model_a_mcc: float
    model_b_mcc: float


@dataclass(frozen=True)
class DatasetPairedEffect:
    """Seed-aggregated paired effect for one dataset."""

    dataset_id: str
    dependency_cluster_id: str
    seed_effects: tuple[tuple[int, float], ...]
    median_effect: float


@dataclass(frozen=True)
class ClusterPairedEffect:
    """Dataset-aggregated paired effect for one dependency cluster."""

    dependency_cluster_id: str
    dataset_effects: tuple[tuple[str, float], ...]
    median_effect: float


def aggregate_paired_seed_mcc(
    records: Sequence[PairedSeedMcc], expected_seeds: Sequence[int]
) -> list[DatasetPairedEffect]:
    """Aggregate paired seed differences without treating seeds as replicates."""

    expected = tuple(int(seed) for seed in expected_seeds)
    if not expected or len(set(expected)) != len(expected):
        raise ValueError("expected_seeds must be non-empty and unique")
    grouped: dict[str, list[PairedSeedMcc]] = defaultdict(list)
    for record in records:
        if not record.dataset_id or not record.dependency_cluster_id:
            raise ValueError("dataset and dependency-cluster identifiers are required")
        if not math.isfinite(record.model_a_mcc) or not math.isfinite(record.model_b_mcc):
            raise ValueError("MCC values must be finite")
        grouped[record.dataset_id].append(record)
    if not grouped:
        raise ValueError("at least one paired seed record is required")

    output = []
    for dataset_id in sorted(grouped):
        dataset_records = grouped[dataset_id]
        clusters = {record.dependency_cluster_id for record in dataset_records}
        if len(clusters) != 1:
            raise ValueError(f"dataset {dataset_id!r} maps to multiple dependency clusters")
        by_seed: dict[int, PairedSeedMcc] = {}
        for record in dataset_records:
            if record.seed in by_seed:
                raise ValueError(f"duplicate seed {record.seed} for dataset {dataset_id!r}")
            by_seed[record.seed] = record
        if set(by_seed) != set(expected):
            missing = sorted(set(expected) - set(by_seed))
            unexpected = sorted(set(by_seed) - set(expected))
            raise ValueError(
                f"seed mismatch for dataset {dataset_id!r}: "
                f"missing={missing}, unexpected={unexpected}"
            )
        seed_effects = tuple(
            (seed, by_seed[seed].model_a_mcc - by_seed[seed].model_b_mcc)
            for seed in expected
        )
        output.append(
            DatasetPairedEffect(
                dataset_id=dataset_id,
                dependency_cluster_id=clusters.pop(),
                seed_effects=seed_effects,
                median_effect=float(np.median([effect for _, effect in seed_effects])),
            )
        )
    return output


def aggregate_dependency_clusters(
    dataset_effects: Sequence[DatasetPairedEffect],
) -> list[ClusterPairedEffect]:
    """Collapse related dataset effects before cross-dataset inference."""

    grouped: dict[str, list[DatasetPairedEffect]] = defaultdict(list)
    seen_datasets: set[str] = set()
    for effect in dataset_effects:
        if effect.dataset_id in seen_datasets:
            raise ValueError(f"duplicate dataset effect for {effect.dataset_id!r}")
        seen_datasets.add(effect.dataset_id)
        grouped[effect.dependency_cluster_id].append(effect)
    if not grouped:
        raise ValueError("at least one dataset effect is required")

    output = []
    for cluster_id in sorted(grouped):
        members = tuple(
            sorted(
                (
                    (effect.dataset_id, float(effect.median_effect))
                    for effect in grouped[cluster_id]
                ),
                key=lambda item: item[0],
            )
        )
        output.append(
            ClusterPairedEffect(
                dependency_cluster_id=cluster_id,
                dataset_effects=members,
                median_effect=float(np.median([effect for _, effect in members])),
            )
        )
    return output


def summarize_cluster_effects(
    cluster_effects: Sequence[ClusterPairedEffect], minimum_clusters: int = 10
) -> dict[str, float | int | bool | None]:
    """Summarize cluster effects and run Wilcoxon only at the declared minimum."""

    values = np.asarray([effect.median_effect for effect in cluster_effects], dtype=float)
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("cluster effects must be non-empty and finite")
    if minimum_clusters < 1:
        raise ValueError("minimum_clusters must be positive")
    result: dict[str, float | int | bool | None] = {
        "cluster_count": int(values.size),
        "median_effect": float(np.median(values)),
        "wins": int(np.sum(values > 0)),
        "ties": int(np.sum(values == 0)),
        "losses": int(np.sum(values < 0)),
        "wilcoxon_performed": False,
        "wilcoxon_statistic": None,
        "wilcoxon_two_sided_p": None,
    }
    if values.size < minimum_clusters:
        return result
    if np.all(values == 0):
        statistic, p_value = 0.0, 1.0
    else:
        from scipy.stats import wilcoxon

        test = wilcoxon(values, alternative="two-sided", zero_method="wilcox")
        statistic, p_value = float(test.statistic), float(test.pvalue)
    result.update(
        wilcoxon_performed=True,
        wilcoxon_statistic=statistic,
        wilcoxon_two_sided_p=p_value,
    )
    return result


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    """Return Holm-adjusted p-values while preserving hypothesis identifiers."""

    if not p_values:
        raise ValueError("at least one p-value is required")
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for _, value in ordered):
        raise ValueError("p-values must be finite and between zero and one")
    adjusted: dict[str, float] = {}
    running_max = 0.0
    count = len(ordered)
    for rank, (identifier, value) in enumerate(ordered):
        running_max = max(running_max, (count - rank) * value)
        adjusted[identifier] = min(1.0, running_max)
    return adjusted


def paired_stratified_bootstrap_mcc(
    labels: Sequence[int],
    predictions_a: Mapping[int, Sequence[int]],
    predictions_b: Mapping[int, Sequence[int]],
    *,
    resamples: int,
    random_seed: int,
    confidence_level: float = 0.95,
) -> dict[str, float | list[float]]:
    """Bootstrap the median paired-seed MCC effect with shared record indices."""

    from sklearn.metrics import matthews_corrcoef

    y_true = np.asarray(labels, dtype=int)
    if y_true.size == 0 or set(np.unique(y_true)) != {0, 1}:
        raise ValueError("labels must be non-empty and contain both binary classes")
    if resamples < 1 or not 0.0 < confidence_level < 1.0:
        raise ValueError("resamples and confidence_level are invalid")
    seeds = tuple(sorted(predictions_a))
    if not seeds or set(seeds) != set(predictions_b):
        raise ValueError("models must have the same non-empty seed set")
    arrays_a = {seed: np.asarray(predictions_a[seed], dtype=int) for seed in seeds}
    arrays_b = {seed: np.asarray(predictions_b[seed], dtype=int) for seed in seeds}
    for values in (*arrays_a.values(), *arrays_b.values()):
        if values.shape != y_true.shape or not set(np.unique(values)).issubset({0, 1}):
            raise ValueError("every prediction vector must be binary and match labels")

    class_indices = [np.flatnonzero(y_true == label) for label in (0, 1)]
    rng = np.random.default_rng(random_seed)
    bootstrap_effects = np.empty(resamples, dtype=float)
    for index in range(resamples):
        sampled = np.concatenate(
            [rng.choice(indices, size=len(indices), replace=True) for indices in class_indices]
        )
        seed_effects = [
            matthews_corrcoef(y_true[sampled], arrays_a[seed][sampled])
            - matthews_corrcoef(y_true[sampled], arrays_b[seed][sampled])
            for seed in seeds
        ]
        bootstrap_effects[index] = np.median(seed_effects)

    point_effects = [
        matthews_corrcoef(y_true, arrays_a[seed])
        - matthews_corrcoef(y_true, arrays_b[seed])
        for seed in seeds
    ]
    alpha = 1.0 - confidence_level
    interval = np.quantile(bootstrap_effects, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {
        "median_paired_seed_effect": float(np.median(point_effects)),
        "confidence_level": float(confidence_level),
        "bootstrap_resamples": int(resamples),
        "bootstrap_interval": [float(interval[0]), float(interval[1])],
    }
