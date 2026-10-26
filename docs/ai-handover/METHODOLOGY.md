# Methodology

## Confirmed protocol

The active protocol is `configs/evaluation_protocol_v3.yaml`, backed by `specs/statistical_evaluation_protocol.md`. Its status is `design_locked_execution_blocked`; confirmatory ranking is disabled.

- Primary metric: Matthews correlation coefficient (MCC).
- Secondary metrics: ROC-AUC, average precision, specificity, balanced accuracy, accuracy, precision, recall, and F1.
- Selection: deterministic stratified five-fold training-only selection, fold seed 42.
- Neural epoch rule: lower median fold-best epoch per dataset/model/configuration/seed.
- Stochastic seeds: 13, 29, 42, 71, 101, 137, 173, 211, 251, 293.
- Failed seeds are reported, not replaced.
- Primary threshold is 0.5; any training-selected threshold is secondary.
- Predictions require stable row identifiers and persistent row-level output.
- Calibration is fit only from out-of-fold training predictions.
- Within-dataset effects are paired; folds and seeds are not independent test observations.
- Across-dataset inference uses the 14 audited dependency clusters, cluster-median effects, Wilcoxon/Friedman procedures, and Holm correction for predeclared primary families.
- Test outcomes cannot drive selection.

## Basic CapsProm development decision

Training-only controls selected a stability-first setting: learning rate 0.0001, maximum 30 epochs, patience 15, decoder disabled, and the compatible runner contract. The five-epoch warm-up and tested exponential decay were rejected; 60 epochs did not improve the 30-epoch checkpoints. This is a development decision based on inner-training stability, not external-test performance.

The canonical model currently accepts one-hot k=1 tensors. Trainable embeddings, physicochemical initialization, multi-head variants, attention, and SparseCapsProm are separate future model identities. They cannot silently replace the baseline.

## Tracking and reproducibility

Each run must preserve config and dataset hashes, fold manifests, model/implementation versions, feature blocks, seeds, hardware, metrics, predictions, artifacts, and MLflow run IDs. Neural campaigns use deterministic parent/child identities, atomic state, per-fold locks, resumable checkpoints, and a failure/retry policy. Scientific or statistical changes require a new YAML version and state root.

## Interpretation rule

Use these categories in reports: development/feasibility, exploratory, or confirmatory. Infrastructure fixtures establish implementation behavior, not biological evidence. Inner-validation results cannot be reported as external effectiveness.
