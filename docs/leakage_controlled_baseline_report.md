# Leakage-Controlled Baseline Report

## Scope

This report evaluates logistic regression and XGBoost on the deduplicated,
group-split Bhandari human shuffle-control dataset. Both models use the same 66
features: normalized 3-mer frequencies, global GC content, and GC skew.

Table `tab:leakage-controlled-baselines` reports the first fixed-seed results.
Unlike the legacy split, every test sequence is absent from training. The
negative class remains synthetic, so these values quantify discrimination from
mononucleotide shuffles rather than from real genomic non-promoters.

| Metric | Logistic regression | XGBoost |
| --- | ---: | ---: |
| Accuracy | 0.7913 | 0.8211 |
| Precision | 0.7924 | 0.8291 |
| Recall | 0.7894 | 0.8088 |
| Specificity | 0.7932 | 0.8333 |
| F1 | 0.7909 | 0.8189 |
| ROC-AUC | 0.8727 | 0.9049 |
| Average precision | 0.8744 | 0.9102 |
| Matthews correlation coefficient | 0.5826 | 0.6423 |
| Brier score | 0.1486 | 0.1258 |
| Log-loss | 0.4608 | 0.3951 |
| Expected calibration error | 0.0572 | 0.0311 |

Table label: `tab:leakage-controlled-baselines`.

The MLflow run identifiers are `087af681966b474f9259e452028e4a7a` for logistic
regression and `be88eb2442864393b66f6fb23cc67542` for XGBoost. Both runs include
the configuration, dataset hashes, row-level predictions, fold manifest,
confusion matrix, metrics, and fitted model.

## Interpretation

XGBoost remains stronger under the corrected exact-sequence split, but this is
a single-seed development comparison. The small change relative to the legacy
metrics indicates that the shuffle-control task contains a strong sequence-order
signal even after leakage removal. It does not rehabilitate the legacy split or
establish performance against biological non-promoters.

Repeated seeds and paired uncertainty estimates may now be applied to this
shuffle-control dataset. A separate benchmark with provenance-backed genomic
non-promoters remains necessary for the thesis's biological generalization
claims.
