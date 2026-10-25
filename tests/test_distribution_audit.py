import pytest

from capsprom.data.distribution_audit import (
    maximum_positional_total_variation,
    summarize_class_distribution,
)


def test_distribution_summary_and_positional_distance():
    summary = summarize_class_distribution(["A" * 81, "G" * 81])
    position, distance = maximum_positional_total_variation(
        ["A" * 81, "A" * 81], ["A" * 80 + "C", "A" * 80 + "C"]
    )

    assert summary.gc_mean == 0.5
    assert summary.gc_median == 0.5
    assert position == 20
    assert distance == 1.0


def test_distribution_summary_rejects_empty_input():
    with pytest.raises(ValueError, match="at least one"):
        summarize_class_distribution([])
