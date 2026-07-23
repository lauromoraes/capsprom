"""Dependency-free SVG plots for CapsProm feature EDA outputs."""

from __future__ import annotations

import csv
import html
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

CLASS_COLORS = {0: "#6b7280", 1: "#2563eb"}
DATASET_FILE_RE_NOTE = "figures are generated from strict-DNA EDA CSV artifacts"


def generate_eda_figures(output_dir: Path) -> list[dict[str, str]]:
    """Generate stable SVG figures from EDA CSV artifacts."""

    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    figures = [
        _write_class_balance_by_study(output_dir, figures_dir),
        _write_gc_content_by_study(output_dir, figures_dir),
        _write_positional_base_difference(output_dir, figures_dir),
        _write_recurrent_kmer_differences(output_dir, figures_dir),
        _write_physicochemical_property_shift(output_dir, figures_dir),
    ]
    return figures


def write_figure_report(output_dir: Path, figures: list[dict[str, str]]) -> None:
    """Write a Markdown report that introduces and captions all EDA figures."""

    lines = [
        "# Feature-Oriented EDA Figures",
        "",
        "This report introduces graphical artifacts generated from the strict-DNA intra-source EDA tables. "
        "The figures are descriptive and should be used to guide interpretation and later ablation planning, "
        "not as final supervised feature selection evidence.",
        "",
    ]
    for figure in figures:
        lines.extend([
            f"Figure `{figure['label']}` summarizes {figure['introduction']}",
            "",
            f"![{figure['caption']}]({figure['path']})",
            "",
            f"Caption: {figure['caption']}",
            "",
        ])
    (output_dir / "eda_figures_report.md").write_text("\n".join(lines), encoding="utf-8")


def _write_class_balance_by_study(output_dir: Path, figures_dir: Path) -> dict[str, str]:
    rows = _read_csv(output_dir / "dataset_summary.csv")
    totals: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        totals[row["study"]]["positive"] += int(row["positives"])
        totals[row["study"]]["negative"] += int(row["negatives"])
    data = [(study, counts["positive"], counts["negative"]) for study, counts in sorted(totals.items())]
    path = figures_dir / "class_balance_by_study.svg"
    _stacked_bar_svg(path, "Class balance by study", data, "promoter", "non-promoter", "sequences")
    return {
        "label": "fig:eda-class-balance-by-study",
        "path": "figures/class_balance_by_study.svg",
        "introduction": "the number of promoter and non-promoter sequences retained in each strict-DNA source group.",
        "caption": "Class balance by source study after strict-DNA cleaning. Bars aggregate train and test partitions and separate promoter from non-promoter examples.",
    }


def _write_gc_content_by_study(output_dir: Path, figures_dir: Path) -> dict[str, str]:
    rows = _read_csv(output_dir / "gc_content_summary.csv")
    values: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["feature"] == "gc_content":
            values[row["study"]][int(row["label"])].append(float(row["mean"]))
    data = [(study, _mean(by_label[1]), _mean(by_label[0])) for study, by_label in sorted(values.items())]
    path = figures_dir / "gc_content_by_study_class.svg"
    _grouped_bar_svg(path, "Mean GC content by study and class", data, "promoter", "non-promoter", "mean GC content", 0.0, 1.0)
    return {
        "label": "fig:eda-gc-content-by-study-class",
        "path": "figures/gc_content_by_study_class.svg",
        "introduction": "class-wise mean GC content for each source group.",
        "caption": "Mean GC content by source study and class. Values are averaged across dataset-level EDA summaries and provide an interpretable compositional comparison between promoter and non-promoter windows.",
    }


def _write_positional_base_difference(output_dir: Path, figures_dir: Path) -> dict[str, str]:
    rows = _read_csv(output_dir / "positional_base_frequency.csv")
    counts: dict[tuple[int, int, str], float] = defaultdict(float)
    totals: dict[tuple[int, int], float] = defaultdict(float)
    for row in rows:
        label = int(row["label"])
        position = int(row["position"])
        base = row["base"]
        count = float(row["count"])
        counts[(label, position, base)] += count
        totals[(label, position)] += count
    bases = ["A", "C", "G", "T"]
    positions = sorted({position for _, position, _ in counts})
    matrix = []
    for base in bases:
        row_values = []
        for position in positions:
            positive = counts[(1, position, base)] / totals[(1, position)]
            negative = counts[(0, position, base)] / totals[(0, position)]
            row_values.append(positive - negative)
        matrix.append(row_values)
    path = figures_dir / "positional_base_frequency_difference.svg"
    _heatmap_svg(path, "Promoter minus non-promoter positional base frequency", bases, len(positions), matrix, -0.15, 0.15)
    return {
        "label": "fig:eda-positional-base-frequency-difference",
        "path": "figures/positional_base_frequency_difference.svg",
        "introduction": "position-specific nucleotide differences between promoter and non-promoter sequences.",
        "caption": "Promoter minus non-promoter positional base-frequency differences after strict-DNA cleaning. Columns correspond to positions in the 81 bp window and rows correspond to A, C, G, and T.",
    }


def _write_recurrent_kmer_differences(output_dir: Path, figures_dir: Path) -> dict[str, str]:
    rows = _read_csv(output_dir / "top_kmer_differences.csv")
    stats: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if int(row["k"]) == 3:
            stats[row["kmer"]].append(float(row["absolute_difference"]))
    ranked = sorted(((kmer, len(values), _mean(values)) for kmer, values in stats.items()), key=lambda item: (item[1], item[2]), reverse=True)[:18]
    path = figures_dir / "recurrent_discriminative_trimers.svg"
    _horizontal_bar_svg(path, "Recurrent discriminative 3-mers", [(kmer, count) for kmer, count, _ in ranked], "number of dataset summaries where selected")
    return {
        "label": "fig:eda-recurrent-discriminative-trimers",
        "path": "figures/recurrent_discriminative_trimers.svg",
        "introduction": "which 3-mers recur most often among the strongest class-wise k-mer differences.",
        "caption": "Most recurrent discriminative 3-mers across strict-DNA intra-source dataset summaries. Counts indicate how often each 3-mer appears among the top class-wise frequency differences.",
    }


def _write_physicochemical_property_shift(output_dir: Path, figures_dir: Path) -> dict[str, str]:
    rows = _read_csv(output_dir / "physicochemical_summary.csv")
    by_key: dict[tuple[str, str, str, int], dict[int, float]] = defaultdict(dict)
    for row in rows:
        key = (row["study"], row["dataset"], row["property"], int(row["k"]))
        by_key[key][int(row["label"])] = float(row["mean"])
    shifts: dict[str, list[float]] = defaultdict(list)
    for (_, _, prop, k), by_label in by_key.items():
        if 0 in by_label and 1 in by_label:
            shifts[f"k={k}: {prop}"].append(by_label[1] - by_label[0])
    ranked = sorted(((name, _mean(values)) for name, values in shifts.items()), key=lambda item: abs(item[1]), reverse=True)
    path = figures_dir / "physicochemical_property_shift.svg"
    _diverging_bar_svg(path, "Mean physicochemical shift by class", ranked, "promoter mean minus non-promoter mean")
    return {
        "label": "fig:eda-physicochemical-property-shift",
        "path": "figures/physicochemical_property_shift.svg",
        "introduction": "average class-wise shifts for selected dinucleotide and trinucleotide physicochemical properties.",
        "caption": "Mean promoter minus non-promoter shift for selected normalized physicochemical properties. Positive values indicate higher average property values in promoter windows.",
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _mean(values: Iterable[float]) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else 0.0


def _svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#1f2937}.title{font-size:18px;font-weight:700}.axis{font-size:11px}.label{font-size:12px}.small{font-size:10px}</style>',
    ]


def _write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines + ["</svg>", ""]), encoding="utf-8")


def _axis(lines: list[str], left: int, top: int, chart_w: int, chart_h: int) -> None:
    lines.append(f'<line x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}" stroke="#374151"/>')
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}" stroke="#374151"/>')


def _legend(lines: list[str], items: list[tuple[str, str]], x: int, y: int) -> None:
    for idx, (label, color) in enumerate(items):
        yy = y + idx * 20
        lines.append(f'<rect x="{x}" y="{yy}" width="12" height="12" fill="{color}"/>')
        lines.append(f'<text class="axis" x="{x + 18}" y="{yy + 10}">{html.escape(label)}</text>')


def _stacked_bar_svg(path: Path, title: str, data: list[tuple[str, int, int]], positive_label: str, negative_label: str, y_label: str) -> None:
    width, height = 760, 430
    left, top, chart_w, chart_h = 90, 60, 610, 280
    max_total = max(pos + neg for _, pos, neg in data) or 1
    bar_w = chart_w / len(data) * 0.58
    lines = _svg_header(width, height)
    lines.append(f'<text class="title" x="{left}" y="32">{html.escape(title)}</text>')
    lines.append(f'<text class="axis" x="18" y="{top + chart_h / 2}" transform="rotate(-90 18 {top + chart_h / 2})">{html.escape(y_label)}</text>')
    for idx, (study, positive, negative) in enumerate(data):
        x = left + idx * (chart_w / len(data)) + (chart_w / len(data) - bar_w) / 2
        neg_h = chart_h * negative / max_total
        pos_h = chart_h * positive / max_total
        y_neg = top + chart_h - neg_h
        y_pos = y_neg - pos_h
        lines.append(f'<rect x="{x:.1f}" y="{y_pos:.1f}" width="{bar_w:.1f}" height="{pos_h:.1f}" fill="{CLASS_COLORS[1]}"/>')
        lines.append(f'<rect x="{x:.1f}" y="{y_neg:.1f}" width="{bar_w:.1f}" height="{neg_h:.1f}" fill="{CLASS_COLORS[0]}"/>')
        lines.append(f'<text class="axis" x="{x + bar_w / 2:.1f}" y="{height - 45}" text-anchor="middle">{html.escape(study)}</text>')
    _axis(lines, left, top, chart_w, chart_h)
    _legend(lines, [(positive_label, CLASS_COLORS[1]), (negative_label, CLASS_COLORS[0])], width - 230, 30)
    _write(path, lines)


def _grouped_bar_svg(path: Path, title: str, data: list[tuple[str, float, float]], first_label: str, second_label: str, y_label: str, y_min: float, y_max: float) -> None:
    width, height = 760, 430
    left, top, chart_w, chart_h = 90, 60, 610, 280
    group_w = chart_w / len(data)
    bar_w = group_w * 0.24
    lines = _svg_header(width, height)
    lines.append(f'<text class="title" x="{left}" y="32">{html.escape(title)}</text>')
    lines.append(f'<text class="axis" x="18" y="{top + chart_h / 2}" transform="rotate(-90 18 {top + chart_h / 2})">{html.escape(y_label)}</text>')
    for idx, (study, first, second) in enumerate(data):
        base_x = left + idx * group_w + group_w / 2
        for offset, value, color in [(-bar_w * 0.55, first, CLASS_COLORS[1]), (bar_w * 0.55, second, CLASS_COLORS[0])]:
            h = chart_h * (value - y_min) / (y_max - y_min)
            lines.append(f'<rect x="{base_x + offset - bar_w / 2:.1f}" y="{top + chart_h - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{color}"/>')
        lines.append(f'<text class="axis" x="{base_x:.1f}" y="{height - 45}" text-anchor="middle">{html.escape(study)}</text>')
    _axis(lines, left, top, chart_w, chart_h)
    _legend(lines, [(first_label, CLASS_COLORS[1]), (second_label, CLASS_COLORS[0])], width - 230, 30)
    _write(path, lines)


def _horizontal_bar_svg(path: Path, title: str, data: list[tuple[str, int]], x_label: str) -> None:
    width, height = 760, 520
    left, top, chart_w, bar_h, gap = 150, 58, 560, 18, 7
    max_value = max(value for _, value in data) or 1
    lines = _svg_header(width, height)
    lines.append(f'<text class="title" x="{left}" y="32">{html.escape(title)}</text>')
    for idx, (label, value) in enumerate(data):
        y = top + idx * (bar_h + gap)
        w = chart_w * value / max_value
        lines.append(f'<text class="axis" x="{left - 10}" y="{y + 13}" text-anchor="end">{html.escape(label)}</text>')
        lines.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" fill="#2563eb"/>')
        lines.append(f'<text class="small" x="{left + w + 5:.1f}" y="{y + 13}">{value}</text>')
    lines.append(f'<line x1="{left}" y1="{height - 52}" x2="{left + chart_w}" y2="{height - 52}" stroke="#374151"/>')
    lines.append(f'<text class="axis" x="{left + chart_w / 2}" y="{height - 22}" text-anchor="middle">{html.escape(x_label)}</text>')
    _write(path, lines)


def _diverging_bar_svg(path: Path, title: str, data: list[tuple[str, float]], x_label: str) -> None:
    width, height = 780, 360
    left, top, chart_w, bar_h, gap = 270, 58, 420, 24, 12
    max_abs = max(abs(value) for _, value in data) or 1.0
    center = left + chart_w / 2
    lines = _svg_header(width, height)
    lines.append(f'<text class="title" x="{left}" y="32">{html.escape(title)}</text>')
    lines.append(f'<line x1="{center:.1f}" y1="{top - 10}" x2="{center:.1f}" y2="{top + len(data) * (bar_h + gap)}" stroke="#111827"/>')
    for idx, (label, value) in enumerate(data):
        y = top + idx * (bar_h + gap)
        w = (chart_w / 2) * abs(value) / max_abs
        x = center if value >= 0 else center - w
        color = "#2563eb" if value >= 0 else "#b84a4a"
        anchor = "start" if value >= 0 else "end"
        text_x = x + w + 5 if value >= 0 else x - 5
        lines.append(f'<text class="axis" x="{left - 8}" y="{y + 16}" text-anchor="end">{html.escape(label)}</text>')
        lines.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{bar_h}" fill="{color}"/>')
        lines.append(f'<text class="small" x="{text_x:.1f}" y="{y + 16}" text-anchor="{anchor}">{value:.4f}</text>')
    lines.append(f'<text class="axis" x="{left + chart_w / 2}" y="{height - 24}" text-anchor="middle">{html.escape(x_label)}</text>')
    _write(path, lines)


def _heatmap_svg(path: Path, title: str, row_labels: list[str], column_count: int, matrix: list[list[float]], value_min: float, value_max: float) -> None:
    width, height = 900, 280
    left, top, cell_w, cell_h = 70, 70, 9, 34
    lines = _svg_header(width, height)
    lines.append(f'<text class="title" x="{left}" y="32">{html.escape(title)}</text>')
    for r, label in enumerate(row_labels):
        y = top + r * cell_h
        lines.append(f'<text class="label" x="{left - 14}" y="{y + 22}" text-anchor="end">{html.escape(label)}</text>')
        for c in range(column_count):
            color = _diverging_color(matrix[r][c], value_min, value_max)
            lines.append(f'<rect x="{left + c * cell_w}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{color}"/>')
    for tick in [1, 20, 40, 60, 81]:
        x = left + (tick - 1) * cell_w
        lines.append(f'<line x1="{x}" y1="{top + len(row_labels) * cell_h}" x2="{x}" y2="{top + len(row_labels) * cell_h + 5}" stroke="#374151"/>')
        lines.append(f'<text class="small" x="{x}" y="{top + len(row_labels) * cell_h + 20}" text-anchor="middle">{tick}</text>')
    lines.append(f'<text class="axis" x="{left + column_count * cell_w / 2}" y="{height - 22}" text-anchor="middle">position in 81 bp window</text>')
    lines.append(f'<text class="small" x="{width - 185}" y="62">red: non-promoter enriched</text>')
    lines.append(f'<text class="small" x="{width - 185}" y="78">blue: promoter enriched</text>')
    _write(path, lines)


def _diverging_color(value: float, value_min: float, value_max: float) -> str:
    if value >= 0:
        intensity = min(1.0, value / value_max)
        r = int(245 - 208 * intensity)
        g = int(247 - 148 * intensity)
        b = int(250 - 15 * intensity)
    else:
        intensity = min(1.0, value / value_min)
        r = int(245 - 61 * intensity)
        g = int(247 - 173 * intensity)
        b = int(250 - 176 * intensity)
    return f"#{r:02x}{g:02x}{b:02x}"
