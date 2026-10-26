# Experiments

## Experiment ledger

| Experiment | State | Evidence and result | Safe next action |
| --- | --- | --- | --- |
| MVP/full logistic | Completed exploratory baseline | `configs/mvp_logistic.yaml`, `configs/full_logistic.yaml`, `docs/full_dataset_logistic_report.md`, MLflow/run outputs | Preserve; do not rerun for handover |
| Full XGBoost | Completed exploratory comparison | `configs/full_xgboost.yaml`, `docs/full_xgboost_report.md` | Preserve |
| Fixed-seed real-negative batch | 50/50 completed | `configs/real_negative_baseline_batch.yaml`, `outputs/reports/real_negative_baseline_batch/batch_state.json` | Reuse only under hash-equivalence rules |
| XGBoost replication v1 | Superseded/incomplete: 35/250 | `configs/xgboost_ten_seed_replication.yaml`, state file | Do not resume by default |
| XGBoost replication v2 | 250/250 completed | `configs/xgboost_ten_seed_replication_v2.yaml`, `outputs/reports/xgboost_ten_seed_replication_v2/replication_state.json`, `docs/xgboost_ten_seed_replication.md` | Preserve and reuse |
| Active baseline consolidation | Completed, no new fits | `configs/active_baseline_consolidation_v1.yaml`, `outputs/reports/active_baseline_consolidation_v1/summary.json` | Use as current classical comparison |
| CapsProm optimizer controls | Completed training-only development | `docs/capsprom_mcc_training_audit.md` and per-seed YAML files | Frozen development choice; no test claim |
| Canonical CPU plan/fixtures | Implemented and fixture-tested | `configs/capsprom_basic_canonical_v1.yaml`, canonical neural tests | Preserve |
| GPU v4 bounded tranche | Five folds completed for Chlamydophila seed 13 | `configs/capsprom_basic_canonical_gpu_execution_v4.yaml`, `configs/capsprom_campaign_release_v3.yaml`, `docs/capsprom_v4_seed13_training_report.md`, remote registry | Review readiness; a new release is required for more work |
| Full 18-dataset CapsProm campaign | Planned and blocked | evaluation/canonical contracts and plan state | Do not execute without bounded release |
| Final refits/external tests | Not released | gates remain closed | Keep structurally unavailable |
| Embedding/multi-head ablations | Not implemented/executed | status documented in `docs/capsprom_embedding_ablation_status.md` | Predeclare only after baseline boundary is stable |
| GraphPro reconstruction/training | Deferred | `configs/graphpro_deferral_policy_v1.yaml` | No work without explicit decision |

## Consolidated classical result

`outputs/reports/active_baseline_consolidation_v1/summary.json` records 18 datasets and 10 XGBoost seeds. XGBoost wins 17/18; median XGBoost-minus-logistic MCC is 0.068100, mean 0.067286, bootstrap 95% interval [0.036066, 0.092715], Wilcoxon statistic 1.0, two-sided p=1.52587890625e-05. The per-dataset rows include all MLflow run IDs and seeds.

## CapsProm tranche result

The five v4 folds completed on their first attempts. Best epochs were 31, 41, 7, 30, and 25; the lower-median rule selects 30. One fold reached the 50-epoch ceiling and is a monitoring signal, not authorization to alter the budget. No external-test access occurred.

## Reproduction rule

Before reusing a run, verify configuration SHA-256, dataset hashes, eligibility and dependency manifests, code/runner contract, fold manifest, output/state root, and MLflow identifiers. If any experimental input, model, seed, output policy, or inference rule changes, create a successor YAML and state path.
