"""Build versioned exploratory integrity views for released Human and Mouse."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

import yaml

from capsprom.data.integrity_treatment import treat_labeled_sequences
from capsprom.data.loading import sha256_file
from capsprom.data.sequences import read_fasta, write_fasta
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/graphpro_eukaryotic_integrity_v1.yaml"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent
    ) as temporary:
        staging = Path(temporary) / args.output_dir.name
        staging.mkdir()
        summaries = []
        all_removed = []
        for item in config["datasets"]:
            organism = item["organism"]
            positive_path = Path(item["positive"])
            negative_path = Path(item["negative"])
            _verify_hash(positive_path, item["positive_sha256"])
            _verify_hash(negative_path, item["negative_sha256"])
            positive = read_fasta(positive_path)
            negative = read_fasta(negative_path)
            result = treat_labeled_sequences(
                positive,
                negative,
                dataset=f"graphpro-released-{organism}",
                organism=organism,
                sequence_length=int(config["policy"]["sequence_length"]),
            )
            dataset_dir = staging / organism
            dataset_dir.mkdir()
            write_fasta(result.positive, dataset_dir / "positive.fa")
            write_fasta(result.negative, dataset_dir / "negative.fa")
            for removed in result.removed:
                all_removed.append(removed.as_dict())
            reason_counts = {
                reason: sum(row.reason == reason for row in result.removed)
                for reason in sorted({row.reason for row in result.removed})
            }
            summaries.append(
                {
                    "organism": organism,
                    "before": {"positive": len(positive), "negative": len(negative)},
                    "after": {
                        "positive": len(result.positive),
                        "negative": len(result.negative),
                    },
                    "removed": {
                        "positive": sum(
                            row.class_name == "positive" for row in result.removed
                        ),
                        "negative": sum(
                            row.class_name == "negative" for row in result.removed
                        ),
                    },
                    "removal_reasons": reason_counts,
                    "balance_difference_before": abs(len(positive) - len(negative)),
                    "balance_difference_after": abs(
                        len(result.positive) - len(result.negative)
                    ),
                    "outputs": {
                        "positive_sha256": sha256_file(dataset_dir / "positive.fa"),
                        "negative_sha256": sha256_file(dataset_dir / "negative.fa"),
                    },
                }
            )
        ledger_path = staging / "exclusion_ledger.csv"
        fields = [
            "dataset",
            "organism",
            "class_name",
            "source_index",
            "identifier",
            "description",
            "sequence_sha256",
            "reason",
        ]
        with ledger_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(all_removed)
        write_json_atomic(
            staging / "treatment_summary.json",
            {
                "schema_version": 1,
                "dataset_identity": config["dataset"]["name"],
                "config": str(args.config),
                "config_sha256": sha256_file(args.config),
                "confirmatory_use_enabled": False,
                "exclusion_ledger_sha256": sha256_file(ledger_path),
                "datasets": summaries,
            },
        )
        os.replace(staging, args.output_dir)
    print(json.dumps(summaries, indent=2))


def _verify_hash(path: Path, expected: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"hash mismatch for {path}: expected {expected}, observed {observed}")


if __name__ == "__main__":
    main()
