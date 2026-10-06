"""Strict configuration loading for reproducible CapsProm experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from .features import FeatureEngineeringSpec, feature_spec_from_mapping


@dataclass(frozen=True)
class DataConfig:
    train_csv: Path
    test_csv: Path
    sequence_column: str
    label_column: str
    sequence_length: int
    alphabet: tuple[str, ...]
    max_train_samples: int | None
    max_test_samples: int | None
    random_seed: int


@dataclass(frozen=True)
class ModelConfig:
    name: str
    hyperparameters: dict[str, Any]


@dataclass(frozen=True)
class TrackingConfig:
    tracking_uri: str
    experiment_name: str


@dataclass(frozen=True)
class OutputConfig:
    artifact_dir: Path


@dataclass(frozen=True)
class ExperimentConfig:
    path: Path
    name: str
    data: DataConfig
    features: FeatureEngineeringSpec
    raw_features: Mapping[str, Any]
    model: ModelConfig
    metrics: tuple[str, ...]
    tracking: TrackingConfig
    outputs: OutputConfig


_ROOT_KEYS = {"project", "tracking", "data", "features", "model", "evaluation", "outputs"}
_METRICS = {
    "accuracy",
    "average_precision",
    "balanced_accuracy",
    "brier_score",
    "expected_calibration_error",
    "f1",
    "log_loss",
    "matthews_corrcoef",
    "precision",
    "recall",
    "roc_auc",
    "specificity",
}


def load_experiment_config(path: Path | str) -> ExperimentConfig:
    """Load and validate an MVP experiment configuration."""

    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("experiment configuration must be a YAML mapping")
    unknown = sorted(set(raw) - _ROOT_KEYS)
    if unknown:
        raise ValueError(f"unknown top-level configuration keys: {unknown}")
    missing = sorted(_ROOT_KEYS - set(raw))
    if missing:
        raise ValueError(f"missing top-level configuration keys: {missing}")

    base_dir = config_path.parent.parent
    project = _mapping(raw, "project")
    data = _mapping(raw, "data")
    features = _mapping(raw, "features")
    model = _mapping(raw, "model")
    evaluation = _mapping(raw, "evaluation")
    tracking = _mapping(raw, "tracking")
    outputs = _mapping(raw, "outputs")

    experiment_name = _non_empty(project, "name")
    train_csv = _path(data, "train_csv", base_dir)
    test_csv = _path(data, "test_csv", base_dir)
    for dataset_path in (train_csv, test_csv):
        if not dataset_path.is_file():
            raise ValueError(f"dataset does not exist: {dataset_path}")

    sequence_length = _positive_int(data, "sequence_length")
    alphabet_raw = data.get("alphabet")
    if not isinstance(alphabet_raw, list) or not alphabet_raw:
        raise ValueError("data.alphabet must be a non-empty list")
    alphabet = tuple(str(symbol).upper() for symbol in alphabet_raw)
    if len(set(alphabet)) != len(alphabet):
        raise ValueError("data.alphabet contains duplicate symbols")

    feature_spec = feature_spec_from_mapping(features, base_dir=base_dir)
    if feature_spec.combination_mode != "concatenate":
        raise ValueError("the MVP classical baseline requires features.combination_mode='concatenate'")

    model_name = _non_empty(model, "name")
    if model_name not in {"logistic_regression", "xgboost"}:
        raise ValueError("model.name must be 'logistic_regression' or 'xgboost'")
    hyperparameters = model.get("hyperparameters", {})
    if not isinstance(hyperparameters, Mapping):
        raise ValueError("model.hyperparameters must be a mapping")

    metrics_raw = evaluation.get("metrics")
    if not isinstance(metrics_raw, list) or not metrics_raw:
        raise ValueError("evaluation.metrics must be a non-empty list")
    metrics = tuple(str(metric) for metric in metrics_raw)
    unsupported = sorted(set(metrics) - _METRICS)
    if unsupported:
        raise ValueError(f"unsupported evaluation metrics: {unsupported}")

    return ExperimentConfig(
        path=config_path,
        name=experiment_name,
        data=DataConfig(
            train_csv=train_csv,
            test_csv=test_csv,
            sequence_column=str(data.get("sequence_column", "sequence")),
            label_column=str(data.get("label_column", "label")),
            sequence_length=sequence_length,
            alphabet=alphabet,
            max_train_samples=_optional_positive_int(data, "max_train_samples"),
            max_test_samples=_optional_positive_int(data, "max_test_samples"),
            random_seed=int(data.get("random_seed", 42)),
        ),
        features=feature_spec,
        raw_features=features,
        model=ModelConfig(name=model_name, hyperparameters=dict(hyperparameters)),
        metrics=metrics,
        tracking=TrackingConfig(
            tracking_uri=str(tracking.get("tracking_uri", "./mlruns")),
            experiment_name=_non_empty(tracking, "experiment_name"),
        ),
        outputs=OutputConfig(artifact_dir=_path(outputs, "artifact_dir", base_dir, must_exist=False)),
    )


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a mapping")
    return value


def _non_empty(parent: Mapping[str, Any], key: str) -> str:
    value = str(parent.get(key, "")).strip()
    if not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _positive_int(parent: Mapping[str, Any], key: str) -> int:
    try:
        value = int(parent[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a positive integer") from exc
    if value < 1:
        raise ValueError(f"{key} must be a positive integer")
    return value


def _optional_positive_int(parent: Mapping[str, Any], key: str) -> int | None:
    if parent.get(key) is None:
        return None
    return _positive_int(parent, key)


def _path(parent: Mapping[str, Any], key: str, base_dir: Path, must_exist: bool = True) -> Path:
    value = _non_empty(parent, key)
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    path = path.resolve()
    if must_exist and not path.exists():
        raise ValueError(f"{key} does not exist: {path}")
    return path
