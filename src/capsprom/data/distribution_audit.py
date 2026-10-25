"""Descriptive class-distribution summaries for aligned DNA datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .sequence_logo import sequence_logo_matrices


@dataclass(frozen=True)
class ClassDistribution:
    count: int
    gc_mean: float
    gc_std: float
    gc_q05: float
    gc_median: float
    gc_q95: float


def summarize_class_distribution(sequences: Sequence[str]) -> ClassDistribution:
    """Summarize per-sequence GC fractions without interpreting class validity."""

    if not sequences:
        raise ValueError("at least one sequence is required")
    gc = np.asarray(
        [(sequence.count("G") + sequence.count("C")) / len(sequence) for sequence in sequences]
    )
    return ClassDistribution(
        count=len(sequences),
        gc_mean=float(gc.mean()),
        gc_std=float(gc.std(ddof=1)) if len(gc) > 1 else 0.0,
        gc_q05=float(np.quantile(gc, 0.05)),
        gc_median=float(np.median(gc)),
        gc_q95=float(np.quantile(gc, 0.95)),
    )


def maximum_positional_total_variation(
    positive: Sequence[str], negative: Sequence[str], coordinate_start: int = -60
) -> tuple[int, float]:
    """Return the aligned position with the largest class-frequency distance."""

    positive_frequency = sequence_logo_matrices(positive).frequencies
    negative_frequency = sequence_logo_matrices(negative).frequencies
    total_variation = 0.5 * np.abs(positive_frequency - negative_frequency).sum(axis=1)
    index = int(np.argmax(total_variation))
    return coordinate_start + index, float(total_variation[index])
