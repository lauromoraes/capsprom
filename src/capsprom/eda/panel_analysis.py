"""Descriptive sequence features for comparing negative panels.

Everything here is model-free. Callers pass training rows only.
"""

from __future__ import annotations

from itertools import product
from typing import Sequence

import numpy as np

BASES = "ACGT"
_CODE = {base: index for index, base in enumerate(BASES)}
_COMPLEMENT = str.maketrans("ACGT", "TGCA")


def reverse_complement(sequence: str) -> str:
    return sequence.translate(_COMPLEMENT)[::-1]


def encode(sequences: Sequence[str]) -> np.ndarray:
    """Return an equal-length integer matrix of A=0, C=1, G=2, T=3."""

    return np.array([[_CODE[base] for base in sequence] for sequence in sequences], dtype=np.int8)


def gc_fraction(codes: np.ndarray) -> np.ndarray:
    return np.isin(codes, (1, 2)).mean(axis=1)


def gc_skew(codes: np.ndarray) -> np.ndarray:
    g, c = (codes == 2).sum(axis=1), (codes == 1).sum(axis=1)
    return (g - c) / np.maximum(g + c, 1)


def shannon_entropy(codes: np.ndarray) -> np.ndarray:
    frequencies = np.stack([(codes == base).mean(axis=1) for base in range(4)], axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        logged = np.where(frequencies > 0, np.log2(frequencies), 0.0)
    return -(frequencies * logged).sum(axis=1)


def periodicity_3(codes: np.ndarray) -> np.ndarray:
    """Base identity at lag 3 minus the mean at lags 2 and 4; coding sequence scores high."""

    match = {lag: (codes[:, :-lag] == codes[:, lag:]).mean(axis=1) for lag in (2, 3, 4)}
    return match[3] - (match[2] + match[4]) / 2


def kmer_names(k: int) -> list[str]:
    return ["".join(kmer) for kmer in product(BASES, repeat=k)]


def kmer_frequencies(codes: np.ndarray, k: int) -> np.ndarray:
    weights = 4 ** np.arange(k - 1, -1, -1)
    windows = np.lib.stride_tricks.sliding_window_view(codes, k, axis=1) @ weights
    counts = np.zeros((codes.shape[0], 4**k))
    for row, indices in enumerate(windows):
        counts[row] = np.bincount(indices, minlength=4**k)
    return counts / counts.sum(axis=1, keepdims=True)


def hellinger(frequencies: np.ndarray) -> np.ndarray:
    """Square-root transform: Euclidean distance then suits compositions."""

    return np.sqrt(frequencies)


def one_hot(codes: np.ndarray) -> np.ndarray:
    return np.eye(4, dtype=np.float32)[codes].reshape(codes.shape[0], -1)


def position_frequencies(codes: np.ndarray) -> np.ndarray:
    return np.stack([(codes == base).mean(axis=0) for base in range(4)], axis=1)


def total_variation(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    """Per-position total variation distance between two frequency matrices."""

    return 0.5 * np.abs(first - second).sum(axis=1)


def relative_entropy_to_background(frequencies: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Per-position Kullback-Leibler divergence in bits from a panel's own composition."""

    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(frequencies > 0, frequencies * np.log2(frequencies / background), 0.0)
    return terms.sum(axis=1)


def standardized_mean_difference(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    """Columnwise difference in means over the pooled standard deviation."""

    pooled = np.sqrt((first.var(axis=0, ddof=1) + second.var(axis=0, ddof=1)) / 2)
    difference = first.mean(axis=0) - second.mean(axis=0)
    return np.divide(difference, pooled, out=np.zeros_like(difference), where=pooled > 0)


def best_motif_mismatches(codes: np.ndarray, motif: str, start: int, stop: int) -> np.ndarray:
    """Fewest mismatches to a motif over window indices start..stop, both inclusive."""

    target = np.array([_CODE[base] for base in motif], dtype=np.int8)
    span = len(motif)
    scores = [(codes[:, i : i + span] != target).sum(axis=1) for i in range(start, stop - span + 2)]
    return np.min(scores, axis=0)


def nearest_identity(query: np.ndarray, reference: np.ndarray, exclude_self: bool = False) -> np.ndarray:
    """Highest ungapped identity of each query to any reference, either strand."""

    reverse = 3 - reference[:, ::-1]
    best = np.zeros(query.shape[0])
    for start in range(0, query.shape[0], 256):
        chunk = query[start : start + 256]
        forward = (chunk[:, None, :] == reference[None, :, :]).mean(axis=2)
        if exclude_self:
            forward[np.arange(chunk.shape[0]), np.arange(start, start + chunk.shape[0])] = 0
        backward = (chunk[:, None, :] == reverse[None, :, :]).mean(axis=2)
        if exclude_self:
            backward[np.arange(chunk.shape[0]), np.arange(start, start + chunk.shape[0])] = 0
        best[start : start + chunk.shape[0]] = np.maximum(forward.max(axis=1), backward.max(axis=1))
    return best


def same_group_neighbor_fraction(points: np.ndarray, groups: np.ndarray, k: int) -> float:
    """Mean share of a point's k nearest neighbours that carry its group label."""

    from sklearn.neighbors import NearestNeighbors

    indices = NearestNeighbors(n_neighbors=k + 1).fit(points).kneighbors(points, return_distance=False)
    return float((groups[indices[:, 1:]] == groups[:, None]).mean())


def neighbor_overlap(first: np.ndarray, second: np.ndarray, k: int) -> float:
    """Mean share of k nearest neighbours kept between two representations."""

    from sklearn.neighbors import NearestNeighbors

    a = NearestNeighbors(n_neighbors=k + 1).fit(first).kneighbors(first, return_distance=False)[:, 1:]
    b = NearestNeighbors(n_neighbors=k + 1).fit(second).kneighbors(second, return_distance=False)[:, 1:]
    return float(np.mean([len(set(x) & set(y)) / k for x, y in zip(a, b)]))
