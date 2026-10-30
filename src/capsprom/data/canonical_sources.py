"""Parse acquired source files into one canonical, validated record table per collection."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

import yaml

from capsprom.data.acquisition import file_digests
from capsprom.state import write_json_atomic

CANONICAL_SCHEMA_VERSION = 1
DNA_ALPHABET = frozenset("ACGT")
FORMATS = ("fasta", "lines", "ipro_fasta", "label_csv")
CANONICAL_COLUMNS = (
    "record_id",
    "collection_id",
    "source",
    "organism",
    "domain",
    "source_file",
    "source_member",
    "record_index",
    "source_split",
    "source_class",
    "label",
    "original_header",
    "sequence",
    "length",
    "tss_index",
    "sequence_sha1",
    "strict_dna",
    "invalid_symbols",
    "case_normalized",
    "length_matches_expected",
    "duplicate_of",
    "cross_label_collision",
)
_IPRO_NEGATIVE_SUFFIXES = (("Convergent", "negative_intergenic"), ("CDS", "negative_cds"))


def load_canonicalization_config(path: Path) -> dict[str, Any]:
    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if set(config) != {"canonicalization", "collections"}:
        raise ValueError("canonicalization config must contain 'canonicalization' and 'collections'")
    ids = [c["collection_id"] for c in config["collections"]]
    if len(ids) != len(set(ids)):
        raise ValueError("collection_id values must be unique")
    for collection in config["collections"]:
        for item in collection["inputs"]:
            if item["format"] not in FORMATS:
                raise ValueError(f"{collection['collection_id']}: unsupported format {item['format']}")
            if item["format"] == "ipro_fasta":
                if not isinstance(item["expected_records"], dict):
                    raise ValueError(f"{collection['collection_id']}: ipro_fasta needs per-class counts")
            elif item.get("label") not in (0, 1) or not item.get("source_class"):
                raise ValueError(f"{collection['collection_id']}: inputs need label 0/1 and source_class")
            if item["format"] == "label_csv" and not item.get("source_label"):
                raise ValueError(f"{collection['collection_id']}: label_csv needs the declared source_label")
    return config


def _read_bytes(path: Path, member: str | None) -> bytes:
    if member is not None:
        with zipfile.ZipFile(path) as archive:
            return archive.read(member)
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == ".gz" else data


def parse_fasta(text: str) -> Iterator[tuple[str, str]]:
    """Yield (header, raw sequence) pairs; whitespace inside sequence lines is removed."""

    header: str | None = None
    chunks: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith(">"):
            if header is not None:
                yield header, "".join(chunks)
            header, chunks = line[1:].strip(), []
        elif header is None:
            raise ValueError("sequence data found before the first FASTA header")
        else:
            chunks.append("".join(line.split()))
    if header is not None:
        yield header, "".join(chunks)


def parse_lines(text: str) -> Iterator[tuple[str, str]]:
    for line in text.splitlines():
        if line.strip():
            yield "", "".join(line.split())


def parse_label_csv(text: str, source_label: str) -> Iterator[tuple[str, str]]:
    """Yield (source label, raw sequence) from two-field "label,sequence" rows.

    Every row must carry the declared source label, so that a file holding
    another class or a header row is rejected instead of being relabelled.
    """

    for number, row in enumerate(csv.reader(io.StringIO(text)), start=1):
        if not row:
            continue
        if len(row) != 2 or row[0] != source_label:
            raise ValueError(f"row {number}: expected '{source_label},<sequence>', found {row[:1]}")
        yield row[0], row[1]


def ipro_source_class(header: str) -> str:
    """Return the iPro-MP class encoded in a header such as '<species> CDS--12'."""

    name = header.rsplit("--", 1)[0]
    for suffix, source_class in _IPRO_NEGATIVE_SUFFIXES:
        if name.endswith(" " + suffix):
            return source_class
    return "positive"


def normalize_sequence(raw: str) -> tuple[str, bool, str]:
    """Return (uppercase sequence, whether case changed, sorted invalid symbols)."""

    sequence = "".join(raw.split())
    upper = sequence.upper()
    return upper, upper != sequence, "".join(sorted(set(upper) - DNA_ALPHABET))


def _input_records(
    item: dict[str, Any], acquired_root: Path, default_length: int | None
) -> Iterator[dict[str, Any]]:
    text = _read_bytes(acquired_root / item["file"], item.get("member")).decode("utf-8", "replace")
    if item["format"] == "label_csv":
        records = parse_label_csv(text, item["source_label"])
    else:
        records = (parse_lines if item["format"] == "lines" else parse_fasta)(text)
    expected_length = item.get("expected_length", default_length)
    for index, (header, raw) in enumerate(records):
        if item["format"] == "ipro_fasta":
            source_class = ipro_source_class(header)
            label = 1 if source_class == "positive" else 0
        else:
            source_class, label = item["source_class"], item["label"]
        sequence, case_normalized, invalid = normalize_sequence(raw)
        yield {
            "source_file": item["file"],
            "source_member": item.get("member", ""),
            "record_index": index,
            "source_split": item.get("source_split", "none"),
            "source_class": source_class,
            "label": label,
            "original_header": header,
            "sequence": sequence,
            "length": len(sequence),
            "tss_index": item.get("tss_index") if label == 1 else None,
            "sequence_sha1": hashlib.sha1(sequence.encode()).hexdigest(),
            "strict_dna": bool(sequence) and not invalid,
            "invalid_symbols": invalid,
            "case_normalized": case_normalized,
            "length_matches_expected": (
                None if expected_length is None else len(sequence) == expected_length
            ),
        }


def build_collection_rows(collection: dict[str, Any], acquired_root: Path) -> list[dict[str, Any]]:
    """Parse every input of a collection and annotate duplicates and label collisions."""

    rows: list[dict[str, Any]] = []
    for item in collection["inputs"]:
        for record in _input_records(item, acquired_root, collection.get("expected_length")):
            file_key = item["file"] + (f"!{item['member']}" if item.get("member") else "")
            record["record_id"] = f"{collection['collection_id']}:{file_key}:{record['record_index']:07d}"
            rows.append(record)

    first_by_label: dict[tuple[int, str], str] = {}
    labels_by_sequence: dict[str, set[int]] = {}
    for row in rows:
        labels_by_sequence.setdefault(row["sequence"], set()).add(row["label"])
    for row in rows:
        key = (row["label"], row["sequence"])
        row["duplicate_of"] = first_by_label.setdefault(key, row["record_id"])
        if row["duplicate_of"] == row["record_id"]:
            row["duplicate_of"] = ""
        row["cross_label_collision"] = len(labels_by_sequence[row["sequence"]]) > 1
        row.update(
            collection_id=collection["collection_id"],
            source=collection["source"],
            organism=collection.get("organism") or "",
            domain=collection["domain"],
        )
    return rows


def _expected_by_class(collection: dict[str, Any]) -> Counter:
    expected: Counter = Counter()
    for item in collection["inputs"]:
        if isinstance(item["expected_records"], dict):
            expected.update(item["expected_records"])
        else:
            expected[item["source_class"]] += item["expected_records"]
    return expected


def _legacy_sequences(collection: dict[str, Any], repo_root: Path) -> dict[str, Counter]:
    by_class: dict[str, Counter] = {}
    for item in collection.get("legacy_inputs", []):
        text = _read_bytes(repo_root / item["path"], item.get("member")).decode("utf-8", "replace")
        parser = parse_lines if item["format"] == "lines" else parse_fasta
        for header, raw in parser(text):
            source_class = (
                ipro_source_class(header) if item["format"] == "ipro_fasta" else item["source_class"]
            )
            by_class.setdefault(source_class, Counter())[normalize_sequence(raw)[0]] += 1
    return by_class


def validate_collection(
    collection: dict[str, Any], rows: list[dict[str, Any]], repo_root: Path
) -> dict[str, Any]:
    """Summarize integrity checks; only release counts and legacy parity decide the status."""

    observed = Counter(row["source_class"] for row in rows)
    expected = _expected_by_class(collection)
    lengths = Counter(row["length"] for row in rows)
    report: dict[str, Any] = {
        "records": len(rows),
        "records_by_class": dict(sorted(observed.items())),
        "expected_release_records_by_class": dict(sorted(expected.items())),
        "release_counts_match": observed == expected,
        "most_common_lengths": [[length, n] for length, n in lengths.most_common(5)],
        "records_not_expected_length": sum(row["length_matches_expected"] is False for row in rows),
        "non_strict_dna_records": sum(not row["strict_dna"] for row in rows),
        "case_normalized_records": sum(row["case_normalized"] for row in rows),
        "duplicate_records": sum(bool(row["duplicate_of"]) for row in rows),
        "cross_label_collision_records": sum(row["cross_label_collision"] for row in rows),
        "unique_sequences": len({row["sequence"] for row in rows}),
    }
    publication = collection.get("publication_counts") or {}
    report["publication_count_discrepancies"] = {
        name: {"publication": count, "release": observed.get(name, 0)}
        for name, count in sorted(publication.items())
        if observed.get(name, 0) != count
    }
    legacy = _legacy_sequences(collection, repo_root)
    if legacy:
        current: dict[str, Counter] = {}
        for row in rows:
            current.setdefault(row["source_class"], Counter())[row["sequence"]] += 1
        report["legacy_sequence_match"] = {
            name: current.get(name, Counter()) == counter for name, counter in sorted(legacy.items())
        }
    legacy_ok = all(report.get("legacy_sequence_match", {}).values())
    report["status"] = "pass" if report["release_counts_match"] and legacy_ok else "fail"
    return report


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_canonical_csv_gz(rows: list[dict[str, Any]], path: Path) -> None:
    """Write a byte-reproducible gzip CSV (fixed mtime, no embedded filename) atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                    writer = csv.writer(text, lineterminator="\n")
                    writer.writerow(CANONICAL_COLUMNS)
                    for row in rows:
                        writer.writerow([_format_value(row[column]) for column in CANONICAL_COLUMNS])
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _input_digests(collection: dict[str, Any], acquisition: dict[str, Any], root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    for item in collection["inputs"]:
        recorded = acquisition["files"].get(item["file"])
        if recorded is None:
            raise ValueError(f"{collection['collection_id']}: {item['file']} is not in the acquisition manifest")
        current = file_digests(root / item["file"])["sha256"]
        if current != recorded["sha256"]:
            raise ValueError(f"{item['file']}: acquired file changed since acquisition")
        digests[item["file"]] = current
    return digests


def canonicalize_sources(
    config_path: Path,
    repo_root: Path,
    *,
    only_collections: set[str] | None = None,
) -> dict[str, Any]:
    """Build every collection, persisting the manifest atomically after each one."""

    config = load_canonicalization_config(config_path)
    settings = config["canonicalization"]
    acquired_root = repo_root / settings["acquired_root"]
    acquisition_manifest_path = repo_root / settings["acquisition_manifest"]
    acquisition = json.loads(acquisition_manifest_path.read_text(encoding="utf-8"))
    output_dir = repo_root / settings["output_dir"]
    manifest_path = output_dir / "canonical_manifest.json"
    config_sha256 = hashlib.sha256(Path(config_path).read_bytes()).hexdigest()
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["config_sha256"] != config_sha256:
            raise ValueError("canonical manifest belongs to a different config; create a new version")
    else:
        manifest = {
            "schema_version": CANONICAL_SCHEMA_VERSION,
            "canonicalization": settings["name"],
            "config_sha256": config_sha256,
            "columns": list(CANONICAL_COLUMNS),
            "collections": {},
        }

    summary = {"built": 0, "skipped_unchanged": 0, "failed_validation": []}
    for collection in config["collections"]:
        collection_id = collection["collection_id"]
        if only_collections is not None and collection_id not in only_collections:
            continue
        inputs = _input_digests(collection, acquisition, acquired_root)
        output = output_dir / f"{collection_id}.csv.gz"
        recorded = manifest["collections"].get(collection_id)
        if (
            recorded
            and recorded["input_sha256"] == inputs
            and output.exists()
            and file_digests(output)["sha256"] == recorded["output_sha256"]
        ):
            summary["skipped_unchanged"] += 1
            if recorded["validation"]["status"] != "pass":
                summary["failed_validation"].append(collection_id)
            continue
        rows = build_collection_rows(collection, acquired_root)
        validation = validate_collection(collection, rows, repo_root)
        write_canonical_csv_gz(rows, output)
        manifest["collections"][collection_id] = {
            "source": collection["source"],
            "output": output.relative_to(repo_root).as_posix(),
            "output_sha256": file_digests(output)["sha256"],
            "input_sha256": inputs,
            "notes": collection.get("notes", ""),
            "validation": validation,
        }
        write_json_atomic(manifest_path, manifest)
        summary["built"] += 1
        if validation["status"] != "pass":
            summary["failed_validation"].append(collection_id)
    return summary
