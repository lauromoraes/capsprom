"""Describe positives and negatives of the CNNProm E. coli pilot panels.

Sequence-content analyses read training folds only; the test partition enters
the count tables alone. Run from the repository root with PYTHONPATH=. so the
logo drawing of the GraphPro report can be reused.
"""

from __future__ import annotations

import argparse
import csv
import gzip
from collections import Counter
from pathlib import Path
import shutil
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import orthogonal_procrustes
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import yaml

from capsprom.data.loading import sha256_file
from capsprom.data.pilot_panels import (
    check_group_safety,
    genomic_records,
    native_records,
    training_records,
)
from capsprom.data.sequence_logo import sequence_logo_matrices
from capsprom.eda import panel_analysis as pa
from capsprom.state import write_json_atomic
from scripts.generate_graphpro_dataset_logos import _draw_logo, _write_matrix

POSITIVE, NATIVE, GENOMIC = "positive", "native_negative", "genomic_control"
GROUPS = (POSITIVE, NATIVE, GENOMIC)
LABELS = {POSITIVE: "Positives", NATIVE: "Native negatives", GENOMIC: "Genomic controls"}
COLORS = {POSITIVE: "#2a78d6", NATIVE: "#eb6834", GENOMIC: "#1baf7a"}
INK, MUTED, GRID = "#1f2328", "#6b7280", "#e5e7eb"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/cnnprom_ecoli_panel_analysis_v3.yaml"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    target = Path(config["analysis"]["output_dir"])
    if target.exists():
        raise FileExistsError(f"{target} exists; analyses are immutable")
    _style()
    inputs = config["inputs"]
    _verify(inputs)
    pinned = config["analysis"]["contract_frozen_before_this_analysis"]
    if sha256_file(Path(pinned["path"])) != pinned["sha256"]:
        raise SystemExit("the training contract changed after the analysis was declared")

    grouped = _read_csv(Path(inputs["native_records"]))
    ledger = _read_csv(Path(inputs["pair_ledger"]))
    native = native_records(grouped)
    panel = genomic_records(ledger, native)
    check_group_safety(native + panel)

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    try:
        (staging / "figures").mkdir()
        (staging / "matrices").mkdir()
        (staging / "tables").mkdir()
        counts = _count_tables(native, panel, ledger, inputs, staging / "tables")

        # Everything below sees training rows only.
        train_native = training_records(native)
        train_panel = training_records(panel)
        train_ledger = [row for row in ledger if row["partition"].startswith("train:")]
        if any(r.partition == "test" for r in train_native + train_panel) or any(row["partition"] == "test" for row in train_ledger):
            raise AssertionError("a test row reached the content analyses")
        sets = {
            POSITIVE: [r.sequence for r in train_native if r.label == 1],
            NATIVE: [r.sequence for r in train_native if r.label == 0],
            GENOMIC: [r.sequence for r in train_panel if r.label == 0],
        }
        codes = {name: pa.encode(values) for name, values in sets.items()}
        genome = _read_genome(Path(inputs["genome_fasta"]), "NC_000913.3")
        coding = _coding_masks(Path(inputs["annotation_gff"]), "NC_000913.3", len(genome))
        intervals = _intervals(train_ledger, sets[NATIVE], genome)
        results = {"counts": counts, "train_group_sizes": {k: len(v) for k, v in sets.items()}}
        results["logos"] = _logos(sets, train_ledger, config, staging)
        results["positional"] = _positional(codes, train_ledger, sets, config, staging)
        results["distributions"] = _distributions(codes, intervals, genome, config, staging)
        results["pairing"] = _pairing(codes, train_ledger, config, staging)
        results["context"] = _context(intervals, coding, genome, config, staging)
        results["motifs"] = _motifs(codes, config, staging)
        negative_folds = [r.partition for r in train_native if r.label == 0]
        results["native_negative_structure"] = _native_structure(intervals, negative_folds, config, staging)
        results["diversity"] = _diversity(sets, codes, train_ledger, train_panel, train_native, intervals, staging)
        results["projections"] = _projections(codes, config, staging)
        write_json_atomic(
            staging / "analysis_manifest.json",
            {
                "config_sha256": sha256_file(args.config),
                "partition_policy": config["partition_policy"],
                "test_sequences_analysed": False,
                "results": results,
                "outputs": {
                    str(path.relative_to(staging)).replace("\\", "/"): sha256_file(path)
                    for path in sorted(staging.rglob("*"))
                    if path.is_file()
                },
            },
        )
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(f"written {target}")


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": INK,
            "axes.titlesize": 10,
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "legend.frameon": False,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
        }
    )


def _verify(inputs: dict) -> None:
    for key in ("native_records", "pair_ledger", "genome_fasta"):
        if sha256_file(Path(inputs[key])) != inputs[f"{key}_sha256"]:
            raise SystemExit(f"hash mismatch: {key}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: list[str], rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _count_tables(native, panel, ledger, inputs, tables: Path) -> dict:
    """Counts only: this is the single place that touches the test partition."""

    rows = []
    for name, records in (("native", native), ("genomic_gc_matched", panel)):
        for side in ("train", "test"):
            subset = [r for r in records if r.partition.split(":")[0] == side]
            for label in (1, 0):
                chosen = [r for r in subset if r.label == label]
                rows.append(("cnnprom-ecoli", "Escherichia coli K-12", "CNNProm", name, side, label, len(chosen), len({r.group for r in chosen})))
    _write_csv(tables / "pilot_counts.csv", ["dataset", "organism", "source", "panel", "partition", "label", "records", "homology_groups"], rows)

    shared = {r.sequence for r in native if r.label == 1} & {r.sequence for r in panel if r.label == 1}
    only_native = sorted({r.record_id for r in native if r.label == 1} - {r.record_id for r in panel if r.label == 1})
    reuse = {"positives_shared_by_both_panels": len(shared), "positives_only_in_native": len(only_native)}

    context = []
    for directory in sorted(Path(inputs["context_counts_root"]).iterdir()):
        path = directory / "records.csv"
        if not path.is_file():
            continue
        tally = Counter((row["partition"].split(":")[0], row["label"]) for row in _read_csv(path))
        source, domain, organism = directory.name.split("-", 2)
        context.append((source, domain, organism, "native", tally[("train", "1")], tally[("train", "0")], tally[("test", "1")], tally[("test", "0")]))
    for root, panel_name, name in (
        (inputs["graphpro_genomic_root"], "genomic_gc_matched", "pair_ledger.csv"),
        (inputs["graphpro_cds_root"], "cds_derived", "cds_pair_ledger.csv"),
    ):
        for directory in sorted(Path(root).iterdir()):
            path = directory / name
            if not path.is_file():
                continue
            ledger_rows = _read_csv(path)
            organism = directory.name.rsplit("-", 1)[-1]
            if "partition" in ledger_rows[0]:
                sides = Counter(row["partition"].split(":")[0] for row in ledger_rows)
                context.append(("graphpro-reconstructed-v3", "prokaryotic", organism, panel_name, sides["train"], sides["train"], sides["test"], sides["test"]))
            else:
                # The genomic ledger of this build carries no partition, so only pairs are known here.
                context.append(("graphpro-reconstructed-v3", "prokaryotic", organism, panel_name, "", "", "", "", len(ledger_rows)))
    _write_csv(
        tables / "dataset_panel_context_counts.csv",
        ["source", "domain", "organism", "panel", "train_positive", "train_negative", "test_positive", "test_negative", "pairs_without_partition_column"],
        context,
    )
    return {"pilot_rows": len(rows), "reuse": reuse, "context_rows": len(context)}


def _read_genome(path: Path, contig: str) -> str:
    sequence: list[str] = []
    keep = False
    with gzip.open(path, "rt", encoding="ascii") as handle:
        for line in handle:
            if line.startswith(">"):
                keep = line[1:].split()[0] == contig
            elif keep:
                sequence.append(line.strip().upper())
    return "".join(sequence)


def _coding_masks(path: Path, contig: str, length: int) -> dict[str, np.ndarray]:
    masks = {strand: np.zeros(length + 1, dtype=np.int32) for strand in "+-"}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            parts = line.split("\t")
            if len(parts) > 6 and parts[0] == contig and parts[2] == "CDS":
                masks[parts[6]][int(parts[3]) - 1] += 1
                masks[parts[6]][int(parts[4])] -= 1
    return {strand: np.concatenate(([0], np.cumsum(np.cumsum(mask[:-1]) > 0))) for strand, mask in masks.items()}


def _intervals(ledger, native_negatives, genome: str) -> dict[str, list[tuple[int, int, str]]]:
    """Zero-based half-open windows; native negatives are placed by exact search."""

    reverse_genome = pa.reverse_complement(genome)
    length = len(genome)
    positives, controls = [], []
    for row in ledger:
        tss, strand = int(row["tss_zero_based"]), row["strand"]
        start = tss - 60 if strand == "+" else tss - 20
        positives.append((start, start + 81, strand))
        begin, end, control_strand = int(row["negative_start"]), int(row["negative_end"]), row["negative_strand"]
        window = genome[begin:end]
        if (window if control_strand == "+" else pa.reverse_complement(window)) != row["negative_sequence"].upper():
            raise AssertionError(f"control coordinates do not reproduce {row['record_id']}")
        controls.append((begin, end, control_strand))
    natives = []
    for sequence in native_negatives:
        forward = genome.find(sequence)
        if forward >= 0:
            natives.append((forward, forward + 81, "+"))
            continue
        backward = reverse_genome.find(sequence)
        if backward >= 0:
            natives.append((length - backward - 81, length - backward, "-"))
    return {POSITIVE: positives, GENOMIC: controls, NATIVE: natives}


def _legend_handles():
    from matplotlib.lines import Line2D

    return [Line2D([], [], color=COLORS[name], lw=2, label=LABELS[name]) for name in GROUPS]


def _positional_positive_sequences(sets, ledger) -> list[str]:
    """Shifted positives stay in the panel but leave positional analyses."""

    shifted = {row["positive_sequence"].upper() for row in ledger if row["support_class"] == "shifted"}
    return [sequence for sequence in sets[POSITIVE] if sequence not in shifted]


def _logos(sets, ledger, config, staging: Path) -> dict:
    alignment = config["alignment"]
    start = alignment["coordinate_start"]
    views = {POSITIVE: _positional_positive_sequences(sets, ledger), NATIVE: sets[NATIVE], GENOMIC: sets[GENOMIC]}
    matrices, summary = {}, {}
    for name, sequences in views.items():
        result = sequence_logo_matrices(sequences)
        matrices[name] = result
        _write_matrix(staging / "matrices" / f"{name}_frequency.csv", result.frequencies, start)
        _write_matrix(staging / "matrices" / f"{name}_information.csv", result.information_heights, start)
        count = result.frequencies * result.sequence_count
        _write_matrix(staging / "matrices" / f"{name}_count.csv", count, start)
        summary[name] = {
            "n": result.sequence_count,
            "small_sample_bias_bits": 3 / (2 * np.log(2) * result.sequence_count),
            "mean_information_bits": float(result.information_heights.sum(axis=1).mean()),
            "max_information_bits": float(result.information_heights.sum(axis=1).max()),
            "max_information_position": int(np.argmax(result.information_heights.sum(axis=1))) + start,
        }
    for suffix, limits in zip(("full_scale", "zoomed"), alignment["y_axes"]):
        figure, axes = plt.subplots(3, 1, figsize=(13, 6.6), sharex=True, sharey=True)
        for axis, name in zip(axes, GROUPS):
            _draw_logo(axis, matrices[name].information_heights, start)
            axis.set_ylim(*limits)
            axis.set_ylabel("bits")
            if name == POSITIVE:
                axis.set_title(f"{LABELS[name]} (n={matrices[name].sequence_count:,}, training folds, aligned on the TSS)")
                axis.axvline(0, color=INK, linestyle="--", linewidth=0.8)
                axis.text(0.4, limits[1] * 0.93, "TSS", fontsize=8, va="top", color=INK)
            else:
                axis.set_title(f"{LABELS[name]} (n={matrices[name].sequence_count:,}, training folds, no TSS: same window index only)")
        axes[-1].set_xlabel("Window coordinate (nt); offsets from the TSS apply to positives only")
        figure.savefig(staging / "figures" / f"fig01_logos_{suffix}.png", dpi=170)
        plt.close(figure)
    return summary


def _positional(codes, ledger, sets, config, staging: Path) -> dict:
    start = config["alignment"]["coordinate_start"]
    positions = np.arange(start, start + config["alignment"]["sequence_length"])
    positive = pa.encode(_positional_positive_sequences(sets, ledger))
    rng = np.random.default_rng(config["permutation"]["seed"])
    rounds = config["permutation"]["label_permutations"]
    figure, axes = plt.subplots(2, 1, figsize=(11, 5.6), sharex=True, sharey=True)
    summary = {}
    rows = []
    for axis, name in zip(axes, (NATIVE, GENOMIC)):
        other = codes[name]
        observed = pa.total_variation(pa.position_frequencies(positive), pa.position_frequencies(other))
        pooled = np.concatenate([positive, other])
        null = np.zeros((rounds, observed.size))
        for index in range(rounds):
            order = rng.permutation(pooled.shape[0])
            null[index] = pa.total_variation(
                pa.position_frequencies(pooled[order[: positive.shape[0]]]),
                pa.position_frequencies(pooled[order[positive.shape[0] :]]),
            )
        envelope = np.quantile(null.max(axis=1), 0.95)
        axis.fill_between(positions, 0, envelope, color=GRID, label="95% of the permutation maximum")
        axis.plot(positions, observed, color=COLORS[name], lw=2, label=f"Positives vs {LABELS[name].lower()}")
        axis.axvline(0, color=INK, linestyle="--", linewidth=0.8)
        axis.set_ylabel("Total variation")
        axis.legend(loc="upper left", ncols=2)
        order = np.argsort(observed)[::-1][:5]
        summary[name] = {
            "median": float(np.median(observed)),
            "maximum_null_q95": float(envelope),
            "positions_above_null": int((observed > envelope).sum()),
            "top_positions": [{"position": int(positions[i]), "total_variation": float(observed[i])} for i in order],
        }
        rows.extend((name, int(p), float(v)) for p, v in zip(positions, observed))
    axes[-1].set_xlabel("Position relative to the positive's TSS (nt); dashed line is the TSS of positives")
    figure.savefig(staging / "figures" / "fig02_positional_divergence.png")
    plt.close(figure)
    _write_csv(staging / "matrices" / "positional_total_variation.csv", ["comparison", "position", "total_variation"], rows)
    return summary


def _flank_gc(interval, genome: str, flank: int) -> float:
    start, end, _ = interval
    text = genome[max(0, start - flank) : start] + genome[end : end + flank]
    return (text.count("G") + text.count("C")) / max(len(text), 1)


def _hist(axis, values: dict, bins, xlabel: str) -> None:
    for name in GROUPS:
        axis.hist(values[name], bins=bins, density=True, histtype="step", lw=2, color=COLORS[name])
    axis.set_xlabel(xlabel)
    axis.set_ylabel("Density")


def _distributions(codes, intervals, genome, config, staging: Path) -> dict:
    flank = config["features"]["flank_nt"]
    features = {
        "gc": {k: pa.gc_fraction(v) for k, v in codes.items()},
        "gc_skew": {k: pa.gc_skew(v) for k, v in codes.items()},
        "entropy": {k: pa.shannon_entropy(v) for k, v in codes.items()},
        "periodicity_3": {k: pa.periodicity_3(v) for k, v in codes.items()},
        "flank_gc": {k: np.array([_flank_gc(i, genome, flank) for i in intervals[k]]) for k in GROUPS},
    }
    figure, axes = plt.subplots(2, 3, figsize=(12, 6.4))
    axes = axes.ravel()
    lengths = {k: [v.shape[1]] * v.shape[0] for k, v in codes.items()}
    labels = [LABELS[k] for k in GROUPS]
    axes[0].bar(labels, [len(lengths[k]) for k in GROUPS], color=[COLORS[k] for k in GROUPS], width=0.5)
    axes[0].set_ylabel("Training sequences, all 81 nt")
    axes[0].tick_params(axis="x", labelsize=8)
    _hist(axes[1], features["gc"], np.arange(0.1, 0.81, 1 / 40.5), "G+C fraction of the 81-nt window")
    _hist(axes[2], features["flank_gc"], 40, f"G+C fraction of {flank} nt flanks on each side")
    _hist(axes[3], features["gc_skew"], 30, "GC skew of the window")
    _hist(axes[4], features["entropy"], 30, "Mononucleotide entropy (bits)")
    _hist(axes[5], features["periodicity_3"], 30, "Lag-3 periodicity score")
    figure.legend(handles=_legend_handles(), loc="upper center", ncols=3, bbox_to_anchor=(0.5, 1.03))
    figure.tight_layout()
    figure.savefig(staging / "figures" / "fig03_distributions.png")
    plt.close(figure)
    return {
        name: {group: {"mean": float(np.mean(v)), "median": float(np.median(v)), "sd": float(np.std(v, ddof=1))} for group, v in values.items()}
        for name, values in features.items()
    }


def _pairing(codes, ledger, config, staging: Path) -> dict:
    positive = pa.encode([row["positive_sequence"].upper() for row in ledger])
    control = pa.encode([row["negative_sequence"].upper() for row in ledger])
    gap = (np.isin(positive, (1, 2)).sum(axis=1) - np.isin(control, (1, 2)).sum(axis=1))
    di_positive, di_control = pa.kmer_frequencies(positive, 2), pa.kmer_frequencies(control, 2)
    within = np.abs(di_positive - di_control).sum(axis=1) / 2
    rng = np.random.default_rng(config["permutation"]["seed"] + 1)
    shuffled = np.abs(di_positive - di_control[rng.permutation(control.shape[0])]).sum(axis=1) / 2

    names, first, second, third = [], [], [], []
    def column(label, function):
        names.append(label)
        first.append(function(codes[POSITIVE]))
        second.append(function(codes[NATIVE]))
        third.append(function(codes[GENOMIC]))

    column("G+C", pa.gc_fraction)
    column("GC skew", pa.gc_skew)
    column("Entropy", pa.shannon_entropy)
    column("Lag-3 periodicity", pa.periodicity_3)
    for index, kmer in enumerate(pa.kmer_names(2)):
        column(kmer, lambda c, i=index: pa.kmer_frequencies(c, 2)[:, i])
    native_smd = pa.standardized_mean_difference(np.stack(first, axis=1), np.stack(second, axis=1))
    genomic_smd = pa.standardized_mean_difference(np.stack(first, axis=1), np.stack(third, axis=1))

    figure, axes = plt.subplots(1, 3, figsize=(13, 5.8), gridspec_kw={"width_ratios": [1, 1, 1.25]})
    axes[0].bar(*np.unique(gap, return_counts=True), color=COLORS[GENOMIC], width=0.5)
    axes[0].set_xlim(-4.5, 4.5)
    axes[0].set_xlabel("Within-pair G+C count difference (positive minus control)")
    axes[0].set_ylabel("Training pairs")
    bins = np.linspace(0, max(within.max(), shuffled.max()), 35)
    axes[1].hist(within, bins=bins, histtype="step", lw=2, color=COLORS[GENOMIC], label="Actual pairs")
    axes[1].hist(shuffled, bins=bins, histtype="step", lw=2, color=MUTED, label="Randomly re-paired")
    axes[1].set_xlabel("Within-pair dinucleotide distance (total variation)")
    axes[1].set_ylabel("Training pairs")
    axes[1].legend()
    order = np.argsort(np.abs(native_smd))
    y = np.arange(len(names))
    axes[2].scatter(native_smd[order], y, s=26, color=COLORS[NATIVE], marker="s", label="Vs native negatives", zorder=3)
    axes[2].scatter(genomic_smd[order], y, s=26, color=COLORS[GENOMIC], label="Vs genomic controls", zorder=3)
    axes[2].set_yticks(y, [names[i] for i in order], fontsize=7)
    for limit in (-0.1, 0.1):
        axes[2].axvline(limit, color=MUTED, linestyle=":", linewidth=1)
    axes[2].axvline(0, color=INK, linewidth=0.8)
    axes[2].set_xlabel("Standardized mean difference (positives minus negatives)")
    axes[2].legend(loc="center right")
    figure.tight_layout()
    figure.savefig(staging / "figures" / "fig04_pairing_diagnostics.png")
    plt.close(figure)
    _write_csv(
        staging / "tables" / "balance_standardized_differences.csv",
        ["feature", "vs_native_negatives", "vs_genomic_controls"],
        [(n, float(a), float(b)) for n, a, b in zip(names, native_smd, genomic_smd)],
    )
    return {
        "pairs": int(gap.size),
        "gc_count_gap_counts": {str(k): int(v) for k, v in zip(*np.unique(gap, return_counts=True))},
        "dinucleotide_distance_median": {"actual": float(np.median(within)), "random_pairing": float(np.median(shuffled))},
        "smd_above_0_1": {"native": int((np.abs(native_smd) > 0.1).sum()), "genomic": int((np.abs(genomic_smd) > 0.1).sum()), "features": len(names)},
        "largest_smd": {
            "native": sorted(zip(names, map(float, native_smd)), key=lambda x: -abs(x[1]))[:5],
            "genomic": sorted(zip(names, map(float, genomic_smd)), key=lambda x: -abs(x[1]))[:5],
        },
    }


def _context(intervals, coding, genome, config, staging: Path) -> dict:
    minimum = config["features"]["coding_call_minimum_overlap"]
    bin_size = config["features"]["genome_bin_nt"]
    calls, table = {}, []
    for name in GROUPS:
        tally = Counter()
        for start, end, strand in intervals[name]:
            other = "-" if strand == "+" else "+"
            same_fraction = (coding[strand][end] - coding[strand][start]) / (end - start)
            other_fraction = (coding[other][end] - coding[other][start]) / (end - start)
            if max(same_fraction, other_fraction) < minimum:
                tally["noncoding"] += 1
            elif same_fraction >= other_fraction:
                tally["same_strand_cds"] += 1
            else:
                tally["opposite_strand_cds"] += 1
        calls[name] = dict(tally)
        table.extend((name, key, value) for key, value in tally.items())
    _write_csv(staging / "tables" / "coding_context.csv", ["group", "context", "windows"], table)

    figure, axes = plt.subplots(2, 1, figsize=(11, 6), gridspec_kw={"height_ratios": [1, 1.4]})
    shades = {"noncoding": "#9ca3af", "same_strand_cds": "#3f4752", "opposite_strand_cds": "#c9ced6"}
    y = np.arange(3)
    left = np.zeros(3)
    for key in ("noncoding", "same_strand_cds", "opposite_strand_cds"):
        values = np.array([calls[name].get(key, 0) / max(sum(calls[name].values()), 1) for name in GROUPS])
        axes[0].barh(y, values, left=left, color=shades[key], edgecolor="white", linewidth=2, height=0.6, label=key.replace("_", " ").replace("cds", "CDS"))
        for row, (value, base) in enumerate(zip(values, left)):
            if value > 0.04:
                axes[0].text(base + value / 2, row, f"{value:.0%}", ha="center", va="center", fontsize=8, color="white" if key == "same_strand_cds" else INK)
        left += values
    axes[0].set_yticks(y, [f"{LABELS[n]} (n={sum(calls[n].values()):,})" for n in GROUPS])
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Share of placed training windows")
    axes[0].legend(ncols=3, loc="upper center", bbox_to_anchor=(0.5, 1.28))
    bins = np.arange(0, len(genome) + bin_size, bin_size)
    for name in GROUPS:
        middle = [(s + e) / 2 for s, e, _ in intervals[name]]
        share, _ = np.histogram(middle, bins=bins)
        axes[1].step(bins[:-1] / 1e6, share / share.sum(), where="post", lw=1.6, color=COLORS[name], label=LABELS[name])
    axes[1].set_xlabel("Genome coordinate (Mb)")
    axes[1].set_ylabel(f"Share of windows per {bin_size // 1000} kb")
    axes[1].legend(ncols=3)
    figure.tight_layout()
    figure.savefig(staging / "figures" / "fig05_genomic_context.png")
    plt.close(figure)
    return {"placed": {k: len(v) for k, v in intervals.items()}, "coding_context": calls}


def _native_structure(intervals, folds, config, staging: Path) -> dict:
    """Where native negatives lie, and whether they overlap across inner folds."""

    windows = intervals[NATIVE]
    if len(windows) != len(folds):
        raise AssertionError("every native negative must be placed for this analysis")
    order = sorted(range(len(windows)), key=lambda i: windows[i][0])
    starts = np.array([windows[i][0] for i in order])
    gaps = np.diff(starts)
    pairs, across, lengths = 0, 0, []
    for position, i in enumerate(order):
        end = windows[i][1]
        for j in order[position + 1 :]:
            if windows[j][0] >= end:
                break
            pairs += 1
            lengths.append(end - windows[j][0])
            across += folds[i] != folds[j]
    component_sizes, size, reach = [], 0, -1
    for i in order:
        if windows[i][0] >= reach and size:
            component_sizes.append(size)
            size = 0
        size += 1
        reach = max(reach, windows[i][1])
    component_sizes.append(size)
    positive_hits = sum(
        any(s < end and start < e for s, e, _ in intervals[POSITIVE]) for start, end, _ in windows
    )
    figure, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    axes[0].plot(np.sort(starts) / 1e3, np.arange(1, starts.size + 1) / starts.size, color=COLORS[NATIVE], lw=2)
    axes[0].set_xlim(0, 400)
    axes[0].set_xlabel("Genome coordinate (kb), first 400 kb of 4,642 kb")
    axes[0].set_ylabel("Cumulative share of native negatives")
    axes[1].hist(np.clip(gaps, 0, 1000), bins=50, color=COLORS[NATIVE])
    axes[1].set_xlabel("Distance between consecutive window starts (nt, clipped at 1,000)")
    axes[1].set_ylabel("Window pairs")
    figure.tight_layout()
    figure.savefig(staging / "figures" / "fig10_native_negative_structure.png")
    plt.close(figure)
    return {
        "first_coordinate": int(starts.min()),
        "share_below_200_kb": float((starts < 200_000).mean()),
        "share_below_300_kb": float((starts < 300_000).mean()),
        "strand_counts": dict(Counter(strand for _, _, strand in windows)),
        "median_start_gap_nt": float(np.median(gaps)),
        "overlapping_window_pairs": pairs,
        "overlapping_pairs_across_inner_folds": int(across),
        "overlap_length_quantiles": [float(q) for q in np.quantile(lengths, (0, 0.5, 1))] if lengths else [],
        "pairs_overlapping_below_80_percent": int(sum(length < 65 for length in lengths)),
        "overlap_components": len(component_sizes),
        "largest_overlap_component": max(component_sizes),
        "windows_in_components_of_at_least_10": int(sum(c for c in component_sizes if c >= 10)),
        "native_negatives_overlapping_a_positive_window": int(positive_hits),
    }


def _motifs(codes, config, staging: Path) -> dict:
    start = config["alignment"]["coordinate_start"]
    figure, axes = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
    summary = {}
    for axis, (name, motif) in zip(axes, config["features"]["motifs"].items()):
        first, last = (value - start for value in motif["coordinates"])
        summary[name] = {}
        offsets = np.array([-0.26, 0, 0.26])
        for offset, group in zip(offsets, GROUPS):
            scores = pa.best_motif_mismatches(codes[group], motif["consensus"], first, last)
            shares = np.bincount(scores, minlength=7)[:7] / scores.size
            axis.bar(np.arange(7) + offset, shares, width=0.24, color=COLORS[group])
            summary[name][group] = {"median_mismatches": float(np.median(scores)), "share_within_one": float((scores <= 1).mean())}
        axis.set_title(f"{motif['consensus']}, window {motif['coordinates'][0]}..{motif['coordinates'][1]}")
        axis.set_xlabel("Fewest mismatches to the consensus")
    axes[0].set_ylabel("Share of sequences")
    figure.legend(handles=_legend_handles(), loc="upper center", ncols=3, bbox_to_anchor=(0.5, 1.08))
    figure.tight_layout()
    figure.savefig(staging / "figures" / "fig06_consensus_matches.png")
    plt.close(figure)
    return summary


def _diversity(sets, codes, ledger, train_panel, train_native, intervals, staging: Path) -> dict:
    self_identity = {name: pa.nearest_identity(codes[name], codes[name], exclude_self=True) for name in GROUPS}
    cross = {
        "positive_to_native_negative": pa.nearest_identity(codes[POSITIVE], codes[NATIVE]),
        "positive_to_genomic_control": pa.nearest_identity(codes[POSITIVE], codes[GENOMIC]),
        "native_negative_to_genomic_control": pa.nearest_identity(codes[NATIVE], codes[GENOMIC]),
    }
    canonical = {name: {min(s, pa.reverse_complement(s)) for s in values} for name, values in sets.items()}
    overlap_rows = []
    for a in GROUPS:
        for b in GROUPS:
            overlap_rows.append((a, b, len(canonical[a] & canonical[b])))
    _write_csv(staging / "tables" / "exact_identity_overlap.csv", ["group_a", "group_b", "shared_strand_invariant_sequences"], overlap_rows)

    def window_overlaps(first, second) -> int:
        ends = sorted(second)
        count = 0
        for start, end, _ in first:
            count += any(s < end and start < e for s, e, _ in ends)
        return count

    genomic = {
        "controls_overlapping_a_positive_window": window_overlaps(intervals[GENOMIC], intervals[POSITIVE]),
        "controls_overlapping_a_native_negative": window_overlaps(intervals[GENOMIC], intervals[NATIVE]),
        "controls_overlapping_another_control": sum(
            1 for i, (s, e, _) in enumerate(intervals[GENOMIC])
            if any(x != i and a < e and s < b for x, (a, b, _) in enumerate(intervals[GENOMIC]))
        ),
    }
    figure, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    bins = np.linspace(0.3, 1, 36)
    for name in GROUPS:
        axes[0].hist(self_identity[name], bins=bins, density=True, histtype="step", lw=2, color=COLORS[name], label=LABELS[name])
    axes[0].set_xlabel("Best ungapped identity to another sequence of the group")
    axes[0].set_ylabel("Density")
    axes[0].legend()
    for name, color, label in (
        ("positive_to_native_negative", COLORS[NATIVE], "Positive to nearest native negative"),
        ("positive_to_genomic_control", COLORS[GENOMIC], "Positive to nearest genomic control"),
    ):
        axes[1].hist(cross[name], bins=bins, density=True, histtype="step", lw=2, color=color, label=label)
    axes[1].set_xlabel("Best ungapped identity across classes")
    axes[1].set_ylabel("Density")
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(staging / "figures" / "fig07_diversity.png")
    plt.close(figure)

    group_sizes = {}
    for name, records in (("native_train", train_native), ("genomic_train", train_panel)):
        group_sizes[name] = dict(sorted(Counter(Counter(r.group for r in records).values()).items()))
    mixed = {
        name: sum(1 for labels in _labels_by_group(records).values() if len(labels) > 1)
        for name, records in (("native_train", train_native), ("genomic_train", train_panel))
    }
    return {
        "nearest_identity_within": {k: {"median": float(np.median(v)), "share_at_least_0_9": float((v >= 0.9).mean())} for k, v in self_identity.items()},
        "nearest_identity_across": {k: {"median": float(np.median(v)), "maximum": float(v.max()), "share_at_least_0_8": float((v >= 0.8).mean())} for k, v in cross.items()},
        "genomic_overlaps": genomic,
        "homology_group_size_counts": {k: {str(a): b for a, b in v.items()} for k, v in group_sizes.items()},
        "groups_holding_both_labels": mixed,
    }


def _labels_by_group(records) -> dict:
    labels: dict[str, set[int]] = {}
    for record in records:
        labels.setdefault(record.group, set()).add(record.label)
    return labels


def _representation(codes: np.ndarray, spec: dict) -> np.ndarray:
    if spec["kind"] == "one_hot_by_position":
        return pa.one_hot(codes)
    return pa.hellinger(pa.kmer_frequencies(codes, spec["k"]))


def _procrustes_disparity(first: np.ndarray, second: np.ndarray) -> float:
    a = (first - first.mean(axis=0)) / np.linalg.norm(first - first.mean(axis=0))
    b = (second - second.mean(axis=0)) / np.linalg.norm(second - second.mean(axis=0))
    rotation, scale = orthogonal_procrustes(b, a)
    return float(1 - scale**2)


def _projections(codes, config, staging: Path) -> dict:
    settings = config["projection"]
    rng = np.random.default_rng(settings["sampling_seed"])
    size = settings["samples_per_group"]
    chosen = {name: rng.choice(codes[name].shape[0], size, replace=False) for name in GROUPS}
    sample = np.concatenate([codes[name][chosen[name]] for name in GROUPS])
    groups = np.repeat(np.array(GROUPS), size)
    k = settings["neighbors_k"]
    matched = groups != NATIVE
    results: dict = {"n_per_group": size}

    def scatter(axis, points, values=None, cmap=None):
        if values is None:
            order = rng.permutation(points.shape[0])
            axis.scatter(points[order, 0], points[order, 1], s=7, c=[COLORS[g] for g in groups[order]], linewidths=0, alpha=0.75)
            return None
        return axis.scatter(points[:, 0], points[:, 1], s=7, c=values, cmap=cmap, linewidths=0, alpha=0.8)

    specs = [settings["primary_representation"], *settings["sensitivity_representations"]]
    embedded = {}
    figure, axes = plt.subplots(2, 3, figsize=(13, 7.6))
    gc = pa.gc_fraction(sample)
    for column, spec in enumerate(specs):
        name = spec["kind"] if "k" not in spec else f"kmer_{spec['k']}"
        matrix = _representation(sample, spec)
        pca = PCA(n_components=settings["pca"]["components"], svd_solver="full")
        scores = pca.fit_transform(matrix)
        embedded[name] = scores
        ratios = pca.explained_variance_ratio_
        scatter(axes[0, column], scores)
        axes[0, column].set_title(f"{name}: identity of each point")
        axes[0, column].set_xlabel(f"PC1 ({ratios[0]:.1%} of variance)")
        axes[0, column].set_ylabel(f"PC2 ({ratios[1]:.1%} of variance)")
        painted = scatter(axes[1, column], scores, gc, "viridis")
        figure.colorbar(painted, ax=axes[1, column], label="Window G+C fraction", shrink=0.85)
        axes[1, column].set_title(f"{name}: same projection, by G+C")
        axes[1, column].set_xlabel("PC1")
        axes[1, column].set_ylabel("PC2")
        permuted = [
            pa.same_group_neighbor_fraction(scores, rng.permutation(groups), k)
            for _ in range(settings["group_label_permutations"])
        ]
        results[name] = {
            "pc1_variance": float(ratios[0]),
            "pc2_variance": float(ratios[1]),
            "pc1_gc_correlation": float(np.corrcoef(scores[:, 0], gc)[0, 1]),
            "pc2_gc_correlation": float(np.corrcoef(scores[:, 1], gc)[0, 1]),
            "same_group_neighbors_in_50_pcs": pa.same_group_neighbor_fraction(scores, groups, k),
            "positive_vs_genomic_same_group_neighbors": pa.same_group_neighbor_fraction(scores[matched], groups[matched], k),
            "positive_vs_genomic_permuted_q95": float(
                np.quantile(
                    [
                        pa.same_group_neighbor_fraction(scores[matched], rng.permutation(groups[matched]), k)
                        for _ in range(settings["group_label_permutations"])
                    ],
                    0.95,
                )
            ),
            "same_group_neighbors_permuted_mean": float(np.mean(permuted)),
            "same_group_neighbors_permuted_q95": float(np.quantile(permuted, 0.95)),
        }
    figure.legend(handles=_legend_handles(), loc="upper center", ncols=3, bbox_to_anchor=(0.5, 1.02))
    figure.tight_layout()
    figure.savefig(staging / "figures" / "fig08_pca_common_space.png", dpi=170)
    plt.close(figure)
    np.savez_compressed(staging / "matrices" / "pca_scores.npz", groups=groups, **embedded)

    tsne = settings["tsne"]
    base = embedded[f"kmer_{settings['primary_representation']['k']}"]

    def run(seed: int, perplexity: int) -> np.ndarray:
        # PCA initialization makes the run seed-independent, so a seed check needs random starts.
        return TSNE(
            n_components=2,
            perplexity=perplexity,
            init=tsne["init"],
            learning_rate=tsne["learning_rate"],
            metric=tsne["metric"],
            max_iter=tsne["max_iter"],
            random_state=seed,
        ).fit_transform(base)

    by_seed = {seed: run(seed, tsne["perplexity"]) for seed in tsne["seeds"]}
    by_perplexity = {value: by_seed[tsne["seeds"][0]] if value == tsne["perplexity"] else run(tsne["seeds"][0], value) for value in tsne["perplexity_sensitivity"]}
    figure, axes = plt.subplots(2, 4, figsize=(13, 6.6))
    for axis, seed in zip(axes[0], tsne["seeds"][:4]):
        scatter(axis, by_seed[seed])
        axis.set_title(f"Seed {seed}, perplexity {tsne['perplexity']}")
    for axis, value in zip(axes[1], tsne["perplexity_sensitivity"]):
        scatter(axis, by_perplexity[value])
        axis.set_title(f"Seed {tsne['seeds'][0]}, perplexity {value}")
    painted = scatter(axes[1, 3], by_seed[tsne["seeds"][0]], gc, "viridis")
    axes[1, 3].set_title(f"Seed {tsne['seeds'][0]}, by G+C")
    figure.colorbar(painted, ax=axes[1, 3], shrink=0.85)
    for axis in axes.ravel():
        axis.set_xticks([])
        axis.set_yticks([])
        axis.grid(False)
    figure.legend(handles=_legend_handles(), loc="upper center", ncols=3, bbox_to_anchor=(0.5, 1.03))
    figure.tight_layout()
    figure.savefig(staging / "figures" / "fig09_tsne_stability.png", dpi=170)
    plt.close(figure)
    np.savez_compressed(staging / "matrices" / "tsne_embeddings.npz", groups=groups, **{f"seed_{s}": v for s, v in by_seed.items()})

    seeds = list(by_seed)
    disparities = [_procrustes_disparity(by_seed[a], by_seed[b]) for i, a in enumerate(seeds) for b in seeds[i + 1 :]]
    results["tsne"] = {
        "procrustes_disparity_between_seeds": {"median": float(np.median(disparities)), "maximum": float(np.max(disparities))},
        "same_group_neighbors_by_seed": {str(s): pa.same_group_neighbor_fraction(v, groups, k) for s, v in by_seed.items()},
        "neighbors_kept_from_50_pcs_by_seed": {str(s): pa.neighbor_overlap(base, v, k) for s, v in by_seed.items()},
        "positive_vs_genomic_same_group_neighbors_by_seed": {
            str(s): pa.same_group_neighbor_fraction(v[matched], groups[matched], k) for s, v in by_seed.items()
        },
    }
    return results


if __name__ == "__main__":
    main()
