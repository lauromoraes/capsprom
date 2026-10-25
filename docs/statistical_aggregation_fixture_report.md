# Statistical Aggregation Fixture Report

## Scope

This report records the synthetic validation of the evaluation-protocol v3
aggregation rules. The fixtures contain invented MCC values and binary
predictions only. They do not read real test predictions and do not support a
model-performance or biological conclusion.

## Validated behavior

The fixture uses the ten locked seeds and constructs eleven synthetic datasets.
Two datasets share one dependency cluster, while the remaining nine datasets
belong to independent clusters. The implementation produces eleven dataset
effects but only ten inferential cluster effects. The shared cluster contributes
the median of its two dataset effects, demonstrating that related variants do
not inflate the effective sample size.

Additional fixtures verify that missing, unexpected, and duplicate seeds fail
before aggregation; Wilcoxon inference is withheld below ten dependency
clusters; the stratified paired bootstrap is reproducible for a frozen random
seed and applies each sampled record index to both models and all seeds; and
Holm-adjusted p-values are monotone in ordered raw p-values.

## Outcome and limitations

The fixture criteria in `specs/statistical_evaluation_protocol.md` pass. This
closes the synthetic statistical-aggregation validation gate only. The current
implementation does not make folds or seeds independent observations, does not
read held-out outcomes, and does not authorize confirmatory ranking. Group-level
bootstrap for datasets with defensible biological groups and the final
prediction-report integration remain separate implementation tasks. The
secondary paired-randomization and exact McNemar procedures and the multi-model
Friedman path also remain pending; none is silently substituted by the
cluster-level two-model test validated here.
