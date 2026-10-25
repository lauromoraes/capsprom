"""Builders that convert raw CapsProm source datasets into normalized FASTA files."""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from pathlib import Path

from .sequences import SequenceRecord, keep_most_common_length, normalize_sequence, normalize_to_min_length, read_fasta, write_fasta


GRAPHPRO_DATASET_NAMES = {
    "Bamy": "bacillus_amyloliquefaciens",
    "Cje": "campylobacter_jejuni",
    # The distributed records use accession NC_000922.1 and identify
    # Chlamydophila/Chlamydia pneumoniae CWL029.  The folder abbreviation is
    # therefore Cpne, not Clostridium phytofermentans.
    "Cpne": "chlamydophila_pneumoniae",
    "Ecol": "escherichia_coli",
    "human": "Human",
    "Lint": "leptospira_interrogans",
    "mouse": "Mouse",
    "Rcap": "rhodobacter_capsulatus",
}


@dataclass(frozen=True)
class FastaBuildResult:
    source: Path
    output: Path
    records: int
    sequence_length: int


def _records_from_fasta(path: Path) -> list[SequenceRecord]:
    return read_fasta(path)


def _records_from_gzip_fasta(path: Path) -> list[SequenceRecord]:
    records: list[SequenceRecord] = []
    identifier: str | None = None
    description = ""
    chunks: list[str] = []

    def flush() -> None:
        nonlocal identifier, description, chunks
        if identifier is None:
            return
        records.append(SequenceRecord(identifier, normalize_sequence("".join(chunks)), description))
        identifier = None
        description = ""
        chunks = []

    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                flush()
                header = line[1:]
                parts = header.split(maxsplit=1)
                identifier = parts[0] if parts else str(len(records))
                description = parts[1] if len(parts) > 1 else ""
            else:
                chunks.append(line)
        flush()
    return records


def _write_named(records: list[SequenceRecord], output_dir: Path, name: str, source: Path) -> FastaBuildResult:
    if not records:
        raise ValueError(f"no records generated for {source}")
    lengths = {len(record.sequence) for record in records}
    if len(lengths) != 1:
        raise ValueError(f"records still have variable lengths for {source}: {sorted(lengths)}")
    output = output_dir / f"{name}.fa"
    write_fasta(records, output)
    return FastaBuildResult(source, output, len(records), next(iter(lengths)))


def build_cnnprom_fastas(raw_dir: Path, output_dir: Path) -> list[FastaBuildResult]:
    """Convert CNNProm FASTA files into the common CapsProm FASTA naming scheme."""

    prokaryotic = {"Bacillus", "Ecoli"}
    results: list[FastaBuildResult] = []
    for source in sorted(raw_dir.glob("*.fa")):
        name = source.name
        class_name = "nonprom" if name.endswith("neg.fa") else "prom"
        dataset = name.replace("_neg.fa", "").replace("_pos.fa", "").replace(".fa", "")
        karyote = "prokaryotic" if any(token in dataset for token in prokaryotic) else "eukaryotic"
        records = _records_from_fasta(source)
        lengths = {len(record.sequence) for record in records}
        if len(lengths) != 1:
            raise ValueError(f"CNNProm sequences have variable lengths in {source}: {sorted(lengths)}")
        dataset_name = f"{class_name}-cnnprom-{karyote}-{dataset}-{len(records)}-{next(iter(lengths))}"
        results.append(_write_named(records, output_dir, dataset_name, source))
    return results


def build_graphpro_fastas(raw_dir: Path, output_dir: Path) -> list[FastaBuildResult]:
    """Convert GraphPro positive/negative folders into common FASTA files."""

    eukaryotic = {"human", "mouse"}
    results: list[FastaBuildResult] = []
    for folder, dataset in GRAPHPRO_DATASET_NAMES.items():
        karyote = "eukaryotic" if folder in eukaryotic else "prokaryotic"
        for raw_name, class_name in (("positive", "prom"), ("negative", "nonprom")):
            source = raw_dir / folder / raw_name
            records = normalize_to_min_length(_records_from_fasta(source))
            length = len(records[0].sequence) if records else 0
            dataset_name = f"{class_name}-graphpro-{karyote}-{dataset}-{len(records)}-{length}"
            results.append(_write_named(records, output_dir, dataset_name, source))
    return results


def build_bhandari_fastas(raw_dir: Path, output_dir: Path) -> list[FastaBuildResult]:
    """Convert Bhandari gzip FASTA files into common FASTA files."""

    results: list[FastaBuildResult] = []
    for source in sorted(raw_dir.glob("*.gz")):
        source_name = source.name.replace(".gz", "")
        karyote = "eukaryotic"
        class_name = "prom" if "_promoter" in source_name.lower() or "promoters" in source_name.lower() else "nonprom"
        records = keep_most_common_length(_records_from_gzip_fasta(source))
        length = len(records[0].sequence) if records else 0
        dataset_name = f"{class_name}-bhandari-{karyote}-{source_name}-{len(records)}-{length}"
        results.append(_write_named(records, output_dir, dataset_name, source))
    return results


def build_cdbprom_fastas(raw_dir: Path, output_dir: Path) -> list[FastaBuildResult]:
    """Convert CDBProm line-oriented TXT files into common FASTA files."""

    results: list[FastaBuildResult] = []
    for source in sorted(raw_dir.glob("*.txt")):
        if source.name.upper().startswith("README"):
            continue
        name = source.stem
        class_name = "nonprom" if "negative" in name else "prom"
        dataset = name.replace("negative", "").replace("positive", "").strip("_-")
        records = []
        for idx, line in enumerate(source.read_text(encoding="utf-8", errors="replace").splitlines()):
            seq = normalize_sequence(line)
            if seq:
                records.append(SequenceRecord(str(idx), seq, f"{class_name} prokaryotic sequence {idx}"))
        records = keep_most_common_length(records)
        length = len(records[0].sequence) if records else 0
        dataset_name = f"{class_name}-cdbprom-prokaryotic-{dataset}-{len(records)}-{length}"
        results.append(_write_named(records, output_dir, dataset_name, source))
    return results
