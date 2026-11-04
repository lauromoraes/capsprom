# Seed Policy

## Status and scope

Design (2026-11-03, log R-059). This policy fixes the random seeds of the project and the
role of each one. It applies to every definitive run, which in this project
means a run under a frozen contract whose external test partition may later be
opened. Exploratory runs and diagnostics may use other seeds, as described in
"Exploratory runs" below.

The policy collects values that frozen contracts already use. It does not
change any existing contract, partition, state file, or execution gate. Every
versioned YAML file still lists its seeds explicitly; this document defines
which values those lists may hold. `specs/statistical_evaluation_protocol.md`
remains authoritative for how seeds enter inference.

## Seed roles

A seed has exactly one of the following roles. A value may occur in more than
one role (42 is both a run seed and the partition seed), but each contract
field names its role, and no seed is chosen because of the role it plays
elsewhere.

| Role | Values | Used for |
|---|---|---|
| Run seeds | `13, 29, 42, 71, 101, 137, 173, 211, 251, 293` | Algorithmic randomness of stochastic models |
| Reserve run seeds | `337, 379, 421, 463, 509, 547, 593, 631, 673, 719` | Only as a block, under the rule below |
| Partition seed | `42` | Inner folds and group-to-fold assignment |
| Sampling seeds | one `YYYYMMDD` value per procedure | Data construction (negative sampling, subsampling) |
| Resampling seeds | one `YYYYMMDD` value per evaluation protocol | Bootstrap and randomization inference |

### Run seeds

The ten run seeds receive every stochastic component of a stochastic model:
weight initialization, data-loader order, dropout, and model-specific sampling
such as XGBoost row and column subsampling. All stochastic models in a
comparison use the same ten seeds, so their results pair by seed.
Deterministic models are fitted once and are not repeated to create
pseudo-replicates.

Seeds measure algorithmic instability on a fixed dataset. They are not
independent biological or cross-dataset observations; the dataset is the unit
of inference.

A failed seed is reported and never replaced, by a reserve seed or any other.
The list is never reordered, shortened, or extended on the basis of observed
results.

### Reserve run seeds

The reserve block exists so that a larger replication, if one is ever needed,
uses seeds that were fixed before any result was seen. It is used only when
all of the following hold:

1. A new versioned protocol activates it before any external test partition of
   the affected datasets is opened.
2. The reason is stated in that protocol and does not depend on observed test
   results. The expected reason is a confirmatory claim about the per-dataset
   rate of a failure mode, such as single-class collapse, that ten seeds cannot
   bound tightly enough (see "Number of seeds").
3. All ten reserve seeds are run, in addition to the ten run seeds, for every
   model and dataset in the comparison. A partial block is not allowed.

### Partition seed

Seed 42 generates the five-fold stratified inner-fold manifests and the
group-to-fold assignment (`fold_seed`, `inner_fold_seed`, and
`assignment_seed` in the contracts). Partitions are materialized once, hashed,
and held fixed across all run seeds, so seed-to-seed variation reflects only
the algorithm. A partition is never regenerated with a run seed.

Because partition manifests are frozen files, the shared value 42 does not
correlate the partition with the run-seed-42 model fit.

### Sampling seeds

Each data-construction procedure that samples records gets its own seed,
written as the `YYYYMMDD` date on which its contract was designed (for
example `20261021` for GraphPro reconstruction sampling and `20261102` for the
CDS-derived control). The seed is recorded in the contract and in the
provenance log (`specs/data_provenance_policy.md`). Two procedures never share
a sampling seed, and a sampling seed never equals a run seed.

A replay of a published procedure follows the published seed and seed count
when they are known. When they are not, the replay contract states the seeds
it uses and why.

### Resampling seeds

Each frozen evaluation protocol declares one resampling seed for its bootstrap
and randomization procedures, written as a `YYYYMMDD` date. The confirmatory
value is `resampling_seed: 20260715` in `configs/evaluation_protocol_v4.yaml`.
Descriptive reports may declare their own resampling seed (for example
`bootstrap_seed: 20261019` in `configs/active_baseline_consolidation_v1.yaml`),
but that seed never replaces the protocol seed in a confirmatory analysis.

## Number of seeds

Ten run seeds are enough to estimate dataset-level performance. In the
completed ten-seed tranches, the standard deviation of seed means ranged from
about 0.006 to 0.008 MCC, which puts the standard error of the ten-seed mean
at about 0.002 to 0.0026 MCC. That is well below any difference this project
treats as substantive.

Ten seeds are weaker for bounding failure rates. If no seed out of `n`
collapses, the exact one-sided 95% upper bound on the per-dataset collapse
probability is `1 - 0.05^(1/n)`:

| Seeds | Upper bound with zero failures |
|---|---|
| 10 | 0.259 |
| 20 | 0.139 |

A claim that a model "does not collapse" on a dataset, based on ten seeds, is
therefore limited to "collapse probability below about 26%". Tighter claims
require the reserve block.

## Determinism and reproducibility

The neural runner seeds Python, NumPy, and PyTorch, disables cuDNN
benchmarking, enables deterministic cuDNN kernels, and calls
`torch.use_deterministic_algorithms(True)` (`_seed_everything` in
`src/capsprom/neural_training.py`). Classical models receive the run seed
through their `random_state` parameter (`src/capsprom/models/classical.py`).

A seed guarantees identical results only on the same hardware and software
stack. Every definitive run must record the device, driver, and library
versions with its MLflow run. Today only the feasibility probe
(`src/capsprom/feasibility.py`) records them, so the training runners must add
this before the definitive runs. Reproducing a run on a different stack is judged by a stated
numerical tolerance, not by bitwise equality, and any difference is reported.

## Exploratory runs

Exploratory and diagnostic runs, such as the five-seed optimizer controls in
`specs/capsprom_reproduction.md` (seeds 23, 29, 31, 37, 42), may use any
seeds. Their results never select, drop, or reorder canonical run seeds. An
exploratory result reused in a definitive analysis must have used a canonical
run seed and pass the scientific-equivalence check required by `AGENTS.md`.

## Changes

Any change to a seed list, to a seed's role, or to the activation of the
reserve block creates a new versioned configuration and state path. Existing
contracts keep their seeds.
