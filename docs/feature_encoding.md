# Feature Encoding Notes

The project supports feature construction as named blocks. This keeps feature
engineering independent from the classifier and makes it possible to compare
single-source and multi-source inputs under the same experimental pipeline.
Academic references for each feature family are maintained in the thesis
bibliography and summarized in the feature-engineering chapter. General
deep-learning notation and learned-representation terminology should be aligned
with Goodfellow, Bengio, and Courville (2016) whenever applicable.


## Academic Reference Map

The implemented feature families should be documented with the following
reference anchors in thesis text and experiment reports:

- One-hot ordered nucleotide or k-mer inputs: CNNProm and CapsProm promoter models
  (Umarov and Solovyev, 2017; Moraes et al., 2022).
- K-mer frequency vectors: spectrum-style sequence representations (Leslie,
  Eskin, and Noble, 2002).
- GC content and nucleotide skew: strand-asymmetry descriptors in bacterial
  genomes (Lobry, 1996).
- Dinucleotide and trinucleotide physicochemical matrices: prior promoter
  classification experiments with physicochemical properties (Moraes et al.,
  2023).
- PseKNC/PseDNC/PseTNC: pseudo nucleotide composition methods (Chen et al.,
  2014; Chen et al., 2015).
- DNA-BERT embeddings: pretrained transformer representations for DNA language
  modeling (Ji et al., 2021).


## One-Hot Encodings

The `one_hot` encoder supports configurable k-mer tokens through the `k`
parameter. With `k: 1`, each nucleotide position is encoded as a four-component
indicator vector. With `k: 2`, each overlapping dinucleotide is encoded against
a 16-token vocabulary; in general, an 81 bp sequence produces a matrix with
`81 - k + 1` rows and `4^k` columns.

Example feature block:

```yaml
- name: one_hot_1
  encoding: one_hot
  k: 1
```

For this thesis, `k: 1` is the primary ordered one-hot representation. `k: 2`
may be used only in controlled ablation experiments because one-hot
dimensionality grows exponentially with `k`. Larger one-hot k-mer encodings
should not be introduced without an explicit methodological justification and
resource assessment.

## Controlled Ablation Potential

Controlled ablation potential describes how naturally a feature family supports
experiments that remove, isolate, compare, or group meaningful components. It
helps answer whether a representation, parameter choice, or interpretable subset
contributes to model performance. K-mer, GC/skew, physicochemical, and PseKNC
features have high controlled ablation potential because they can be varied by
explicit parameters or named biological descriptors. One-hot and DNA-BERT remain
ablatable, but their individual components are less directly tied to compact
biological concepts: one-hot ablation can become very fine-grained, while
DNA-BERT embeddings are dense learned vectors.

## K-Dependent Dimensionality

Several feature families depend directly on k-mer vocabulary size. K-mer
frequency vectors have `4^k` components, one-hot k-mer matrices have
`(L - k + 1) * 4^k` components for sequence length `L`, and PseKNC descriptors
contain `4^k + lambda_value` components. This growth can increase memory use,
training time, and overfitting risk, especially when multiple blocks are
concatenated for classical classifiers.

The methodological restrictions adopted in this project are:

- `one_hot`: use `k: 1` as the primary representation; reserve `k: 2` for
  controlled ablations.
- `kmer_frequency`: use small values of `k` selected before training.
- `physicochemical`: use only the available dinucleotide and trinucleotide
  reference tables.
- `pseknc`: use PseDNC (`k: 2`) and PseTNC (`k: 3`) only.
- `dna_bert`: keep `k: 6` because `zhihan1996/DNA_bert_6` was pretrained with
  six-mer tokenization.

## Physicochemical Properties

The files `data/raw/references/normalized-dinuc.tsv` and
`data/raw/references/normalized-trinuc.tsv` are the official references for
physicochemical encodings. They contain normalized property values for all DNA
2-mers and 3-mers, respectively.

For an 81 bp sequence:

- Dinucleotide physicochemical encoding produces 80 positions by 38 properties.
- Trinucleotide physicochemical encoding produces 79 positions by 12 properties.

These outputs should normally remain as matrices for deep-learning models. For
classical tabular classifiers, they can be flattened and concatenated with other
feature blocks.


## Selecting Physicochemical Properties

A physicochemical block can use all properties or a named subset. Subsets are
useful for ablation studies, biological interpretability, and reducing input
dimensionality for neural architectures. Property names must match the TSV row
names exactly.

Example:

```yaml
properties:
  - Base stacking
  - B-DNA twist
  - Dinucleotide GC Content
```


## Implemented Feature Engineering Entry Point

The first reusable feature-engineering layer is implemented in
`capsprom.features.builder`. It converts a plain experiment mapping into a
validated `FeatureEngineeringSpec`, instantiates the requested encoders, and
exports encoded data in two forms:

- `encode_sequences_as_vectors`: flattened feature vectors for classical
  classifiers.
- `encode_sequences_as_multi_head`: named feature heads for deep neural-network
  architectures.

This layer intentionally receives ordinary Python mappings rather than depending
on a specific YAML parser. YAML parsing can be added at the experiment-runner
level without changing the feature code.

Current validation behavior:

- Feature block names must be unique.
- Unsupported encodings fail during specification parsing.
- DNA-BERT blocks default to `zhihan1996/DNA_bert_6` and require `k: 6`.
- Physicochemical and PseKNC blocks must declare a reference table.
- The declared `k` must match the k-mer length encoded by the reference table.
- Unknown physicochemical properties fail fast.
- GC content/skew blocks must define either global features or a valid window size.
- Input sequences are validated against the strict DNA alphabet before encoding.


## GC Content and Skew Features

GC content and nucleotide skew features provide compact descriptors of sequence
composition. For a sequence window, GC content is computed as the fraction of
`G` and `C` bases, while GC skew is `(G - C) / (G + C)`. AT skew can also be
recorded as `(A - T) / (A + T)` when required.

These descriptors can be computed globally across the full 81 bp sequence and,
optionally, across fixed-size windows. Windowed descriptors are useful when the
experiment needs to preserve coarse positional information without using a full
position-by-base representation.

Example feature block:

```yaml
- name: gc_content_skew
  encoding: gc_content_skew
  include_global: true
  window_size: 27
  step: 27
  include_skew: true
  include_at_skew: false
```

## Pseudo K-Tuple Nucleotide Composition

The PseKNC encoder combines k-mer composition with sequence-order correlation
terms derived from selected physicochemical properties. In this project, the
main intended uses are PseDNC with the normalized dinucleotide table and PseTNC
with the normalized trinucleotide table. The method follows the pseudo k-tuple
nucleotide composition family introduced by Chen et al. (2014) and generalized
in PseKNC-General by Chen et al. (2015). PseDNC and PseTNC are documented as
specialized applications in iSS-PseDNC and iTIS-PseTNC, respectively.

For a selected property set, the encoder first estimates normalized k-mer
composition and then adds `lambda_value` correlation factors. Each correlation
factor compares physicochemical vectors for k-mers separated by a fixed lag. The
`weight` parameter controls the contribution of the correlation terms relative
to composition terms.

Example PseDNC block:

```yaml
- name: psednc_physicochemical
  encoding: pseknc
  k: 2
  reference_tsv: data/raw/references/normalized-dinuc.tsv
  properties:
    - Base stacking
    - B-DNA twist
    - Dinucleotide GC Content
  lambda_value: 3
  weight: 0.05
```

Example PseTNC block:

```yaml
- name: psetnc_physicochemical
  encoding: pseknc
  k: 3
  reference_tsv: data/raw/references/normalized-trinuc.tsv
  properties:
    - Bendability (DNAse)
    - Trinucleotide GC Content
  lambda_value: 3
  weight: 0.05
```

## DNA-BERT Embeddings

The feature layer can also represent each DNA sequence with embeddings from a
DNABERT-style Hugging Face model. The initial supported configuration targets
`zhihan1996/DNA_bert_6`, which uses overlapping 6-mer tokens. For example, the
sequence `ACGTACGT` is converted to the token sentence:

```text
ACGTAC CGTACG GTACGT
```

Example feature block:

```yaml
- name: dna_bert_6_embedding
  encoding: dna_bert
  model_name: zhihan1996/DNA_bert_6
  k: 6
  pooling: mean
  max_length: 128
```

DNA-BERT support is optional at runtime. The feature specification can be parsed
without installing deep-learning dependencies, but encoding sequences with this
block requires `torch` and `transformers` to be available in the project
environment. This keeps classical and physicochemical feature experiments light
while allowing deep representation experiments when the environment is ready.

## Feature Combination

Feature blocks can be used in two ways:

- `single_vector`: flatten and concatenate blocks for models such as XGBoost.
- `multi_head`: keep blocks separate for deep neural networks with one branch per
  input source.

The YAML configuration should record every active block, reference file, and
fusion strategy so that MLflow can reproduce the experiment.
