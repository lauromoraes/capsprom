# Feature-Oriented EDA

This document defines the first exploratory data analysis stage for the final intra-source CapsProm datasets. The EDA stage is intended to characterize candidate DNA feature families before model training and to support thesis interpretation.

## Scope

The default analysis reads CSV files from `data/processed/assembled_datasets/intra_strict_dna` and ignores any path containing `predictions_ecoli`. This strict-DNA directory is the active input for current and future feature-oriented EDA, feature engineering, model training, and evaluation. The original `data/processed/assembled_datasets/intra` directory is retained for preprocessing audit and provenance checks. Dataset-level summaries use every valid row. Feature-level summaries use a deterministic stratified sample per label by default, because the largest sources can otherwise dominate runtime and descriptive patterns.

## Generated Artifacts

Running the default script creates `outputs/eda/intra_strict_feature_exploration` with the following files:

- `dataset_summary.csv`: sample counts, class balance, strict DNA validity, and sequence-length consistency.
- `gc_content_summary.csv`: class-wise GC content, GC skew, and AT skew summaries.
- `positional_base_frequency.csv`: position-wise nucleotide frequencies by class.
- `top_kmer_differences.csv`: k-mers ranked by promoter versus non-promoter frequency differences.
- `physicochemical_summary.csv`: selected dinucleotide and trinucleotide property summaries by class.
- `eda_report.md`: thesis-oriented narrative that introduces each table with stable labels.
- `figures/*.svg`: graphical summaries for class balance, GC content, positional base differences, recurrent discriminative 3-mers, and physicochemical shifts.
- `eda_figures_report.md`: thesis-oriented narrative that introduces and captions every generated figure.

## Usage

```bash
PYTHONPATH=src python3 scripts/run_feature_eda.py
```

Useful options:

```bash
PYTHONPATH=src python3 scripts/run_feature_eda.py --feature-sample-per-label 2000 --kmer-values 2 3 --top-kmers 20
```

Use `--feature-sample-per-label 0` only when a full feature-level EDA pass is explicitly needed. Full passes can be slow on the largest Bhandari and CNNProm datasets.

## Thesis Interpretation

The EDA outputs should be treated as descriptive evidence. They can motivate hypotheses, identify dataset-specific biases, and guide ablation design, but they must not be used as final supervised feature selection on held-out test sets.

When any EDA table or figure is moved into the thesis, it must be introduced in the text, referenced by a stable label, and accompanied by a descriptive caption.
