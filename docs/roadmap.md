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
- Completed: adopt statistical-protocol version 2 for future model comparisons.
  Five folds remain selection-only, ten seeds remain algorithmic-stability
  replicates, and the dataset effect is now the median of seed-paired MCC
  differences. Cross-dataset inference uses audited dependency clusters,
  Wilcoxon for two-model comparisons, Friedman for the multi-model omnibus, and
  Holm-adjusted predeclared pairwise tests. Version 1 remains unchanged for
  analyses already bound to it.
- Next: construct and review the 26-dataset dependency manifest, then implement
  fixture-tested paired-seed and cluster-level aggregation. Confirmatory model
  ranking remains blocked until both gates pass.
- Completed: freeze a separate 50-epoch, patience-15 canonical candidate after
  the budget decision. Version 2 starts every fold at epoch one and cannot reuse
  the ten historical 30-epoch folds. New protocol, output, and MLflow identities
  prevent accidental resume; all execution gates remain false.
- Completed: run the local exact cross-dataset dependency audit and create a
  provisional 26-dataset manifest. Eight pairs share sequences. The largest
  findings are 535 opposite-label identities across the two
  *B. amyloliquefaciens* datasets and 195 shared positives between CDBProm
  Chlamydophila and GraphPro *C. phytofermentans*. These findings block final
  dependency clusters pending source-lineage review.
- Completed: review source-label semantics and freeze the eligible confirmatory
  scope. The review identified 1,345 raw GraphPro E. coli contradictions,
  perfect class--strand confounding in five bacterial folders, 535 GraphPro
  Bacillus negatives matching CDBProm positive TSS windows, and a CapsProm
  `Cpne` organism-mapping error. The builder now identifies `Cpne` as
  Chlamydophila pneumoniae. All eight GraphPro identities are exploratory until
  independently reconstructed; the confirmatory scope contains 18 CDBProm and
  CNNProm datasets in 14 reviewed dependency clusters.
- Completed: define the GraphPro treatment and reinstatement contract. Released
  labels remain unchanged; new `graphpro-reconstructed-v1` candidates require
  independent TSS/EPD provenance, exact assembly versions, deterministic
  GC-matched genomic controls, full filtering ledgers, and per-organism
  eligibility. Fixture tests validate deterministic strand-aware reconstruction
  and source auditing. No reconstructed real dataset or model job has run.
- Completed: verify bacterial reconstruction feasibility against Promotech
  commit `56251ad9b883ef831b4753fc623d5ec970fe65e0`. Matching BED6 TSS tables and
  assemblies exist for all six bacteria. A controlled local run produced
  11,903 positive--control pairs after TSS-level deduplication and source-window
  filtering. Source hashes and BED--FASTA orientation checks pass for all six;
  the smallest common discrete GC tolerance is four bases in 81 nt. These are feasibility
  counts, not released datasets; no model job ran.
- Completed: materialize immutable GraphPro reconstruction candidates. Version
  1 exposed 77 strand-invariant repeated positive windows after TSS
  deduplication. Version 2 removes each affected positive--control pair and
  retains 11,826 balanced pairs across six organisms. Its exact-integrity audit
  has zero within-class identities, zero cross-label exact/reverse-complement
  collisions, zero invalid sequences, and zero GC-policy violations. No split
  or model job has run.
- Completed: freeze and materialize near-duplicate-aware group-safe splits for
  the six bacterial version-2 candidates. Positive--control pairs and connected
  components at strand-invariant Hamming distance at most eight are
  indivisible. The split contains 18,920 training and 4,732 test rows with exact
  class balance; an independent audit finds zero pair, group, exact,
  reverse-complement, or distance-eight train/test overlap. A clean rebuild is
  byte-identical. Model and confirmatory gates remain false.
- Completed: create versioned exploratory integrity views for the released
  GraphPro Human and Mouse collections without inferring biological labels.
  Bilateral exact-collision and within-class duplicate filtering removes 13
  Human records (8 positive and 5 negative) and four Mouse records (3 positive
  and 1 negative), with every exclusion recorded by source identifier, class,
  index, sequence hash, and reason. The resulting identities are not treated as
  EPD-based reconstructions and remain blocked from training.
- Completed: generate fixed-scale, class-separated before/after dataset logos
  for the six bacterial reconstruction candidates and the two released
  eukaryotic integrity views. Sixteen figures and 64 frequency/information CSV
  matrices are bound to logo-audit contract v2. A standalone 11-page LaTeX/PDF
  report distinguishes dataset composition from model-extracted motifs and
  independently positioned bacterial TSSs from nominal eukaryotic alignment.
- Completed: assess derived-artifact impact. The bacterial v2 grouped split
  remains valid; released GraphPro model results remain historical only;
  Human/Mouse canonical-v3 partitions cannot be reused for the new integrity
  identity or a future EPD reconstruction. The active eligibility scope remains
  18 CDBProm/CNNProm datasets.
- Completed: run the formal candidate distribution and strand-invariant exact
  dependency audits. All bacterial pairs respect the frozen four-base GC
  tolerance, but five of six show small aggregate GC shifts after Holm
  correction. Human and Mouse released integrity views show much larger class
  differences of 11.0 and 10.4 GC percentage points. Across 26 identities,
  five dependencies involve a GraphPro-derived candidate/view: 404 shared
  Chlamydophila positives, two shared Bacillus positives, six CNNProm-negative
  versus reconstructed-E. coli-positive conflicts, one CNNProm-positive versus
  released-Mouse-negative conflict, and one shared Human/Mouse positive.
  E. coli reinstatement is blocked pending source resolution; Chlamydophila
  requires shared dependency clustering if reinstated. No labels were changed.
- Completed: freeze the November 2023 EPDnew archive metadata, assemblies,
  CC BY 4.0 notice, and BED hashes, then resolve the released Human/Mouse
  identifiers. All 2,339 Human identifiers resolve to HsNC v001 on hg38; all
  2,576 identifiers in the Mouse class union resolve to MmNC v001 on mm10.
  Every Human identifier and 1,116 Mouse identifiers occur in both released
  class files, confirming that EPD resolution cannot validate the released
  negative label. A row-level coordinate ledger is reproducible and atomic.
- Completed: perform a preliminary strand-aware coordinate check on three
  Human pairs, one Mouse pair present in both classes, and one Mouse positive.
  All checked positives span -80 through the EPD TSS; all checked paired
  negatives span +1000 through +1080 relative to that TSS. This identifies a
  likely released-data construction rule but does not replace a complete
  hash-bound recreation from local hg38/mm10 assemblies.
- Completed: acquire and verify the official UCSC hg38/mm10 twoBit assemblies
  on the bounded `bioserver04` workspace and recreate all 8,370 released
  Human/Mouse records. Every positive is exactly the strand-oriented EPD
  interval [-80, 1), and every negative is [1000, 1081); there are zero
  sequence or header-label mismatches. Two complete executions are byte-equal.
  The result establishes source provenance, not verified non-promoter status.
- Completed: perform a preliminary coordinate-only exclusion check for the
  historical +1 kb controls. Another known coding/non-coding EPD TSS falls
  inside 22 Human and 11 Mouse controls; the frozen 100-nt exclusion margin
  affects 74 Human and 40 Mouse controls. Formal row-level treatment remains
  pending.
- Completed: materialize the formal historical downstream-control treatment on
  top of the exact-integrity view. The all-EPD 100-nt exclusion removes 73
  Human controls (21 direct TSS overlaps) and 40 Mouse controls (11 direct
  overlaps); one Human positive reverse-complement duplicate is also removed.
  Final counts are 2,330/2,261 Human and 1,843/1,805 Mouse. The ledger and
  FASTAs rebuild byte-identically, and all final exact/reverse-complement and
  TSS-margin checks pass. No artificial pairing or rebalancing was introduced.
- Completed: audit the treated Human/Mouse downstream condition against the
  confirmatory scope. Mean positive-minus-negative GC differences remain 0.1149
  and 0.1069, so the construction shortcut persists. Human and Mouse share one
  positive identity; one Mouse control (`FP002834|Gm50063_1`) reverse-complement
  matches a CNNProm Mouse non-TATA positive. Mouse remains blocked pending
  source resolution, and neither candidate receives a split or execution gate.
- Completed: create the immutable downstream-treatment v2 successor under the
  external-positive control-suitability rule. Only Mouse control
  `FP002834|Gm50063_1` was removed; CNNProm was not modified or relabeled.
  Mouse v2 contains 1,843 positives and 1,804 negatives, while Human is
  byte-identical to v1. Rebuilds are deterministic. The repeated dependency
  audit has no remaining opposite-label identity with the active confirmatory
  scope, but one Human/Mouse shared positive remains. Mean class GC differences
  remain 0.1149 and 0.1070, so both conditions remain exploratory, unsplit, and
  blocked from training.
- Completed: materialize the separate primary EPD GC-matched Human/Mouse v5
  candidate. The frozen contract uses the union of 2,339 Human and 2,576 Mouse
  EPD identifiers and one same-chromosome, same-strand control with at most two
  GC-base differences per positive. Exact, one-base, and random-only two-base
  feasibility attempts were preserved separately. A deterministic exhaustive
  fallback was required for two extreme-GC Mouse promoters. Bilateral duplicate
  filtering retained 2,332 Human and 2,571 Mouse pairs. Pairs are indivisible;
  all known EPD
  TSS margins, target/external positive identities, ambiguous windows, and
  selected-control overlaps are excluded. Execution is isolated on
  `bioserver04`; split and training gates remain false. The descriptive audit
  reports mean class GC gaps of 0.00289 and 0.00405 and no opposite-label exact
  dependency with the 18-dataset confirmatory scope. Same-label positive
  dependencies remain for grouping. The distance-eight audit links 53 Human and
  49 Mouse pairs; largest components contain six pairs, and Human has three
  cross-label near-neighbor edges. A clean rebuild reproduced the complete
  output tree and log byte-for-byte. Generation is validated; manual source
  review and eligibility approval remain pending.
- Next: independently sample-audit the primary TSS provenance, run the
  near-duplicate/grouping audit, archive source citations for the six bacteria,
  and predeclare a negative-control sensitivity for residual GC structure.
  Approve per-organism eligibility only after those gates; do not generate
  grouped splits beforehand.
- Completed: implement and fixture-test paired-seed and cluster-level
  aggregation under evaluation protocol v3. The synthetic contract enforces
  the complete ten-seed pairing, calculates the median within-seed difference
  per dataset, collapses related datasets to one dependency-cluster median,
  withholds Wilcoxon inference below ten clusters, applies monotone Holm
  adjustment, and validates a deterministic paired stratified bootstrap with
  shared record indices. This closes only the fixture gate; group bootstrap,
  final report integration, and all real canonical jobs remain blocked.
- Next: reverify the remote plan and MLflow identities only after explicit
  authorization, then decide whether to retain the frozen 30-epoch budget or
  create a separate sensitivity contract. The release policy remains locally
  blocked in `configs/capsprom_future_campaign_release_policy_v1.yaml`.
- Completed: supersede the remote usage policy with v3. Long remote commands
  must use a disconnect-safe asynchronous launcher, persist their exit code,
  and register server, process identity, command, working directory,
  configuration, logs, results, and checkpoints in
  `manifests/remote_jobs.json`. `make status` exposes pending entries. Future
  authorized interactions inspect registered jobs before launching equivalent
  work; no automatic monitoring between interactions is claimed. The registry
  currently has no pending jobs, and all canonical, final-fit, external-test,
  and embedding gates remain closed.
- Completed: freeze the version-1 negative-control sensitivity design. Native,
  GC-matched genomic, synthetic-shuffle, CDS-derived, and multi-negative
  conditions keep separate identities and test panels; no pooled MCC is
  allowed. The first future implementation is one provenance-selected pilot,
  but construction and training remain blocked until the GraphPro manual audit,
  statistical-aggregation fixtures, and coordinate feasibility inventory are
  complete.
- Completed: inventory coordinate and assembly feasibility for all 29 local
  Bhandari, CDBProm, CNNProm, and reconstructed GraphPro identities. GraphPro
  Human/Mouse have fully recreated EPD coordinates; the six bacteria have
  reconstructed Promotech coordinates, but five still need primary-study row
  sampling and Rhodobacter lacks an accessible published primary coordinate
  source. CDBProm rows are sequence-only, CNNProm metadata are heterogeneous,
  and the nominal Bhandari Plant file contains exclusively `mm10` coordinate
  headers. No pilot was selected and every construction/training gate remains
  closed.
- Completed: freeze the GraphPro primary-TSS manual sample contract before
  reading primary coordinate tables. Five publication-backed bacterial sources
  receive deterministic ten-row, strand-aware samples. Rhodobacter remains a
  separate blocker: GSE117537 exposes 4,045 rows and therefore cannot silently
  replace the 5,374-row Promotech candidate. Primary file acquisition and the
  row comparisons remain pending.
- Completed: acquire and hash the five official Promotech BED inputs and
  materialize the frozen manual sample. All input hashes match the existing
  source registry; the output contains 50 rows (10 per dataset) with SHA-256
  `751a9a757f0b0080dc9aa3778c3c94c87d057e6b74a49cacfe5754265d8c78f9`.
  Primary supplementary-table acquisition and coordinate comparison remain
  pending, and no dataset eligibility changed.
- Completed: acquire the primary Campylobacter, Chlamydia, and Leptospira
  supplements and compare their 30 frozen sample rows. All 30 match exact
  one-based TSS position and strand after the declared BED0-to-publication
  conversion. The ledger preserves repeated source annotations at identical
  coordinate/strand pairs. Bacillus remains blocked because its exact
  supplement has not been acquired; E. coli remains blocked because the
  provenance of the published 278-row subset is not yet identified. No
  eligibility, split, or execution gate changed.
- Next: obtain the exact Bacillus supplement and resolve the E. coli 278-row
  selection rule, then finish the immutable five-source comparison. Continue
  to keep reconstruction, split, canonical, and embedding jobs blocked.
- Completed: resolve the nominal E. coli source identity. The 278 Promotech BED
  rows match the 278 ordered rows of Scientific Reports Supplementary Dataset
  S1 exactly by converted coordinate, strand, and locus. All 278 published
  51-nt windows match the pAA plasmid reference `NC_018666.1`; zero BED rows
  declare that accession because all are mislabeled `NC_000913.3`. The nominal
  MG1655 reconstruction and its controls, split, distribution, similarity, and
  dependency artifacts are invalidated and retained only for provenance. No
  source file was edited or relabeled.
- Next: define a fresh pAA-specific reconstruction contract using
  `NC_018666.1`, while continuing the legitimate search for a coordinate-level
  Bacillus supplement. Do not generate pAA controls or splits until the new
  contract is frozen; all model-execution gates remain closed.
- Decision: defer the complete GraphPro line, including released datasets,
  bacterial reconstructions, the pAA successor, Bacillus source resolution,
  and Human/Mouse EPD reconstructions. Existing artifacts and immutable
  contracts remain preserved as exploratory provenance; no additional GraphPro
  audit, reconstruction, control, split, eligibility, or training work is
  active. The deferral is recorded in
  `configs/graphpro_deferral_policy_v1.yaml` and can be reversed only by a new
  explicit project decision.
- Completed: freeze and execute the active classical-baseline consolidation
  for the 18 eligible CDBProm/CNNProm datasets. It reuses completed logistic
  and ten-seed XGBoost results, excludes GraphPro by the independently defined
  eligibility scope, and performs no new model fitting. XGBoost wins 17 of 18
  datasets; its median paired MCC advantage is 0.0681 with bootstrap 95%
  interval [0.0361, 0.0927] and two-sided Wilcoxon p=0.00001526.
- Next: prepare the already drafted 18-dataset basic-CapsProm GPU v3 campaign
  and predeclare the subsequent representation/model comparison. Keep
  canonical folds, final fits, external tests, and embedding jobs closed until
  a bounded execution tranche is explicitly released.
- Completed: create the execution-enabled v4 successor and release exactly five
  training-only folds for CDBProm Chlamydophila at seed 13 on `bioserver03`.
  All five completed on their first attempt with mean inner-validation MCC
  0.757628 and sample standard deviation 0.031603. The lower-median rule selects
  epoch 30 from best epochs 31, 41, 7, 30, and 25. The persistent launcher
  exited zero, SQLite passed integrity checking, 55 files were hash-manifested,
  and the plan records no external-test access. One fold reached the 50-epoch
  ceiling and is retained as a monitoring signal; no budget was changed after
  observing the result.
- Completed: copy the v4 seed-13 campaign boundary directly from `bioserver03`
  to `bioserver04`. A checksum dry run reports no differences, the snapshot has
  55 files, and its SQLite copy independently passes integrity checking with
  the same five finished children and one open campaign parent.
- Completed: review the v4 seed-13 tranche locally (values consistent, within
  release v3) and predeclare the next unit, Chlamydophila seed 29 folds 0-4,
  as the closed draft `configs/capsprom_campaign_release_v4.yaml`. The unit
  comes from the deterministic smallest-dataset-first schedule.
- Completed: after explicit authorization, synchronize `src/` and `scripts/` to
  `bioserver03` without changing the v4 contract. The inner-fold path was
  verified unchanged. The readiness refresh marked only Chlamydophila seed 13
  `ready_for_final_fit` (epoch 30), and a rerun was idempotent. All 18 data and
  fold-manifest hashes matched, and SQLite integrity was `ok`. No training ran.
- Completed: release v4 ran Chlamydophila seed 29, folds 0-4, in 54 seconds,
  with exit code 0 and every fold completing on its first attempt. Mean
  inner-validation MCC is 0.759851 (SD 0.044298), and the lower-median epoch
  is 23. Two of five folds reached the 50-epoch ceiling, which is recorded as a
  monitoring signal only. All hashes match and SQLite is `ok`. The backup on
  `bioserver04` is checksum-verified.
- Completed: releases v5 (seed 42) and v6 (seeds 71-293) finished all 10
  contract seeds for Chlamydophila, 50 inner folds in total, each completing on
  its first attempt. All 10 units are `ready_for_final_fit`. The mean of seed
  means is 0.752760 (SD 0.009823). Sixteen of 50 folds ran the full 50 epochs,
  so the budget is often binding; this is recorded only. The backup on
  `bioserver04` is checksum-verified. The tranche runner now accepts a `seeds`
  list.
- Decision (2026-10-27, user): keep the 50-epoch ceiling. Contract v4 is
  unchanged for the whole campaign, and ceiling contact stays a reported
  monitoring statistic, not a trigger for adaptation.
- Completed: release v7 ran Corynebacterium glutamicum (906 rows), all 10
  seeds and 50 folds, in 11 min 14 s, with exit code 0 and every fold completing
  on its first attempt. The mean of seed means is 0.770813 (SD 0.006269). 13 of
  50 folds reached the ceiling. All 20 units are `ready_for_final_fit`. All
  hashes match and SQLite is `ok`. The backup on `bioserver04` is
  checksum-verified.
- Completed: release v8 ran `cnnprom-prokaryotic-Bacillus` (1,098 rows), all
  10 seeds and 50 folds, in 13 min 3 s, with exit code 0 and every fold
  completing on its first attempt. The mean of seed means is 0.752207 (SD
  0.005389). 24 of 50 folds reached the ceiling, the highest share so far
  (recorded only). All 30 units are `ready_for_final_fit`. The backup is
  checksum-verified, and the remote output uses about 20 MB per fold.
- Completed: release v9 ran `cdbprom-prokaryotic-helicobacter_pylori` (1,130
  rows), all 10 seeds and 50 folds, in 13 min 56 s, with exit code 0 and every
  fold completing on its first attempt. The mean of seed means is 0.892857 (SD
  0.008179). 36 of 50 folds reached the ceiling, and seed 293 selected epoch 50
  (recorded only; the ceiling is kept by decision). All 40 units are
  `ready_for_final_fit`, and the backup is checksum-verified.
- Completed: release v10 ran `cdbprom-prokaryotic-salmonella_typhimurium`
  (1,564 rows), all 10 seeds and 50 folds, in 15 min 30 s, with exit code 0
  and every fold completing on its first attempt. The mean of seed means is
  0.865136 (SD 0.006930). 37 of 50 folds reached the ceiling (recorded only).
  All 50 units are `ready_for_final_fit`, and the backup is checksum-verified.
  Later backups use `rsync --link-dest` so that `bioserver04` does not fill up.
- Completed: release v11 ran `cdbprom-prokaryotic-bacillus_amyloliquefaciens`
  (1,692 rows), all 10 seeds and 50 folds, in 12 min 59 s, with exit code 0
  and every fold completing on its first attempt. The mean of seed means is
  0.663824 (SD 0.007074), the lowest dataset so far. Only 9 of 50 folds
  reached the ceiling. All 60 units are `ready_for_final_fit`. The first
  hardlinked backup is verified and used about 1 GB of new space.
- Next: release the next scheduled dataset,
  `cdbprom-prokaryotic-klebisiella_pneumoniae` (2,124 rows), all 10 seeds.
  600 inner folds remain, and final fits, external tests, and embeddings
  remain closed.

## Phase 5: Interpretability and Thesis Artifacts

Status: planned.

Goals:

- Relate learned patterns to candidate motifs and biological concepts.
- Generate plots, tables, and LaTeX snippets.
- Document where each artifact belongs in the thesis.

Exit criteria:

- Experimental outputs can be directly reused in doctoral writing.
