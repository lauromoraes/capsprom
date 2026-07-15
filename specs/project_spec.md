# Project Specification

## Objective

Build a reproducible doctoral research codebase for promoter region prediction
using capsule networks, with rigorous experiment tracking, statistical
evaluation, and thesis-oriented documentation.

## Dataset Contract

Datasets must be CSV files with exactly the following required semantic fields:

| Field | Description |
| --- | --- |
| `sequence` | DNA nucleotide sequence normalized to 81 bp |
| `label` | Binary class label: `0` for non-promoter, `1` for promoter |

Validation requirements:

- Every sequence must have length 81.
- Every sequence must use only `A`, `C`, `G`, and `T`.
- Labels must be binary.
- Dataset partitions must be explicit in the filename or configuration.
- Positive and negative counts should be recoverable from the filename when
  the naming convention is used.

Dataset naming convention:

```text
[study]-[organism]-[dataset_name]-p-[count]-n-[count]-[partition].csv
```

## Feature Engineering Requirements

Supported encodings:

- K-mer frequency vectors for 1-mers through 6-mers.
- One-hot encoding applied to 1-mer through 6-mer representations.
- Physicochemical property vectors for dinucleotides and trinucleotides.
- DNA-BERT embeddings.

The implementation should expose encoders through a common interface so that
models and experiments can switch encodings through YAML configuration.

## Model Requirements

Baseline models:

- XGBoost.
- CNNProm.
- iPro-MP.
- EDEN.
- Fine-tuned DNA-BERT.

Proposed models:

- CapsProm.
- SparseCapsProm.

## Experiment Requirements

Experiments must measure:

- Effectiveness.
- Efficiency.
- Robustness.
- Statistical significance where appropriate.

Required metrics and tests will be specified during the pipeline design phase.

## Tracking Requirements

MLflow must record:

- Dataset identity and partition metadata.
- Configuration file used for the run.
- Model family and implementation version.
- Feature encoding settings.
- Hyperparameters.
- Metrics.
- Plots and figures.
- Model artifacts when appropriate.

## Configuration Requirements

Experiments must be launched from YAML configuration files. The configuration
schema must be strict enough to make runs reproducible and comparable.

## CLI Requirements

The repository must provide a CLI that can:

- Validate a configuration file.
- Validate datasets.
- Execute an experiment workflow.
- Write outputs and MLflow artifacts in predictable locations.

## Documentation Requirements

All documentation, code, comments, and configuration files must be in English.
Scholarly outputs should be prepared as LaTeX snippets with notes indicating
where they fit in the doctoral thesis.
