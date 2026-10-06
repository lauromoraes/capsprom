# Project Specification

## Objective

Build a reproducible doctoral research codebase for promoter region prediction
using capsule networks, with rigorous experiment tracking, statistical
evaluation, and thesis-oriented documentation.

## Dataset Contract

Current active model-ready dataset scope is restricted to the strict-DNA cleaned intra-source CSV files in `data/processed/assembled_datasets/intra_strict_dna/`. The original files in `data/processed/assembled_datasets/intra/` are preserved for provenance and preprocessing audit, but current and future EDA, feature engineering, model training, and evaluation stages should use `intra_strict_dna` unless a specification explicitly states otherwise. Generated project information must not treat other files under `data/` as active experimental datasets.

The Bhandari human promoter dataset is an explicit exception. Its legacy split
contains extensive exact-sequence duplication and train/test overlap. Current
Bhandari human experiments must use
`data/processed/leakage_controlled/bhandari_human_shuffle_v1/`, whose positive
windows are deduplicated before one deterministic shuffled negative is generated
per positive and whose positive--negative groups are assigned wholly to train or
test. This dataset is a synthetic-negative shuffle control and must be labeled
accordingly; it does not replace evaluation against genomic non-promoters.


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

The normalized physicochemical reference files are canonical inputs for these
encodings:

- `data/raw/references/normalized-dinuc.tsv` for dinucleotide properties.
- `data/raw/references/normalized-trinuc.tsv` for trinucleotide properties.

Physicochemical encoders must support selecting all properties or a named
subset of properties from the relevant reference file.

The implementation should expose encoders through a common interface so that
models and experiments can switch encodings through YAML configuration.
Experiments must also support feature combinations. Classical models may
receive flattened concatenated feature vectors, while deep neural networks must
be able to receive named feature blocks as independent inputs for multi-head or
multi-branch architectures before feature fusion.

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

The confirmatory metric, resampling, calibration, replication, and statistical
comparison rules are defined in `specs/statistical_evaluation_protocol.md` and
mirrored in `configs/evaluation_protocol.yaml`. Development runs whose test
results have already informed project decisions must be labeled exploratory and
must not be presented as blind confirmatory evidence.

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
where they fit in the doctoral thesis. No figure, table, chart, diagram, or
visual artifact may be included without a descriptive caption, a stable label,
and a preceding textual reference in the surrounding text.
