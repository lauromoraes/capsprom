import json
import sqlite3
from pathlib import Path

import yaml

from capsprom.remote_operations import (
    backup_sqlite_store,
    build_pending_fold_schedule,
    resolve_failure_event,
    verify_artifact_snapshot,
    write_artifact_snapshot_manifest,
    write_failure_event,
)


def test_schedule_is_smallest_first_deterministic_and_retry_bounded() -> None:
    plan = {
        "datasets": [
            {"dataset_id": "large", "train_rows": 100},
            {"dataset_id": "small", "train_rows": 10},
        ],
        "jobs": [
            {"dataset_id": "large", "seed": 13, "stage": "inner_fold", "fold": 0, "status": "pending"},
            {"dataset_id": "small", "seed": 29, "stage": "inner_fold", "fold": 1, "status": "failed", "attempts": 2},
            {"dataset_id": "small", "seed": 13, "stage": "inner_fold", "fold": 0, "status": "pending"},
            {"dataset_id": "small", "seed": 13, "stage": "inner_fold", "fold": 1, "status": "failed", "attempts": 3},
            {"dataset_id": "small", "seed": 13, "stage": "final_fit", "status": "blocked_pending_epoch_selection"},
        ],
    }

    schedule = build_pending_fold_schedule(plan)

    assert [(job["dataset_id"], job["seed"], job["fold"]) for job in schedule] == [
        ("small", 13, 0),
        ("small", 29, 1),
        ("large", 13, 0),
    ]


def test_failure_outbox_is_atomic_and_retry_replaces_same_job_event(tmp_path: Path) -> None:
    path = write_failure_event(
        tmp_path / "notifications",
        job_key="dataset--seed-13--fold-0",
        error="RuntimeError: fixture",
        attempt=1,
        run_id="run-1",
    )
    replaced = write_failure_event(
        tmp_path / "notifications",
        job_key="dataset--seed-13--fold-0",
        error="RuntimeError: fixture again",
        attempt=2,
        run_id="run-1",
    )
    resolved = resolve_failure_event(
        tmp_path / "notifications", job_key="dataset--seed-13--fold-0"
    )

    payload = json.loads(path.read_text())
    assert replaced == path
    assert resolved == path
    assert payload["attempt"] == 2
    assert payload["run_id"] == "run-1"
    assert payload["status"] == "resolved"
    assert list(path.parent.glob("*.json")) == [path]


def test_sqlite_backup_is_consistent_hashed_and_independent(tmp_path: Path) -> None:
    source = tmp_path / "mlflow.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE runs (id TEXT PRIMARY KEY, status TEXT)")
        connection.execute("INSERT INTO runs VALUES ('one', 'FINISHED')")
    destination = tmp_path / "backup"

    manifest = backup_sqlite_store(source, destination)
    with sqlite3.connect(source) as connection:
        connection.execute("INSERT INTO runs VALUES ('two', 'RUNNING')")
    with sqlite3.connect(destination / "mlflow.db") as connection:
        rows = connection.execute("SELECT id, status FROM runs").fetchall()

    assert rows == [("one", "FINISHED")]
    assert manifest["sqlite_integrity_check"] == "ok"
    assert manifest["backup_size_bytes"] > 0
    assert len(manifest["backup_sha256"]) == 64


def test_artifact_snapshot_manifest_detects_exact_copy_and_tampering(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "nested").mkdir(parents=True)
    (source / "model.pt").write_bytes(b"model-fixture")
    (source / "nested/metrics.json").write_text('{"mcc": 0.5}\n')
    manifest_path = tmp_path / "snapshot_manifest.json"
    manifest = write_artifact_snapshot_manifest(source, manifest_path)
    restored = tmp_path / "restored"
    (restored / "nested").mkdir(parents=True)
    (restored / "model.pt").write_bytes((source / "model.pt").read_bytes())
    (restored / "nested/metrics.json").write_bytes(
        (source / "nested/metrics.json").read_bytes()
    )

    verified = verify_artifact_snapshot(restored, manifest_path)
    (restored / "model.pt").write_bytes(b"tampered")
    tampered = verify_artifact_snapshot(restored, manifest_path)

    assert manifest["file_count"] == 2
    assert verified["valid"] is True
    assert tampered["valid"] is False
    assert tampered["mismatched"] == ["model.pt"]


def test_remote_usage_policy_is_local_first_and_campaign_bounded() -> None:
    root = Path(__file__).parents[1]
    policy = yaml.safe_load(
        (root / "configs/capsprom_remote_usage_policy_v2.yaml").read_text()
    )

    assert policy["policy"]["status"] == "active_local_first"
    assert policy["default_work_location"]["host"] == "local"
    assert policy["remote_access"]["default"] == "do_not_access"
    assert policy["remote_access"]["requires_explicit_bounded_authorization"] is True
    assert policy["synchronization"]["routine_remote_updates"] is False
    assert policy["bioserver03"]["primary_role"] == "gpu_heavy_or_many_fit_execution"
    assert policy["bioserver04"]["primary_role"] == "heavy_cpu_auxiliary_and_remote_backup"
    assert policy["execution_gates"]["current_campaign_paused"] is True
    assert policy["execution_gates"]["final_fits_enabled"] is False
    assert policy["execution_gates"]["external_test_enabled"] is False
    assert policy["execution_gates"]["embedding_jobs_enabled"] is False
