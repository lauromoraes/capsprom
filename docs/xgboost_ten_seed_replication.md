# XGBoost Ten-Seed Replication Contract

## Purpose

The canonical v3 source-negative baseline sweep initially evaluated XGBoost at
seed 42. This replication replaces that screening estimate with a predeclared
ten-seed estimate on the same 25 confirmatory datasets. The exploratory GraphPro
`clostridium_phytofermentans` pair remains excluded because its test result was
observed during pipeline validation.

## Frozen Contracts

The seeds are `13, 29, 42, 71, 101, 137, 173, 211, 251, 293`, matching the
thesis protocol. Data, features, XGBoost hyperparameters, prediction threshold,
metrics, and test partitions are unchanged from the fixed-seed batch. The 25
existing seed-42 XGBoost runs are reused by run identifier and recorded as such
in the replication state; the other 225 combinations are executed as new MLflow
runs. State is persisted after every completed run.

Version 1 logged a complete model for every seed and is retained unchanged for
audit. Version 2 is the active contract. It uses a new state path, verifies the
scientific equivalence of every reused seed-42 configuration, preserves source
and target configuration hashes separately, writes checkpoints atomically, and
disables repeated model serialization. Configuration, data hashes, dependency
versions, predictions, fold manifests, parameters, and metrics remain tracked.

Materialize or inspect the plan with:

```bash
make replication-plan
```

Execute or resume it with:

```bash
make replication-resume
```

After all 250 entries are complete, generate the confirmatory summaries with:

```bash
make replication-summary
```

The primary dataset-level XGBoost estimate is the median MCC across seeds, with
the interquartile range as the dispersion descriptor. It is paired with the
single deterministic logistic-regression MCC for the same dataset. Across
datasets, the primary effect is the median of these paired differences, with a
bootstrap 95% interval and a two-sided Wilcoxon signed-rank test. Mean and
sample standard deviation are retained as supplementary descriptors.
