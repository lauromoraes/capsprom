"""Distribution and cross-dataset dependency audit of graphpro-reconstructed-v3 panels.

Descriptive release-gate audit: GC and positional composition per panel (all
records and test only, Holm across panels), exact strand-invariant sharing,
and MMseqs2 alignment dependence of each v3 dataset against the others and
the 18 eligible datasets, with the dependency-manifest v3 join rule.  It reads
no model output and changes no dataset.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import ks_2samp, mannwhitneyu

from capsprom.data.dependency import audit_named_sequence_dependencies
from capsprom.data.distribution_audit import maximum_positional_total_variation, summarize_class_distribution
from capsprom.data.homology_grouping import GroupingRecord, SearchSettings, alignment_edges, run_mmseqs_search
from capsprom.data.loading import sha256_file
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/graphpro_v3_distribution_dependency_audit_v1.yaml"))
    parser.add_argument("--mmseqs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/reports/graphpro_v3_distribution_dependency_v1"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    inputs = config["inputs"]
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")
    if sha256_file(args.mmseqs) != inputs["mmseqs2_binary_sha256"]:
        raise SystemExit("MMseqs2 binary hash differs from the audit contract")
    if sha256_file(Path(inputs["dependency_manifest"])) != inputs["dependency_manifest_sha256"]:
        raise ValueError("dependency manifest hash mismatch")
    panels = {panel["panel_id"]: _load_panel(panel) for panel in inputs["panels"]}
    distributions = [_distribution(panel_id, rows) for panel_id, rows in panels.items()]
    for column in ("mann_whitney_p", "ks_p", "test_mann_whitney_p"):
        _add_holm(distributions, column)

    eligible, clusters = _load_eligible(inputs)
    genomic = {pid.removesuffix(".genomic"): rows for pid, rows in panels.items() if pid.endswith(".genomic")}
    labelled = {name: {1: {r["positive"] for r in rows}, 0: {r["negative"] for r in rows}} for name, rows in genomic.items()}
    for name, rows in panels.items():
        if name.endswith(".cds"):
            labelled[name] = {1: set(), 0: {r["negative"] for r in rows}}
    exact = audit_named_sequence_dependencies({**labelled, **eligible})
    exact["overlaps_involving_v3"] = [
        row for row in exact["overlaps"] if row["left_dataset_id"].startswith("graphpro-") or row["right_dataset_id"].startswith("graphpro-")
    ]

    OUT = args.output_dir
    OUT.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".v3-audit-", dir=OUT.parent))
    try:
        alignment = _alignment_dependence(labelled, eligible, config, args.mmseqs, staging)
        threshold = config["dependency"]["alignment"]["pair_join_threshold_records"]
        proposals = {}
        for name in genomic:
            joins = sorted(
                {
                    clusters.get(other, other)
                    for other, count in alignment["records_with_neighbour"].get(name, {}).items()
                    if count > threshold
                }
            )
            proposals[name] = {"joins_clusters": joins, "proposed_cluster": joins[0] if len(joins) == 1 else ("+".join(joins) if joins else f"{name}-own")}
        write_json_atomic(staging / "distribution_audit.json", distributions)
        write_json_atomic(staging / "exact_dependency_audit.json", exact)
        write_json_atomic(staging / "alignment_dependency_audit.json", {**alignment, "proposals": proposals})
        shutil.rmtree(staging / "mmseqs" / "tmp", ignore_errors=True)
        manifest = {
            "audit": config["audit"]["name"],
            "config_sha256": sha256_file(args.config),
            "outputs": {p.name: sha256_file(p) for p in sorted(staging.iterdir()) if p.is_file()},
        }
        write_json_atomic(staging / "audit_manifest.json", manifest)
        staging.rename(OUT)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(json.dumps({"distributions": distributions, "exact_v3_overlaps": exact["overlaps_involving_v3"], "alignment": alignment["records_with_neighbour"], "proposals": proposals}, indent=1))


def _load_panel(panel: dict) -> list[dict]:
    if sha256_file(Path(panel["manifest"])) != panel["manifest_sha256"]:
        raise ValueError(f"manifest hash mismatch: {panel['panel_id']}")
    rows = list(csv.DictReader(Path(panel["ledger"]).open(encoding="utf-8")))
    if "positive_ledger" in panel:
        positives = {r["pair_id"]: r["positive_sequence"] for r in csv.DictReader(Path(panel["positive_ledger"]).open(encoding="utf-8"))}
        return [{"positive": positives[r["pair_id"]], "negative": r[panel["negative_column"]], "partition": r["partition"]} for r in rows]
    partitions = {}
    group_table = Path(panel["ledger"]).with_name("group_table.csv")
    for row in csv.DictReader(group_table.open(encoding="utf-8")):
        partitions[row["record_id"]] = row["partition"]
    return [{"positive": r["positive_sequence"], "negative": r[panel["negative_column"]], "partition": partitions[r["pair_id"]]} for r in rows]


def _gc(sequences) -> np.ndarray:
    return np.array([(s.count("G") + s.count("C")) / len(s) for s in sequences])


def _distribution(panel_id: str, rows: list[dict]) -> dict:
    positive, negative = [r["positive"] for r in rows], [r["negative"] for r in rows]
    test = [r for r in rows if r["partition"] == "test"]
    position, distance = maximum_positional_total_variation(positive, negative)
    pgc, ngc = _gc(positive), _gc(negative)
    tpgc, tngc = _gc([r["positive"] for r in test]), _gc([r["negative"] for r in test])
    return {
        "panel_id": panel_id,
        "pairs": len(rows),
        "test_pairs": len(test),
        "positive": asdict(summarize_class_distribution(positive)),
        "negative": asdict(summarize_class_distribution(negative)),
        "gc_mean_difference_positive_minus_negative": float(pgc.mean() - ngc.mean()),
        "mann_whitney_p": float(mannwhitneyu(pgc, ngc, alternative="two-sided").pvalue),
        "ks_p": float(ks_2samp(pgc, ngc).pvalue),
        "test_gc_mean_difference": float(tpgc.mean() - tngc.mean()),
        "test_mann_whitney_p": float(mannwhitneyu(tpgc, tngc, alternative="two-sided").pvalue),
        "max_positional_total_variation": {"position": position, "distance": distance},
    }


def _add_holm(rows: list[dict], column: str) -> None:
    order = sorted(range(len(rows)), key=lambda i: rows[i][column])
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(rows) - rank) * rows[index][column]))
        rows[index][f"{column}_holm"] = running


def _load_eligible(inputs: dict):
    manifest = yaml.safe_load(Path(inputs["dependency_manifest"]).read_text(encoding="utf-8"))
    datasets, clusters = {}, {}
    for entry in manifest["datasets"]:
        dataset_id = entry["dataset_id"]
        clusters[dataset_id] = entry["dependency_cluster_id"]
        labels = {0: set(), 1: set()}
        for path in sorted(Path(inputs["confirmatory_root"]).glob(f"{dataset_id}-p-*-n-*-*.csv")):
            for row in csv.DictReader(path.open(encoding="utf-8")):
                labels[int(row["label"])].add(row["sequence"].strip().upper())
        datasets[dataset_id] = labels
    return datasets, clusters


def _alignment_dependence(v3: dict, eligible: dict, config: dict, mmseqs: Path, staging: Path) -> dict:
    """Count records of each v3 dataset with a cross-dataset neighbour, per partner dataset."""

    records, owner = [], {}
    for name, labels in {**v3, **eligible}.items():
        if name.endswith(".cds"):
            continue
        for label, sequences in labels.items():
            for index, sequence in enumerate(sorted(sequences)):
                record_id = f"r{len(records)}"
                owner[record_id] = (name, label)
                records.append(GroupingRecord(record_id, sequence, label, record_id))
    grouping = yaml.safe_load(Path(config["dependency"]["alignment"]["search"]).read_text(encoding="utf-8"))
    settings = SearchSettings.from_config(grouping["search"])
    search = run_mmseqs_search(records, staging / "mmseqs", mmseqs, settings)
    neighbours = collections.defaultdict(lambda: collections.defaultdict(set))
    label_mix = collections.defaultdict(collections.Counter)
    for left, right in alignment_edges(Path(search["hits"]), settings):
        (ln, ll), (rn, rl) = owner[left], owner[right]
        if ln == rn:
            continue
        for a, b, al, bl, rec in ((ln, rn, ll, rl, left), (rn, ln, rl, ll, right)):
            if a in v3:
                neighbours[a][b].add(rec)
                label_mix[f"{a}|{b}"]["same_label" if al == bl else "opposite_label"] += 1
    return {
        "records_with_neighbour": {a: {b: len(s) for b, s in sorted(bs.items())} for a, bs in neighbours.items()},
        "edge_label_mix": {k: dict(v) for k, v in sorted(label_mix.items())},
        "mmseqs": {k: search[k] for k in ("binary_sha256", "version", "command_line", "hits_sha256")},
        "record_count": len(records),
    }


if __name__ == "__main__":
    main()
