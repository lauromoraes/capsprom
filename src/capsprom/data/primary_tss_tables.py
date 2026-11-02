"""Readers for the primary dRNA-seq TSS tables behind the reconstructed GraphPro bacteria.

Each reader returns ``{(one_based_position, strand): set_of_classes}``.  Class
names are lower case: ``primary``, ``secondary``, ``internal``, ``antisense``,
``putative srna``, ``orphan`` (and the source's own labels for
*L. interrogans*).  Only acquired supplements are read; nothing is inferred.
"""

from __future__ import annotations

import collections
import re
import zipfile
from pathlib import Path
from typing import Sequence
from xml.etree import ElementTree as ET

_M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

TssClasses = dict[tuple[int, str], set[str]]


def read_xlsx(path: Path, sheet: str) -> list[dict[str, str]]:
    """Read one worksheet as rows of ``{column_letter: text}`` without a spreadsheet library."""

    archive = zipfile.ZipFile(path)
    shared = [
        "".join(node.text or "" for node in item.iter(_M + "t"))
        for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall(_M + "si")
    ]
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {rel.get("Id"): rel.get("Target") for rel in rels}
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    member = {
        node.get("name"): "xl/" + targets[node.get(_R + "id")].lstrip("/").removeprefix("xl/")
        for node in workbook.iter(_M + "sheet")
    }[sheet]
    rows = []
    for row in ET.fromstring(archive.read(member)).iter(_M + "row"):
        values = {}
        for cell in row.findall(_M + "c"):
            node = cell.find(_M + "v")
            value = node.text if node is not None else ""
            if cell.get("t") == "s":
                value = shared[int(value)]
            values[re.sub(r"\d", "", cell.get("r"))] = value
        rows.append(values)
    return rows


def clean_strand(value: str) -> str:
    return value.strip().strip("'")


def campylobacter_classes(path: Path, sheets: Sequence[str] = ("NCTC11168",)) -> TssClasses:
    flags = ("Primary", "Secondary", "Internal", "Antisense", "Putative sRNA")
    classes: TssClasses = collections.defaultdict(set)
    for sheet in sheets:
        rows = read_xlsx(path, sheet)
        column = {name: letter for letter, name in rows[2].items()}
        for row in rows[3:]:
            if not row.get(column["Pos"]):
                continue
            key = (int(row[column["Pos"]]), clean_strand(row[column["Strand"]]))
            found = [name.lower() for name in flags if row.get(column[name]) == "1"]
            classes[key].update(found or ["orphan"])
    return dict(classes)


def chlamydophila_classes(path: Path, sheets: Sequence[str] = ("TSS",)) -> TssClasses:
    classes: TssClasses = collections.defaultdict(set)
    for sheet in sheets:
        for row in read_xlsx(path, sheet)[1:]:
            for column, name in (("B", "primary"), ("C", "secondary")):
                value = row.get(column, "").strip()
                if value.isdigit():
                    classes[(int(value), clean_strand(row.get("G", "")))].add(name)
    return dict(classes)


def leptospira_classes(
    path: Path, sheets: Sequence[str] = ("TSS-30_all", "TSS_37_all")
) -> TssClasses:
    classes: TssClasses = collections.defaultdict(set)
    for sheet in sheets:
        for row in read_xlsx(path, sheet)[1:]:
            if row.get("B", "").isdigit():
                classes[(int(row["B"]), clean_strand(row["C"]))].add(row.get("E", "unknown"))
    return dict(classes)


READERS = {
    "graphpro-cje": campylobacter_classes,
    "graphpro-cpne": chlamydophila_classes,
    "graphpro-lint": leptospira_classes,
}
