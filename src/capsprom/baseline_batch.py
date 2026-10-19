"""Resumable orchestration for canonical real-negative classical baselines."""

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
from .state import write_json_atomic


@dataclass(frozen=True)
class PlannedBaselineRun:
    key: str
    dataset_id: str
    model: str
    tier: str
    config_path: Path
    config_sha256: str


def materialize_baseline_batch(batch_config: Path) -> list[PlannedBaselineRun]:
    """Validate one batch contract and write immutable per-run YAML configs."""

    config_path = batch_config.resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("batch configuration must be a YAML mapping")
    required = {"batch", "tracking", "features", "models", "evaluation", "outputs"}
    if set(raw) != required:
        raise ValueError(f"batch configuration keys must be exactly {sorted(required)}")
    batch = _mapping(raw, "batch")
    models = _mapping(raw, "models")
    if set(models) != {"logistic_regression", "xgboost"}:
        raise ValueError("models must define logistic_regression and xgboost")

    root = config_path.parent.parent
    dataset_dir = _resolve(root, batch.get("dataset_dir"))
    generated_dir = _resolve(root, batch.get("generated_config_dir"))
    artifact_dir = _resolve(root, _mapping(raw, "outputs").get("artifact_dir"))
    excluded = {str(value) for value in batch.get("excluded_from_confirmatory", [])}
    seed = int(batch.get("random_seed", 42))
    generated_dir.mkdir(parents=True, exist_ok=True)

    tracking = dict(_mapping(raw, "tracking"))
    tracking_uri = str(tracking.get("tracking_uri", ""))
    if tracking_uri == "sqlite:///mlflow.db":
        tracking["tracking_uri"] = f"sqlite:///{(root / 'mlflow.db').as_posix()}"
    pairs = discover_dataset_pairs(dataset_dir, ("cdbprom", "cnnprom", "graphpro"))
    plan: list[PlannedBaselineRun] = []
    for train, test in pairs:
        tier = "exploratory" if train.identity in excluded else "confirmatory"
        for model_name, hyperparameters in sorted(models.items()):
            key = f"{train.identity}--{model_name}"
            derived = {
                "project": {"name": f"{tier}-{key}"},
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
                "model": {"name": model_name, "hyperparameters": dict(hyperparameters)},
                "evaluation": dict(_mapping(raw, "evaluation")),
                "outputs": {"artifact_dir": artifact_dir.as_posix()},
            }
            run_config = generated_dir / f"{key}.yaml"
            content = yaml.safe_dump(derived, sort_keys=False)
            if run_config.exists() and run_config.read_text(encoding="utf-8") != content:
                raise ValueError(f"refusing to overwrite changed generated config: {run_config}")
            run_config.write_text(content, encoding="utf-8")
            load_experiment_config(run_config)
            plan.append(
                PlannedBaselineRun(
                    key=key,
                    dataset_id=train.identity,
                    model=model_name,
                    tier=tier,
                    config_path=run_config,
                    config_sha256=hashlib.sha256(content.encode()).hexdigest(),
                )
            )
    _write_plan(_resolve(root, batch.get("state_path")), config_path, plan)
    return plan


def execute_baseline_batch(
    batch_config: Path,
    model: str | None = None,
    dataset: str | None = None,
    tier: str | None = None,
    max_runs: int | None = None,
) -> dict[str, Any]:
    """Execute pending planned runs and persist state after every completion."""

    plan = materialize_baseline_batch(batch_config)
    raw = yaml.safe_load(batch_config.resolve().read_text(encoding="utf-8"))
    root = batch_config.resolve().parent.parent
    state_path = _resolve(root, _mapping(raw, "batch").get("state_path"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    completed = state.setdefault("completed", {})
    selected = [
        item
        for item in plan
        if item.key not in completed
        and (model is None or item.model == model)
        and (dataset is None or item.dataset_id == dataset)
        and (tier is None or item.tier == tier)
    ]
    if max_runs is not None:
        selected = selected[:max_runs]
    for item in selected:
        result = run_experiment(load_experiment_config(item.config_path))
        completed[item.key] = {
            "run_id": result.run_id,
            "output_dir": result.output_dir.as_posix(),
            "metrics": result.metrics,
            "config_sha256": item.config_sha256,
            "tier": item.tier,
        }
        write_json_atomic(state_path, state)
    return state


def _write_plan(state_path: Path, batch_config: Path, plan: list[PlannedBaselineRun]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    batch_hash = hashlib.sha256(batch_config.read_bytes()).hexdigest()
    if state_path.exists():
        existing = json.loads(state_path.read_text(encoding="utf-8"))
        existing_hash = existing.get("batch_config_sha256")
        if existing_hash != batch_hash:
            raise ValueError(
                "batch configuration changed after state creation; use a new batch name and state path"
            )
        existing_configs = {item["key"]: item["config_sha256"] for item in existing.get("plan", [])}
        current_configs = {item.key: item.config_sha256 for item in plan}
        if existing_configs != current_configs:
            raise ValueError("derived run plan changed after state creation")
    payload = {
        "batch_config": batch_config.as_posix(),
        "batch_config_sha256": batch_hash,
        "planned_run_count": len(plan),
        "confirmatory_run_count": sum(item.tier == "confirmatory" for item in plan),
        "exploratory_run_count": sum(item.tier == "exploratory" for item in plan),
        "plan": [{**asdict(item), "config_path": item.config_path.as_posix()} for item in plan],
        "completed": existing.get("completed", {}),
    }
    write_json_atomic(state_path, payload)


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a mapping")
    return value


def _resolve(root: Path, value: object) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (root / path).resolve()
