"""Plan or execute the CNNProm E. coli genomic-control pilot (contract v1).

Without ``--execute`` it verifies the inputs, places every positive on the
target contig, resolves multiple loci, classes TSS support, checks the
contract's observed cases, and writes the placement summary and ledger; it
generates no control.  ``--execute`` additionally generates controls, only
when the ``contract_frozen`` and ``builder_fixture_tested`` gates are open.
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
    exclusion_positions,
    native_negative_intervals,
    place_all,
    read_regulondb_acquisition,
    regulondb_union,
    select_nearest_gc_controls,
)
from capsprom.data.exact_mapping import read_fasta
from capsprom.data.graphpro_reconstruction import TssLocus, filter_reconstructed_pairs, find_control_exclusion_violations
from capsprom.data.loading import sha256_file
from capsprom.state import write_json_atomic

SUMMARY = Path("manifests/provenance/cnnprom_ecoli_genomic_control_pilot_v1/placement_summary.json")
LEDGER = Path("data/interim/cnnprom_ecoli_genomic_pilot_v1/placement_ledger.csv")
OUTPUT_ROOT = Path("data/interim/cnnprom_ecoli_genomic_pilot_v1/builds")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    contract = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    gates = contract["pilot"]["execution_gates"]
    if args.execute and not (gates["contract_frozen"] and gates["builder_fixture_tested"]):
        raise SystemExit("contract_frozen and builder_fixture_tested gates must be open to generate controls")

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
        "undeclared_statuses": dict(undeclared),
        "placement_ledger": {"path": str(LEDGER), "sha256": sha256_file(LEDGER)},
    }
    write_json_atomic(SUMMARY, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "non_exact_positives"}, indent=2))
    if undeclared or not summary["observed_cases_reproduced"]:
        raise SystemExit("placement differs from the contract; see the summary")
    if args.execute:
        _generate(contract, contigs, union, placements, blocked, positives)


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


def _generate(contract, contigs, union, placements, blocked, positives) -> None:
    pilot, window, policy = contract["pilot"], contract["window"], contract["negative_policy"]
    contig = contract["reference"]["contig"]
    target = OUTPUT_ROOT / pilot["dataset_id"]
    if target.exists():
        raise FileExistsError(f"{target} exists; builds are immutable")
    external = _external_positives(policy["external_active_positive_identity"])
    genome = InMemoryGenome(contigs)
    loci = [TssLocus(p.record_id, contig, p.tss, p.strand) for p in placements if p.in_genomic_panel]
    sequences = {row["record_id"]: row["sequence"].upper() for row in positives}
    for locus in loci:
        if positive_window(genome, locus, window["upstream"], window["downstream"])[2] != sequences[locus.identifier]:
            raise AssertionError(f"re-extracted window differs for {locus.identifier}")
    exclusion = exclusion_positions(union, placements)
    known = [TssLocus(f"tss:{contig}:{tss}:{strand}", contig, tss, strand) for tss, strand in exclusion]
    index = admissible_windows(contig, contigs[contig], {tss for tss, _ in exclusion}, policy["exclusion_radius_nt"], blocked.get(contig, ()))
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
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{pilot['dataset_id']}-", dir=OUTPUT_ROOT))
    try:
        by_id = {p.record_id: p for p in placements}
        _write_rows(staging / "pair_ledger.csv", [_pair_row(s, by_id[s.pair.positive_locus.identifier]) for s in selections if s.pair.positive_locus.identifier in kept])
        _write_rows(staging / "control_failures.csv", [_placement_row(by_id[locus.identifier]) for locus in failures])
        gaps = [s.pair.positive_gc - s.pair.negative_gc for s in selections if s.pair.positive_locus.identifier in kept]
        result = {
            "contract_sha256": sha256_file(Path("configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml")),
            "genomic_panel_positives": len(loci),
            "admissible_index": dict(index.excluded),
            "control_failures": len(failures),
            "gc_distance": dict(Counter(s.gc_distance for s in selections)),
            "residual_gc_gap_mean_positive_minus_control": sum(gaps) / len(gaps) if gaps else None,
            "filter": {k: v for k, v in dataclasses.asdict(filtered).items() if k != "pairs"},
            "pairs": len(filtered.pairs),
        }
        result["outputs"] = {p.name: sha256_file(p) for p in sorted(staging.iterdir()) if p.is_file()}
        write_json_atomic(staging / "build_manifest.json", result)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(json.dumps(result, indent=2))


def _external_positives(scope: dict) -> list[str]:
    missing = [key for key in ("dependency_manifest_sha256", "dataset_count", "processed_root") if key not in scope]
    if missing:
        raise SystemExit(f"external_active_positive_identity lacks {missing}; declare them before freezing")
    manifest = Path(scope["dependency_manifest"])
    if sha256_file(manifest) != scope["dependency_manifest_sha256"]:
        raise SystemExit("dependency manifest hash mismatch")
    datasets = yaml.safe_load(manifest.read_text(encoding="utf-8"))["datasets"]
    if len(datasets) != scope["dataset_count"]:
        raise SystemExit("dependency manifest dataset count changed")
    sequences = set()
    for dataset in datasets:
        for path in sorted(Path(scope["processed_root"]).glob(f"{dataset['dataset_id']}*.csv")):
            with path.open(encoding="utf-8", newline="") as handle:
                sequences.update(row["sequence"].strip().upper() for row in csv.DictReader(handle) if int(row["label"]) == 1)
    return sorted(sequences)


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
