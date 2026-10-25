"""Build paired EPD Human/Mouse candidates with exact GC-matched controls."""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import tempfile

import yaml

from capsprom.data.downstream_control import index_known_tss
from capsprom.data.epd_genomic_controls import reconstruct_epd_gc_matched_controls
from capsprom.data.epd_resolution import load_epd_bed
from capsprom.data.graphpro_reconstruction import filter_reconstructed_pairs
from capsprom.data.loading import sha256_file
from capsprom.data.sequences import read_fasta, write_fasta
from capsprom.data.twobit import TwoBitGenome
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/graphpro_epd_gc_matched_reconstruction_v1.yaml"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = _load_config(args.config)
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")

    external_positives = _load_external_positives(config["active_external_positive_scope"])
    window = config["window"]
    policy = config["negative_policy"]
    summaries = []
    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent
    ) as temporary:
        staging = Path(temporary) / args.output_dir.name
        staging.mkdir()
        for organism in config["organisms"]:
            identifiers = _source_identifiers(organism["source_fastas"])
            expected = int(organism["expected_source_identifier_count"])
            if len(identifiers) != expected:
                raise AssertionError(f"expected {expected} source identifiers, found {len(identifiers)}")
            primary_spec = organism["primary_bed"]
            primary = _load_hashed_bed(primary_spec)
            missing = identifiers - set(primary)
            if missing:
                raise AssertionError(f"{len(missing)} EPD identifiers are missing from the primary BED")
            coordinates = [primary[identifier] for identifier in sorted(identifiers)]
            known_collections = [_load_hashed_bed(spec) for spec in organism["known_tss_beds"]]
            known_tss = index_known_tss(known_collections)
            twobit = organism["twobit"]
            twobit_path = Path(twobit["path"])
            _verify_size_and_md5(twobit_path, int(twobit["size_bytes"]), twobit["md5"])
            with TwoBitGenome(twobit_path) as genome:
                generated = reconstruct_epd_gc_matched_controls(
                    genome,
                    coordinates,
                    known_tss,
                    external_positive_sequences=external_positives,
                    upstream=int(window["upstream"]),
                    downstream=int(window["downstream"]),
                    exclusion_margin=int(policy["exclusion_margin_nt"]),
                    maximum_gc_count_difference=int(policy["maximum_gc_count_difference"]),
                    seed=int(policy["sampling_seed"]),
                    max_attempts_per_positive=int(policy["max_attempts_per_positive"]),
                    exhaustive_fallback_on_random_exhaustion=bool(
                        policy.get("exhaustive_fallback_on_random_exhaustion", False)
                    ),
                )
            filtered = filter_reconstructed_pairs(generated)
            organism_dir = staging / organism["organism"]
            organism_dir.mkdir()
            positive_path = organism_dir / "positive.fa"
            negative_path = organism_dir / "negative.fa"
            ledger_path = organism_dir / "pair_ledger.csv"
            write_fasta((pair.positive for pair in filtered.pairs), positive_path)
            write_fasta((pair.negative for pair in filtered.pairs), negative_path)
            _write_pair_ledger(ledger_path, filtered.pairs)
            summary = {
                "organism": organism["organism"],
                "assembly": organism["assembly"],
                "source_identifier_count": len(identifiers),
                "pairs_before_integrity_filter": len(generated),
                "pairs_after_integrity_filter": len(filtered.pairs),
                "pair_filter": {
                    "cross_label_pairs_removed": filtered.cross_label_pairs_removed,
                    "positive_duplicate_pairs_removed": filtered.positive_duplicate_pairs_removed,
                    "negative_duplicate_pairs_removed": filtered.negative_duplicate_pairs_removed,
                },
                "maximum_observed_gc_count_difference": max(
                    abs(round(pair.positive_gc * 81) - round(pair.negative_gc * 81))
                    for pair in filtered.pairs
                ),
                "sampling_attempts": {
                    "maximum": max(pair.sampling_attempts for pair in filtered.pairs),
                    "mean": sum(pair.sampling_attempts for pair in filtered.pairs)
                    / len(filtered.pairs),
                },
                "search_modes": {
                    mode: sum(pair.search_mode == mode for pair in filtered.pairs)
                    for mode in sorted({pair.search_mode for pair in filtered.pairs})
                },
                "exhaustive_windows_scanned": sum(
                    pair.exhaustive_windows_scanned for pair in filtered.pairs
                ),
                "outputs": {
                    path.name: sha256_file(path)
                    for path in (positive_path, negative_path, ledger_path)
                },
            }
            summaries.append(summary)
            write_json_atomic(organism_dir / "build_manifest.json", summary)
        write_json_atomic(
            staging / "build_summary.json",
            {
                "schema_version": 1,
                "dataset_family": config["reconstruction"]["name"],
                "config_sha256": sha256_file(args.config),
                "active_external_positive_sequence_count": len(external_positives),
                "datasets": summaries,
                "split_generation_enabled": False,
                "model_training_enabled": False,
                "confirmatory_use_enabled": False,
            },
        )
        os.replace(staging, args.output_dir)
    print(json.dumps({"datasets": summaries}, indent=2))


def _source_identifiers(specs: list[dict[str, str]]) -> set[str]:
    identifiers = set()
    for spec in specs:
        path = Path(spec["path"])
        _verify_sha256(path, spec["sha256"])
        for record in read_fasta(path):
            identifiers.add(record.identifier.split("|", maxsplit=1)[1])
    return identifiers


def _load_config(path: Path) -> dict[str, object]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    base_spec = config.pop("extends", None)
    if base_spec is None:
        return config
    base_path = Path(base_spec["path"])
    _verify_sha256(base_path, base_spec["sha256"])
    base = _load_config(base_path)
    return _deep_merge(base, config)


def _deep_merge(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_hashed_bed(spec: dict[str, str]):
    path = Path(spec["path"])
    _verify_sha256(path, spec["sha256"])
    return load_epd_bed(path, spec["collection"])


def _load_external_positives(scope: dict[str, object]) -> list[str]:
    manifest_path = Path(str(scope["dependency_manifest"]))
    _verify_sha256(manifest_path, str(scope["dependency_manifest_sha256"]))
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    datasets = manifest["datasets"]
    if len(datasets) != int(scope["dataset_count"]):
        raise AssertionError("active dependency manifest dataset count changed")
    root = Path(str(scope["processed_root"]))
    positives = set()
    for dataset in datasets:
        paths = sorted(root.glob(f"{dataset['dataset_id']}-p-*-n-*-*.csv"))
        if len(paths) != 2:
            raise ValueError(f"expected train/test files for {dataset['dataset_id']}")
        for path in paths:
            with path.open(encoding="utf-8", newline="") as handle:
                positives.update(
                    row["sequence"].strip().upper()
                    for row in csv.DictReader(handle)
                    if int(row["label"]) == 1
                )
    return sorted(positives)


def _write_pair_ledger(path: Path, pairs) -> None:
    rows = []
    for pair in pairs:
        row = dataclasses.asdict(pair)
        row["pair_id"] = pair.positive_locus.identifier
        row["positive_identifier"] = pair.positive.identifier
        row["positive_sequence"] = pair.positive.sequence
        row["negative_identifier"] = pair.negative.identifier
        row["negative_sequence"] = pair.negative.sequence
        row["contig"] = pair.positive_locus.contig
        row["tss_zero_based"] = pair.positive_locus.tss
        row["strand"] = pair.positive_locus.strand
        for nested in ("positive", "negative", "positive_locus"):
            row.pop(nested)
        rows.append(row)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _verify_sha256(path: Path, expected: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: expected {expected}, observed {observed}")


def _verify_size_and_md5(path: Path, expected_size: int, expected_md5: str) -> None:
    if path.stat().st_size != expected_size:
        raise ValueError(f"size mismatch for {path}")
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != expected_md5:
        raise ValueError(f"MD5 mismatch for {path}")


if __name__ == "__main__":
    main()
