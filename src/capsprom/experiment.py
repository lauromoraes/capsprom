"""Minimum viable classical experiment workflow with MLflow provenance."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .config import DataConfig, ExperimentConfig
from .features import build_feature_set, encode_sequences_as_vectors


@dataclass(frozen=True)
class DatasetSplit:
    row_ids: list[str]
    sequences: list[str]
    labels: list[int]


@dataclass(frozen=True)
class RunResult:
    run_id: str
    output_dir: Path
    metrics: dict[str, float]
    train_samples: int
    test_samples: int


def validate_dataset(path: Path, config: DataConfig) -> dict[str, int | str]:
    """Validate one CSV against the experiment's biological data contract."""

    split = read_dataset(path, config, max_samples=None)
    return {
        "path": path.as_posix(),
        "rows": len(split.labels),
        "positive": sum(split.labels),
        "negative": len(split.labels) - sum(split.labels),
        "sha256": sha256_file(path),
    }


def audit_dataset_pair(config: DataConfig) -> dict[str, object]:
    """Audit exact duplicates, label conflicts, and normalized train/test overlap."""

    train = read_dataset(config.train_csv, config, max_samples=None)
    test = read_dataset(config.test_csv, config, max_samples=None)
    train_counts = Counter(train.sequences)
    test_counts = Counter(test.sequences)
    train_labels = _labels_by_sequence(train)
    test_labels = _labels_by_sequence(test)
    overlap = set(train_counts) & set(test_counts)
    conflicting_train = {sequence for sequence, labels in train_labels.items() if len(labels) > 1}
    conflicting_test = {sequence for sequence, labels in test_labels.items() if len(labels) > 1}
    conflicting_across = {
        sequence for sequence in overlap if len(train_labels[sequence] | test_labels[sequence]) > 1
    }
    return {
        "train_rows": len(train.labels),
        "test_rows": len(test.labels),
        "train_unique_sequences": len(train_counts),
        "test_unique_sequences": len(test_counts),
        "train_duplicate_rows": sum(count - 1 for count in train_counts.values()),
        "test_duplicate_rows": sum(count - 1 for count in test_counts.values()),
        "train_conflicting_label_sequences": len(conflicting_train),
        "test_conflicting_label_sequences": len(conflicting_test),
        "train_test_overlap_unique_sequences": len(overlap),
        "train_rows_in_overlap": sum(train_counts[sequence] for sequence in overlap),
        "test_rows_in_overlap": sum(test_counts[sequence] for sequence in overlap),
        "train_test_conflicting_label_sequences": len(conflicting_across),
        "train_sha256": sha256_file(config.train_csv),
        "test_sha256": sha256_file(config.test_csv),
    }


def read_dataset(path: Path, config: DataConfig, max_samples: int | None) -> DatasetSplit:
    """Read, strictly validate, and optionally stratified-sample a dataset."""

    groups: dict[int, list[tuple[str, str]]] = {0: [], 1: []}
    alphabet = set(config.alphabet)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {config.sequence_column, config.label_column}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain columns {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            sequence = row[config.sequence_column].strip().upper()
            try:
                label = int(row[config.label_column])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{row_number} has a non-integer label") from exc
            if label not in groups:
                raise ValueError(f"{path}:{row_number} has non-binary label {label}")
            if len(sequence) != config.sequence_length:
                raise ValueError(
                    f"{path}:{row_number} has sequence length {len(sequence)}; expected {config.sequence_length}"
                )
            invalid = sorted(set(sequence) - alphabet)
            if invalid:
                raise ValueError(f"{path}:{row_number} has invalid sequence symbols {invalid}")
            row_id = f"row-{row_number - 1:09d}"
            groups[label].append((row_id, sequence))

    if not groups[0] or not groups[1]:
        raise ValueError(f"{path} must contain both binary classes")
    if max_samples is not None:
        groups = _stratified_sample(groups, max_samples, config.random_seed)

    pairs = [(row_id, sequence, label) for label, records in groups.items() for row_id, sequence in records]
    random.Random(config.random_seed).shuffle(pairs)
    return DatasetSplit(
        row_ids=[row_id for row_id, _, _ in pairs],
        sequences=[sequence for _, sequence, _ in pairs],
        labels=[label for _, _, label in pairs],
    )


def run_experiment(config: ExperimentConfig) -> RunResult:
    """Train, evaluate, and track the MVP logistic-regression experiment."""

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

    tracking_uri = _resolve_tracking_uri(config)
    mlflow.set_tracking_uri(tracking_uri)
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
        confusion = confusion_counts(test.labels, predictions)
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
            "confusion_matrix": confusion,
            "metrics": metrics,
        }
        (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

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
        mlflow.log_artifact(str(output_dir / "run_summary.json"), artifact_path="reports")
        mlflow.log_artifact(str(predictions_path), artifact_path="predictions")
        mlflow.log_artifact(str(fold_manifest_path), artifact_path="provenance")
        mlflow.log_param("log_model", config.outputs.log_model)
        if config.outputs.log_model:
            if config.model.name == "xgboost":
                mlflow.xgboost.log_model(
                    model,
                    name="model",
                    pip_requirements=pip_requirements,
                )
            else:
                mlflow.sklearn.log_model(
                    model,
                    name="model",
                    pip_requirements=pip_requirements,
                )

    return RunResult(run_id, output_dir, metrics, len(train.labels), len(test.labels))


def build_model(config: ExperimentConfig):
    """Build the configured classical model with explicit reproducibility defaults."""

    import sklearn

    if config.model.name == "logistic_regression":
        from sklearn.linear_model import LogisticRegression

        hyperparameters = {
            "max_iter": 1000,
            "class_weight": "balanced",
            "random_state": config.data.random_seed,
        }
        hyperparameters.update(config.model.hyperparameters)
        return LogisticRegression(**hyperparameters), hyperparameters, [f"scikit-learn=={sklearn.__version__}"]

    if config.model.name == "xgboost":
        import xgboost
        from xgboost import XGBClassifier

        hyperparameters = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "random_state": config.data.random_seed,
            "n_jobs": -1,
        }
        hyperparameters.update(config.model.hyperparameters)
        requirements = [f"scikit-learn=={sklearn.__version__}", f"xgboost=={xgboost.__version__}"]
        return XGBClassifier(**hyperparameters), hyperparameters, requirements

    raise ValueError(f"unsupported model {config.model.name!r}")


def encode_sequences_batched(sequences: Sequence[str], feature_set: object, batch_size: int = 4096):
    """Encode sequences into a compact float32 matrix without retaining Python float objects."""

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


def calculate_metrics(
    names: Sequence[str], labels: Sequence[int], predictions: Sequence[int], probabilities: Sequence[float]
) -> dict[str, float]:
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        balanced_accuracy_score,
        brier_score_loss,
        confusion_matrix,
        f1_score,
        log_loss,
        matthews_corrcoef,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    functions = {
        "accuracy": lambda: accuracy_score(labels, predictions),
        "average_precision": lambda: average_precision_score(labels, probabilities),
        "balanced_accuracy": lambda: balanced_accuracy_score(labels, predictions),
        "brier_score": lambda: brier_score_loss(labels, probabilities),
        "expected_calibration_error": lambda: expected_calibration_error(labels, probabilities),
        "precision": lambda: precision_score(labels, predictions, zero_division=0),
        "recall": lambda: recall_score(labels, predictions, zero_division=0),
        "f1": lambda: f1_score(labels, predictions, zero_division=0),
        "log_loss": lambda: log_loss(labels, probabilities, labels=[0, 1]),
        "roc_auc": lambda: roc_auc_score(labels, probabilities),
        "matthews_corrcoef": lambda: matthews_corrcoef(labels, predictions),
        "specificity": lambda: confusion_matrix(labels, predictions, labels=[0, 1])[0, 0]
        / sum(confusion_matrix(labels, predictions, labels=[0, 1])[0]),
    }
    return {name: float(functions[name]()) for name in names}


def expected_calibration_error(labels: Sequence[int], probabilities: Sequence[float], bins: int = 10) -> float:
    """Calculate ECE using deterministic equal-frequency probability bins."""

    import numpy as np

    if bins < 1:
        raise ValueError("bins must be at least 1")
    y_true = np.asarray(labels, dtype=np.float64)
    y_score = np.asarray(probabilities, dtype=np.float64)
    if len(y_true) == 0 or len(y_true) != len(y_score):
        raise ValueError("labels and probabilities must be non-empty and have equal length")
    if np.any((y_score < 0.0) | (y_score > 1.0)):
        raise ValueError("probabilities must be between 0 and 1")

    ordered = np.argsort(y_score, kind="stable")
    error = 0.0
    for indices in np.array_split(ordered, min(bins, len(ordered))):
        error += (len(indices) / len(ordered)) * abs(float(y_true[indices].mean() - y_score[indices].mean()))
    return error


def confusion_counts(labels: Sequence[int], predictions: Sequence[int]) -> dict[str, int]:
    """Return explicitly named binary confusion-matrix cells."""

    from sklearn.metrics import confusion_matrix

    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {"true_negative": int(tn), "false_positive": int(fp), "false_negative": int(fn), "true_positive": int(tp)}


def write_predictions(
    path: Path,
    row_ids: Sequence[str],
    labels: Sequence[int],
    probabilities: Sequence[float],
    predictions: Sequence[int],
) -> None:
    """Persist row-level test outputs without copying raw sequences."""

    lengths = {len(row_ids), len(labels), len(probabilities), len(predictions)}
    if len(lengths) != 1:
        raise ValueError("prediction columns must have equal lengths")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row_id", "y_true", "y_score", "y_pred"])
        writer.writerows(zip(row_ids, labels, probabilities, predictions, strict=True))


def write_fold_manifest(path: Path, row_ids: Sequence[str], labels: Sequence[int], folds: int = 5, seed: int = 42) -> None:
    """Persist a fixed stratified training-fold assignment for model selection."""

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stratified_sample(
    groups: dict[int, list[tuple[str, str]]], maximum: int, seed: int
) -> dict[int, list[tuple[str, str]]]:
    if maximum < 2:
        raise ValueError("sample limits must be at least 2 to retain both classes")
    total = sum(len(values) for values in groups.values())
    if maximum >= total:
        return groups
    rng = random.Random(seed)
    class_zero = maximum // 2
    targets = {0: min(class_zero, len(groups[0])), 1: min(maximum - class_zero, len(groups[1]))}
    unused = maximum - sum(targets.values())
    for label in (0, 1):
        available = len(groups[label]) - targets[label]
        addition = min(unused, available)
        targets[label] += addition
        unused -= addition
    return {label: rng.sample(values, targets[label]) for label, values in groups.items()}


def _labels_by_sequence(split: DatasetSplit) -> dict[str, set[int]]:
    labels: dict[str, set[int]] = defaultdict(set)
    for sequence, label in zip(split.sequences, split.labels, strict=True):
        labels[sequence].add(label)
    return labels


def _resolve_tracking_uri(config: ExperimentConfig) -> str:
    raw = config.tracking.tracking_uri
    if raw.startswith("sqlite:///") and not raw.startswith("sqlite:////"):
        relative_path = Path(raw.removeprefix("sqlite:///"))
        database_path = (config.path.parent.parent / relative_path).resolve()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{database_path.as_posix()}"
    if "://" in raw or raw.startswith("file:"):
        return raw
    path = Path(raw)
    if not path.is_absolute():
        path = config.path.parent.parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve().as_uri()
