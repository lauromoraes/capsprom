"""Homology grouping and group-safe partitioning (``specs/homology_grouping_protocol.md``).

Records are joined by four edge sources: a shared unit (an indivisible
positive--control pair), an MMseqs2 alignment above the identity and coverage
thresholds, an exact Hamming distance of at most ``floor(0.20 * L)`` on either
strand, and overlapping windows on the same assembly.  Groups are the
connected components.  Partitioning is label-aware only to target class
fractions; grouping itself never reads labels.
"""

from __future__ import annotations

import collections
import dataclasses
import hashlib
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np

from .graphpro_reconstruction import reverse_complement
from .near_duplicate_audit import hamming_distance
from .similarity_groups import _blocks, _DisjointSet

HIT_COLUMNS = ("query", "target", "fident", "alnlen", "qstart", "qend", "tstart", "tend", "qlen", "tlen", "evalue", "bits")
EDGE_SOURCES = ("unit", "alignment", "hamming", "genomic_overlap")


@dataclass(frozen=True)
class GroupingRecord:
    """One record of a dataset; ``unit`` ties records that must stay together."""

    record_id: str
    sequence: str
    label: int
    unit: str
    contig: str | None = None
    start: int | None = None
    end: int | None = None


@dataclass(frozen=True)
class SearchSettings:
    min_seq_id: float = 0.80
    coverage: float = 0.80
    kmer_size: int = 9
    e_value: float = 0.001
    max_seqs: int = 1000
    split_memory_limit: str = "3G"
    threads: int | None = None

    @classmethod
    def from_config(cls, search: Mapping[str, object]) -> "SearchSettings":
        if search.get("search_type") != 3 or search.get("strand") != 2 or search.get("cov_mode") != 0:
            raise ValueError("homology grouping requires search_type 3, strand 2, and cov_mode 0")
        return cls(
            min_seq_id=float(search["min_seq_id"]),
            coverage=float(search["coverage"]),
            kmer_size=int(search["kmer_size"]),
            e_value=float(search["e_value"]),
            max_seqs=int(search["max_seqs"]),
            split_memory_limit=str(search["split_memory_limit"]),
        )


@dataclass
class Grouping:
    """Connected components and the edges that produced them."""

    group_of: dict[str, int]
    edges: dict[tuple[str, str], set[str]] = field(default_factory=dict)

    def groups(self) -> dict[int, list[str]]:
        members: dict[int, list[str]] = collections.defaultdict(list)
        for record_id, group in self.group_of.items():
            members[group].append(record_id)
        return dict(members)


def write_fasta(records: Sequence[GroupingRecord], path: Path) -> None:
    with Path(path).open("w", encoding="ascii", newline="\n") as handle:
        for record in records:
            handle.write(f">{record.record_id}\n{record.sequence}\n")


def mmseqs_provenance(binary: Path) -> dict[str, str]:
    version = subprocess.run([str(binary), "version"], capture_output=True, text=True, check=True)
    return {
        "binary": str(binary),
        "binary_sha256": hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
        "version": version.stdout.strip(),
    }


def mmseqs_command(binary: Path, fasta: Path, hits: Path, tmp: Path, settings: SearchSettings) -> list[str]:
    command = [
        str(binary), "easy-search", str(fasta), str(fasta), str(hits), str(tmp),
        "--search-type", "3", "--strand", "2",
        "--min-seq-id", str(settings.min_seq_id), "-c", str(settings.coverage), "--cov-mode", "0",
        "-k", str(settings.kmer_size), "-e", str(settings.e_value),
        "--max-seqs", str(settings.max_seqs), "--split-memory-limit", settings.split_memory_limit,
        "--format-output", ",".join(HIT_COLUMNS),
    ]
    if settings.threads:
        command += ["--threads", str(settings.threads)]
    return command


def run_mmseqs_search(
    records: Sequence[GroupingRecord], workdir: Path, binary: Path, settings: SearchSettings
) -> dict[str, object]:
    """Run the all-versus-all search and return the hit path and provenance."""

    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    fasta, hits = workdir / "records.fasta", workdir / "hits.m8"
    write_fasta(records, fasta)
    command = mmseqs_command(binary, fasta, hits, workdir / "tmp", settings)
    subprocess.run(command, check=True, capture_output=True, text=True)
    return {
        **mmseqs_provenance(binary),
        "command_line": shlex.join(command),
        "hits": str(hits),
        "hits_sha256": hashlib.sha256(hits.read_bytes()).hexdigest(),
    }


def alignment_edges(hits: Path, settings: SearchSettings) -> set[tuple[str, str]]:
    """Read MMseqs2 hits, drop self-hits, re-apply thresholds, and enforce the hit cap."""

    edges, per_query = set(), collections.Counter()
    for line in Path(hits).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = dict(zip(HIT_COLUMNS, line.split("\t"), strict=True))
        per_query[row["query"]] += 1
        if row["query"] == row["target"]:
            continue
        query_cover = (abs(int(row["qend"]) - int(row["qstart"])) + 1) / int(row["qlen"])
        target_cover = (abs(int(row["tend"]) - int(row["tstart"])) + 1) / int(row["tlen"])
        if (
            float(row["fident"]) >= settings.min_seq_id
            and min(query_cover, target_cover) >= settings.coverage
        ):
            edges.add(_edge(row["query"], row["target"]))
    saturated = sorted(query for query, count in per_query.items() if count >= settings.max_seqs)
    if saturated:
        raise RuntimeError(f"{len(saturated)} queries reached max_seqs; edges may be missing")
    return edges


def hamming_edges(records: Sequence[GroupingRecord], max_fraction: float = 0.20) -> set[tuple[str, str]]:
    """Exact strand-invariant Hamming edges among equal-length records (pigeonhole index)."""

    by_length: dict[int, list[GroupingRecord]] = collections.defaultdict(list)
    for record in records:
        by_length[len(record.sequence)].append(record)
    edges = set()
    for length, members in by_length.items():
        threshold = int(np.floor(max_fraction * length + 1e-9))
        bounds = _blocks(length, threshold)
        index: dict[tuple[int, str], list[int]] = collections.defaultdict(list)
        for position, record in enumerate(members):
            forward = record.sequence
            reverse = reverse_complement(forward)
            candidates: set[int] = set()
            for oriented in {forward, reverse}:
                for block, (start, end) in enumerate(bounds):
                    candidates.update(index.get((block, oriented[start:end]), ()))
            for other in candidates:
                sequence = members[other].sequence
                if min(hamming_distance(forward, sequence), hamming_distance(reverse, sequence)) <= threshold:
                    edges.add(_edge(record.record_id, members[other].record_id))
            for block, (start, end) in enumerate(bounds):
                index[(block, forward[start:end])].append(position)
    return edges


def genomic_overlap_edges(records: Sequence[GroupingRecord]) -> set[tuple[str, str]]:
    """Join records whose windows overlap on the same contig, on either strand."""

    by_contig: dict[str, list[GroupingRecord]] = collections.defaultdict(list)
    for record in records:
        if record.contig is not None:
            if record.start is None or record.end is None or record.start >= record.end:
                raise ValueError(f"invalid coordinates for {record.record_id}")
            by_contig[record.contig].append(record)
    edges = set()
    for members in by_contig.values():
        members.sort(key=lambda record: (record.start, record.end))
        active: list[GroupingRecord] = []
        for record in members:
            active = [other for other in active if other.end > record.start]
            edges.update(_edge(record.record_id, other.record_id) for other in active)
            active.append(record)
    return edges


def place_unique_windows(records: Sequence[GroupingRecord], contig: str, genome: str) -> list[GroupingRecord]:
    """Add coordinates to records with one exact match on either strand.

    Multi-locus and unplaced records stay without coordinates, so they keep
    sequence edges only.
    """

    reverse = reverse_complement(genome)
    placed = []
    for record in records:
        length = len(record.sequence)
        starts = _occurrences(genome, record.sequence)
        starts += [len(genome) - hit - length for hit in _occurrences(reverse, record.sequence)]
        if len(starts) == 1:
            record = dataclasses.replace(record, contig=contig, start=starts[0], end=starts[0] + length)
        placed.append(record)
    return placed


def _occurrences(text: str, query: str) -> list[int]:
    hits, position = [], text.find(query)
    while position >= 0:
        hits.append(position)
        position = text.find(query, position + 1)
    return hits


def unit_edges(records: Sequence[GroupingRecord]) -> set[tuple[str, str]]:
    by_unit: dict[str, list[str]] = collections.defaultdict(list)
    for record in records:
        by_unit[record.unit].append(record.record_id)
    return {_edge(ids[0], other) for ids in by_unit.values() for other in ids[1:]}


def connected_groups(
    records: Sequence[GroupingRecord], edge_sets: Mapping[str, Iterable[tuple[str, str]]]
) -> Grouping:
    """Union every edge source into connected components with stable group ids."""

    ids = [record.record_id for record in records]
    if len(set(ids)) != len(ids):
        raise ValueError("record identifiers must be unique")
    position = {record_id: index for index, record_id in enumerate(ids)}
    dsu = _DisjointSet(len(ids))
    sources: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for source, edges in edge_sets.items():
        for left, right in edges:
            dsu.union(position[left], position[right])
            sources[_edge(left, right)].add(source)
    roots: dict[int, int] = {}
    group_of = {}
    for record_id in ids:  # group ids follow first appearance in input order
        root = dsu.find(position[record_id])
        group_of[record_id] = roots.setdefault(root, len(roots))
    return Grouping(group_of, dict(sources))


def grouping_report(records: Sequence[GroupingRecord], grouping: Grouping, max_component_fraction: float) -> dict:
    labels = {record.record_id: record.label for record in records}
    groups = grouping.groups()
    sizes = sorted((len(members) for members in groups.values()), reverse=True)
    combinations = collections.Counter("+".join(sorted(sources)) for sources in grouping.edges.values())
    largest_fraction = sizes[0] / len(records) if records else 0.0
    return {
        "records": len(records),
        "groups": len(groups),
        "largest_group": sizes[0] if sizes else 0,
        "largest_group_fraction": largest_fraction,
        "oversized": largest_fraction > max_component_fraction,
        "mixed_label_groups": sum(len({labels[r] for r in members}) > 1 for members in groups.values()),
        "group_size_distribution": dict(sorted(collections.Counter(sizes).items())),
        "edges_by_source": {source: sum(source in s for s in grouping.edges.values()) for source in EDGE_SOURCES},
        "edges_by_source_combination": dict(sorted(combinations.items())),
        "coordinate_coverage": sum(record.contig is not None for record in records) / len(records)
        if records
        else 0.0,
    }


def partition_groups(
    records: Sequence[GroupingRecord],
    grouping: Grouping,
    *,
    test_fraction: float,
    seed: int,
    folds: int,
    fold_seed: int,
) -> dict[str, str]:
    """Assign whole groups to test toward each class target, then inner folds to train.

    Groups are shuffled with ``numpy.random.default_rng(seed)``; a group joins
    the test set when that lowers the summed absolute deviation from the
    per-class targets.  Training groups receive stratified group k-fold folds.
    Returns ``record_id -> "test" | "train:<fold>"``.
    """

    from sklearn.model_selection import StratifiedGroupKFold

    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between zero and one")
    labels = {record.record_id: record.label for record in records}
    groups = grouping.groups()
    class_totals = collections.Counter(labels.values())
    targets = {label: round(count * test_fraction) for label, count in class_totals.items()}
    counts = {label: 0 for label in class_totals}
    order = np.random.default_rng(seed).permutation(sorted(groups))
    test_groups = set()
    for group in order.tolist():
        added = collections.Counter(labels[record_id] for record_id in groups[group])
        before = sum(abs(targets[c] - counts[c]) for c in counts)
        after = sum(abs(targets[c] - counts[c] - added[c]) for c in counts)
        if after < before:
            test_groups.add(group)
            for label, count in added.items():
                counts[label] += count
    assignment = {record_id: "test" for g in test_groups for record_id in groups[g]}
    train = [record.record_id for record in records if record.record_id not in assignment]
    if not train or not assignment:
        raise ValueError("group structure cannot produce non-empty partitions")
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=fold_seed)
    train_labels = [labels[record_id] for record_id in train]
    train_groups = [grouping.group_of[record_id] for record_id in train]
    for fold, (_, held) in enumerate(splitter.split(train, train_labels, train_groups)):
        for index in held:
            assignment[train[index]] = f"train:{fold}"
    return assignment


def cross_partition_edges(grouping: Grouping, assignment: Mapping[str, str]) -> dict[str, int]:
    """Count edges that cross train/test or inner-fold boundaries (must be zero)."""

    train_test = folds = 0
    for left, right in grouping.edges:
        a, b = assignment[left], assignment[right]
        if (a == "test") != (b == "test"):
            train_test += 1
        elif a != b:
            folds += 1
    return {"train_test": train_test, "inner_fold": folds}


def _edge(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left <= right else (right, left)
