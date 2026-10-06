# Bhandari Human Promoter Split Audit

## Purpose

This audit evaluates exact sequence duplication and normalized train--test
overlap in the strict-DNA Bhandari human promoter benchmark used by the initial
logistic-regression and XGBoost runs. It was executed before repeated-seed or
confirmatory comparisons, as required by the statistical evaluation protocol.

## Results

Table `tab:bhandari-human-overlap-audit` summarizes the exact-sequence audit.
No sequence was associated with conflicting labels, but duplication and
cross-partition overlap were substantial.

| Audit quantity | Count | Relevant proportion |
| --- | ---: | ---: |
| Training rows | 393,513 | -- |
| Unique training sequences | 230,650 | 58.61% of training rows |
| Duplicate training rows | 162,863 | 41.39% of training rows |
| Test rows | 98,375 | -- |
| Unique test sequences | 72,672 | 73.87% of test rows |
| Duplicate test rows | 25,703 | 26.13% of test rows |
| Unique sequences shared across partitions | 23,453 | 32.27% of unique test sequences |
| Training rows belonging to shared sequences | 148,656 | 37.78% of training rows |
| Test rows belonging to shared sequences | 49,060 | 49.87% of test rows |
| Conflicting-label sequences | 0 | 0% |

Table label: `tab:bhandari-human-overlap-audit`.

The audited files were identified by the following SHA-256 hashes:

- Training: `628afb0778f3d2e15a1398c410ebad9469fd45dff788c0d8815cb1939c68cd4f`
- Test: `275b1f58f2488d5c0f9938eab402babdc099f19588b54485eb950c5821185c59`

## Consequences for Existing Results

Almost half of the test rows represent sequences also present in training.
Therefore, the existing logistic-regression and XGBoost metrics cannot be
interpreted as independent estimates of generalization to unseen sequences.
They remain useful as pipeline-development checks and as measurements of the
legacy fixed split, but they are likely optimistic and must not support
confirmatory model-ranking claims.

Repeated-seed execution on the unchanged split would quantify training
variability while leaving the more important leakage problem unresolved. It is
therefore intentionally deferred.

## Required Corrective Experiment

The next dataset version must assign normalized exact-sequence groups wholly to
one partition. Conflicting labels, if found in another dataset, must be resolved
by a predeclared exclusion rule. The corrective pipeline should:

1. group records by normalized sequence before splitting;
2. preserve labels and approximate class proportions at group level;
3. generate deterministic train/test manifests with explicit seed and hashes;
4. verify zero exact-sequence overlap after splitting;
5. retain the legacy split only as a separately labeled comparability analysis;
6. rerun logistic regression and XGBoost on the leakage-controlled split before
   adding repeated seeds or more complex models.

Near-duplicate or homology-aware grouping remains a subsequent sensitivity
analysis; zero exact overlap is the minimum acceptance criterion.
