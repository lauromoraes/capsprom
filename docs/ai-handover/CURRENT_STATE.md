# Current State

## Audit snapshot

**Verified on 2026-10-26:** `make status` completed successfully. The reviewed implementation snapshot is commit `315f5cc` on branch `codex/estruturar-projeto-de-doutorado`; the subsequent handover commit contains this directory. The active dataset root, eligibility manifest, evaluation protocol, and GraphPro deferral policy were all present.

The previously dirty campaign, consolidation, GraphPro deferral, reports, status implementation, manifests, and tests were reviewed and committed together in `315f5cc`. No dataset, MLflow database, checkpoint, prediction, or generated experiment report was added to Git. The handover documentation is intentionally a separate commit so its state description can reference the implementation snapshot.

The post-correction validation passed Ruff and all 160 tests in 268.77 seconds. `make status-snapshot` was refreshed before the implementation commit.

## Verified development state

- The reproducible classical pipeline, MLflow integration, dataset validation, feature encoders, statistical comparison utilities, CapsProm model, canonical neural planner, resumable fold execution, failure retry, filesystem locking, and explainability fixtures exist with tests.
- The active exact-identity-safe build contains 26 dataset pairs, but only 18 CDBProm/CNNProm identities are eligible for confirmatory inference.
- The classical fixed-seed baseline batch completed 50/50 jobs.
- XGBoost replication v2 completed 250/250 planned jobs and has a summary. The superseded v1 state remains incomplete at 35/250 and must not be resumed by default.
- Active baseline consolidation is available at `outputs/reports/active_baseline_consolidation_v1/summary.json`.
- The bounded CapsProm v4 tranche completed five inner folds for CDBProm *Chlamydophila pneumoniae*, seed 13. Its mean validation MCC was 0.757628, sample SD 0.031603, and selected lower-median epoch 30. This is training-only evidence; external test access is recorded as false.
- `manifests/remote_jobs.json` records that tranche as completed with exit code 0 and SQLite/hash integrity checks.
- A local process listing found no evident running CapsProm, MLflow, or XGBoost worker. This does not establish remote absence.

## Main result

On 18 eligible datasets, XGBoost won 17 and logistic regression won 1. The median per-dataset difference was 0.068100 MCC (XGBoost minus logistic), with bootstrap 95% interval [0.036066, 0.092715] and two-sided Wilcoxon p=0.0000152588. This consolidation reused existing results and did not fit new models. It is the strongest currently consolidated model-comparison result, but `configs/evaluation_protocol_v3.yaml` still marks confirmatory ranking disabled.

## Confirmed next boundary

The project is preparing the 18-dataset basic-CapsProm GPU campaign. Only a bounded five-fold seed-13 tranche has been released and completed. The next bounded training-only seed must be separately released after readiness review. Final fits, external tests, embeddings, and GraphPro remain closed.

## Unrecovered or not verified

- Live state of `bioserver03` and `bioserver04` was not queried because remote policy requires explicit authorization.
- The remote v4 output tree and backup copy were not independently inspected during this audit; their status comes from local reports and registries.
- No credentials were inspected or recorded.
- The qualification thesis external path was not revalidated.
- The handover does not prove that ignored experimental outputs were copied to another machine; migration still needs an explicit artifact-transfer check.
