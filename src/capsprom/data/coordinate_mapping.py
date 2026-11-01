"""Persisted, resumable coordinate mapping of canonical records (protocol Stage B2).

One shard is one collection on one reference assembly. Each shard writes a record
table and a locus table, byte-reproducibly, and the manifest is rewritten
atomically after every shard. A rerun skips shards whose inputs and outputs are
unchanged.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from capsprom.data.exact_mapping import extract, find_exact, non_acgt_count, read_fasta
from capsprom.state import write_json_atomic

RECORD_COLUMNS = (
    "mapping_version", "record_id", "collection_id", "sequence_sha1", "length", "source_class", "label",
    "organism_declared", "assembly_accession", "assembly_evidence", "declared_assembly",
    "declared_coordinate_text", "declared_check", "method_id", "n_candidates", "n_candidates_truncated",
    "status", "status_reason",
)
LOCUS_COLUMNS = (
    "record_id", "locus_rank", "assembly_accession", "contig_accession", "start", "end", "strand",
    "match_class", "edit_distance", "ambiguous_bases_reference", "coordinate_source", "reference_file_sha256",
)
_TRUSTED_ASSEMBLY = {"declared", "verified"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv_gz(columns: tuple[str, ...], rows: list[dict[str, Any]], path: Path) -> None:
    """Write a byte-reproducible gzip CSV (fixed mtime, no embedded name) atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                    writer = csv.writer(text, lineterminator="\n")
                    writer.writerow(columns)
                    for row in rows:
                        writer.writerow([row[column] for column in columns])
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def record_status(n_candidates: int, assembly_evidence: str, label_conflict: bool) -> tuple[str, list[str]]:
    """Apply the protocol's record-status rules for exact search."""

    reasons = ["label_conflict"] if label_conflict else []
    if n_candidates == 0:
        return "unmapped", ["no_candidate", *reasons]
    if n_candidates > 1:
        return "ambiguous", ["multiple_loci", *reasons]
    if assembly_evidence == "conflicting":
        return "inconsistent", ["assembly_conflicting", *reasons]
    if assembly_evidence not in _TRUSTED_ASSEMBLY:
        return "inconsistent", ["assembly_mismatch", *reasons]
    return "verified", reasons


def map_collection(
    canonical_rows: list[dict[str, str]],
    contigs: dict[str, str],
    entry: dict[str, Any],
    mapping_version: str,
    reference_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map every record of one collection and return its record and locus rows."""

    cache: dict[str, tuple] = {}
    records: list[dict[str, Any]] = []
    loci_rows: list[dict[str, Any]] = []
    for row in sorted(canonical_rows, key=lambda item: item["record_id"]):
        sequence = row["sequence"].upper()
        label_conflict = row["cross_label_collision"] == "true"
        if non_acgt_count(sequence):
            loci = ()
            status, reasons = "not_evaluated", ["ambiguous_bases", *(["label_conflict"] if label_conflict else [])]
        else:
            if sequence not in cache:
                cache[sequence] = find_exact(sequence, contigs)
            loci = cache[sequence]
            for locus in loci:
                if locus.match_class == "exact" and extract(contigs, locus) != sequence:
                    raise RuntimeError(f"round trip failed for {row['record_id']}")
            status, reasons = record_status(len(loci), entry["assembly_evidence"], label_conflict)
        records.append({
            "mapping_version": mapping_version,
            "record_id": row["record_id"],
            "collection_id": row["collection_id"],
            "sequence_sha1": row["sequence_sha1"],
            "length": row["length"],
            "source_class": row["source_class"],
            "label": row["label"],
            "organism_declared": row["organism"],
            "assembly_accession": entry["assembly"],
            "assembly_evidence": entry["assembly_evidence"],
            "declared_assembly": entry.get("declared_assembly", ""),
            "declared_coordinate_text": row["original_header"],
            "declared_check": "unparsed",
            "method_id": "exact_search",
            "n_candidates": len(loci),
            "n_candidates_truncated": "false",
            "status": status,
            "status_reason": ";".join(reasons),
        })
        for rank, locus in enumerate(loci, start=1):
            loci_rows.append({
                "record_id": row["record_id"],
                "locus_rank": rank,
                "assembly_accession": entry["assembly"],
                "contig_accession": locus.contig,
                "start": locus.start,
                "end": locus.end,
                "strand": locus.strand,
                "match_class": locus.match_class,
                "edit_distance": 0,
                "ambiguous_bases_reference": non_acgt_count(contigs[locus.contig][locus.start : locus.end]),
                "coordinate_source": "exact_search",
                "reference_file_sha256": reference_sha256,
            })
    return records, loci_rows


def _code_state(repo_root: Path) -> dict[str, Any]:
    def git(*args: str) -> str:
        result = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=False)
        return result.stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "clean": git("status", "--porcelain") == "",
        "module_sha256": _sha256(Path(__file__)),
        "exact_mapping_sha256": _sha256(Path(__file__).with_name("exact_mapping.py")),
    }


def run_mapping(config_path: Path, repo_root: Path, *, only: set[str] | None = None) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    settings = config["mapping"]
    config_sha256 = _sha256(config_path)
    output_dir = repo_root / settings["output_dir"]
    manifest_path = output_dir / "mapping_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["config_sha256"] != config_sha256:
            raise ValueError("mapping manifest belongs to a different config; create a new version")
    else:
        manifest = {"mapping": settings["name"], "config_sha256": config_sha256, "shards": {}, "runs": []}
    canonical_manifest = json.loads((repo_root / settings["canonical_manifest"]).read_text(encoding="utf-8"))
    run = {"started_utc": datetime.now(UTC).isoformat(timespec="seconds"), "code": _code_state(repo_root),
           "shard_filter": sorted(only) if only else None, "built": [], "skipped": []}
    mapping_version = f"{settings['name']}@{config_sha256[:16]}"
    run["status"] = "failed"
    try:
        for entry in config["collections"]:
            collection_id = entry["collection_id"]
            if only is not None and collection_id not in only:
                continue
            canonical_path = repo_root / settings["canonical_root"] / f"{collection_id}.csv.gz"
            canonical_sha256 = _sha256(canonical_path)
            recorded_canonical = canonical_manifest["collections"][collection_id]["output_sha256"]
            if canonical_sha256 != recorded_canonical:
                raise ValueError(f"{collection_id}: canonical table differs from its manifest")
            acquisition_root = repo_root / "data/acquired" / entry["acquisition"]
            acquisition = json.loads((acquisition_root / "acquisition_manifest.json").read_text(encoding="utf-8"))
            fasta_key = entry.get("reference_file") or next(
                key for key in acquisition["files"]
                if key.startswith(f"{entry['source_id']}/") and "_genomic.fna" in key
            )
            reference_path = acquisition_root / fasta_key
            reference_sha256 = _sha256(reference_path)
            if reference_sha256 != acquisition["files"][fasta_key]["sha256"]:
                raise ValueError(f"{fasta_key}: reference changed since acquisition")
            inputs = {"canonical_sha256": canonical_sha256, "reference_sha256": reference_sha256,
                      "config_sha256": config_sha256}
            record_path = output_dir / "records" / f"{collection_id}.csv.gz"
            locus_path = output_dir / "loci" / f"{collection_id}.csv.gz"
            recorded = manifest["shards"].get(collection_id)
            if (recorded and recorded["inputs"] == inputs and record_path.exists() and locus_path.exists()
                    and _sha256(record_path) == recorded["records_sha256"]
                    and _sha256(locus_path) == recorded["loci_sha256"]):
                run["skipped"].append(collection_id)
                continue
            with gzip.open(canonical_path, "rt", encoding="utf-8", newline="") as handle:
                canonical_rows = list(csv.DictReader(handle))
            records, loci = map_collection(canonical_rows, read_fasta(reference_path), entry, mapping_version,
                                           reference_sha256)
            write_csv_gz(RECORD_COLUMNS, records, record_path)
            write_csv_gz(LOCUS_COLUMNS, loci, locus_path)
            counts: dict[str, int] = {}
            for record in records:
                counts[record["status"]] = counts.get(record["status"], 0) + 1
            if sum(int(record["n_candidates"]) for record in records) != len(loci):
                raise RuntimeError(f"{collection_id}: candidate count differs from locus rows")
            manifest["shards"][collection_id] = {
                "inputs": inputs, "reference_file": fasta_key, "assembly": entry["assembly"],
                "records_sha256": _sha256(record_path), "loci_sha256": _sha256(locus_path),
                "records": len(records), "loci": len(loci), "status_counts": dict(sorted(counts.items())),
            }
            run["built"].append(collection_id)
            write_json_atomic(manifest_path, manifest)
        run["status"] = "completed"
    finally:
        run["finished_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
        manifest["runs"].append(run)
        write_json_atomic(manifest_path, manifest)
    return {"built": run["built"], "skipped": run["skipped"]}
