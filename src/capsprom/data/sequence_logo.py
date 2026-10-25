"""Position-frequency and Shannon-information matrices for aligned DNA."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np


NUCLEOTIDES = ("A", "C", "G", "T")


@dataclass(frozen=True)
class SequenceLogoMatrices:
    """Frequency and information-height matrices for one aligned collection."""

    sequence_count: int
    sequence_length: int
    frequencies: np.ndarray
    information_heights: np.ndarray


def sequence_logo_matrices(sequences: Sequence[str]) -> SequenceLogoMatrices:
    """Calculate uncorrected Shannon-information logo heights in bits."""

    if not sequences:
        raise ValueError("at least one sequence is required")
    lengths = {len(sequence) for sequence in sequences}
    if len(lengths) != 1:
        raise ValueError("all sequences must have equal length")
    invalid = sorted({base for sequence in sequences for base in sequence} - set(NUCLEOTIDES))
    if invalid:
        raise ValueError(f"invalid DNA symbols: {invalid}")
    sequence_length = lengths.pop()
    frequencies = np.zeros((sequence_length, len(NUCLEOTIDES)), dtype=float)
    for column, nucleotide in enumerate(NUCLEOTIDES):
        frequencies[:, column] = [
            sum(sequence[position] == nucleotide for sequence in sequences)
            / len(sequences)
            for position in range(sequence_length)
        ]
    entropy = np.zeros(sequence_length, dtype=float)
    for position in range(sequence_length):
        entropy[position] = -sum(
            frequency * math.log2(frequency)
            for frequency in frequencies[position]
            if frequency > 0
        )
    information = 2.0 - entropy
    return SequenceLogoMatrices(
        sequence_count=len(sequences),
        sequence_length=sequence_length,
        frequencies=frequencies,
        information_heights=frequencies * information[:, None],
    )
