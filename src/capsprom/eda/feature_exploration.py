"""Feature-oriented EDA for final intra-source CapsProm datasets."""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from collections import Counter, defaultdict

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from capsprom.features.encoders import DNA_BASES, kmers_for_k, sliding_kmers, validate_dna_sequence
from capsprom.features.physicochemical import load_physicochemical_table
from capsprom.eda.plots import generate_eda_figures, write_figure_report

DATASET_FILE_RE = re.compile(r".+-p-\d+-n-\d+-(train|test)\.csv$")


@dataclass(frozen=True)
class DatasetRecord:
    """One input sequence and its binary label."""

    sequence: str
    label: int


@dataclass(frozen=True)
class EDAConfig:
    """Configuration for feature-oriented EDA."""

    input_dir: Path
    output_dir: Path
    sequence_column: str = "sequence"
    label_column: str = "label"
    expected_length: int = 81
    feature_sample_per_label: int = 1000
    top_kmers: int = 25
    kmer_values: tuple[int, ...] = (2, 3, 4)
    dinucleotide_reference: Path | None = None
    trinucleotide_reference: Path | None = None
    dinucleotide_properties: tuple[str, ...] = ()
    trinucleotide_properties: tuple[str, ...] = ()


def run_feature_eda(config: EDAConfig) -> None:
    """Run all configured EDA summaries and write CSV/Markdown artifacts."""

    config.output_dir.mkdir(parents=True, exist_ok=True)
    datasets = list(iter_dataset_files(config.input_dir))

    dataset_rows = []
    gc_rows = []
    positional_rows = []
    kmer_rows = []
    physicochemical_rows = []

    for dataset_path in datasets:
        records, invalid_rows = read_dataset(dataset_path, config.sequence_column, config.label_column)
        descriptor = parse_dataset_name(dataset_path)
        dataset_rows.append(summarize_dataset(dataset_path, descriptor, records, invalid_rows, config.expected_length))
        feature_records = stratified_records(records, config.feature_sample_per_label)
        gc_rows.extend(summarize_gc_features(descriptor, feature_records))
        positional_rows.extend(summarize_positional_base_frequency(descriptor, feature_records))
        for k in config.kmer_values:
            kmer_rows.extend(summarize_kmer_differences(descriptor, feature_records, k, config.top_kmers))
        physicochemical_rows.extend(summarize_physicochemical_features(descriptor, feature_records, config))

    write_csv(config.output_dir / "dataset_summary.csv", dataset_rows)
    write_csv(config.output_dir / "gc_content_summary.csv", gc_rows)
    write_csv(config.output_dir / "positional_base_frequency.csv", positional_rows)
    write_csv(config.output_dir / "top_kmer_differences.csv", kmer_rows)
    write_csv(config.output_dir / "physicochemical_summary.csv", physicochemical_rows)
    write_report(config.output_dir / "eda_report.md", config, dataset_rows, gc_rows, kmer_rows, physicochemical_rows)
    figures = generate_eda_figures(config.output_dir)
    write_figure_report(config.output_dir, figures)


def iter_dataset_files(input_dir: Path) -> Iterable[Path]:
    """Yield final intra-source CSV datasets, excluding metadata CSV files."""

    for path in sorted(input_dir.rglob("*.csv")):
        if "predictions_ecoli" in path.parts:
            continue
        if DATASET_FILE_RE.fullmatch(path.name):
            yield path


def read_dataset(path: Path, sequence_column: str, label_column: str) -> tuple[list[DatasetRecord], int]:
    """Read a dataset and keep only rows with strict DNA sequences and binary labels."""

    records: list[DatasetRecord] = []
    invalid_rows = 0
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                sequence = validate_dna_sequence(row[sequence_column])
                label = int(row[label_column])
                if label not in {0, 1}:
                    raise ValueError("label must be 0 or 1")
            except (KeyError, TypeError, ValueError):
                invalid_rows += 1
                continue
            records.append(DatasetRecord(sequence=sequence, label=label))
    return records, invalid_rows


def stratified_records(records: list[DatasetRecord], per_label: int) -> list[DatasetRecord]:
    """Return a deterministic class-balanced prefix sample for feature EDA."""

    if per_label <= 0:
        return records
    selected = []
    counts = Counter()
    for record in records:
        if counts[record.label] < per_label:
            selected.append(record)
            counts[record.label] += 1
        if counts[0] >= per_label and counts[1] >= per_label:
            break
    return selected


def parse_dataset_name(path: Path) -> dict[str, str]:
    """Parse study, domain, dataset, and split metadata from the file name."""

    stem = path.stem
    split = "train" if stem.endswith("-train") else "test" if stem.endswith("-test") else "unknown"
    core = stem.removesuffix("-train").removesuffix("-test")
    parts = core.split("-")
    study = parts[0] if parts else "unknown"
    domain = parts[1] if len(parts) > 1 else "unknown"
    descriptor_parts = []
    for part in parts[2:]:
        if part in {"p", "n"} or part.isdigit():
            break
        descriptor_parts.append(part)
    dataset = "-".join(descriptor_parts) if descriptor_parts else "unknown"
    return {"study": study, "domain": domain, "dataset": dataset, "split": split, "file": path.name}


def summarize_dataset(
    path: Path,
    descriptor: dict[str, str],
    records: list[DatasetRecord],
    invalid_rows: int,
    expected_length: int,
) -> dict[str, object]:
    """Summarize sample counts, labels, and sequence-length consistency."""

    lengths = [len(record.sequence) for record in records]
    positives = sum(record.label == 1 for record in records)
    negatives = sum(record.label == 0 for record in records)
    return {
        **descriptor,
        "path": path.as_posix(),
        "samples": len(records),
        "positives": positives,
        "negatives": negatives,
        "positive_fraction": _safe_divide(positives, len(records)),
        "invalid_rows_ignored": invalid_rows,
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
        "mean_length": mean(lengths),
        "expected_length_fraction": _safe_divide(sum(length == expected_length for length in lengths), len(lengths)),
    }


def summarize_gc_features(descriptor: dict[str, str], records: list[DatasetRecord]) -> list[dict[str, object]]:
    """Summarize GC content, GC skew, and AT skew by class."""

    values: dict[tuple[int, str], list[float]] = defaultdict(list)
    for record in records:
        counts = Counter(record.sequence)
        values[(record.label, "gc_content")].append(_safe_divide(counts["G"] + counts["C"], len(record.sequence)))
        values[(record.label, "gc_skew")].append(_safe_skew(counts["G"], counts["C"]))
        values[(record.label, "at_skew")].append(_safe_skew(counts["A"], counts["T"]))

    rows = []
    for (label, feature), feature_values in sorted(values.items()):
        rows.append({**descriptor, "label": label, "feature": feature, **describe_values(feature_values)})
    return rows


def summarize_positional_base_frequency(descriptor: dict[str, str], records: list[DatasetRecord]) -> list[dict[str, object]]:
    """Compute base frequencies for every position and class."""

    counts: dict[tuple[int, int], Counter[str]] = defaultdict(Counter)
    totals: Counter[tuple[int, int]] = Counter()
    for record in records:
        for position, base in enumerate(record.sequence, start=1):
            counts[(record.label, position)][base] += 1
            totals[(record.label, position)] += 1

    rows = []
    for (label, position), base_counts in sorted(counts.items()):
        total = totals[(label, position)]
        for base in DNA_BASES:
            rows.append(
                {
                    **descriptor,
                    "label": label,
                    "position": position,
                    "base": base,
                    "frequency": _safe_divide(base_counts[base], total),
                    "count": base_counts[base],
                    "total": total,
                }
            )
    return rows


def summarize_kmer_differences(
    descriptor: dict[str, str],
    records: list[DatasetRecord],
    k: int,
    top_n: int,
) -> list[dict[str, object]]:
    """Rank k-mers by absolute promoter versus non-promoter frequency difference."""

    class_counts = {0: Counter(), 1: Counter()}
    class_totals = Counter()
    for record in records:
        observed = sliding_kmers(record.sequence, k)
        class_counts[record.label].update(observed)
        class_totals[record.label] += len(observed)

    ranked = []
    for kmer in kmers_for_k(k):
        positive_frequency = _safe_divide(class_counts[1][kmer], class_totals[1])
        negative_frequency = _safe_divide(class_counts[0][kmer], class_totals[0])
        difference = positive_frequency - negative_frequency
        ranked.append(
            {
                **descriptor,
                "k": k,
                "kmer": kmer,
                "positive_frequency": positive_frequency,
                "negative_frequency": negative_frequency,
                "difference": difference,
                "absolute_difference": abs(difference),
                "log2_odds_ratio": _log2_odds(class_counts[1][kmer], class_totals[1], class_counts[0][kmer], class_totals[0]),
            }
        )
    ranked.sort(key=lambda row: (row["absolute_difference"], abs(row["log2_odds_ratio"])), reverse=True)
    return ranked[:top_n]


def summarize_physicochemical_features(
    descriptor: dict[str, str],
    records: list[DatasetRecord],
    config: EDAConfig,
) -> list[dict[str, object]]:
    """Summarize selected physicochemical property means by class."""

    rows = []
    references = [
        (config.dinucleotide_reference, config.dinucleotide_properties),
        (config.trinucleotide_reference, config.trinucleotide_properties),
    ]
    for reference_path, properties in references:
        if reference_path is None or not properties:
            continue
        table = load_physicochemical_table(reference_path).select_properties(properties)
        values: dict[tuple[int, str], list[float]] = defaultdict(list)
        for record in records:
            kmers = sliding_kmers(record.sequence, table.k)
            if not kmers:
                continue
            for property_index, property_name in enumerate(table.properties):
                property_values = [table.encode_kmer(kmer)[property_index] for kmer in kmers]
                values[(record.label, property_name)].append(mean(property_values))
        for (label, property_name), feature_values in sorted(values.items()):
            rows.append(
                {
                    **descriptor,
                    "label": label,
                    "k": table.k,
                    "property": property_name,
                    "reference": table.path.as_posix(),
                    **describe_values(feature_values),
                }
            )
    return rows


def write_report(
    path: Path,
    config: EDAConfig,
    dataset_rows: list[dict[str, object]],
    gc_rows: list[dict[str, object]],
    kmer_rows: list[dict[str, object]],
    physicochemical_rows: list[dict[str, object]],
) -> None:
    """Write a compact thesis-oriented EDA report in Markdown."""

    total_samples = sum(int(row["samples"]) for row in dataset_rows)
    total_files = len(dataset_rows)
    path.write_text(
        "\n".join(
            [
                "# Feature-Oriented EDA Report",
                "",
                "This report summarizes exploratory analyses for the final intra-source datasets used in the CapsProm project. "
                "The goal is to characterize the candidate DNA feature families before model training and to identify interpretable "
                "patterns that can motivate later ablation studies.",
                "",
                "Table `tab:eda-dataset-summary` should be used to introduce the dataset-level consistency summary. "
                "It reports sample counts, class balance, strict DNA validity, and sequence-length consistency.",
                "",
                f"- Input directory: `{config.input_dir.as_posix()}`",
                f"- Output directory: `{config.output_dir.as_posix()}`",
                f"- Dataset files analyzed: {total_files}",
                f"- Valid sequences analyzed: {total_samples}",
                f"- Feature-level sample per label: {config.feature_sample_per_label if config.feature_sample_per_label > 0 else 'all'}",
                f"- K-mer sizes analyzed: {', '.join(str(k) for k in config.kmer_values)}",
                "",
                "Table `tab:eda-gc-summary` should be used to discuss global compositional descriptors by class. "
                "GC content, GC skew, and AT skew are directly interpretable because they are computed from nucleotide counts.",
                "",
                f"- GC/skew summary rows: {len(gc_rows)}",
                "",
                "Table `tab:eda-top-kmer-differences` should be used to discuss explicit lexical signals. "
                "The reported k-mers are ranked by the absolute difference between promoter and non-promoter frequencies.",
                "",
                f"- Top k-mer rows: {len(kmer_rows)}",
                "",
                "Table `tab:eda-physicochemical-summary` should be used to discuss biologically informed feature behavior. "
                "Each row summarizes a selected normalized physicochemical property after averaging it over sequence positions.",
                "",
                f"- Physicochemical summary rows: {len(physicochemical_rows)}",
                "",
                "All generated tables require a preceding textual introduction, a stable label, and a descriptive caption before "
                "being incorporated into the thesis.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write dictionaries to CSV with a stable union of columns."""

    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def describe_values(values: list[float]) -> dict[str, float | int]:
    """Return descriptive statistics for a numeric vector."""

    return {
        "count": len(values),
        "mean": mean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
    }


def mean(values: Iterable[float]) -> float:
    """Return the arithmetic mean or zero for an empty iterable."""

    materialized = list(values)
    if not materialized:
        return 0.0
    return sum(materialized) / len(materialized)


def _safe_skew(positive: int, negative: int) -> float:
    return _safe_divide(positive - negative, positive + negative)


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _log2_odds(pos_count: int, pos_total: int, neg_count: int, neg_total: int) -> float:
    pos_probability = (pos_count + 0.5) / (pos_total + 1.0)
    neg_probability = (neg_count + 0.5) / (neg_total + 1.0)
    return math.log2(pos_probability / neg_probability)


def default_config() -> EDAConfig:
    """Return the default intra-source EDA configuration."""

    return EDAConfig(
        input_dir=Path("data/processed/assembled_datasets/intra_strict_dna"),
        output_dir=Path("outputs/eda/intra_strict_feature_exploration"),
        feature_sample_per_label=1000,
        dinucleotide_reference=Path("data/raw/references/normalized-dinuc.tsv"),
        trinucleotide_reference=Path("data/raw/references/normalized-trinuc.tsv"),
        dinucleotide_properties=("Base stacking", "B-DNA twist", "Dinucleotide GC Content"),
        trinucleotide_properties=("Bendability (DNAse)", "Trinucleotide GC Content"),
    )


def config_from_yaml(path: Path) -> EDAConfig:
    """Load EDA configuration from the project YAML format."""

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    data = raw.get("data", {})
    eda = raw.get("eda", {})
    physicochemical = eda.get("physicochemical", {})
    return EDAConfig(
        input_dir=Path(data.get("input_dir", "data/processed/assembled_datasets/intra_strict_dna")),
        output_dir=Path(eda.get("output_dir", "outputs/eda/intra_strict_feature_exploration")),
        sequence_column=str(data.get("sequence_column", "sequence")),
        label_column=str(data.get("label_column", "label")),
        expected_length=int(data.get("sequence_length", 81)),
        feature_sample_per_label=int(eda.get("feature_sample_per_label", 1000)),
        top_kmers=int(eda.get("top_kmers", 25)),
        kmer_values=tuple(int(value) for value in eda.get("kmer_values", [2, 3, 4])),
        dinucleotide_reference=Path(physicochemical["dinucleotide_reference"])
        if physicochemical.get("enabled", True) and physicochemical.get("dinucleotide_reference")
        else None,
        trinucleotide_reference=Path(physicochemical["trinucleotide_reference"])
        if physicochemical.get("enabled", True) and physicochemical.get("trinucleotide_reference")
        else None,
        dinucleotide_properties=tuple(physicochemical.get("dinucleotide_properties", [])),
        trinucleotide_properties=tuple(physicochemical.get("trinucleotide_properties", [])),
    )


def main() -> None:
    """Command-line entry point for the default EDA pass."""

    parser = argparse.ArgumentParser(description="Run feature-oriented EDA for CapsProm intra-source datasets.")
    parser.add_argument("--config", type=Path, default=Path("configs/eda_intra_features.yaml"))
    parser.add_argument("--input-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--top-kmers", type=int, default=None)
    parser.add_argument("--kmer-values", type=int, nargs="*", default=None)
    parser.add_argument("--feature-sample-per-label", type=int, default=None)
    args = parser.parse_args()

    config = config_from_yaml(args.config) if args.config.exists() else default_config()
    config = EDAConfig(
        input_dir=args.input_dir or config.input_dir,
        output_dir=args.output_dir or config.output_dir,
        expected_length=config.expected_length,
        feature_sample_per_label=(
            args.feature_sample_per_label
            if args.feature_sample_per_label is not None
            else config.feature_sample_per_label
        ),
        top_kmers=args.top_kmers or config.top_kmers,
        kmer_values=tuple(args.kmer_values) if args.kmer_values else config.kmer_values,
        dinucleotide_reference=config.dinucleotide_reference,
        trinucleotide_reference=config.trinucleotide_reference,
        dinucleotide_properties=config.dinucleotide_properties,
        trinucleotide_properties=config.trinucleotide_properties,
    )
    run_feature_eda(config)


if __name__ == "__main__":
    main()
