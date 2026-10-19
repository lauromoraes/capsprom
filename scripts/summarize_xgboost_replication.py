"""Summarize ten-seed XGBoost replication against deterministic logistic runs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon


REPLICATION_STATE = Path("outputs/reports/xgboost_ten_seed_replication/replication_state.json")
BASELINE_STATE = Path("outputs/reports/real_negative_baseline_batch/batch_state.json")
OUTPUT_DIR = REPLICATION_STATE.parent


def main() -> None:
    replication = json.loads(REPLICATION_STATE.read_text(encoding="utf-8"))
    if len(replication["completed"]) != replication["planned_run_count"]:
        raise ValueError(
            f"replication incomplete: {len(replication['completed'])}/"
            f"{replication['planned_run_count']} runs completed"
        )
    baseline = json.loads(BASELINE_STATE.read_text(encoding="utf-8"))
    logistic = {
        key.removesuffix("--logistic_regression"): run
        for key, run in baseline["completed"].items()
        if run.get("tier") == "confirmatory" and key.endswith("--logistic_regression")
    }
    grouped: dict[str, list[dict[str, object]]] = {}
    for key, run in replication["completed"].items():
        dataset = key.split("--xgboost--seed-", 1)[0]
        grouped.setdefault(dataset, []).append(run)
    if set(grouped) != set(logistic):
        raise ValueError("replication and deterministic baseline dataset sets differ")

    rows = []
    for dataset in sorted(grouped):
        runs = sorted(grouped[dataset], key=lambda run: int(run["seed"]))
        if len(runs) != 10:
            raise ValueError(f"expected ten seeds for {dataset}; found {len(runs)}")
        values = np.asarray([float(run["metrics"]["matthews_corrcoef"]) for run in runs])
        logistic_mcc = float(logistic[dataset]["metrics"]["matthews_corrcoef"])
        q1, q3 = np.quantile(values, [0.25, 0.75])
        median = float(np.median(values))
        rows.append({
            "dataset": dataset,
            "logistic_mcc": logistic_mcc,
            "xgboost_median_mcc": median,
            "xgboost_mcc_q1": float(q1),
            "xgboost_mcc_q3": float(q3),
            "xgboost_mcc_mean": float(np.mean(values)),
            "xgboost_mcc_std": float(np.std(values, ddof=1)),
            "median_difference_xgboost_minus_logistic": median - logistic_mcc,
            "seeds": ";".join(str(run["seed"]) for run in runs),
            "run_ids": ";".join(str(run["run_id"]) for run in runs),
        })

    differences = np.asarray([row["median_difference_xgboost_minus_logistic"] for row in rows])
    rng = np.random.default_rng(20261019)
    bootstrap = np.median(rng.choice(differences, size=(10000, len(differences))), axis=1)
    test = wilcoxon(differences, alternative="two-sided", zero_method="wilcox")
    summary = {
        "dataset_count": len(rows),
        "seed_count": 10,
        "primary_effect": "median_xgboost_mcc_minus_deterministic_logistic_mcc",
        "median_paired_difference": float(np.median(differences)),
        "mean_paired_difference": float(np.mean(differences)),
        "bootstrap_median_ci95": [float(x) for x in np.quantile(bootstrap, [0.025, 0.975])],
        "wilcoxon_statistic": float(test.statistic),
        "wilcoxon_two_sided_p": float(test.pvalue),
        "xgboost_wins": int(np.sum(differences > 0)),
        "ties": int(np.sum(differences == 0)),
        "logistic_wins": int(np.sum(differences < 0)),
        "rows": rows,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "ten_seed_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (OUTPUT_DIR / "ten_seed_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
