"""Auditable sequence-pattern artifacts for model explainability."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .state import write_json_atomic

DNA_ALPHABET = "ACGT"


@dataclass(frozen=True)
class ActivationWindow:
    sequence_id: str
    sequence: str
    label: int
    filter_index: int
    start: int
    activation: float
    strand: str = "+"

    @property
    def end(self) -> int:
        return self.start + len(self.sequence)


def select_max_activation_windows(
    sequence_ids: Sequence[str],
    sequences: Sequence[str],
    labels: Sequence[int],
    activations: np.ndarray,
    *,
    kernel_size: int,
    filter_index: int,
    eligible_label: int | None = 1,
    maximum_windows: int | None = None,
) -> list[ActivationWindow]:
    """Map valid-convolution maxima back to one original-DNA window per row."""

    if activations.ndim != 3:
        raise ValueError("activations must have shape [sequences, filters, positions]")
    if not (len(sequence_ids) == len(sequences) == len(labels) == activations.shape[0]):
        raise ValueError("sequence identifiers, sequences, labels, and activations must align")
    if kernel_size < 1 or not 0 <= filter_index < activations.shape[1]:
        raise ValueError("kernel_size and filter_index must identify a valid filter")
    candidates = []
    for row, (sequence_id, sequence, label) in enumerate(
        zip(sequence_ids, sequences, labels, strict=True)
    ):
        if eligible_label is not None and label != eligible_label:
            continue
        values = activations[row, filter_index]
        start = int(np.argmax(values))
        if start + kernel_size > len(sequence):
            raise ValueError("activation position cannot map inside the original sequence")
        candidates.append(
            ActivationWindow(
                sequence_id=sequence_id,
                sequence=sequence[start : start + kernel_size],
                label=int(label),
                filter_index=filter_index,
                start=start,
                activation=float(values[start]),
            )
        )
    candidates.sort(key=lambda item: (-item.activation, item.sequence_id, item.start))
    if maximum_windows is not None:
        if maximum_windows < 1:
            raise ValueError("maximum_windows must be positive when supplied")
        candidates = candidates[:maximum_windows]
    return candidates


def write_activation_logo_artifacts(
    output_dir: Path,
    windows: Sequence[ActivationWindow],
    *,
    dataset_id: str,
    model_name: str,
    config_sha256: str,
    checkpoint_sha256: str,
    seed: int,
    fold: int,
    source_partition: str,
    pseudocount: float = 0.5,
) -> Path:
    """Persist selected windows, matrices, an SVG logo, and hashed provenance."""

    if not windows:
        raise ValueError("at least one activation window is required")
    width = len(windows[0].sequence)
    filter_index = windows[0].filter_index
    if width < 1 or any(len(item.sequence) != width for item in windows):
        raise ValueError("activation windows must have one positive common width")
    if any(set(item.sequence) - set(DNA_ALPHABET) for item in windows):
        raise ValueError("activation windows must contain strict ACGT DNA")
    if any(item.filter_index != filter_index for item in windows):
        raise ValueError("one artifact group must contain exactly one filter")
    if source_partition not in {"fold_train", "fold_validation", "full_train", "external_test"}:
        raise ValueError("source_partition is not recognized")
    if pseudocount < 0:
        raise ValueError("pseudocount must be non-negative")

    output_dir.mkdir(parents=True, exist_ok=True)
    selected_path = output_dir / "selected_windows.csv"
    ordered = sorted(windows, key=lambda item: (-item.activation, item.sequence_id, item.start))
    with selected_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "selection_rank", "sequence_id", "label", "filter_index", "start",
                "end", "strand", "activation", "window",
            ],
        )
        writer.writeheader()
        for rank, item in enumerate(ordered, start=1):
            writer.writerow(
                {
                    "selection_rank": rank,
                    "sequence_id": item.sequence_id,
                    "label": item.label,
                    "filter_index": item.filter_index,
                    "start": item.start,
                    "end": item.end,
                    "strand": item.strand,
                    "activation": f"{item.activation:.17g}",
                    "window": item.sequence,
                }
            )
    counts = np.zeros((width, 4), dtype=np.int64)
    for item in ordered:
        for position, nucleotide in enumerate(item.sequence):
            counts[position, DNA_ALPHABET.index(nucleotide)] += 1
    probabilities = (counts + pseudocount) / (len(ordered) + 4 * pseudocount)
    information = 2.0 + np.sum(
        np.where(probabilities > 0, probabilities * np.log2(probabilities), 0.0), axis=1
    )
    heights = probabilities * information[:, None]
    matrix_path = output_dir / "motif_matrices.json"
    write_json_atomic(
        matrix_path,
        {
            "alphabet": list(DNA_ALPHABET),
            "window_length": width,
            "sequence_count": len(ordered),
            "pseudocount": pseudocount,
            "pfm": counts.tolist(),
            "ppm": probabilities.tolist(),
            "information_content_bits": information.tolist(),
            "logo_heights_bits": heights.tolist(),
        },
    )
    logo_path = output_dir / "sequence_logo.svg"
    logo_path.write_text(_sequence_logo_svg(heights), encoding="utf-8")
    artifacts = {
        path.name: _sha256(path) for path in (selected_path, matrix_path, logo_path)
    }
    manifest_path = output_dir / "manifest.json"
    write_json_atomic(
        manifest_path,
        {
            "schema_version": 1,
            "analysis": "first_convolution_activation_windows",
            "evidence_level": "learned_pattern_not_biological_validation",
            "dataset_id": dataset_id,
            "model_name": model_name,
            "config_sha256": config_sha256,
            "checkpoint_sha256": checkpoint_sha256,
            "seed": seed,
            "fold": fold,
            "source_partition": source_partition,
            "filter_index": filter_index,
            "selection": {
                "criterion": "preselected maximum-activation window per sequence",
                "sequence_count": len(ordered),
            },
            "coordinate_system": "zero_based_half_open_original_sequence",
            "strand_policy": "recorded_per_window_no_implicit_canonicalization",
            "artifacts": artifacts,
        },
    )
    return manifest_path


def log_explainability_artifacts(client: Any, run_id: str, manifest_path: Path) -> None:
    """Attach a complete explainability directory to an existing MLflow child run."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    client.set_tag(run_id, "capsprom.explainability.schema_version", str(manifest["schema_version"]))
    client.set_tag(run_id, "capsprom.explainability.fold", str(manifest["fold"]))
    client.set_tag(run_id, "capsprom.explainability.checkpoint_sha256", manifest["checkpoint_sha256"])
    client.log_artifacts(run_id, str(manifest_path.parent), "explainability")


def _sequence_logo_svg(heights: np.ndarray) -> str:
    colors = {"A": "#2ca02c", "C": "#1f77b4", "G": "#ff7f0e", "T": "#d62728"}
    column_width = 42
    plot_height = 200
    left = 42
    width = left + column_width * len(heights) + 12
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="250" viewBox="0 0 {width} 250">',
        '<title>Sequence logo from selected convolution activation windows</title>',
        '<desc>Letter heights show per-position information content in bits.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<line x1="{left}" y1="10" x2="{left}" y2="{10 + plot_height}" stroke="black"/>',
        f'<line x1="{left}" y1="{10 + plot_height}" x2="{width - 8}" y2="{10 + plot_height}" stroke="black"/>',
        '<text x="12" y="115" transform="rotate(-90 12 115)" font-size="12">information (bits)</text>',
    ]
    for position, row in enumerate(heights):
        y = 10 + plot_height
        x = left + position * column_width + 6
        for index in np.argsort(row):
            height = float(row[index]) / 2.0 * plot_height
            if height <= 0.05:
                continue
            y -= height
            symbol = DNA_ALPHABET[int(index)]
            font_size = max(1.0, height)
            body.append(
                f'<text x="{x}" y="{y + height}" font-family="sans-serif" '
                f'font-weight="bold" font-size="{font_size:.4f}" fill="{colors[symbol]}" '
                f'textLength="30" lengthAdjust="spacingAndGlyphs">{escape(symbol)}</text>'
            )
        body.append(f'<text x="{x + 10}" y="230" font-size="10">{position + 1}</text>')
    body.append("</svg>\n")
    return "\n".join(body)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
