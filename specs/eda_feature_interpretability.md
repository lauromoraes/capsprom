# EDA and Feature Interpretability Specification

## Purpose

The exploratory data analysis stage evaluates how candidate DNA feature
families behave across the final intra-source datasets before model training.
This stage is descriptive and diagnostic: it does not estimate model
performance and must not be interpreted as a substitute for held-out evaluation.

## Scope

The initial feature-oriented EDA scope is restricted to the model-ready strict-DNA intra-source datasets under `data/processed/assembled_datasets/intra_strict_dna`. Analyses must preserve the study, organism or subset, and split encoded in each dataset filename. The original `data/processed/assembled_datasets/intra` directory remains available for preprocessing audit and provenance checks, but it is not the default input for current or future feature-level EDA. The `predictions_ecoli` folder remains outside the EDA scope.

Dataset-level consistency summaries should use all rows. Feature-oriented
summaries may use a deterministic stratified sample per class during the first
EDA pass so that large sources do not dominate the exploratory stage or make it
computationally impractical. Any sampling limit must be reported in the EDA
report.

## Required Outputs

Each EDA run should create a timestamp-free, reproducible output directory with
the following artifacts:

- `dataset_summary.csv`: sample counts, label counts, class balance, sequence
  length distribution, and strict DNA validity checks for each file.
- `gc_content_summary.csv`: class-wise summary statistics for GC content,
  GC skew, and AT skew.
- `positional_base_frequency.csv`: base frequencies by position and class.
- `top_kmer_differences.csv`: most discriminative k-mers by absolute promoter
  versus non-promoter frequency difference.
- `physicochemical_summary.csv`: optional class-wise summaries for selected
  dinucleotide or trinucleotide physicochemical properties.
- `eda_report.md`: thesis-oriented narrative with captions and stable table
  labels for all generated tabular artifacts.
- `figures/*.svg`: dependency-free graphical summaries derived from the EDA
  tables, each introduced and captioned in `eda_figures_report.md`.
- `eda_figures_report.md`: thesis-oriented figure narrative with stable labels,
  descriptive captions, and explicit interpretability notes.

## Interpretability Questions

The first EDA pass should answer the following questions:

1. Are the final datasets internally consistent after preprocessing?
2. Do promoter and non-promoter sequences differ in global GC content or skew?
3. Are there position-specific nucleotide patterns that may correspond to
   promoter motifs or source-specific biases?
4. Which k-mers show the largest class-wise frequency differences?
5. Do selected physicochemical properties show class-wise shifts that justify
   biologically informed encodings?

## Methodological Notes

EDA must remain separate from model selection. Any feature ranking produced in
this stage is descriptive and should be reused for hypothesis generation,
ablation design, and thesis interpretation, not as supervised feature selection
on the final test set.

When EDA outputs are incorporated into thesis text, every table or figure must
be introduced in the surrounding text, referenced by label, and accompanied by a
descriptive caption.
