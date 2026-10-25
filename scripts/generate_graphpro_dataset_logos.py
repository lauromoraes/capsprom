"""Generate comparable pre/post-treatment GraphPro dataset sequence logos."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MatplotlibPath
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D
import numpy as np
import yaml

from capsprom.data.loading import sha256_file
from capsprom.data.sequence_logo import NUCLEOTIDES, sequence_logo_matrices
from capsprom.data.sequences import read_fasta
from capsprom.state import write_json_atomic


COLORS = {"A": "#2ca02c", "C": "#1f77b4", "G": "#ff7f0e", "T": "#d62728"}
FONT = FontProperties(family="DejaVu Sans", weight="bold")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/graphpro_dataset_logo_audit_v1.yaml"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_dir}")
    _verify_inputs(config["inputs"])
    alignment = config["alignment"]

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.", dir=args.output_dir.parent
    ) as temporary:
        staging = Path(temporary) / args.output_dir.name
        (staging / "figures").mkdir(parents=True)
        (staging / "matrices").mkdir()
        results = []
        for dataset in config["datasets"]:
            for class_name in ("positive", "negative"):
                before_path, after_path = _paths(dataset, class_name, config["inputs"])
                before_sequences = [record.sequence for record in read_fasta(before_path)]
                after_sequences = [record.sequence for record in read_fasta(after_path)]
                before = sequence_logo_matrices(before_sequences)
                after = sequence_logo_matrices(after_sequences)
                if before.sequence_length != int(alignment["sequence_length"]):
                    raise ValueError(f"unexpected length in {before_path}")
                stem = f"{dataset['dataset'].lower()}_{class_name}"
                matrix_paths = {}
                for version, matrices in (("before", before), ("after", after)):
                    frequency_path = staging / "matrices" / f"{stem}_{version}_frequency.csv"
                    information_path = staging / "matrices" / f"{stem}_{version}_information.csv"
                    _write_matrix(frequency_path, matrices.frequencies, int(alignment["coordinate_start"]))
                    _write_matrix(
                        information_path,
                        matrices.information_heights,
                        int(alignment["coordinate_start"]),
                    )
                    matrix_paths[f"{version}_frequency"] = frequency_path
                    matrix_paths[f"{version}_information"] = information_path
                figure_path = staging / "figures" / f"{stem}_before_after.png"
                _plot_comparison(
                    figure_path,
                    before.information_heights,
                    after.information_heights,
                    dataset=dataset,
                    class_name=class_name,
                    before_count=before.sequence_count,
                    after_count=after.sequence_count,
                    coordinate_start=int(alignment["coordinate_start"]),
                )
                results.append(
                    {
                        **dataset,
                        "class": class_name,
                        "before_path": str(before_path),
                        "after_path": str(after_path),
                        "before_sha256": sha256_file(before_path),
                        "after_sha256": sha256_file(after_path),
                        "before_count": before.sequence_count,
                        "after_count": after.sequence_count,
                        "changed": before_sequences != after_sequences,
                        "before_gc_fraction": _gc_fraction(before.frequencies),
                        "after_gc_fraction": _gc_fraction(after.frequencies),
                        "before_mean_information_bits": float(
                            before.information_heights.sum(axis=1).mean()
                        ),
                        "after_mean_information_bits": float(
                            after.information_heights.sum(axis=1).mean()
                        ),
                        "figure": str(figure_path.relative_to(staging)),
                        "figure_sha256": sha256_file(figure_path),
                        "matrices": {
                            name: {
                                "path": str(path.relative_to(staging)),
                                "sha256": sha256_file(path),
                            }
                            for name, path in matrix_paths.items()
                        },
                    }
                )
        write_json_atomic(
            staging / "logo_audit_summary.json",
            {
                "schema_version": 1,
                "report_identity": config["report"]["name"],
                "config": str(args.config),
                "config_sha256": sha256_file(args.config),
                "alignment": alignment,
                "analysis_is_model_motif_extraction": False,
                "datasets": results,
            },
        )
        os.replace(staging, args.output_dir)
    print(json.dumps({"logos": len(results), "datasets": len(config["datasets"])}, indent=2))


def _paths(dataset: dict[str, str], class_name: str, inputs: dict[str, str]) -> tuple[Path, Path]:
    name = dataset["dataset"]
    if dataset["family"] == "reconstructed":
        return (
            Path(inputs["bacterial_before_root"]) / name / f"{class_name}.fa",
            Path(inputs["bacterial_after_root"]) / name / f"{class_name}.fa",
        )
    return (
        Path(inputs["eukaryotic_before_root"]) / name / class_name,
        Path(inputs["eukaryotic_after_root"]) / name / f"{class_name}.fa",
    )


def _verify_inputs(inputs: dict[str, str]) -> None:
    checks = (
        (Path(inputs["bacterial_before_root"]) / "build_summary.json", inputs["bacterial_before_summary_sha256"]),
        (Path(inputs["bacterial_after_root"]) / "build_summary.json", inputs["bacterial_after_summary_sha256"]),
        (Path(inputs["eukaryotic_after_root"]) / "treatment_summary.json", inputs["eukaryotic_after_summary_sha256"]),
    )
    for path, expected in checks:
        observed = sha256_file(path)
        if observed != expected:
            raise ValueError(f"hash mismatch for {path}: expected {expected}, observed {observed}")


def _write_matrix(path: Path, matrix: np.ndarray, coordinate_start: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["position", *NUCLEOTIDES])
        for index, row in enumerate(matrix):
            writer.writerow([coordinate_start + index, *(f"{value:.12f}" for value in row)])


def _plot_comparison(
    path: Path,
    before: np.ndarray,
    after: np.ndarray,
    *,
    dataset: dict[str, str],
    class_name: str,
    before_count: int,
    after_count: int,
    coordinate_start: int,
) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(15, 6), sharex=True, sharey=True)
    for axis, matrix, label, count in (
        (axes[0], before, "Before treatment", before_count),
        (axes[1], after, "After treatment", after_count),
    ):
        _draw_logo(axis, matrix, coordinate_start)
        axis.set_title(f"{label} (n={count:,})", loc="left", fontsize=10)
        axis.set_ylabel("bits")
        axis.axvline(0, color="black", linestyle="--", linewidth=0.8)
        tss_label = (
            "TSS"
            if dataset["tss_status"] == "independently_positioned"
            else "nominal TSS"
        )
        axis.text(0.2, 1.87, tss_label, fontsize=8, ha="left", va="top")
    axes[1].set_xlabel("Position relative to TSS (nt)")
    figure.suptitle(
        f"Dataset sequence logo — {dataset['organism']} — {class_name} class",
        fontsize=12,
    )
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def _draw_logo(axis: plt.Axes, matrix: np.ndarray, coordinate_start: int) -> None:
    for position, heights in enumerate(matrix):
        baseline = 0.0
        for column in np.argsort(heights):
            height = float(heights[column])
            if height <= 1e-10:
                continue
            letter = NUCLEOTIDES[column]
            _draw_letter(axis, letter, coordinate_start + position, baseline, height)
            baseline += height
    axis.set_ylim(0, 2.0)
    axis.set_xlim(coordinate_start - 0.6, coordinate_start + len(matrix) - 0.4)
    axis.set_xticks([-60, -50, -40, -30, -20, -10, 0, 10, 20])
    axis.grid(axis="y", color="#dddddd", linewidth=0.4)


def _draw_letter(axis: plt.Axes, letter: str, x: float, y: float, height: float) -> None:
    glyph = TextPath((0, 0), letter, size=1, prop=FONT)
    bounds = glyph.get_extents()
    transform = (
        Affine2D()
        .translate(-bounds.xmin, -bounds.ymin)
        .scale(0.88 / bounds.width, height / bounds.height)
        .translate(x - 0.44, y)
    )
    axis.add_patch(
        PathPatch(
            MatplotlibPath(transform.transform(glyph.vertices), glyph.codes),
            facecolor=COLORS[letter],
            edgecolor="none",
        )
    )


def _gc_fraction(frequencies: np.ndarray) -> float:
    return float(frequencies[:, 1:3].sum(axis=1).mean())


if __name__ == "__main__":
    main()
