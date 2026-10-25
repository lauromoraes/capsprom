from capsprom.data.similarity_groups import (
    assign_components_to_partitions,
    audit_cross_partition_similarity,
    audit_paired_sequence_similarity,
    similarity_components,
)


def test_similarity_audit_is_strand_invariant_and_keeps_pairs_indivisible():
    pairs = [
        ("A" * 81, "AC" * 40 + "A"),
        ("A" * 80 + "C", "AG" * 40 + "A"),
        ("C" * 81, "CG" * 40 + "C"),
    ]

    audit = audit_paired_sequence_similarity(pairs)
    by_threshold = {item.threshold: item for item in audit.thresholds}

    assert by_threshold[1].pairs_with_neighbor == 2
    assert by_threshold[1].largest_component_pairs == 2
    assert by_threshold[1].cross_label_edges == 0
    assert similarity_components(pairs, threshold=1) == [[0, 1], [2]]


def test_similarity_audit_detects_reverse_complement_neighbor():
    first = "A" * 40 + "C" * 41
    reverse_neighbor = "G" * 41 + "T" * 39 + "A"
    pairs = [
        (first, "AC" * 40 + "A"),
        (reverse_neighbor, "AG" * 40 + "A"),
    ]

    audit = audit_paired_sequence_similarity(pairs, thresholds=(1,))

    assert audit.thresholds[0].pairs_with_neighbor == 2
    assert audit.thresholds[0].largest_component_pairs == 2


def test_component_assignment_is_deterministic_and_never_splits_components():
    components = [[0, 1], [2], [3], [4, 5], [6], [7], [8], [9]]

    first = assign_components_to_partitions(
        components, pair_count=10, test_fraction=0.2, seed=42, dataset_id="fixture"
    )
    second = assign_components_to_partitions(
        components, pair_count=10, test_fraction=0.2, seed=42, dataset_id="fixture"
    )

    assert first == second
    assert len(first["test"]) == 2
    for component in components:
        assert set(component) <= set(first["train"]) or set(component) <= set(first["test"])


def test_cross_partition_audit_detects_strand_invariant_neighbors():
    train = [("A" * 81, 1), ("C" * 81, 0)]
    test = [("T" * 81, 1), ("C" * 80 + "A", 1), ("G" * 70 + "A" * 11, 0)]

    audit = audit_cross_partition_similarity(train, test, thresholds=(0, 1, 8))

    assert audit[0].neighbor_edges == 1
    assert audit[0].same_label_edges == 1
    assert audit[1].neighbor_edges == 2
    assert audit[1].cross_label_edges == 1
    assert audit[2].neighbor_edges == 2
