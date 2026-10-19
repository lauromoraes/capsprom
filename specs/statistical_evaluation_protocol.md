# Statistical Evaluation Protocol

## Purpose and Status

This specification defines the confirmatory evaluation contract for CapsProm
baselines and proposed models. It separates exploratory development from
confirmatory comparison, prevents test-set feedback from driving model choices,
and makes effectiveness, calibration, efficiency, robustness, and statistical
uncertainty reproducible.

The completed Bhandari human promoter logistic-regression and XGBoost runs are
development baselines. Their test results have already been observed and may be
reported as fixed-split reference results, but they must not be described as a
blind confirmatory comparison.

## Analysis Tiers

### Development Tier

The deduplicated Bhandari human shuffle-control split is the initial development
benchmark. It may be used for pipeline verification, debugging, feature
ablation design, and computational feasibility. Its negative class consists of
deterministic mononucleotide shuffles rather than genomic non-promoters. Every
use of its test partition must be recorded, and no subsequent design choice may
be justified as though that partition remained unseen. The contaminated legacy
Bhandari split is retained only for provenance and historical comparability.

### Confirmatory Tier

Confirmatory comparisons use all eligible strict-DNA within-source train/test
pairs. A dataset is eligible when both models can consume its representation,
both labels occur in train and test, and the data audit passes. Comparisons
between two models use the intersection of their eligible datasets. The model
specification, feature set, search space, training budget, and evaluation code
must be frozen before test predictions are generated.

Dataset-level results, rather than individual sequences pooled across sources,
are the primary units for cross-dataset inference. This prevents the largest
source datasets from dominating conclusions about general performance.

The first batch audit found that none of the 26 CDBProm, CNNProm, and GraphPro
pairs passes the exact-sequence integrity criteria. Their current fixed
partitions are therefore development/provenance inputs only. Confirmatory use
requires corrected group-safe partitions that retain the source-provided
non-promoter examples.

## Data Integrity and Leakage Controls

Before confirmatory training, each dataset pair must be audited for:

- exact duplicate sequences within and across partitions;
- identical sequences carrying conflicting labels;
- train/test overlap after sequence normalization;
- class counts, sequence length, and strict DNA alphabet compliance;
- source-specific identifiers or groups that could induce dependence;
- near-duplicate or homologous clusters when a defensible grouping method is
  available.

Fixed benchmark partitions are preserved for comparability. If cross-partition
duplicates or groups are found, the primary report must quantify them and add a
sensitivity analysis that removes or groups affected records. Any deduplication
rule is learned and frozen without examining model performance on the test set.

## Model Development and Hyperparameter Selection

All preprocessing and feature-selection operations that can learn from data
must be fitted on training data only. Hyperparameters are selected with a fixed
five-fold stratified cross-validation manifest generated from the training
partition using seed 42. The same folds and an explicitly equal search budget
are used for models being compared whenever their training contracts permit it.

The test partition is evaluated only after the model configuration is locked.
No test metric may be used for early stopping, threshold selection, calibration,
feature selection, or hyperparameter tuning.

## Replication Policy

Stochastic models use the following ten predeclared seeds:

```text
13, 29, 42, 71, 101, 137, 173, 211, 251, 293
```

Every stochastic component, including initialization, sampling, data-loader
ordering, and model-specific randomness, must receive the run seed. Deterministic
models are fitted once per locked configuration and are not duplicated to create
pseudo-replicates. For stochastic models, dataset-level tables report the median
and interquartile range across seeds, with mean and standard deviation retained
as supplementary descriptors.

## Prediction and Threshold Contract

Each evaluated record must produce a positive-class score, a probability when
the model supports probabilistic interpretation, and a binary prediction. The
primary classification threshold is 0.5 and is fixed before test evaluation.
An alternative threshold optimized on out-of-fold training predictions may be
reported only as a separately labeled secondary analysis; it must be frozen
before application to the test partition.

If calibration is applied, sigmoid or isotonic calibration is fitted only from
training-derived out-of-fold predictions. Raw and calibrated models are treated
as distinct locked conditions. The test partition is never used to fit a
calibrator.

## Outcomes

### Primary Outcome

Matthews correlation coefficient (MCC) is the single primary effectiveness
outcome because it incorporates all confusion-matrix cells and remains
informative under class imbalance.

### Secondary Effectiveness Outcomes

Secondary outcomes are ROC-AUC, average precision, sensitivity (recall),
specificity, balanced accuracy, accuracy, precision, and F1. ROC-AUC and average
precision are calculated from continuous scores; thresholded metrics use the
predeclared threshold contract.

### Calibration Outcomes

Calibration is described by Brier score, binary log-loss, and expected
calibration error (ECE) with ten equal-frequency bins. Reliability diagrams
must show bin counts and the identity line. Because ECE is bin-dependent, it is
descriptive rather than a sole basis for model selection.

### Efficiency Outcomes

Feature encoding, training, calibration, and inference times are measured
separately. Timing comparisons use one untimed warm-up followed by three timed
runs on the same hardware and resource settings; the median and interquartile
range are reported. Peak resident memory, software versions, processor/GPU
identity, thread count, and input sample count are recorded.

## Uncertainty and Paired Comparisons

For each dataset and locked run, point estimates receive 95% confidence
intervals from 10,000 stratified bootstrap resamples of the test records. The
same resampled indices are applied to every model in a comparison. If biological
or source groups are available, a group bootstrap replaces record-level
resampling. Record-level intervals must be qualified when sequence dependence
cannot be modeled.

Within a dataset, the primary pairwise comparison is the paired difference in
MCC. Its effect estimate and 95% paired-bootstrap confidence interval are
reported. A two-sided paired randomization test with 10,000 swaps provides the
confirmatory p-value. McNemar's exact test is retained as a secondary analysis
of discordant classification errors, not as a replacement for the MCC effect
estimate.

Across datasets, each dataset contributes one paired summary per model. When at
least ten eligible datasets are available, the primary cross-dataset comparison
uses a two-sided Wilcoxon signed-rank test on dataset-level MCC differences and
reports the median paired difference with a confidence interval. Win/tie/loss
counts are descriptive supplementary results.

The family-wise significance level is 0.05. Holm correction is applied across
all confirmatory model-pair hypotheses for the primary outcome. Secondary
metric p-values are exploratory and are reported with effect sizes and
confidence intervals rather than used to multiply claims of superiority.

## Robustness and Sensitivity Analyses

Robustness reporting includes performance by dataset source, organism domain,
class-imbalance range, and random seed. Predeclared sensitivity analyses cover
cross-partition duplicate removal, raw versus calibrated probability outputs,
and the fixed 0.5 versus training-selected threshold. Post hoc analyses must be
labeled exploratory.

## Required Provenance and Artifacts

Each MLflow parent experiment and child run must record:

- protocol version and YAML hash;
- dataset paths, SHA-256 hashes, source, domain, and partition counts;
- data-audit report and fold-manifest hash;
- feature and model configuration, implementation version, and run seed;
- software, hardware, accelerator, and thread settings;
- row identifier, true label, score/probability, and prediction for every test
  record;
- confusion matrix and all effectiveness, calibration, and efficiency metrics;
- bootstrap/randomization seeds and comparison outputs;
- fitted model, calibrator when applicable, and thesis-ready tables/figures.

Prediction artifacts must use stable row identifiers and must not expose raw
sequences unnecessarily. Any figure or table promoted to the thesis follows
the repository caption, label, and preceding-reference requirements.

## Reporting Rules

Reports distinguish exploratory, development, and confirmatory results. They
state the eligible dataset set, exclusions, number of seeds, missing or failed
runs, and whether intervals are record- or group-based. Claims emphasize effect
sizes and uncertainty. A p-value below the corrected threshold is not described
as biologically important without a corresponding effect-size interpretation.

## Implementation Gates

The protocol becomes executable in the following order:

1. Add prediction persistence and stable row identifiers. Implemented.
2. Add the missing effectiveness and calibration metrics. Implemented.
3. Generate and hash the five-fold training manifests. Implemented.
4. Implement repeated-seed orchestration and MLflow parent/child runs.
5. Implement paired bootstrap, randomization, Holm correction, and
   cross-dataset aggregation.
6. Complete cross-dataset leakage audits, reliability diagrams, and
   thesis-ready reports. Exact-sequence auditing and the Bhandari corrective
   report are implemented; the broader cross-dataset stage remains pending.

No confirmatory model ranking should be published before these gates are
implemented and validated with synthetic or fixture data.
