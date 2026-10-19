# Near-Duplicate Sensitivity Report

## Scope

This report evaluates residual train/test dependence after the canonical v3
exact-sequence correction for the 26 CDBProm, CNNProm, and GraphPro pairs. It
uses Hamming distance on fixed 81 bp sequences and does not remove records
automatically.

## Method

For every test sequence, the audit searches for training neighbors at Hamming
distance thresholds 1, 2, 4, and 8. These correspond to minimum identities of
98.77%, 97.53%, 95.06%, and 90.12%, respectively. An exact pigeonhole block
index guarantees that every pair within the largest threshold is considered.
Counts indicate test sequences with at least one qualifying training neighbor.

## Results

Table `tab:near-duplicate-sensitivity-summary` summarizes the complete audit.

| Threshold | Minimum identity | Test sequences | Percentage of 35,991 |
| --- | ---: | ---: | ---: |
| Hamming <= 1 | 98.77% | 17 | 0.047% |
| Hamming <= 2 | 97.53% | 32 | 0.089% |
| Hamming <= 4 | 95.06% | 49 | 0.136% |
| Hamming <= 8 | 90.12% | 96 | 0.267% |

All 96 test sequences at distance at most 8 have a neighbor with the same
label. None has a training neighbor with the opposite label within that
threshold. Ten of the 26 dataset pairs contain at least one such neighbor; the
remaining 16 contain none.

## Interpretation

The v3 datasets satisfy the exact-identity eligibility rules, while a small
residual near-duplicate dependence remains. Primary experiments retain the
frozen v3 partitions. A predeclared sensitivity analysis should repeat the
dataset-level evaluation after excluding affected test rows or after a
similarity-clustered repartition, without using test outcomes for model
selection.

The deterministic near-duplicate audit identifier is
`f3918a8c91b6ebd3e930b019b9b1183871fed3f5ca7910c73079e900146f30ea`.
