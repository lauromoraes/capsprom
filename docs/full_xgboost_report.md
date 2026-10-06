# Full-Dataset XGBoost Report

## Purpose

This experiment introduces the first nonlinear baseline under the unified
CapsProm pipeline. It preserves the full-dataset logistic-regression split,
feature representation, random seed, evaluation metrics, and provenance
contract so that the model family is the principal controlled change.

## Experimental Setup

The model used all 393,513 strict-DNA Bhandari human promoter training records
and all 98,375 fixed test records. Inputs comprised 64 normalized 3-mer
frequencies, global GC content, and global GC skew. The XGBoost classifier used
300 trees, maximum depth 4, learning rate 0.05, row and column subsampling of
0.9, and the histogram tree method.

The exact specification is stored in `configs/full_xgboost.yaml`. The local
SQLite-backed MLflow experiment `capsprom-baselines` contains the dataset
hashes, configuration, model hyperparameters, sample counts, feature metadata,
timings, metrics, run summary, and fitted booster. The successful run identifier
was `21a7839addd04a598058f7effcd55d17`.

## XGBoost Results

Table `tab:full-xgboost-results` reports the legacy fixed-split evaluation. A
later exact-sequence audit found that 49.87% of test rows belong to sequences
also present in training. The values are therefore potentially optimistic
development results and do not establish independent generalization or
statistical superiority. See `docs/bhandari_human_data_audit.md`.

| Metric | Value |
| --- | ---: |
| Accuracy | 0.8234 |
| Precision | 0.8288 |
| Recall | 0.8152 |
| F1 | 0.8219 |
| ROC-AUC | 0.9061 |
| Matthews correlation coefficient | 0.6468 |
| Feature encoding time | 13.6616 s |
| Model training time | 6.9311 s |

Table label: `tab:full-xgboost-results`.

## Comparison with Logistic Regression

Table `tab:logistic-versus-xgboost` compares both full-data baselines. XGBoost
improved every effectiveness metric under the shared feature and evaluation
contract, at the cost of a modest increase in training time.

| Metric | Logistic regression | XGBoost | Difference |
| --- | ---: | ---: | ---: |
| Accuracy | 0.7807 | 0.8234 | +0.0427 |
| Precision | 0.7803 | 0.8288 | +0.0485 |
| Recall | 0.7813 | 0.8152 | +0.0338 |
| F1 | 0.7808 | 0.8219 | +0.0411 |
| ROC-AUC | 0.8628 | 0.9061 | +0.0433 |
| Matthews correlation coefficient | 0.5613 | 0.6468 | +0.0855 |
| Training time | 5.3647 s | 6.9311 s | +1.5664 s |

Table label: `tab:logistic-versus-xgboost`.

## Reproducibility Note

An initial XGBoost attempt completed training and evaluation but failed during
model serialization because the MLflow scikit-learn flavor rejected XGBoost's
internal model types. That run remains in MLflow with failed status for audit.
The pipeline now selects the native MLflow XGBoost flavor, and the successful
run persisted the fitted booster without weakening serialization safety.

## Interpretation and Next Gate

XGBoost performed better on the legacy split, but leakage prevents this
difference from supporting a generalization claim. The next methodological gate
is a deterministic group-aware repartition with zero exact-sequence overlap,
followed by rerunning both reference models. Repeated seeds and statistical
comparison remain deferred until the corrected split passes the audit.
