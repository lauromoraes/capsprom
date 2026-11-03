"""Assign the frozen repeat-linked strata to graphpro-reconstructed-v3 records.

Reads the build's group tables and MMseqs2 hit tables (verified by SHA-256),
marks every record that has a non-self hit at the homology-grouping thresholds,
and writes one stratum table per dataset under a new output root.  It changes
no build and reads no model output.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
from pathlib import Path

import yaml

from capsprom.data.homology_grouping import SearchSettings, alignment_edges
from capsprom.data.loading import sha256_file
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/graphpro_reconstruction_v3_repeat_strata_v1.yaml"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    rule, inputs = config["stratum_rule"], config["inputs"]
    settings = SearchSettings(min_seq_id=rule["min_seq_id"], coverage=rule["coverage_both_sequences"])
    output = Path(config["output_root"])
    if output.exists():
        raise FileExistsError(f"{output} exists; strata are immutable")
    output.mkdir(parents=True)
    summary = {"config_sha256": sha256_file(args.config), "datasets": {}}
    for dataset, expected in inputs["hit_tables_sha256"].items():
        folder = Path(inputs["build_root"]) / dataset
        hits = folder / "mmseqs" / "hits.m8"
        if sha256_file(hits) != expected:
            raise ValueError(f"hit table hash mismatch for {dataset}")
        linked = {record for edge in alignment_edges(hits, settings) for record in edge}
        rows = []
        for row in csv.DictReader((folder / "group_table.csv").open(encoding="utf-8")):
            stratum = "repeat_linked" if row["record_id"] in linked else "not_repeat_linked"
            rows.append({"record_id": row["record_id"], "label": row["label"], "partition": row["partition"], "stratum": stratum})
        path = output / f"{dataset}_strata.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        counts = collections.Counter((r["stratum"], r["label"], r["partition"] == "test") for r in rows)
        summary["datasets"][dataset] = {
            "table_sha256": sha256_file(path),
            "counts": {f"{s}|label={lab}|{'test' if t else 'train'}": n for (s, lab, t), n in sorted(counts.items())},
        }
    write_json_atomic(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
