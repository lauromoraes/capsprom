import json
from pathlib import Path

from capsprom.xgboost_replication import materialize_xgboost_replication


def test_materialize_replication_reuses_existing_seed(tmp_path: Path):
    project = tmp_path / "project"
    config_dir = project / "configs"
    data_dir = project / "data"
    config_dir.mkdir(parents=True)
    data_dir.mkdir()
    (data_dir / "cnnprom-prokaryotic-fixture-p-2-n-2-train.csv").write_text(
        "sequence,label\nAAAAAAAA,1\nAAAAAAAC,1\nCCCCCCCC,0\nCCCCCCCA,0\n"
    )
    (data_dir / "cnnprom-prokaryotic-fixture-p-1-n-1-test.csv").write_text(
        "sequence,label\nAAAAAACC,1\nCCCCCCAA,0\n"
    )
    source = project / "source.json"
    source.write_text(json.dumps({"completed": {
        "cnnprom-prokaryotic-fixture--xgboost": {
            "run_id": "old", "output_dir": "old", "metrics": {"matthews_corrcoef": 0.5},
            "config_sha256": "old", "tier": "confirmatory"
        }
    }}))
    seeds = [13, 29, 42, 71, 101, 137, 173, 211, 251, 293]
    config = config_dir / "replication.yaml"
    config.write_text(f"""
replication:
  name: fixture
  dataset_dir: data
  generated_config_dir: generated
  state_path: state.json
  reuse_state_path: source.json
  reuse_seed: 42
  seeds: {seeds}
  excluded_datasets: []
tracking: {{tracking_uri: sqlite:///mlflow.db, experiment_name: fixture}}
features:
  combination_mode: concatenate
  blocks:
    - {{name: kmer, encoding: kmer_frequency, k: 1, normalize: true}}
model:
  name: xgboost
  hyperparameters: {{n_estimators: 2, max_depth: 1}}
evaluation: {{metrics: [matthews_corrcoef]}}
outputs: {{artifact_dir: outputs/runs}}
""".strip() + "\n")

    plan = materialize_xgboost_replication(config)
    state = json.loads((project / "state.json").read_text())

    assert len(plan) == 10
    assert state["planned_run_count"] == 10
    assert state["reused_run_count"] == 1
    reused = state["completed"]["cnnprom-prokaryotic-fixture--xgboost--seed-42"]
    assert reused["run_id"] == "old"
    assert reused["reused"] is True
