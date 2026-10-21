"""Small operational primitives for the blocked canonical remote campaign."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .state import write_json_atomic


def build_pending_fold_schedule(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Order runnable inner folds deterministically, smallest datasets first."""

    rows = {item["dataset_id"]: int(item["train_rows"]) for item in plan["datasets"]}
    eligible = [
        dict(job)
        for job in plan["jobs"]
        if job["stage"] == "inner_fold"
        and job["status"] in {"pending", "failed"}
        and int(job.get("attempts", 0)) < 3
    ]
    return sorted(
        eligible,
        key=lambda job: (
            rows[job["dataset_id"]],
            job["dataset_id"],
            int(job["seed"]),
            int(job["fold"]),
        ),
    )


def write_failure_event(
    outbox_dir: Path,
    *,
    job_key: str,
    error: str,
    attempt: int,
    run_id: str | None,
) -> Path:
    """Persist one replaceable notification event without external delivery."""

    if not job_key or not error or attempt < 1:
        raise ValueError("failure event requires job key, error, and positive attempt")
    path = outbox_dir / "events" / f"{job_key}.json"
    write_json_atomic(
        path,
        {
            "schema_version": 1,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "job_key": job_key,
            "attempt": attempt,
            "run_id": run_id,
            "error": error,
            "status": "pending",
            "delivery": "filesystem_outbox",
        },
    )
    return path


def resolve_failure_event(outbox_dir: Path, *, job_key: str) -> Path | None:
    """Mark an existing failure event resolved while preserving its audit trail."""

    path = outbox_dir / "events" / f"{job_key}.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["status"] = "resolved"
    payload["resolved_at_utc"] = datetime.now(UTC).isoformat()
    write_json_atomic(path, payload)
    return path


def backup_sqlite_store(database: Path, destination: Path) -> dict[str, Any]:
    """Create an internally consistent SQLite backup and hashed manifest."""

    if not database.is_file():
        raise ValueError("MLflow SQLite database does not exist")
    destination.mkdir(parents=True, exist_ok=True)
    backup_path = destination / "mlflow.db"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".mlflow.db.", suffix=".tmp", dir=destination
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with sqlite3.connect(database) as source, sqlite3.connect(temporary) as target:
            source.backup(target)
        os.replace(temporary, backup_path)
    finally:
        temporary.unlink(missing_ok=True)
    integrity = _sqlite_integrity(backup_path)
    if integrity != "ok":
        raise ValueError(f"backed-up SQLite integrity check failed: {integrity}")
    manifest = {
        "schema_version": 1,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_name": database.name,
        "backup_name": backup_path.name,
        "backup_size_bytes": backup_path.stat().st_size,
        "backup_sha256": _sha256(backup_path),
        "sqlite_integrity_check": integrity,
        "scope": "tracking_database_only_artifacts_require_separate_snapshot",
    }
    write_json_atomic(destination / "backup_manifest.json", manifest)
    return manifest


def write_artifact_snapshot_manifest(root: Path, manifest_path: Path) -> dict[str, Any]:
    """Hash every regular file below an artifact snapshot root."""

    if not root.is_dir():
        raise ValueError("artifact snapshot root does not exist")
    files = [path for path in sorted(root.rglob("*")) if path.is_file()]
    if not files:
        raise ValueError("artifact snapshot root contains no files")
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "file_count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in files
        ],
    }
    write_json_atomic(manifest_path, payload)
    return payload


def verify_artifact_snapshot(root: Path, manifest_path: Path) -> dict[str, Any]:
    """Verify exact file membership, sizes, and hashes for a copied snapshot."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {item["path"]: item for item in manifest["files"]}
    observed_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.resolve() != manifest_path.resolve()
    }
    missing = sorted(set(expected) - observed_paths)
    unexpected = sorted(observed_paths - set(expected))
    mismatched = []
    for relative in sorted(set(expected) & observed_paths):
        path = root / relative
        item = expected[relative]
        if path.stat().st_size != int(item["size_bytes"]) or _sha256(path) != item["sha256"]:
            mismatched.append(relative)
    return {
        "valid": not missing and not unexpected and not mismatched,
        "expected_file_count": len(expected),
        "missing": missing,
        "unexpected": unexpected,
        "mismatched": mismatched,
    }


def _sqlite_integrity(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
