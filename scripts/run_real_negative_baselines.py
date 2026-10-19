"""Materialize or execute the canonical real-negative baseline batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capsprom.baseline_batch import execute_baseline_batch, materialize_baseline_batch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/real_negative_baseline_batch.yaml"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--model", choices=("logistic_regression", "xgboost"))
    parser.add_argument("--dataset")
    parser.add_argument("--max-runs", type=int)
    args = parser.parse_args()
    if args.execute:
        state = execute_baseline_batch(args.config, args.model, args.dataset, args.max_runs)
        print(json.dumps({"completed": len(state["completed"]), "planned": state["planned_run_count"]}))
    else:
        plan = materialize_baseline_batch(args.config)
        print(json.dumps({"planned": len(plan), "confirmatory": sum(x.tier == "confirmatory" for x in plan)}))


if __name__ == "__main__":
    main()
