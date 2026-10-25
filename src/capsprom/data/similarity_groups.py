"""Strand-invariant near-duplicate grouping for paired DNA datasets."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import hashlib
from typing import Sequence

from .graphpro_reconstruction import reverse_complement
from .near_duplicate_audit import hamming_distance


@dataclass(frozen=True)
class SimilarityThresholdAudit:
    """Connected-component summary at one Hamming-distance threshold."""

    threshold: int
    neighbor_edges: int
    same_label_edges: int
    cross_label_edges: int
    pairs_with_neighbor: int
    component_count: int
    multi_pair_component_count: int
    largest_component_pairs: int
    singleton_pair_count: int


@dataclass(frozen=True)
class PairSimilarityAudit:
    """Near-duplicate structure for positive-control pairs."""

    pair_count: int
    sequence_count: int
    sequence_length: int
    candidate_comparisons: int
    thresholds: tuple[SimilarityThresholdAudit, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "pair_count": self.pair_count,
            "sequence_count": self.sequence_count,
            "sequence_length": self.sequence_length,
            "candidate_comparisons": self.candidate_comparisons,
            "thresholds": [asdict(item) for item in self.thresholds],
        }


@dataclass(frozen=True)
class CrossPartitionThresholdAudit:
    """Direct train--test neighbor counts at one distance threshold."""

    threshold: int
    neighbor_edges: int
    same_label_edges: int
    cross_label_edges: int
    train_sequences_with_neighbor: int
    test_sequences_with_neighbor: int


def audit_cross_partition_similarity(
    train: Sequence[tuple[str, int]],
    test: Sequence[tuple[str, int]],
    thresholds: tuple[int, ...] = (0, 1, 2, 4, 8),
) -> tuple[CrossPartitionThresholdAudit, ...]:
    """Independently audit strand-invariant train--test Hamming neighbors."""

    if not train or not test:
        raise ValueError("both train and test sequences are required")
    if not thresholds or thresholds != tuple(sorted(set(thresholds))):
        raise ValueError("thresholds must be non-empty, unique, and sorted")
    lengths = {len(sequence) for sequence, _ in (*train, *test)}
    if len(lengths) != 1:
        raise ValueError("all sequences must have one common length")
    sequence_length = lengths.pop()
    max_distance = thresholds[-1]
    if max_distance >= sequence_length:
        raise ValueError("maximum distance must be smaller than sequence length")

    bounds = _blocks(sequence_length, max_distance)
    index: dict[tuple[int, str], list[int]] = defaultdict(list)
    for train_index, (sequence, _) in enumerate(train):
        for oriented in {sequence, reverse_complement(sequence)}:
            for block_index, (start, end) in enumerate(bounds):
                index[(block_index, oriented[start:end])].append(train_index)

    edges: list[tuple[int, int, int, int, int]] = []
    for test_index, (sequence, test_label) in enumerate(test):
        candidates: set[int] = set()
        for oriented in {sequence, reverse_complement(sequence)}:
            for block_index, (start, end) in enumerate(bounds):
                candidates.update(index.get((block_index, oriented[start:end]), ()))
        for train_index in candidates:
            train_sequence, train_label = train[train_index]
            distance = min(
                hamming_distance(sequence, train_sequence),
                hamming_distance(sequence, reverse_complement(train_sequence)),
            )
            if distance <= max_distance:
                edges.append(
                    (train_index, test_index, train_label, test_label, distance)
                )

    audits = []
    for threshold in thresholds:
        selected = [edge for edge in edges if edge[4] <= threshold]
        audits.append(
            CrossPartitionThresholdAudit(
                threshold=threshold,
                neighbor_edges=len(selected),
                same_label_edges=sum(
                    train_label == test_label
                    for _, _, train_label, test_label, _ in selected
                ),
                cross_label_edges=sum(
                    train_label != test_label
                    for _, _, train_label, test_label, _ in selected
                ),
                train_sequences_with_neighbor=len({edge[0] for edge in selected}),
                test_sequences_with_neighbor=len({edge[1] for edge in selected}),
            )
        )
    return tuple(audits)


def audit_paired_sequence_similarity(
    pairs: Sequence[tuple[str, str]],
    thresholds: tuple[int, ...] = (1, 2, 4, 8),
) -> PairSimilarityAudit:
    """Audit strand-invariant Hamming neighbors and pair components exactly."""

    if not pairs:
        raise ValueError("at least one pair is required")
    if not thresholds or thresholds != tuple(sorted(set(thresholds))):
        raise ValueError("thresholds must be non-empty, unique, and sorted")
    lengths = {len(sequence) for pair in pairs for sequence in pair}
    if len(lengths) != 1:
        raise ValueError("all sequences must have one common length")
    sequence_length = lengths.pop()
    max_distance = thresholds[-1]
    if max_distance >= sequence_length:
        raise ValueError("maximum distance must be smaller than sequence length")

    bounds = _blocks(sequence_length, max_distance)
    sequences = [
        (pair_index, label, sequence)
        for pair_index, pair in enumerate(pairs)
        for label, sequence in enumerate(pair)
    ]
    index: dict[tuple[int, str], list[int]] = defaultdict(list)
    edges: list[tuple[int, int, int, int, int]] = []
    comparisons = 0
    for sequence_index, (pair_index, label, sequence) in enumerate(sequences):
        reverse = reverse_complement(sequence)
        candidates: set[int] = set()
        for oriented in {sequence, reverse}:
            for block_index, (start, end) in enumerate(bounds):
                candidates.update(index.get((block_index, oriented[start:end]), ()))
        for other_index in candidates:
            other_pair, other_label, other_sequence = sequences[other_index]
            if pair_index == other_pair:
                continue
            comparisons += 1
            distance = min(
                hamming_distance(sequence, other_sequence),
                hamming_distance(sequence, reverse_complement(other_sequence)),
            )
            if distance <= max_distance:
                edges.append((pair_index, other_pair, label, other_label, distance))
        for oriented in {sequence, reverse}:
            for block_index, (start, end) in enumerate(bounds):
                index[(block_index, oriented[start:end])].append(sequence_index)

    audits = tuple(_summarize_threshold(len(pairs), edges, threshold) for threshold in thresholds)
    return PairSimilarityAudit(
        pair_count=len(pairs),
        sequence_count=len(sequences),
        sequence_length=sequence_length,
        candidate_comparisons=comparisons,
        thresholds=audits,
    )


def similarity_components(
    pairs: Sequence[tuple[str, str]], threshold: int
) -> list[list[int]]:
    """Return pair indices grouped by strand-invariant sequence similarity."""

    audit = _neighbor_edges(pairs, threshold)
    dsu = _DisjointSet(len(pairs))
    for left, right, _, _, _ in audit:
        dsu.union(left, right)
    grouped: dict[int, list[int]] = defaultdict(list)
    for pair_index in range(len(pairs)):
        grouped[dsu.find(pair_index)].append(pair_index)
    return sorted(grouped.values(), key=lambda component: component[0])


def assign_components_to_partitions(
    components: Sequence[Sequence[int]],
    *,
    pair_count: int,
    test_fraction: float,
    seed: int,
    dataset_id: str,
) -> dict[str, list[int]]:
    """Assign indivisible components deterministically near a target test size."""

    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between zero and one")
    flattened = sorted(index for component in components for index in component)
    if flattened != list(range(pair_count)):
        raise ValueError("components must contain every pair index exactly once")
    target = min(pair_count - 1, max(1, round(pair_count * test_fraction)))
    ordered = sorted(
        (list(component) for component in components),
        key=lambda component: hashlib.sha256(
            f"{seed}:{dataset_id}:{','.join(map(str, component))}".encode("utf-8")
        ).digest(),
    )
    test: list[int] = []
    deferred: list[list[int]] = []
    for component in ordered:
        if len(test) + len(component) <= target:
            test.extend(component)
        else:
            deferred.append(component)
    if len(test) < target:
        # Select the smallest deterministic deferred component only when it
        # improves the absolute target deviation.
        candidate = min(deferred, key=lambda component: (len(component), component[0]))
        if abs(target - (len(test) + len(candidate))) < abs(target - len(test)):
            test.extend(candidate)
    test_set = set(test)
    train = [index for index in range(pair_count) if index not in test_set]
    if not train or not test:
        raise ValueError("component structure cannot produce non-empty partitions")
    return {"train": train, "test": sorted(test)}


def _neighbor_edges(
    pairs: Sequence[tuple[str, str]], threshold: int
) -> list[tuple[int, int, int, int, int]]:
    # Reuse the exact audited implementation for the requested threshold.
    if not pairs:
        return []
    lengths = {len(sequence) for pair in pairs for sequence in pair}
    if len(lengths) != 1:
        raise ValueError("all sequences must have one common length")
    sequence_length = lengths.pop()
    bounds = _blocks(sequence_length, threshold)
    sequences = [
        (pair_index, label, sequence)
        for pair_index, pair in enumerate(pairs)
        for label, sequence in enumerate(pair)
    ]
    index: dict[tuple[int, str], list[int]] = defaultdict(list)
    edges = []
    for sequence_index, (pair_index, label, sequence) in enumerate(sequences):
        reverse = reverse_complement(sequence)
        candidates: set[int] = set()
        for oriented in {sequence, reverse}:
            for block_index, (start, end) in enumerate(bounds):
                candidates.update(index.get((block_index, oriented[start:end]), ()))
        for other_index in candidates:
            other_pair, other_label, other_sequence = sequences[other_index]
            if pair_index == other_pair:
                continue
            distance = min(
                hamming_distance(sequence, other_sequence),
                hamming_distance(sequence, reverse_complement(other_sequence)),
            )
            if distance <= threshold:
                edges.append((pair_index, other_pair, label, other_label, distance))
        for oriented in {sequence, reverse}:
            for block_index, (start, end) in enumerate(bounds):
                index[(block_index, oriented[start:end])].append(sequence_index)
    return edges


def _summarize_threshold(
    pair_count: int,
    edges: Sequence[tuple[int, int, int, int, int]],
    threshold: int,
) -> SimilarityThresholdAudit:
    selected = [edge for edge in edges if edge[4] <= threshold]
    dsu = _DisjointSet(pair_count)
    pairs_with_neighbor: set[int] = set()
    for left, right, _, _, _ in selected:
        dsu.union(left, right)
        pairs_with_neighbor.update((left, right))
    sizes: dict[int, int] = defaultdict(int)
    for pair_index in range(pair_count):
        sizes[dsu.find(pair_index)] += 1
    return SimilarityThresholdAudit(
        threshold=threshold,
        neighbor_edges=len(selected),
        same_label_edges=sum(left_label == right_label for _, _, left_label, right_label, _ in selected),
        cross_label_edges=sum(left_label != right_label for _, _, left_label, right_label, _ in selected),
        pairs_with_neighbor=len(pairs_with_neighbor),
        component_count=len(sizes),
        multi_pair_component_count=sum(size > 1 for size in sizes.values()),
        largest_component_pairs=max(sizes.values()),
        singleton_pair_count=sum(size == 1 for size in sizes.values()),
    )


def _blocks(sequence_length: int, max_distance: int) -> list[tuple[int, int]]:
    block_count = max_distance + 1
    base, extra = divmod(sequence_length, block_count)
    bounds = []
    start = 0
    for index in range(block_count):
        end = start + base + (index < extra)
        bounds.append((start, end))
        start = end
    return bounds


class _DisjointSet:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1
