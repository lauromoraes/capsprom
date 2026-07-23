# Academic Writing Specification

## Objective

Academic outputs in this repository must be thesis-ready, traceable to the
experimental pipeline, and internally coherent. This applies to Markdown notes,
LaTeX snippets, generated tables, plots, diagrams, and any text intended for the
doctoral thesis.


## Mathematical Notation Consistency

Thesis-oriented mathematical text must reuse the project notation before
introducing new symbols. Future edits, including AI-assisted edits, should check
this section and the current thesis chapter context before adding equations.

Canonical notation for the current promoter-prediction formulation:

- `\Sigma=\{A,C,G,T\}` denotes the strict DNA alphabet.
- `L=81` denotes the standardized sequence length.
- `x_i=(x_{i1},...,x_{iL})\in\Sigma^L` denotes one model-ready DNA sequence.
- `y_i\in\{0,1\}` denotes the binary class label.
- `\mathcal{D}=\{(x_i,y_i)\}_{i=1}^{n}` denotes a labeled dataset.
- `k` denotes k-mer length, `\mathcal{K}_k=\Sigma^k` the k-mer vocabulary, and
  `L_k=L-k+1` the number of overlapping k-mers in a standardized sequence.
- `u_{it}^{(k)}` denotes the `t`-th overlapping k-mer of sequence `x_i`.
- `\phi_j` denotes a feature mapping and `z_{ij}=\phi_j(x_i)` its output.
- `\Phi(x_i)` denotes a combined feature representation.
- `\rho^{(k)}` denotes a physicochemical reference mapping from k-mers to
  selected normalized property values.
- `\lambda` and `w` denote the PseKNC lag parameter and sequence-order weight.

When a symbol already has a canonical meaning, do not reuse it for a different
concept in the same chapter. Prefer notation commonly used in biological
sequence analysis and machine learning literature. For deep-learning concepts,
use the conventions of Goodfellow, Bengio, and Courville's *Deep Learning* when
applicable: explicit mappings for models and encoders, tensors/vectors for
representations, named parameter sets, and clear separation between data,
features, model functions, and learned parameters. Use indicator functions for
k-mer counts and `\operatorname{vec}` for flattening.


## Explanatory Feature Diagrams

When a DNA feature family would be clearer with a visual explanation, thesis
text should include one or more explanatory diagrams. This is especially
recommended for encodings whose mechanism is not immediately visible from the
sequence string alone, such as k-mer tokenization, physicochemical lookup
matrices, PseKNC sequence-order correlations, DNA-BERT tokenization/embedding,
and multi-head feature fusion.

Feature diagrams may be original schematic diagrams inspired by the method
described in the source literature, but they must not reproduce copyrighted
figures from papers without permission. When the diagram is based on an original
method or article, the surrounding text and/or caption must cite the relevant
source. Every such figure must follow the figure/table reference rule: it needs
a preceding textual reference, a stable label, and a descriptive caption that
explains the conceptual operation shown by the diagram.

Captions for feature diagrams should state:

- The feature family or transformation represented.
- The input object, such as a sequence, k-mer stream, property table, or tensor.
- The main transformation steps.
- The resulting representation consumed by the classifier.
- The methodological source or inspiration, when applicable.

## Figure and Table Reference Rule

No figure, table, chart, diagram, or other floating visual artifact may appear
without being introduced and referenced in the surrounding text.

Every figure or table must have:

- A descriptive caption explaining what the reader should understand from it.
- A stable `\label{...}`.
- At least one preceding textual reference using `Figure~\ref{...}` or
  `Table~\ref{...}` before the artifact appears.
- Enough surrounding explanation that the artifact is not interpreted as a
  standalone decoration.

This rule applies to:

- LaTeX tables and figures.
- TikZ diagrams and flowcharts.
- Exported plots and charts.
- Result tables generated from experiments.
- Any thesis-oriented visual or tabular artifact.

## Quality Check

Before finalizing a thesis-oriented document, verify that:

- Every `figure` environment has a preceding textual reference, caption, and
  label.
- Every `table` environment has a preceding textual reference, caption, and
  label.
- Captions describe the analytical purpose of the artifact, not only its title.
- Text explains how the artifact supports the argument or methodology.
