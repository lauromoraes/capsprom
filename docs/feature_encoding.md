# Feature Encoding Notes

The project supports feature construction as named blocks. This keeps feature
engineering independent from the classifier and makes it possible to compare
single-source and multi-source inputs under the same experimental pipeline.

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

## Feature Combination

Feature blocks can be used in two ways:

- `single_vector`: flatten and concatenate blocks for models such as XGBoost.
- `multi_head`: keep blocks separate for deep neural networks with one branch per
  input source.

The YAML configuration should record every active block, reference file, and
fusion strategy so that MLflow can reproduce the experiment.
