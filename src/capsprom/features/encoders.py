"""Feature encoders and feature-combination primitives for CapsProm."""

from __future__ import annotations

import itertools
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .physicochemical import PhysicochemicalTable, load_physicochemical_table

DNA_BASES = ("A", "C", "G", "T")
DNA_ALPHABET = set(DNA_BASES)


@dataclass(frozen=True)
class FeatureBlock:
    """One named feature block generated from the same input sequence."""

    name: str
    values: list[list[float]] | list[float]
    shape: tuple[int, ...]
    metadata: dict[str, str | int | float]


@dataclass(frozen=True)
class CombinedFeatures:
    """Container for single-input and multi-input model features."""

    blocks: tuple[FeatureBlock, ...]

    def as_flat_vector(self) -> list[float]:
        """Flatten and concatenate all feature blocks for classical models."""

        flat: list[float] = []
        for block in self.blocks:
            flat.extend(_flatten(block.values))
        return flat

    def as_multi_head_inputs(self) -> dict[str, list[list[float]] | list[float]]:
        """Return named inputs for deep-learning multi-head architectures."""

        return {block.name: block.values for block in self.blocks}


def _flatten(values: list[list[float]] | list[float]) -> list[float]:
    if not values:
        return []
    first = values[0]
    if isinstance(first, list):
        return [item for row in values for item in row]  # type: ignore[arg-type]
    return list(values)  # type: ignore[arg-type]


def kmers_for_k(k: int) -> tuple[str, ...]:
    """Return lexicographically ordered DNA k-mers."""

    if k < 1:
        raise ValueError("k must be >= 1")
    return tuple("".join(parts) for parts in itertools.product(DNA_BASES, repeat=k))


def validate_dna_sequence(sequence: str) -> str:
    """Normalize and validate a DNA sequence over the ACGT alphabet."""

    normalized = sequence.strip().upper()
    invalid = sorted(set(normalized) - DNA_ALPHABET)
    if invalid:
        raise ValueError(f"sequence contains invalid DNA symbols: {''.join(invalid)}")
    return normalized


def sliding_kmers(sequence: str, k: int) -> list[str]:
    """Return overlapping k-mers from a strict DNA sequence."""

    normalized = validate_dna_sequence(sequence)
    if len(normalized) < k:
        return []
    return [normalized[index : index + k] for index in range(len(normalized) - k + 1)]


class KmerFrequencyEncoder:
    """Encode a sequence as normalized k-mer frequencies."""

    def __init__(self, k: int, normalize: bool = True, name: str | None = None) -> None:
        self.k = k
        self.normalize = normalize
        self.name = name or f"kmer_frequency_k{self.k}"
        self.vocabulary = kmers_for_k(k)

    def encode(self, sequence: str) -> FeatureBlock:
        observed = sliding_kmers(sequence, self.k)
        counts = Counter(observed)
        denominator = len(observed) if self.normalize and observed else 1
        values = [counts.get(kmer, 0) / denominator for kmer in self.vocabulary]
        return FeatureBlock(
            name=self.name,
            values=values,
            shape=(len(values),),
            metadata={"encoding": "kmer_frequency", "k": self.k, "normalize": int(self.normalize)},
        )


class OneHotEncoder:
    """Encode sequence positions as one-hot vectors over the DNA alphabet."""

    def __init__(self, k: int = 1, name: str | None = None) -> None:
        self.k = k
        self.name = name or f"one_hot_k{self.k}"
        self.vocabulary = kmers_for_k(k)
        self.index = {kmer: idx for idx, kmer in enumerate(self.vocabulary)}

    def encode(self, sequence: str) -> FeatureBlock:
        rows: list[list[float]] = []
        for kmer in sliding_kmers(sequence, self.k):
            row = [0.0] * len(self.vocabulary)
            if kmer in self.index:
                row[self.index[kmer]] = 1.0
            rows.append(row)
        return FeatureBlock(
            name=self.name,
            values=rows,
            shape=(len(rows), len(self.vocabulary)),
            metadata={"encoding": "one_hot", "k": self.k},
        )


class PhysicochemicalEncoder:
    """Encode overlapping k-mers using normalized physicochemical properties."""

    def __init__(
        self,
        table: PhysicochemicalTable,
        name: str | None = None,
        properties: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        self.table = table.select_properties(properties)
        self.name = name or f"physicochemical_{self.table.k}mer"

    @classmethod
    def from_tsv(
        cls,
        path: Path,
        name: str | None = None,
        properties: list[str] | tuple[str, ...] | None = None,
    ) -> "PhysicochemicalEncoder":
        return cls(load_physicochemical_table(path), name=name, properties=properties)

    def encode(self, sequence: str) -> FeatureBlock:
        rows = [list(self.table.encode_kmer(kmer)) for kmer in sliding_kmers(sequence, self.table.k)]
        return FeatureBlock(
            name=self.name,
            values=rows,
            shape=(len(rows), self.table.feature_count),
            metadata={
                "encoding": "physicochemical",
                "k": self.table.k,
                "property_count": self.table.feature_count,
                "property_names": "|".join(self.table.properties),
                "reference": self.table.path.as_posix(),
            },
        )


class FeatureSetBuilder:
    """Apply one or more encoders to build combined model inputs."""

    def __init__(self, encoders: Sequence[object]) -> None:
        self.encoders = tuple(encoders)
        names = [getattr(encoder, "name", None) for encoder in self.encoders]
        if len(names) != len(set(names)):
            raise ValueError(f"feature block names must be unique: {names}")

    def encode(self, sequence: str) -> CombinedFeatures:
        blocks = []
        for encoder in self.encoders:
            encode = getattr(encoder, "encode", None)
            if encode is None:
                raise TypeError(f"encoder {encoder!r} does not provide encode(sequence)")
            blocks.append(encode(sequence))
        return CombinedFeatures(tuple(blocks))

    def encode_many(self, sequences: Iterable[str]) -> list[CombinedFeatures]:
        return [self.encode(sequence) for sequence in sequences]
