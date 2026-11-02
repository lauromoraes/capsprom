"""Plan or execute the graphpro-reconstructed-v3 bacterial build.

Without ``--execute`` it verifies the contract inputs (reference and primary
table hashes), selects the P-or-S positives, screens their windows, and prints
the counts against the declared ones; it writes nothing.  ``--execute`` runs
only the stages whose gates are open in the contract: control generation,
homology grouping (needs ``--mmseqs``), and the group-safe split.  Each
dataset is written once, atomically, to a new directory.
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
from pathlib import Path

import yaml

from capsprom.data.bacterial_reconstruction import (
    InMemoryGenome,
    exclusion_loci,
    grouping_records,
    positive_window,
    reconstruct_bacterial_controls,
    select_positive_loci,
)
from capsprom.data.graphpro_reconstruction import filter_reconstructed_pairs
from capsprom.data.homology_grouping import (
    SearchSettings,
    alignment_edges,
    connected_groups,
    cross_partition_edges,
    genomic_overlap_edges,
    grouping_report,
    hamming_edges,
    partition_groups,
    run_mmseqs_search,
    unit_edges,
)
from capsprom.data.loading import sha256_file
from capsprom.data.primary_tss_tables import READERS
from capsprom.data.sequences import is_strict_dna
from capsprom.state import write_json_atomic

OUTPUT_ROOT = Path("data/interim/graphpro_reconstructed_v3")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/graphpro_reconstruction_v3.yaml"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--mmseqs", type=Path, help="MMseqs2 binary, required when grouping runs")
    parser.add_argument("--dataset", action="append", help="restrict to a collection_id (repeatable)")
    args = parser.parse_args()
    config_sha256 = sha256_file(args.config)
    contract = _load_contract(args.config)
    gates = contract["execution_gates"]
    if args.execute and not (gates["positive_extraction_enabled"] and gates["control_generation_enabled"]):
        raise SystemExit("extraction and control-generation gates are closed")
    if args.execute and gates["grouping_enabled"]:
        if args.mmseqs is None:
            raise SystemExit("grouping is enabled: pass --mmseqs")
        expected = contract.get("execution", {}).get("mmseqs2", {}).get("binary_sha256")
        if expected and sha256_file(args.mmseqs) != expected:
            raise SystemExit("MMseqs2 binary hash differs from the execution contract")
    references = _verified_references(contract["reference"])
    external = _external_positives(contract["negative_policy"]["external_active_positive_identity"]) if args.execute else []
    summary = {"contract": str(args.config), "contract_sha256": config_sha256, "execute": args.execute, "datasets": {}}
    for organism in contract["organisms"]:
        if args.dataset and organism["collection_id"] not in args.dataset:
            continue
        summary["datasets"][organism["dataset_id"]] = _build(organism, contract, references, external, args, config_sha256)
    print(json.dumps(summary, indent=2))


def _build(organism, contract, references, external, args, config_sha256) -> dict:
    table = organism["primary_table"]
    if sha256_file(Path(table["path"])) != table["sha256"]:
        raise ValueError(f"primary table hash mismatch for {organism['collection_id']}")
    reader = READERS[organism["collection_id"]]
    positive_classes = reader(Path(table["path"]), table["positive_sheets"])
    all_classes = reader(Path(table["path"]), table["exclusion_sheets"])
    contig = organism["assembly"]
    genome = InMemoryGenome({contig: references[organism["reference_source_id"]][contig]})
    window = contract["window"]
    loci = select_positive_loci(contig, positive_classes, organism["collection_id"])
    known = exclusion_loci(contig, all_classes)
    screened, rejected = [], []
    for locus in loci:
        found = positive_window(genome, locus, window["upstream"], window["downstream"])
        if found is None:
            rejected.append((locus, "window_out_of_reference_bounds"))
        elif not is_strict_dna(found[2]):
            rejected.append((locus, "window_contains_ambiguous_dna"))
        else:
            screened.append(locus)
    result = {
        "declared_positives": organism["declared_positives"],
        "selected_positives": len(loci),
        "declared_exclusion_set": organism["exclusion_set_size"],
        "exclusion_set": len(known),
        "screened_positives": len(screened),
        "rejected_positive_windows": len(rejected),
    }
    if len(loci) != organism["declared_positives"] or len(known) != organism["exclusion_set_size"]:
        raise ValueError(f"declared counts differ for {organism['collection_id']}: {result}")
    if not args.execute:
        return result

    target = OUTPUT_ROOT / organism["dataset_id"]
    if target.exists():
        raise FileExistsError(f"{target} exists; builds are immutable")
    policy, gates, split = contract["negative_policy"], contract["execution_gates"], contract["grouping_and_split"]
    pairs, failures = reconstruct_bacterial_controls(
        genome,
        screened,
        known,
        external_positive_sequences=external,
        upstream=window["upstream"],
        downstream=window["downstream"],
        exclusion_radius=policy["exclusion_radius_nt"],
        maximum_gc_count_difference=policy["maximum_gc_count_difference"],
        seed=policy["sampling_seed"],
        max_attempts_per_positive=policy["max_attempts_per_positive"],
    )
    filtered = filter_reconstructed_pairs(pairs)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{organism['dataset_id']}-", dir=OUTPUT_ROOT))
    try:
        _write_rows(staging / "rejected_positive_windows.csv", [{"pair_id": locus.identifier, "reason": reason} for locus, reason in rejected])
        _write_rows(staging / "control_failures.csv", [{**dataclasses.asdict(f)["locus"], **{k: v for k, v in dataclasses.asdict(f).items() if k != "locus"}} for f in failures])
        _write_rows(staging / "pair_ledger.csv", [_ledger_row(pair, positive_classes) for pair in filtered.pairs])
        result.update(
            control_failures=len(failures),
            exhaustive_fallback_pairs=sum(p.search_mode == "exhaustive_fallback" for p in pairs),
            filter={k: v for k, v in dataclasses.asdict(filtered).items() if k != "pairs"},
            pairs=len(filtered.pairs),
        )
        if gates["grouping_enabled"]:
            result.update(_group(filtered.pairs, contract, gates, split, staging, args.mmseqs))
        result.update(config_sha256=config_sha256, outputs={p.name: sha256_file(p) for p in sorted(staging.iterdir()) if p.is_file()})
        write_json_atomic(staging / "build_manifest.json", result)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return result


def _group(pairs, contract, gates, split, staging, mmseqs) -> dict:
    grouping_config = yaml.safe_load(Path(split["protocol"]).read_text(encoding="utf-8"))
    settings = SearchSettings.from_config(grouping_config["search"])
    records = grouping_records(pairs, contract["window"]["upstream"], contract["window"]["downstream"])
    search = run_mmseqs_search(records, staging / "mmseqs", mmseqs, settings)
    edges = {
        "unit": unit_edges(records),
        "alignment": alignment_edges(Path(search["hits"]), settings),
        "hamming": hamming_edges(records, grouping_config["grouping"]["hamming_edge"]["max_mismatch_fraction"]),
        "genomic_overlap": genomic_overlap_edges(records),
    }
    grouping = connected_groups(records, edges)
    report = grouping_report(records, grouping, grouping_config["grouping"]["max_component_fraction"])
    shutil.rmtree(staging / "mmseqs" / "tmp", ignore_errors=True)
    assignment = {}
    if gates["split_enabled"]:
        if report["oversized"]:
            raise RuntimeError("largest homology group exceeds the contract fraction; review before splitting")
        assignment = partition_groups(
            records,
            grouping,
            test_fraction=split["test_fraction"],
            seed=split["assignment_seed"],
            folds=split["inner_folds"],
            fold_seed=split["inner_fold_seed"],
        )
        crossing = cross_partition_edges(grouping, assignment)
        if any(crossing.values()):
            raise AssertionError(f"cross-partition edges remain: {crossing}")
        report["cross_partition_edges"] = crossing
    _write_rows(
        staging / "group_table.csv",
        [
            {"record_id": r.record_id, "pair_id": r.unit, "label": r.label, "group": grouping.group_of[r.record_id], "partition": assignment.get(r.record_id, "")}
            for r in records
        ],
    )
    write_json_atomic(staging / "grouping_report.json", {**report, "mmseqs": search})
    return {"grouping": report}


def _load_contract(path: Path) -> dict:
    """Load a contract; an ``extends`` base must match its declared SHA-256."""

    contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    base = contract.pop("extends", None)
    if base is None:
        return contract
    if sha256_file(Path(base["path"])) != base["sha256"]:
        raise ValueError(f"base contract hash mismatch: {base['path']}")
    merged = _load_contract(Path(base["path"]))
    for key, value in contract.items():
        merged[key] = {**merged[key], **value} if isinstance(value, dict) and isinstance(merged.get(key), dict) else value
    merged["base_contract_sha256"] = base["sha256"]
    return merged


def _ledger_row(pair, classes) -> dict:
    locus = pair.positive_locus
    row = {k: v for k, v in dataclasses.asdict(pair).items() if k not in ("positive", "negative", "positive_locus")}
    return {
        "pair_id": locus.identifier,
        "contig": locus.contig,
        "tss_zero_based": locus.tss,
        "strand": locus.strand,
        "tss_classes": "+".join(sorted(classes[(locus.tss + 1, locus.strand)])),
        "positive_sequence": pair.positive.sequence,
        "negative_identifier": pair.negative.identifier,
        "negative_sequence": pair.negative.sequence,
        **row,
    }


def _verified_references(reference: dict) -> dict[str, dict[str, str]]:
    manifest = json.loads(Path(reference["manifest"]).read_text(encoding="utf-8"))
    root = Path(yaml.safe_load(Path(reference["acquisition"]).read_text(encoding="utf-8"))["acquisition"]["root"])
    sequences = {}
    for key, entry in manifest["files"].items():
        if not key.endswith("_genomic.fna.gz"):
            continue
        path = root / key
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"reference hash mismatch: {path}")
        sequences[key.split("/", 1)[0]] = _read_fasta_gz(path)
    return sequences


def _read_fasta_gz(path: Path) -> dict[str, str]:
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


def _external_positives(scope: dict) -> list[str]:
    manifest_path = Path(scope["dependency_manifest"])
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != scope["dependency_manifest_sha256"]:
        raise ValueError("dependency manifest hash mismatch")
    datasets = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))["datasets"]
    if len(datasets) != scope["dataset_count"]:
        raise AssertionError("active dependency manifest dataset count changed")
    positives = set()
    for dataset in datasets:
        paths = sorted(Path(scope["processed_root"]).glob(f"{dataset['dataset_id']}-p-*-n-*-*.csv"))
        if len(paths) != 2:
            raise ValueError(f"expected train/test files for {dataset['dataset_id']}")
        for path in paths:
            with path.open(encoding="utf-8", newline="") as handle:
                positives.update(row["sequence"].strip().upper() for row in csv.DictReader(handle) if int(row["label"]) == 1)
    return sorted(positives)


def _write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not rows:
            return
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
