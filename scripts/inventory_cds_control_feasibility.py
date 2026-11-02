"""Model-free feasibility inventory for CDS-derived negative controls.

For each reconstructed bacterium in ``configs/cds_negative_control_v2.yaml`` it
counts eligible RefSeq CDS, every admissible 81-nt sense-strand window after the
end margins, the complete-primary-table TSS exclusion, and the CDS/RNA overlap
exclusion, and then the windows available to each P+S positive in its assigned
frame within the GC caliper.  It samples no control and changes no dataset.
Frames are assigned in the predeclared 0/1/2 cycle over positives sorted by
(position, strand); the genomic successor build fixes the final order.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from capsprom.data.cds_controls import (
    blocking_intervals,
    eligible_cds,
    enumerate_windows,
    gc_histogram,
    matched_candidates,
    read_gff,
)
from inventory_graphpro_tss_classes import (
    SOURCES,
    campylobacter_classes,
    chlamydophila_classes,
    leptospira_classes,
    read_xlsx,
    strand as clean_strand,
)

CONTRACT = Path("configs/cds_negative_control_v2.yaml")
ACQUIRED = Path("data/acquired/reference_acquisition_v12")
# v2: L. interrogans positives come from the 30 °C sheet only (log R-042).
OUTPUT = Path("outputs/reports/cds_control_feasibility_v2")
POSITIVE_CLASSES = {"primary", "secondary"}


def leptospira_30c_classes() -> dict[tuple[int, str], set[str]]:
    classes: dict[tuple[int, str], set[str]] = {}
    for row in read_xlsx(SOURCES / "leptospira_table_s4.xlsx", "TSS-30_all")[1:]:
        if row.get("B", "").isdigit():
            classes.setdefault((int(row["B"]), clean_strand(row["C"])), set()).add(row.get("E", "unknown"))
    return classes


# dataset: (acquired source, replicon, exclusion classes, positive classes or None for the same)
ORGANISMS = {
    "graphpro-cje": (
        "refseq-campylobacter-jejuni-nctc11168", "NC_002163.1", campylobacter_classes, None
    ),
    "graphpro-cpne": (
        "refseq-chlamydia-pneumoniae-cwl029", "NC_000922.1", chlamydophila_classes, None
    ),
    "graphpro-lint": (
        "refseq-leptospira-interrogans-manilae-l495",
        "NZ_LT962963.1",
        leptospira_classes,
        leptospira_30c_classes,
    ),
}
_COMPLEMENT = str.maketrans("ACGT", "TGCA")


def read_fasta_gz(path: Path) -> dict[str, str]:
    records: dict[str, list[str]] = {}
    name = None
    with gzip.open(path, "rt", encoding="ascii") as handle:
        for line in handle:
            if line.startswith(">"):
                name = line[1:].split()[0]
                records[name] = []
            elif name is not None:
                records[name].append(line.strip().upper())
    return {key: "".join(value) for key, value in records.items()}


def positive_window(sequence: str, position: int, strand: str, upstream: int, downstream: int) -> str | None:
    tss = position - 1
    start, end = (tss - upstream, tss + downstream + 1) if strand == "+" else (tss - downstream, tss + upstream + 1)
    if start < 0 or end > len(sequence):
        return None
    window = sequence[start:end]
    return window.translate(_COMPLEMENT)[::-1] if strand == "-" else window


def quantiles(values: list[int]) -> dict[str, float]:
    if not values:
        return {}
    array = np.asarray(values)
    return {name: float(np.quantile(array, q)) for name, q in (("min", 0), ("p01", 0.01), ("p05", 0.05), ("median", 0.5))}


def inventory(dataset: str, contract: dict) -> tuple[dict, list[dict]]:
    source_id, seqid, load_classes, load_positive_classes = ORGANISMS[dataset]
    window, exclusions = contract["window"], contract["exclusions"]
    length = window["length_nt"]
    caliper = exclusions["gc_caliper_bases"]
    folder = ACQUIRED / source_id
    gff_path = next(folder.glob("*_genomic.gff.gz"))
    sequence = read_fasta_gz(next(folder.glob("*_genomic.fna.gz")))[seqid]
    features = read_gff(gff_path)
    replicon_features = [feature for feature in features if feature.seqid == seqid]

    cds, excluded = eligible_cds(replicon_features, min_length=contract["annotation"]["min_cds_length_nt"])
    classes = load_classes()
    tss_positions = [position - 1 for position, _ in classes]
    table = enumerate_windows(
        sequence,
        cds,
        blocking_intervals(replicon_features, seqid),
        tss_positions,
        length=length,
        end_margin=window["min_distance_from_start_codon_nt"],
        tss_radius=exclusions["known_tss_radius_nt"],
    )
    margin_only = enumerate_windows(
        sequence, cds, [(item.start, item.end) for item in cds], [], length=length,
        end_margin=window["min_distance_from_start_codon_nt"], tss_radius=0,
    )
    histogram = gc_histogram(table, length)

    positive_classes = load_positive_classes() if load_positive_classes else classes
    keys = sorted(key for key, names in positive_classes.items() if names & POSITIVE_CLASSES)
    rows, in_frame, any_frame = [], [], []
    for index, (position, strand) in enumerate(keys):
        positive = positive_window(sequence, position, strand, 60, 20)
        frame = index % 3
        row = {"position": position, "strand": strand, "frame": frame}
        if positive is None or set(positive) - set("ACGT"):
            row.update(gc_count="", candidates_in_frame="", candidates_any_frame="", status="invalid_positive")
        else:
            gc_count = positive.count("G") + positive.count("C")
            count = matched_candidates(histogram, gc_count, frame, caliper)
            total = sum(matched_candidates(histogram, gc_count, f, caliper) for f in range(3))
            in_frame.append(count)
            any_frame.append(total)
            row.update(
                gc_count=gc_count,
                candidates_in_frame=count,
                candidates_any_frame=total,
                status="no_candidate" if count == 0 else "feasible",
            )
        rows.append(row)

    positive_gc = [row["gc_count"] for row in rows if row["gc_count"] != ""]
    window_gc = table.gc_count
    summary = {
        "assembly": seqid,
        "replicon_length": len(sequence),
        "gff": {"path": str(gff_path), "sha256": hashlib.sha256(gff_path.read_bytes()).hexdigest()},
        "cds_rows_on_replicon": sum(1 for f in replicon_features if f.feature_type == "CDS"),
        "cds_eligible": len(cds),
        "cds_excluded_by_rule": dict(excluded),
        "primary_table_tss_all_classes": len(classes),
        "positives_p_or_s": len(keys),
        "positives_invalid_window": sum(row["status"] == "invalid_positive" for row in rows),
        "windows_after_margins_only": len(margin_only),
        "windows_admissible": len(table),
        "windows_admissible_by_frame": {str(f): int((table.frame == f).sum()) for f in range(3)},
        "cds_with_admissible_window": int(len(np.unique(table.cds_index))),
        "gc_count_mean": {
            "positives": float(np.mean(positive_gc)) if positive_gc else None,
            "admissible_windows": float(window_gc.mean()) if len(table) else None,
        },
        "positives_without_candidate_in_frame": sum(count == 0 for count in in_frame),
        "positives_without_candidate_any_frame": sum(count == 0 for count in any_frame),
        "positives_with_fewer_than_100_in_frame": sum(count < 100 for count in in_frame),
        "candidates_in_frame_quantiles": quantiles(in_frame),
        "failed_positive_gc_counts": sorted(row["gc_count"] for row in rows if row["status"] == "no_candidate"),
    }
    return summary, rows


def main() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    if not contract["execution_gates"].get("feasibility_inventory_enabled"):
        raise SystemExit("feasibility inventory gate is closed")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {
        "inventory": "cds-control-feasibility-v1",
        "contract": str(CONTRACT),
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "positive_classes": sorted(POSITIVE_CLASSES),
        "frame_assignment": "cycle_0_1_2_over_positives_sorted_by_position_and_strand",
        "not_applied": [
            "exact_identity_with_positives_or_controls",
            "selected_control_overlap",
            "genomic_successor_deduplication_and_grouping",
        ],
        "model_outcomes_used": False,
        "datasets": {},
    }
    for dataset in contract["scope"]["datasets"]:
        summary, rows = inventory(dataset, contract)
        report["datasets"][dataset] = summary
        path = OUTPUT / f"{dataset}_positives.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        summary["positives_csv_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    target = OUTPUT / "summary.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(json.dumps(report, indent=2))
    print("summary_sha256", hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
