# Configuration Files

Experiment configuration files are written in YAML and should be treated as
part of the scientific record. A configuration file must contain enough
information to reproduce a run, compare it with other runs, and connect its
outputs to the doctoral thesis.

`example_experiment.yaml` describes the broader target architecture and includes
features and models beyond the current executable boundary.

`mvp_logistic.yaml` is the executable restart milestone. It runs a deterministic
sampled logistic-regression experiment using 3-mer frequency and GC/skew
features, with local SQLite-backed MLflow tracking. Validate and run it with:

```bash
PYTHONPATH=src python -m capsprom validate-config configs/mvp_logistic.yaml
PYTHONPATH=src python -m capsprom validate-data configs/mvp_logistic.yaml
PYTHONPATH=src python -m capsprom audit-data configs/mvp_logistic.yaml
PYTHONPATH=src python -m capsprom run configs/mvp_logistic.yaml
```

`full_logistic.yaml` promotes the same fixed experimental contract to every
record in the Bhandari human promoter train/test split. It deliberately changes
only the sample limits and MLflow experiment name:

```bash
PYTHONPATH=src python -m capsprom run configs/full_logistic.yaml
```

`full_xgboost.yaml` is the first comparative nonlinear baseline. It preserves
the full logistic-regression data and feature contract while changing only the
model family and its explicit hyperparameters:

```bash
PYTHONPATH=src python -m capsprom run configs/full_xgboost.yaml
```

`evaluation_protocol.yaml` is the version-1 machine-readable statistical contract
for confirmatory experiments. It is marked `partially_implemented`: the
current CLI persists predictions, metrics, calibration summaries, data audits,
and fold manifests, but it does not yet execute repeated-seed orchestration,
paired resampling, or cross-dataset comparisons.

`evaluation_protocol_v2.yaml` preserves version 1 for completed analyses and
locks the thesis-wide hierarchy for future confirmatory comparisons. Five inner
folds select each dataset--model--configuration--seed fit but are not test
replicates; ten seeds measure algorithmic stability but are not independent
datasets. Model effects are paired by seed, summarized within each dataset by
the median paired MCC difference, and then aggregated by audited dataset-
dependency cluster. Its confirmatory-ranking gates remain closed pending the
dependency manifest and fixture validation of the statistical aggregation.

`leakage_controlled_logistic.yaml` and
`leakage_controlled_xgboost.yaml` use the deduplicated, group-split Bhandari
human shuffle-control dataset. They replace the contaminated Bhandari human
split for current development experiments.

`real_negative_smoke_logistic.yaml` and
`real_negative_smoke_xgboost.yaml` exercise the canonical v3 GraphPro
`clostridium_phytofermentans` pair. They are explicitly exploratory integration
checks and must not be treated as confirmatory model comparisons.

`real_negative_baseline_batch.yaml` freezes the canonical v3 two-model batch.
It excludes the observed smoke-test pair from primary confirmatory inference
and is materialized or resumed with `scripts/run_real_negative_baselines.py`.

`xgboost_ten_seed_replication.yaml` freezes the confirmatory replication of
XGBoost over the ten seeds declared in the thesis protocol. It reuses the
seed-42 run identifiers from the completed baseline batch and plans the
remaining combinations with `scripts/run_xgboost_replication.py`.

`xgboost_ten_seed_replication_v2.yaml` is the active execution contract. It
retains all scientific settings, validates seed-42 reuse against the source
configuration, uses atomic checkpoints, and skips redundant complete-model
serialization while preserving predictions and provenance. Version 1 remains
unchanged for audit.

Dataset-pair integrity auditing is independent of a model configuration. Audit
the canonical strict-DNA CDBProm, CNNProm, and GraphPro pairs with:

```bash
PYTHONPATH=src python -m capsprom audit-datasets \
  data/processed/assembled_datasets/intra_regenerated_v3_strict_dna \
  data/processed/audits/real_negative_regenerated_v3
```

The command writes JSON, CSV, and Markdown reports with deterministic input
hashes and strict eligibility classifications.

`capsprom_1c_training_smoke_v1.yaml` and
`capsprom_2c_training_smoke_v1.yaml` are training-only Phase 4 integration
checks. They use 64 records from the already exploratory GraphPro
`clostridium_phytofermentans` training file, reserve a fixed inner validation
split, run one epoch, and never load its external test file. Their validation
metrics verify execution and tracking only and must not be interpreted as model
comparisons or used for architecture selection.

`cnn_control_learnability_v1.yaml`, `capsprom_basic_learnability_v1.yaml`, and
`capsprom_basic_learnability_v2.yaml` are training-only diagnostics. Academic
text reserves the name CapsProm for the two-output basic architecture; the
one-output CapsProm-1C implementation remains a historical reproduction only.
Runner version 2 adds validation-loss tie-breaking when validation MCC is
unchanged, using new state and checkpoint paths.

`capsprom_basic_full_train_learnability_v1.yaml` and
`capsprom_basic_full_train_learnability_v2.yaml` extend that diagnostic to all
747 records in the same exploratory training file without accessing the
external test file. Version 1 propagates gradients through all routing
iterations. Version 2 explicitly uses `routing_gradient_mode: final_iteration`,
which detaches intermediate agreement updates while retaining gradients through
the final capsule computation. The separate contracts and output paths preserve
both diagnostic histories.

`capsprom_basic_full_train_learnability_v3.yaml` is the first
seminal-alignment contract. It uses two output capsules, final-iteration routing
gradients, flattened class-mask decoding, and summed per-sample reconstruction
error. It has a new contract version and output path; version 1 and 2 YAML files
retain their executed behavior and hashes.

The four `capsprom_basic_decoder_ablation_v1_*.yaml` contracts form a
training-only `2 x 2` component diagnostic: selected-vector versus flattened
class-mask decoding, crossed with mean versus summed-per-sample reconstruction.
They use identical data, split, seed, optimizer, and patience 15, and never name
or load an external test split.

The five `capsprom_basic_no_reconstruction_seed*_v1.yaml` contracts evaluate
the margin-loss capsule core at seeds 23, 29, 31, 37, and 42 with reconstruction
weight zero. Decoder output is consequently inert. All runs use the same
training-only data and fixed optimization contract, with separate MLflow runs,
checkpoints, and atomic states.

The five `capsprom_basic_no_reconstruction_decay_seed*_v1.yaml` contracts use
runner contract version 4, structurally disable the decoder, and apply an
epoch-wise exponential learning-rate factor of 0.9. They form the comparison
arm against the scientifically equivalent fixed-rate no-reconstruction runs.

`capsprom_basic_capsule_trace_seed37_v1.yaml` and
`capsprom_basic_capsule_trace_seed42_v1.yaml` use runner contract version 5 to
persist and track per-epoch output-capsule norms, class-stratified norms,
correct-minus-incorrect norm margins, and predicted-positive fractions. They
are an exploratory comparison of a previously non-collapsed and collapsed seed
under the fixed-rate, decoder-disabled contract; they do not access external
test data.

The five `capsprom_basic_low_lr_seed*_v1.yaml` contracts are the predeclared
fixed-rate stability control at learning rate `0.0001`. They use the same five
seeds, training-only split, architecture, margin loss, patience, and capsule
trace contract as the preceding controls. Their independent output paths and
MLflow runs preserve the comparison without modifying an existing contract.

The five `capsprom_basic_warmup_seed*_v1.yaml` contracts use runner contract
version 6 and linearly increase the learning rate from `0.0001` to `0.001`
across the first five epochs. The effective epoch rate is stored in the atomic
state and logged to MLflow, and the scheduler state is resumable. These are
training-only optimizer diagnostics with independent output paths.

The five `capsprom_basic_low_lr_60ep_seed*_v1.yaml` contracts extend only the
maximum horizon of the fixed-`0.0001` control from 30 to 60 epochs. They test
whether the lower-rate arm was truncated before convergence while retaining
patience 15 and every other scientific setting. All five stopped by patience
before epoch 39 and reproduced the 30-epoch selected checkpoints exactly.

`capsprom_basic_canonical_v1.yaml` is the design-locked multi-dataset protocol,
not a single-run neural configuration. It lists all 26 eligible v3 dataset
identities, ten canonical seeds, five-fold epoch selection, the frozen basic
CapsProm architecture, and execution gates. `prepare-neural-canonical` reads
training files only, writes hashed fold manifests, and creates a resumable
1,560-job plan whose final fits remain blocked pending fold-derived epochs.
`refresh-neural-canonical-readiness` performs the separate, evaluation-free
transition from that blocked state to `ready_for_final_fit` after all five inner
folds for a dataset/seed are complete. It persists the five best epochs and
their lower median atomically but does not train, open a test file, or enable a
final-fit gate.

`capsprom_basic_canonical_gpu_v1.yaml` is a separate draft execution contract
for the validated `bioserver03` CUDA path. It changes only the protocol and
tracking identities, runner contract to version 7, and explicit device to
`cuda`; the datasets, folds, seeds, architecture, optimizer, epoch-selection
rule, and prediction policy remain identical to the CPU design. Both canonical
and embedding job gates remain false. No state has been created for this
configuration, so it has not authorized or started a real run.

`capsprom_basic_canonical_gpu_execution_v1.yaml` is the reviewed execution
contract, not by itself an authorization record. Relative to the blocked GPU
design, it changes only the protocol and experiment identities, declares
host-local SQLite and artifact locations, enables inner-fold jobs, and adds an
explicit false final-fit gate. Final fits, external-test access, and embedding
jobs remain disabled. Following successive explicit bounded authorizations, its
training-only plan was created on `bioserver03` and the five inner folds for the
smallest dataset were completed at seeds 13 and 29. The campaign is paused
before any additional seed or dataset. The YAML is now immutable because its
hash is bound to plan and run state.

`capsprom_future_campaign_release_policy_v1.yaml` is a local planning record,
not an execution contract. It freezes the prerequisites for a future bounded
remote tranche, records the epoch-30 ceiling contact, and keeps remote, final-
fit, external-test, and embedding gates closed.

`capsprom_remote_usage_policy_v2.yaml` is the active local-first access policy.
It preserves the scientific, recovery, MLflow, and backup rules of the earlier
remote execution policy while superseding its access-frequency assumptions.
Routine development, fixture tests, documentation, status checks, and repository
synchronization remain local. `bioserver03` is reserved for explicitly
authorized GPU-heavy or many-fit work; `bioserver04` is reserved for explicitly
authorized heavy CPU work and backup verification associated with such a
campaign. Remote synchronization occurs only at campaign boundaries and carries
the minimum immutable execution snapshot.
