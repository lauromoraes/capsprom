"""Summarize paired canonical real-negative baseline runs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, wilcoxon


STATE = Path("outputs/reports/real_negative_baseline_batch/batch_state.json")
OUTPUT_DIR = Path("outputs/reports/real_negative_baseline_batch")


def predictions(path: Path) -> dict[str, tuple[int, int]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            row["row_id"]: (int(row["y_true"]), int(row["y_pred"]))
            for row in csv.DictReader(handle)
        }


def main() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    grouped: dict[str, dict[str, dict[str, object]]] = {}
    for key, run in state["completed"].items():
        if run["tier"] != "confirmatory":
            continue
        dataset, model = key.rsplit("--", 1)
        grouped.setdefault(dataset, {})[model] = run
    incomplete = sorted(dataset for dataset, models in grouped.items() if len(models) != 2)
    if incomplete or len(grouped) != 25:
        raise ValueError(f"expected 25 complete confirmatory pairs; incomplete={incomplete}")

    rows = []
    for dataset, models in sorted(grouped.items()):
        logistic = models["logistic_regression"]
        xgboost = models["xgboost"]
        logistic_mcc = float(logistic["metrics"]["matthews_corrcoef"])
        xgboost_mcc = float(xgboost["metrics"]["matthews_corrcoef"])
        logistic_predictions = predictions(Path(logistic["output_dir"]) / "test_predictions.csv")
        xgboost_predictions = predictions(Path(xgboost["output_dir"]) / "test_predictions.csv")
        if logistic_predictions.keys() != xgboost_predictions.keys():
            raise ValueError(f"prediction row identifiers differ for {dataset}")
        logistic_only = 0
        xgboost_only = 0
        for row_id, (label, logistic_pred) in logistic_predictions.items():
            xgb_label, xgb_pred = xgboost_predictions[row_id]
            if label != xgb_label:
                raise ValueError(f"true labels differ for {dataset}:{row_id}")
            logistic_correct = logistic_pred == label
            xgboost_correct = xgb_pred == label
            logistic_only += logistic_correct and not xgboost_correct
            xgboost_only += xgboost_correct and not logistic_correct
        discordant = logistic_only + xgboost_only
        mcnemar_p = 1.0 if discordant == 0 else binomtest(logistic_only, discordant, 0.5).pvalue
        rows.append(
            {
                "dataset": dataset,
                "logistic_mcc": logistic_mcc,
                "xgboost_mcc": xgboost_mcc,
                "mcc_difference_xgboost_minus_logistic": xgboost_mcc - logistic_mcc,
                "logistic_only_correct": logistic_only,
                "xgboost_only_correct": xgboost_only,
                "mcnemar_exact_p": mcnemar_p,
                "logistic_run_id": logistic["run_id"],
                "xgboost_run_id": xgboost["run_id"],
            }
        )

    differences = np.asarray([row["mcc_difference_xgboost_minus_logistic"] for row in rows])
    rng = np.random.default_rng(20260715)
    bootstrap = np.median(rng.choice(differences, size=(10000, len(differences))), axis=1)
    wilcoxon_result = wilcoxon(differences, alternative="two-sided", zero_method="wilcox")
    summary = {
        "dataset_count": len(rows),
        "primary_effect": "xgboost_mcc_minus_logistic_mcc",
        "median_paired_difference": float(np.median(differences)),
        "mean_paired_difference": float(np.mean(differences)),
        "bootstrap_median_ci95": [float(x) for x in np.quantile(bootstrap, [0.025, 0.975])],
        "wilcoxon_statistic": float(wilcoxon_result.statistic),
        "wilcoxon_two_sided_p": float(wilcoxon_result.pvalue),
        "xgboost_wins": int(np.sum(differences > 0)),
        "ties": int(np.sum(differences == 0)),
        "logistic_wins": int(np.sum(differences < 0)),
        "rows": rows,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "paired_baseline_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (OUTPUT_DIR / "paired_baseline_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
