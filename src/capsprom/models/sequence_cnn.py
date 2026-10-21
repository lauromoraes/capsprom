"""Parameter-transparent CNN control for capsule ablations."""

from __future__ import annotations

import torch
from torch import Tensor, nn
from torch.nn import functional as F


class SequenceCnnControl(nn.Module):
    """Use the CapsProm convolutional stem without capsule transformations."""

    def __init__(
        self,
        sequence_length: int = 81,
        input_channels: int = 4,
        filters: int = 256,
        kernel_size: int = 9,
    ) -> None:
        super().__init__()
        if sequence_length < kernel_size:
            raise ValueError("sequence_length must be at least kernel_size")
        self.sequence_length = sequence_length
        self.input_channels = input_channels
        self.convolution = nn.Conv1d(input_channels, filters, kernel_size)
        self.classifier = nn.Linear(filters, 1)

    def forward(self, one_hot: Tensor) -> Tensor:
        expected = (self.sequence_length, self.input_channels)
        if one_hot.ndim != 3 or one_hot.shape[1:] != expected:
            raise ValueError(f"one-hot input must have shape [batch, {expected[0]}, {expected[1]}]")
        features = F.relu(self.convolution(one_hot.transpose(1, 2)))
        pooled = torch.amax(features, dim=-1)
        return self.classifier(pooled).squeeze(-1)
