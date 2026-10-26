"""Consolidate completed classical baselines for the active eligible scope."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import wilcoxon


CONFIG = Path("configs/active_baseline_consolidation_v1.yaml")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def consolidate(config_path: Path = CONFIG) -> dict[str, object]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    scope = config["scope"]
    inputs = config["inputs"]
    statistics = config["statistics"]

    eligibility_path = Path(scope["eligibility_manifest"])
    if _sha256(eligibility_path) != scope["eligibility_manifest_sha256"]:
        raise ValueError("eligibility manifest hash does not match the frozen contract")
    eligibility = yaml.safe_load(eligibility_path.read_text(encoding="utf-8"))
    expected_from_manifest = sum(
        int(eligibility["eligible_sources"][prefix]["dataset_count"])
        for prefix in scope["included_source_prefixes"]
    )
    if expected_from_manifest != int(scope["expected_dataset_count"]):
        raise ValueError("eligible dataset count differs from the frozen contract")

    summary_path = Path(inputs["completed_summary"])
    if _sha256(summary_path) != inputs["completed_summary_sha256"]:
        raise ValueError("completed summary hash does not match the frozen contract")
    completed = json.loads(summary_path.read_text(encoding="utf-8"))
    prefixes = tuple(f"{prefix}-" for prefix in scope["included_source_prefixes"])
    rows = [row for row in completed["rows"] if row["dataset"].startswith(prefixes)]
    if len(rows) != int(scope["expected_dataset_count"]):
        raise ValueError(f"expected {scope['expected_dataset_count']} eligible datasets; found {len(rows)}")
    if any(row["dataset"].startswith("graphpro-") for row in rows):
        raise ValueError("GraphPro result entered the active consolidation")

    differences = np.asarray(
        [float(row["median_difference_xgboost_minus_logistic"]) for row in rows]
    )
    rng = np.random.default_rng(int(statistics["bootstrap_seed"]))
    bootstrap = np.median(
        rng.choice(
            differences,
            size=(int(statistics["bootstrap_resamples"]), len(differences)),
        ),
        axis=1,
    )
    alpha = 1.0 - float(statistics["confidence_level"])
    test = wilcoxon(differences, alternative="two-sided", zero_method="wilcox")
    result: dict[str, object] = {
        "contract": config["consolidation"]["name"],
        "eligibility_manifest": scope["eligibility_manifest"],
        "dataset_count": len(rows),
        "included_sources": list(scope["included_source_prefixes"]),
        "excluded_sources": list(scope["excluded_source_prefixes"]),
        "seed_count": int(inputs["xgboost_seed_count"]),
        "primary_effect": statistics["primary_effect"],
        "median_paired_difference": float(np.median(differences)),
        "mean_paired_difference": float(np.mean(differences)),
        "bootstrap_median_ci95": [
            float(value) for value in np.quantile(bootstrap, [alpha / 2, 1 - alpha / 2])
        ],
        "wilcoxon_statistic": float(test.statistic),
        "wilcoxon_two_sided_p": float(test.pvalue),
        "xgboost_wins": int(np.sum(differences > 0)),
        "ties": int(np.sum(differences == 0)),
        "logistic_wins": int(np.sum(differences < 0)),
        "rows": rows,
    }
    output = config["outputs"]
    output_dir = Path(output["directory"])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / output["json"]).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / output["csv"]).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return result


def main() -> None:
    result = consolidate()
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
