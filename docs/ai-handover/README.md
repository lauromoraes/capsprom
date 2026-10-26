# CapsProm AI Handover

Audit date: 2026-10-26 (America/Sao_Paulo). The reviewed implementation, bounded campaign, reports, and operational state were preserved in commit `315f5cc` (`Record bounded CapsProm campaign and active baseline scope`) on branch `codex/estruturar-projeto-de-doutorado`. This handover is versioned by the subsequent commit that first contains `docs/ai-handover/`; use `git log -1 -- docs/ai-handover/README.md` to recover its full identifier after migration.

This directory is the entry point for resuming CapsProm without the preceding AI conversation. It summarizes verified repository state and links to the versioned specifications and artifacts that remain authoritative. It does not replace `specs/`, immutable YAML contracts, state files, or MLflow records.

## Resume order

1. Read `AGENTS.md`, this file, `AI_CONTEXT.md`, and `CURRENT_STATE.md`.
2. Use `PROJECT_INDEX.md` to route selective inspection.
3. Run `git status --short`, `git rev-parse HEAD`, and `make status`; compare them with this audit. The handover checkpoint should be clean unless the environment generated a new status timestamp.
4. Read `specs/project_spec.md`, `specs/statistical_evaluation_protocol.md`, and `specs/capsprom_canonical_experiment.md` before changing scientific behavior.
5. Check `RUNNING_TASKS.md` before contacting a server or launching work.
6. Read `ROADMAP.md` and continue only an explicitly released action.
7. Use `RESUME_PROMPT.md` to initialize another AI session.

## Document map

- `PROJECT_OVERVIEW.md`: research question, hypotheses, and scope.
- `PROJECT_INDEX.md`: compact routing map, verified drift, and prioritized refactoring queue.
- `CURRENT_STATE.md`: verified state, results, and evidence classes.
- `ARCHITECTURE.md`: code layout and processing flow.
- `DATASETS.md`: data inventory, provenance, and eligibility.
- `METHODOLOGY.md`: scientific protocol and locked decisions.
- `EXPERIMENTS.md`: experiment ledger and artifact links.
- `DECISIONS.md`: chronological decision record.
- `ENVIRONMENT.md`: local and remote environments.
- `RUNNING_TASKS.md`: process/job status and safe operations.
- `KNOWN_ISSUES.md`: contradictions, risks, and unknowns.
- `ROADMAP.md`: prioritized continuation plan.
- `AI_CONTEXT.md`: minimum context for an AI agent.
- `RESUME_PROMPT.md`: copy-ready restart prompt.
- `AUDIT_EVIDENCE.md`: audit commands, validation, and limitations.

## Evidence labels

Documents use **Verified** for facts observed in accessible files or commands, **Confirmed decision** for versioned project policy, **Untested hypothesis** for claims requiring experiments, and **Unrecovered** for information not available or not safely checked. A planned item is never treated as completed without a state or result artifact.
