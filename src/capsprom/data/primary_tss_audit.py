"""Deterministic sampling for primary-source TSS coordinate audits."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
from pathlib import Path
import re
from typing import Iterable
from xml.etree import ElementTree
from zipfile import ZipFile


@dataclass(frozen=True)
class TssBedRow:
    """One BED6 TSS row together with its stable source position."""

    contig: str
    start: int
    end: int
    name: str
    score: str
    strand: str
    source_row: int


@dataclass(frozen=True)
class PrimaryTssRow:
    """A TSS coordinate read from a primary publication supplement."""

    position_1based: int
    strand: str
    source_sheet: str
    source_row: int


_SPREADSHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_RELATIONSHIP_ID = (
    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
)


def _xlsx_sheet_rows(path: Path, sheet_name: str) -> list[dict[str, str]]:
    """Read the small OOXML subset needed by the source audit."""

    with ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared_strings = [
                "".join(node.text or "" for node in item.iter(_SPREADSHEET_NS + "t"))
                for item in root
            ]
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            relationship.attrib["Id"]: relationship.attrib["Target"]
            for relationship in relationships
        }
        sheets = workbook.find(_SPREADSHEET_NS + "sheets")
        if sheets is None:
            raise ValueError(f"{path} has no worksheets")
        sheet = next(
            (item for item in sheets if item.attrib.get("name") == sheet_name), None
        )
        if sheet is None:
            raise ValueError(f"{path} has no sheet {sheet_name!r}")
        target = targets[sheet.attrib[_RELATIONSHIP_ID]]
        if not target.startswith("xl/"):
            target = "xl/" + target.lstrip("/")
        worksheet = ElementTree.fromstring(archive.read(target))
        rows: list[dict[str, str]] = []
        for row in worksheet.iter(_SPREADSHEET_NS + "row"):
            cells: dict[str, str] = {}
            for cell in row.findall(_SPREADSHEET_NS + "c"):
                match = re.match(r"[A-Z]+", cell.attrib.get("r", ""))
                if match is None:
                    continue
                value_node = cell.find(_SPREADSHEET_NS + "v")
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                cells[match.group()] = value
            rows.append(cells)
        return rows


def read_primary_tss_xlsx(
    path: Path,
    *,
    sheets: Iterable[str],
    position_column: str,
    strand_column: str,
) -> list[PrimaryTssRow]:
    """Read coordinate/strand pairs from selected primary-source worksheets."""

    result = []
    for sheet_name in sheets:
        for source_row, cells in enumerate(
            _xlsx_sheet_rows(path, sheet_name), start=1
        ):
            position_text = cells.get(position_column, "")
            strand = cells.get(strand_column, "").strip("'\"")
            try:
                position = int(float(position_text))
            except ValueError:
                continue
            if position < 1 or strand not in {"+", "-"}:
                continue
            result.append(PrimaryTssRow(position, strand, sheet_name, source_row))
    if not result:
        raise ValueError(f"{path} contains no usable TSS rows")
    return result


def read_frozen_sample(path: Path) -> list[dict[str, str]]:
    """Read the immutable selected-row ledger."""

    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def compare_sample_to_primary(
    sample_rows: Iterable[dict[str, str]],
    primary_rows: Iterable[PrimaryTssRow],
) -> list[dict[str, object]]:
    """Compare BED0 point starts with publication 1-based TSS coordinates."""

    index: dict[tuple[int, str], list[PrimaryTssRow]] = {}
    for row in primary_rows:
        index.setdefault((row.position_1based, row.strand), []).append(row)
    ledger = []
    for sample in sample_rows:
        expected_position = int(sample["start"]) + 1
        matches = index.get((expected_position, sample["strand"]), [])
        ledger.append(
            {
                **sample,
                "coordinate_transform": "bed_start_0based_plus_1",
                "expected_primary_position_1based": expected_position,
                # Multiple records may annotate the same coordinate for different
                # genes, categories, or conditions. They are one coordinate
                # match, not competing coordinate candidates.
                "primary_coordinate_match_count": int(bool(matches)),
                "primary_record_count": len(matches),
                "primary_locations": ";".join(
                    f"{match.source_sheet}:{match.source_row}" for match in matches
                ),
                "status": "match" if matches else "missing",
            }
        )
    return ledger


def read_tss_bed(path: Path) -> list[TssBedRow]:
    """Read a headerless BED6 file and reject malformed point features."""

    rows = []
    with path.open(encoding="utf-8") as handle:
        for source_row, line in enumerate(handle, start=1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 6:
                raise ValueError(f"{path}:{source_row} is not BED6")
            contig, start_text, end_text, name, score, strand = fields
            start, end = int(start_text), int(end_text)
            if not contig or start < 0 or end != start + 1 or strand not in {"+", "-"}:
                raise ValueError(f"{path}:{source_row} is not a valid point TSS")
            rows.append(TssBedRow(contig, start, end, name, score, strand, source_row))
    if not rows:
        raise ValueError(f"{path} contains no TSS rows")
    return rows


def audit_key(dataset_id: str, row: TssBedRow) -> str:
    """Return the canonical key frozen by the sample-audit contract."""

    return "\t".join(
        (dataset_id, row.contig, str(row.start), str(row.end), row.strand)
    )


def select_stratified_hash_sample(
    dataset_id: str,
    rows: Iterable[TssBedRow],
    *,
    sample_size: int,
    target_per_strand: int,
) -> list[tuple[TssBedRow, str]]:
    """Select a deterministic strand-aware sample by lowest SHA-256 rank."""

    if sample_size < 1 or target_per_strand < 0 or 2 * target_per_strand > sample_size:
        raise ValueError("invalid sample size or strand target")
    ranked = []
    for row in rows:
        digest = hashlib.sha256(audit_key(dataset_id, row).encode("utf-8")).hexdigest()
        ranked.append((digest, row.source_row, row))
    if len(ranked) < sample_size:
        raise ValueError(f"dataset {dataset_id!r} has fewer rows than the sample size")

    selected: list[tuple[str, int, TssBedRow]] = []
    selected_rows: set[int] = set()
    for strand in ("+", "-"):
        candidates = sorted(item for item in ranked if item[2].strand == strand)
        for item in candidates[:target_per_strand]:
            selected.append(item)
            selected_rows.add(item[1])
    if len(selected) < sample_size:
        remaining = sorted(item for item in ranked if item[1] not in selected_rows)
        selected.extend(remaining[: sample_size - len(selected)])
    return [(row, digest) for digest, _, row in sorted(selected)]
