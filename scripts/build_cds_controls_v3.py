"""Build the CDS-derived control panel on top of graphpro-reconstructed-v3.

For each dataset it reuses the v3 positives, partitions, and groups (hash
checked), draws one CDS control per positive in the frozen frame cycle,
excludes v3 controls and every known identity, groups CDS controls with the v3
records under homology grouping v1, drops any pair whose CDS control links to
another partition, fixes the cross-panel test intersection, and writes the
required diagnostics.  Each dataset is written once, atomically.
"""

from __future__ import annotations

import argparse
import collections
import csv
import dataclasses
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import yaml

from build_graphpro_reconstruction_v3 import _external_positives, _load_contract, _read_fasta_gz
from capsprom.data.cds_controls import (
    blocking_intervals,
    eligible_cds,
    enumerate_windows,
    read_gff,
    sample_cds_controls,
)
from capsprom.data.homology_grouping import (
    GroupingRecord,
    SearchSettings,
    alignment_edges,
    genomic_overlap_edges,
    hamming_edges,
    run_mmseqs_search,
)
from capsprom.data.loading import sha256_file
from capsprom.data.primary_tss_tables import READERS
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/cds_negative_control_v3.yaml"))
    parser.add_argument("--mmseqs", type=Path, required=True)
    args = parser.parse_args()
    contract = _load_contract(args.config)
    gates, basis = contract["execution_gates"], contract["genomic_basis"]
    if not (gates["control_generation_enabled"] and gates["split_enabled"]):
        raise SystemExit("CDS generation or split gate is closed")
    if sha256_file(args.mmseqs) != basis["mmseqs2_binary_sha256"]:
        raise SystemExit("MMseqs2 binary hash differs from the contract")
    genomic = _load_contract(Path(basis["contract"]))
    external = _external_positives(genomic["negative_policy"]["external_active_positive_identity"])
    summary = {"contract": str(args.config), "contract_sha256": sha256_file(args.config), "datasets": {}}
    for collection_id in contract["scope"]["datasets"]:
        summary["datasets"][collection_id] = _build(collection_id, contract, genomic, external, args.mmseqs)
    print(json.dumps(summary, indent=2))


def _build(collection_id, contract, genomic, external, mmseqs) -> dict:
    basis = contract["genomic_basis"]
    entry = basis["datasets"][collection_id]
    source = Path(basis["build_root"]) / entry["dataset_id"]
    if sha256_file(source / "build_manifest.json") != entry["build_manifest_sha256"]:
        raise ValueError(f"v3 build manifest hash mismatch for {collection_id}")
    target = Path(contract["output_root"]) / entry["dataset_id"]
    if target.exists():
        raise FileExistsError(f"{target} exists; panels are immutable")
    organism = next(o for o in genomic["organisms"] if o["collection_id"] == collection_id)
    contig = organism["assembly"]
    acquired = Path("data/acquired/reference_acquisition_v12") / organism["reference_source_id"]
    sequence = _read_fasta_gz(next(acquired.glob("*_genomic.fna.gz")))[contig]
    features = [f for f in read_gff(next(acquired.glob("*_genomic.gff.gz"))) if f.seqid == contig]
    window, exclusions = contract["window"], contract["exclusions"]
    cds, excluded = eligible_cds(features, min_length=contract["annotation"]["min_cds_length_nt"])
    table_spec = organism["primary_table"]
    known = READERS[collection_id](Path(table_spec["path"]), table_spec["exclusion_sheets"])
    table = enumerate_windows(
        sequence, cds, blocking_intervals(features, contig), [p - 1 for p, _ in known],
        length=window["length_nt"], end_margin=window["min_distance_from_start_codon_nt"],
        tss_radius=exclusions["known_tss_radius_nt"],
    )
    pairs = list(csv.DictReader((source / "pair_ledger.csv").open(encoding="utf-8")))
    group_rows = list(csv.DictReader((source / "group_table.csv").open(encoding="utf-8")))
    partition = {row["record_id"]: row["partition"] for row in group_rows}
    inherited_group = {row["record_id"]: row["group"] for row in group_rows}
    sampling = contract["sampling"]
    controls, failures = sample_cds_controls(
        sequence, cds, table, [(p["pair_id"], p["positive_sequence"]) for p in pairs],
        occupied=[(int(p["negative_start"]), int(p["negative_end"])) for p in pairs],
        forbidden_sequences=[p["negative_sequence"] for p in pairs] + external,
        caliper=exclusions["gc_caliper_bases"], seed=sampling["seed"], max_probes=sampling["random_probe_ceiling"],
        length=window["length_nt"],
    )

    records = []
    for p in pairs:
        t = int(p["tss_zero_based"])
        start, end = (t - 60, t + 21) if p["strand"] == "+" else (t - 20, t + 61)
        records.append(GroupingRecord(p["pair_id"], p["positive_sequence"], 1, p["pair_id"], contig, start, end))
        records.append(GroupingRecord(p["negative_identifier"], p["negative_sequence"], 0, p["pair_id"], contig, int(p["negative_start"]), int(p["negative_end"])))
    cds_ids = {}
    for control in controls:
        record_id = f"{control.pair_id}|cds-control"
        cds_ids[record_id] = control
        records.append(GroupingRecord(record_id, control.sequence, 0, control.pair_id, contig, control.genomic_start, control.genomic_start + 81))
    grouping_config = yaml.safe_load(Path(genomic["grouping_and_split"]["protocol"]).read_text(encoding="utf-8"))
    settings = SearchSettings.from_config(grouping_config["search"])
    staging = Path(tempfile.mkdtemp(prefix=f".{entry['dataset_id']}-", dir=_ensure(Path(contract["output_root"]))))
    try:
        search = run_mmseqs_search(records, staging / "mmseqs", mmseqs, settings)
        shutil.rmtree(staging / "mmseqs" / "tmp", ignore_errors=True)
        edges = (
            alignment_edges(Path(search["hits"]), settings)
            | hamming_edges(records, grouping_config["grouping"]["hamming_edge"]["max_mismatch_fraction"])
            | genomic_overlap_edges(records)
        )
        neighbours = collections.defaultdict(set)
        for left, right in edges:
            neighbours[left].add(right)
            neighbours[right].add(left)
        kept, dropped = [], []
        for record_id, control in cds_ids.items():
            home = partition[control.pair_id]
            # The control inherits its positive's partition; any edge elsewhere would leak.
            crossing = sorted(
                {partition.get(n, partition.get(n.split("|", 1)[0], "")) for n in neighbours[record_id]} - {home}
            )
            (dropped if crossing else kept).append((control, home, crossing))
        ledger = [
            {**dataclasses.asdict(c), "partition": home, "inherited_group": inherited_group[c.pair_id]}
            for c, home, _ in kept
        ]
        _write(staging / "cds_pair_ledger.csv", ledger)
        _write(staging / "control_failures.csv", [dataclasses.asdict(f) for f in failures])
        _write(staging / "cross_partition_drops.csv", [{"pair_id": c.pair_id, "partition": h, "linked_partitions": "+".join(x)} for c, h, x in dropped])
        genomic_test = {p["pair_id"] for p in pairs if partition[p["pair_id"]] == "test"}
        cds_test = {c.pair_id for c, home, _ in kept if home == "test"}
        intersection = sorted(genomic_test & cds_test)
        _write(staging / "test_intersection.csv", [{"pair_id": pair_id} for pair_id in intersection])
        positive_by_id = {p["pair_id"]: p["positive_sequence"] for p in pairs}
        diagnostics = _diagnostics([c for c, _, _ in kept], positive_by_id, known, cds, failures)
        result = {
            "cds_eligible": len(cds),
            "cds_excluded_by_rule": dict(excluded),
            "admissible_windows": len(table),
            "positives": len(pairs),
            "control_failures": len(failures),
            "exhaustive_fallback_controls": sum(c.search_mode == "exhaustive_fallback" for c in controls),
            "cross_partition_drops": len(dropped),
            "cds_pairs": len(kept),
            "test_pairs_genomic": len(genomic_test),
            "test_pairs_cds": len(cds_test),
            "test_intersection": len(intersection),
            "diagnostics": diagnostics,
            "mmseqs": {k: search[k] for k in ("binary_sha256", "version", "command_line", "hits_sha256")},
        }
        result["outputs"] = {p.name: sha256_file(p) for p in sorted(staging.iterdir()) if p.is_file()}
        write_json_atomic(staging / "build_manifest.json", result)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {k: v for k, v in result.items() if k not in ("outputs", "mmseqs")}


def _diagnostics(controls, positives, known, cds, failures) -> dict:
    def periodicity(sequences):
        lags = range(1, 10)
        return {str(k): round(float(np.mean([np.mean([s[i] == s[i + k] for i in range(len(s) - k)]) for s in sequences])), 4) for k in lags}

    tss = sorted(p - 1 for p, _ in known)
    boundaries = sorted({b for f in cds for b in (f.start, f.end)})

    def nearest(values, start, end):
        import bisect
        i = bisect.bisect_left(values, start)
        candidates = [abs(values[j] - start) for j in (i - 1, i) if 0 <= j < len(values)]
        candidates += [abs(values[j] - end) for j in (i - 1, i) if 0 <= j < len(values)]
        return min(candidates) if candidates else None

    gc_control = [c.gc_count for c in controls]
    gc_positive = [positives[c.pair_id].count("G") + positives[c.pair_id].count("C") for c in controls]
    return {
        "frame_proportions": {str(f): round(sum(c.frame == f for c in controls) / len(controls), 4) for f in range(3)},
        "gc_mean_positive": round(float(np.mean(gc_positive)), 3),
        "gc_mean_control": round(float(np.mean(gc_control)), 3),
        "gc_mean_control_minus_positive": round(float(np.mean(np.subtract(gc_control, gc_positive))), 3),
        "lag_identity_positive": periodicity([positives[c.pair_id] for c in controls]),
        "lag_identity_control": periodicity([c.sequence for c in controls]),
        "median_distance_to_tss": float(np.median([nearest(tss, c.genomic_start, c.genomic_start + 81) for c in controls])),
        "median_distance_to_cds_boundary": float(np.median([nearest(boundaries, c.genomic_start, c.genomic_start + 81) for c in controls])),
        "failed_positive_gc_counts": sorted(f.positive_gc_count for f in failures),
    }


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        if rows:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
