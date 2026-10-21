"""Classical experiment orchestration with MLflow provenance."""

from __future__ import annotations

import csv
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .config import ExperimentConfig
from .data.loading import read_dataset, sha256_file
from .evaluation import calculate_metrics, confusion_counts
from .features import build_feature_set, encode_sequences_as_vectors
from .models.classical import build_model
from .tracking import resolve_tracking_uri


@dataclass(frozen=True)
class RunResult:
    run_id: str
    output_dir: Path
    metrics: dict[str, float]
    train_samples: int
    test_samples: int


def run_experiment(config: ExperimentConfig) -> RunResult:
    import mlflow
    import mlflow.sklearn
    import mlflow.xgboost

    train = read_dataset(config.data.train_csv, config.data, config.data.max_train_samples)
    test = read_dataset(config.data.test_csv, config.data, config.data.max_test_samples)
    feature_set = build_feature_set(config.features)
    encode_started = time.perf_counter()
    x_train = encode_sequences_batched(train.sequences, feature_set)
    x_test = encode_sequences_batched(test.sequences, feature_set)
    encode_seconds = time.perf_counter() - encode_started
    model, hyperparameters, pip_requirements = build_model(config)
    train_started = time.perf_counter()
    model.fit(x_train, train.labels)
    train_seconds = time.perf_counter() - train_started
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    metrics = calculate_metrics(config.metrics, test.labels, predictions, probabilities)
    metrics.update({"encode_seconds": encode_seconds, "train_seconds": train_seconds})

    mlflow.set_tracking_uri(resolve_tracking_uri(config))
    mlflow.set_experiment(config.tracking.experiment_name)
    with mlflow.start_run(run_name=config.name) as active_run:
        run_id = active_run.info.run_id
        output_dir = config.outputs.artifact_dir / run_id
        output_dir.mkdir(parents=True, exist_ok=False)
        shutil.copy2(config.path, output_dir / "experiment.yaml")
        predictions_path = output_dir / "test_predictions.csv"
        write_predictions(predictions_path, test.row_ids, test.labels, probabilities, predictions)
        fold_manifest_path = output_dir / "training_fold_manifest.csv"
        write_fold_manifest(fold_manifest_path, train.row_ids, train.labels)
        summary = {
            "run_id": run_id,
            "experiment": config.name,
            "train_samples": len(train.labels),
            "test_samples": len(test.labels),
            "train_dataset_sha256": sha256_file(config.data.train_csv),
            "test_dataset_sha256": sha256_file(config.data.test_csv),
            "feature_blocks": [block.name for block in config.features.blocks],
            "feature_count": int(x_train.shape[1]),
            "train_matrix_mib": x_train.nbytes / (1024**2),
            "test_matrix_mib": x_test.nbytes / (1024**2),
            "random_seed": config.data.random_seed,
            "training_fold_seed": 42,
            "training_fold_manifest_sha256": sha256_file(fold_manifest_path),
            "confusion_matrix": confusion_counts(test.labels, predictions),
            "metrics": metrics,
        }
        summary_path = output_dir / "run_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        mlflow.log_params(
            {
                "model": config.model.name,
                "random_seed": config.data.random_seed,
                "train_samples": len(train.labels),
                "test_samples": len(test.labels),
                "train_dataset_sha256": summary["train_dataset_sha256"],
                "test_dataset_sha256": summary["test_dataset_sha256"],
                "feature_blocks": ",".join(summary["feature_blocks"]),
                "feature_count": summary["feature_count"],
                "train_matrix_mib": summary["train_matrix_mib"],
                "test_matrix_mib": summary["test_matrix_mib"],
                "training_fold_seed": summary["training_fold_seed"],
                "training_fold_manifest_sha256": summary["training_fold_manifest_sha256"],
                **{f"model.{key}": value for key, value in hyperparameters.items()},
            }
        )
        mlflow.log_metrics(metrics)
        mlflow.log_artifact(str(output_dir / "experiment.yaml"), artifact_path="provenance")
        mlflow.log_artifact(str(summary_path), artifact_path="reports")
        mlflow.log_artifact(str(predictions_path), artifact_path="predictions")
        mlflow.log_artifact(str(fold_manifest_path), artifact_path="provenance")
        mlflow.log_param("log_model", config.outputs.log_model)
        if config.outputs.log_model:
            if config.model.name == "xgboost":
                mlflow.xgboost.log_model(model, name="model", pip_requirements=pip_requirements)
            else:
                mlflow.sklearn.log_model(model, name="model", pip_requirements=pip_requirements)
    return RunResult(run_id, output_dir, metrics, len(train.labels), len(test.labels))


def encode_sequences_batched(
    sequences: Sequence[str], feature_set: object, batch_size: int = 4096
):
    import numpy as np

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if not sequences:
        raise ValueError("at least one sequence is required for feature encoding")
    matrix = None
    for start in range(0, len(sequences), batch_size):
        vectors = encode_sequences_as_vectors(sequences[start : start + batch_size], feature_set)
        batch = np.asarray(vectors, dtype=np.float32)
        if batch.ndim != 2:
            raise ValueError("feature encoder must produce a two-dimensional matrix")
        if matrix is None:
            matrix = np.empty((len(sequences), batch.shape[1]), dtype=np.float32)
        elif batch.shape[1] != matrix.shape[1]:
            raise ValueError("feature encoder produced inconsistent vector lengths")
        matrix[start : start + len(batch)] = batch
    return matrix


def write_predictions(
    path: Path,
    row_ids: Sequence[str],
    labels: Sequence[int],
    probabilities: Sequence[float],
    predictions: Sequence[int],
) -> None:
    if len({len(row_ids), len(labels), len(probabilities), len(predictions)}) != 1:
        raise ValueError("prediction columns must have equal lengths")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row_id", "y_true", "y_score", "y_pred"])
        writer.writerows(zip(row_ids, labels, probabilities, predictions, strict=True))


def write_fold_manifest(
    path: Path, row_ids: Sequence[str], labels: Sequence[int], folds: int = 5, seed: int = 42
) -> None:
    import numpy as np
    from sklearn.model_selection import StratifiedKFold

    if len(row_ids) != len(labels):
        raise ValueError("row_ids and labels must have equal lengths")
    assignments = np.empty(len(labels), dtype=np.int16)
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    positions = np.arange(len(labels))
    for fold, (_, validation_indices) in enumerate(splitter.split(positions, labels)):
        assignments[validation_indices] = fold
    rows = sorted(zip(row_ids, labels, assignments.tolist(), strict=True), key=lambda row: row[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row_id", "label", "fold"])
        writer.writerows(rows)
