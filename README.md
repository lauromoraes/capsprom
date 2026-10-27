# CapsProm

CapsProm is a doctoral research project for promoter region prediction in DNA
sequences using capsule networks and rigorous, reproducible machine learning
experiments.

The project starts from a deliberately incremental plan. The first goal is not
to implement every model at once, but to define a reliable research and
engineering structure that can support careful pipeline development,
experimental validation, and thesis-grade documentation.

## Research Scope

- Task: binary promoter prediction from DNA nucleotide sequences.
- Input format: CSV files with `sequence` and `label` columns.
- Current processed data path: `data/processed/assembled_datasets/`.
- Sequence length: normalized to 81 bp.
- Alphabet: `A`, `C`, `G`, `T`.
- Labels: `0` for non-promoter and `1` for promoter.
- Main proposed models: `CapsProm` and `SparseCapsProm`.
- Required tracking: MLflow for parameters, metrics, plots, artifacts, and run
  provenance.
- Required configuration: YAML files validated by a robust schema.
- Required scholarly output: LaTeX snippets and thesis-ready documentation.

## Repository Organization and Current State

See `docs/ai-handover/PROJECT_INDEX.md` for the component map, data and
experiment locations, and recovery path. Current execution state comes from
`make status`; released work is tracked in `docs/roadmap.md`. The sections
below describe the original incremental plan and the first MVP runs.

## Development Environment

A local virtual environment is available at `.venv/`. Setup and activation instructions are documented in `docs/development_environment.md`.

Install the repository package in editable mode and run the standard checks:

```bash
make install-dev
make check
make status
```

`make status` provides the active dataset contract, Git state, experiment
checkpoints, and the next recommended command without loading the ML stack.

## Academic Writing

Thesis-oriented figures, tables, diagrams, and plots must always be introduced and referenced in the surrounding text, with descriptive captions and stable labels. See `specs/academic_writing_spec.md`.

## Feature Encoding

Feature engineering supports named blocks, physicochemical references, concatenated inputs for classical models, and multi-head inputs for deep neural networks. See `specs/feature_architecture.md` and `docs/feature_encoding.md`.

## Active Data Scope

Confirmatory experiments with source-provided negatives use the canonical
exact-sequence-safe datasets under
`data/processed/assembled_datasets/intra_regenerated_v3_strict_dna/`. Legacy
`intra/` and `intra_strict_dna/` files are retained only for provenance and
audit. See `docs/intra_source_data_scope.md`.

## Data Processing

The notebook-derived dataset construction logic is available as reusable Python modules under `src/capsprom/data/`. The processing methodology is documented in `docs/dataset_processing.md`, with a thesis-ready LaTeX snippet in `docs/thesis/dataset_processing_latex.tex`.

## Incremental Development Strategy

1. Establish the canonical research specification and repository conventions.
2. Design the minimum viable pipeline around dataset validation,
   preprocessing, feature encoding, train/evaluate execution, and MLflow
   tracking.
3. Implement and test the data layer before adding model complexity.
4. Add baseline models and statistical evaluation.
5. Add CapsProm and SparseCapsProm only after the pipeline is stable.
6. Add interpretability methods and thesis-oriented LaTeX reporting.

## Executable MVP

The first end-to-end sanity-check experiment uses the strict-DNA Bhandari human
promoter split, normalized 3-mer frequencies, global GC/skew descriptors,
logistic regression, and a local SQLite-backed MLflow store. From the repository
root, run:

```bash
PYTHONPATH=src .venv/bin/python -m capsprom validate-config configs/mvp_logistic.yaml
PYTHONPATH=src .venv/bin/python -m capsprom validate-data configs/mvp_logistic.yaml
PYTHONPATH=src .venv/bin/python -m capsprom run configs/mvp_logistic.yaml
```

The sampled MVP is deliberately small enough to validate configuration, data,
feature encoding, training, evaluation, provenance, and artifact logging before
full-data baselines or capsule models are introduced.

The corresponding full-data reference run is configured separately so that the
change in experimental scale remains explicit:

```bash
PYTHONPATH=src .venv/bin/python -m capsprom run configs/full_logistic.yaml
```

Its first recorded result is documented in
`docs/full_dataset_logistic_report.md`.

The first nonlinear comparison uses the same full dataset and feature contract:

```bash
PYTHONPATH=src .venv/bin/python -m capsprom run configs/full_xgboost.yaml
```

The controlled logistic-regression versus XGBoost comparison is documented in
`docs/full_xgboost_report.md`.

## Language Policy

All repository documentation, source code, comments, configuration files, and
experiment notes are written in English.
