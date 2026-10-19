# AI-Assisted Development Workflow

## Purpose

This workflow keeps AI-assisted changes small, reviewable, and scientifically
reproducible. Repository code and documentation define the intended method;
versioned configurations define frozen experimental contracts; local MLflow
artifacts record executions; and compact manifests communicate current state
without committing datasets or model artifacts.

## Required Change Sequence

1. Read the relevant specification and roadmap entry.
2. Record a short design note before changing an experimental stage.
3. Create a new configuration and state path when a frozen contract changes.
4. Add focused tests and run `make check`.
5. Materialize the plan before starting a long experiment.
6. Persist state atomically after every run and update the versioned status
   snapshot at meaningful checkpoints.
7. Update the experiment report and thesis text only after the declared summary
   is complete.

## Long-Running Experiments

Long runs must be resumable and must never depend on uncommitted source changes.
Generated state, predictions, and MLflow artifacts remain local. A compact
versioned snapshot records the contract name, configuration hash, counts, and
next action. Changing data, features, models, seeds, output policy, or inference
requires a new contract version rather than mutation of an existing state.

## XGBoost Replication Version 2

The first replication contract logged a complete MLflow model for every seed.
Because model serialization dominated runtime while predictions and provenance
were already retained, version 2 disables repeated model logging. It preserves
the original contract for audit and starts from a new state path. Reused seed-42
runs are accepted only after their data, feature, model, evaluation, and seed
fields are proven equivalent to the new target configuration. Source and target
configuration hashes are stored separately.
