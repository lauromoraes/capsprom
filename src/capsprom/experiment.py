"""Backward-compatible facade for the former monolithic experiment module."""

from .data.loading import DatasetSplit, audit_dataset_pair, read_dataset, sha256_file, validate_dataset
from .evaluation import calculate_metrics, confusion_counts, expected_calibration_error
from .models.classical import build_model
from .runner import RunResult, encode_sequences_batched, run_experiment, write_fold_manifest, write_predictions
from .tracking import resolve_tracking_uri

_resolve_tracking_uri = resolve_tracking_uri

__all__ = [
    "DatasetSplit",
    "RunResult",
    "audit_dataset_pair",
    "build_model",
    "calculate_metrics",
    "confusion_counts",
    "encode_sequences_batched",
    "expected_calibration_error",
    "read_dataset",
    "run_experiment",
    "sha256_file",
    "validate_dataset",
    "write_fold_manifest",
    "write_predictions",
]
