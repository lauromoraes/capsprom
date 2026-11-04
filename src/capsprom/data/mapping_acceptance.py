"""Acceptance audit of a completed coordinate mapping (protocol validation criteria).

Reads the persisted record and locus tables of one mapping version; it never maps
again. It checks coverage and consistency (criteria 1-2), applies declared
coordinate rules (Stage B1) where a source rule is frozen, records whether the
alignment fallback (B3) has any input, and draws a stratified sample for the
independent manual audit (criterion 8).
"""

from __future__ import annotations

import csv
import gzip
import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

ECOLI_NC_000913_2_LENGTH = 4_639_675
_UPSTREAM = 60


def read_csv_gz(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def declared_integer(text: str) -> int | None:
    """Return the trailing integer of a CNNProm header (``...__<int>`` or ``<int>``)."""

    tail = text.rsplit("__", 1)[-1].strip()
    return int(tail) if tail.isdigit() else None


def expected_cnnprom_ecoli_integer(label: int, start: int, end: int, strand: str) -> int:
    """Header integer predicted by the F-098 rule for a locus on NC_000913.2.

    Positives: 1-based TSS, with the TSS at window index 60 in transcript
    orientation. Negatives: 0-based window start + 60, measured on the forward
    sequence (plus) or on the reverse complement of the whole sequence (minus).
    """

    if strand not in {"+", "-"}:
        raise ValueError(f"strand must be + or -, got {strand!r}")
    if label == 1:
        tss0 = start + _UPSTREAM if strand == "+" else end - 1 - _UPSTREAM
        return tss0 + 1
    if strand == "+":
        return start + _UPSTREAM
    return ECOLI_NC_000913_2_LENGTH - end + _UPSTREAM


def b1_cnnprom_ecoli(records: list[dict[str, str]], loci: list[dict[str, str]]) -> dict[str, Any]:
    """Compare declared header integers with every verified single locus (F-098 rule)."""

    by_record = {row["record_id"]: row for row in loci if row["locus_rank"] == "1"}
    counts: Counter[str] = Counter()
    mismatches: list[str] = []
    for record in records:
        if record["status"] != "verified":
            counts[f"skipped_{record['status']}"] += 1
            continue
        declared = declared_integer(record["declared_coordinate_text"])
        if declared is None:
            counts["unparsed"] += 1
            continue
        locus = by_record[record["record_id"]]
        expected = expected_cnnprom_ecoli_integer(
            int(record["label"]), int(locus["start"]), int(locus["end"]), locus["strand"]
        )
        key = "positive" if record["label"] == "1" else "negative"
        if expected == declared:
            counts[f"{key}_match"] += 1
            if key == "positive":
                header_strand = record["declared_coordinate_text"].split("__")[-2]
                wanted = "forward" if locus["strand"] == "+" else "reverse"
                counts["positive_strand_match" if header_strand == wanted else "positive_strand_mismatch"] += 1
        else:
            counts[f"{key}_mismatch"] += 1
            mismatches.append(record["record_id"])
    return {"rule": "cnnprom_ecoli_f098", "counts": dict(sorted(counts.items())), "mismatches": mismatches}


def coverage_and_consistency(records: list[dict[str, str]], loci: list[dict[str, str]]) -> dict[str, Any]:
    """Criteria 1-2: unique records, candidate counts equal locus rows, status agrees."""

    ids = [row["record_id"] for row in records]
    per_record = Counter(row["record_id"] for row in loci)
    violations: Counter[str] = Counter()
    for row in records:
        n = int(row["n_candidates"])
        truncated = row["n_candidates_truncated"] == "true"
        if not truncated and per_record.get(row["record_id"], 0) != n:
            violations["n_candidates_ne_locus_rows"] += 1
        if row["status"] == "verified" and n != 1:
            violations["verified_not_single"] += 1
        if row["status"] == "ambiguous" and n < 2 and not truncated:
            violations["ambiguous_lt_two"] += 1
    orphan = set(per_record) - set(ids)
    return {
        "records": len(ids),
        "duplicate_record_ids": len(ids) - len(set(ids)),
        "orphan_loci_records": len(orphan),
        "status_counts": dict(sorted(Counter(row["status"] for row in records).items())),
        "violations": dict(sorted(violations.items())),
    }


def b3_input(records: list[dict[str, str]]) -> int:
    """Number of records B3 would receive: evaluated strict-DNA records with no exact hit."""

    return sum(1 for row in records if row["status"] == "unmapped")


def sample_rank(record_id: str) -> str:
    return hashlib.sha256(record_id.encode("utf-8")).hexdigest()


def stratified_sample(
    records_by_collection: dict[str, list[dict[str, str]]], per_stratum: int
) -> list[dict[str, str]]:
    """Lowest SHA-256 ranks per (collection, status, label) stratum."""

    sample: list[dict[str, str]] = []
    for collection in sorted(records_by_collection):
        strata: dict[tuple[str, str], list[dict[str, str]]] = {}
        for row in records_by_collection[collection]:
            strata.setdefault((row["status"], row["label"]), []).append(row)
        for key in sorted(strata):
            chosen = sorted(strata[key], key=lambda row: sample_rank(row["record_id"]))[:per_stratum]
            sample.extend(chosen)
    return sample
