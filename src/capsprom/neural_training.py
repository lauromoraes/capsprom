"""Training-only neural runner primitives for Phase 4 model development."""

from __future__ import annotations

import os
import random
import tempfile
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    matthews_corrcoef,
)
from sklearn.model_selection import train_test_split
from torch import Tensor, nn
from torch.utils.data import DataLoader, TensorDataset

from .models.capsprom import (
    CapsProm,
    CapsPromConfig,
    binary_capsule_predictions,
    capsprom_loss,
)
from .models.sequence_cnn import SequenceCnnControl
from .state import write_json_atomic

NEURAL_RUNNER_VERSION = 7


class SimulatedFixedEpochInterruption(RuntimeError):
    """Test-only interruption after an atomic fixed-epoch checkpoint."""


@dataclass(frozen=True)
class NeuralTrainingConfig:
    """Explicit training-only contract; external test data is not accepted."""

    model_name: str
    random_seed: int
    validation_fraction: float
    batch_size: int
    learning_rate: float
    maximum_epochs: int
    patience: int
    checkpoint_path: Path
    state_path: Path
    capsule: CapsPromConfig = CapsPromConfig()
    reconstruction_weight: float = 0.0005
    reconstruction_reduction: str = "sum_per_sample"
    contract_version: int = NEURAL_RUNNER_VERSION
    learning_rate_schedule: str = "fixed"
    learning_rate_decay: float = 1.0
    warmup_initial_learning_rate: float | None = None
    warmup_epochs: int = 0
    device: str = "cpu"

    def __post_init__(self) -> None:
        allowed = {"cnn_control", "capsprom_original_1c", "capsprom_2c", "capsprom_basic"}
        if self.model_name not in allowed:
            raise ValueError(f"model_name must be one of {sorted(allowed)}")
        if not 0.0 < self.validation_fraction < 0.5:
            raise ValueError("validation_fraction must be between 0 and 0.5")
        if min(self.batch_size, self.maximum_epochs, self.patience) < 1:
            raise ValueError("batch_size, maximum_epochs, and patience must be positive")
        if self.learning_rate <= 0.0:
            raise ValueError("learning_rate must be positive")
        if self.reconstruction_reduction not in {"mean", "sum_per_sample"}:
            raise ValueError(
                "reconstruction_reduction must be 'mean' or 'sum_per_sample'"
            )
        if self.contract_version not in {2, 3, 4, 5, 6, NEURAL_RUNNER_VERSION}:
            raise ValueError("contract_version must identify runner version 2 through 7")
        if self.device not in {"cpu", "cuda", "auto"}:
            raise ValueError("device must be 'cpu', 'cuda', or 'auto'")
        if self.contract_version < 7 and self.device != "cpu":
            raise ValueError("accelerator selection requires runner contract version 7")
        if self.learning_rate_schedule not in {"fixed", "exponential", "linear_warmup"}:
            raise ValueError(
                "learning_rate_schedule must be 'fixed', 'exponential', or 'linear_warmup'"
            )
        if not 0.0 < self.learning_rate_decay <= 1.0:
            raise ValueError("learning_rate_decay must be in the interval (0, 1]")
        if self.learning_rate_schedule == "fixed" and self.learning_rate_decay != 1.0:
            raise ValueError("fixed learning rate requires learning_rate_decay=1.0")
        if self.learning_rate_schedule == "linear_warmup":
            if self.contract_version not in {6, NEURAL_RUNNER_VERSION}:
                raise ValueError("linear warm-up requires runner contract version 6 or 7")
            if self.warmup_initial_learning_rate is None:
                raise ValueError("linear warm-up requires warmup_initial_learning_rate")
            if not 0.0 < self.warmup_initial_learning_rate < self.learning_rate:
                raise ValueError(
                    "warmup_initial_learning_rate must be positive and below learning_rate"
                )
            if self.warmup_epochs < 2:
                raise ValueError("linear warm-up requires warmup_epochs >= 2")
            if self.learning_rate_decay != 1.0:
                raise ValueError("linear warm-up requires learning_rate_decay=1.0")
        elif self.warmup_initial_learning_rate is not None or self.warmup_epochs != 0:
            raise ValueError("warm-up fields require learning_rate_schedule='linear_warmup'")
        if self.capsule.decoder_mode == "disabled" and self.reconstruction_weight != 0.0:
            raise ValueError("disabled decoder requires reconstruction_weight=0.0")
        expected_capsules = 1 if self.model_name == "capsprom_original_1c" else 2
        if self.model_name.startswith("capsprom") and self.capsule.output_capsules != expected_capsules:
            raise ValueError(
                f"{self.model_name} requires capsule.output_capsules={expected_capsules}"
            )


@dataclass(frozen=True)
class NeuralTrainingResult:
    best_epoch: int
    best_validation_mcc: float
    epochs_completed: int
    checkpoint_path: Path


@dataclass(frozen=True)
class NeuralPredictionResult:
    """Raw, relative, and discrete outputs from a frozen CapsProm checkpoint."""

    capsule_lengths: np.ndarray
    positive_scores: np.ndarray
    predictions: np.ndarray
    first_convolution_activations: np.ndarray


def encode_one_hot(sequences: Sequence[str], sequence_length: int) -> Tensor:
    """Encode strict ACGT sequences in the canonical A,C,G,T channel order."""

    alphabet = {symbol: index for index, symbol in enumerate("ACGT")}
    encoded = torch.zeros((len(sequences), sequence_length, 4), dtype=torch.float32)
    for row, raw in enumerate(sequences):
        sequence = raw.strip().upper()
        if len(sequence) != sequence_length:
            raise ValueError(f"sequence {row} has length {len(sequence)}; expected {sequence_length}")
        try:
            indices = torch.tensor([alphabet[symbol] for symbol in sequence], dtype=torch.long)
        except KeyError as exc:
            raise ValueError(f"sequence {row} contains a non-ACGT symbol") from exc
        encoded[row] = torch.nn.functional.one_hot(indices, num_classes=4).float()
    return encoded


def build_neural_model(config: NeuralTrainingConfig) -> nn.Module:
    if config.model_name == "cnn_control":
        return SequenceCnnControl(
            sequence_length=config.capsule.sequence_length,
            input_channels=config.capsule.input_channels,
            filters=config.capsule.convolution_filters,
            kernel_size=config.capsule.convolution_kernel,
        )
    return CapsProm(config.capsule)


def run_training_only(
    sequences: Sequence[str], labels: Sequence[int], config: NeuralTrainingConfig
) -> NeuralTrainingResult:
    """Fit using a fixed inner split and never accept or inspect external test data."""

    if len(sequences) != len(labels) or not sequences:
        raise ValueError("sequences and labels must be non-empty and have equal length")
    contract = _serializable_contract(config)
    contract_hash = hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if config.state_path.exists():
        existing = json.loads(config.state_path.read_text(encoding="utf-8"))
        if existing.get("contract_sha256") != contract_hash:
            raise ValueError(
                "neural training contract changed after state creation; use new state and checkpoint paths"
            )
    _seed_everything(config.random_seed)
    features = encode_one_hot(sequences, config.capsule.sequence_length)
    targets = torch.as_tensor(labels, dtype=torch.long)
    positions = np.arange(len(labels))
    train_positions, validation_positions = train_test_split(
        positions,
        test_size=config.validation_fraction,
        random_state=config.random_seed,
        stratify=np.asarray(labels),
    )
    return _run_training_tensors(
        features[train_positions],
        targets[train_positions],
        features[validation_positions],
        targets[validation_positions],
        config,
        contract,
    )


def run_training_with_validation(
    train_sequences: Sequence[str],
    train_labels: Sequence[int],
    validation_sequences: Sequence[str],
    validation_labels: Sequence[int],
    config: NeuralTrainingConfig,
    selection_manifest_sha256: str,
    validation_fold: int,
) -> NeuralTrainingResult:
    """Fit one manifest-defined inner fold without accepting test data."""

    if not train_sequences or len(train_sequences) != len(train_labels):
        raise ValueError("training sequences and labels must be non-empty and aligned")
    if not validation_sequences or len(validation_sequences) != len(validation_labels):
        raise ValueError("validation sequences and labels must be non-empty and aligned")
    if not selection_manifest_sha256 or validation_fold < 0:
        raise ValueError("a manifest hash and non-negative validation fold are required")
    contract = _serializable_contract(config)
    contract["selection_manifest_sha256"] = selection_manifest_sha256
    contract["validation_fold"] = validation_fold
    _seed_everything(config.random_seed)
    return _run_training_tensors(
        encode_one_hot(train_sequences, config.capsule.sequence_length),
        torch.as_tensor(train_labels, dtype=torch.long),
        encode_one_hot(validation_sequences, config.capsule.sequence_length),
        torch.as_tensor(validation_labels, dtype=torch.long),
        config,
        contract,
    )


def run_fixed_epoch_training(
    sequences: Sequence[str],
    labels: Sequence[int],
    config: NeuralTrainingConfig,
    *,
    epochs: int,
    selection_provenance: dict[str, object],
    interrupt_after_epoch: int | None = None,
) -> Path:
    """Fit all supplied training rows for an already selected epoch count.

    This primitive deliberately accepts no evaluation data. Its atomic state is
    sufficient to resume after training but before downstream tracking.
    """

    if not sequences or len(sequences) != len(labels):
        raise ValueError("training sequences and labels must be non-empty and aligned")
    if epochs < 1 or epochs > config.maximum_epochs:
        raise ValueError("selected epochs must be within the configured maximum")
    if interrupt_after_epoch is not None and not 1 <= interrupt_after_epoch < epochs:
        raise ValueError("interrupt_after_epoch must precede the selected final epoch")
    contract = _serializable_contract(config)
    contract.update(
        {
            "stage": "final_fit",
            "selected_epochs": epochs,
            "selection_provenance": selection_provenance,
        }
    )
    contract_hash = hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if config.state_path.exists():
        state = json.loads(config.state_path.read_text(encoding="utf-8"))
        if state.get("contract_sha256") != contract_hash:
            raise ValueError("final-fit contract changed; use new state and checkpoint paths")
        if state.get("status") == "completed":
            if not config.checkpoint_path.is_file():
                raise ValueError("completed final-fit state has no checkpoint")
            return config.checkpoint_path

    _seed_everything(config.random_seed)
    device = _resolve_device(config.device)
    features = encode_one_hot(sequences, config.capsule.sequence_length)
    targets = torch.as_tensor(labels, dtype=torch.long)
    generator = torch.Generator().manual_seed(config.random_seed)
    loader = DataLoader(
        TensorDataset(features, targets),
        batch_size=config.batch_size,
        shuffle=True,
        generator=generator,
    )
    model = build_neural_model(config).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    scheduler = _build_learning_rate_scheduler(optimizer, config)
    history: list[dict[str, float | int]] = []
    latest_path = _latest_checkpoint_path(config.checkpoint_path)
    start_epoch = 1
    if config.state_path.exists():
        state = json.loads(config.state_path.read_text(encoding="utf-8"))
        history = list(state.get("history", []))
        if not latest_path.is_file():
            raise ValueError("final-fit state exists but latest checkpoint is missing")
        latest = torch.load(latest_path, map_location=device, weights_only=False)
        model.load_state_dict(latest["model_state"])
        optimizer.load_state_dict(latest["optimizer_state"])
        if scheduler is not None:
            scheduler.load_state_dict(latest["scheduler_state"])
        generator.set_state(latest["data_loader_generator_state"].cpu())
        torch.set_rng_state(latest["torch_rng_state"].cpu())
        start_epoch = int(latest["epoch"]) + 1

    for epoch in range(start_epoch, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch_features, batch_labels in loader:
            batch_features = batch_features.to(device)
            batch_labels = batch_labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = _loss(model, batch_features, batch_labels, config)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * len(batch_labels)
        history.append({"epoch": epoch, "training_loss": total_loss / len(targets)})
        if scheduler is not None:
            scheduler.step()
        _save_checkpoint_atomic(
            latest_path, model, optimizer, epoch, generator, scheduler=scheduler
        )
        write_json_atomic(
            config.state_path,
            {
                "status": "running",
                "contract": contract,
                "contract_sha256": contract_hash,
                "epochs_completed": epoch,
                "history": history,
            },
        )
        if epoch == interrupt_after_epoch:
            raise SimulatedFixedEpochInterruption(f"interrupted after epoch {epoch}")
    _save_checkpoint_atomic(config.checkpoint_path, model, optimizer, epochs, scheduler=scheduler)
    write_json_atomic(
        config.state_path,
        {
            "status": "completed",
            "contract": contract,
            "contract_sha256": contract_hash,
            "epochs_completed": epochs,
            "history": history,
        },
    )
    return config.checkpoint_path


def predict_capsprom_checkpoint(
    sequences: Sequence[str], config: NeuralTrainingConfig
) -> NeuralPredictionResult:
    """Run deterministic inference and retain first-layer activations."""

    if not sequences:
        raise ValueError("prediction requires at least one sequence")
    if not config.checkpoint_path.is_file():
        raise ValueError("prediction checkpoint is missing")
    device = _resolve_device(config.device)
    model = build_neural_model(config).to(device)
    if not isinstance(model, CapsProm):
        raise ValueError("capsule row artifacts require a CapsProm model")
    checkpoint = torch.load(config.checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state"])
    features = encode_one_hot(sequences, config.capsule.sequence_length).to(device)
    model.eval()
    with torch.no_grad():
        convolution = torch.relu(model.convolution(model._channels_first(features)))
        output = model(features)
        positive_scores, predictions = binary_capsule_predictions(output.scores)
    return NeuralPredictionResult(
        capsule_lengths=output.scores.detach().cpu().numpy(),
        positive_scores=positive_scores.detach().cpu().numpy(),
        predictions=predictions.detach().cpu().numpy(),
        first_convolution_activations=convolution.squeeze(2).detach().cpu().numpy(),
    )


def _run_training_tensors(
    train_features: Tensor,
    train_targets: Tensor,
    validation_features: Tensor,
    validation_targets: Tensor,
    config: NeuralTrainingConfig,
    contract: dict[str, object],
) -> NeuralTrainingResult:
    contract_hash = hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if config.state_path.exists():
        existing = json.loads(config.state_path.read_text(encoding="utf-8"))
        if existing.get("contract_sha256") != contract_hash:
            raise ValueError(
                "neural training contract changed after state creation; use new state and checkpoint paths"
            )
    device = _resolve_device(config.device)
    generator = torch.Generator().manual_seed(config.random_seed)
    train_loader = DataLoader(
        TensorDataset(train_features, train_targets),
        batch_size=config.batch_size,
        shuffle=True,
        generator=generator,
    )
    validation = (validation_features.to(device), validation_targets.to(device))
    model = build_neural_model(config).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    scheduler = _build_learning_rate_scheduler(optimizer, config)
    best_mcc = -1.0
    best_validation_loss = float("inf")
    best_epoch = 0
    stale_epochs = 0
    history: list[dict[str, float | int]] = []
    start_epoch = 1
    latest_path = _latest_checkpoint_path(config.checkpoint_path)
    if config.state_path.exists():
        state = json.loads(config.state_path.read_text(encoding="utf-8"))
        history = list(state.get("history", []))
        best_mcc = float(state.get("best_validation_mcc", -1.0))
        best_validation_loss = float(state.get("best_validation_loss", float("inf")))
        best_epoch = int(state.get("best_epoch", 0))
        stale_epochs = int(state.get("stale_epochs", 0))
        if not latest_path.is_file():
            raise ValueError("neural state exists but the latest optimizer checkpoint is missing")
        latest = torch.load(latest_path, map_location=device, weights_only=False)
        model.load_state_dict(latest["model_state"])
        optimizer.load_state_dict(latest["optimizer_state"])
        if scheduler is not None:
            scheduler.load_state_dict(latest["scheduler_state"])
        generator.set_state(latest["data_loader_generator_state"].cpu())
        torch.set_rng_state(latest["torch_rng_state"].cpu())
        start_epoch = int(latest["epoch"]) + 1

    for epoch in range(start_epoch, config.maximum_epochs + 1):
        epoch_learning_rate = float(optimizer.param_groups[0]["lr"])
        model.train()
        training_loss = 0.0
        for batch_features, batch_labels in train_loader:
            batch_features = batch_features.to(device)
            batch_labels = batch_labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = _loss(model, batch_features, batch_labels, config)
            loss.backward()
            optimizer.step()
            training_loss += float(loss.detach()) * len(batch_labels)
        validation_metrics = _validate(model, validation, config)
        validation_mcc = validation_metrics["validation_mcc"]
        history.append(
            {
                "epoch": epoch,
                "learning_rate": epoch_learning_rate,
                "training_loss": training_loss / len(train_targets),
                **validation_metrics,
            }
        )
        validation_loss = float(validation_metrics["validation_loss"])
        improved = validation_mcc > best_mcc or (
            validation_mcc == best_mcc and validation_loss < best_validation_loss
        )
        if improved:
            best_mcc = validation_mcc
            best_validation_loss = validation_loss
            best_epoch = epoch
            stale_epochs = 0
            _save_checkpoint_atomic(config.checkpoint_path, model, optimizer, epoch, scheduler=scheduler)
        else:
            stale_epochs += 1
        if scheduler is not None:
            scheduler.step()
        _save_checkpoint_atomic(
            latest_path, model, optimizer, epoch, generator, scheduler=scheduler
        )
        write_json_atomic(
            config.state_path,
            {
                "contract": contract,
                "contract_sha256": contract_hash,
                "best_epoch": best_epoch,
                "best_validation_mcc": best_mcc,
                "best_validation_loss": best_validation_loss,
                "epochs_completed": epoch,
                "stale_epochs": stale_epochs,
                "history": history,
            },
        )
        if stale_epochs >= config.patience:
            break
    return NeuralTrainingResult(best_epoch, best_mcc, len(history), config.checkpoint_path)


def _build_learning_rate_scheduler(
    optimizer: torch.optim.Optimizer, config: NeuralTrainingConfig
) -> torch.optim.lr_scheduler.LRScheduler | None:
    if config.learning_rate_schedule == "exponential":
        return torch.optim.lr_scheduler.ExponentialLR(
            optimizer, gamma=config.learning_rate_decay
        )
    if config.learning_rate_schedule == "linear_warmup":
        assert config.warmup_initial_learning_rate is not None
        return torch.optim.lr_scheduler.LinearLR(
            optimizer,
            start_factor=config.warmup_initial_learning_rate / config.learning_rate,
            end_factor=1.0,
            total_iters=config.warmup_epochs - 1,
        )
    return None


def _loss(model: nn.Module, features: Tensor, labels: Tensor, config: NeuralTrainingConfig) -> Tensor:
    if isinstance(model, CapsProm):
        return capsprom_loss(
            model(features, labels=labels),
            labels,
            features,
            config.reconstruction_weight,
            config.reconstruction_reduction,
        )
    logits = model(features)
    return torch.nn.functional.binary_cross_entropy_with_logits(logits, labels.float())


def _validate(
    model: nn.Module, validation: tuple[Tensor, Tensor], config: NeuralTrainingConfig
) -> dict[str, float | int]:
    features, labels = validation
    model.eval()
    with torch.no_grad():
        loss = _loss(model, features, labels, config)
        if isinstance(model, CapsProm):
            scores = model(features).scores
            predictions = (scores[:, 0] >= 0.5).long() if scores.shape[1] == 1 else scores.argmax(1)
        else:
            predictions = (torch.sigmoid(model(features)) >= 0.5).long()
    true = labels.detach().cpu().numpy()
    predicted = predictions.detach().cpu().numpy()
    tn, fp, fn, tp = confusion_matrix(true, predicted, labels=[0, 1]).ravel()
    metrics: dict[str, float | int] = {
        "validation_loss": float(loss),
        "validation_mcc": float(matthews_corrcoef(true, predicted)),
        "validation_accuracy": float(accuracy_score(true, predicted)),
        "validation_balanced_accuracy": float(balanced_accuracy_score(true, predicted)),
        "validation_true_negative": int(tn),
        "validation_false_positive": int(fp),
        "validation_false_negative": int(fn),
        "validation_true_positive": int(tp),
    }
    if isinstance(model, CapsProm) and scores.shape[1] == 2:
        metrics.update(_capsule_score_metrics(scores, labels, predictions))
    return metrics


def _capsule_score_metrics(
    scores: Tensor, labels: Tensor, predictions: Tensor
) -> dict[str, float]:
    rows = torch.arange(len(labels), device=scores.device)
    correct = scores[rows, labels]
    incorrect = scores[rows, 1 - labels]
    metrics = {
        "validation_capsule_0_norm_mean": float(scores[:, 0].mean()),
        "validation_capsule_1_norm_mean": float(scores[:, 1].mean()),
        "validation_correct_capsule_norm_mean": float(correct.mean()),
        "validation_incorrect_capsule_norm_mean": float(incorrect.mean()),
        "validation_correct_minus_incorrect_mean": float((correct - incorrect).mean()),
        "validation_predicted_positive_fraction": float(predictions.float().mean()),
    }
    for true_class in (0, 1):
        subset = labels == true_class
        metrics[f"validation_true_{true_class}_capsule_0_norm_mean"] = float(
            scores[subset, 0].mean()
        )
        metrics[f"validation_true_{true_class}_capsule_1_norm_mean"] = float(
            scores[subset, 1].mean()
        )
    return metrics


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)


def _resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is not available")
    return torch.device(requested)


def _save_checkpoint_atomic(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    generator: torch.Generator | None = None,
    scheduler: torch.optim.lr_scheduler.LRScheduler | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        payload = {
            "epoch": epoch,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
        }
        if generator is not None:
            payload["data_loader_generator_state"] = generator.get_state()
            payload["torch_rng_state"] = torch.get_rng_state()
        if scheduler is not None:
            payload["scheduler_state"] = scheduler.state_dict()
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _serializable_contract(config: NeuralTrainingConfig) -> dict[str, object]:
    payload = asdict(config)
    if config.contract_version == 2:
        payload.pop("contract_version")
        payload.pop("reconstruction_reduction")
        capsule = payload["capsule"]
        if isinstance(capsule, dict):
            capsule.pop("decoder_mode")
            if capsule.get("routing_gradient_mode") == "full":
                capsule.pop("routing_gradient_mode")
        payload["neural_runner_version"] = 2
        payload.pop("learning_rate_schedule")
        payload.pop("learning_rate_decay")
        payload.pop("warmup_initial_learning_rate")
        payload.pop("warmup_epochs")
        payload.pop("device")
    elif config.contract_version == 3:
        payload["neural_runner_version"] = 3
        payload.pop("learning_rate_schedule")
        payload.pop("learning_rate_decay")
        payload.pop("warmup_initial_learning_rate")
        payload.pop("warmup_epochs")
        payload.pop("device")
    elif config.contract_version == 4:
        payload["neural_runner_version"] = 4
        payload.pop("warmup_initial_learning_rate")
        payload.pop("warmup_epochs")
        payload.pop("device")
    elif config.contract_version == 5:
        payload["neural_runner_version"] = 5
        payload.pop("warmup_initial_learning_rate")
        payload.pop("warmup_epochs")
        payload.pop("device")
    elif config.contract_version == 6:
        payload["neural_runner_version"] = 6
        payload.pop("device")
    else:
        payload["neural_runner_version"] = NEURAL_RUNNER_VERSION
    payload["checkpoint_path"] = config.checkpoint_path.as_posix()
    payload["state_path"] = config.state_path.as_posix()
    return payload


def _latest_checkpoint_path(best_path: Path) -> Path:
    return best_path.with_name(f"{best_path.stem}.latest{best_path.suffix}")
