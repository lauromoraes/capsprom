# Active Classical-Baseline Consolidation

## Scope

This report consolidates already completed logistic-regression and ten-seed
XGBoost results for the current 18-dataset confirmatory scope. The scope is
defined independently of model outcomes by
`configs/dataset_eligibility_manifest_v1.yaml` and contains 11 CDBProm and
seven CNNProm datasets. GraphPro results remain historical exploratory
provenance and are not included. No model was fitted for this consolidation.

The immutable consolidation contract is
`configs/active_baseline_consolidation_v1.yaml`. It binds the eligibility
manifest and the completed 25-dataset replication summary by SHA-256, then
selects only the eligible source prefixes. Machine-readable results are written
to `outputs/reports/active_baseline_consolidation_v1/`.

## Result

Across the 18 eligible datasets, the median paired difference between ten-seed
median XGBoost MCC and deterministic logistic-regression MCC is 0.0681 in favor
of XGBoost. The paired dataset bootstrap 95% interval for the median is
[0.0361, 0.0927]. XGBoost wins on 17 datasets and logistic regression wins on
one, with no ties. The two-sided Wilcoxon signed-rank p-value is 0.00001526.

These estimates replace the earlier 25-dataset aggregate as the active
classical reference. The earlier aggregate remains valid only for its recorded
historical scope and is not reinterpreted as confirmatory evidence.

## Next comparison

The next model family is the basic two-output CapsProm under
`configs/capsprom_basic_canonical_gpu_execution_v4.yaml`, which lists only the
18 eligible datasets and requires a separate bounded release. The first
five-fold training-only release is complete, but every additional inner fold,
final fit, external test, and embedding job remains closed. Any further
expensive execution must use the persistent remote-job protocol and a new
explicitly bounded training-only release.
