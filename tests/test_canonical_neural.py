import csv
import copy
import json
import statistics
from pathlib import Path

import pytest
import yaml

from capsprom.canonical_neural import (
    SimulatedCanonicalInterruption,
    SimulatedFinalFitInterruption,
    SimulatedFinalTrainingInterruption,
    _get_or_create_experiment,
    prepare_canonical_neural_plan,
    refresh_canonical_final_fit_readiness,
    run_canonical_external_inference_job,
    run_canonical_final_fit_job,
    run_canonical_inner_fold_job,
    run_canonical_inner_fold_jobs,
    run_fixture_final_fit_job,
)


def _write_training_file(path: Path) -> None:
    path.parent.mkdir(parents=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sequence", "label"])
        for index in range(10):
            symbol = "A" if index % 2 == 0 else "C"
            writer.writerow([symbol * 81, index % 2])


def _write_evaluation_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sequence", "label"])
        writer.writerow(["AC" * 40 + "A", 0])
        writer.writerow(["GT" * 40 + "G", 1])
        writer.writerow(["AG" * 40 + "A", 0])
        writer.writerow(["CT" * 40 + "C", 1])


def _write_protocol(path: Path, dataset_root: Path, tracking_uri: str = "./mlruns") -> None:
    relative_root = dataset_root.relative_to(path.parent.parent)
    path.write_text(
        f"""protocol:
  name: fixture
  status: design_locked_test_execution_blocked
  dataset_root: {relative_root.as_posix()}
  dataset_ids: [fixture-source-organism]
selection: {{method: five_fold_then_full_refit, folds: 5, fold_seed: 42, epoch_rule: lower_median_fold_best_epoch}}
replication: {{seeds: [13, 29]}}
model:
  name: capsprom_basic
  input: {{encoding: one_hot, k: 1, sequence_length: 81, channels: 4}}
  architecture:
    convolution_filters: 8
    convolution_kernel: 9
    primary_channels: 2
    primary_dim: 4
    primary_kernel: 9
    primary_stride: 2
    output_capsules: 2
    output_dim: 4
    routing_iterations: 1
    routing_mode: dynamic
    routing_gradient_mode: final_iteration
    decoder_mode: disabled
training:
  runner_contract_version: 6
  batch_size: 4
  optimizer: adam
  learning_rate: 0.0001
  learning_rate_schedule: fixed
  maximum_epochs: 2
  patience: 2
  reconstruction_weight: 0.0
prediction: {{decision: raw_score_argmax}}
tracking: {{backend: mlflow, tracking_uri: "{tracking_uri}", experiment_name: fixture-canonical}}
execution_gates:
  external_test_enabled: false
  require_dataset_hashes: true
  require_fold_manifest_hashes: true
  require_fixture_validation: true
""",
        encoding="utf-8",
    )


def test_prepare_plan_uses_training_only_and_is_resumable(tmp_path: Path) -> None:
    project = tmp_path / "project"
    config = project / "configs" / "canonical.yaml"
    data = project / "data"
    config.parent.mkdir(parents=True)
    _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
    _write_protocol(config, data)
    output = project / "outputs" / "canonical"

    state = prepare_canonical_neural_plan(config, output)
    resumed = prepare_canonical_neural_plan(config, output)

    assert state == resumed
    assert state["external_test_accessed"] is False
    assert state["dataset_count"] == 1
    assert state["total_jobs"] == 12
    assert len(state["datasets"]) == 1
    assert (output / state["datasets"][0]["fold_manifest"]).is_file()
    assert all(job["stage"] != "external_test" for job in state["jobs"])


def test_prepare_plan_rejects_protocol_change_after_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    config = project / "configs" / "canonical.yaml"
    data = project / "data"
    config.parent.mkdir(parents=True)
    _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
    _write_protocol(config, data)
    output = project / "outputs" / "canonical"
    prepare_canonical_neural_plan(config, output)
    config.write_text(config.read_text(encoding="utf-8").replace("[13, 29]", "[13]"))

    with pytest.raises(ValueError, match="protocol changed"):
        prepare_canonical_neural_plan(config, output)


def test_fold_job_resume_reuses_mlflow_run_and_matches_continuous(tmp_path: Path) -> None:
    from mlflow import MlflowClient

    results = []
    run_counts = []
    for mode in ("continuous", "resumed", "failed_retry"):
        project = tmp_path / mode / "project"
        config = project / "configs" / "canonical.yaml"
        data = project / "data"
        config.parent.mkdir(parents=True)
        _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
        tracking = f"sqlite:///{project / 'mlflow.db'}"
        _write_protocol(config, data, tracking)
        output = project / "outputs" / "canonical"
        prepare_canonical_neural_plan(config, output)
        if mode == "resumed":
            with pytest.raises(SimulatedCanonicalInterruption):
                run_canonical_inner_fold_job(
                    config,
                    output,
                    "fixture-source-organism",
                    13,
                    0,
                    interrupt_after_training=True,
                )
            interrupted = prepare_canonical_neural_plan(config, output)
            job = interrupted["jobs"][0]
            assert job["status"] == "running"
            interrupted_run_id = job["run_id"]
        if mode == "failed_retry":
            with pytest.raises(RuntimeError, match="simulated retryable failure"):
                run_canonical_inner_fold_job(
                    config,
                    output,
                    "fixture-source-organism",
                    13,
                    0,
                    fail_after_training=True,
                )
            failed = prepare_canonical_neural_plan(config, output)
            failed_job = failed["jobs"][0]
            assert failed_job["status"] == "failed"
            failed_run_id = failed_job["run_id"]
            failure_event = (
                output
                / "notifications/events"
                / "fixture-source-organism--seed-13--fold-0.json"
            )
            assert json.loads(failure_event.read_text())["status"] == "pending"
        result = run_canonical_inner_fold_job(
            config, output, "fixture-source-organism", 13, 0
        )
        if mode == "resumed":
            assert result["run_id"] == interrupted_run_id
        if mode == "failed_retry":
            assert result["run_id"] == failed_run_id
            assert result["attempts"] == 2
            assert json.loads(failure_event.read_text())["status"] == "resolved"
        state = prepare_canonical_neural_plan(config, output)
        assert state["completed_jobs"] == 1
        assert result["status"] == "completed"
        client = MlflowClient(tracking_uri=tracking)
        experiment = client.get_experiment_by_name("fixture-canonical")
        runs = client.search_runs([experiment.experiment_id])
        assert len(runs) == 2
        child = next(run for run in runs if run.data.tags.get("capsprom.run_role") == "inner_fold")
        parent = next(run for run in runs if run.data.tags.get("capsprom.run_role") == "parent")
        assert child.data.tags["mlflow.parentRunId"] == parent.info.run_id
        assert child.info.status == "FINISHED"
        artifacts = client.list_artifacts(child.info.run_id, "provenance")
        assert {artifact.path.rsplit("/", 1)[-1] for artifact in artifacts} == {
            "fixture-source-organism.csv",
            "state.json",
        }
        results.append((result["best_epoch"], result["best_validation_mcc"]))
        run_counts.append(len(runs))

    assert results[0][0] == results[1][0]
    assert results[0][1] == pytest.approx(results[1][1], abs=0.0, rel=0.0)
    assert results[0][0] == results[2][0]
    assert results[0][1] == pytest.approx(results[2][1], abs=0.0, rel=0.0)
    assert run_counts == [2, 2, 2]


def test_fixture_final_fit_is_gated_resumable_and_logs_row_artifacts(tmp_path: Path) -> None:
    from mlflow import MlflowClient

    observed = []
    for mode in ("continuous", "resumed"):
        project = tmp_path / mode / "project"
        config = project / "configs" / "canonical.yaml"
        data = project / "data"
        config.parent.mkdir(parents=True)
        _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
        evaluation = data / "held-out-fixture.csv"
        _write_evaluation_fixture(evaluation)
        tracking = f"sqlite:///{project / 'mlflow.db'}"
        _write_protocol(config, data, tracking)
        output = project / "outputs" / "canonical"
        prepare_canonical_neural_plan(config, output)
        for fold in range(5):
            run_canonical_inner_fold_job(
                config, output, "fixture-source-organism", 13, fold
            )

        with pytest.raises(ValueError, match="explicitly declared fixture"):
            run_fixture_final_fit_job(
                config,
                output,
                "fixture-source-organism",
                13,
                evaluation,
                fixture_only=False,
            )
        if mode == "resumed":
            with pytest.raises(SimulatedFinalFitInterruption):
                run_fixture_final_fit_job(
                    config,
                    output,
                    "fixture-source-organism",
                    13,
                    evaluation,
                    fixture_only=True,
                    interrupt_after_artifacts=True,
                )
            interrupted = prepare_canonical_neural_plan(config, output)
            assert interrupted["external_test_accessed"] is False
            assert interrupted["fixture_evaluation_accessed"] is True
            assert _final_job(interrupted)["status"] == "artifacts_persisted_fixture_validation"

        result = run_fixture_final_fit_job(
            config,
            output,
            "fixture-source-organism",
            13,
            evaluation,
            fixture_only=True,
        )
        state = prepare_canonical_neural_plan(config, output)
        assert result["status"] == "completed_fixture_validation"
        assert result["attempts"] == (2 if mode == "resumed" else 1)
        assert state["external_test_accessed"] is False
        assert state["fixture_evaluation_accessed"] is True
        assert result["selected_epoch"] in {1, 2}

        artifact_dir = (
            output
            / "jobs"
            / "fixture-source-organism"
            / "seed-13"
            / "final-fit-fixture"
            / "artifacts"
        )
        prediction_text = (artifact_dir / "predictions.csv").read_text(encoding="utf-8")
        assert "capsule_0_length,capsule_1_length,positive_score,prediction" in prediction_text
        assert (artifact_dir / "metrics.json").is_file()
        assert (artifact_dir / "explainability/filter-0/sequence_logo.svg").is_file()

        client = MlflowClient(tracking_uri=tracking)
        experiment = client.get_experiment_by_name("fixture-canonical")
        runs = client.search_runs([experiment.experiment_id])
        assert len(runs) == 7
        final_runs = [
            run
            for run in runs
            if run.data.tags.get("capsprom.run_role") == "final_fit_fixture_validation"
        ]
        assert len(final_runs) == 1
        assert final_runs[0].info.status == "FINISHED"
        assert client.list_artifacts(final_runs[0].info.run_id, "evaluation")
        assert client.list_artifacts(final_runs[0].info.run_id, "explainability")
        observed.append((prediction_text, result["metrics"]))

    assert observed[0] == observed[1]


def _final_job(state: dict) -> dict:
    return next(
        job
        for job in state["jobs"]
        if job["stage"] == "final_fit"
        and job["dataset_id"] == "fixture-source-organism"
        and job["seed"] == 13
    )


def test_gpu_contract_changes_only_execution_identity_and_blocked_gates() -> None:
    root = Path(__file__).parents[1]
    cpu = yaml.safe_load((root / "configs/capsprom_basic_canonical_v1.yaml").read_text())
    gpu = yaml.safe_load(
        (root / "configs/capsprom_basic_canonical_gpu_v1.yaml").read_text()
    )
    normalized = copy.deepcopy(gpu)
    normalized["protocol"]["name"] = cpu["protocol"]["name"]
    normalized["tracking"]["experiment_name"] = cpu["tracking"]["experiment_name"]
    normalized["training"]["runner_contract_version"] = cpu["training"][
        "runner_contract_version"
    ]
    normalized["training"].pop("device")
    normalized["execution_gates"].pop("canonical_jobs_enabled")
    normalized["execution_gates"].pop("embedding_jobs_enabled")

    assert normalized == cpu
    assert gpu["training"]["runner_contract_version"] == 7
    assert gpu["training"]["device"] == "cuda"
    assert gpu["execution_gates"]["canonical_jobs_enabled"] is False
    assert gpu["execution_gates"]["embedding_jobs_enabled"] is False


def test_gpu_execution_candidate_changes_only_authorized_execution_fields() -> None:
    root = Path(__file__).parents[1]
    blocked = yaml.safe_load(
        (root / "configs/capsprom_basic_canonical_gpu_v1.yaml").read_text()
    )
    candidate = yaml.safe_load(
        (
            root / "configs/capsprom_basic_canonical_gpu_execution_v1.yaml"
        ).read_text()
    )
    normalized = copy.deepcopy(candidate)
    normalized["protocol"] = copy.deepcopy(blocked["protocol"])
    normalized["tracking"]["experiment_name"] = blocked["tracking"][
        "experiment_name"
    ]
    normalized["tracking"].pop("tracking_uri")
    normalized["tracking"].pop("artifact_location")
    normalized["execution_gates"]["canonical_jobs_enabled"] = False
    normalized["execution_gates"].pop("final_fits_enabled")

    assert normalized == blocked
    assert candidate["protocol"]["status"] == "draft_awaiting_explicit_authorization"
    assert candidate["tracking"]["tracking_uri"].startswith("sqlite:////home/lauro/")
    assert candidate["tracking"]["artifact_location"].startswith(
        "file:///home/lauro/"
    )
    assert candidate["execution_gates"]["canonical_jobs_enabled"] is True
    assert candidate["execution_gates"]["final_fits_enabled"] is False
    assert candidate["execution_gates"]["external_test_enabled"] is False
    assert candidate["execution_gates"]["embedding_jobs_enabled"] is False
    assert not (
        root
        / "outputs/capsprom_basic_canonical_gpu_execution_v1/plan_state.json"
    ).exists()


def test_mlflow_experiment_artifact_location_is_immutable(tmp_path: Path) -> None:
    from mlflow import MlflowClient

    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    artifact_location = (tmp_path / "artifacts").as_uri()
    client = MlflowClient(tracking_uri=tracking_uri)

    experiment_id = _get_or_create_experiment(
        client, "fixture-explicit-artifacts", artifact_location
    )

    assert (
        _get_or_create_experiment(
            client, "fixture-explicit-artifacts", artifact_location
        )
        == experiment_id
    )
    experiment = client.get_experiment(experiment_id)
    assert experiment.artifact_location == artifact_location
    with pytest.raises(ValueError, match="conflicting artifact location"):
        _get_or_create_experiment(
            client,
            "fixture-explicit-artifacts",
            (tmp_path / "other-artifacts").as_uri(),
        )


def test_versioned_gate_blocks_canonical_fold_execution(tmp_path: Path) -> None:
    project = tmp_path / "project"
    config = project / "configs" / "canonical.yaml"
    data = project / "data"
    config.parent.mkdir(parents=True)
    _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
    _write_protocol(config, data)
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "require_fixture_validation: true",
            "require_fixture_validation: true\n  canonical_jobs_enabled: false",
        ),
        encoding="utf-8",
    )
    output = project / "outputs" / "canonical"
    prepare_canonical_neural_plan(config, output)

    with pytest.raises(ValueError, match="blocked by the versioned contract"):
        run_canonical_inner_fold_job(
            config, output, "fixture-source-organism", 13, 0
        )

    state = prepare_canonical_neural_plan(config, output)
    assert state["completed_jobs"] == 0
    assert state["jobs"][0]["status"] == "pending"


def test_external_inference_gate_is_checked_before_evaluation_input(tmp_path: Path) -> None:
    project = tmp_path / "project"
    config = project / "configs" / "canonical.yaml"
    data = project / "data"
    config.parent.mkdir(parents=True)
    _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
    _write_protocol(config, data)
    output = project / "outputs" / "canonical"
    prepare_canonical_neural_plan(config, output)

    with pytest.raises(ValueError, match="external inference is blocked"):
        run_canonical_external_inference_job(
            config,
            output,
            "fixture-source-organism",
            13,
            project / "must-not-be-opened.csv",
        )
    assert prepare_canonical_neural_plan(config, output)["external_test_accessed"] is False


def test_readiness_refresh_selects_epoch_without_evaluation_access(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    config = project / "configs" / "canonical.yaml"
    data = project / "data"
    config.parent.mkdir(parents=True)
    _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
    _write_protocol(config, data, f"sqlite:///{project / 'mlflow.db'}")
    output = project / "outputs" / "canonical"
    prepare_canonical_neural_plan(config, output)

    before = refresh_canonical_final_fit_readiness(config, output)
    for fold in range(5):
        run_canonical_inner_fold_job(
            config, output, "fixture-source-organism", 13, fold
        )
    refreshed = refresh_canonical_final_fit_readiness(config, output)
    repeated = refresh_canonical_final_fit_readiness(config, output)
    state = prepare_canonical_neural_plan(config, output)
    final = _final_job(state)

    assert before["newly_ready_count"] == 0
    assert refreshed["newly_ready_count"] == 1
    assert refreshed["ready_total"] == 1
    assert repeated["newly_ready_count"] == 0
    assert repeated["ready_total"] == 1
    assert refreshed["external_test_accessed"] is False
    assert state["external_test_accessed"] is False
    assert "fixture_evaluation_accessed" not in state
    assert final["status"] == "ready_for_final_fit"
    assert final["selected_epoch"] == statistics.median_low(
        final["fold_best_epochs"]
    )


def test_final_fit_training_is_gated_and_resume_reuses_mlflow_run(
    tmp_path: Path,
) -> None:
    from mlflow import MlflowClient

    observed = []
    for mode in ("continuous", "resumed"):
        project = tmp_path / mode / "project"
        config = project / "configs" / "canonical.yaml"
        data = project / "data"
        config.parent.mkdir(parents=True)
        _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
        tracking = f"sqlite:///{project / 'mlflow.db'}"
        _write_protocol(config, data, tracking)
        output = project / "outputs" / "canonical"
        prepare_canonical_neural_plan(config, output)

        with pytest.raises(ValueError, match="must be ready_for_final_fit"):
            run_canonical_final_fit_job(
                config, output, "fixture-source-organism", 13, fixture_only=True
            )
        for fold in range(5):
            run_canonical_inner_fold_job(
                config, output, "fixture-source-organism", 13, fold
            )
        refresh_canonical_final_fit_readiness(config, output)
        with pytest.raises(ValueError, match="blocked by the versioned contract"):
            run_canonical_final_fit_job(
                config, output, "fixture-source-organism", 13
            )

        if mode == "resumed":
            with pytest.raises(SimulatedFinalTrainingInterruption):
                run_canonical_final_fit_job(
                    config,
                    output,
                    "fixture-source-organism",
                    13,
                    fixture_only=True,
                    interrupt_after_training=True,
                )
            interrupted = prepare_canonical_neural_plan(config, output)
            interrupted_job = _final_job(interrupted)
            assert interrupted_job["status"] == "ready_for_final_fit"
            interrupted_run_id = interrupted_job["run_id"]

        result = run_canonical_final_fit_job(
            config, output, "fixture-source-organism", 13, fixture_only=True
        )
        repeated = run_canonical_final_fit_job(
            config, output, "fixture-source-organism", 13, fixture_only=True
        )
        assert repeated == result
        assert result["status"] == "completed_final_fit_training"
        if mode == "resumed":
            assert result["run_id"] == interrupted_run_id
            assert result["attempts"] == 2
        assert prepare_canonical_neural_plan(config, output)["external_test_accessed"] is False

        client = MlflowClient(tracking_uri=tracking)
        experiment = client.get_experiment_by_name("fixture-canonical")
        runs = client.search_runs([experiment.experiment_id])
        final_runs = [
            run
            for run in runs
            if run.data.tags.get("capsprom.run_role") == "final_fit_training"
        ]
        assert len(runs) == 7
        assert len(final_runs) == 1
        assert final_runs[0].info.status == "FINISHED"
        assert final_runs[0].info.run_id == result["run_id"]
        observed.append(
            json.loads(
                (
                    output
                    / "jobs/fixture-source-organism/seed-13/final-fit/state.json"
                ).read_text(encoding="utf-8")
            )
        )

    assert observed[0]["status"] == observed[1]["status"] == "completed"
    assert observed[0]["epochs_completed"] == observed[1]["epochs_completed"]
    assert observed[0]["history"] == observed[1]["history"]


def test_bounded_dispatch_uses_one_parent_and_distinct_mlflow_children(
    tmp_path: Path,
) -> None:
    from mlflow import MlflowClient

    project = tmp_path / "project"
    config = project / "configs" / "canonical.yaml"
    data = project / "data"
    config.parent.mkdir(parents=True)
    _write_training_file(data / "fixture-source-organism-p-5-n-5-train.csv")
    tracking = f"sqlite:///{project / 'mlflow.db'}"
    _write_protocol(config, data, tracking)
    output = project / "outputs" / "canonical"
    prepare_canonical_neural_plan(config, output)

    results = run_canonical_inner_fold_jobs(
        config,
        output,
        [
            ("fixture-source-organism", 13, 0),
            ("fixture-source-organism", 13, 1),
        ],
        maximum_workers=2,
    )

    assert [result["fold"] for result in results] == [0, 1]
    assert all(result["status"] == "completed" for result in results)
    state = prepare_canonical_neural_plan(config, output)
    assert state["completed_jobs"] == 2
    client = MlflowClient(tracking_uri=tracking)
    experiment = client.get_experiment_by_name("fixture-canonical")
    runs = client.search_runs([experiment.experiment_id])
    parents = [run for run in runs if run.data.tags.get("capsprom.run_role") == "parent"]
    children = [
        run for run in runs if run.data.tags.get("capsprom.run_role") == "inner_fold"
    ]
    assert len(parents) == 1
    assert len(children) == 2
    assert {run.data.tags["mlflow.parentRunId"] for run in children} == {
        parents[0].info.run_id
    }
    assert all(run.info.status == "FINISHED" for run in children)


def test_remote_policy_is_single_gpu_writer_and_keeps_cpu_host_auxiliary() -> None:
    root = Path(__file__).parents[1]
    policy = yaml.safe_load(
        (root / "configs/capsprom_remote_execution_policy_v1.yaml").read_text()
    )

    assert policy["gpu_training"]["host"] == "bioserver03"
    assert policy["gpu_training"]["maximum_concurrent_workers"] == 1
    assert policy["tracking"]["backend"] == "sqlite"
    assert policy["tracking"]["topology"] == "host_local_single_writer"
    assert policy["tracking"]["network_filesystem_sharing"] is False
    assert policy["cpu_auxiliary"]["host"] == "bioserver04"
    assert policy["cpu_auxiliary"]["canonical_training_workers"] == 0
    assert all(value is False for value in policy["execution_gates"].values())


def test_future_campaign_release_policy_remains_locally_blocked() -> None:
    root = Path(__file__).parents[1]
    policy = yaml.safe_load(
        (root / "configs/capsprom_future_campaign_release_policy_v1.yaml").read_text()
    )

    assert policy["policy"]["status"] == "local_draft_execution_blocked"
    assert policy["scope"]["pending_inner_folds_documented_locally"] == 1290
    assert policy["epoch_ceiling_policy"]["current_documented_contacts"] == [
        {
            "dataset_id": "cdbprom-prokaryotic-chlamydophila_pneumoniae",
            "seed": 13,
            "fold": 3,
            "best_epoch": 30,
        }
    ]
    assert all(value is False for value in policy["execution_gates"].values())
