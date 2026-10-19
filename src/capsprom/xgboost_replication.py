"""Resumable ten-seed XGBoost replication for canonical real-negative data."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from .config import load_experiment_config
from .data.batch_audit import discover_dataset_pairs
from .experiment import run_experiment


@dataclass(frozen=True)
class PlannedReplicationRun:
    key: str
    dataset_id: str
    seed: int
    config_path: Path
    config_sha256: str


def materialize_xgboost_replication(config: Path) -> list[PlannedReplicationRun]:
    """Freeze per-dataset, per-seed configs and initialize reusable seed-42 runs."""

    config_path = config.resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("replication configuration must be a YAML mapping")
    required = {"replication", "tracking", "features", "model", "evaluation", "outputs"}
    if set(raw) != required:
        raise ValueError(f"replication configuration keys must be exactly {sorted(required)}")
    replication = _mapping(raw, "replication")
    model = _mapping(raw, "model")
    if model.get("name") != "xgboost":
        raise ValueError("model.name must be xgboost")

    root = config_path.parent.parent
    dataset_dir = _resolve(root, replication.get("dataset_dir"))
    generated_dir = _resolve(root, replication.get("generated_config_dir"))
    artifact_dir = _resolve(root, _mapping(raw, "outputs").get("artifact_dir"))
    excluded = {str(value) for value in replication.get("excluded_datasets", [])}
    seeds = [int(value) for value in replication.get("seeds", [])]
    if len(seeds) != 10 or len(set(seeds)) != 10:
        raise ValueError("replication.seeds must contain exactly ten unique seeds")
    generated_dir.mkdir(parents=True, exist_ok=True)

    tracking = dict(_mapping(raw, "tracking"))
    if tracking.get("tracking_uri") == "sqlite:///mlflow.db":
        tracking["tracking_uri"] = f"sqlite:///{(root / 'mlflow.db').as_posix()}"
    pairs = discover_dataset_pairs(dataset_dir, ("cdbprom", "cnnprom", "graphpro"))
    plan: list[PlannedReplicationRun] = []
    for train, test in pairs:
        if train.identity in excluded:
            continue
        for seed in seeds:
            key = f"{train.identity}--xgboost--seed-{seed}"
            derived = {
                "project": {"name": f"confirmatory-{key}"},
                "tracking": tracking,
                "data": {
                    "train_csv": train.path.as_posix(),
                    "test_csv": test.path.as_posix(),
                    "sequence_column": "sequence",
                    "label_column": "label",
                    "sequence_length": 81,
                    "alphabet": ["A", "C", "G", "T"],
                    "max_train_samples": None,
                    "max_test_samples": None,
                    "random_seed": seed,
                },
                "features": dict(_mapping(raw, "features")),
                "model": dict(model),
                "evaluation": dict(_mapping(raw, "evaluation")),
                "outputs": {"artifact_dir": artifact_dir.as_posix()},
            }
            run_config = generated_dir / f"{key}.yaml"
            content = yaml.safe_dump(derived, sort_keys=False)
            if run_config.exists() and run_config.read_text(encoding="utf-8") != content:
                raise ValueError(f"refusing to overwrite changed generated config: {run_config}")
            run_config.write_text(content, encoding="utf-8")
            load_experiment_config(run_config)
            plan.append(PlannedReplicationRun(
                key=key,
                dataset_id=train.identity,
                seed=seed,
                config_path=run_config,
                config_sha256=hashlib.sha256(content.encode()).hexdigest(),
            ))
    _write_state(root, config_path, replication, plan)
    return plan


def execute_xgboost_replication(config: Path, max_runs: int | None = None) -> dict[str, Any]:
    """Execute pending replications and persist state after every completed run."""

    plan = materialize_xgboost_replication(config)
    raw = yaml.safe_load(config.resolve().read_text(encoding="utf-8"))
    root = config.resolve().parent.parent
    state_path = _resolve(root, _mapping(raw, "replication").get("state_path"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    completed = state["completed"]
    pending = [item for item in plan if item.key not in completed]
    if max_runs is not None:
        pending = pending[:max_runs]
    for item in pending:
        result = run_experiment(load_experiment_config(item.config_path))
        completed[item.key] = {
            "run_id": result.run_id,
            "output_dir": result.output_dir.as_posix(),
            "metrics": result.metrics,
            "config_sha256": item.config_sha256,
            "seed": item.seed,
            "reused": False,
        }
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def _write_state(root: Path, config: Path, spec: Mapping[str, Any], plan: list[PlannedReplicationRun]) -> None:
    state_path = _resolve(root, spec.get("state_path"))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    config_hash = hashlib.sha256(config.read_bytes()).hexdigest()
    existing = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    if existing and existing.get("replication_config_sha256") != config_hash:
        raise ValueError("replication configuration changed after state creation; use a new state path")
    completed = existing.get("completed", {})
    source_state = json.loads(_resolve(root, spec.get("reuse_state_path")).read_text(encoding="utf-8"))
    reuse_seed = int(spec.get("reuse_seed", 42))
    by_key = {item.key: item for item in plan}
    for source_key, run in source_state["completed"].items():
        if run.get("tier") != "confirmatory" or not source_key.endswith("--xgboost"):
            continue
        dataset = source_key.removesuffix("--xgboost")
        target_key = f"{dataset}--xgboost--seed-{reuse_seed}"
        if target_key in by_key and target_key not in completed:
            completed[target_key] = {
                **run,
                "config_sha256": by_key[target_key].config_sha256,
                "seed": reuse_seed,
                "reused": True,
                "source_batch_key": source_key,
            }
    payload = {
        "replication_config": config.as_posix(),
        "replication_config_sha256": config_hash,
        "planned_run_count": len(plan),
        "reused_run_count": sum(bool(run.get("reused")) for run in completed.values()),
        "plan": [{**asdict(item), "config_path": item.config_path.as_posix()} for item in plan],
        "completed": completed,
    }
    state_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a mapping")
    return value


def _resolve(root: Path, value: object) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (root / path).resolve()
