"""Evaluation primitives shared by classical and neural experiments."""

from __future__ import annotations

from typing import Sequence


def calculate_metrics(
    names: Sequence[str],
    labels: Sequence[int],
    predictions: Sequence[int],
    probabilities: Sequence[float],
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


def expected_calibration_error(
    labels: Sequence[int], probabilities: Sequence[float], bins: int = 10
) -> float:
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
        error += (len(indices) / len(ordered)) * abs(
            float(y_true[indices].mean() - y_score[indices].mean())
        )
    return error


def confusion_counts(labels: Sequence[int], predictions: Sequence[int]) -> dict[str, int]:
    from sklearn.metrics import confusion_matrix

    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }
