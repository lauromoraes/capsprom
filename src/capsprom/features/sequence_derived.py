"""Sequence-derived DNA feature encoders."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .encoders import FeatureBlock, kmers_for_k, sliding_kmers, validate_dna_sequence
from .physicochemical import PhysicochemicalTable, load_physicochemical_table


def _safe_skew(positive: int, negative: int) -> float:
    denominator = positive + negative
    if denominator == 0:
        return 0.0
    return (positive - negative) / denominator


def _gc_content(sequence: str) -> float:
    if not sequence:
        return 0.0
    return (sequence.count("G") + sequence.count("C")) / len(sequence)


class GCContentSkewEncoder:
    """Encode global and optional windowed GC content/skew features."""

    def __init__(
        self,
        name: str | None = None,
        window_size: int | None = None,
        step: int | None = None,
        include_global: bool = True,
        include_skew: bool = True,
        include_at_skew: bool = False,
    ) -> None:
        if window_size is not None and window_size < 1:
            raise ValueError("window_size must be >= 1")
        if step is not None and step < 1:
            raise ValueError("step must be >= 1")
        if not include_global and window_size is None:
            raise ValueError("GC features must include global features or define window_size")
        self.name = name or "gc_content_skew"
        self.window_size = window_size
        self.step = step or window_size
        self.include_global = include_global
        self.include_skew = include_skew
        self.include_at_skew = include_at_skew

    def encode(self, sequence: str) -> FeatureBlock:
        normalized = validate_dna_sequence(sequence)
        values: list[float] = []
        feature_names: list[str] = []

        if self.include_global:
            self._append_features(normalized, "global", values, feature_names)

        if self.window_size is not None:
            step = self.step or self.window_size
            for start in range(0, len(normalized) - self.window_size + 1, step):
                end = start + self.window_size
                self._append_features(normalized[start:end], f"window_{start}_{end}", values, feature_names)

        return FeatureBlock(
            name=self.name,
            values=values,
            shape=(len(values),),
            metadata={
                "encoding": "gc_content_skew",
                "window_size": self.window_size or 0,
                "step": self.step or 0,
                "include_global": int(self.include_global),
                "include_skew": int(self.include_skew),
                "include_at_skew": int(self.include_at_skew),
                "feature_names": "|".join(feature_names),
            },
        )

    def _append_features(self, sequence: str, prefix: str, values: list[float], feature_names: list[str]) -> None:
        values.append(_gc_content(sequence))
        feature_names.append(f"{prefix}_gc_content")
        if self.include_skew:
            values.append(_safe_skew(sequence.count("G"), sequence.count("C")))
            feature_names.append(f"{prefix}_gc_skew")
        if self.include_at_skew:
            values.append(_safe_skew(sequence.count("A"), sequence.count("T")))
            feature_names.append(f"{prefix}_at_skew")


class PseKNCEncoder:
    """Encode pseudo k-tuple nucleotide composition features.

    The encoder combines normalized k-mer composition with sequence-order
    correlation factors computed from selected physicochemical properties. With
    k=2 this corresponds to a PseDNC-style representation; with k=3 it
    corresponds to a PseTNC-style representation.
    """

    def __init__(
        self,
        table: PhysicochemicalTable,
        name: str | None = None,
        properties: list[str] | tuple[str, ...] | None = None,
        lambda_value: int = 1,
        weight: float = 0.05,
    ) -> None:
        if lambda_value < 1:
            raise ValueError("lambda_value must be >= 1")
        if weight < 0:
            raise ValueError("weight must be >= 0")
        self.table = table.select_properties(properties)
        self.name = name or f"pseknc_k{self.table.k}"
        self.lambda_value = lambda_value
        self.weight = weight
        self.vocabulary = kmers_for_k(self.table.k)

    @classmethod
    def from_tsv(
        cls,
        path: Path,
        name: str | None = None,
        properties: list[str] | tuple[str, ...] | None = None,
        lambda_value: int = 1,
        weight: float = 0.05,
    ) -> "PseKNCEncoder":
        return cls(
            load_physicochemical_table(path),
            name=name,
            properties=properties,
            lambda_value=lambda_value,
            weight=weight,
        )

    def encode(self, sequence: str) -> FeatureBlock:
        kmers = sliding_kmers(sequence, self.table.k)
        if not kmers:
            raise ValueError(f"sequence length must be at least k={self.table.k} for PseKNC encoding")

        counts = Counter(kmers)
        frequencies = [counts.get(kmer, 0) / len(kmers) for kmer in self.vocabulary]
        theta = [self._correlation_factor(kmers, lag) for lag in range(1, self.lambda_value + 1)]
        denominator = 1.0 + self.weight * sum(theta)
        values = [value / denominator for value in frequencies]
        values.extend((self.weight * value) / denominator for value in theta)

        return FeatureBlock(
            name=self.name,
            values=values,
            shape=(len(values),),
            metadata={
                "encoding": "pseknc",
                "k": self.table.k,
                "lambda_value": self.lambda_value,
                "weight": self.weight,
                "property_count": self.table.feature_count,
                "property_names": "|".join(self.table.properties),
                "reference": self.table.path.as_posix(),
                "composition_count": len(self.vocabulary),
                "correlation_count": self.lambda_value,
            },
        )

    def _correlation_factor(self, kmers: list[str], lag: int) -> float:
        pair_count = len(kmers) - lag
        if pair_count <= 0:
            return 0.0
        total = 0.0
        for index in range(pair_count):
            left = self.table.encode_kmer(kmers[index])
            right = self.table.encode_kmer(kmers[index + lag])
            squared_distance = sum((a - b) ** 2 for a, b in zip(left, right)) / self.table.feature_count
            total += squared_distance
        return total / pair_count
