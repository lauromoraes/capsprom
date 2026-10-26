import json
import subprocess
from pathlib import Path

from capsprom.project_status import collect_project_status, write_status_snapshot


def test_status_reports_checkpoint_and_writes_portable_snapshot(tmp_path: Path):
    root = tmp_path / "project"
    (root / "configs").mkdir(parents=True)
    state_dir = root / "outputs/reports/xgboost_ten_seed_replication_v2"
    state_dir.mkdir(parents=True)
    (root / "configs/xgboost_ten_seed_replication_v2.yaml").write_text("version: 2\n")
    (state_dir / "replication_state.json").write_text(json.dumps({
        "planned_run_count": 10,
        "reused_run_count": 1,
        "completed": {"one": {}},
    }))
    (root / "manifests").mkdir()
    (root / "manifests/remote_jobs.json").write_text(json.dumps({
        "schema_version": 1,
        "updated_at_utc": "2026-10-23T00:00:00+00:00",
        "jobs": [{"job_id": "remote-1", "status": "running"}],
    }))
    subprocess.run(("git", "init"), cwd=root, check=True, capture_output=True)
    snapshot_path = root / "manifests/current_status.json"

    status = collect_project_status(root)
    written = write_status_snapshot(snapshot_path, root)

    assert status["experiments"]["xgboost_replication_v2"]["remaining"] == 9
    assert status["experiments"]["xgboost_replication_v2"]["summary_available"] is False
    assert status["active_confirmatory_dataset_count"] == 18
    assert status["active_evaluation_protocol"] == "configs/evaluation_protocol_v3.yaml"
    assert status["graphpro_policy"] == "configs/graphpro_deferral_policy_v1.yaml"
    assert status["remote_jobs"]["pending_count"] == 1
    assert status["remote_jobs"]["jobs"][0]["job_id"] == "remote-1"
    assert written["next_action"] == "make replication-resume"
    assert "repository_root" not in json.loads(snapshot_path.read_text())
