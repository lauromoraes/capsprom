# Exploratory Real-Negative Smoke Test

## Purpose

This smoke test verifies that the canonical v3 data can pass through YAML
configuration, feature encoding, fold-manifest generation, model fitting,
prediction persistence, metric calculation, and MLflow tracking. It is not a
confirmatory model comparison because the test results have been observed.

## Dataset and Features

- Dataset: GraphPro `clostridium_phytofermentans`.
- Training: 402 promoters and 345 non-promoters.
- Test: 101 promoters and 86 non-promoters.
- Features: normalized 3-mer frequencies, global GC content, and GC skew.
- Seed: 42.

## Results

Table `tab:real-negative-smoke-results` reports the exploratory results.

| Metric | Logistic regression | XGBoost |
| --- | ---: | ---: |
| MCC | 0.1158 | -0.0245 |
| ROC-AUC | 0.5748 | 0.5091 |
| Average precision | 0.5940 | 0.5759 |
| Balanced accuracy | 0.5578 | 0.4880 |
| Brier score | 0.2466 | 0.2866 |
| Log-loss | 0.6864 | 0.7846 |

MLflow run identifiers:

- logistic regression: `4d94852cb8ea4e0db3fba1b4caa24e93`;
- XGBoost: `cc70a008d63045a2a289a3b055371c01`.

Both runs used the identical five-fold training manifest, whose SHA-256 is
`ccab6f311a7f3ad6d940b599094dca407e8bd6407d7d41e199a8b08e4e90e84d`.

The low and unstable effectiveness estimates are useful as a pipeline check but
must not drive model selection. Confirmatory baselines require frozen search
spaces, all eligible datasets, and the predeclared replication and paired
comparison procedures.
