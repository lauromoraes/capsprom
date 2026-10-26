# Running Tasks and Remote Operations

## Observed state

**Verified locally on 2026-10-26:** `make status` reported zero pending remote jobs. A local process listing found no evident CapsProm/MLflow/XGBoost worker. `manifests/remote_jobs.json` contains one job, marked `completed` with exit code 0:

- ID: `capsprom-v4-cdbprom-chlamydophila-seed13-folds0-4`
- Server/directory: `bioserver03`, `/home/lauro/workspace/capsprom`
- Remote PID: 530103 (historical; do not treat as currently live)
- Contract/release: `configs/capsprom_basic_canonical_gpu_execution_v4.yaml`, `configs/capsprom_campaign_release_v3.yaml`
- Remote log (not present locally): `outputs/capsprom_basic_canonical_gpu_execution_v4/remote_jobs/seed13-folds0-4.log`
- Remote exit marker (not present locally): `outputs/capsprom_basic_canonical_gpu_execution_v4/remote_jobs/seed13-folds0-4.exit`
- State/database/hash manifest: listed in `manifests/remote_jobs.json`
- Integrity: SQLite OK and a 55-file hash manifest recorded.

**Unrecovered:** no live remote process query was made. Therefore this audit can say that no registered job is pending, not that no unregistered remote process exists.

## Safe status procedure

Only with explicit remote authorization:

1. Read `configs/capsprom_remote_usage_policy_v3.yaml` and `docs/remote_job_operations.md`.
2. Inspect the local registry first.
3. On the named host, check the exit marker, log tail, `plan_state.json`, process identity, disk space, and SQLite integrity without modifying them.
4. Compare the remote immutable contract/config/data hashes with local copies.
5. Mark completion only when the process is absent, exit code is zero, all released jobs are finished, state is internally consistent, and integrity/hash checks pass.

## Recovery/restart rule

Do not relaunch the completed command. For a failed or interrupted released fold, use the repository's resume path so the existing MLflow child run and durable neural state are reused. Never delete state, change a used YAML contract, substitute a fold manifest, or create a second output root to bypass a lock. If integrity is uncertain, stop and preserve logs/state for diagnosis.

## Next operational task

The readiness implementation is preserved in `315f5cc` and passed the full local suite. Review the completed v4 tranche before drafting any further release. A further bounded training-only seed requires a new explicit release. Final refits, external tests, embeddings, and the full campaign remain blocked.
