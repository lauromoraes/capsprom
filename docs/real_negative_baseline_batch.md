# Canonical Real-Negative Baseline Batch

## Frozen Contract

The batch contract is versioned in
`configs/real_negative_baseline_batch.yaml`. It plans logistic regression and
XGBoost on every canonical v3 CDBProm, CNNProm, and GraphPro pair using the same
3-mer-frequency, GC-content, and GC-skew representation.

The GraphPro `clostridium_phytofermentans` pair is marked exploratory because
its smoke-test outcomes were observed before the full batch was frozen. The
remaining 25 pairs produce 50 primary confirmatory runs. The two models receive
the same dataset partitions, training seed, and five-fold manifest contract.

The frozen batch configuration SHA-256 is
`634feaa35671fa91db149e21934372f36647ae4526851f56bc07658441c870bf`.

## Resumable Execution

The following command materializes and validates all 52 derived YAML files
without fitting models:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_real_negative_baselines.py
```

Execution is explicitly enabled and may be filtered or bounded:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_real_negative_baselines.py \
  --execute --tier confirmatory --model logistic_regression --max-runs 1
```

State is persisted after every successful run in
`outputs/reports/real_negative_baseline_batch/batch_state.json`. A completed run
is skipped on resumption. Changing the batch contract or any derived YAML after
state creation is rejected; a revised experiment requires a new batch name and
state path.

## Initial Confirmatory Run

The first completed confirmatory run is logistic regression on GraphPro
`bacillus_amyloliquefaciens`, MLflow run
`de6c8dbf95b24efbb142e26c3b628a9c`. Its MCC is -0.0538 and ROC-AUC is 0.4600.
This single result is not interpreted independently; it remains part of the
frozen cross-dataset batch and will be analyzed only after the planned runs and
paired procedures are complete.
