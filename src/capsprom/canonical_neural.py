"""Prepare the training-only execution plan for canonical CapsProm evaluation."""

from __future__ import annotations

import csv
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import statistics
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Mapping

import yaml

from .config import DataConfig
from .data.loading import read_dataset, sha256_file
from .evaluation import calculate_metrics, confusion_counts
from .explainability import (
    log_explainability_artifacts,
    select_max_activation_windows,
    write_activation_logo_artifacts,
)
from .models.capsprom import CapsPromConfig
from .neural_training import (
    NeuralTrainingConfig,
    SimulatedFixedEpochInterruption,
    predict_capsprom_checkpoint,
    run_fixed_epoch_training,
    run_training_with_validation,
)
from .runner import write_fold_manifest
from .remote_operations import resolve_failure_event, write_failure_event
from .state import write_json_atomic


def prepare_canonical_neural_plan(config_path: Path, output_dir: Path) -> dict[str, Any]:
    """Write fold manifests and an immutable plan without opening test files."""

    config_path = config_path.resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    required = {
        "protocol",
        "selection",
        "replication",
        "model",
        "training",
        "prediction",
        "tracking",
        "execution_gates",
    }
    if not isinstance(raw, Mapping) or set(raw) != required:
        raise ValueError(f"canonical neural keys must be exactly {sorted(required)}")
    protocol = _mapping(raw, "protocol")
    selection = _mapping(raw, "selection")
    replication = _mapping(raw, "replication")
    gates = _mapping(raw, "execution_gates")
    if gates.get("external_test_enabled") is not False:
        raise ValueError("canonical plan preparation requires external_test_enabled=false")
    dataset_ids = protocol.get("dataset_ids")
    seeds = replication.get("seeds")
    if not isinstance(dataset_ids, list) or not dataset_ids or len(set(dataset_ids)) != len(dataset_ids):
        raise ValueError("protocol.dataset_ids must be a non-empty unique list")
    if not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("replication.seeds must be a non-empty unique list")
    folds = int(selection.get("folds", 0))
    fold_seed = int(selection.get("fold_seed", -1))
    if folds < 2 or fold_seed < 0:
        raise ValueError("selection requires folds >= 2 and a non-negative fold_seed")

    root = config_path.parent.parent
    dataset_root = root / str(protocol.get("dataset_root"))
    output_dir = output_dir.resolve()
    state_path = output_dir / "plan_state.json"
    protocol_sha256 = sha256_file(config_path)
    if state_path.exists():
        existing = json.loads(state_path.read_text(encoding="utf-8"))
        if existing.get("protocol_sha256") != protocol_sha256:
            raise ValueError("canonical protocol changed after plan creation; use a new output path")
        return existing

    datasets: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    for dataset_id in dataset_ids:
        if not isinstance(dataset_id, str) or not dataset_id:
            raise ValueError("every canonical dataset id must be a non-empty string")
        matches = sorted(dataset_root.glob(f"{dataset_id}-p-*-n-*-train.csv"))
        if len(matches) != 1:
            raise ValueError(f"{dataset_id} must resolve to exactly one training file")
        train_path = matches[0]
        data_config = DataConfig(
            train_csv=train_path,
            test_csv=train_path,
            sequence_column="sequence",
            label_column="label",
            sequence_length=81,
            alphabet=("A", "C", "G", "T"),
            max_train_samples=None,
            max_test_samples=None,
            random_seed=fold_seed,
        )
        split = read_dataset(train_path, data_config, max_samples=None)
        manifest_path = output_dir / "fold_manifests" / f"{dataset_id}.csv"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        write_fold_manifest(manifest_path, split.row_ids, split.labels, folds=folds, seed=fold_seed)
        datasets.append(
            {
                "dataset_id": dataset_id,
                "train_path": train_path.relative_to(root).as_posix(),
                "train_sha256": sha256_file(train_path),
                "train_rows": len(split.labels),
                "fold_manifest": manifest_path.relative_to(output_dir).as_posix(),
                "fold_manifest_sha256": sha256_file(manifest_path),
            }
        )
        for seed in seeds:
            for fold in range(folds):
                jobs.append(
                    {
                        "dataset_id": dataset_id,
                        "seed": int(seed),
                        "stage": "inner_fold",
                        "fold": fold,
                        "status": "pending",
                    }
                )
            jobs.append(
                {
                    "dataset_id": dataset_id,
                    "seed": int(seed),
                    "stage": "final_fit",
                    "status": "blocked_pending_epoch_selection",
                }
            )

    state = {
        "protocol_path": config_path.relative_to(root).as_posix(),
        "protocol_sha256": protocol_sha256,
        "phase": "prepared_training_only",
        "external_test_accessed": False,
        "dataset_count": len(datasets),
        "seed_count": len(seeds),
        "fold_count": folds,
        "total_jobs": len(jobs),
        "completed_jobs": 0,
        "datasets": datasets,
        "jobs": jobs,
    }
    write_json_atomic(state_path, state)
    return state


def _mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be a mapping")
    return value


class SimulatedCanonicalInterruption(RuntimeError):
    """Test-only interruption after durable training and before MLflow completion."""


class SimulatedFinalFitInterruption(RuntimeError):
    """Test-only interruption after durable row artifacts and before MLflow completion."""


class SimulatedFinalTrainingInterruption(RuntimeError):
    """Test-only interruption after final training and before MLflow completion."""


def run_canonical_inner_fold_job(
    config_path: Path,
    output_dir: Path,
    dataset_id: str,
    seed: int,
    fold: int,
    *,
    interrupt_after_training: bool = False,
    fail_after_training: bool = False,
) -> dict[str, Any]:
    """Execute or resume one manifest-defined fold and reconcile MLflow/state."""

    output_dir = output_dir.resolve()
    lock_path = output_dir / ".locks" / f"{_job_key(dataset_id, seed, fold)}.lock"
    with _exclusive_file_lock(lock_path, blocking=False):
        return _run_canonical_inner_fold_job_locked(
            config_path,
            output_dir,
            dataset_id,
            seed,
            fold,
            interrupt_after_training=interrupt_after_training,
            fail_after_training=fail_after_training,
        )


def run_canonical_inner_fold_jobs(
    config_path: Path,
    output_dir: Path,
    jobs: list[tuple[str, int, int]],
    *,
    maximum_workers: int,
) -> list[dict[str, Any]]:
    """Dispatch an explicit bounded batch of canonical inner-fold jobs."""

    if not jobs:
        raise ValueError("at least one canonical fold job is required")
    if not 1 <= maximum_workers <= 8:
        raise ValueError("maximum_workers must be between 1 and 8")
    if len(set(jobs)) != len(jobs):
        raise ValueError("a dispatch batch cannot contain duplicate fold identities")

    def execute(identity: tuple[str, int, int]) -> dict[str, Any]:
        dataset_id, seed, fold = identity
        return run_canonical_inner_fold_job(
            config_path, output_dir, dataset_id, seed, fold
        )

    with ThreadPoolExecutor(max_workers=maximum_workers) as executor:
        return list(executor.map(execute, jobs))


def refresh_canonical_final_fit_readiness(
    config_path: Path, output_dir: Path
) -> dict[str, Any]:
    """Materialize fold-derived epochs without training or opening evaluation data."""

    config_path = config_path.resolve()
    output_dir = output_dir.resolve()
    plan_path = output_dir / "plan_state.json"
    if not plan_path.is_file():
        raise ValueError("canonical plan is missing; prepare it before refreshing readiness")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    selection = _mapping(raw, "selection")
    if selection.get("method") != "five_fold_then_full_refit":
        raise ValueError("unsupported canonical selection method")
    if selection.get("epoch_rule") != "lower_median_fold_best_epoch":
        raise ValueError("unsupported canonical epoch-selection rule")

    with _exclusive_file_lock(plan_path.with_suffix(".lock")):
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if plan.get("protocol_sha256") != sha256_file(config_path):
            raise ValueError("canonical plan and protocol hashes differ")
        if plan.get("external_test_accessed") is not False:
            raise ValueError("readiness refresh requires external_test_accessed=false")
        newly_ready = []
        for final_job in (
            job for job in plan["jobs"] if job["stage"] == "final_fit"
        ):
            if final_job["status"] != "blocked_pending_epoch_selection":
                continue
            folds = sorted(
                (
                    job
                    for job in plan["jobs"]
                    if job["stage"] == "inner_fold"
                    and job["dataset_id"] == final_job["dataset_id"]
                    and job["seed"] == final_job["seed"]
                ),
                key=lambda job: job["fold"],
            )
            if len(folds) != int(plan["fold_count"]) or any(
                fold["status"] != "completed" for fold in folds
            ):
                continue
            best_epochs = [int(fold["best_epoch"]) for fold in folds]
            final_job.update(
                {
                    "status": "ready_for_final_fit",
                    "selected_epoch": int(statistics.median_low(best_epochs)),
                    "fold_best_epochs": best_epochs,
                    "selection_rule": "lower_median_fold_best_epoch",
                }
            )
            newly_ready.append(
                {
                    "dataset_id": final_job["dataset_id"],
                    "seed": final_job["seed"],
                    "selected_epoch": final_job["selected_epoch"],
                }
            )
        write_json_atomic(plan_path, plan)
        return {
            "newly_ready": newly_ready,
            "newly_ready_count": len(newly_ready),
            "ready_total": sum(
                job["stage"] == "final_fit"
                and job["status"] == "ready_for_final_fit"
                for job in plan["jobs"]
            ),
            "external_test_accessed": plan["external_test_accessed"],
        }


def _run_canonical_inner_fold_job_locked(
    config_path: Path,
    output_dir: Path,
    dataset_id: str,
    seed: int,
    fold: int,
    *,
    interrupt_after_training: bool,
    fail_after_training: bool,
) -> dict[str, Any]:
    """Run one job while its process-scoped filesystem lock is held."""

    import mlflow
    from mlflow import MlflowClient

    config_path = config_path.resolve()
    plan_path = output_dir / "plan_state.json"
    if not plan_path.is_file():
        raise ValueError("canonical plan is missing; prepare it before running a fold")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("protocol_sha256") != sha256_file(config_path):
        raise ValueError("canonical plan and protocol hashes differ")
    gates = _mapping(raw, "execution_gates")
    if gates.get("canonical_jobs_enabled") is False:
        raise ValueError("canonical fold execution is blocked by the versioned contract")
    key = _job_key(dataset_id, seed, fold)
    job = _find_job(plan, dataset_id, seed, fold)
    if job["status"] == "completed":
        return dict(job)

    tracking = _mapping(raw, "tracking")
    tracking_uri = str(tracking.get("tracking_uri", "sqlite:///mlflow.db"))
    experiment_name = str(tracking.get("experiment_name", "capsprom-basic-canonical-v1"))
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    experiment_id = _get_or_create_experiment(
        client, experiment_name, tracking.get("artifact_location")
    )
    with _exclusive_file_lock(output_dir / ".locks" / "mlflow-identity.lock"):
        parent_run_id = _get_or_create_mlflow_run(
            client,
            experiment_id,
            run_name=f"{experiment_name}-parent",
            identity_tag="capsprom.protocol_sha256",
            identity_value=plan["protocol_sha256"],
            extra_tags={"capsprom.run_role": "parent"},
        )
        child_run_id = _get_or_create_mlflow_run(
            client,
            experiment_id,
            run_name=key,
            identity_tag="capsprom.job_key",
            identity_value=key,
            extra_tags={
                "capsprom.run_role": "inner_fold",
                "mlflow.parentRunId": parent_run_id,
            },
        )
    job = _update_plan_job(
        plan_path,
        dataset_id,
        seed,
        fold,
        {
            "status": "running",
            "run_id": child_run_id,
            "attempts": int(job.get("attempts", 0)) + 1,
        },
        parent_run_id=parent_run_id,
    )

    dataset = next(
        (item for item in plan["datasets"] if item["dataset_id"] == dataset_id), None
    )
    if dataset is None:
        raise ValueError(f"unknown canonical dataset id {dataset_id}")
    root = config_path.parent.parent
    train_path = root / dataset["train_path"]
    manifest_path = output_dir / dataset["fold_manifest"]
    if sha256_file(train_path) != dataset["train_sha256"]:
        raise ValueError("canonical training dataset hash changed")
    if sha256_file(manifest_path) != dataset["fold_manifest_sha256"]:
        raise ValueError("canonical fold manifest hash changed")
    data_config = DataConfig(
        train_csv=train_path,
        test_csv=train_path,
        sequence_column="sequence",
        label_column="label",
        sequence_length=81,
        alphabet=("A", "C", "G", "T"),
        max_train_samples=None,
        max_test_samples=None,
        random_seed=42,
    )
    split = read_dataset(train_path, data_config, max_samples=None)
    assignments = _read_fold_assignments(manifest_path)
    validation_mask = [assignments[row_id] == fold for row_id in split.row_ids]
    if not any(validation_mask) or all(validation_mask):
        raise ValueError("canonical fold must define non-empty train and validation partitions")
    train_sequences = [x for x, held_out in zip(split.sequences, validation_mask) if not held_out]
    train_labels = [y for y, held_out in zip(split.labels, validation_mask) if not held_out]
    validation_sequences = [x for x, held_out in zip(split.sequences, validation_mask) if held_out]
    validation_labels = [y for y, held_out in zip(split.labels, validation_mask) if held_out]
    job_dir = output_dir / "jobs" / dataset_id / f"seed-{seed}" / f"fold-{fold}"
    training_config = _canonical_training_config(raw, seed, job_dir)
    try:
        result = run_training_with_validation(
            train_sequences,
            train_labels,
            validation_sequences,
            validation_labels,
            training_config,
            dataset["fold_manifest_sha256"],
            fold,
        )
        if interrupt_after_training:
            raise SimulatedCanonicalInterruption(key)
        if fail_after_training:
            raise RuntimeError(f"simulated retryable failure for {key}")
        for name, value in {
            "dataset_id": dataset_id,
            "seed": seed,
            "fold": fold,
            "protocol_sha256": plan["protocol_sha256"],
            "train_sha256": dataset["train_sha256"],
            "fold_manifest_sha256": dataset["fold_manifest_sha256"],
        }.items():
            client.log_param(child_run_id, name, value)
        client.log_metric(child_run_id, "best_inner_validation_mcc", result.best_validation_mcc)
        client.log_metric(child_run_id, "best_epoch", float(result.best_epoch))
        client.log_artifact(child_run_id, str(training_config.state_path), "provenance")
        client.log_artifact(child_run_id, str(manifest_path), "provenance")
        client.set_terminated(child_run_id, status="FINISHED")
        job = _update_plan_job(
            plan_path,
            dataset_id,
            seed,
            fold,
            {
                "status": "completed",
                "best_epoch": result.best_epoch,
                "best_validation_mcc": result.best_validation_mcc,
                "epochs_completed": result.epochs_completed,
                "error": None,
            },
        )
        resolve_failure_event(
            output_dir / "notifications", job_key=key
        )
        return dict(job)
    except SimulatedCanonicalInterruption:
        raise
    except Exception as exc:
        job = _update_plan_job(
            plan_path,
            dataset_id,
            seed,
            fold,
            {"status": "failed", "error": f"{type(exc).__name__}: {exc}"},
        )
        client.set_tag(child_run_id, "capsprom.failure", job["error"])
        client.set_terminated(child_run_id, status="FAILED")
        write_failure_event(
            output_dir / "notifications",
            job_key=key,
            error=job["error"],
            attempt=int(job.get("attempts", 1)),
            run_id=child_run_id,
        )
        raise


def _canonical_training_config(
    raw: Mapping[str, Any], seed: int, job_dir: Path
) -> NeuralTrainingConfig:
    model = _mapping(raw, "model")
    architecture = _mapping(model, "architecture")
    training = _mapping(raw, "training")
    input_config = _mapping(model, "input")
    capsule = CapsPromConfig(
        sequence_length=int(input_config.get("sequence_length", 81)),
        input_channels=int(input_config.get("channels", 4)),
        convolution_filters=int(architecture.get("convolution_filters", 256)),
        convolution_kernel=int(architecture.get("convolution_kernel", 9)),
        primary_channels=int(architecture.get("primary_channels", 32)),
        primary_dim=int(architecture.get("primary_dim", 8)),
        primary_kernel=int(architecture.get("primary_kernel", 9)),
        primary_stride=int(architecture.get("primary_stride", 2)),
        output_capsules=int(architecture.get("output_capsules", 2)),
        output_dim=int(architecture.get("output_dim", 16)),
        routing_iterations=int(architecture.get("routing_iterations", 3)),
        routing_mode=str(architecture.get("routing_mode", "dynamic")),
        routing_gradient_mode=str(architecture.get("routing_gradient_mode", "final_iteration")),
        decoder_mode=str(architecture.get("decoder_mode", "disabled")),
    )
    return NeuralTrainingConfig(
        model_name="capsprom_basic",
        random_seed=seed,
        validation_fraction=0.2,
        batch_size=int(training.get("batch_size", 64)),
        learning_rate=float(training.get("learning_rate", 0.0001)),
        maximum_epochs=int(training.get("maximum_epochs", 30)),
        patience=int(training.get("patience", 15)),
        checkpoint_path=job_dir / "best.pt",
        state_path=job_dir / "state.json",
        capsule=capsule,
        reconstruction_weight=float(training.get("reconstruction_weight", 0.0)),
        reconstruction_reduction="mean",
        contract_version=int(training.get("runner_contract_version", 6)),
        learning_rate_schedule=str(training.get("learning_rate_schedule", "fixed")),
        device=str(training.get("device", "cpu")),
    )


def run_canonical_final_fit_job(
    config_path: Path,
    output_dir: Path,
    dataset_id: str,
    seed: int,
    *,
    fixture_only: bool = False,
    release_path: Path | None = None,
    interrupt_after_epoch: int | None = None,
    interrupt_after_training: bool = False,
) -> dict[str, Any]:
    """Train one ready final-fit job without accepting evaluation data."""

    import mlflow
    from mlflow import MlflowClient

    config_path = config_path.resolve()
    output_dir = output_dir.resolve()
    plan_path = output_dir / "plan_state.json"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("protocol_sha256") != sha256_file(config_path):
        raise ValueError("canonical plan and protocol hashes differ")
    gates = _mapping(raw, "execution_gates")
    release_sha256 = None
    if release_path is not None:
        release_sha256 = _check_final_fit_release(
            release_path, plan["protocol_sha256"], dataset_id, seed
        )
    elif not fixture_only and gates.get("final_fits_enabled") is not True:
        raise ValueError("canonical final-fit execution is blocked by the versioned contract")
    job = _find_final_job(plan, dataset_id, seed)
    if job["status"] == "completed_final_fit_training":
        return dict(job)
    if job["status"] != "ready_for_final_fit":
        raise ValueError("final-fit job must be ready_for_final_fit before training")
    selected_epoch = int(job.get("selected_epoch", 0))
    fold_best_epochs = job.get("fold_best_epochs")
    if (
        job.get("selection_rule") != "lower_median_fold_best_epoch"
        or not isinstance(fold_best_epochs, list)
        or selected_epoch != statistics.median_low(fold_best_epochs)
    ):
        raise ValueError("final-fit job has invalid or ambiguous epoch-selection provenance")

    dataset = next(
        (item for item in plan["datasets"] if item["dataset_id"] == dataset_id), None
    )
    if dataset is None:
        raise ValueError(f"unknown canonical dataset id {dataset_id}")
    root = config_path.parent.parent
    train_path = root / dataset["train_path"]
    if sha256_file(train_path) != dataset["train_sha256"]:
        raise ValueError("canonical training dataset hash changed")
    data_config = DataConfig(
        train_csv=train_path,
        test_csv=train_path,
        sequence_column="sequence",
        label_column="label",
        sequence_length=81,
        alphabet=("A", "C", "G", "T"),
        max_train_samples=None,
        max_test_samples=None,
        random_seed=42,
    )
    training = read_dataset(train_path, data_config, max_samples=None)
    job_dir = output_dir / "jobs" / dataset_id / f"seed-{seed}" / "final-fit"
    training_config = _canonical_training_config(raw, seed, job_dir)

    tracking = _mapping(raw, "tracking")
    tracking_uri = str(tracking.get("tracking_uri", "sqlite:///mlflow.db"))
    experiment_name = str(tracking.get("experiment_name", "capsprom-basic-canonical-v1"))
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    experiment_id = _get_or_create_experiment(
        client, experiment_name, tracking.get("artifact_location")
    )
    with _exclusive_file_lock(output_dir / ".locks" / "mlflow-identity.lock"):
        parent_run_id = _get_or_create_mlflow_run(
            client,
            experiment_id,
            run_name=f"{experiment_name}-parent",
            identity_tag="capsprom.protocol_sha256",
            identity_value=plan["protocol_sha256"],
            extra_tags={"capsprom.run_role": "parent"},
        )
        run_id = _get_or_create_mlflow_run(
            client,
            experiment_id,
            run_name=_final_job_key(dataset_id, seed),
            identity_tag="capsprom.job_key",
            identity_value=_final_job_key(dataset_id, seed),
            extra_tags={
                "capsprom.run_role": "final_fit_training",
                "mlflow.parentRunId": parent_run_id,
            },
        )
    _update_final_job(
        plan_path,
        dataset_id,
        seed,
        {"run_id": run_id, "attempts": int(job.get("attempts", 0)) + 1},
        parent_run_id=parent_run_id,
    )
    try:
        checkpoint = run_fixed_epoch_training(
            training.sequences,
            training.labels,
            training_config,
            epochs=selected_epoch,
            selection_provenance={
                "rule": "lower_median_fold_best_epoch",
                "fold_best_epochs": fold_best_epochs,
                "fold_manifest_sha256": dataset["fold_manifest_sha256"],
            },
            interrupt_after_epoch=interrupt_after_epoch,
        )
        checkpoint_sha256 = sha256_file(checkpoint)
        state_sha256 = sha256_file(training_config.state_path)
        _update_final_job(
            plan_path,
            dataset_id,
            seed,
            {
                "checkpoint_sha256": checkpoint_sha256,
                "training_state_sha256": state_sha256,
                "training_rows": len(training.labels),
                "error": None,
            },
        )
        if interrupt_after_training:
            raise SimulatedFinalTrainingInterruption(_final_job_key(dataset_id, seed))
        for name, value in {
            "dataset_id": dataset_id,
            "seed": seed,
            "selected_epoch": selected_epoch,
            "protocol_sha256": plan["protocol_sha256"],
            "train_sha256": dataset["train_sha256"],
            "checkpoint_sha256": checkpoint_sha256,
            **({"release_sha256": release_sha256} if release_sha256 else {}),
        }.items():
            client.log_param(run_id, name, value)
        client.log_artifact(run_id, str(training_config.state_path), "provenance")
        client.set_terminated(run_id, status="FINISHED")
        return _update_final_job(
            plan_path,
            dataset_id,
            seed,
            {
                "status": "completed_final_fit_training",
                "error": None,
                **({"release_sha256": release_sha256} if release_sha256 else {}),
            },
            parent_run_id=parent_run_id,
        )
    except (SimulatedFixedEpochInterruption, SimulatedFinalTrainingInterruption):
        raise
    except Exception as exc:
        _update_final_job(
            plan_path,
            dataset_id,
            seed,
            {"error": f"{type(exc).__name__}: {exc}"},
        )
        raise


def run_canonical_external_inference_job(
    config_path: Path,
    output_dir: Path,
    dataset_id: str,
    seed: int,
    evaluation_csv: Path,
) -> dict[str, Any]:
    """Evaluate one persisted final checkpoint behind the external-test gate."""

    import mlflow
    from mlflow import MlflowClient

    config_path = config_path.resolve()
    output_dir = output_dir.resolve()
    plan_path = output_dir / "plan_state.json"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if _mapping(raw, "execution_gates").get("external_test_enabled") is not True:
        raise ValueError("canonical external inference is blocked by the versioned contract")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("protocol_sha256") != sha256_file(config_path):
        raise ValueError("canonical plan and protocol hashes differ")
    job = _find_final_job(plan, dataset_id, seed)
    if job["status"] == "completed_external_evaluation":
        return dict(job)
    if job["status"] != "completed_final_fit_training":
        raise ValueError(
            "external inference requires completed_final_fit_training checkpoint state"
        )
    dataset = next(
        (item for item in plan["datasets"] if item["dataset_id"] == dataset_id), None
    )
    if dataset is None:
        raise ValueError(f"unknown canonical dataset id {dataset_id}")
    job_dir = output_dir / "jobs" / dataset_id / f"seed-{seed}" / "final-fit"
    training_config = _canonical_training_config(raw, seed, job_dir)
    if sha256_file(training_config.checkpoint_path) != job.get("checkpoint_sha256"):
        raise ValueError("persisted final checkpoint hash changed")
    if sha256_file(training_config.state_path) != job.get("training_state_sha256"):
        raise ValueError("persisted final training-state hash changed")

    data_config = DataConfig(
        train_csv=evaluation_csv,
        test_csv=evaluation_csv,
        sequence_column="sequence",
        label_column="label",
        sequence_length=81,
        alphabet=("A", "C", "G", "T"),
        max_train_samples=None,
        max_test_samples=None,
        random_seed=42,
    )
    evaluation_sha256 = sha256_file(evaluation_csv)
    evaluation = read_dataset(evaluation_csv, data_config, max_samples=None)
    prediction = predict_capsprom_checkpoint(evaluation.sequences, training_config)
    metrics = calculate_metrics(
        [
            "accuracy",
            "balanced_accuracy",
            "precision",
            "recall",
            "f1",
            "matthews_corrcoef",
            "roc_auc",
            "average_precision",
            "brier_score",
            "expected_calibration_error",
            "log_loss",
            "specificity",
        ],
        evaluation.labels,
        prediction.predictions.tolist(),
        prediction.positive_scores.tolist(),
    )
    metrics.update(confusion_counts(evaluation.labels, prediction.predictions.tolist()))
    artifact_dir = job_dir / "external-evaluation"
    rows_path = artifact_dir / "predictions.csv"
    metrics_path = artifact_dir / "metrics.json"
    _write_prediction_rows_atomic(
        rows_path,
        evaluation.row_ids,
        evaluation.labels,
        prediction.capsule_lengths,
        prediction.positive_scores,
        prediction.predictions,
    )
    write_json_atomic(
        metrics_path,
        {
            "schema_version": 1,
            "partition": "external_test",
            "evaluation_sha256": evaluation_sha256,
            "row_count": len(evaluation.labels),
            "metrics": metrics,
        },
    )

    tracking = _mapping(raw, "tracking")
    tracking_uri = str(tracking.get("tracking_uri", "sqlite:///mlflow.db"))
    experiment_name = str(tracking.get("experiment_name", "capsprom-basic-canonical-v1"))
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    experiment_id = _get_or_create_experiment(
        client, experiment_name, tracking.get("artifact_location")
    )
    run_key = f"{dataset_id}--seed-{seed}--external-evaluation"
    with _exclusive_file_lock(output_dir / ".locks" / "mlflow-identity.lock"):
        run_id = _get_or_create_mlflow_run(
            client,
            experiment_id,
            run_name=run_key,
            identity_tag="capsprom.job_key",
            identity_value=run_key,
            extra_tags={
                "capsprom.run_role": "external_evaluation",
                "mlflow.parentRunId": plan["parent_run_id"],
            },
        )
    for name, value in metrics.items():
        client.log_metric(run_id, name, float(value))
    for name, value in {
        "dataset_id": dataset_id,
        "seed": seed,
        "protocol_sha256": plan["protocol_sha256"],
        "evaluation_sha256": evaluation_sha256,
        "checkpoint_sha256": job["checkpoint_sha256"],
    }.items():
        client.log_param(run_id, name, value)
    client.log_artifact(run_id, str(rows_path), "evaluation")
    client.log_artifact(run_id, str(metrics_path), "evaluation")
    client.set_terminated(run_id, status="FINISHED")
    return _update_external_evaluation(
        plan_path,
        dataset_id,
        seed,
        {
            "status": "completed_external_evaluation",
            "external_evaluation_run_id": run_id,
            "external_evaluation_sha256": evaluation_sha256,
            "external_metrics": metrics,
        },
    )
def run_fixture_final_fit_job(
    config_path: Path,
    output_dir: Path,
    dataset_id: str,
    seed: int,
    evaluation_csv: Path,
    *,
    fixture_only: bool,
    interrupt_after_artifacts: bool = False,
) -> dict[str, Any]:
    """Validate final fit, frozen scoring, and artifacts without canonical test access."""

    if fixture_only is not True:
        raise ValueError("this gate accepts only explicitly declared fixture evaluation data")
    output_dir = output_dir.resolve()
    lock_path = output_dir / ".locks" / f"{_final_job_key(dataset_id, seed)}.lock"
    with _exclusive_file_lock(lock_path, blocking=False):
        return _run_fixture_final_fit_job_locked(
            config_path.resolve(),
            output_dir,
            dataset_id,
            seed,
            evaluation_csv.resolve(),
            interrupt_after_artifacts=interrupt_after_artifacts,
        )


def _run_fixture_final_fit_job_locked(
    config_path: Path,
    output_dir: Path,
    dataset_id: str,
    seed: int,
    evaluation_csv: Path,
    *,
    interrupt_after_artifacts: bool,
) -> dict[str, Any]:
    import mlflow
    from mlflow import MlflowClient

    plan_path = output_dir / "plan_state.json"
    if not plan_path.is_file():
        raise ValueError("canonical plan is missing; prepare it before final fit")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("protocol_sha256") != sha256_file(config_path):
        raise ValueError("canonical plan and protocol hashes differ")
    if _mapping(raw, "execution_gates").get("external_test_enabled") is not False:
        raise ValueError("fixture validation requires the canonical external-test gate closed")
    job = _find_final_job(plan, dataset_id, seed)
    if job["status"] == "completed_fixture_validation":
        return dict(job)

    folds = sorted(
        (
            item
            for item in plan["jobs"]
            if item["dataset_id"] == dataset_id
            and item["seed"] == seed
            and item["stage"] == "inner_fold"
        ),
        key=lambda item: item["fold"],
    )
    if len(folds) != int(plan["fold_count"]) or any(
        item["status"] != "completed" for item in folds
    ):
        raise ValueError("all inner folds must complete before selecting the final-fit epoch")
    best_epochs = [int(item["best_epoch"]) for item in folds]
    selected_epoch = int(statistics.median_low(best_epochs))
    job = _update_final_job(
        plan_path,
        dataset_id,
        seed,
        {
            "status": "running_fixture_validation",
            "selected_epoch": selected_epoch,
            "fold_best_epochs": best_epochs,
            "selection_rule": "lower_median_fold_best_epoch",
            "attempts": int(job.get("attempts", 0)) + 1,
        },
    )

    dataset = next(
        (item for item in plan["datasets"] if item["dataset_id"] == dataset_id), None
    )
    if dataset is None:
        raise ValueError(f"unknown canonical dataset id {dataset_id}")
    root = config_path.parent.parent
    train_path = root / dataset["train_path"]
    if sha256_file(train_path) != dataset["train_sha256"]:
        raise ValueError("canonical training dataset hash changed")
    data_config = DataConfig(
        train_csv=train_path,
        test_csv=evaluation_csv,
        sequence_column="sequence",
        label_column="label",
        sequence_length=81,
        alphabet=("A", "C", "G", "T"),
        max_train_samples=None,
        max_test_samples=None,
        random_seed=42,
    )
    training = read_dataset(train_path, data_config, max_samples=None)
    job_dir = output_dir / "jobs" / dataset_id / f"seed-{seed}" / "final-fit-fixture"
    training_config = _canonical_training_config(raw, seed, job_dir)
    selection_provenance = {
        "rule": "lower_median_fold_best_epoch",
        "fold_best_epochs": best_epochs,
        "fold_manifest_sha256": dataset["fold_manifest_sha256"],
    }
    run_fixed_epoch_training(
        training.sequences,
        training.labels,
        training_config,
        epochs=selected_epoch,
        selection_provenance=selection_provenance,
    )

    # Evaluation input is deliberately opened only after epoch selection and
    # the completed final-training state have both been durably persisted.
    evaluation_sha256 = sha256_file(evaluation_csv)
    evaluation = read_dataset(evaluation_csv, data_config, max_samples=None)
    prediction = predict_capsprom_checkpoint(evaluation.sequences, training_config)
    metrics = calculate_metrics(
        [
            "accuracy",
            "balanced_accuracy",
            "precision",
            "recall",
            "f1",
            "matthews_corrcoef",
            "roc_auc",
            "average_precision",
            "brier_score",
            "expected_calibration_error",
            "log_loss",
            "specificity",
        ],
        evaluation.labels,
        prediction.predictions.tolist(),
        prediction.positive_scores.tolist(),
    )
    metrics.update(confusion_counts(evaluation.labels, prediction.predictions.tolist()))
    artifacts_dir = job_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    rows_path = artifacts_dir / "predictions.csv"
    _write_prediction_rows_atomic(
        rows_path,
        evaluation.row_ids,
        evaluation.labels,
        prediction.capsule_lengths,
        prediction.positive_scores,
        prediction.predictions,
    )
    metrics_path = artifacts_dir / "metrics.json"
    write_json_atomic(
        metrics_path,
        {
            "schema_version": 1,
            "partition": "fixture_evaluation",
            "evaluation_sha256": evaluation_sha256,
            "row_count": len(evaluation.labels),
            "metrics": metrics,
        },
    )
    checkpoint_sha256 = sha256_file(training_config.checkpoint_path)
    train_prediction = predict_capsprom_checkpoint(training.sequences, training_config)
    windows = select_max_activation_windows(
        training.row_ids,
        training.sequences,
        training.labels,
        train_prediction.first_convolution_activations,
        kernel_size=training_config.capsule.convolution_kernel,
        filter_index=0,
        eligible_label=1,
        maximum_windows=min(20, sum(training.labels)),
    )
    explainability_manifest = write_activation_logo_artifacts(
        artifacts_dir / "explainability" / "filter-0",
        windows,
        dataset_id=dataset_id,
        model_name="capsprom_basic",
        config_sha256=plan["protocol_sha256"],
        checkpoint_sha256=checkpoint_sha256,
        seed=seed,
        fold=-1,
        source_partition="full_train",
    )
    artifact_hashes = {
        "predictions.csv": sha256_file(rows_path),
        "metrics.json": sha256_file(metrics_path),
        "explainability_manifest.json": sha256_file(explainability_manifest),
    }
    job = _update_final_job(
        plan_path,
        dataset_id,
        seed,
        {
            "status": "artifacts_persisted_fixture_validation",
            "evaluation_kind": "fixture",
            "evaluation_sha256": evaluation_sha256,
            "checkpoint_sha256": checkpoint_sha256,
            "artifact_hashes": artifact_hashes,
            "metrics": metrics,
            "error": None,
        },
        fixture_evaluation_accessed=True,
    )
    if interrupt_after_artifacts:
        raise SimulatedFinalFitInterruption(_final_job_key(dataset_id, seed))

    tracking = _mapping(raw, "tracking")
    tracking_uri = str(tracking.get("tracking_uri", "sqlite:///mlflow.db"))
    experiment_name = str(tracking.get("experiment_name", "capsprom-basic-canonical-v1"))
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    experiment_id = _get_or_create_experiment(
        client, experiment_name, tracking.get("artifact_location")
    )
    with _exclusive_file_lock(output_dir / ".locks" / "mlflow-identity.lock"):
        parent_run_id = _get_or_create_mlflow_run(
            client,
            experiment_id,
            run_name=f"{experiment_name}-parent",
            identity_tag="capsprom.protocol_sha256",
            identity_value=plan["protocol_sha256"],
            extra_tags={"capsprom.run_role": "parent"},
        )
        run_id = _get_or_create_mlflow_run(
            client,
            experiment_id,
            run_name=_final_job_key(dataset_id, seed),
            identity_tag="capsprom.job_key",
            identity_value=_final_job_key(dataset_id, seed),
            extra_tags={
                "capsprom.run_role": "final_fit_fixture_validation",
                "mlflow.parentRunId": parent_run_id,
            },
        )
    for name, value in {
        "dataset_id": dataset_id,
        "seed": seed,
        "selected_epoch": selected_epoch,
        "protocol_sha256": plan["protocol_sha256"],
        "train_sha256": dataset["train_sha256"],
        "evaluation_sha256": evaluation_sha256,
    }.items():
        client.log_param(run_id, name, value)
    for name, value in metrics.items():
        client.log_metric(run_id, name, float(value))
    client.log_artifact(run_id, str(rows_path), "evaluation")
    client.log_artifact(run_id, str(metrics_path), "evaluation")
    client.log_artifact(run_id, str(training_config.state_path), "provenance")
    log_explainability_artifacts(client, run_id, explainability_manifest)
    client.set_terminated(run_id, status="FINISHED")
    return _update_final_job(
        plan_path,
        dataset_id,
        seed,
        {"status": "completed_fixture_validation", "run_id": run_id},
        parent_run_id=parent_run_id,
        fixture_evaluation_accessed=True,
    )


def _write_prediction_rows_atomic(
    path: Path,
    row_ids: list[str],
    labels: list[int],
    capsule_lengths: Any,
    positive_scores: Any,
    predictions: Any,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["row_id", "label", "capsule_0_length", "capsule_1_length", "positive_score", "prediction"]
            )
            for row_id, label, lengths, score, predicted in zip(
                row_ids, labels, capsule_lengths, positive_scores, predictions, strict=True
            ):
                writer.writerow(
                    [
                        row_id,
                        label,
                        f"{float(lengths[0]):.17g}",
                        f"{float(lengths[1]):.17g}",
                        f"{float(score):.17g}",
                        int(predicted),
                    ]
                )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _get_or_create_mlflow_run(
    client: Any,
    experiment_id: str,
    *,
    run_name: str,
    identity_tag: str,
    identity_value: str,
    extra_tags: Mapping[str, str],
) -> str:
    matches = client.search_runs(
        [experiment_id], filter_string=f"tags.`{identity_tag}` = '{identity_value}'"
    )
    if len(matches) > 1:
        raise ValueError(f"multiple MLflow runs share {identity_tag}={identity_value}")
    if matches:
        return matches[0].info.run_id
    tags = {"mlflow.runName": run_name, identity_tag: identity_value, **extra_tags}
    return client.create_run(experiment_id, tags=tags).info.run_id


def _get_or_create_experiment(
    client: Any, experiment_name: str, artifact_location: object
) -> str:
    expected = None if artifact_location is None else str(artifact_location)
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        return client.create_experiment(
            experiment_name, artifact_location=expected
        )
    if expected is not None and experiment.artifact_location != expected:
        raise ValueError("existing MLflow experiment has a conflicting artifact location")
    return experiment.experiment_id


def _find_job(
    plan: Mapping[str, Any], dataset_id: str, seed: int, fold: int
) -> dict[str, Any]:
    matches = [
        job
        for job in plan["jobs"]
        if job["dataset_id"] == dataset_id
        and job["seed"] == seed
        and job["stage"] == "inner_fold"
        and job["fold"] == fold
    ]
    if len(matches) != 1:
        raise ValueError("canonical inner-fold job identity is missing or ambiguous")
    return matches[0]


def _find_final_job(
    plan: Mapping[str, Any], dataset_id: str, seed: int
) -> dict[str, Any]:
    matches = [
        job
        for job in plan["jobs"]
        if job["dataset_id"] == dataset_id
        and job["seed"] == seed
        and job["stage"] == "final_fit"
    ]
    if len(matches) != 1:
        raise ValueError("canonical final-fit job identity is missing or ambiguous")
    return matches[0]


def _job_key(dataset_id: str, seed: int, fold: int) -> str:
    return f"{dataset_id}--seed-{seed}--fold-{fold}"


def _check_final_fit_release(
    release_path: Path, protocol_sha256: str, dataset_id: str, seed: int
) -> str:
    """Return the release hash if it opens exactly this final fit and nothing else."""

    release = yaml.safe_load(release_path.read_text(encoding="utf-8"))
    scope = _mapping(release, "scope")
    gates = _mapping(release, "execution_gates")
    if scope.get("execution_contract_sha256") != protocol_sha256:
        raise ValueError("final-fit release targets a different execution contract")
    if gates.get("final_fits_enabled") is not True:
        raise ValueError("final-fit release does not open the final-fit gate")
    if any(open_ for name, open_ in gates.items() if name != "final_fits_enabled"):
        raise ValueError("final-fit release opens a gate outside final fits")
    dataset_ids = list(scope.get("dataset_ids", []))
    seeds = [int(item) for item in scope.get("seeds", [])]
    if scope.get("maximum_new_final_fits") != len(dataset_ids) * len(seeds):
        raise ValueError("released final-fit count differs from the bounded maximum")
    if dataset_id not in dataset_ids or seed not in seeds:
        raise ValueError("final fit is outside the release scope")
    return sha256_file(release_path)


def _final_job_key(dataset_id: str, seed: int) -> str:
    return f"{dataset_id}--seed-{seed}--final-fit-training"


def _read_fold_assignments(path: Path) -> dict[str, int]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assignments = {row["row_id"]: int(row["fold"]) for row in rows}
    if len(assignments) != len(rows):
        raise ValueError("fold manifest contains duplicate row identifiers")
    return assignments


def _update_plan_job(
    plan_path: Path,
    dataset_id: str,
    seed: int,
    fold: int,
    updates: Mapping[str, Any],
    *,
    parent_run_id: str | None = None,
) -> dict[str, Any]:
    with _exclusive_file_lock(plan_path.with_suffix(".lock")):
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        job = _find_job(plan, dataset_id, seed, fold)
        job.update(updates)
        if parent_run_id is not None:
            existing_parent = plan.get("parent_run_id")
            if existing_parent not in {None, parent_run_id}:
                raise ValueError("canonical plan has conflicting MLflow parent runs")
            plan["parent_run_id"] = parent_run_id
        plan["completed_jobs"] = sum(item["status"] == "completed" for item in plan["jobs"])
        write_json_atomic(plan_path, plan)
        return dict(job)


def _update_final_job(
    plan_path: Path,
    dataset_id: str,
    seed: int,
    updates: Mapping[str, Any],
    *,
    parent_run_id: str | None = None,
    fixture_evaluation_accessed: bool | None = None,
) -> dict[str, Any]:
    with _exclusive_file_lock(plan_path.with_suffix(".lock")):
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        job = _find_final_job(plan, dataset_id, seed)
        job.update(updates)
        if parent_run_id is not None:
            existing_parent = plan.get("parent_run_id")
            if existing_parent not in {None, parent_run_id}:
                raise ValueError("canonical plan has conflicting MLflow parent runs")
            plan["parent_run_id"] = parent_run_id
        if fixture_evaluation_accessed is not None:
            plan["fixture_evaluation_accessed"] = fixture_evaluation_accessed
        # A fixture validation never changes the canonical external-test flag.
        if plan.get("external_test_accessed") is not False:
            raise ValueError("fixture validation cannot alter canonical external-test state")
        plan["completed_jobs"] = sum(
            item["status"]
            in {
                "completed",
                "completed_final_fit_training",
                "completed_fixture_validation",
            }
            for item in plan["jobs"]
        )
        write_json_atomic(plan_path, plan)
        return dict(job)


def _update_external_evaluation(
    plan_path: Path,
    dataset_id: str,
    seed: int,
    updates: Mapping[str, Any],
) -> dict[str, Any]:
    with _exclusive_file_lock(plan_path.with_suffix(".lock")):
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        job = _find_final_job(plan, dataset_id, seed)
        job.update(updates)
        plan["external_test_accessed"] = True
        plan["completed_jobs"] = sum(
            item["status"]
            in {
                "completed",
                "completed_final_fit_training",
                "completed_fixture_validation",
                "completed_external_evaluation",
            }
            for item in plan["jobs"]
        )
        write_json_atomic(plan_path, plan)
        return dict(job)


@contextmanager
def _exclusive_file_lock(path: Path, *, blocking: bool = True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        operation = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
        try:
            fcntl.flock(handle.fileno(), operation)
        except BlockingIOError as exc:
            raise ValueError(f"canonical job is already claimed: {path.stem}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
