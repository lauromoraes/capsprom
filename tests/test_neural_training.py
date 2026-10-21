from pathlib import Path

import pytest
import json

torch = pytest.importorskip("torch")

from capsprom.models.capsprom import CapsPromConfig  # noqa: E402
from capsprom.neural_training import (  # noqa: E402
    NeuralTrainingConfig,
    SimulatedFixedEpochInterruption,
    encode_one_hot,
    run_fixed_epoch_training,
    run_training_only,
    run_training_with_validation,
)
from capsprom.neural_experiment import load_neural_experiment_config  # noqa: E402


def test_encode_one_hot_uses_canonical_channel_order() -> None:
    encoded = encode_one_hot(["ACGT"], 4)
    assert torch.equal(encoded[0], torch.eye(4))


def test_training_only_runner_writes_atomic_state_and_checkpoint(tmp_path: Path) -> None:
    sequences = ["ACGT" * 7 for _ in range(10)] + ["TGCA" * 7 for _ in range(10)]
    labels = [0] * 10 + [1] * 10
    capsule = CapsPromConfig(
        sequence_length=28,
        convolution_filters=8,
        primary_channels=2,
        primary_dim=4,
        output_capsules=2,
        output_dim=4,
        decoder_hidden=(8, 8),
        routing_iterations=1,
    )
    config = NeuralTrainingConfig(
        model_name="capsprom_basic",
        random_seed=42,
        validation_fraction=0.2,
        batch_size=8,
        learning_rate=0.001,
        maximum_epochs=1,
        patience=1,
        checkpoint_path=tmp_path / "best.pt",
        state_path=tmp_path / "state.json",
        capsule=capsule,
        learning_rate_schedule="exponential",
        learning_rate_decay=0.9,
    )

    result = run_training_only(sequences, labels, config)

    assert result.epochs_completed == 1
    assert result.checkpoint_path.is_file()
    assert config.state_path.is_file()
    assert (tmp_path / "best.latest.pt").is_file()
    latest = torch.load(tmp_path / "best.latest.pt", map_location="cpu", weights_only=False)
    assert "scheduler_state" in latest
    history = json.loads(config.state_path.read_text(encoding="utf-8"))["history"]
    assert "validation_capsule_0_norm_mean" in history[0]
    assert "validation_capsule_1_norm_mean" in history[0]
    assert "validation_correct_minus_incorrect_mean" in history[0]
    assert "validation_predicted_positive_fraction" in history[0]

    resumed = run_training_only(sequences, labels, config)
    assert resumed.epochs_completed == 1

    changed = NeuralTrainingConfig(
        **{**config.__dict__, "learning_rate": 0.002}
    )
    with pytest.raises(ValueError, match="contract changed"):
        run_training_only(sequences, labels, changed)


def test_neural_yaml_is_strict_and_has_no_external_test_input(tmp_path: Path) -> None:
    dataset = tmp_path / "train.csv"
    dataset.write_text("sequence,label\n" + "ACGT" * 7 + ",0\n" + "TGCA" * 7 + ",1\n")
    config = tmp_path / "neural.yaml"
    config.write_text(
        f"""project: {{name: smoke}}
data:
  train_csv: {dataset}
  sequence_column: sequence
  label_column: label
  sequence_length: 28
  maximum_samples: null
model:
  name: capsprom_basic
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
    routing_mode: uniform
    decoder_hidden: [8, 8]
training:
  random_seed: 42
  validation_fraction: 0.2
  batch_size: 2
  learning_rate: 0.001
  maximum_epochs: 1
  patience: 1
  reconstruction_weight: 0.0005
tracking: {{tracking_uri: ./mlruns, experiment_name: tests}}
outputs: {{checkpoint_path: ./best.pt, state_path: ./state.json}}
""",
        encoding="utf-8",
    )
    loaded = load_neural_experiment_config(config)
    assert loaded.training.model_name == "capsprom_basic"

    config.write_text(config.read_text() + "external_test_csv: forbidden.csv\n")
    with pytest.raises(ValueError, match="neural configuration keys"):
        load_neural_experiment_config(config)


def test_linear_warmup_uses_five_epoch_ramp_and_persists_state(tmp_path: Path) -> None:
    sequences = ["ACGT" * 7 for _ in range(10)] + ["TGCA" * 7 for _ in range(10)]
    labels = [0] * 10 + [1] * 10
    config = NeuralTrainingConfig(
        model_name="cnn_control",
        random_seed=42,
        validation_fraction=0.2,
        batch_size=8,
        learning_rate=0.001,
        maximum_epochs=5,
        patience=10,
        checkpoint_path=tmp_path / "best.pt",
        state_path=tmp_path / "state.json",
        capsule=CapsPromConfig(
            sequence_length=28,
            convolution_filters=8,
            primary_channels=2,
            primary_dim=4,
            output_capsules=2,
            output_dim=4,
            decoder_hidden=(8, 8),
            routing_iterations=1,
        ),
        reconstruction_weight=0.0,
        reconstruction_reduction="mean",
        contract_version=6,
        learning_rate_schedule="linear_warmup",
        warmup_initial_learning_rate=0.0001,
        warmup_epochs=5,
    )

    result = run_training_only(sequences, labels, config)

    assert result.epochs_completed == 5
    history = json.loads(config.state_path.read_text(encoding="utf-8"))["history"]
    assert [row["learning_rate"] for row in history] == pytest.approx(
        [0.0001, 0.000325, 0.00055, 0.000775, 0.001]
    )
    latest = torch.load(tmp_path / "best.latest.pt", map_location="cpu", weights_only=False)
    assert "scheduler_state" in latest


def test_manifest_defined_validation_is_part_of_contract(tmp_path: Path) -> None:
    config = NeuralTrainingConfig(
        model_name="cnn_control",
        random_seed=13,
        validation_fraction=0.2,
        batch_size=4,
        learning_rate=0.0001,
        maximum_epochs=1,
        patience=1,
        checkpoint_path=tmp_path / "best.pt",
        state_path=tmp_path / "state.json",
        capsule=CapsPromConfig(sequence_length=28, convolution_filters=8),
        reconstruction_weight=0.0,
        reconstruction_reduction="mean",
    )
    train_sequences = ["ACGT" * 7, "TGCA" * 7] * 4
    validation_sequences = ["ACGT" * 7, "TGCA" * 7]

    run_training_with_validation(
        train_sequences,
        [0, 1] * 4,
        validation_sequences,
        [0, 1],
        config,
        selection_manifest_sha256="abc123",
        validation_fold=0,
    )
    state = json.loads(config.state_path.read_text(encoding="utf-8"))

    assert state["contract"]["selection_manifest_sha256"] == "abc123"
    assert state["contract"]["validation_fold"] == 0
    with pytest.raises(ValueError, match="contract changed"):
        run_training_with_validation(
            train_sequences,
            [0, 1] * 4,
            validation_sequences,
            [0, 1],
            config,
            selection_manifest_sha256="abc123",
            validation_fold=1,
        )


def test_fixed_epoch_training_resume_is_exact(tmp_path: Path) -> None:
    sequences = ["ACGT" * 7, "TGCA" * 7] * 5
    labels = [0, 1] * 5

    def config_for(directory: Path) -> NeuralTrainingConfig:
        return NeuralTrainingConfig(
            model_name="capsprom_basic",
            random_seed=13,
            validation_fraction=0.2,
            batch_size=4,
            learning_rate=0.0001,
            maximum_epochs=3,
            patience=3,
            checkpoint_path=directory / "best.pt",
            state_path=directory / "state.json",
            capsule=CapsPromConfig(
                sequence_length=28,
                convolution_filters=8,
                primary_channels=2,
                primary_dim=4,
                output_capsules=2,
                output_dim=4,
                routing_iterations=1,
                decoder_mode="disabled",
            ),
            reconstruction_weight=0.0,
            reconstruction_reduction="mean",
        )

    continuous = config_for(tmp_path / "continuous")
    resumed = config_for(tmp_path / "resumed")
    provenance = {"rule": "fixture_lower_median", "fold_best_epochs": [3] * 5}
    run_fixed_epoch_training(
        sequences, labels, continuous, epochs=3, selection_provenance=provenance
    )
    with pytest.raises(SimulatedFixedEpochInterruption):
        run_fixed_epoch_training(
            sequences,
            labels,
            resumed,
            epochs=3,
            selection_provenance=provenance,
            interrupt_after_epoch=1,
        )
    run_fixed_epoch_training(
        sequences, labels, resumed, epochs=3, selection_provenance=provenance
    )

    continuous_state = json.loads(continuous.state_path.read_text(encoding="utf-8"))
    resumed_state = json.loads(resumed.state_path.read_text(encoding="utf-8"))
    assert continuous_state["status"] == resumed_state["status"] == "completed"
    assert continuous_state["epochs_completed"] == resumed_state["epochs_completed"] == 3
    assert continuous_state["history"] == resumed_state["history"]
    continuous_model = torch.load(
        continuous.checkpoint_path, map_location="cpu", weights_only=False
    )["model_state"]
    resumed_model = torch.load(
        resumed.checkpoint_path, map_location="cpu", weights_only=False
    )["model_state"]
    assert continuous_model.keys() == resumed_model.keys()
    assert all(
        torch.equal(continuous_model[name], resumed_model[name])
        for name in continuous_model
    )
