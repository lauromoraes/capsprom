# Roadmap

## Phase 0: Project Foundation

Status: complete.

Goals:

- Define the canonical project specification.
- Establish repository organization.
- Create an AI-oriented project skill.
- Add a first YAML experiment example.

Exit criteria:

- The repository has clear documentation for scope, constraints, and next
  development steps.

## Phase 1: Pipeline Design and MVP Execution

Status: complete.

Goals:

- Use `docs/qualification_context.md` to preserve the methodological continuity
  between the qualification thesis and the current reproducible pipeline.
- Define the minimum viable experiment pipeline.
- Specify dataset validation rules.
- Specify configuration schema.
- Decide how MLflow run metadata and artifacts will be organized.
- Provide a strict YAML loader, dataset validation command, and a small
  end-to-end sanity-check experiment.

Exit criteria:

- A pipeline specification exists before implementation.
- The user has reviewed the assumptions.
- The logistic-regression MVP runs from `configs/mvp_logistic.yaml` and records
  dataset hashes, configuration, metrics, timings, and the fitted model in a
  local SQLite-backed MLflow store.
- The same contract runs on the complete Bhandari human promoter split through
  `configs/full_logistic.yaml`.

## Phase 2: Data and Encoding Layer

Status: in progress.

Goals:

- Implement dataset loading and validation.
- Implement sequence normalization checks.
- Implement k-mer frequency encodings.
- Implement one-hot encodings for k-mer representations.
- Define interfaces for physicochemical vectors and DNA-BERT embeddings.
- Implement GC/skew and PseKNC descriptors and feature-oriented EDA.

Exit criteria:

- Encoders are independently testable.
- Invalid datasets fail with clear errors.

Current state:

- Strict-DNA preprocessing and validation are complete for 58 model-ready
  files containing 1,828,924 sequences.
- K-mer frequency, one-hot, physicochemical, GC/skew, PseKNC, and DNA-BERT
  feature interfaces are implemented.
- Concatenated classical inputs and named multi-head inputs are supported.
- Feature and EDA tests are in place; broader data-pipeline regression tests
  remain to be added.

## Phase 3: Baselines

Status: in progress.

Goals:

- Implement or integrate baseline models in a controlled way.
- Include fine-tuned DNA-BERT as a classifier baseline, distinct from DNA-BERT
  embedding features.
- Track all baseline runs in MLflow.
- Define fair comparison conditions.

Exit criteria:

- Baseline results are reproducible from YAML configuration files.

Entry condition:

- Completed: promote the Phase 1 logistic-regression sanity check to a full-data
  baseline.
- Completed: add XGBoost under the same data, feature, metric, and tracking
  contract.
- Completed: specify repeated-seed rules, confidence intervals, calibration
  assessment, paired comparison, multiplicity control, and cross-dataset
  inference in `specs/statistical_evaluation_protocol.md`.
- Completed: implement stable row-level prediction artifacts, missing
  effectiveness and calibration metrics, hashed five-fold manifests, and exact
  duplicate/overlap audits.
- Audit finding: 49.87% of Bhandari human test rows belong to exact sequences
  also present in training, so current baseline metrics are development-only and
  potentially optimistic.
- Completed: create and validate a deterministic deduplicated group split with
  one explicit shuffled negative per unique positive, zero duplicates, and zero
  train/test overlap.
- Completed: rerun logistic regression and XGBoost on the corrected
  shuffle-control dataset with full prediction and calibration artifacts.
- Completed: audit all 26 CDBProm, CNNProm, and GraphPro train/test pairs for
  exact duplicates, conflicts, and partition overlap. None passes the strict
  eligibility rule; 98.09% of test rows belong to sequences present in train.
- Completed: trace the dominant duplication to append-mode writes in the legacy
  cropping notebook, switch to overwrite mode, and regenerate the datasets.
  Test-row overlap falls from 98.09% to 2.17%, and 9 of 26 pairs pass the strict
  integrity rule without further correction.
- Completed: make post-crop cross-label removal mandatory, record every filter
  stage in JSON/CSV manifests, and regenerate v2 with zero label conflicts. Ten
  of 26 pairs now pass the strict integrity rule.
- Completed: regenerate all 26 pairs as canonical v3 datasets after bilateral
  collision removal, within-class deduplication, strict-DNA filtering, and
  deterministic unique-sequence group splitting. All 26 pairs pass the exact
  duplicate, label-conflict, and train/test-overlap audit.
- Completed: audit train/test near duplicates at Hamming distances 1, 2, 4,
  and 8. At the broadest threshold, 96 of 35,991 test sequences have a
  same-label training neighbor and none has an opposite-label neighbor.
- Next: freeze dataset/fold manifests and begin biological-negative baseline
  runs, retaining the near-duplicate result as a secondary sensitivity analysis.
- Completed: run exploratory logistic-regression and XGBoost smoke tests on the
  canonical GraphPro `clostridium_phytofermentans` pair with MLflow provenance,
  fold manifests, row predictions, and calibration metrics.
- Next: freeze model search spaces and orchestrate all-dataset biological-negative
  baselines without using the observed smoke-test pair for design decisions.
- Completed: freeze a resumable 52-run baseline batch: 50 primary confirmatory
  runs across 25 still-blind datasets and two exploratory runs for the observed
  smoke-test pair. The first confirmatory logistic-regression run completed with
  MLflow and fold-manifest provenance.
- Next: resume the remaining 49 confirmatory runs, then execute the predeclared
  paired and cross-dataset summaries without changing the frozen contract.
- Completed: finish the 50-run fixed-seed paired sweep over 25 still-blind
  datasets and compute the cross-dataset MCC summary. XGBoost wins 21 of 25
  pairs with a median MCC difference of 0.0621 at seed 42.
- In progress: execute the frozen ten-seed XGBoost replication contract over
  the 25 confirmatory datasets. The 25 seed-42 runs are reused with explicit
  provenance; 225 additional MLflow runs are resumable from a per-run state
  file. On completion, replace the fixed-seed screening effect with the median
  XGBoost MCC across seeds and its paired cross-dataset inference.

## Phase 4: CapsProm Models

Status: planned.

Goals:

- Reproduce the original CapsProm direction under the unified pipeline.
- Implement CapsProm.
- Implement SparseCapsProm.
- Plan the attention-enhanced A-CapsProm extension after baseline reproduction.
- Add hyperparameter optimization.
- Compare against baselines using the same pipeline.

Exit criteria:

- Proposed models can be evaluated under reproducible, statistically sound
  conditions.

## Phase 5: Interpretability and Thesis Artifacts

Status: planned.

Goals:

- Relate learned patterns to candidate motifs and biological concepts.
- Generate plots, tables, and LaTeX snippets.
- Document where each artifact belongs in the thesis.

Exit criteria:

- Experimental outputs can be directly reused in doctoral writing.
