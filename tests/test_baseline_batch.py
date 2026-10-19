from pathlib import Path

import pytest

from capsprom.baseline_batch import materialize_baseline_batch


def test_materialize_canonical_batch(tmp_path: Path):
    project = tmp_path / "project"
    config_dir = project / "configs"
    data_dir = project / "data"
    config_dir.mkdir(parents=True)
    data_dir.mkdir()
    train = data_dir / "cnnprom-prokaryotic-fixture-p-2-n-2-train.csv"
    test = data_dir / "cnnprom-prokaryotic-fixture-p-1-n-1-test.csv"
    train.write_text("sequence,label\nAAAAAAAA,1\nAAAAAAAC,1\nCCCCCCCC,0\nCCCCCCCA,0\n")
    test.write_text("sequence,label\nAAAAAACC,1\nCCCCCCAA,0\n")
    batch = config_dir / "batch.yaml"
    batch.write_text(
        """
batch:
  name: fixture
  dataset_dir: data
  generated_config_dir: generated
  state_path: state.json
  random_seed: 42
  excluded_from_confirmatory: [cnnprom-prokaryotic-fixture]
tracking: {tracking_uri: sqlite:///mlflow.db, experiment_name: fixture}
features:
  combination_mode: concatenate
  blocks:
    - {name: kmer, encoding: kmer_frequency, k: 1, normalize: true}
models:
  logistic_regression: {solver: liblinear}
  xgboost: {n_estimators: 2, max_depth: 1}
evaluation: {metrics: [matthews_corrcoef]}
outputs: {artifact_dir: outputs/runs}
""".strip()
        + "\n"
    )

    plan = materialize_baseline_batch(batch)

    assert len(plan) == 2
    assert {item.model for item in plan} == {"logistic_regression", "xgboost"}
    assert {item.tier for item in plan} == {"exploratory"}
    assert all(item.config_path.is_file() for item in plan)
    assert (project / "state.json").is_file()

    batch.write_text(batch.read_text().replace("name: fixture", "name: changed", 1))
    with pytest.raises(ValueError, match="configuration changed"):
        materialize_baseline_batch(batch)
