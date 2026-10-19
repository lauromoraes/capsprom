"""Materialize or execute the canonical ten-seed XGBoost replication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capsprom.xgboost_replication import execute_xgboost_replication, materialize_xgboost_replication


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/xgboost_ten_seed_replication_v2.yaml"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-runs", type=int)
    args = parser.parse_args()
    if args.execute:
        state = execute_xgboost_replication(args.config, args.max_runs)
        print(json.dumps({"completed": len(state["completed"]), "planned": state["planned_run_count"]}))
    else:
        plan = materialize_xgboost_replication(args.config)
        print(json.dumps({"planned": len(plan)}))


if __name__ == "__main__":
    main()
