# Feature Architecture Specification

## Objective

CapsProm experiments must support multiple DNA feature encodings and controlled
feature combinations. The same dataset should be usable by classical machine
learning models and deep neural-network architectures without changing the data
files.


## Mathematical Notation Contract

Feature-engineering documentation and thesis text must use a consistent notation
contract. When writing about neural networks, learned embeddings, model inputs,
losses, or trainable parameters, prefer the notation style used by Goodfellow,
Bengio, and Courville's *Deep Learning*. A model-ready DNA sequence is `x_i\in\Sigma^L`, with
`\Sigma=\{A,C,G,T\}` and `L` the domain window length of
`specs/sequence_window_policy.md` (`L=251` for eukaryotes, `L=81` for
prokaryotes). For k-mer encodings, use
`\mathcal{K}_k=\Sigma^k`, `L_k=L-k+1`, and `u_{it}^{(k)}` for the `t`-th
overlapping k-mer. Use `\phi_j` for an individual feature mapping,
`z_{ij}=\phi_j(x_i)` for its output, and `\Phi(x_i)` for combined feature
representations. Use `\rho^{(k)}` for physicochemical reference mappings,
`\theta_{i,d}^{(k)}` for PseKNC sequence-order correlation terms, `\lambda`
for the number of lags, and `w` for the PseKNC weight.

Future feature families should first be expressed as a mapping compatible with
this notation before being connected to configuration files or implementation
classes. New symbols should be introduced only when they represent concepts not
covered by the canonical notation.


## Feature Diagram Requirement

For each feature family, documentation should consider whether an explanatory
schematic would improve the reader's understanding of the transformation
$\phi_j(x_i)$. Diagrams are particularly useful when the feature involves
sliding k-mers, lookup tables, sequence-order correlation terms, learned
embeddings, or multiple neural input branches. When included, diagrams must be
methodologically aligned with the original literature, use the canonical
notation from this specification, and be introduced in thesis text with a
citation and an explanatory caption.

Recommended diagram candidates for the current project are:

- One-hot/k-mer tokenization from $x_i$ to $O_i^{(k)}$.
- K-mer frequency aggregation from overlapping $u_{it}^{(k)}$ to $F_i^{(k)}$.
- Physicochemical lookup from $u_{it}^{(k)}$ and $\rho^{(k)}$ to $P_i^{(k)}$.
- PseKNC construction from k-mer frequencies and $\theta_{i,d}^{(k)}$ to
  $Q_i^{(k,\lambda,w)}$.
- DNA-BERT tokenization, transformer encoding, and pooling to $B_i$.
- Multi-head fusion from named feature blocks to a classifier input.

## Canonical Physicochemical References

The following files are the canonical normalized references for physicochemical
feature construction:

| Reference | Scope | Current property count |
| --- | --- | ---: |
| `data/raw/references/normalized-dinuc.tsv` | Dinucleotide properties | 38 |
| `data/raw/references/normalized-trinuc.tsv` | Trinucleotide properties | 12 |

Each TSV file stores physicochemical properties as rows and k-mers as columns.
Encoders must load these files directly, preserving property names for
provenance and downstream interpretability. The thesis bibliography must provide
reference anchors for each active feature family: ordered one-hot nucleotide or k-mer encodings,
k-mer composition, GC/skew descriptors, physicochemical properties, PseKNC-style
pseudo-composition, and DNA-BERT embeddings.


## Property Selection

Physicochemical feature blocks may use either all properties from a reference
file or an explicitly named subset. Subset selections must preserve the order
defined in the YAML configuration and must be logged as part of the feature
metadata. Unknown property names should fail configuration validation instead of
silently falling back to all properties.

Example:

```yaml
- name: dinucleotide_physicochemical
  encoding: physicochemical
  k: 2
  reference_tsv: data/raw/references/normalized-dinuc.tsv
  properties:
    - Base stacking
    - B-DNA twist
    - Dinucleotide GC Content
```

## Feature Blocks

Every encoding produces a named feature block. A block has:

- `name`: unique identifier inside one experiment.
- `encoding`: encoder type, such as `kmer_frequency`, `one_hot`,
  `physicochemical`, `gc_content_skew`, `pseknc`, or `dna_bert`.
- `shape`: output tensor/vector shape.
- `metadata`: parameters and reference paths required for reproducibility.

Examples:

- `kmer_frequency_3`: flat vector of 3-mer frequencies.
- `one_hot_1`: position-by-base matrix; `one_hot_2` may be used for controlled dinucleotide-token ablations.
- `dinucleotide_physicochemical`: position-by-property matrix generated from
  `normalized-dinuc.tsv`.
- `trinucleotide_physicochemical`: position-by-property matrix generated from
  `normalized-trinuc.tsv`.
- `gc_content_skew`: compact global and/or windowed composition descriptors.
- `psednc_physicochemical`: dinucleotide composition plus sequence-order
  correlation terms computed from `normalized-dinuc.tsv`.
- `psetnc_physicochemical`: trinucleotide composition plus sequence-order
  correlation terms computed from `normalized-trinuc.tsv`.
- `dna_bert_6_embedding`: sequence-level embedding generated from `zhihan1996/DNA_bert_6`.


## K-Dependent Dimensionality Constraints

Any feature block with a k-mer vocabulary must record `k` explicitly. The
configuration layer supports one-hot k-mer tokens, but the methodological
default is `one_hot` with `k: 1`. For a sequence of length `L`, one-hot k-mer
matrices have `(L - k + 1) x 4^k` values (at `L = 251` and `k = 6`, 1,007,616), k-mer frequency vectors have `4^k` values,
and PseKNC vectors have `4^k + lambda_value` values. These dimensions must be
considered before combining feature blocks.

The initial thesis experiments should treat the following as methodological
constraints unless a later experiment specification justifies an exception:

- `one_hot`: primary `k: 1`; optional `k: 2` ablation only.
- `kmer_frequency`: small predeclared values of `k`.
- `physicochemical`: `k: 2` and `k: 3`, determined by the reference TSVs.
- `pseknc`: `k: 2` for PseDNC and `k: 3` for PseTNC.
- `dna_bert`: fixed `k: 6` for `zhihan1996/DNA_bert_6`.

## PseKNC Provenance

PseKNC feature blocks must be documented as implementations of the pseudo
k-tuple nucleotide composition method introduced by Chen et al. (2014) and
extended in PseKNC-General by Chen et al. (2015). When `k: 2`, the block should
be interpreted as a PseDNC-style representation; when `k: 3`, it should be
interpreted as a PseTNC-style representation. Experiment reports must record the
reference table, selected properties, `lambda_value`, and `weight` because these
parameters define the biological and mathematical meaning of the resulting
features.

## Combination Modes

Classical models:

- Use `combination_mode: concatenate`.
- Feature blocks are flattened and concatenated into a single vector.
- This mode is appropriate for XGBoost and other tabular classifiers.

Deep neural networks:

- Use `input_mode: multi_head` or an equivalent architecture-specific flag.
- Each feature block remains a named input tensor.
- Model branches may process each input independently before fusion.
- Fusion may use concatenation, attention, capsule routing, or another explicitly
  configured mechanism.


## DNA-BERT Role Boundary

DNA-BERT can be used in two distinct roles in this project:

- As a feature encoder, where `zhihan1996/DNA_bert_6` produces sequence-level
  embeddings consumed by classical classifiers or multi-head neural models.
- As a classifier baseline, where DNA-BERT is fine-tuned with a promoter versus
  non-promoter classification head during the model-development phase.

The current feature-engineering implementation covers only the first role. The
fine-tuned DNA-BERT classifier must be specified and implemented later as part
of the baseline model layer, not inside the feature encoder.

## Neural Architecture Requirement

Deep-learning implementations of CapsProm, SparseCapsProm, CNN baselines, or
BERT-hybrid variants must allow more than one feature source. At minimum, the
architecture interface should support:

- Single-input mode for one feature block.
- Multi-head mode for two or more feature blocks.
- Named input mapping from configuration to model branch.
- Explicit fusion strategy.
- MLflow logging of all active feature blocks, reference files, and pretrained embedding model identifiers.

## Implementation References

Initial reusable feature code lives in:

- `capsprom.features.physicochemical`
- `capsprom.features.encoders`
- `capsprom.features.builder`

The current implementation supports loading normalized physicochemical TSVs,
encoding dinucleotide/trinucleotide property matrices, k-mer frequency vectors,
one-hot matrices, GC content/skew descriptors, PseKNC descriptors for PseDNC and
PseTNC experiments, optional DNA-BERT embeddings, strict DNA sequence
validation, feature-block construction from configuration mappings, flattened
vector outputs, and named multi-head input mappings.
