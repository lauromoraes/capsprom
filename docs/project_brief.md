# Project Brief

## Title

Promoter Region Prediction using Capsule Networks

## Objective

This doctoral research project investigates promoter region prediction in DNA
nucleotide sequences. The central aim is to develop, evaluate, and interpret
capsule-network-based models with the level of reproducibility, statistical
rigor, and documentation expected from a doctoral thesis.

## Core Hypothesis Direction

Capsule networks may capture structured motif relationships in promoter
sequences more effectively than conventional encoders or standard neural
architectures, especially when routing mechanisms are adapted to biological
sequence patterns.

This hypothesis must be refined into measurable experimental hypotheses before
full model development begins.


## Qualification Thesis Context

This repository builds on the initial doctoral qualification thesis version kept
at `C:/Users/lauro/OneDrive/Documents/academic/ufop/doc_tese_v1_0/`. A
repository-local synthesis is maintained in `docs/qualification_context.md` and
should be used as historical and methodological context for future
specifications, experiment design, and thesis writing.

The qualification text establishes the project background, prior CapsProm and
physicochemical-property contributions, baseline evaluation strategy, and planned
extensions such as a unified workflow, attention-enhanced CapsProm, conformal
prediction, GraphPro/transformer baselines, and MLflow-managed reproducibility.

## Data Assumptions

- Datasets are CSV files.
- Required columns are `sequence` and `label`.
- Labels are binary: `0` for non-promoter and `1` for promoter.
- Sequences are normalized to 81 bp.
- Sequences use only the DNA alphabet: `A`, `C`, `G`, `T`.
- Dataset filenames should follow:

```text
[study]-[organism]-[dataset_name]-p-[count]-n-[count]-[partition].csv
```

Example:

```text
bhandari-eukaryotic-Human_promoter-p-49213-n-49213-test.csv
```

## Model Families

Baseline models:

- XGBoost
- CNNProm
- iPro-MP
- EDEN
- Fine-tuned DNA-BERT

Proposed models:

- CapsProm
- SparseCapsProm

## Required Infrastructure

- YAML experiment configuration.
- CLI for reproducible experiment execution.
- MLflow tracking for parameters, metrics, plots, artifacts, and provenance.
- Statistical analysis for effectiveness, efficiency, and robustness.
- LaTeX-ready reporting artifacts for thesis writing.

## Development Principle

The pipeline should be developed and validated before the custom models become
the main focus. This prevents model architecture work from hiding data,
tracking, or evaluation problems.
