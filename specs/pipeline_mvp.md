# Minimum Viable Pipeline Specification

This document defines the first pipeline target. It intentionally avoids custom
capsule architecture work until the data, configuration, tracking, and
evaluation path is stable.

## MVP Goal

Run a single reproducible promoter prediction experiment from a YAML file,
using one dataset split, one encoding strategy, one model, and MLflow tracking.

## Pipeline Stages

1. Load configuration.
2. Validate configuration schema.
3. Resolve dataset paths.
4. Validate dataset structure and biological constraints.
5. Build the requested feature encoding.
6. Train the requested model.
7. Evaluate the trained model.
8. Log parameters, metrics, plots, and artifacts to MLflow.
9. Write a run summary for later thesis reporting.

## Initial CLI Shape

```bash
capsprom validate-config configs/example_experiment.yaml
capsprom validate-data configs/example_experiment.yaml
capsprom run configs/example_experiment.yaml
```

## Initial Implementation Boundary

The first implementation should support:

- CSV datasets.
- Binary labels.
- 81 bp sequence validation (the MVP scope; later builds validate the domain
  window of `specs/sequence_window_policy.md`).
- DNA alphabet validation.
- One k-mer frequency encoder.
- Physicochemical encoder loading from the dinucleotide and trinucleotide TSV references.
- A feature-combination interface that can emit either concatenated vectors or named blocks.
- One simple baseline model.
- MLflow parameter and metric logging.

Out of scope for the first implementation:

- DNA-BERT embeddings.
- Full multi-head deep learning training, beyond defining the input contract.
- Capsule networks.
- Sparse routing.
- Full hyperparameter optimization.
- Full statistical comparison.
- Interpretability visualizations.

## Review Questions Before Implementation

The project restart milestone resolves the initial questions as follows:

- The strict-DNA Bhandari human promoter train/test split is the first pipeline
  fixture.
- Logistic regression is the first sanity-check classifier. XGBoost follows
  only after the complete data-to-tracking path is verified.
- Mandatory MVP metrics are accuracy, precision, recall, F1, ROC-AUC, and
  Matthews correlation coefficient. Encoding and training time are also
  recorded.
- MLflow initially uses the local SQLite store at `./mlflow.db`. MLflow 3.14
  places the legacy filesystem tracking backend in maintenance mode, so SQLite
  provides the supported local backend without requiring a tracking server.
- Dependencies remain in the versioned `requirements/*.txt` files and the
  project uses the repository-local `.venv` environment.
- The first run uses a deterministic stratified sample and two inexpensive
  feature blocks: normalized 3-mer frequency and global GC content/skew.

## Implemented Restart Milestone

The MVP is configured in `configs/mvp_logistic.yaml` and exposes:

```bash
PYTHONPATH=src python -m capsprom validate-config configs/mvp_logistic.yaml
PYTHONPATH=src python -m capsprom validate-data configs/mvp_logistic.yaml
PYTHONPATH=src python -m capsprom run configs/mvp_logistic.yaml
```

Each run copies the exact YAML configuration and writes a JSON summary under
`outputs/runs/<run-id>/`. MLflow records the same provenance, metrics, fitted
scikit-learn model, dataset SHA-256 hashes, feature block names, sample counts,
and timing measurements.
