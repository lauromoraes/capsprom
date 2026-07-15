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
- 81 bp sequence validation.
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

- Confirm whether the Bhandari human promoter intra-study split should be the first pipeline fixture.
- Which baseline should be implemented first: XGBoost or a simpler sanity-check
  classifier?
- Which metrics are mandatory for the first run?
- Should the first MLflow backend be local file-based tracking?
- Which package manager and dependency format should be used for the project?
