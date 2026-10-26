# Audit Evidence and Validation

## Read-only evidence collected

The audit inspected Git status/history, repository inventory, `AGENTS.md`, the CapsProm skill, `specs/`, key project/data/experiment reports, active YAML contracts, requirements, dataset filenames, ignored report/state paths, remote registry, local processes, and `make status`. No experiment was rerun and no remote host was contacted.

Core commands included:

```bash
git status --short
git rev-parse HEAD
git log -8 --date=iso --pretty=format:'%h %ad %s'
make status
rg --files
find data/processed/assembled_datasets/intra_regenerated_v3_strict_dna -name '*.csv'
find outputs/reports -name 'summary.json' -o -name '*state.json'
ps -u "$(id -u)" -o pid,etimes,cmd
```

## Path validation

All repository-relative paths named as current local inputs, contracts, state, or reports in this handover were observed during the audit, except where a gap is explicitly recorded. The v4 log and exit-marker paths in `RUNNING_TASKS.md` are remote paths copied from the job registry and are not present in the local output tree. The reported missing XGBoost v2 `summary.json` is intentionally documented in `KNOWN_ISSUES.md` rather than silently invented.

## Consistency assessment

The scientific source of truth is internally coherent across project specification, eligibility manifest, evaluation protocol, GraphPro deferral, baseline consolidation, and v4 report. The stale next-action and remote-policy references were corrected in `315f5cc`; the XGBoost summary-path ambiguity remains recorded in `KNOWN_ISSUES.md`. The remote registry and roadmap agree that the only registered v4 tranche completed, while direct live remote verification remains outside this audit.

## Autonomous migration limits

A new agent can recover scientific and local operational context from this directory and commits `315f5cc` plus the handover commit. Fully autonomous migration still requires transferring ignored experiment artifacts/MLflow databases where the destination does not share storage. Remote credentials and live server state intentionally require human authorization. These are explicit safety boundaries, not missing documentation to fill with guesses.

## Post-edit validation required

Because this audit adds documentation only, run `make check`, verify all relative references, and run `make status-snapshot`. Record failures rather than modifying scientific contracts to make checks pass.
