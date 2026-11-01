"""Exact both-strand search of released sequences on reference genomes (protocol B2).

Coordinates are 0-based, half-open, on the forward strand of the contig. A hit on
the minus strand means the record equals the reverse complement of the interval.
"""

from __future__ import annotations

import gzip
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

_COMPLEMENT = str.maketrans("ACGTNRYSWKMBDHV", "TGCANYRSWMKVHDB")
_IUPAC = {
    "R": "AG", "Y": "CT", "S": "CG", "W": "AT", "K": "GT", "M": "AC",
    "B": "CGT", "D": "AGT", "H": "ACT", "V": "ACG", "N": "ACGT",
}
_COMPATIBLE = {base: base + "".join(code for code, bases in _IUPAC.items() if base in bases) for base in "ACGT"}
_NON_ACGT = re.compile("[^ACGT]")


@dataclass(frozen=True)
class Locus:
    contig: str
    start: int
    end: int
    strand: str
    match_class: str = "exact"


@dataclass(frozen=True)
class MappingResult:
    status: str
    loci: tuple[Locus, ...]


def reverse_complement(sequence: str) -> str:
    return sequence.translate(_COMPLEMENT)[::-1]


def read_fasta(path: Path) -> dict[str, str]:
    """Read a (optionally gzipped) FASTA into upper-case sequences keyed by accession."""

    opener = gzip.open if path.suffix == ".gz" else open
    contigs: dict[str, list[str]] = {}
    current: list[str] | None = None
    with opener(path, "rt") as handle:
        for line in handle:
            line = line.strip()
            if line.startswith(">"):
                name = line[1:].split()[0]
                if name in contigs:
                    raise ValueError(f"duplicate contig {name} in {path}")
                current = contigs[name] = []
            elif line:
                if current is None:
                    raise ValueError(f"sequence before header in {path}")
                current.append(line.upper())
    return {name: "".join(parts) for name, parts in contigs.items()}


def non_acgt_count(sequence: str) -> int:
    return len(_NON_ACGT.findall(sequence))


def _occurrences(text: str, query: str) -> Iterable[int]:
    position = text.find(query)
    while position != -1:
        yield position
        position = text.find(query, position + 1)


def _compatible_occurrences(text: str, query: str) -> set[int]:
    pattern = re.compile("(?=" + "".join(f"[{_COMPATIBLE[base]}]" for base in query) + ")")
    return {match.start() for match in pattern.finditer(text)}


def find_exact(query: str, contigs: Mapping[str, str]) -> tuple[Locus, ...]:
    """Return every occurrence on both strands, overlapping hits included.

    Exact hits are class ``exact``. On contigs with non-ACGT bases, hits that match
    only where the reference has an IUPAC code compatible with the record base are
    class ``iupac_compatible``. A palindromic hit, equal on both strands at one
    interval, is reported once with strand ``.``.
    """

    query = query.upper()
    if _NON_ACGT.search(query):
        raise ValueError("query must be strict DNA")
    reverse = reverse_complement(query)
    loci: list[Locus] = []
    for name in sorted(contigs):
        text = contigs[name]
        plus = set(_occurrences(text, query))
        minus = plus if reverse == query else set(_occurrences(text, reverse))
        exact = plus | minus
        if _NON_ACGT.search(text):
            plus |= _compatible_occurrences(text, query)
            minus |= plus if reverse == query else _compatible_occurrences(text, reverse)
        for start in sorted(plus | minus):
            if start in plus and start in minus:
                strand = "."
            else:
                strand = "+" if start in plus else "-"
            match_class = "exact" if start in exact else "iupac_compatible"
            loci.append(Locus(name, start, start + len(query), strand, match_class))
    return tuple(loci)


def map_sequence(query: str, contigs: Mapping[str, str]) -> MappingResult:
    loci = find_exact(query, contigs)
    if not loci:
        return MappingResult("unmapped", loci)
    return MappingResult("verified" if len(loci) == 1 else "ambiguous", loci)


def extract(contigs: Mapping[str, str], locus: Locus) -> str:
    """Re-extract the oriented record sequence of a locus (round-trip check)."""

    segment = contigs[locus.contig][locus.start : locus.end]
    return reverse_complement(segment) if locus.strand == "-" else segment
