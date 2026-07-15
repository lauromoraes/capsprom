"""Load physicochemical property tables for nucleotide k-mers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PhysicochemicalTable:
    """Normalized physicochemical values indexed by k-mer and property."""

    path: Path
    k: int
    kmers: tuple[str, ...]
    properties: tuple[str, ...]
    values_by_kmer: dict[str, tuple[float, ...]]

    @property
    def feature_count(self) -> int:
        """Number of physicochemical properties per k-mer."""

        return len(self.properties)

    def encode_kmer(self, kmer: str) -> tuple[float, ...]:
        """Return the property vector for a k-mer."""

        normalized = kmer.upper()
        if normalized not in self.values_by_kmer:
            raise KeyError(f"k-mer {kmer!r} is not available in {self.path}")
        return self.values_by_kmer[normalized]

    def select_properties(self, properties: list[str] | tuple[str, ...] | None) -> "PhysicochemicalTable":
        """Return a table restricted to selected properties.

        `None` keeps all properties. Explicit selections preserve the requested
        order and must match property names exactly.
        """

        if properties is None:
            return self
        requested = tuple(properties)
        property_to_index = {name: index for index, name in enumerate(self.properties)}
        missing = [name for name in requested if name not in property_to_index]
        if missing:
            available = ", ".join(self.properties)
            raise ValueError(f"unknown physicochemical properties {missing}; available properties: {available}")
        indexes = tuple(property_to_index[name] for name in requested)
        return PhysicochemicalTable(
            path=self.path,
            k=self.k,
            kmers=self.kmers,
            properties=requested,
            values_by_kmer={kmer: tuple(values[index] for index in indexes) for kmer, values in self.values_by_kmer.items()},
        )


def load_physicochemical_table(path: Path) -> PhysicochemicalTable:
    """Load a normalized dinucleotide or trinucleotide property table.

    Expected input format: the first column contains property names and the
    remaining columns contain DNA k-mers. Each row maps one property to all
    k-mer values.
    """

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader)
        if len(header) < 2:
            raise ValueError(f"invalid physicochemical table header: {path}")
        kmers = tuple(column.strip().upper() for column in header[1:])
        lengths = {len(kmer) for kmer in kmers}
        if len(lengths) != 1:
            raise ValueError(f"mixed k-mer lengths in {path}: {sorted(lengths)}")
        properties: list[str] = []
        by_kmer: dict[str, list[float]] = {kmer: [] for kmer in kmers}
        for row_number, row in enumerate(reader, start=2):
            if not row or not row[0].strip():
                continue
            if len(row) != len(header):
                raise ValueError(f"row {row_number} in {path} has {len(row)} columns; expected {len(header)}")
            properties.append(row[0].strip())
            for kmer, raw_value in zip(kmers, row[1:]):
                by_kmer[kmer].append(float(raw_value.strip()))
    return PhysicochemicalTable(
        path=path,
        k=next(iter(lengths)),
        kmers=kmers,
        properties=tuple(properties),
        values_by_kmer={kmer: tuple(values) for kmer, values in by_kmer.items()},
    )
