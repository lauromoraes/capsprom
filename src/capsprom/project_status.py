"""Compact project status for human and AI-assisted resumptions."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .state import write_json_atomic


def collect_project_status(root: Path | None = None) -> dict[str, Any]:
    """Collect Git and experiment checkpoint state without loading ML libraries."""

    project_root = (root or Path(__file__).resolve().parents[2]).resolve()
    status: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "repository_root": project_root.as_posix(),
        "git": _git_status(project_root),
        "active_dataset": "data/processed/assembled_datasets/intra_regenerated_v3_strict_dna",
        "active_dataset_eligibility_manifest": "configs/dataset_eligibility_manifest_v1.yaml",
        "active_confirmatory_dataset_count": 18,
        "active_evaluation_protocol": "configs/evaluation_protocol_v3.yaml",
        "graphpro_policy": "configs/graphpro_deferral_policy_v1.yaml",
        "experiments": {},
        "remote_jobs": _remote_job_status(project_root),
    }
    contracts = {
        "fixed_seed_baseline": (
            "configs/real_negative_baseline_batch.yaml",
            "outputs/reports/real_negative_baseline_batch/batch_state.json",
        ),
        "xgboost_replication_v1": (
            "configs/xgboost_ten_seed_replication.yaml",
            "outputs/reports/xgboost_ten_seed_replication/replication_state.json",
        ),
        "xgboost_replication_v2": (
            "configs/xgboost_ten_seed_replication_v2.yaml",
            "outputs/reports/xgboost_ten_seed_replication_v2/replication_state.json",
        ),
    }
    for name, (config_relative, state_relative) in contracts.items():
        config = project_root / config_relative
        state = project_root / state_relative
        entry: dict[str, Any] = {
            "config": config_relative,
            "config_sha256": _sha256(config) if config.is_file() else None,
            "state": state_relative,
            "state_available": state.is_file(),
        }
        if state.is_file():
            payload = json.loads(state.read_text(encoding="utf-8"))
            planned = int(payload.get("planned_run_count", 0))
            completed_runs = payload.get("completed", {})
            completed = len(completed_runs)
            if name == "fixed_seed_baseline":
                planned = int(payload.get("confirmatory_run_count", planned))
                completed = sum(run.get("tier") == "confirmatory" for run in completed_runs.values())
            entry.update({
                "planned": planned,
                "completed": completed,
                "remaining": planned - completed,
                "reused": int(payload.get("reused_run_count", 0)),
            })
        status["experiments"][name] = entry
    active = status["experiments"]["xgboost_replication_v2"]
    summary_relative = "outputs/reports/xgboost_ten_seed_replication_v2/ten_seed_summary.json"
    summary = project_root / summary_relative
    active["summary"] = summary_relative
    active["summary_available"] = summary.is_file()
    active_summary = (
        project_root / "outputs/reports/active_baseline_consolidation_v1/summary.json"
    )
    status["active_baseline_consolidation"] = {
        "config": "configs/active_baseline_consolidation_v1.yaml",
        "summary": "outputs/reports/active_baseline_consolidation_v1/summary.json",
        "summary_available": active_summary.is_file(),
    }
    if active.get("remaining", 0):
        status["next_action"] = "make replication-resume"
    elif not summary.is_file():
        status["next_action"] = "make replication-summary"
    elif not active_summary.is_file():
        status["next_action"] = "make baseline-consolidation"
    else:
        status["next_action"] = (
            "readiness synced on bioserver03; authorize configs/capsprom_campaign_release_v4.yaml"
        )
    return status


def write_status_snapshot(path: Path, root: Path | None = None) -> dict[str, Any]:
    """Write a compact versionable snapshot and return it."""

    status = collect_project_status(root)
    snapshot = dict(status)
    snapshot.pop("repository_root", None)
    snapshot.pop("git", None)
    write_json_atomic(path, snapshot)
    return snapshot


def _git_status(root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        result = subprocess.run(
            ("git", *args), cwd=root, check=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    try:
        porcelain = run("status", "--porcelain")
        return {
            "branch": run("branch", "--show-current"),
            "commit": run("rev-parse", "HEAD"),
            "clean": not bool(porcelain),
            "changed_path_count": len(porcelain.splitlines()) if porcelain else 0,
        }
    except (OSError, subprocess.CalledProcessError):
        return {"available": False}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _remote_job_status(root: Path) -> dict[str, Any]:
    registry_path = root / "manifests/remote_jobs.json"
    relative = "manifests/remote_jobs.json"
    if not registry_path.is_file():
        return {"registry": relative, "available": False, "pending_count": 0, "jobs": []}
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    jobs = payload.get("jobs", [])
    pending = [job for job in jobs if job.get("status") in {"pending", "running"}]
    return {
        "registry": relative,
        "available": True,
        "updated_at_utc": payload.get("updated_at_utc"),
        "pending_count": len(pending),
        "jobs": pending,
    }
