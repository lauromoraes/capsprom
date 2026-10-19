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
    source_config = project / "source-run.yaml"
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

    source_config.write_text(config.read_text().replace(
        "replication:\n  name: fixture\n  dataset_dir: data\n  generated_config_dir: generated\n"
        "  state_path: state.json\n  reuse_state_path: source.json\n  reuse_seed: 42\n"
        f"  seeds: {seeds}\n  excluded_datasets: []\n",
        "project: {name: source}\n",
    ).replace(
        "model:\n  name: xgboost\n  hyperparameters: {n_estimators: 2, max_depth: 1}\n",
        "model:\n  name: xgboost\n  hyperparameters: {n_estimators: 2, max_depth: 1}\n",
    ).replace(
        "tracking: {tracking_uri: sqlite:///mlflow.db, experiment_name: fixture}\n",
        "tracking: {tracking_uri: sqlite:///mlflow.db, experiment_name: source}\n"
        "data:\n"
        f"  train_csv: {(data_dir / 'cnnprom-prokaryotic-fixture-p-2-n-2-train.csv').as_posix()}\n"
        f"  test_csv: {(data_dir / 'cnnprom-prokaryotic-fixture-p-1-n-1-test.csv').as_posix()}\n"
        "  sequence_column: sequence\n  label_column: label\n  sequence_length: 81\n"
        "  alphabet: [A, C, G, T]\n  max_train_samples: null\n  max_test_samples: null\n"
        "  random_seed: 42\n",
    ))
    source_payload = {
        "plan": [{
            "key": "cnnprom-prokaryotic-fixture--xgboost",
            "config_path": source_config.as_posix(),
            "config_sha256": "old",
        }],
        "completed": {
            "cnnprom-prokaryotic-fixture--xgboost": {
                "run_id": "old", "output_dir": "old", "metrics": {"matthews_corrcoef": 0.5},
                "config_sha256": "old", "tier": "confirmatory"
            }
        },
    }
    source.write_text(json.dumps(source_payload))

    plan = materialize_xgboost_replication(config)
    state = json.loads((project / "state.json").read_text())

    assert len(plan) == 10
    assert state["planned_run_count"] == 10
    assert state["reused_run_count"] == 1
    reused = state["completed"]["cnnprom-prokaryotic-fixture--xgboost--seed-42"]
    assert reused["run_id"] == "old"
    assert reused["reused"] is True
    assert reused["source_config_sha256"] == "old"
    assert reused["replication_config_sha256"]
