"""PyTorch reproduction of the original one-hot CapsProm architecture.

The module reproduces the model topology without reproducing the original
test-set-based checkpoint selection. Training orchestration is intentionally
kept outside this module so it can enforce the canonical evaluation protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import torch
from torch import Tensor, nn
from torch.nn import functional as F


def squash(vectors: Tensor, dim: int = -1, epsilon: float = 1e-8) -> Tensor:
    """Capsule squash nonlinearity with a finite zero-vector result."""

    squared_norm = vectors.square().sum(dim=dim, keepdim=True)
    scale = squared_norm / (1.0 + squared_norm)
    return scale * vectors / torch.sqrt(squared_norm + epsilon)


class DynamicRoutingCapsules(nn.Module):
    """Fully connected capsule layer using routing-by-agreement."""

    def __init__(
        self,
        input_capsules: int,
        input_dim: int,
        output_capsules: int,
        output_dim: int,
        routing_iterations: int,
        routing_mode: str = "dynamic",
        routing_gradient_mode: str = "full",
    ) -> None:
        super().__init__()
        if min(input_capsules, input_dim, output_capsules, output_dim, routing_iterations) < 1:
            raise ValueError("capsule dimensions and routing iterations must be positive")
        self.output_capsules = output_capsules
        self.routing_iterations = routing_iterations
        if routing_mode not in {"dynamic", "uniform"}:
            raise ValueError("routing_mode must be 'dynamic' or 'uniform'")
        self.routing_mode = routing_mode
        if routing_gradient_mode not in {"full", "final_iteration"}:
            raise ValueError("routing_gradient_mode must be 'full' or 'final_iteration'")
        self.routing_gradient_mode = routing_gradient_mode
        self.weight = nn.Parameter(
            torch.empty(input_capsules, output_capsules, input_dim, output_dim)
        )
        nn.init.xavier_uniform_(self.weight)

    def forward(self, inputs: Tensor) -> Tensor:
        if inputs.ndim != 3:
            raise ValueError("capsule inputs must have shape [batch, capsules, dimensions]")
        votes = torch.einsum("bid,ijdo->bijo", inputs, self.weight)
        routing_votes = (
            votes.detach() if self.routing_gradient_mode == "final_iteration" else votes
        )
        logits = inputs.new_zeros(inputs.shape[0], inputs.shape[1], self.output_capsules)
        iterations = 1 if self.routing_mode == "uniform" else self.routing_iterations
        for iteration in range(iterations):
            coupling = logits.softmax(dim=2)
            active_votes = votes if iteration + 1 == iterations else routing_votes
            outputs = squash((coupling.unsqueeze(-1) * active_votes).sum(dim=1))
            if iteration + 1 < iterations:
                logits = logits + (routing_votes * outputs.unsqueeze(1)).sum(dim=-1)
        return outputs


@dataclass(frozen=True)
class CapsPromConfig:
    sequence_length: int = 81
    input_channels: int = 4
    convolution_filters: int = 256
    convolution_kernel: int = 9
    primary_channels: int = 32
    primary_dim: int = 8
    primary_kernel: int = 9
    primary_stride: int = 2
    output_capsules: int = 2
    output_dim: int = 16
    routing_iterations: int = 3
    routing_mode: str = "dynamic"
    routing_gradient_mode: str = "final_iteration"
    decoder_mode: str = "masked_flatten"
    decoder_hidden: tuple[int, int] = (512, 1024)

    def __post_init__(self) -> None:
        positive = (
            self.sequence_length,
            self.input_channels,
            self.convolution_filters,
            self.convolution_kernel,
            self.primary_channels,
            self.primary_dim,
            self.primary_kernel,
            self.primary_stride,
            self.output_capsules,
            self.output_dim,
            self.routing_iterations,
        )
        if min(positive) < 1:
            raise ValueError("all CapsProm dimensions must be positive")
        if self.routing_mode not in {"dynamic", "uniform"}:
            raise ValueError("routing_mode must be 'dynamic' or 'uniform'")
        if self.routing_gradient_mode not in {"full", "final_iteration"}:
            raise ValueError("routing_gradient_mode must be 'full' or 'final_iteration'")
        if self.decoder_mode not in {"selected_vector", "masked_flatten", "disabled"}:
            raise ValueError(
                "decoder_mode must be 'selected_vector', 'masked_flatten', or 'disabled'"
            )
        if self.primary_positions < 1:
            raise ValueError("sequence_length is too short for the configured convolutions")

    @property
    def primary_positions(self) -> int:
        after_first = self.sequence_length - self.convolution_kernel + 1
        return (after_first - self.primary_kernel) // self.primary_stride + 1

    @property
    def primary_capsules(self) -> int:
        return self.primary_channels * self.primary_positions


class CapsPromOutput(NamedTuple):
    scores: Tensor
    reconstruction: Tensor | None
    capsules: Tensor


def relative_capsule_scores(scores: Tensor) -> Tensor:
    """Normalize non-negative capsule lengths without claiming calibration."""

    if scores.ndim != 2 or scores.shape[1] < 2:
        raise ValueError("relative capsule scores require [batch, at least two classes]")
    if not torch.isfinite(scores).all() or torch.any(scores < 0.0):
        raise ValueError("capsule scores must be finite and non-negative")
    totals = scores.sum(dim=1, keepdim=True)
    uniform = torch.full_like(scores, 1.0 / scores.shape[1])
    return torch.where(totals > 0.0, scores / totals.clamp_min(torch.finfo(scores.dtype).tiny), uniform)


def binary_capsule_predictions(scores: Tensor) -> tuple[Tensor, Tensor]:
    """Return the relative positive-class score and argmax prediction."""

    if scores.ndim != 2 or scores.shape[1] != 2:
        raise ValueError("binary capsule prediction requires exactly two class scores")
    relative = relative_capsule_scores(scores)
    return relative[:, 1], scores.argmax(dim=1)


class CapsProm(nn.Module):
    """One-hot CapsProm with convolutional primary capsules and a decoder."""

    def __init__(self, config: CapsPromConfig | None = None) -> None:
        super().__init__()
        self.config = config or CapsPromConfig()
        cfg = self.config
        self.convolution = nn.Conv2d(
            1,
            cfg.convolution_filters,
            kernel_size=(cfg.input_channels, cfg.convolution_kernel),
        )
        self.primary_convolution = nn.Conv2d(
            cfg.convolution_filters,
            cfg.primary_channels * cfg.primary_dim,
            kernel_size=(1, cfg.primary_kernel),
            stride=(1, cfg.primary_stride),
        )
        self.digit_capsules = DynamicRoutingCapsules(
            input_capsules=cfg.primary_capsules,
            input_dim=cfg.primary_dim,
            output_capsules=cfg.output_capsules,
            output_dim=cfg.output_dim,
            routing_iterations=cfg.routing_iterations,
            routing_mode=cfg.routing_mode,
            routing_gradient_mode=cfg.routing_gradient_mode,
        )
        self.decoder: nn.Sequential | None = None
        if cfg.decoder_mode != "disabled":
            decoder_input = (
                cfg.output_dim * cfg.output_capsules
                if cfg.decoder_mode == "masked_flatten"
                else cfg.output_dim
            )
            reconstruction_size = cfg.sequence_length * cfg.input_channels
            self.decoder = nn.Sequential(
                nn.Linear(decoder_input, cfg.decoder_hidden[0]),
                nn.ReLU(),
                nn.Linear(cfg.decoder_hidden[0], cfg.decoder_hidden[1]),
                nn.ReLU(),
                nn.Linear(cfg.decoder_hidden[1], reconstruction_size),
                nn.Sigmoid(),
            )

    def forward(self, one_hot: Tensor, labels: Tensor | None = None) -> CapsPromOutput:
        x = self._channels_first(one_hot)
        features = F.relu(self.convolution(x))
        primary = self.primary_convolution(features)
        batch = primary.shape[0]
        primary = primary.reshape(
            batch,
            self.config.primary_channels,
            self.config.primary_dim,
            self.config.primary_positions,
        )
        primary = primary.permute(0, 1, 3, 2).reshape(
            batch, self.config.primary_capsules, self.config.primary_dim
        )
        primary = squash(primary)
        capsules = self.digit_capsules(primary)
        scores = torch.linalg.vector_norm(capsules, dim=-1)
        reconstruction = None
        if self.decoder is not None:
            decoder_capsule = self._mask_decoder_capsules(capsules, scores, labels)
            reconstruction = self.decoder(decoder_capsule).reshape(
                batch, self.config.sequence_length, self.config.input_channels
            )
        return CapsPromOutput(scores=scores, reconstruction=reconstruction, capsules=capsules)

    def _mask_decoder_capsules(
        self, capsules: Tensor, scores: Tensor, labels: Tensor | None
    ) -> Tensor:
        if self.config.output_capsules == 1:
            return capsules[:, 0]
        if labels is None:
            selected = scores.argmax(dim=1)
        else:
            selected = labels.to(device=capsules.device, dtype=torch.long).reshape(-1)
            if torch.any((selected < 0) | (selected >= self.config.output_capsules)):
                raise ValueError("decoder labels are outside the output-capsule range")
        rows = torch.arange(capsules.shape[0], device=capsules.device)
        if self.config.decoder_mode == "selected_vector":
            return capsules[rows, selected]
        mask = F.one_hot(selected, num_classes=self.config.output_capsules).unsqueeze(-1)
        return (capsules * mask).reshape(capsules.shape[0], -1)

    def _channels_first(self, one_hot: Tensor) -> Tensor:
        cfg = self.config
        if one_hot.ndim != 3:
            raise ValueError("one-hot input must have shape [batch, length, channels]")
        if one_hot.shape[1:] != (cfg.sequence_length, cfg.input_channels):
            raise ValueError(
                "one-hot input shape mismatch: expected "
                f"[batch, {cfg.sequence_length}, {cfg.input_channels}]"
            )
        return one_hot.transpose(1, 2).unsqueeze(1)


def margin_loss(
    labels: Tensor,
    scores: Tensor,
    positive_margin: float = 0.9,
    negative_margin: float = 0.1,
    negative_weight: float = 0.5,
) -> Tensor:
    """Binary form of the margin loss used by the original implementation."""

    if scores.ndim != 2:
        raise ValueError("capsule scores must have shape [batch, classes]")
    if scores.shape[1] == 1:
        targets = labels.to(device=scores.device, dtype=scores.dtype).reshape_as(scores)
    else:
        targets = F.one_hot(
            labels.to(device=scores.device, dtype=torch.long).reshape(-1),
            num_classes=scores.shape[1],
        ).to(dtype=scores.dtype)
    positive = targets * F.relu(positive_margin - scores).square()
    negative = negative_weight * (1.0 - targets) * F.relu(scores - negative_margin).square()
    return (positive + negative).sum(dim=1).mean()


def capsprom_loss(
    output: CapsPromOutput,
    labels: Tensor,
    one_hot: Tensor,
    reconstruction_weight: float = 0.0005,
    reconstruction_reduction: str = "sum_per_sample",
) -> Tensor:
    """Original margin-plus-reconstruction objective."""

    if reconstruction_weight < 0:
        raise ValueError("reconstruction_weight must be non-negative")
    classification_loss = margin_loss(labels, output.scores)
    if reconstruction_weight == 0.0:
        return classification_loss
    if output.reconstruction is None:
        raise ValueError("reconstruction_weight must be zero when the decoder is disabled")
    if reconstruction_reduction == "mean":
        reconstruction_loss = F.mse_loss(output.reconstruction, one_hot)
    elif reconstruction_reduction == "sum_per_sample":
        reconstruction_loss = (
            (output.reconstruction - one_hot).square().flatten(start_dim=1).sum(dim=1).mean()
        )
    else:
        raise ValueError("reconstruction_reduction must be 'mean' or 'sum_per_sample'")
    return classification_loss + reconstruction_weight * reconstruction_loss


@dataclass(frozen=True)
class LegacyCapsProm1CConfig(CapsPromConfig):
    """Frozen defaults for reproducing the historical one-capsule implementation."""

    output_capsules: int = 1
    routing_gradient_mode: str = "full"
    decoder_mode: str = "selected_vector"
