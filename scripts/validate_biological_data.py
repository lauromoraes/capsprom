#!/usr/bin/env python3
"""Validate biological sequence files in the CapsProm data directory."""

from __future__ import annotations

import csv
import gzip
import re
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, TextIO

DNA = set("ACGT")
FASTA_EXTENSIONS = {".fa", ".fasta", ".fna"}
SEQUENCE_CSV_COLUMNS = {"sequence", "label"}
COUNT_RE = re.compile(r"-p-(?P<p>\d+)-n-(?P<n>\d+)-(?P<partition>[^./]+)\.csv$", re.IGNORECASE)
LEN_RE = re.compile(r"-(?P<len>\d+)\.(?:fa|fasta|fna)(?:\.gz)?$", re.IGNORECASE)
IGNORED_PATH_MARKERS = ("raw/Nova pasta/predictions_ecoli",)
MAX_ISSUES_PER_FILE = 25


@dataclass
class FileResult:
    path: str
    kind: str
    status: str
    records: int = 0
    min_len: int | None = None
    max_len: int | None = None
    labels: Counter = field(default_factory=Counter)
    issues: list[str] = field(default_factory=list)

    def add_length(self, value: int) -> None:
        self.records += 1
        self.min_len = value if self.min_len is None else min(self.min_len, value)
        self.max_len = value if self.max_len is None else max(self.max_len, value)

    def issue(self, message: str) -> None:
        if len(self.issues) < MAX_ISSUES_PER_FILE:
            self.issues.append(message)


def open_text(path: Path) -> TextIO:
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace", newline="")


def expected_length_from_name(path: Path) -> int | None:
    match = LEN_RE.search(path.name)
    return int(match.group("len")) if match else None


def clean_sequence(seq: str) -> str:
    return re.sub(r"\s+", "", seq).upper()


def validate_dna(seq: str, result: FileResult, context: str) -> int:
    cleaned = clean_sequence(seq)
    if not cleaned:
        result.issue(f"{context}: empty sequence")
        return 0
    invalid = sorted(set(cleaned) - DNA)
    if invalid:
        result.issue(f"{context}: invalid DNA symbols {''.join(invalid)}")
    result.add_length(len(cleaned))
    return len(cleaned)


def validate_fasta_stream(handle: TextIO, path: Path, root: Path, kind: str) -> FileResult:
    result = FileResult(str(path.relative_to(root)), kind, "pass")
    expected = expected_length_from_name(path)
    current: list[str] = []
    current_name = "record 1"

    def flush() -> None:
        nonlocal current, current_name
        if not current:
            return
        observed = validate_dna("".join(current), result, current_name)
        if expected is not None and observed != expected:
            result.issue(f"{current_name}: length {observed}, expected {expected} from filename")
        current = []

    for line in handle:
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            flush()
            current_name = line[1:100] or f"record {result.records + 1}"
        else:
            current.append(line)
    flush()
    if result.records == 0:
        result.issue("no FASTA records found")
    result.status = "pass" if not result.issues else "fail"
    return result


def validate_fasta(path: Path, root: Path) -> FileResult:
    try:
        with open_text(path) as handle:
            return validate_fasta_stream(handle, path, root, "fasta")
    except Exception as exc:
        return FileResult(str(path.relative_to(root)), "fasta", "fail", issues=[f"could not read FASTA: {exc}"])


def validate_sequence_csv(path: Path, root: Path, fieldnames: list[str]) -> FileResult:
    result = FileResult(str(path.relative_to(root)), "sequence_csv", "pass")
    if "sequence" not in fieldnames or "label" not in fieldnames:
        result.issue("missing sequence or label column")
        result.status = "fail"
        return result

    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for idx, row in enumerate(reader, start=2):
                seq = (row.get("sequence") or "").strip()
                label = (row.get("label") or "").strip()
                observed = validate_dna(seq, result, f"line {idx}")
                if observed != 81:
                    result.issue(f"line {idx}: length {observed}, expected 81")
                if label not in {"0", "1"}:
                    result.issue(f"line {idx}: invalid label {label!r}")
                else:
                    result.labels[label] += 1
    except Exception as exc:
        result.issue(f"could not read CSV: {exc}")

    match = COUNT_RE.search(path.name)
    if match:
        expected_p = int(match.group("p"))
        expected_n = int(match.group("n"))
        observed_p = result.labels.get("1", 0)
        observed_n = result.labels.get("0", 0)
        if observed_p != expected_p or observed_n != expected_n:
            result.issue(
                f"filename counts p={expected_p}, n={expected_n}; observed p={observed_p}, n={observed_n}"
            )

    result.status = "pass" if not result.issues else "fail"
    return result


def classify_csv(path: Path) -> tuple[str, list[str]]:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
    except Exception:
        return "unreadable_csv", []
    normalized = [h.strip() for h in header]
    if SEQUENCE_CSV_COLUMNS.issubset(set(normalized)):
        return "sequence_csv", normalized
    return "non_sequence_csv", normalized


def looks_like_fasta(path: Path) -> bool:
    try:
        with open_text(path) as handle:
            for line in handle:
                line = line.strip()
                if line:
                    return line.startswith(">")
    except Exception:
        return False
    return False


def validate_text_sequence_file(path: Path, root: Path) -> FileResult:
    rel = str(path.relative_to(root))
    if looks_like_fasta(path):
        try:
            with open_text(path) as handle:
                return validate_fasta_stream(handle, path, root, "fasta_txt")
        except Exception as exc:
            return FileResult(rel, "fasta_txt", "fail", issues=[f"could not read FASTA-like TXT: {exc}"])

    result = FileResult(rel, "line_sequence_txt", "pass")
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for idx, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                cleaned = clean_sequence(line)
                if sorted(set(cleaned) - DNA):
                    result.issue(f"line {idx}: not a plain DNA sequence line")
                    continue
                validate_dna(cleaned, result, f"line {idx}")
    except Exception as exc:
        result.issue(f"could not read TXT: {exc}")
    if result.records == 0 and not result.issues:
        result.issue("no sequence lines found")
    result.status = "pass" if not result.issues else "fail"
    return result


def validate_unknown_gzip(path: Path, root: Path) -> FileResult:
    rel = str(path.relative_to(root))
    try:
        if looks_like_fasta(path):
            with open_text(path) as handle:
                return validate_fasta_stream(handle, path, root, "fasta_gzip")
        result = FileResult(rel, "line_sequence_gzip", "pass")
        with open_text(path) as handle:
            for idx, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                cleaned = clean_sequence(line)
                if sorted(set(cleaned) - DNA):
                    result.issue(f"line {idx}: not a plain DNA sequence line")
                    continue
                validate_dna(cleaned, result, f"line {idx}")
        result.status = "pass" if result.records and not result.issues else "fail"
        if result.records == 0 and not result.issues:
            result.issue("no sequence lines found")
        return result
    except Exception as exc:
        return FileResult(rel, "compressed_unknown", "review", issues=[f"could not validate gzip content: {exc}"])


def inspect_zip(path: Path, root: Path) -> FileResult:
    result = FileResult(str(path.relative_to(root)), "zip", "review")
    try:
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
        result.records = len(names)
        result.issue("archive inventoried but not expanded during validation")
        if names[:5]:
            result.issue("first entries: " + ", ".join(names[:5]))
    except Exception as exc:
        result.issue(f"could not inspect ZIP: {exc}")
        result.status = "fail"
    return result


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.as_posix()
            try:
                rel = path.relative_to(root).as_posix()
            except ValueError:
                pass
            if any(marker in rel for marker in IGNORED_PATH_MARKERS):
                continue
            yield path


def validate(root: Path) -> list[FileResult]:
    results: list[FileResult] = []
    for path in iter_files(root):
        suffixes = [s.lower() for s in path.suffixes]
        suffix = path.suffix.lower()
        rel = str(path.relative_to(root))
        if suffix in FASTA_EXTENSIONS or (len(suffixes) >= 2 and suffixes[-2] in FASTA_EXTENSIONS and suffixes[-1] == ".gz"):
            results.append(validate_fasta(path, root))
        elif suffix == ".csv":
            kind, header = classify_csv(path)
            if kind == "sequence_csv":
                results.append(validate_sequence_csv(path, root, header))
            elif kind == "unreadable_csv":
                results.append(FileResult(rel, "csv", "fail", issues=["could not read CSV header"]))
            else:
                results.append(FileResult(rel, "non_sequence_csv", "not_applicable"))
        elif suffix == ".txt":
            if path.name.upper().startswith("README"):
                results.append(FileResult(rel, "text_documentation", "not_applicable"))
            else:
                results.append(validate_text_sequence_file(path, root))
        elif suffix == ".gz":
            results.append(validate_unknown_gzip(path, root))
        elif suffix == ".zip":
            results.append(inspect_zip(path, root))
        elif suffix in {".tsv", ".md", ".ipynb", ".py"} or not suffix:
            results.append(FileResult(rel, "non_sequence_artifact", "not_applicable"))
        else:
            results.append(FileResult(rel, "unknown", "review", issues=["unknown file type"]))
    return results


def write_report(results: list[FileResult], out: Path) -> None:
    by_status = Counter(r.status for r in results)
    by_kind = Counter(r.kind for r in results)
    sequence_kinds = {"fasta", "fasta_txt", "fasta_gzip", "sequence_csv", "line_sequence_txt", "line_sequence_gzip"}
    validated = [r for r in results if r.kind in sequence_kinds]
    failed = [r for r in validated if r.status == "fail"]
    review = [r for r in results if r.status == "review"]
    passed = [r for r in validated if r.status == "pass"]

    lines: list[str] = []
    lines.append("# Biological Data Validation Report")
    lines.append("")
    lines.append("This report validates sequence-bearing files in `data/` for DNA alphabet constraints, expected 81 bp processed CSV sequences, binary labels, and filename count consistency where available.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total files inspected: {len(results)}")
    lines.append(f"- Sequence-bearing files validated: {len(validated)}")
    lines.append(f"- Sequence-bearing files passed: {len(passed)}")
    lines.append(f"- Sequence-bearing files failed: {len(failed)}")
    lines.append(f"- Files requiring manual review: {len(review)}")
    if passed:
        total_records = sum(r.records for r in passed)
        lines.append(f"- Valid sequence records in passed files: {total_records}")
    lines.append("")
    lines.append("## Status Counts")
    lines.append("")
    for key, value in sorted(by_status.items()):
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    lines.append("## File Kind Counts")
    lines.append("")
    for key, value in sorted(by_kind.items()):
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    lines.append("## Failures")
    lines.append("")
    if failed:
        for r in failed:
            lines.append(f"### `{r.path}`")
            lines.append("")
            lines.append(f"- Kind: `{r.kind}`")
            lines.append(f"- Records read: {r.records}")
            if r.min_len is not None:
                lines.append(f"- Length range: {r.min_len}-{r.max_len}")
            if r.labels:
                lines.append(f"- Labels: {dict(r.labels)}")
            for issue in r.issues:
                lines.append(f"- Issue: {issue}")
            lines.append("")
    else:
        lines.append("No sequence-bearing files failed validation.")
        lines.append("")
    lines.append("## Manual Review Items")
    lines.append("")
    if review:
        for r in review:
            lines.append(f"- `{r.path}` ({r.kind}, records/items: {r.records}): {'; '.join(r.issues[:3])}")
    else:
        lines.append("No files require manual review.")
    lines.append("")
    lines.append("## Scope Notes")
    lines.append("")
    lines.append("- Processed CSV files with `sequence,label` were checked for DNA alphabet, 81 bp length, binary labels, and filename count consistency.")
    lines.append("- FASTA, FASTA-like TXT, and gzip-compressed sequence files were checked for DNA alphabet. Fixed length was enforced only when an expected length was encoded in the filename.")
    lines.append("- Raw TXT files with one DNA sequence per line were checked for DNA alphabet, without fixed-length enforcement because raw sources may contain longer windows before cropping.")
    lines.append("- Numeric feature CSVs, TSV physicochemical references, notebooks, scripts, and documentation were classified as not applicable for direct biological sequence validation.")
    lines.append("- The `predictions_ecoli` folder was explicitly ignored by request and is outside this validation report.")
    lines.append("- ZIP archives were inventoried but not expanded during validation; use extracted, named source directories for experimental inputs.")
    lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("data")
    out = Path(argv[2]) if len(argv) > 2 else Path("docs/data_validation_report.md")
    results = validate(root)
    write_report(results, out)
    sequence_kinds = {"fasta", "fasta_txt", "fasta_gzip", "sequence_csv", "line_sequence_txt", "line_sequence_gzip"}
    failed = [r for r in results if r.kind in sequence_kinds and r.status == "fail"]
    review = [r for r in results if r.status == "review"]
    print(f"inspected={len(results)} sequence_failures={len(failed)} review_items={len(review)} report={out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
