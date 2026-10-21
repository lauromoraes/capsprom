# CapsProm Reproduction Contract

## Purpose

Phase 4 begins with a faithful, auditable reproduction of the original one-hot
CapsProm model before SparseCapsProm, attention, or multi-feature extensions are
introduced. This contract separates architectural fidelity from methodological
corrections required by the canonical evaluation protocol.

## Reference implementation

The architectural reference is commit
`9b08912648ff5d58a11ebb42225d9ad9851c61ac` of
`lauromoraes/CapsNet-promoter`, principally `capsulenet-onehot.py` and
`capsulelayers2.py`. The reference repository is MIT licensed.

The implementation in `src/capsprom/models/capsprom.py` is a clean PyTorch
translation. It does not depend on the legacy Keras/TensorFlow runtime and does
not copy the legacy experiment orchestration.

## Frozen reproduction architecture

The input is a strict-DNA one-hot tensor with shape `[batch, L, 4]`. The
initial canonical value is `L = 81`; another sequence length creates a distinct
versioned experiment contract.

1. A two-dimensional convolution spans all four nucleotide channels, with 256
   filters, kernel `(4, 9)`, unit stride, valid padding, and ReLU activation.
2. A primary-capsule convolution uses 256 output filters, kernel `(1, 9)`,
   stride `(1, 2)`, and valid padding.
3. The result is reshaped into 32 channels of eight-dimensional primary
   capsules and passed through the capsule squash nonlinearity. For `L = 81`,
   this yields 1,056 primary capsules.
4. A fully connected capsule layer transforms each primary capsule into one
   16-dimensional output capsule and applies three routing iterations. The
   routing logits are updated without backpropagating through intermediate
   agreement iterations; gradients pass through the final capsule computation.
5. The Euclidean length of the output capsule is the promoter score.
6. During training, the true-class capsule is retained and the other class
   capsule is zeroed; inference retains the largest-norm capsule. The complete
   masked tensor is flattened to 32 dimensions and passed through decoder hidden
   layers of 512 and 1,024 ReLU units to reconstruct the `L x 4` input through
   sigmoid outputs.
7. Training uses capsule margin loss plus the mean, across samples, of each
   sample's summed reconstruction squared error. The reconstruction coefficient
   is `0.0005`, matching the scale defined by the seminal CapsNet objective.

All dimensions, loss coefficients, optimizer settings, stopping rules, and
seeds must be recorded in the versioned YAML contract before a canonical run.

## Deliberate methodological corrections

The legacy script trained several seeds and selected the checkpoint with the
highest MCC measured on its held-out test partition. This leaks test outcomes
into model selection and must not be reproduced. Under the canonical protocol:

- checkpoint selection, early stopping, architecture decisions, and
  hyperparameter selection use only fixed inner-training folds;
- the external test set is evaluated once per frozen seed/configuration;
- row-level predictions, dataset hashes, fold-manifest hashes, configuration
  hashes, and MLflow run identifiers are retained;
- no test result may motivate CapsProm, SparseCapsProm, or attention design;
- canonical v3 collision-free, deduplicated, group-split datasets are used;
- comparisons use the same metrics and cross-dataset inference specified in
  `specs/statistical_evaluation_protocol.md`.

## Terminology and historical fidelity

In academic text, `CapsProm` and `basic CapsProm` refer exclusively to the
two-output-capsule architecture, with one capsule for each binary class. The
one-output implementation from the earlier publication is named
`legacy CapsProm-1C` and appears only in historical reproduction and
methodological analysis; it is not the basic model developed in this thesis.

## Known legacy issue and required control

The reference binary model creates one output capsule. Softmax routing is
therefore taken across a dimension of size one, so every coupling coefficient
is exactly one and routing iterations cannot redistribute coupling between
outputs. The implementation preserves this behavior for the reproduction.

The two-output-capsule formulation restores meaningful routing and is the basic
CapsProm architecture for this thesis. The legacy one-capsule implementation is
retained as a frozen reproduction reference rather than an active model-development
branch.

## Implementation boundary

The current milestone includes:

- decomposition of the former monolithic experiment module into data loading,
  model factory, evaluation, tracking, and runner modules, with a compatibility
  facade for frozen classical workflows;
- the PyTorch CapsProm architecture, squash function, dynamic-routing layer,
  margin loss, reconstruction loss, and synthetic shape tests;
- no access to canonical test outcomes and no neural training run.

The next implementation milestone is a neural-only configuration schema and
runner with deterministic seeding, inner-fold checkpoint selection, atomic
resume state, MLflow provenance, and a training-only smoke test. Only after
that runner and its contract pass validation may a canonical CapsProm run be
scheduled.

## Predeclared minimal ablations

The first architecture comparison must use a common one-hot input and fixed
inner-training partition. It comprises:

1. `cnn_control`, which uses a one-dimensional convolution, global max pooling,
   and a binary linear head;
2. `capsprom_basic` with one capsule for each class and uniform routing;
3. `capsprom_basic` with dynamic routing.

Legacy CapsProm-1C is evaluated separately only to reproduce the earlier work
and demonstrate the equivalence of its uniform and nominally dynamic routing.

The two-capsule decoder is class-conditioned: training uses the capsule selected
by the true inner-training label, while inference uses the capsule with the
largest norm. The reconstruction objective is retained initially and removal of
the decoder or a zero reconstruction coefficient is a later, separately
versioned ablation.

Model selection uses validation MCC from the fixed inner-training split. The
training-only runner accepts no external test input, writes its best and latest
checkpoints and state atomically, stores its complete contract and contract
SHA-256, rejects contract changes after state creation, and restores model,
optimizer, data-loader generator, and PyTorch random state after interruption.
Strict YAML loading and MLflow integration remain required before canonical
execution.

## Training-only integration smoke tests

The version 1 smoke contracts use 64 stratified samples from the already
exploratory GraphPro `clostridium_phytofermentans` training file, reserve 20%
for inner validation, and run one epoch. They do not name, load, or evaluate an
external test file. The strict YAML schema rejects unknown sections, including
an external test path, and MLflow records the configuration hash, training-data
hash, seed, architecture identity, run identifier, and inner-validation result.

Both initial integration runs produced inner-validation MCC zero. The one-capsule
model predicted all 13 validation records as positive; the two-capsule model
predicted all records as negative. These outcomes verify end-to-end execution
and expose early class-collapse behavior, but one epoch on 64 samples is not an
effectiveness experiment and must not guide architecture selection.

## Training-only learnability diagnostic

Before any external-test protocol is defined, version 1 freezes a two-arm
diagnostic comprising the CNN control and basic CapsProm. Both arms
uses the same deterministic 128-record sample, 20% inner-validation split, seed
42, batch size 32, Adam learning rate 0.001, at most ten epochs, and patience
three. Capsule dimensions remain faithful to the reproduction architecture.

This diagnostic answers only whether each active implementation can move beyond
single-class predictions under a small controlled training task. Its observed
inner-validation metrics may be reported as engineering diagnostics but must
not select architectures, tune hyperparameters, or enter confirmatory claims.

Runner version 2 uses lexicographic checkpoint and patience improvement: higher
inner-validation MCC is preferred, and lower validation loss breaks exact MCC
ties. Version 1 stopped basic CapsProm after repeated MCC zero even while its
validation loss was still decreasing; its state remains preserved and version
2 uses distinct checkpoint and state paths.

The basic CapsProm version 2 diagnostic still predicted every inner-validation
record as promoter and reached MCC zero. A separate balanced eight-sequence
sanity check reached 100% training accuracy at epoch six, demonstrating that
the implementation and objective can fit a simple discriminative task. The
small exploratory biological sample therefore does not establish learnability,
but the failure is not by itself evidence of a broken gradient path. The next
diagnostic may increase training-only data and duration without consulting an
external test split or changing the frozen architecture.

The subsequent full-training-split contract uses all 747 records from the same
exploratory training file, a fixed 20% inner-validation split, batch size 64,
at most 30 epochs, and patience five. Architecture, optimizer, learning rate,
seed, and reconstruction coefficient remain unchanged. This isolates the effect
of a less data-starved training regime and still excludes the external test
file.

With gradients propagated through every routing iteration, version 1 stopped
after six epochs and predicted every validation record as promoter, producing
MCC zero. Version 2 makes the routing-gradient policy explicit and detaches the
votes used by intermediate agreement updates while retaining the gradient path
through the final iteration. It stopped after 19 epochs and selected epoch 14,
with inner-validation MCC 0.1986 and confusion counts TN=53, FP=16, FN=47, and
TP=34. This result establishes that the basic CapsProm implementation can leave
single-class collapse on the exploratory biological split. It is an engineering
diagnostic, not an external-test result or evidence for comparative superiority.

The final-iteration policy is the canonical basic CapsProm routing-gradient
policy for subsequent newly versioned development contracts. The full-gradient
mode remains available only to reproduce the already executed diagnostic; it
must not be substituted silently in an existing contract.

## Seminal-alignment contract version 3

Repository comparison identified two additional differences between the initial
two-capsule adaptation and widely used implementations of the seminal CapsNet.
The earlier runner passed only the selected 16-dimensional vector to the
decoder and multiplied a globally averaged reconstruction error by `0.0005`.
Version 3 instead flattens the class-masked two-capsule tensor and uses summed
per-sample squared error. The basic model defaults are now two output capsules,
final-iteration routing gradients, and the masked-flat decoder. A dedicated
`LegacyCapsProm1CConfig` preserves the historical one-capsule defaults.

Contracts from runner version 2 retain selected-vector decoding and globally
averaged reconstruction when loaded, and their original hashes remain valid.
The new behavior requires `contract_version: 3`, `decoder_mode:
masked_flatten`, and `reconstruction_reduction: sum_per_sample` in YAML.

The first version 3 training-only diagnostic stopped after six epochs and
remained in promoter-only collapse, with inner-validation MCC zero. This does
not invalidate the seminal alignment; it shows that the decoder and loss-scale
corrections also change optimization materially. Their effects must be isolated
with predeclared inner-training ablations before external-test evaluation.

### Predeclared decoder and reconstruction ablation

The component ablation is a `2 x 2` factorial diagnostic. It crosses decoder
input (`selected_vector` or `masked_flatten`) with reconstruction reduction
(`mean` or `sum_per_sample`). Every arm uses the same 747-record exploratory
training file, deterministic 20% inner-validation split, seed 42, batch size 64,
Adam learning rate 0.001, final-iteration dynamic routing, at most 30 epochs,
and patience 15. The longer patience is fixed for all arms because the earlier
selected-vector diagnostic did not leave class collapse until epoch 14; patience
five therefore confounded component behavior with premature stopping.

The four contracts have independent checkpoint and state paths. Their purpose
is to diagnose optimization and loss construction, not to select a model from
external-test performance. The primary observations are whether both classes
are predicted, the epoch at which collapse is left, inner-validation MCC,
confusion counts, and validation-loss trajectory.

All four arms completed. Both `selected_vector` arms left collapse, whereas
neither `masked_flatten` arm predicted both classes in any epoch. Selected-vector
with mean reconstruction first predicted both classes at epoch 14 and selected
epoch 29 (MCC 0.2012; TN=47, FP=22, FN=39, TP=42). Selected-vector with summed
reconstruction first predicted both classes at epoch 19 and selected epoch 29
(MCC 0.1673; TN=59, FP=10, FN=58, TP=23). Both masked-flat arms stopped after
epoch 16 with epoch 1 as their best checkpoint, promoter-only predictions, and
MCC zero.

Gradient checks found finite nonzero gradients in the initial convolution,
primary capsules, routing transformation, and decoder for all four arms. At the
common initialization, the routing-weight gradient norm from margin loss was
approximately `1.04e-1`; the weighted reconstruction-gradient norms were only
`9.90e-9` to `1.46e-8` under mean reduction and `3.21e-6` to `4.72e-6` under
summed reduction. Reconstruction therefore does not numerically dominate the
classification objective. Instead, the sharp trajectory change under very small
decoder-dependent perturbations indicates fragile optimization near a
single-class solution. The training computation is connected and internally
consistent, but it is not yet robust enough to freeze as the confirmatory
protocol.

### Predeclared no-reconstruction stability control

The next diagnostic removes the auxiliary reconstruction contribution by fixing
its weight at zero. It retains selected-vector decoding only as an inert
implementation detail: with zero reconstruction weight, decoder outputs cannot
change any encoder or capsule parameter. Five independent inner-training runs
use seeds 23, 29, 31, 37, and 42. All other settings are fixed to the component
ablation: the same 747-record exploratory training file, stratified 20%
inner-validation split, batch size 64, Adam learning rate 0.001, 30 epochs,
patience 15, two output capsules, and final-iteration dynamic routing.

The diagnostic evaluates whether the margin-loss CapsProm core consistently
leaves single-class collapse. It records the proportion of seeds predicting
both classes, best inner-validation MCC, first two-class epoch, and confusion
counts. It does not compare or inspect any external test outcome.

Four of five runs left single-class collapse. Seeds 23, 29, 31, and 37 reached
best inner-validation MCC values 0.2328, 0.3373, 0.2303, and 0.3536; their first
two-class epochs were 6, 15, 3, and 15. Seed 42 never predicted both classes and
ended with MCC zero. The median best MCC across all five seeds was 0.2328, and
the collapse rate was 20%.

At the selected checkpoints, confusion counts `(TN, FP, FN, TP)` were
`(39, 30, 27, 54)`, `(29, 40, 10, 71)`, `(37, 32, 25, 56)`, and
`(43, 26, 22, 59)` for the four non-collapsed seeds. Seed 42 selected a
promoter-only checkpoint `(0, 69, 0, 81)`. These observations confirm that the
margin-loss core is learnable but not seed-stable under the current fixed
optimizer contract. Reconstruction is not required for learning, and its
presence can either perturb the model out of or into a collapsed trajectory;
it must not be relied upon as an implicit optimization mechanism.

### Predeclared learning-rate stability control

The fixed-rate results above form the control arm for a five-seed optimizer
diagnostic. The comparison arm uses the same seeds, data, split rule, batch size,
maximum epochs, patience, margin loss, and capsule architecture, but multiplies
the learning rate by `0.9` after every epoch. This reproduces the epoch-wise
exponential schedule used by the historical CapsProm training script without
introducing a data-dependent scheduler.

Runner contract version 4 can disable the decoder structurally. A disabled
decoder is not instantiated, its forward operations are not executed, and it
has no parameters in the optimizer. With reconstruction weight zero this is
scientifically equivalent to the previous fixed-rate control: capsule-layer
initialization precedes decoder initialization, the data-loader generator is
independent, and Adam updates each parameter independently. Automated tests
verify the disabled path and resumable scheduler state. The decayed arm uses
separate versioned state and checkpoint paths and does not access external test
data.

For 81-base inputs, selected-vector decoding contributes 866,116 of 1,736,004
parameters, while masked-flat decoding contributes 874,308 of 1,744,196.
Disabling the decoder leaves 869,888 parameters and also removes its dense
forward operations, saved activations, gradients, and optimizer states. A
decoder with zero loss weight is therefore scientifically inert but
computationally wasteful unless it is structurally disabled.

Exponential decay did not improve stability. Seeds 23, 31, and 37 left collapse
with best inner-validation MCC 0.1990, 0.1890, and 0.3449, while seeds 29 and 42
remained single-class with MCC zero. Its median best MCC was 0.1890 and its
collapse rate was 40%, compared with 0.2328 and 20% for the fixed-rate arm.
The fixed learning rate is therefore the better of these two predeclared
training-only controls, but neither is stable enough for a confirmatory freeze.
No external-test result informed this conclusion.

### Predeclared capsule-norm trace diagnostic

Runner contract version 5 records the two output-capsule norms at every epoch,
including means stratified by true class, the correct-minus-incorrect capsule
margin, and the predicted-positive fraction. These traces are persisted in the
atomic state and logged to MLflow with epoch steps.

The diagnostic repeats fixed-rate, decoder-disabled seeds 37 and 42 because the
previous training-only control observed them as representative non-collapsed
and collapsed trajectories. This is an explicitly exploratory case comparison,
not a seed-selection procedure. Data, split rule, architecture, optimizer,
maximum epochs, and patience remain unchanged, and no external test file is
accepted or inspected.

The traces locate the instability at the beginning of optimization. Before any
update, both capsules have small, approximately symmetric norms on the
validation partition: about `0.00090` and `0.00075` for seed 37, and `0.00116`
and `0.00114` for seed 42. After one epoch, the corresponding means jump to
`0.4072` and `0.7839` for seed 37 and to `0.8639` and `0.9896` for seed 42.
The class-stratified means remain nearly identical at this point, so the model
is increasing capsule length without yet learning a class-conditional score.

Seed 37 eventually leaves this saturated, class-symmetric regime. At epoch 25,
true class 0 has mean capsule norms `0.6389` versus `0.5902`, while true class 1
has `0.5643` versus `0.6813`; its predicted-positive fraction is `0.64` and its
validation MCC is `0.2831`. Its best checkpoint occurs at epoch 28 with MCC
`0.2932`, predicted-positive fraction `0.5067`, and mean correct-minus-incorrect
norm `0.1275`. Seed 42 instead alternates between global capsule dominance and
single-class predictions. It never develops class-conditional separation,
selects epoch 1 with MCC zero, and stops after patience is exhausted.

This behavior is consistent with an optimization instability rather than a
disconnected gradient path: both capsule norms respond strongly to updates, but
the initial step drives them toward the low-gradient saturated region of the
squash nonlinearity before the classes separate. Very small numerical
differences can then lead to different trajectories. Accordingly, the next
minimal, predeclared control should reduce the initial update magnitude while
holding the data, architecture, loss, seeds, and evaluation policy fixed. A
fixed learning rate of `0.0001` is the simplest first control; broader scheduler
or decay-factor searches are deferred until this mechanism is tested. Neither
trace run nor the proposed control may inspect external test outcomes.

### Fixed low-learning-rate control

The five-seed control at fixed learning rate `0.0001` completed without a
single-class checkpoint. Seeds 23, 29, 31, 37, and 42 reached best
inner-validation MCC values `0.2175`, `0.2608`, `0.2317`, `0.1943`, and
`0.1694`, respectively. Their first two-class epochs were 5, 1, 1, 5, and 5.
The median best MCC was `0.2175` and the observed collapse rate was zero,
compared with median `0.2328` and 20% collapse at fixed learning rate `0.001`.

At the selected checkpoints, confusion counts `(TN, FP, FN, TP)` were
`(17, 52, 7, 74)`, `(14, 55, 3, 78)`, `(55, 14, 47, 34)`,
`(18, 51, 9, 72)`, and `(27, 42, 19, 62)`. Mean capsule norms after the first
epoch ranged from `0.7760` to `0.8173`. The smaller update therefore reduced
the extreme first-epoch saturation seen at learning rate `0.001` and recovered
seed 42, but it still moved the norms far from their approximately `0.001`
initial values and reduced the median validation MCC.

The low fixed rate is evidence for the initial-update hypothesis, not a final
optimizer selection. The next minimal control should use a predeclared linear
warm-up from `0.0001` to `0.001` over five epochs and then retain `0.001`, with
the same five seeds and all other variables fixed. This tests whether a guarded
initial trajectory can preserve the zero-collapse behavior while restoring the
later optimization capacity. The warm-up result remains training-only and may
not be selected or interpreted using external test outcomes.

### Five-epoch linear warm-up control

Runner contract version 6 implements the predeclared linear warm-up and records
the learning rate used in every epoch. The five warm-up rates are `0.0001`,
`0.000325`, `0.00055`, `0.000775`, and `0.001`; subsequent epochs retain
`0.001`. Scheduler state is stored in the atomic latest checkpoint so resumed
runs preserve the exact trajectory. Contracts from runner versions 2 through 5
retain their original serialized fields and runner-version identifiers.

Seeds 23, 29, 31, 37, and 42 reached best inner-validation MCC values `0.1943`,
`0.2601`, `0.2115`, `0.0000`, and `0.1712`. Their first two-class epochs were 9,
1, 1, absent, and 10. The median best MCC was `0.1943` and the collapse rate was
20%. At the selected checkpoints, confusion counts `(TN, FP, FN, TP)` were
`(13, 56, 5, 76)`, `(17, 52, 5, 76)`, `(14, 55, 5, 76)`,
`(0, 69, 0, 81)`, and `(21, 48, 13, 68)`.

The warm-up did not combine the advantages of the fixed-rate controls. It
reintroduced collapse in seed 37, which had learned under both fixed rates, and
its median MCC was below both fixed-rate medians. The five-epoch warm-up is
therefore rejected. All fixed-`0.0001` runs reached the 30-epoch limit, with
best epochs from 16 to 23, so the next smallest control is to retain fixed
`0.0001`, patience 15, and all other settings while increasing only the maximum
training horizon to 60 epochs. This remains an exploratory training-only test;
external test outcomes remain unavailable for selection.

### Extended low-rate horizon control

The 60-epoch fixed-`0.0001` control reproduced every selected checkpoint and
metric from the 30-epoch control. Seeds 23, 29, 31, 37, and 42 retained best
epochs 17, 16, 23, 22, and 17 and best MCC values `0.2175`, `0.2608`, `0.2317`,
`0.1943`, and `0.1694`. They stopped after epochs 32, 31, 38, 37, and 32 when
patience 15 was exhausted. No later epoch improved the lexicographic
MCC-then-loss checkpoint criterion.

The lower median MCC at fixed `0.0001` is therefore not explained by an
insufficient 30-epoch horizon. Extending the limit only increases computation;
the 60-epoch control is rejected and the 30-epoch limit is retained. Among the
tested schedules, fixed `0.0001` is the only arm with zero observed collapse
across all five seeds, so it becomes the frozen optimizer setting for the next
basic-CapsProm protocol. This is a stability-first development decision, not a
claim of external-test superiority. Further optimizer tuning on this inner
split is stopped to limit adaptive overfitting. The next step is to define the
canonical multi-dataset CapsProm experiment before any external-test execution.

## DNA-specific extension boundary

The basic model deliberately excludes multiscale convolutions, attention,
recurrent layers, and strand-invariant aggregation. Multiscale convolutions use
several kernel widths to detect motifs and composite patterns at different
lengths. Attention learns input-dependent weights over positions or features.
A bidirectional gated recurrent unit (BiGRU) summarizes ordered context from
both directions of the supplied sequence. Strand invariance combines a sequence
with its reverse complement so that both orientations receive the same output.

These mechanisms are biologically plausible extensions but answer different
questions from seminal CapsNet reproduction. In particular, promoter windows
oriented relative to a transcription start site should not be made
strand-invariant without a dataset-specific justification. Each mechanism must
therefore enter only through a separately versioned ablation after the basic
CapsProm contract is stable.
