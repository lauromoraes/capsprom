# Canonical Real-Negative Fixed-Seed Baseline Results

## Status

This report summarizes the frozen seed-42 sweep over the 25 canonical v3
dataset pairs whose test outcomes were not observed during the earlier smoke
test. Logistic regression and XGBoost use the same feature representation,
partitions, and fold manifests. The sweep is a complete paired dataset analysis,
but it is not the final confirmatory result because the stochastic XGBoost
contract requires ten predeclared seeds.

## Cross-Dataset Summary

Table `tab:real-negative-fixed-seed-summary` reports the paired MCC summary.

| Quantity | Result |
| --- | ---: |
| Dataset pairs | 25 |
| Median logistic-regression MCC | 0.4942 |
| Median XGBoost MCC | 0.5532 |
| Median paired MCC difference, XGBoost minus logistic | 0.0621 |
| Bootstrap 95% CI for median difference | [0.0322, 0.0799] |
| Mean paired MCC difference | 0.0583 |
| XGBoost wins / ties / logistic wins | 21 / 0 / 4 |
| Two-sided Wilcoxon signed-rank p-value | 0.00001234 |

The effect favors XGBoost across this fixed-seed sweep. It must be re-estimated
from the predeclared ten-seed XGBoost summaries before confirmatory reporting.
Dataset-specific exact McNemar results are retained as secondary diagnostics in
the generated paired CSV and are not substituted for the primary MCC effect.

## Dataset-Level MCC

Table `tab:real-negative-fixed-seed-datasets` reports every paired MCC value.

| Dataset | Logistic | XGBoost | Difference |
| --- | ---: | ---: | ---: |
| CDBProm anabaena_sp | 0.5026 | 0.5007 | -0.0020 |
| CDBProm bacillus_amyloliquefaciens | 0.5982 | 0.6764 | 0.0783 |
| CDBProm chlamydophila_pneumoniae | 0.5217 | 0.5436 | 0.0218 |
| CDBProm corynebacterium_glutamicum | 0.4426 | 0.5499 | 0.1073 |
| CDBProm helicobacter_pylori | 0.6482 | 0.6489 | 0.0007 |
| CDBProm klebisiella_pneumoniae | 0.5480 | 0.5898 | 0.0417 |
| CDBProm mycrobacterium_tuberculosis | 0.3899 | 0.5016 | 0.1117 |
| CDBProm pseudonomas_aeruginosa | 0.4883 | 0.5587 | 0.0704 |
| CDBProm salmonella_typhimurium | 0.4732 | 0.5353 | 0.0621 |
| CDBProm streptomyces_coelicolor | 0.5569 | 0.6368 | 0.0799 |
| CDBProm synechocistis | 0.4372 | 0.5532 | 0.1160 |
| CNNProm Arabidopsis_non_tata | 0.6070 | 0.6702 | 0.0632 |
| CNNProm Arabidopsis_tata | 0.5568 | 0.6842 | 0.1275 |
| CNNProm Human_non_tata | 0.6085 | 0.6533 | 0.0448 |
| CNNProm Mouse_non_tata | 0.6930 | 0.7240 | 0.0310 |
| CNNProm Mouse_tata | 0.4942 | 0.6763 | 0.1821 |
| CNNProm Bacillus | 0.6513 | 0.6835 | 0.0322 |
| CNNProm Ecoli | 0.6814 | 0.7341 | 0.0527 |
| GraphPro Human | 0.3299 | 0.4108 | 0.0809 |
| GraphPro Mouse | 0.3667 | 0.4267 | 0.0600 |
| GraphPro bacillus_amyloliquefaciens | -0.0538 | 0.0323 | 0.0860 |
| GraphPro campylobacter_jejuni | 0.1933 | 0.1860 | -0.0074 |
| GraphPro escherichia_coli | 0.1573 | 0.1424 | -0.0150 |
| GraphPro leptospira_interrogans | 0.0784 | 0.0429 | -0.0354 |
| GraphPro rhodobacter_capsulatus | -0.0015 | 0.0653 | 0.0668 |

Generated machine-readable summaries are stored in
`outputs/reports/real_negative_baseline_batch/paired_baseline_summary.json` and
`.csv`. The summary script is versioned as
`scripts/summarize_real_negative_baselines.py`.
