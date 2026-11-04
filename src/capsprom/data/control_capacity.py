"""Free genomic capacity for non-overlapping controls under a both-strand TSS exclusion."""

from __future__ import annotations

from collections.abc import Iterable


def excluded_intervals(tss0: Iterable[int], radius: int, length: int) -> list[tuple[int, int]]:
    """Merged half-open intervals ``[t - r, t + r + 1)`` clipped to ``[0, length)``.

    The exclusion is strand-independent, so one interval set covers both strands.
    """

    positions = list(tss0)
    if any(t < 0 or t >= length for t in positions):
        raise ValueError("TSS position outside the contig")
    spans = sorted((max(0, t - radius), min(length, t + radius + 1)) for t in positions)
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def free_runs(excluded: list[tuple[int, int]], length: int) -> list[tuple[int, int]]:
    """Complement of merged excluded intervals on a linear contig."""

    runs, cursor = [], 0
    for start, end in excluded:
        if start > cursor:
            runs.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < length:
        runs.append((cursor, length))
    return runs


def non_overlapping_slots(runs: list[tuple[int, int]], window: int) -> int:
    """Maximum number of disjoint windows that fit inside the free runs."""

    return sum((end - start) // window for start, end in runs)
