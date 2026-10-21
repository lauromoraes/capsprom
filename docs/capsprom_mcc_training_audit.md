# CapsProm MCC and Training-Regime Audit

## Scope and evidence boundary

This audit is local and does not contact either execution host. The ten current
fold records below are confirmed only from the versioned roadmap and canonical
protocol notes. Their remote plan state, MLflow database, epoch curves, and row
predictions are not present locally and were therefore not independently
revalidated in this audit.

The older development runs are local training diagnostics on the GraphPro
`clostridium_phytofermentans` pair. Stored confusion counts reproduce their
recorded MCC exactly with scikit-learn. Smoke states without confusion counts
cannot be independently recalculated. No local out-of-fold row predictions are
available for the current canonical folds, so a pooled out-of-fold MCC cannot
be reconstructed.

## Why the MCC values differ

The older values and current values do not estimate the same quantity. Older
runs used one exploratory GraphPro dataset, usually a fixed 20% inner holdout,
747 or fewer rows, and several different decoder, routing, learning-rate, seed,
and epoch contracts. The current values use manifest-defined five-fold inner
validation on the 646-row canonical v3 CDBProm Chlamydophila training set.
They are per-fold MCC values; the reported seed summaries are arithmetic means
of those five values, not MCC calculated once over concatenated out-of-fold
predictions.

Both regimes define label `1` as the positive promoter class and calculate MCC
with `sklearn.metrics.matthews_corrcoef`. Basic CapsProm predicts the index of
the larger raw capsule length. Its reported positive score is
`a1 / (a0 + a1)`, which gives the same decision as a 0.5 threshold except for
an exact tie; exact ties are assigned to class 0. Checkpoint selection is
lexicographic: maximize inner-validation MCC and, on an exact MCC tie, minimize
inner-validation loss.

Consequently, the change from historical MCC values near 0.2 (including some
single-class MCC-zero failures) to current values near 0.7--0.8 cannot be
attributed to one code change. Dataset identity, sample count, split method,
and training contracts all changed. Synthetic fixtures validate mechanics only
and provide no predictive or biological evidence.

## Current locally documented folds

| Seed | Fold | Epochs run | Ceiling | Best epoch | Stop reason | Inner-validation MCC |
|---:|---:|---:|---:|---:|---|---:|
| 13 | 0 | 30 | 30 | 28 | maximum epochs | 0.8008534347 |
| 13 | 1 | 30 | 30 | 26 | maximum epochs | 0.7674922078 |
| 13 | 2 | 22 | 30 | 7 | patience 15 | 0.7162640491 |
| 13 | 3 | 30 | 30 | 30 | maximum epochs | 0.7519230769 |
| 13 | 4 | 30 | 30 | 25 | maximum epochs | 0.7476919615 |
| 29 | 0 | 30 | 30 | 23 | maximum epochs | 0.8157708706 |
| 29 | 1 | 23 | 30 | 8 | patience 15 | 0.7371216163 |
| 29 | 2 | 30 | 30 | 23 | maximum epochs | 0.7213272630 |
| 29 | 3 | 20 | 30 | 5 | patience 15 | 0.7519230769 |
| 29 | 4 | 30 | 30 | 21 | maximum epochs | 0.6939441501 |

Seed 13 fold 3 selected its best checkpoint at the epoch-30 ceiling. This is a
ceiling contact, not evidence of convergence. Seed 13 fold 0 also selected a
late epoch (28). Without the remote epoch curves, stabilization cannot be
assessed locally. A larger-budget sensitivity study must therefore be a new
versioned contract and must be decided without external-test outcomes.

The predeclared lower-median rule selects 26 epochs for the seed-13 full refit
from `[28, 26, 7, 30, 25]`, and 21 epochs for seed 29 from
`[23, 8, 23, 5, 21]`. These selections do not authorize either final fit.

## Historical controls relevant to the epoch ceiling

The local fixed-rate, decoder-disabled 30-epoch diagnostic selected epochs 17,
16, 23, 22, and 17 for seeds 23, 29, 31, 37, and 42. Corresponding 60-epoch
controls stopped at epochs 32, 31, 38, 37, and 32 under patience 15 and
reproduced the same selected checkpoints and MCC values. This is evidence that
30 epochs did not limit those historical GraphPro diagnostics. It is not
evidence that the current CDBProm fold reaching epoch 30 has converged.

## Required evidence before confirmatory interpretation

- Restore or export current per-epoch histories and row-level fold predictions.
- Recalculate every fold MCC from immutable predictions and confusion counts.
- Calculate pooled out-of-fold MCC separately and label it as a different
  aggregation from the mean fold MCC.
- Record a ceiling-contact review before authorizing the next campaign tranche.
- Keep external test results unavailable for all of these decisions.
