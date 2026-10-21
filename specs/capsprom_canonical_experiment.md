# Canonical Basic CapsProm Experiment Contract

## Status and purpose

This document defines the design boundary for the first multi-dataset basic
CapsProm evaluation. It does not authorize external-test execution. Test files
remain unavailable to model selection until the orchestration, prediction,
provenance, and statistical-analysis gates are implemented and validated.

## Frozen baseline identity

The basic CapsProm baseline consumes only strict-DNA one-hot input
`z_i = phi_one_hot(x_i)` with shape `81 x 4`. It uses the two-class-capsule
architecture, final-iteration dynamic-routing gradients, a structurally
disabled decoder, capsule margin loss, Adam at fixed learning rate `0.0001`,
batch size 64, maximum 30 epochs, and patience 15. Runner contract version 6
selects checkpoints by inner-validation MCC, using validation loss only to
break exact MCC ties.

The baseline input interface is intentionally narrow. Although the feature
pipeline can produce named multi-head mappings, the current `CapsProm.forward`
method accepts only a tensor with shape `[batch, 81, 4]`. Multi-head features
and trainable embeddings are therefore separate model families rather than
silent changes to basic CapsProm.

## Dataset and replication scope

The eligible set is the 26 collision-free, within-class-deduplicated,
group-partitioned strict-DNA v3 train/test pairs listed in
`configs/capsprom_basic_canonical_v1.yaml`. Every pair must pass the frozen
exact-identity audit before execution. Dataset identity is the canonical stem
before class counts and the `train` or `test` suffix.

The stochastic seeds are `13, 29, 42, 71, 101, 137, 173, 211, 251, 293`.
Dataset-level reporting aggregates the ten runs by median and interquartile
range, with mean and standard deviation as supplementary descriptors. A failed
seed is reported and never silently replaced.

## Inner-training selection

The five-fold stratified manifest generated from each training partition with
seed 42 is the only source for epoch selection. Each run seed trains one model
per fold without reading the external test partition. The selected epoch count
is the lower median of the five fold-specific best epochs, making the rule
integer-valued and deterministic. A final model is then initialized with the
same run seed and fitted on the complete training partition for exactly that
many epochs. The external test partition is evaluated once by that final model.

Epoch selection is materialized as a separate atomic plan transition. The
`refresh-neural-canonical-readiness` command validates the immutable protocol
hash, requires all five inner-fold jobs to be complete, stores their best
epochs and lower median, and changes only the corresponding final job to
`ready_for_final_fit`. The operation is idempotent and requires
`external_test_accessed=false`; it neither trains a model nor accepts an
evaluation path. Readiness therefore does not imply authorization to run a
final fit or open an external test partition.

This rule separates epoch selection from final fitting and avoids withholding
part of the already limited training partition during final evaluation. It also
requires six fits per dataset and seed: five inner-fold fits and one final fit.
The resulting canonical plan therefore contains 1,560 fits before retries:
`26 datasets x 10 seeds x 6 fits`.

## Capsule score and prediction contract

For output-capsule lengths `a_i0` and `a_i1`, the persisted positive-class
score is

```text
s_i = a_i1 / (a_i0 + a_i1).
```

This is a relative score, not a calibrated probability. The binary prediction
is the index of the largest raw capsule length. For non-tied finite scores this
is equivalent to `s_i > 0.5`. Exact ties, including two zero lengths, are
assigned to class 0 by the deterministic first-index `argmax` rule. Raw class
lengths, the relative score, prediction, true label, and stable row identifier
must all be persisted. Sigmoid or isotonic calibration, when enabled, is a
separately labeled secondary condition fitted only from out-of-fold training
scores.

## Feature and embedding extension boundary

A trainable nucleotide embedding maps integer nucleotide tokens to learned
vectors before convolution. For one-base tokens, applying a bias-free learned
linear projection to a one-hot vector is algebraically equivalent to an
embedding lookup. Consequently, a future embedding experiment should replace
the one-hot input branch rather than concatenate a redundant learned projection
of the same tokens.

Integer tokenization such as `A=0`, `T=1`, `C=2`, and `G=3` is valid when the
integers are used only as lookup indices. Their numeric order has no geometric
meaning inside an embedding table. Passing those integers directly as scalar
features is prohibited because it would impose artificial ordinal distances.
New code uses the repository-wide canonical vocabulary order `A,C,G,T`; another
ordering is scientifically equivalent only when it is recorded and applied
consistently. For k-mers, the preferred vocabulary is the deterministic
lexicographic product of `A,C,G,T`, with overlapping stride-one tokens. Fixed
81-base strict-DNA inputs require neither padding nor an unknown token; any
future variable-length or ambiguous-alphabet experiment must reserve separate
padding and unknown identifiers rather than reuse a biological token.

The first embedding ablation should vary only the representation and use a
small predeclared embedding dimension. It is named `Embedding-CapsProm`, not
basic CapsProm, and must be compared against the frozen one-hot baseline under
the same datasets, seeds, selection rule, and training budget.

Multi-head CapsProm variants require explicit branches and fusion:

- Sequence-aligned matrices, such as physicochemical profiles, may use an
  independent convolutional or capsule branch before late fusion.
- Global vectors, such as k-mer frequencies, GC/skew, PseKNC, or pooled
  DNA-BERT embeddings, require a vector branch and cannot be passed directly to
  the current spatial convolution.
- Fusion must be named and versioned. Concatenation before a classification
  head is the minimal control; attention or routing-based fusion is a later
  architectural hypothesis.

No embedding or multi-head result may redefine the basic CapsProm baseline.
These variants are evaluated only after the canonical one-hot execution is
operational and its contracts are frozen.

### Future physicochemical initialization

A future, separately versioned ablation will initialize dinucleotide or
trinucleotide token embeddings from the normalized physicochemical reference
tables. The hypothesis is that biologically informed initialization provides a
more useful local geometry than random initialization, particularly for smaller
training sets, while subsequent adjustment may adapt that prior to promoter
classification.

Two conditions are required: a frozen table, which measures the value of the
fixed physicochemical prior, and a trainable table initialized from the same
values, which measures the additional value of task-specific adjustment. Both
must be compared with a randomly initialized trainable embedding of identical
dimension and architecture. Possible integration points are replacement of the
one-hot input before the first convolution, a separate sequence-aligned branch
in a multi-head model, or initialization of primary token projections. The
reference TSV hash, property order, normalization, token vocabulary, trainable
flag, and fold-local training provenance must be recorded. This ablation is
planned only; no implementation, configuration, MLflow run, or result currently
exists.

### Contextual representation modes

The current DNA-BERT feature encoder tokenizes a sequence into overlapping
six-mers, runs a pretrained transformer, pools its hidden states, and returns a
sequence-level feature vector in memory. The ordinary experiment runner consumes
that vector but does not provide a canonical persistent embedding cache.
Consequently, a feature configuration describes how to compute DNA-BERT
features; it is not evidence that they were materialized or used by CapsProm.

Three future training modes are distinct:

1. A frozen precomputed contextual vector is cached and passed to a new vector
   branch. CapsProm can train only a projection/fusion layer above it.
2. Tokens are passed through a frozen contextual encoder during every batch.
   This avoids a cache but recomputes identical representations.
3. Tokens are passed through a trainable contextual encoder. Gradients update
   the encoder jointly with CapsProm and representations cannot be safely
   precomputed.

For fold safety, any trainable tokenizer vocabulary, normalization, projection,
or contextual encoder adaptation is fitted inside each training fold. A frozen
pretrained encoder may be cached by sequence hash, model revision, tokenizer
revision, pooling rule, and preprocessing hash because it never observes fold
labels. Fine-tuned representations must never be reused across folds. Joint
contextual training has the highest accelerator memory and runtime cost and
requires checkpointing both models, optimizer state, and exact pretrained
revision. The existing basic CapsProm supports none of these three fusion paths;
they require an embedding/token interface and architecture-specific branches.

## Implementation gates before test execution

1. Validate relative capsule scoring, tie handling, batch invariance, and
   continuous-versus-resumed equivalence with fixture data.
2. Generate and hash one five-fold manifest for every canonical training pair.
3. Add resumable parent/child orchestration for dataset, seed, fold, and final
   fit without accepting test input during inner selection.
4. Add a final-fit/inference stage that opens the test file only after the
   selected epoch and final-training contract have been atomically persisted.
5. Persist raw capsule lengths and row-level scores and predictions, then run
   effectiveness, calibration, efficiency, bootstrap, and paired-comparison
   code on fixtures.
6. Run training-only feasibility checks on the smallest and largest training
   pairs before scheduling the full 1,560-fit campaign.

### Fixture-only final-fit checkpoint

The fourth and fifth gates have been exercised without enabling canonical test
access. The fixture path requires all five inner folds to be complete, persists
their best epochs and the lower-median selected epoch atomically, and fits the
full training fixture for exactly that count. Only after the completed
final-training state exists may it open an explicitly declared evaluation
fixture. Passing `fixture_only=false` is rejected, and the canonical
`external_test_accessed` flag remains false throughout.

The resulting row artifact contains stable row identifiers, labels, both raw
capsule lengths, the relative positive score, and the argmax prediction. A
separate hashed metrics artifact covers effectiveness and calibration measures.
First-convolution activation windows and their PFM, PPM, and SVG sequence logo
are extracted only from the full training partition and attached to the same
MLflow final-fit child run. These outputs validate mechanics and provenance;
they are not predictive or biological evidence.

A simulated interruption after artifact persistence and before MLflow logging
was resumed using the same atomic final-fit state and deterministic run
identity. Continuous and resumed executions produced byte-identical row
artifacts and equal metrics, one parent run, five fold child runs, and one
final-fit fixture child run. This does not authorize real final fits or external
test access.

### Synthetic feasibility checkpoint

The sixth gate is scoped to the frozen one-hot basic CapsProm because it is the
new computational bottleneck of this campaign. It is not a retrospective
benchmark of logistic regression or XGBoost, whose complete canonical runs
already provide measured runtime evidence. The CNN control should use the same
measurement harness if promoted beyond development diagnostics. Embedding,
multi-head, and contextual variants require separate feasibility contracts only
after their architectures exist; this checkpoint does not authorize their jobs.

Version 1 uses reproducible balanced synthetic strict-DNA sequences with the
real `81 x 4` `float32` one-hot input, frozen architecture, batch size 64, and
one epoch. Its 646- and 37,438-row scenarios equal the smallest and largest
canonical training cardinalities. The machine-local criteria classify an
out-of-memory error, non-zero exit, or more than 1,800 wall seconds for either
one-epoch scenario as infeasible. Completion measures per-fit executability;
campaign scheduling must additionally consider the extrapolated total cost.

On the recorded CPU-only WSL2 host (6 physical/12 logical CPUs, 8.22 GB RAM,
PyTorch 2.13.0), the small scenario required 0.060 seconds of fixture
preparation, 20.11 seconds of training, 41.93 seconds subprocess wall time, and
539.0 MB peak RSS. The large scenario required 1.468 seconds of preparation,
77.10 seconds of training, 100.34 seconds wall time, and 3.607 GB peak RSS. Both
completed without OOM, so an individual fold is computationally executable on
this host. GPU memory was not measured because CUDA was unavailable.

A linear row-throughput projection from the large fixture gives approximately
4.12 CPU hours per campaign-wide epoch equivalent and 123.5 CPU hours at the
30-epoch maximum before validation, checkpoint, retry, and process overhead.
Early stopping may reduce this figure, and parallelism or a GPU may alter it;
therefore this is a scheduling estimate rather than a runtime guarantee. The
measurement cannot support conclusions about predictive performance or
biological validity. Canonical and embedding jobs remain blocked.

The same fixtures were subsequently executed on `bioserver03` with an NVIDIA
GeForce RTX 3060 (12 GB), 10 physical/20 logical CPU cores, 67.25 GB RAM,
Python 3.13.16, and PyTorch 2.11.0+cu128. Runner contract version 7 adds an
explicit `cpu`, `cuda`, or `auto` device field and transfers the model, training
batches, validation tensors, and resumed checkpoints to the resolved device.
Contracts 2 through 6 retain their previous serialized identity and remain
CPU-only; the immutable canonical version 1 configuration is therefore not
silently converted to GPU execution.

On the RTX 3060, the 646-row fixture required 0.038 seconds of preparation,
1.164 seconds of training, 3.389 seconds subprocess wall time, 1.729 GB peak
RSS, 156.7 MB peak allocated GPU memory, and 182.5 MB peak reserved GPU memory.
The 37,438-row fixture required 1.166 seconds of preparation, 5.132 seconds of
training, 8.460 seconds wall time, 1.824 GB peak RSS, 3.121 GB allocated GPU
memory, and 3.913 GB reserved GPU memory. Both passed without OOM. Relative to
the CPU fixture, large-scenario training was approximately 15 times faster.

A linear throughput projection is about 0.274 GPU hours per campaign-wide epoch
equivalent and 8.22 GPU hours at the 30-epoch maximum. This excludes validation,
checkpointing, job startup, retries, contention, and early stopping and is not
a scheduling guarantee. CPU used PyTorch 2.13.0+cpu whereas the available CUDA
index supplied PyTorch 2.11.0+cu128; numerical and resume equivalence must be
validated under the versioned GPU contract before any canonical run. The remote
neural fixture suite passed 29 tests. The complete remote suite had 68 passes
and 8 expected data-dependent failures because raw reference tables and the
processed dataset collection were intentionally not copied.

Runner-version-7 resume equivalence was subsequently validated on the same RTX
3060 using a balanced 64-row strict-DNA fixture, three epochs, batch size 16,
and a controlled interruption after the first atomic state write. The first
attempt exposed that CUDA `map_location` moved the saved DataLoader RNG state to
the GPU even though `torch.Generator.set_state` requires a CPU byte tensor. The
runner now explicitly restores the DataLoader and global PyTorch RNG states on
CPU while leaving model and optimizer checkpoint tensors on the requested
device.

After that correction, continuous and resumed executions selected epoch 3 and
completed three epochs with exactly equal histories, parameters, capsule
lengths, relative positive scores, and predicted classes. The predeclared
acceptance limits were absolute difference at most `1e-7` for history metrics,
model parameters, and capsule scores, with exact equality for predictions and
selected epoch. The observed maximum difference was zero in every numerical
category. This same-host result validates resume mechanics for the recorded GPU
stack; it does not claim equality with the CPU/PyTorch-2.13 environment.

The separate draft `configs/capsprom_basic_canonical_gpu_v1.yaml` therefore
uses runner contract 7 and explicit `device: cuda` while preserving the model,
data, seeds, folds, optimizer, and prediction policies of the version-1 CPU
design. Its canonical and embedding execution gates remain false, no plan state
has been created, and no real job has started.

The reviewed training-only contract and exactly 26 training CSV files were
then synchronized to `bioserver03`. All remote file hashes matched their local
counterparts, and no `*-test.csv` file was transferred. Plan preparation wrote
26 fold manifests and 1,560 jobs: 1,300 inner folds remain pending, 260 final
fits remain blocked pending epoch selection, no MLflow run identifier exists,
and `external_test_accessed` remains false. The plan is bound to protocol hash
`0d1c3f565ffbcb9076a1de8dd97d9d9591350c8d6fa59913144c70a59f920581`.
The executor also enforces `canonical_jobs_enabled: false`; therefore an
accidental manual fold command is rejected before run creation or training.

### Remote worker and tracking policy

Remote access is governed by the active local-first policy in
`configs/capsprom_remote_usage_policy_v2.yaml`. The worker and tracking topology
below applies only after a heavy or many-run campaign receives explicit bounded
authorization. Routine development, testing, documentation, status inspection,
and incremental synchronization remain local. The earlier version-1 policy is
retained as the historical execution-topology record, but it no longer implies
routine remote availability.

The versioned remote policy assigns one CUDA training worker to `bioserver03`.
Although the 12 GB GPU could hold more than one small fixture, production
concurrency is fixed at one to isolate memory, timing, deterministic-kernel,
checkpoint, and failure behaviour. The bounded dispatcher rejects duplicate
job identities and permits a larger worker count only when an explicit fixture
or future contract requests it.

MLflow uses one contract-local SQLite database and artifact directory on the
same host and filesystem as the worker. Parent/child identity creation remains
protected by the filesystem lock, while plan updates remain protected by the
atomic plan lock. The SQLite file is not shared over a network filesystem.
`bioserver04` is reserved for future CPU-only audits, bootstrap calculations,
summaries, or report generation; it has zero canonical training workers and
must use an independent store or a real tracking server rather than directly
opening the GPU host's SQLite database.

The coordination fixture deliberately stressed the implementation with two
simultaneous CPU workers and two distinct folds. On `bioserver03` it completed
with one parent and two finished child runs, while preserving two completed
plan jobs. This validates locking and SQLite identity coordination under more
concurrency than the one-worker GPU policy, but it does not authorize canonical
training. The production contract, final fit, external test, and embedding
gates remain false.

### Scheduling, retention, failure, and backup policy

The deterministic queue orders eligible inner folds by ascending training-row
count, dataset identifier, seed, and fold. This exercises the smallest datasets
first while making restart order independent of filesystem enumeration. Failed
folds are eligible for retry up to three total attempts; a third failure leaves
the job failed for manual diagnosis. Final fits never enter this queue.

During an active fold, the best checkpoint, latest optimizer checkpoint, and
atomic state are retained. After the child run is finished and both database
and artifact snapshots have been verified, the latest optimizer checkpoint is
eligible for removal; the best checkpoint, state, and hashes remain available
for audit and fold-level explainability. The measured full-model checkpoint is
10,456,705 bytes. Retaining all 1,560 best checkpoints projects 16.31 GB, while
retaining best and latest projects 32.62 GB, against 106.34 GB available on the
recorded host. These are storage estimates, not transfer-time guarantees.

Failures create one atomic filesystem-outbox JSON event per job, recording the
attempt, child run identifier, and error. A successful retry marks the same
event resolved without erasing its audit trail. External delivery is not yet
configured, so the outbox is a durable notification source rather than a claim
that email or messaging was sent.

SQLite backups use the online backup API, atomic destination replacement,
SHA-256 hashing, and `PRAGMA integrity_check`. Database backup is separate from
the artifact snapshot: both must succeed before retention pruning. The planned
artifact snapshot uses checksum-verified `rsync` to `bioserver04`; the fixture
at this gate validates the database backup and manifest but does not transfer
canonical artifacts or delete checkpoints.

The cross-host fixture was subsequently completed. A project-specific private
key remains only on `bioserver03`, and its public key authorizes the backup
account on `bioserver04`. A two-file artifact snapshot was transferred directly
between hosts with `rsync --checksum`; independent destination verification
reported the expected two files with no missing, unexpected, or mismatched
entries. A separate 12,288-byte SQLite fixture was backed up through the online
API, copied to the CPU host, and verified there against its SHA-256 manifest,
`PRAGMA integrity_check = ok`, and expected finished-run row. These fixtures
validate transport and restore auditing, not durability of a future full
campaign. No canonical checkpoint, MLflow database, or result was transferred.

### Execution candidate authorization boundary

`configs/capsprom_basic_canonical_gpu_execution_v1.yaml` was reviewed as the
candidate for inner-fold execution. It preserves the blocked GPU contract's
datasets, fold construction, seeds, architecture, optimizer, selection rule,
and prediction policy. Its only operational changes are new protocol and MLflow
experiment identities, explicit host-local SQLite and artifact URIs, and an
enabled inner-fold gate. It also introduces an explicit false final-fit gate;
external-test and embedding gates remain false.

MLflow experiment creation binds the declared artifact URI on first creation
and rejects an existing experiment with a conflicting URI. This prevents a
resume from silently splitting metadata and artifacts across stores. The
candidate initially had no plan state and was not synchronized to
`bioserver03`. Creating its plan and running even one real fold required a
separate, explicit authorization checkpoint; drafting or testing the file was
not that authorization.

After that authorization, the contract was copied with SHA-256
`500fe8d624801fb6d72f608efb3315716bd65b77c7dd93d330bbce614208b332`
and a new training-only plan was created. The deterministic scheduler selected
the 646-row `cdbprom-prokaryotic-chlamydophila_pneumoniae` dataset, seed 13,
fold 0. Exactly this fold ran on `bioserver03`; it completed 30 epochs in 8.25
wall seconds, selected epoch 28, and recorded inner-validation MCC
`0.8008534347`. Peak process RSS was 1,902,356 KiB. This single validation-fold
measurement is an operational pilot, not an estimate of external-test
performance or evidence for model selection.

The plan contains one completed and 1,299 pending inner folds; all 260 final
fits remain blocked pending epoch selection and external-test access remains
false. MLflow contains one running campaign parent and one finished child run
(`a4c6ac3d689a42f39606a80bba26f1cd`) with the correct parent link, job identity,
metrics, and provenance artifacts. No second fold was claimed.

An online SQLite snapshot and a checksum manifest for the two MLflow provenance
files were copied directly to `bioserver04`. Independent destination validation
found no missing, unexpected, or mismatched artifacts; the database hash
matched its manifest and `PRAGMA integrity_check` returned `ok`. Checkpoints
remain on `bioserver03` and no retention pruning was performed. The campaign is
paused before further inner-fold execution.

A second explicit bounded authorization then covered only folds 1 through 4 of
the same dataset and seed. All four completed on their first attempt, leaving
five completed folds for this dataset/seed and no claimed job elsewhere. The
fold best epochs were 28, 26, 7, 30, and 25; therefore the predeclared lower-
median rule selects 26 epochs for a future full-training refit. Fold MCC values
were 0.8008534347, 0.7674922078, 0.7162640491, 0.7519230769, and 0.7476919615,
with mean 0.7568449460, sample standard deviation 0.0308420264, and median
0.7519230769. These are inner-validation diagnostics and must not be compared
as external-test estimates.

The updated plan has five completed and 1,295 pending inner folds. All 260 final
fits remain blocked and `external_test_accessed` remains false. MLflow contains
one campaign parent and five finished children with unique job identities. A
new, non-overwriting `five-fold-seed-13` snapshot was copied to `bioserver04`;
all 10 provenance files matched the checksum manifest, the SQLite hash matched,
and its integrity check returned `ok`. No checkpoint was pruned. Execution is
paused before another seed, dataset, final fit, embedding job, or external-test
operation.

A third bounded authorization covered only the five folds of the same dataset
at seed 29. All completed on their first attempt in 16.23 aggregate wall
seconds with 1,863,408 KiB peak process RSS. Fold best epochs were 23, 8, 23,
5, and 21, so the lower-median rule selects 21 epochs. Fold MCC values were
0.8157708706, 0.7371216163, 0.7213272630, 0.7519230769, and 0.6939441501;
their mean is 0.7440173954, sample standard deviation 0.0454994087, and median
0.7371216163. Together with seed 13, the plan now has 10 completed and 1,290
pending inner folds, while all 260 final fits remain blocked and external-test
access remains false.

MLflow has one campaign parent and 10 finished child runs with 10 unique job
keys. The non-overwriting `ten-fold-two-seeds` snapshot on `bioserver04`
contains all 20 expected provenance files with no missing, unexpected, or
mismatched entries. Its SQLite hash matches the manifest and its integrity
check returns `ok`. Execution is paused before seed 42 or any other dataset.

Explainability follows `specs/explainability_protocol.md`. The validated
infrastructure currently covers auditable first-convolution activation windows,
PFM/PPM and SVG sequence-logo artifacts, their original-sequence coordinates,
and attachment to the correct MLflow child run. Attribution, motif stability,
known-motif comparison, and biological interpretation require adequately
trained real models and remain blocked with real execution.

External-test execution remains blocked until all six gates pass `make check`
and a versioned status snapshot records the frozen protocol hash.

### Production final-fit and external-inference boundary

The production final-fit command accepts only `ready_for_final_fit`. It validates
the persisted lower median of the five fold-selected epochs, reloads the hashed
training partition, trains from initialization on all authorized training rows,
and atomically persists its optimizer/RNG checkpoint and state. Completion is
recorded as `completed_final_fit_training`; the command has no evaluation input
and cannot invoke external inference.

The external-inference command is separate. It checks
`external_test_enabled=true` before opening the supplied evaluation path and
requires a `completed_final_fit_training` state whose checkpoint and training-
state hashes still match. Current canonical contracts keep this gate false.
The command therefore exists for a future versioned release contract but is not
authorized by the current implementation milestone.

Local fixtures compare uninterrupted training with interruption after an epoch
and after final checkpoint persistence. Optimizer state, data-loader generator
state, PyTorch RNG state, epoch history, and model tensors are restored. Model
tensors and training histories must be exactly equal (zero numerical tolerance)
on CPU. MLflow reuse is verified by one final-training child identity under the
existing parent even when interruption occurs between local persistence and
MLflow completion. Absolute paths and their derived contract hashes naturally
differ when the two fixture modes use isolated temporary directories.
