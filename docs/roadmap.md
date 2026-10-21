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
- Completed: execute version 2 of the frozen ten-seed XGBoost replication
  contract over the 25 confirmatory datasets. Version 1 is retained for audit
  after 10 newly executed runs exposed model-serialization overhead. Version 2
  validates all 25 reused seed-42 configurations, records source and target
  hashes separately, writes atomic checkpoints, and omits redundant model
  serialization while preserving predictions and MLflow provenance. All 250
  planned entries are complete. Across 25 datasets, the median paired MCC
  difference is 0.0574 in favor of XGBoost (bootstrap 95% interval
  [0.0293, 0.0777]; Wilcoxon two-sided p=0.00000656), with 21 wins and 4 losses.
- Next: treat this ten-seed result as the classical reference and begin the
  CapsProm implementation under the same canonical data and evaluation contract.

## Phase 4: CapsProm Models

Status: in progress.

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

Current state:

- Completed: inspect and pin the original CapsProm reference implementation,
  define the faithful one-hot architecture, and document the prohibition on
  legacy test-set-based checkpoint selection in
  `specs/capsprom_reproduction.md`.
- Completed: split the monolithic classical experiment implementation into
  focused data, model, evaluation, tracking, and runner modules while retaining
  a backward-compatible API for frozen workflows.
- Completed: implement and shape-test the PyTorch CapsProm architecture,
  dynamic-routing layer, capsule margin loss, and reconstruction objective
  using synthetic tensors only.
- Completed: add the minimal CNN control, explicit uniform-routing control, and
  two-class-capsule variant with class-conditioned reconstruction.
- Completed: add a training-only neural runner with deterministic inner split,
  validation-MCC checkpoint selection, atomic checkpoint/state writes, and an
  immutable hashed contract. The runner accepts no external test input and
  restores model, optimizer, data-loader generator, and PyTorch random state.
- Completed: add strict neural YAML contracts and MLflow provenance, then run
  one-epoch integration checks for legacy CapsProm-1C and the two-output basic
  CapsProm on 64 records
  from the exploratory training dataset only. Both runs reached inner-validation
  MCC zero through opposite single-class collapse; these are integration
  diagnostics, not comparative model results.
- Finding: the original binary architecture has one output capsule, making its
  routing coupling degenerate. Preserve this behavior only for the separately
  versioned historical reproduction.
- Decision: academic text uses CapsProm exclusively for the basic two-output
  architecture. The one-output model is named legacy CapsProm-1C and is retained
  only for historical reproduction.
- Completed: run the two-arm training-only learnability diagnostic. The CNN
  control reached best inner-validation MCC 0.1581 at epoch 4. Basic CapsProm
  remained in positive-class collapse through runner version 2, with MCC zero.
  These exploratory diagnostics do not select a model.
- Completed: verify on a balanced eight-sequence sanity task that basic
  CapsProm can reach 100% training accuracy by epoch 6, ruling out a completely
  broken optimization path.
- Completed: run the full exploratory training-split diagnostic on all 747
  records. Full-gradient routing remained in single-class collapse, with MCC
  zero. The separately versioned final-iteration-gradient policy left collapse
  and reached inner-validation MCC 0.1986 at epoch 14 (TN=53, FP=16, FN=47,
  TP=34). These are engineering diagnostics and did not access an external test
  split.
- Decision: use final-iteration routing gradients in new basic CapsProm
  development contracts. Preserve full-gradient routing only as an explicit
  reproduction option; do not mutate executed contracts.
- Completed: audit the implementation against the seminal CapsNet and public
  Keras, TensorFlow, and PyTorch implementations. Align new version 3 contracts
  with two-capsule defaults, flattened class-mask decoding, and summed
  per-sample reconstruction error while retaining version 2 compatibility.
- Finding: the first version 3 training-only diagnostic remained in
  promoter-only collapse and reached inner-validation MCC zero. This is an
  optimization diagnostic, not an external-test result.
- Completed: execute the predeclared `2 x 2` decoder and reconstruction
  component ablation with patience 15. Selected-vector decoding left collapse
  under both reductions (best MCC 0.2012 for mean and 0.1673 for summed error),
  while both masked-flat arms remained in promoter-only collapse with MCC zero.
  Gradient audits showed connected finite gradients and reconstruction
  gradients orders of magnitude below the margin-loss gradient.
- Finding: the mechanics of backpropagation are consistent, but optimization is
  fragile to small decoder-dependent perturbations and is not ready for a
  confirmatory freeze.
- Completed: execute a five-seed no-reconstruction stability control. Four
  seeds left collapse with best inner-validation MCC from 0.2303 to 0.3536;
  seed 42 remained promoter-only with MCC zero. The median across all seeds was
  0.2328 and the observed collapse rate was 20%. No external test data was
  accessed.
- Finding: the margin-loss capsule core is learnable without reconstruction but
  remains seed-sensitive under the current fixed Adam contract. Reconstruction
  cannot be treated as a reliable mechanism for escaping collapse.
- Completed: add runner contract version 4 with a structurally disabled decoder
  and resumable fixed or exponential learning-rate scheduling. For 81-base
  inputs, disabling reconstruction removes approximately half of the model
  parameters and avoids decoder computation and optimizer state.
- Completed: compare fixed learning rate with epoch-wise factor 0.9 over the
  same five seeds. Exponential decay produced median best MCC 0.1890 and 40%
  collapse, versus 0.2328 and 20% collapse for the fixed-rate arm.
- Decision: do not adopt the tested exponential decay. Retain the fixed-rate,
  decoder-disabled core as the current development candidate, without freezing
  it as confirmatory because one of five seeds still collapsed.
- Completed: add runner contract version 5 and execute capsule-norm traces for
  fixed-rate seeds 37 and 42. Both runs drove the two capsule norms from about
  `0.001` toward saturation during the first epoch before learning any visible
  class-conditional separation. Seed 37 later escaped and reached best
  inner-validation MCC 0.2932; seed 42 alternated global capsule dominance and
  remained at MCC zero. No external test data was accessed.
- Finding: gradients reach the capsule layer, but the initial Adam updates can
  saturate both squashed capsule norms and make the subsequent optimization
  highly sensitive to small numerical differences. Collapse is therefore an
  optimization-stability problem, not evidence that the capsule path is
  disconnected.
- Completed: execute the same five-seed, training-only control at fixed learning
  rate `0.0001`. All five seeds predicted both classes, including the previously
  collapsed seed 42. Median best inner-validation MCC was 0.2175 and collapse
  rate was zero, versus 0.2328 and 20% at fixed learning rate `0.001`.
- Finding: reducing the initial update improves stability but slightly reduces
  median MCC. First-epoch capsule norms remained high at approximately
  `0.78--0.82`, although below the most extreme saturation observed at `0.001`.
- Decision: treat `0.0001` as support for the initial-update hypothesis, not as
  the final learning rate. Do not freeze either fixed rate yet.
- Completed: add runner contract version 6 with a resumable five-epoch linear
  warm-up from `0.0001` to `0.001`, explicit per-epoch rate history, strict YAML
  fields, and MLflow provenance.
- Completed: execute the same five-seed warm-up control. Median best
  inner-validation MCC was 0.1943 and seed 37 remained in single-class
  collapse, for a 20% collapse rate.
- Decision: reject the five-epoch warm-up because it performed below both fixed
  rates and reintroduced collapse in a seed that learned under both fixed-rate
  controls.
- Completed: extend fixed-`0.0001` training to a maximum of 60 epochs with
  patience 15. All five runs stopped between epochs 31 and 38 and reproduced
  their 30-epoch best checkpoints and metrics exactly.
- Finding: the lower median MCC at `0.0001` is not caused by an insufficient
  30-epoch horizon. The 60-epoch limit adds computation without changing model
  selection.
- Decision: stop optimizer adaptation on this inner split. Freeze fixed learning
  rate `0.0001`, maximum 30 epochs, patience 15, disabled decoder, and runner
  contract version 6 as the stability-first basic-CapsProm development setting.
  This decision is based only on inner-training stability, not external-test
  superiority.
- Next: define and version the canonical multi-dataset basic-CapsProm experiment
  under the existing collision-free data and statistical evaluation protocols
  before executing any external-test evaluation.
- Completed: define the design-locked canonical contract for 26 v3 dataset
  pairs, ten seeds, five-fold epoch selection followed by full-training refit,
  relative capsule scoring, row-level provenance, and explicit execution gates.
  The resulting campaign requires 1,560 fits before retries; external-test
  execution remains disabled.
- Completed: specify the architecture boundary for learned embeddings and
  multi-head inputs. The current basic CapsProm accepts only one-hot tensors;
  embedding and multi-head variants are separate future models and cannot
  silently redefine the baseline.
- Next: implement and fixture-test per-dataset fold-manifest generation plus
  resumable dataset/seed/fold orchestration while keeping the final test stage
  structurally unavailable.
- Completed: implement and fixture-test canonical plan preparation. The command
  resolved all 26 training files, generated five-fold manifests and hashes,
  recorded dataset hashes, and wrote 1,560 pending jobs without opening any
  test file (`external_test_accessed: false`).
- Next: implement execution of one pending inner-fold job with atomic state
  updates and MLflow child-run provenance, then validate continuous-versus-
  resumed equivalence before enabling batch orchestration.
- Completed: add a manifest-defined neural training entry point. The immutable
  neural contract now records the fold-manifest SHA-256 and validation-fold
  index and rejects resume when either selection identity changes. Focused tests
  confirm that no implicit random holdout replaces the canonical fold.
- Next: connect this manifest-defined primitive to atomic plan-job claiming and
  MLflow child-run completion, then execute a fixture job continuously and via
  resume to prove equivalence before scheduling real inner-fold jobs.
- Completed: connect an explicitly selected inner-fold job to atomic plan state,
  a deterministic MLflow parent run, and a deterministic child run. Resume
  reuses the child run identifier, manifest-bound checkpoint, and state; a
  completed plan job is not rerun.
- Completed: validate a continuous fixture against an interruption after neural
  state persistence but before MLflow completion. Resume reused the same child
  run, produced the same best epoch and exactly equal MCC, logged the same state
  and fold-manifest artifacts, and left one parent plus one finished child in
  each isolated tracking store.
- Completed: audit the proposed representation ablation. Only one-hot `k=1` is
  implemented and executed by CapsProm; trainable `k=1` and `k=2` embeddings
  have neither model code, versioned run contracts, nor MLflow runs. Record the
  future frozen-versus-trainable physicochemical initialization strategy without
  implementing it.
- Next: add an atomic multi-worker claim lock and failure-retry policy around
  fold selection, then run a training-only feasibility fixture on representative
  small and large shapes. Do not start real canonical or embedding jobs yet.
- Completed: add process-scoped filesystem locks per fold, a serialized plan
  update lock, and a serialized MLflow identity lock. Different local workers
  can update different jobs without overwriting plan progress, while concurrent
  execution of the same fold fails before training.
- Completed: validate a marked failure followed by retry. The retry reused the
  failed child run identifier and durable neural state, incremented the attempt
  count, finished the existing run, and matched the continuous result exactly
  without creating duplicate parent or child runs.
- Next: add synthetic small/large-shape feasibility fixtures and resource
  measurements for the frozen one-hot model. Keep all 1,560 real jobs and every
  embedding ablation job blocked.
- Completed: measure one-epoch synthetic feasibility for the frozen one-hot
  basic CapsProm at the smallest (646 rows) and largest (37,438 rows) canonical
  training cardinalities. On the CPU-only WSL2 host, training took 20.11 and
  77.10 seconds with peak RSS of 539 MB and 3.61 GB, respectively; both passed
  the 1,800-second/OOM gate. The maximum-epoch campaign projection is about
  123.5 CPU hours before validation and orchestration overhead, so individual
  fits are feasible but campaign scheduling remains a separate decision.
- Completed: define a fold-safe explainability protocol for classical,
  convolutional/capsule, embedding, multi-head, and contextual models. Add and
  fixture-test auditable convolution-activation windows, PFM/PPM matrices, SVG
  sequence logos, coordinate mapping, artifact hashes, and MLflow child-run
  association. These fixtures validate infrastructure, not biology.
- Completed: provision passwordless project-specific SSH access and an isolated
  Python 3.13 CUDA environment on `bioserver03`. Add runner contract version 7
  with explicit accelerator placement while preserving the serialized identity
  and CPU-only behaviour of versions 2 through 6. The RTX 3060 completed the
  646- and 37,438-row one-epoch fixtures in 1.164 and 5.132 training seconds,
  with peak reserved GPU memory of 182 MB and 3.91 GB. The large fixture was
  approximately 15 times faster than the local CPU measurement, projecting
  about 8.22 GPU hours at the campaign's 30-epoch maximum before overhead.
- Finding: PyTorch differs between the local CPU environment (2.13.0+cpu) and
  the available remote CUDA build (2.11.0+cu128). The 29-test remote neural
  fixture suite passed, but GPU continuous-versus-resumed equivalence must be
  explicitly validated before creating a new canonical GPU contract.
- Completed: implement the fixture-only final-fit/prediction and row-artifact
  gate. The lower-median epoch selection and full-training completion are
  persisted before fixture evaluation is opened. Row identifiers, both raw
  capsule lengths, relative positive scores, predictions, effectiveness and
  calibration metrics, and training-only activation-logo artifacts are hashed
  and attached to one deterministic MLflow final-fit child run. Continuous and
  interrupted/resumed fixture executions were exactly equal and created no
  duplicate runs; canonical external-test access remained false.
- Completed: validate runner-contract-7 GPU continuous-versus-resumed
  equivalence on `bioserver03`. The exercise exposed and fixed CUDA restoration
  of CPU RNG state. After correction, histories, parameters, capsule scores,
  selected epoch, and predictions were exactly equal, passing the `1e-7`
  numerical and exact-decision tolerances. No canonical or embedding job ran.
- Completed: draft `capsprom_basic_canonical_gpu_v1.yaml` as a separate CUDA
  contract with new protocol/tracking identities and both real-job gates false.
  No state exists for it, so the versioned contract remains reviewable.
- Completed: audit the GPU contract against the CPU design with a fixture test.
  Only protocol/tracking identities, runner version, CUDA device, and the two
  explicit blocked-job flags differ. Reserve the remote training-only plan root
  without creating state. The expected processed-dataset directory is currently
  absent on `bioserver03`, and no GPU plan state exists.
- Completed: transfer only the 26 immutable v3 training CSV files to
  `bioserver03`; all SHA-256 hashes match and zero test CSVs are present. Prepare
  the GPU training-only plan with 1,300 pending folds, 260 blocked final fits,
  zero completed jobs, and zero run identifiers. Enforce the versioned
  `canonical_jobs_enabled: false` gate in the fold executor.
- Completed: define the remote worker and MLflow policy. Production uses one
  CUDA worker and a contract-local SQLite/artifact store on `bioserver03`;
  `bioserver04` has zero canonical workers and is reserved for CPU auxiliary
  work. A two-worker synthetic stress test on `bioserver03` created exactly one
  parent and two finished child runs while preserving both plan updates.
- Completed: define deterministic smallest-first fold scheduling with a
  three-attempt ceiling; an atomic failure outbox whose events become resolved
  after successful retry; checkpoint retention sized against measured remote
  disk; and integrity-checked online SQLite backup. Artifact backup remains a
  separate checksum snapshot and is required before pruning resumable state.
- Completed: fixture-test direct `bioserver03` to `bioserver04` backup using a
  source-host-specific key. Checksum restore audit found no artifact mismatch;
  the copied SQLite backup matched its manifest, passed integrity checking, and
  contained the expected run record. No canonical artifact was transferred.
- Completed: draft and audit the separate execution-enabled GPU candidate with
  explicit host-local SQLite and artifact locations. A fixture test proves that
  it differs from the blocked GPU design only in identities, storage locations,
  the enabled inner-fold gate, and an explicit false final-fit gate. MLflow now
  rejects a conflicting artifact location for an existing experiment. No plan
  exists and the candidate has not been synchronized to the execution host.
- Completed: after explicit authorization, synchronize the execution contract,
  create its immutable training-only plan, and run exactly one smallest-dataset
  pilot fold on `bioserver03`. The 646-row Chlamydophila dataset at seed 13,
  fold 0 completed 30 epochs in 8.25 seconds, selected epoch 28, and recorded
  inner-validation MCC 0.8008534347 with 1.90 GB peak process RSS. MLflow has
  one campaign parent and one finished child with the correct link and
  provenance. The independently verified `bioserver04` snapshot has two exact
  artifacts and an integrity-checked, hash-matching SQLite backup. No checkpoint
  was pruned and no second fold ran.
- Completed: after a second bounded authorization, finish folds 1 through 4 for
  the same Chlamydophila dataset and seed. All five folds completed on their
  first attempts. Their inner-validation MCC is 0.7568449460 mean with
  0.0308420264 sample standard deviation; the lower-median epoch rule selects
  epoch 26 from fold epochs 28, 26, 7, 30, and 25. MLflow contains one parent
  and five unique finished children. A separate `five-fold-seed-13` backup on
  `bioserver04` contains 10 checksum-matching artifacts and a hash-matching,
  integrity-checked SQLite database. No checkpoint was pruned.
- Completed: execute the five folds of the same dataset at seed 29. All
  completed on their first attempt in 16.23 aggregate seconds. Their mean
  inner-validation MCC is 0.7440173954 with sample standard deviation
  0.0454994087, and the lower-median rule selects epoch 21. MLflow now has 10
  unique finished children. The independently verified two-seed backup contains
  20 exact artifacts and an integrity-checked SQLite database.
- Next: review the two-seed stability evidence before authorizing seed 42 or a
  different dataset. Until then, 1,290 inner folds remain pending, 260 final
  fits remain blocked, and external-test and embedding execution remain
  disabled.
- Completed: adopt a local-first remote usage policy. Routine development,
  tests, documentation, status checks, and incremental synchronization remain
  local. `bioserver03` is reserved for authorized GPU-heavy or many-fit work;
  `bioserver04` is reserved for authorized heavy CPU work and campaign backup
  verification. No remote host is contacted merely to mirror development
  progress.
- Completed: separate fold-derived epoch selection from final fitting. The
  local readiness command atomically marks only dataset/seed units with five
  completed inner folds as `ready_for_final_fit`, persists their fold epochs
  and lower median, is idempotent, and cannot access evaluation data. Final-fit
  and external-test execution gates remain unchanged.
- Completed: implement and fixture-test the production final-fit runner. It
  accepts only `ready_for_final_fit`, trains on all authorized training rows,
  persists resumable optimizer/RNG state, and records
  `completed_final_fit_training` without accepting evaluation input. Continuous
  and interrupted/resumed CPU fixtures have exactly equal model tensors and
  epoch histories, reuse one MLflow child, and are idempotent after completion.
- Completed: implement external inference as a separate command. Its versioned
  gate is checked before the evaluation path is opened, and it additionally
  requires matching hashes for a completed final checkpoint and training state.
  All current real contracts keep this gate false.
- Completed: audit the historical and current MCC evidence locally in
  `docs/capsprom_mcc_training_audit.md`. The current documented values are
  per-fold inner-validation MCC, not pooled out-of-fold MCC, and no current row
  predictions are available locally for independent recalculation. Seed 13,
  fold 3 selected epoch 30 at the ceiling and is explicitly flagged for review.
- Next: reverify the remote plan and MLflow identities only after explicit
  authorization, then decide whether to retain the frozen 30-epoch budget or
  create a separate sensitivity contract. The release policy remains locally
  blocked in `configs/capsprom_future_campaign_release_policy_v1.yaml`.

## Phase 5: Interpretability and Thesis Artifacts

Status: planned.

Goals:

- Relate learned patterns to candidate motifs and biological concepts.
- Generate plots, tables, and LaTeX snippets.
- Document where each artifact belongs in the thesis.

Exit criteria:

- Experimental outputs can be directly reused in doctoral writing.
