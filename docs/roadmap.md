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
- Next: implement repeated seeds and paired uncertainty for the shuffle-control
  analysis, while identifying provenance-backed genomic negatives for the
  primary biological benchmark.

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
