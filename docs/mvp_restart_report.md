# MVP Restart Experiment Report

## Purpose

The project restart milestone verifies the complete path from a versioned YAML
specification to strict dataset loading, feature encoding, model training,
evaluation, MLflow tracking, and persisted run artifacts. This is an
infrastructure sanity check rather than a final baseline comparison.

## Experimental Setup

The run used the strict-DNA Bhandari human promoter train/test split and the
configuration in `configs/mvp_logistic.yaml`. Deterministic stratified samples
of 4,000 training sequences and 2,000 test sequences were selected with random
seed 42. Inputs combined normalized 3-mer frequencies with global GC content
and GC skew. The classifier was class-weighted logistic regression using the
liblinear solver.

Dataset identity, SHA-256 hashes, sample counts, feature blocks, parameters,
metrics, timings, the fitted model, the exact configuration, and a JSON run
summary were recorded in the local SQLite-backed MLflow store. The run identifier
was `7f8624614f2946188e69ae78332e6b13`.

## Results

Table `tab:mvp-restart-results` reports the first end-to-end pipeline result.
The values establish that the pipeline can learn a non-trivial signal and that
the selected low-cost feature blocks are suitable for infrastructure testing.
They must not be presented as full-data baseline performance.

| Metric | Value |
| --- | ---: |
| Accuracy | 0.7635 |
| Precision | 0.7692 |
| Recall | 0.7530 |
| F1 | 0.7610 |
| ROC-AUC | 0.8476 |
| Matthews correlation coefficient | 0.5271 |
| Feature encoding time | 0.1511 s |
| Model training time | 0.1965 s |

Table label: `tab:mvp-restart-results`.

## Interpretation and Next Gate

The result confirms the executable MVP contract, but it does not replace a
formal experiment. The next gate is to retain the same fixed split, provenance,
metrics, and MLflow contract while running logistic regression on the complete
dataset. XGBoost should then be introduced as the first comparative baseline.
Runtime, memory use, class imbalance, calibration, repeated seeds, and
statistical comparison must be addressed before claims are included in the
thesis results chapter.
