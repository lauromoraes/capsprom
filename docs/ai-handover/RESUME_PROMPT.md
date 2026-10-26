# Resume Prompt

Copy the prompt below into a new AI session opened at the repository root.

```text
You are resuming the CapsProm doctoral research project at /mnt/d/workspace/capsprom without access to the preceding conversation.

First read AGENTS.md and every file in docs/ai-handover/, beginning with README.md and AI_CONTEXT.md. Then read specs/project_spec.md, specs/statistical_evaluation_protocol.md, specs/capsprom_canonical_experiment.md, docs/roadmap.md, manifests/current_status.json, and manifests/remote_jobs.json. Treat specs, used versioned YAML contracts, state hashes, and MLflow identifiers as authoritative.

Before changing anything, run read-only checks: git status --short, git rev-parse HEAD, make status, and inspect the relevant config/state paths. Compare the result with the 2026-10-26 handover and report any drift. Do not assume a planned item is completed. Label facts as verified, confirmed decisions, untested hypotheses, or unrecovered.

Preserve the active 18-dataset CDBProm/CNNProm scope, 14 dependency clusters, GraphPro deferral, Bhandari shuffle-control identity, locked statistical protocol, and one-hot basic-CapsProm architecture boundary. Never use test outcomes for model/feature/epoch selection. Do not edit a used YAML contract or reuse its state path after any scientific or execution change.

First verify that commit 315f5cc and the commit containing docs/ai-handover/ are present and that the working tree is clean. The versioning checkpoint already passed lint and 160 tests. The immediate scientific task is to resolve the remaining XGBoost summary-path ambiguity and review the completed v4 tranche before predeclaring any next bounded seed. Do not launch remote work, contact servers, resume XGBoost v1, run final fits/tests, start embeddings, or resume GraphPro unless explicitly authorized. If a next bounded training-only tranche is requested, require a new immutable release and verify hashes, locks, MLflow/state identity, backup, and external_test_accessed=false.

Use docs/ai-handover/ROADMAP.md for priorities and update the handover documents if verified state changes. Keep all repository documentation, code, comments, configs, and experiment notes in English.
```
