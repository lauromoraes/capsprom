"""Plan or execute the CNNProm E. coli genomic-control pilot (contract v1).

Without ``--execute`` it verifies the inputs, places every positive on the
target contig, resolves multiple loci, classes TSS support, checks the
contract's observed cases, matches the records to the native grouped build,
runs the static capacity check, and writes the placement summary and ledger;
it generates no control.  ``--execute`` additionally generates controls,
groups them with the native records under homology grouping v1 (needs
``--mmseqs``), and drops pairs that link across partitions, only when the
``contract_frozen`` and ``builder_fixture_tested`` gates are open.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import gzip
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import yaml

from capsprom.data.bacterial_reconstruction import InMemoryGenome, positive_window
from capsprom.data.ecoli_genomic_pilot import (
    admissible_windows,
    blocked_violations,
    cross_partition_links,
    exclusion_positions,
    forbidden_admissible_windows,
    native_assignments,
    native_negative_intervals,
    nearest_gc_capacity,
    place_all,
    read_active_positives,
    read_regulondb_acquisition,
    regulondb_union,
    select_nearest_gc_controls,
)
from capsprom.data.exact_mapping import read_fasta
from capsprom.data.graphpro_reconstruction import TssLocus, filter_reconstructed_pairs, find_control_exclusion_violations
from capsprom.data.homology_grouping import (
    GroupingRecord,
    SearchSettings,
    alignment_edges,
    genomic_overlap_edges,
    hamming_edges,
    run_mmseqs_search,
)
from capsprom.data.loading import sha256_file
from capsprom.state import write_json_atomic

SUMMARY = Path("manifests/provenance/cnnprom_ecoli_genomic_control_pilot_v1/placement_summary.json")
LEDGER = Path("data/interim/cnnprom_ecoli_genomic_pilot_v1/placement_ledger.csv")
OUTPUT_ROOT = Path("data/interim/cnnprom_ecoli_genomic_pilot_v1/builds")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--mmseqs", type=Path, help="MMseqs2 binary, required with --execute")
    args = parser.parse_args()
    contract = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    gates = contract["pilot"]["execution_gates"]
    if args.execute and not (gates["contract_frozen"] and gates["builder_fixture_tested"]):
        raise SystemExit("contract_frozen and builder_fixture_tested gates must be open to generate controls")
    grouping = contract["grouping_and_split"]
    if args.execute and (args.mmseqs is None or sha256_file(args.mmseqs) != grouping["mmseqs2_binary_sha256"]):
        raise SystemExit("pass --mmseqs with the MMseqs2 binary pinned by the contract")
    if sha256_file(Path(grouping["protocol"])) != grouping["protocol_sha256"]:
        raise SystemExit("homology grouping protocol hash mismatch")

    reference, positive_policy, policy = contract["reference"], contract["positive_policy"], contract["negative_policy"]
    genome_path = Path(reference["genome_fasta"])
    if sha256_file(genome_path) != reference["genome_fasta_sha256"]:
        raise SystemExit("genome hash mismatch")
    contig = reference["contig"]
    contigs = {contig: read_fasta(genome_path)[contig]}
    union = _union(Path(policy["regulondb_acquisition"]), contig, len(contigs[contig]))

    canonical = _read_gz_csv(Path(positive_policy["canonical_table"]))
    mapping = {row["record_id"]: row for row in _read_gz_csv(Path(positive_policy["mapping_records"]))}
    positives = [row for row in canonical if row["label"] == "1"]
    negatives = [row for row in canonical if row["label"] == "0"]
    if {row["record_id"] for row in positives} != {k for k, v in mapping.items() if v["label"] == "1"}:
        raise SystemExit("positive set differs between canonical table and mapping v3")

    placements = place_all(
        [(row["record_id"], row["original_header"], row["sequence"].upper()) for row in positives],
        contigs,
        union,
        int(positive_policy["near_tolerance_nt"]),
        int(positive_policy["multiple_loci"]["header_agreement_tolerance_nt"]),
    )
    undeclared = Counter(p.status for p in placements if p.status not in {"single", "multiple_resolved", "multiple_unresolved"})
    blocked, native_counts = native_negative_intervals((row["sequence"].upper() for row in negatives), contigs)
    cases = _check_observed_cases(placements, positive_policy)
    assignments = _native_assignments(grouping["native_build"], canonical)
    external = _external_positives(policy["external_active_positive_identity"])
    index = admissible_windows(
        contig, contigs[contig], {tss for tss, _ in exclusion_positions(union, placements)}, policy["exclusion_radius_nt"], blocked.get(contig, ())
    )
    sequences = {row["record_id"]: row["sequence"].upper() for row in positives}

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    _write_rows(LEDGER, [_placement_row(p) for p in placements])
    summary = {
        "contract": str(args.config),
        "contract_sha256": sha256_file(args.config),
        "contig": contig,
        "regulondb": {
            "union_tss_position_strand": len(union.positions),
            "out_of_range_rows_dropped": union.out_of_range_rows,
            "per_source": dict(union.per_source),
        },
        "positives": len(placements),
        "placement_status": dict(Counter(p.status for p in placements)),
        "header_strand_disagreements": sum(p.strand is not None and p.strand != p.header_strand for p in placements),
        "support_class": dict(Counter(p.support_class or "unplaced_or_unresolved" for p in placements)),
        "genomic_panel_positives": sum(p.in_genomic_panel for p in placements),
        "exclusion_positions": len(exclusion_positions(union, placements)),
        "native_negatives": dict(native_counts),
        "native_negative_blocked_intervals": sum(len(v) for v in blocked.values()),
        "non_exact_positives": [_placement_row(p) for p in placements if p.status != "single" or p.support_class != "exact"],
        "observed_cases": cases,
        "observed_cases_reproduced": all(case["reproduced"] for case in cases),
        "native_assignment": {
            "records_matched": len(assignments),
            "positive_partitions": dict(
                sorted(Counter(assignments[row["record_id"]].partition.split(":")[0] for row in positives).items())
            ),
        },
        "external_active_positives": {"datasets": len(external[1]), "sequences_81_nt": len(external[0])},
        "static_capacity": {
            "admissible_index": dict(index.excluded),
            "genomic_panel_positives_by_nearest_available_gc_distance": {
                str(k): v for k, v in nearest_gc_capacity(index, [sequences[p.record_id] for p in placements if p.in_genomic_panel]).items()
            },
            "admissible_windows_equal_to_active_external_positive": forbidden_admissible_windows(contigs[contig], index, external[0]),
        },
        "undeclared_statuses": dict(undeclared),
        "placement_ledger": {"path": str(LEDGER), "sha256": sha256_file(LEDGER)},
    }
    write_json_atomic(SUMMARY, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "non_exact_positives"}, indent=2))
    if undeclared or not summary["observed_cases_reproduced"]:
        raise SystemExit("placement differs from the contract; see the summary")
    if args.execute:
        _generate(args, contract, contigs, union, placements, blocked, index, external[0], assignments, canonical)


def _union(acquisition_config: Path, contig: str, length: int):
    acquisition = yaml.safe_load(acquisition_config.read_text(encoding="utf-8"))["acquisition"]
    root = Path(acquisition["root"])
    manifest = json.loads(Path(acquisition["manifest"]).read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        if hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise SystemExit(f"RegulonDB response hash mismatch: {entry['path']}")
    rows, content = read_regulondb_acquisition(root, acquisition["ht_tss_datasets"])
    return regulondb_union(rows, content, contig, length)


def _check_observed_cases(placements, policy) -> list[dict]:
    by_id = {p.record_id: p for p in placements}
    cases = []
    for case in policy["multiple_loci"]["observed_cases"]:
        p = by_id[case["record"]]
        cases.append(
            {
                "record": case["record"],
                "promoter": p.promoter,
                "expected": {"loci": case["loci"], "status": "multiple_resolved"},
                "observed": {"loci": len(p.all_loci), "status": p.status, "resolved_tss": p.tss, "strand": p.strand},
                "reproduced": p.promoter == case["promoter"] and len(p.all_loci) == case["loci"] and p.status == "multiple_resolved",
            }
        )
    for case in policy["observed_cases"]:
        p = by_id[case["record"]]
        cases.append(
            {
                "record": case["record"],
                "promoter": p.promoter,
                "expected": {"class": case["expected_class"], "distance_nt": case["nearest_union_tss_offset_nt"]},
                "observed": {"class": p.support_class, "distance_nt": p.support_distance_nt, "reference": p.support_reference},
                "reproduced": p.promoter == case["promoter"]
                and p.support_class == case["expected_class"]
                and p.support_distance_nt == case["nearest_union_tss_offset_nt"],
            }
        )
    return cases


def _generate(args, contract, contigs, union, placements, blocked, index, external, assignments, canonical) -> None:
    pilot, window, policy, grouping = contract["pilot"], contract["window"], contract["negative_policy"], contract["grouping_and_split"]
    contig = contract["reference"]["contig"]
    target = OUTPUT_ROOT / pilot["dataset_id"]
    if target.exists():
        raise FileExistsError(f"{target} exists; builds are immutable")
    genome = InMemoryGenome(contigs)
    loci = [TssLocus(p.record_id, contig, p.tss, p.strand) for p in placements if p.in_genomic_panel]
    rows = {row["record_id"]: row for row in canonical}
    for locus in loci:
        if positive_window(genome, locus, window["upstream"], window["downstream"])[2] != rows[locus.identifier]["sequence"].upper():
            raise AssertionError(f"re-extracted window differs for {locus.identifier}")
    exclusion = exclusion_positions(union, placements)
    known = [TssLocus(f"tss:{contig}:{tss}:{strand}", contig, tss, strand) for tss, strand in exclusion]
    selections, failures = select_nearest_gc_controls(
        contigs[contig],
        loci,
        index,
        seed=policy["sampling_seed"],
        maximum_gc_count_difference=policy["maximum_gc_count_difference"],
        forbidden_sequences=external,
        upstream=window["upstream"],
        downstream=window["downstream"],
    )
    pairs = [s.pair for s in selections]
    violations = find_control_exclusion_violations(pairs, known, policy["exclusion_radius_nt"])
    violations += blocked_violations(selections, blocked.get(contig, ()))
    if violations:
        raise AssertionError(f"accepted controls violate exclusions: {violations[:5]}")
    filtered = filter_reconstructed_pairs(pairs)
    kept = {pair.positive_locus.identifier for pair in filtered.pairs}
    selections = [s for s in selections if s.pair.positive_locus.identifier in kept]
    by_id = {p.record_id: p for p in placements}

    # Native records keep their grouped-build identity; each control carries its positive's partition.
    records, partition = [], {}
    for record_id, assignment in assignments.items():
        placement = by_id.get(record_id)
        coordinates = (None, None, None)
        if placement is not None and placement.status == "single":
            start = placement.tss - window["upstream"] if placement.strand == "+" else placement.tss - window["downstream"]
            coordinates = (contig, start, start + window["length"])
        records.append(GroupingRecord(assignment.record_id, rows[record_id]["sequence"].upper(), int(rows[record_id]["label"]), assignment.record_id, *coordinates))
        partition[assignment.record_id] = assignment.partition
    control_of = {}
    for selection in selections:
        pair, home = selection.pair, assignments[selection.pair.positive_locus.identifier]
        control_id = f"{home.record_id}|genomic-control"
        control_of[control_id] = selection
        partition[control_id] = home.partition
        records.append(GroupingRecord(control_id, pair.negative.sequence, 0, home.record_id, contig, pair.negative_start, pair.negative_end))
    grouping_config = yaml.safe_load(Path(grouping["protocol"]).read_text(encoding="utf-8"))
    settings = SearchSettings.from_config(grouping_config["search"])
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{pilot['dataset_id']}-", dir=OUTPUT_ROOT))
    try:
        search = run_mmseqs_search(records, staging / "mmseqs", args.mmseqs, settings)
        shutil.rmtree(staging / "mmseqs" / "tmp", ignore_errors=True)
        edges = {
            "alignment": alignment_edges(Path(search["hits"]), settings),
            "hamming": hamming_edges(records, grouping_config["grouping"]["hamming_edge"]["max_mismatch_fraction"]),
            "genomic_overlap": genomic_overlap_edges(records),
        }
        links = cross_partition_links(partition, control_of, set().union(*edges.values()))
        retained = [(cid, s) for cid, s in control_of.items() if cid not in links]
        _write_rows(
            staging / "pair_ledger.csv",
            [
                {
                    **_pair_row(s, by_id[s.pair.positive_locus.identifier]),
                    "native_record_id": assignments[s.pair.positive_locus.identifier].record_id,
                    "group": assignments[s.pair.positive_locus.identifier].group,
                    "partition": partition[cid],
                }
                for cid, s in retained
            ],
        )
        _write_rows(staging / "control_failures.csv", [_placement_row(by_id[locus.identifier]) for locus in failures])
        _write_rows(
            staging / "cross_partition_drops.csv",
            [
                {"record_id": control_of[cid].pair.positive_locus.identifier, "control_id": cid, "partition": partition[cid], "linked_partitions": "+".join(reached)}
                for cid, reached in sorted(links.items())
            ],
        )
        test = sorted(s.pair.positive_locus.identifier for cid, s in retained if partition[cid] == "test")
        _write_rows(staging / "test_intersection.csv", [{"record_id": record_id} for record_id in test])
        gaps = [s.pair.positive_gc - s.pair.negative_gc for _, s in retained]
        result = {
            "contract_sha256": sha256_file(args.config),
            "genomic_panel_positives": len(loci),
            "admissible_index": dict(index.excluded),
            "control_failures": len(failures),
            "gc_distance": {str(k): v for k, v in sorted(Counter(s.gc_distance for _, s in retained).items())},
            "residual_gc_gap_mean_positive_minus_control": sum(gaps) / len(gaps) if gaps else None,
            "filter": {k: v for k, v in dataclasses.asdict(filtered).items() if k != "pairs"},
            "grouping_edges": {name: len(values) for name, values in edges.items()},
            "cross_partition_drops": len(links),
            "pairs": len(retained),
            "pairs_by_partition": {k: v for k, v in sorted(Counter(partition[cid].split(":")[0] for cid, _ in retained).items())},
            "test_intersection": len(test),
            "mmseqs": {k: search[k] for k in ("binary_sha256", "version", "command_line", "hits_sha256")},
        }
        result["outputs"] = {p.name: sha256_file(p) for p in sorted(staging.iterdir()) if p.is_file()}
        write_json_atomic(staging / "build_manifest.json", result)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(json.dumps({k: v for k, v in result.items() if k not in ("outputs", "mmseqs")}, indent=2))


def _native_assignments(spec: dict, canonical: list[dict]):
    path = Path(spec["records"])
    if sha256_file(path) != spec["records_sha256"] or sha256_file(path.parent / "build_manifest.json") != spec["build_manifest_sha256"]:
        raise SystemExit("native grouped build hash mismatch")
    with path.open(encoding="utf-8", newline="") as handle:
        grouped = list(csv.DictReader(handle))
    try:
        return native_assignments(canonical, grouped)
    except ValueError as error:
        raise SystemExit(f"native grouped build does not match the source records: {error}") from error


def _external_positives(scope: dict) -> tuple[list[str], list[str]]:
    manifest = Path(scope["dependency_manifest"])
    if sha256_file(manifest) != scope["dependency_manifest_sha256"]:
        raise SystemExit("dependency manifest hash mismatch")
    datasets = [d["dataset_id"] for d in yaml.safe_load(manifest.read_text(encoding="utf-8"))["datasets"]]
    sources = {source["dataset_id"]: source for source in scope["sources"]}
    if len(datasets) != scope["dataset_count"] or sorted(datasets) != sorted(sources):
        raise SystemExit("declared external sources differ from the dependency manifest")
    sequences = set()
    for dataset_id in datasets:
        path = Path(sources[dataset_id]["path"])
        if sha256_file(path) != sources[dataset_id]["sha256"]:
            raise SystemExit(f"external positive source hash mismatch: {dataset_id}")
        sequences |= read_active_positives(path, scope["window_length_nt"])
    return sorted(sequences), datasets


def _placement_row(p) -> dict:
    return {
        "record_id": p.record_id,
        "promoter": p.promoter,
        "header_strand": p.header_strand,
        "header_coordinate": p.header_coordinate,
        "n_loci": len(p.all_loci),
        "all_loci": ";".join(f"{tss}{strand}" for tss, strand in p.all_loci),
        "status": p.status,
        "tss_zero_based": "" if p.tss is None else p.tss,
        "strand": p.strand or "",
        "resolution_evidence": p.resolution_evidence,
        "support_class": p.support_class or "",
        "support_distance_nt": "" if p.support_distance_nt is None else p.support_distance_nt,
        "support_reference": p.support_reference,
        "action": p.action,
    }


def _pair_row(selection, placement) -> dict:
    pair = selection.pair
    row = {k: v for k, v in dataclasses.asdict(pair).items() if k not in ("positive", "negative", "positive_locus")}
    return {
        **_placement_row(placement),
        "positive_sequence": pair.positive.sequence,
        "negative_identifier": pair.negative.identifier,
        "negative_sequence": pair.negative.sequence,
        **row,
        "gc_distance": selection.gc_distance,
        "candidates_at_distance": selection.candidates_at_distance,
    }


def _read_gz_csv(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not rows:
            return
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
