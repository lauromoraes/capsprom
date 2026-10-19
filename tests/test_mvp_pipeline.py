import csv
from pathlib import Path

import pytest

from capsprom.config import load_experiment_config
from capsprom.experiment import (
    audit_dataset_pair,
    calculate_metrics,
    encode_sequences_batched,
    expected_calibration_error,
    read_dataset,
    write_fold_manifest,
    write_predictions,
)
from capsprom.features import KmerFrequencyEncoder, FeatureSetBuilder


def _write_dataset(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sequence", "label"])
        writer.writeheader()
        for index in range(10):
            writer.writerow({"sequence": ("ACGT" if index % 2 else "TGCA") * 2, "label": index % 2})


def _write_config(path: Path, train: Path, test: Path) -> None:
    path.write_text(
        f"""project:\n  name: test-run\ntracking:\n  tracking_uri: ./mlruns\n  experiment_name: tests\ndata:\n  train_csv: {train}\n  test_csv: {test}\n  sequence_length: 8\n  alphabet: [A, C, G, T]\n  max_train_samples: 6\n  max_test_samples: 4\n  random_seed: 7\nfeatures:\n  combination_mode: concatenate\n  blocks:\n    - name: kmer2\n      encoding: kmer_frequency\n      k: 2\nmodel:\n  name: logistic_regression\n  hyperparameters: {{}}\nevaluation:\n  metrics: [accuracy, f1, roc_auc]\noutputs:\n  artifact_dir: outputs/runs\n""",
        encoding="utf-8",
    )


def test_load_config_and_stratified_dataset(tmp_path):
    train = tmp_path / "train.csv"
    test = tmp_path / "test.csv"
    config_path = tmp_path / "experiment.yaml"
    _write_dataset(train)
    _write_dataset(test)
    _write_config(config_path, train, test)

    config = load_experiment_config(config_path)
    split = read_dataset(train, config.data, config.data.max_train_samples)

    assert config.model.name == "logistic_regression"
    assert len(split.labels) == 6
    assert split.labels.count(0) == split.labels.count(1) == 3
    assert len(split.row_ids) == len(set(split.row_ids)) == 6
    assert all(row_id.startswith("row-") for row_id in split.row_ids)


def test_config_rejects_unknown_root_key(tmp_path):
    train = tmp_path / "train.csv"
    test = tmp_path / "test.csv"
    config_path = tmp_path / "experiment.yaml"
    _write_dataset(train)
    _write_dataset(test)
    _write_config(config_path, train, test)
    config_path.write_text(config_path.read_text(encoding="utf-8") + "unknown: true\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unknown top-level"):
        load_experiment_config(config_path)


def test_config_accepts_xgboost_model(tmp_path):
    train = tmp_path / "train.csv"
    test = tmp_path / "test.csv"
    config_path = tmp_path / "experiment.yaml"
    _write_dataset(train)
    _write_dataset(test)
    _write_config(config_path, train, test)
    text = config_path.read_text(encoding="utf-8").replace("name: logistic_regression", "name: xgboost")
    config_path.write_text(text, encoding="utf-8")

    assert load_experiment_config(config_path).model.name == "xgboost"


def test_config_accepts_disabled_model_logging(tmp_path):
    train = tmp_path / "train.csv"
    test = tmp_path / "test.csv"
    config_path = tmp_path / "experiment.yaml"
    _write_dataset(train)
    _write_dataset(test)
    _write_config(config_path, train, test)
    text = config_path.read_text(encoding="utf-8").replace(
        "outputs:\n  artifact_dir: outputs/runs",
        "outputs:\n  artifact_dir: outputs/runs\n  log_model: false",
    )
    config_path.write_text(text, encoding="utf-8")

    assert load_experiment_config(config_path).outputs.log_model is False


def test_metric_calculation():
    metrics = calculate_metrics(
        [
            "accuracy",
            "average_precision",
            "balanced_accuracy",
            "brier_score",
            "expected_calibration_error",
            "precision",
            "recall",
            "specificity",
            "f1",
            "log_loss",
            "roc_auc",
            "matthews_corrcoef",
        ],
        [0, 0, 1, 1],
        [0, 1, 1, 1],
        [0.1, 0.6, 0.7, 0.9],
    )

    assert metrics["accuracy"] == 0.75
    assert metrics["recall"] == 1.0
    assert metrics["specificity"] == 0.5
    assert metrics["roc_auc"] == 1.0
    assert 0.0 <= metrics["expected_calibration_error"] <= 1.0


def test_batched_encoding_uses_compact_consistent_matrix():
    feature_set = FeatureSetBuilder([KmerFrequencyEncoder(k=2)])
    matrix = encode_sequences_batched(["ACGT", "TGCA", "AAAA"], feature_set, batch_size=2)

    assert matrix.shape == (3, 16)
    assert str(matrix.dtype) == "float32"
    assert matrix[0].sum() == pytest.approx(1.0)


def test_expected_calibration_error_is_zero_for_perfect_probabilities():
    assert expected_calibration_error([0, 0, 1, 1], [0.0, 0.0, 1.0, 1.0], bins=2) == 0.0


def test_prediction_and_fold_artifacts_are_stable(tmp_path):
    row_ids = [f"row-{index:09d}" for index in range(10)]
    labels = [index % 2 for index in range(10)]
    predictions_path = tmp_path / "predictions.csv"
    folds_path = tmp_path / "folds.csv"

    write_predictions(predictions_path, row_ids, labels, [0.1, 0.9] * 5, labels)
    write_fold_manifest(folds_path, row_ids, labels)

    prediction_rows = list(csv.DictReader(predictions_path.open(encoding="utf-8")))
    fold_rows = list(csv.DictReader(folds_path.open(encoding="utf-8")))
    assert [row["row_id"] for row in prediction_rows] == row_ids
    assert sorted({int(row["fold"]) for row in fold_rows}) == [0, 1, 2, 3, 4]
    assert all("sequence" not in row for row in prediction_rows)


def test_data_audit_detects_duplicates_and_partition_overlap(tmp_path):
    train = tmp_path / "train.csv"
    test = tmp_path / "test.csv"
    config_path = tmp_path / "experiment.yaml"
    _write_dataset(train)
    _write_dataset(test)
    _write_config(config_path, train, test)

    report = audit_dataset_pair(load_experiment_config(config_path).data)

    assert report["train_duplicate_rows"] == 8
    assert report["test_duplicate_rows"] == 8
    assert report["train_test_overlap_unique_sequences"] == 2
    assert report["train_test_conflicting_label_sequences"] == 0
