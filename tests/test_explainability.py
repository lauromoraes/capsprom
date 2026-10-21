import json
from pathlib import Path

import numpy as np

from capsprom.explainability import (
    ActivationWindow,
    log_explainability_artifacts,
    select_max_activation_windows,
    write_activation_logo_artifacts,
)


def test_activation_artifacts_preserve_coordinates_matrices_and_provenance(
    tmp_path: Path,
) -> None:
    windows = [
        ActivationWindow("row-b", "ACGT", 1, 3, 7, 0.8),
        ActivationWindow("row-a", "ACGA", 1, 3, 11, 0.9),
    ]
    manifest_path = write_activation_logo_artifacts(
        tmp_path / "explain",
        windows,
        dataset_id="fixture",
        model_name="capsprom_basic",
        config_sha256="c" * 64,
        checkpoint_sha256="d" * 64,
        seed=13,
        fold=2,
        source_partition="fold_train",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    matrices = json.loads((manifest_path.parent / "motif_matrices.json").read_text())
    selected = (manifest_path.parent / "selected_windows.csv").read_text()
    logo = (manifest_path.parent / "sequence_logo.svg").read_text()
    assert manifest["fold"] == 2
    assert manifest["checkpoint_sha256"] == "d" * 64
    assert set(manifest["artifacts"]) == {
        "selected_windows.csv", "motif_matrices.json", "sequence_logo.svg"
    }
    assert matrices["pfm"][3] == [1, 0, 0, 1]
    assert "row-a,1,3,11,15,+,0.90000000000000002,ACGA" in selected
    assert "Sequence logo from selected convolution activation windows" in logo


def test_activation_maxima_map_to_original_sequence_coordinates() -> None:
    activations = np.asarray(
        [
            [[0.1, 0.9, 0.2], [0.0, 0.0, 0.0]],
            [[0.7, 0.2, 0.1], [0.0, 0.0, 0.0]],
            [[0.2, 0.3, 0.8], [0.0, 0.0, 0.0]],
        ]
    )
    windows = select_max_activation_windows(
        ["a", "b", "c"], ["AACGT", "TTAAA", "CCGTA"], [1, 0, 1], activations,
        kernel_size=3, filter_index=0, eligible_label=1, maximum_windows=1,
    )

    assert windows == [ActivationWindow("a", "ACG", 1, 0, 1, 0.9)]


def test_explainability_directory_is_attached_to_existing_mlflow_run(tmp_path: Path) -> None:
    from mlflow import MlflowClient

    tracking = f"sqlite:///{tmp_path / 'mlflow.db'}"
    client = MlflowClient(tracking_uri=tracking)
    experiment_id = client.create_experiment("explainability-fixture")
    run_id = client.create_run(
        experiment_id,
        tags={"capsprom.run_role": "inner_fold", "mlflow.parentRunId": "parent-fixture"},
    ).info.run_id
    manifest_path = write_activation_logo_artifacts(
        tmp_path / "explain",
        [ActivationWindow("row-1", "AAAA", 1, 0, 0, 1.0)],
        dataset_id="fixture",
        model_name="capsprom_basic",
        config_sha256="a" * 64,
        checkpoint_sha256="b" * 64,
        seed=13,
        fold=0,
        source_partition="fold_train",
    )
    log_explainability_artifacts(client, run_id, manifest_path)
    client.set_terminated(run_id)

    run = client.get_run(run_id)
    artifacts = client.list_artifacts(run_id, "explainability")
    assert run.data.tags["mlflow.parentRunId"] == "parent-fixture"
    assert run.data.tags["capsprom.explainability.fold"] == "0"
    assert {item.path.rsplit("/", 1)[-1] for item in artifacts} == {
        "manifest.json", "motif_matrices.json", "selected_windows.csv", "sequence_logo.svg"
    }
