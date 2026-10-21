"""Strict YAML loading and MLflow tracking for training-only neural experiments."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from .config import DataConfig
from .data.loading import read_dataset, sha256_file
from .models.capsprom import CapsPromConfig, LegacyCapsProm1CConfig
from .neural_training import NeuralTrainingConfig, NeuralTrainingResult, run_training_only
from .tracking import resolve_tracking_uri


@dataclass(frozen=True)
class NeuralExperimentConfig:
    path: Path
    name: str
    train_csv: Path
    data: DataConfig
    maximum_samples: int | None
    training: NeuralTrainingConfig
    tracking_uri: str
    tracking_experiment: str


@dataclass(frozen=True)
class TrackedNeuralResult:
    run_id: str
    training: NeuralTrainingResult


def load_neural_experiment_config(path: Path | str) -> NeuralExperimentConfig:
    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    required = {"project", "data", "model", "training", "tracking", "outputs"}
    if not isinstance(raw, Mapping) or set(raw) != required:
        raise ValueError(f"neural configuration keys must be exactly {sorted(required)}")
    root = config_path.parent.parent
    project = _mapping(raw, "project")
    data = _mapping(raw, "data")
    model = _mapping(raw, "model")
    training = _mapping(raw, "training")
    tracking = _mapping(raw, "tracking")
    outputs = _mapping(raw, "outputs")
    _exact_keys(project, {"name"}, "project")
    _exact_keys(
        data,
        {"train_csv", "sequence_column", "label_column", "sequence_length", "maximum_samples"},
        "data",
    )
    _exact_keys(model, {"name", "architecture"}, "model")
    training_keys = {
        "random_seed",
        "validation_fraction",
        "batch_size",
        "learning_rate",
        "maximum_epochs",
        "patience",
        "reconstruction_weight",
    }
    accepted_training_keys = {
        frozenset(training_keys),
        frozenset(training_keys | {"contract_version", "reconstruction_reduction"}),
        frozenset(
            training_keys
            | {
                "contract_version",
                "reconstruction_reduction",
                "learning_rate_schedule",
                "learning_rate_decay",
            }
        ),
        frozenset(
            training_keys
            | {
                "contract_version",
                "reconstruction_reduction",
                "learning_rate_schedule",
                "learning_rate_decay",
                "warmup_initial_learning_rate",
                "warmup_epochs",
            }
        ),
    }
    if frozenset(training) not in accepted_training_keys:
        raise ValueError("training keys must match a supported neural contract schema")
    _exact_keys(tracking, {"tracking_uri", "experiment_name"}, "tracking")
    _exact_keys(outputs, {"checkpoint_path", "state_path"}, "outputs")
    train_csv = _path(root, data.get("train_csv"), must_exist=True)
    sequence_length = _positive_int(data, "sequence_length")
    model_name = _string(model, "name")
    architecture = _mapping(model, "architecture")
    architecture_keys = {
        "convolution_filters",
        "convolution_kernel",
        "primary_channels",
        "primary_dim",
        "primary_kernel",
        "primary_stride",
        "output_capsules",
        "output_dim",
        "routing_iterations",
        "routing_mode",
        "decoder_hidden",
    }
    accepted_architecture_keys = {
        frozenset(architecture_keys),
        frozenset(architecture_keys | {"routing_gradient_mode"}),
        frozenset(architecture_keys | {"routing_gradient_mode", "decoder_mode"}),
    }
    if frozenset(architecture) not in accepted_architecture_keys:
        raise ValueError(
            "model.architecture keys must match the canonical architecture schema"
        )
    output_capsules = _positive_int(architecture, "output_capsules")
    contract_version = int(training.get("contract_version", 2))
    config_type = LegacyCapsProm1CConfig if model_name == "capsprom_original_1c" else CapsPromConfig
    capsule = config_type(
        sequence_length=sequence_length,
        convolution_filters=_positive_int(architecture, "convolution_filters"),
        convolution_kernel=_positive_int(architecture, "convolution_kernel"),
        primary_channels=_positive_int(architecture, "primary_channels"),
        primary_dim=_positive_int(architecture, "primary_dim"),
        primary_kernel=_positive_int(architecture, "primary_kernel"),
        primary_stride=_positive_int(architecture, "primary_stride"),
        output_capsules=output_capsules,
        output_dim=_positive_int(architecture, "output_dim"),
        routing_iterations=_positive_int(architecture, "routing_iterations"),
        routing_mode=_string(architecture, "routing_mode"),
        routing_gradient_mode=str(architecture.get("routing_gradient_mode", "full")),
        decoder_mode=str(architecture.get("decoder_mode", "selected_vector")),
        decoder_hidden=tuple(_positive_int_list(architecture, "decoder_hidden", length=2)),
    )
    checkpoint_path = _path(root, outputs.get("checkpoint_path"), must_exist=False)
    state_path = _path(root, outputs.get("state_path"), must_exist=False)
    maximum_samples = data.get("maximum_samples")
    maximum_samples = None if maximum_samples is None else int(maximum_samples)
    neural_training = NeuralTrainingConfig(
        model_name=model_name,
        random_seed=int(training.get("random_seed", 42)),
        validation_fraction=float(training.get("validation_fraction", 0.2)),
        batch_size=_positive_int(training, "batch_size"),
        learning_rate=float(training.get("learning_rate", 0.001)),
        maximum_epochs=_positive_int(training, "maximum_epochs"),
        patience=_positive_int(training, "patience"),
        checkpoint_path=checkpoint_path,
        state_path=state_path,
        capsule=capsule,
        reconstruction_weight=float(training.get("reconstruction_weight", 0.0005)),
        reconstruction_reduction=str(training.get("reconstruction_reduction", "mean")),
        contract_version=contract_version,
        learning_rate_schedule=str(training.get("learning_rate_schedule", "fixed")),
        learning_rate_decay=float(training.get("learning_rate_decay", 1.0)),
        warmup_initial_learning_rate=(
            None
            if training.get("warmup_initial_learning_rate") is None
            else float(training["warmup_initial_learning_rate"])
        ),
        warmup_epochs=int(training.get("warmup_epochs", 0)),
    )
    data_config = DataConfig(
        train_csv=train_csv,
        test_csv=train_csv,
        sequence_column=str(data.get("sequence_column", "sequence")),
        label_column=str(data.get("label_column", "label")),
        sequence_length=sequence_length,
        alphabet=("A", "C", "G", "T"),
        max_train_samples=maximum_samples,
        max_test_samples=None,
        random_seed=neural_training.random_seed,
    )
    return NeuralExperimentConfig(
        path=config_path,
        name=_string(project, "name"),
        train_csv=train_csv,
        data=data_config,
        maximum_samples=maximum_samples,
        training=neural_training,
        tracking_uri=str(tracking.get("tracking_uri", "sqlite:///mlflow.db")),
        tracking_experiment=_string(tracking, "experiment_name"),
    )


def run_tracked_neural_training(config: NeuralExperimentConfig) -> TrackedNeuralResult:
    """Run and track inner-training development without loading an external test split."""

    import mlflow

    split = read_dataset(config.train_csv, config.data, config.maximum_samples)
    tracking_config = _TrackingAdapter(config)
    mlflow.set_tracking_uri(resolve_tracking_uri(tracking_config))
    mlflow.set_experiment(config.tracking_experiment)
    with mlflow.start_run(run_name=config.name) as active_run:
        result = run_training_only(split.sequences, split.labels, config.training)
        run_id = active_run.info.run_id
        config_sha256 = sha256_file(config.path)
        mlflow.log_params(
            {
                "mode": "training_only",
                "model": config.training.model_name,
                "random_seed": config.training.random_seed,
                "train_dataset_sha256": sha256_file(config.train_csv),
                "config_sha256": config_sha256,
                "inner_samples": len(split.labels),
                "validation_fraction": config.training.validation_fraction,
                "routing_mode": config.training.capsule.routing_mode,
                "routing_gradient_mode": (
                    config.training.capsule.routing_gradient_mode
                ),
                "output_capsules": config.training.capsule.output_capsules,
                "decoder_mode": config.training.capsule.decoder_mode,
                "reconstruction_reduction": config.training.reconstruction_reduction,
                "neural_contract_version": config.training.contract_version,
                "learning_rate_schedule": config.training.learning_rate_schedule,
                "learning_rate_decay": config.training.learning_rate_decay,
                "warmup_initial_learning_rate": (
                    config.training.warmup_initial_learning_rate
                    if config.training.warmup_initial_learning_rate is not None
                    else "none"
                ),
                "warmup_epochs": config.training.warmup_epochs,
            }
        )
        mlflow.log_metrics(
            {
                "best_inner_validation_mcc": result.best_validation_mcc,
                "best_epoch": float(result.best_epoch),
                "epochs_completed": float(result.epochs_completed),
            }
        )
        state = json.loads(config.training.state_path.read_text(encoding="utf-8"))
        for epoch_metrics in state.get("history", []):
            epoch = int(epoch_metrics["epoch"])
            trace = {
                key: float(value)
                for key, value in epoch_metrics.items()
                if key.startswith("validation_capsule_")
                or key.startswith("validation_correct_")
                or key.startswith("validation_incorrect_")
                or key.startswith("validation_true_")
                or key == "validation_predicted_positive_fraction"
                or key == "learning_rate"
            }
            if trace:
                mlflow.log_metrics(trace, step=epoch)
        mlflow.log_artifact(str(config.path), artifact_path="provenance")
        mlflow.log_artifact(str(config.training.state_path), artifact_path="provenance")
        mlflow.log_artifact(str(config.training.checkpoint_path), artifact_path="checkpoints")
    return TrackedNeuralResult(run_id=run_id, training=result)


@dataclass(frozen=True)
class _TrackingFields:
    tracking_uri: str


@dataclass(frozen=True)
class _TrackingAdapter:
    source: NeuralExperimentConfig

    @property
    def path(self) -> Path:
        return self.source.path

    @property
    def tracking(self) -> _TrackingFields:
        return _TrackingFields(self.source.tracking_uri)


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a mapping")
    return value


def _exact_keys(mapping: Mapping[str, Any], expected: set[str], context: str) -> None:
    if set(mapping) != expected:
        raise ValueError(f"{context} keys must be exactly {sorted(expected)}")


def _string(parent: Mapping[str, Any], key: str) -> str:
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


def _positive_int_list(parent: Mapping[str, Any], key: str, length: int) -> list[int]:
    raw = parent.get(key)
    if not isinstance(raw, list) or len(raw) != length:
        raise ValueError(f"{key} must be a list of {length} positive integers")
    values = [int(value) for value in raw]
    if min(values) < 1:
        raise ValueError(f"{key} must contain positive integers")
    return values


def _path(root: Path, value: object, must_exist: bool) -> Path:
    path = Path(str(value))
    path = path.resolve() if path.is_absolute() else (root / path).resolve()
    if must_exist and not path.is_file():
        raise ValueError(f"path does not exist: {path}")
    return path
