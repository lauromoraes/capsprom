#!/usr/bin/env python3
"""Validate runner-v7 continuous-versus-resumed equivalence on an accelerator."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import torch

import capsprom.neural_training as neural_training
from capsprom.models.capsprom import CapsPromConfig
from capsprom.neural_training import (
    NeuralTrainingConfig,
    predict_capsprom_checkpoint,
    run_training_only,
)
from capsprom.state import write_json_atomic


class PlannedInterruption(RuntimeError):
    """Controlled interruption after a durable epoch checkpoint and state."""


def validate_equivalence(output_dir: Path, device: str = "cuda") -> dict[str, Any]:
    """Run one continuous and one interrupted/resumed synthetic fixture."""

    if device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA equivalence was requested but CUDA is unavailable")
    output_dir = output_dir.resolve()
    continuous_dir = output_dir / "continuous"
    resumed_dir = output_dir / "resumed"
    sequences, labels = _fixture(rows=64, sequence_length=81, seed=20261020)
    continuous_config = _config(continuous_dir, device)
    resumed_config = _config(resumed_dir, device)

    run_training_only(sequences, labels, continuous_config)
    _run_with_one_planned_interruption(sequences, labels, resumed_config, epoch=1)
    run_training_only(sequences, labels, resumed_config)

    continuous_state = json.loads(continuous_config.state_path.read_text(encoding="utf-8"))
    resumed_state = json.loads(resumed_config.state_path.read_text(encoding="utf-8"))
    history_max_abs = _history_max_abs(
        continuous_state["history"], resumed_state["history"]
    )
    parameter_max_abs = _checkpoint_max_abs(
        _latest_path(continuous_config.checkpoint_path),
        _latest_path(resumed_config.checkpoint_path),
    )
    continuous_prediction = predict_capsprom_checkpoint(sequences, continuous_config)
    resumed_prediction = predict_capsprom_checkpoint(sequences, resumed_config)
    score_max_abs = float(
        np.max(
            np.abs(
                continuous_prediction.capsule_lengths
                - resumed_prediction.capsule_lengths
            )
        )
    )
    positive_score_max_abs = float(
        np.max(
            np.abs(
                continuous_prediction.positive_scores
                - resumed_prediction.positive_scores
            )
        )
    )
    predictions_equal = bool(
        np.array_equal(
            continuous_prediction.predictions, resumed_prediction.predictions
        )
    )
    numeric_tolerance = 1e-7 if device == "cuda" else 1e-6
    tolerances = {
        "history_metric_absolute": numeric_tolerance,
        "model_parameter_absolute": numeric_tolerance,
        "capsule_score_absolute": numeric_tolerance,
        "predictions": "exact",
        "selected_epoch": "exact",
    }
    passed = (
        history_max_abs <= tolerances["history_metric_absolute"]
        and parameter_max_abs <= tolerances["model_parameter_absolute"]
        and score_max_abs <= tolerances["capsule_score_absolute"]
        and positive_score_max_abs <= tolerances["capsule_score_absolute"]
        and predictions_equal
        and continuous_state["best_epoch"] == resumed_state["best_epoch"]
        and continuous_state["epochs_completed"] == resumed_state["epochs_completed"] == 3
    )
    report = {
        "schema_version": 1,
        "purpose": "runner_v7_continuous_vs_resumed_fixture_equivalence",
        "scope": "synthetic training-only basic CapsProm; no canonical jobs",
        "hardware": {
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "device": device,
            "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
        },
        "fixture": {
            "rows": len(labels),
            "sequence_length": 81,
            "representation": "one_hot_k1_float32",
            "seed": 20261020,
            "epochs": 3,
            "interruption_after_epoch": 1,
        },
        "tolerances": tolerances,
        "observed": {
            "history_metric_max_absolute_difference": history_max_abs,
            "model_parameter_max_absolute_difference": parameter_max_abs,
            "capsule_length_max_absolute_difference": score_max_abs,
            "positive_score_max_absolute_difference": positive_score_max_abs,
            "predictions_exactly_equal": predictions_equal,
            "continuous_best_epoch": continuous_state["best_epoch"],
            "resumed_best_epoch": resumed_state["best_epoch"],
            "continuous_epochs_completed": continuous_state["epochs_completed"],
            "resumed_epochs_completed": resumed_state["epochs_completed"],
        },
        "passed": passed,
        "limitations": [
            "same-host equivalence does not establish cross-version CPU/GPU equality",
            "synthetic data cannot establish predictive or biological validity",
            "the fixture covers one GPU model and one deterministic architecture contract",
        ],
        "canonical_jobs_started": 0,
        "embedding_jobs_started": 0,
    }
    write_json_atomic(output_dir / "equivalence_report.json", report)
    return report


def _run_with_one_planned_interruption(
    sequences: list[str], labels: list[int], config: NeuralTrainingConfig, *, epoch: int
) -> None:
    original = neural_training.write_json_atomic
    interrupted = False

    def interrupt_after_write(path: Path, payload: dict[str, object]) -> None:
        nonlocal interrupted
        original(path, payload)
        if not interrupted and int(payload.get("epochs_completed", -1)) == epoch:
            interrupted = True
            raise PlannedInterruption(f"planned interruption after epoch {epoch}")

    neural_training.write_json_atomic = interrupt_after_write
    try:
        try:
            run_training_only(sequences, labels, config)
        except PlannedInterruption:
            pass
        else:
            raise AssertionError("planned interruption did not occur")
    finally:
        neural_training.write_json_atomic = original


def _fixture(rows: int, sequence_length: int, seed: int) -> tuple[list[str], list[int]]:
    rng = random.Random(seed)
    sequences = ["".join(rng.choices("ACGT", k=sequence_length)) for _ in range(rows)]
    labels = [index % 2 for index in range(rows)]
    return sequences, labels


def _config(output_dir: Path, device: str) -> NeuralTrainingConfig:
    return NeuralTrainingConfig(
        model_name="capsprom_basic",
        random_seed=42,
        validation_fraction=0.25,
        batch_size=16,
        learning_rate=0.0001,
        maximum_epochs=3,
        patience=3,
        checkpoint_path=output_dir / "best.pt",
        state_path=output_dir / "state.json",
        capsule=CapsPromConfig(
            sequence_length=81,
            convolution_filters=16,
            convolution_kernel=9,
            primary_channels=4,
            primary_dim=4,
            primary_kernel=9,
            primary_stride=2,
            output_capsules=2,
            output_dim=8,
            routing_iterations=2,
            routing_gradient_mode="final_iteration",
            decoder_mode="disabled",
        ),
        reconstruction_weight=0.0,
        reconstruction_reduction="mean",
        contract_version=7,
        learning_rate_schedule="fixed",
        device=device,
    )


def _history_max_abs(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> float:
    if len(left) != len(right):
        return float("inf")
    maximum = 0.0
    for left_row, right_row in zip(left, right, strict=True):
        if set(left_row) != set(right_row):
            return float("inf")
        for key in left_row:
            if key == "epoch":
                if left_row[key] != right_row[key]:
                    return float("inf")
            else:
                maximum = max(maximum, abs(float(left_row[key]) - float(right_row[key])))
    return maximum


def _checkpoint_max_abs(left_path: Path, right_path: Path) -> float:
    left = torch.load(left_path, map_location="cpu", weights_only=False)["model_state"]
    right = torch.load(right_path, map_location="cpu", weights_only=False)["model_state"]
    if set(left) != set(right):
        return float("inf")
    return max(float(torch.max(torch.abs(left[key] - right[key]))) for key in left)


def _latest_path(best_path: Path) -> Path:
    return best_path.with_name(f"{best_path.stem}.latest{best_path.suffix}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    report = validate_equivalence(args.output_dir, args.device)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
