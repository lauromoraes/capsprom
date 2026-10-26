# Decision Record

This is a concise index; detailed rationale remains in versioned specs and `docs/roadmap.md`.

- **Project restart:** build data/config/tracking/evaluation infrastructure before capsule complexity; logistic regression is the first end-to-end sanity check.
- **Data contract:** normalize to 81 bp, strict A/C/G/T, remove post-crop conflicts from both classes, deduplicate within class, and split exact-sequence groups safely.
- **Bhandari:** retain only as a separately named synthetic-shuffle development control because the legacy split leaks exact sequences.
- **Active source scope:** use 18 CDBProm/CNNProm datasets for confirmatory work; exact cleanliness alone does not validate label semantics.
- **GraphPro:** exclude all eight identities, preserve artifacts without relabeling, and defer the entire line until a new explicit decision.
- **Statistical design:** MCC primary; five-fold training-only selection; ten predeclared stochastic seeds; dependency clusters are the across-dataset units; never treat folds or seeds as independent datasets.
- **Basic CapsProm stability:** freeze fixed learning rate 0.0001, 30 epochs, patience 15, and decoder disabled for the current baseline. Reject tested warm-up and decay schedules.
- **Architecture boundary:** one-hot k=1 basic CapsProm is distinct from future embedding, multi-head, attention, or sparse variants.
- **Campaign safety:** deterministic manifests, atomic state, resumable checkpoints, filesystem locks, explicit releases, and structurally closed final-test gates.
- **Remote policy:** local-first; use remote hosts only for explicitly authorized campaign-scale work and synchronize minimal immutable snapshots.
- **Current release:** only Chlamydophila seed 13 folds 0-4 were released under v4/release v3. Completion does not release another seed, final refit, or external test.
- **Classical consolidation:** reuse completed logistic/XGBoost outputs for the 18-dataset comparison; do not refit merely to rebuild context.

Chronology and full rationale are in Git history and `docs/roadmap.md`; relevant commits include `0ba28ff` (canonical CapsProm), `05949a9` (hierarchical statistics), `b702554` (50-epoch campaign/dependency audit), `93a3bed` (GraphPro provenance/contracts), and `315f5cc` (bounded v4 campaign, active baseline consolidation, and versioned operational state).
