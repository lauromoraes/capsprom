# Feature Architecture Specification

## Objective

CapsProm experiments must support multiple DNA feature encodings and controlled
feature combinations. The same dataset should be usable by classical machine
learning models and deep neural-network architectures without changing the data
files.

## Canonical Physicochemical References

The following files are the canonical normalized references for physicochemical
feature construction:

| Reference | Scope | Current property count |
| --- | --- | ---: |
| `data/raw/references/normalized-dinuc.tsv` | Dinucleotide properties | 38 |
| `data/raw/references/normalized-trinuc.tsv` | Trinucleotide properties | 12 |

Each TSV file stores physicochemical properties as rows and k-mers as columns.
Encoders must load these files directly, preserving property names for
provenance and downstream interpretability.


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
- `encoding`: encoder type, such as `kmer_frequency`, `one_hot`, or
  `physicochemical`.
- `shape`: output tensor/vector shape.
- `metadata`: parameters and reference paths required for reproducibility.

Examples:

- `kmer_frequency_3`: flat vector of 3-mer frequencies.
- `one_hot_1`: position-by-base matrix.
- `dinucleotide_physicochemical`: position-by-property matrix generated from
  `normalized-dinuc.tsv`.
- `trinucleotide_physicochemical`: position-by-property matrix generated from
  `normalized-trinuc.tsv`.

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

## Neural Architecture Requirement

Deep-learning implementations of CapsProm, SparseCapsProm, CNN baselines, or
BERT-hybrid variants must allow more than one feature source. At minimum, the
architecture interface should support:

- Single-input mode for one feature block.
- Multi-head mode for two or more feature blocks.
- Named input mapping from configuration to model branch.
- Explicit fusion strategy.
- MLflow logging of all active feature blocks and reference files.

## Implementation References

Initial reusable feature code lives in:

- `capsprom.features.physicochemical`
- `capsprom.features.encoders`

The current implementation supports loading normalized physicochemical TSVs,
encoding dinucleotide/trinucleotide property matrices, k-mer frequency vectors,
one-hot matrices, flattened concatenation, and named multi-head input mappings.
