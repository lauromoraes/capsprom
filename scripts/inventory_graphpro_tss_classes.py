"""Inventory the TSS classes behind the Promotech BED files used by GraphPro.

Each Promotech BED row is joined to its cited primary TSS table by one-based
position and strand (primary position equals BED start plus one).  The script
reports the class mix of the Promotech positives, the size of the complete
primary TSS set, and how many existing reconstructed-v2 controls fall inside
the 100-nt margin of a primary-table TSS that the BED omits.  It reads
acquired files only and changes no dataset.
"""

from __future__ import annotations

import bisect
import collections
import csv
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import xlrd

SOURCES = Path("data/raw/references/graphpro_primary_tss_sources_v1")
BEDS = Path("data/raw/references/promotech_primary_audit_v1")
CONTROLS = Path("data/interim/graphpro_reconstructed_v2")
OUTPUT = Path("outputs/reports/graphpro_tss_class_inventory_v1/summary.json")
RADIUS = 100
_M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def read_xlsx(path: Path, sheet: str) -> list[dict[str, str]]:
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


def strand(value: str) -> str:
    return value.strip().strip("'")


def paa_classes() -> dict[tuple[int, str], set[str]]:
    sheet = xlrd.open_workbook(SOURCES / "ecoli_paa_dataset_s1.xls").sheet_by_index(0)
    classes: dict[tuple[int, str], set[str]] = collections.defaultdict(set)
    for index in range(3, sheet.nrows):
        row = sheet.row_values(index)
        if row[0] == "":
            continue
        key = (int(float(row[0])), strand(str(row[1])))
        for column, name in zip(range(5, 9), ("gene", "internal", "antisense", "orphan")):
            if str(row[column]).strip() not in ("", "0", "0.0"):
                classes[key].add(name)
    return classes


def campylobacter_classes() -> dict[tuple[int, str], set[str]]:
    rows = read_xlsx(SOURCES / "campylobacter_table_s4.xlsx", "NCTC11168")
    column = {name: letter for letter, name in rows[2].items()}
    flags = ("Primary", "Secondary", "Internal", "Antisense", "Putative sRNA")
    classes: dict[tuple[int, str], set[str]] = collections.defaultdict(set)
    for row in rows[3:]:
        if not row.get(column["Pos"]):
            continue
        key = (int(row[column["Pos"]]), strand(row[column["Strand"]]))
        found = [name.lower() for name in flags if row.get(column[name]) == "1"]
        classes[key].update(found or ["orphan"])
    return classes


def chlamydophila_classes() -> dict[tuple[int, str], set[str]]:
    classes: dict[tuple[int, str], set[str]] = collections.defaultdict(set)
    for row in read_xlsx(SOURCES / "chlamydia_table_s2.xlsx", "TSS")[1:]:
        for column, name in (("B", "primary"), ("C", "secondary")):
            value = row.get(column, "").strip()
            if value.isdigit():
                classes[(int(value), strand(row.get("G", "")))].add(name)
    return classes


def leptospira_classes() -> dict[tuple[int, str], set[str]]:
    classes: dict[tuple[int, str], set[str]] = collections.defaultdict(set)
    for sheet in ("TSS-30_all", "TSS_37_all"):
        for row in read_xlsx(SOURCES / "leptospira_table_s4.xlsx", sheet)[1:]:
            if row.get("B", "").isdigit():
                classes[(int(row["B"]), strand(row["C"]))].add(row.get("E", "unknown"))
    return classes


def bed_keys(name: str) -> list[tuple[int, str]]:
    keys = []
    for line in (BEDS / name).read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) >= 6:
            keys.append((int(fields[1]) + 1, fields[5]))
    return keys


def control_margin_hits(folder: str, classes: dict[tuple[int, str], set[str]]) -> dict[str, int] | None:
    ledger = CONTROLS / folder / "pair_ledger.csv"
    if not ledger.exists():
        return None
    # Zero-based TSS positions; a control [start, end) is within the margin when
    # some TSS satisfies start - RADIUS <= tss < end + RADIUS.
    positions = sorted(position - 1 for position, _ in classes)
    within = containing = 0
    rows = list(csv.DictReader(ledger.open(encoding="utf-8")))
    for row in rows:
        start, end = int(row["negative_start"]), int(row["negative_end"])
        first = bisect.bisect_left(positions, start - RADIUS)
        if first < len(positions) and positions[first] < end + RADIUS:
            within += 1
        first = bisect.bisect_left(positions, start)
        if first < len(positions) and positions[first] < end:
            containing += 1
    return {"controls": len(rows), "within_100nt_of_primary_tss": within, "containing_primary_tss": containing}


def summarize(bed: str, classes: dict[tuple[int, str], set[str]], controls: str | None) -> dict:
    keys = bed_keys(bed)
    unique = set(keys)
    combinations = collections.Counter(
        "+".join(sorted(classes[key])) if key in classes else "no_primary_match" for key in unique
    )
    return {
        "bed": bed,
        "bed_rows": len(keys),
        "bed_unique_tss": len(unique),
        "primary_unique_tss": len(classes),
        "primary_tss_absent_from_bed": len(set(classes) - unique),
        "bed_class_combinations": dict(combinations.most_common()),
        "reconstructed_v2_controls": control_margin_hits(controls, classes) if controls else None,
    }


def main() -> None:
    summary = {
        "inventory": "graphpro-tss-class-inventory-v1",
        "join_rule": "primary_one_based_position_equals_bed_start_plus_one_and_same_strand",
        "control_margin_nt": RADIUS,
        "model_outcomes_used": False,
        "sources": {
            "ecoli_paa": summarize("ECOLI.bed", paa_classes(), None),
            "campylobacter_jejuni": summarize("CJEJUNI_2.bed", campylobacter_classes(), "CJEJUNI_2"),
            "chlamydophila_pneumoniae": summarize(
                "CPNEUMONIAE.bed", chlamydophila_classes(), "CPNEUMONIAE"
            ),
            "leptospira_interrogans": summarize(
                "LINTERROGANS.bed", leptospira_classes(), "LINTERROGANS"
            ),
        },
        "not_inventoried": {
            "bacillus_amyloliquefaciens": "primary coordinate supplement not acquired",
            "rhodobacter_capsulatus": "no primary table identified for the 5,374-row collection",
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".tmp")
    temporary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
