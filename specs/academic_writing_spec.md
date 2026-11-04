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

The problem formulation is defined once, in thesis Section
`sec:bg-formulation` (Chapter 2, `chapters/02_background.tex`). Other chapters
and drafts cite that section with `\ref` and do not redefine its symbols; they
may only add domain-specific detail (for example, the sources in
`\mathcal{D}_s`). Before submission, search the thesis for each symbol below and
confirm that it has a single definition.

Canonical notation (approved 2026-11-04; rationale and the full collision audit
in `docs/thesis/notation_audit.md`). One letter has one meaning at thesis
scope; a letter may be reused only as a bound index inside a single displayed
formula. Labels in subscripts are upright (`n_{\mathrm{boot}}`); indices are
italic. Losses are always calligraphic (`\mathcal{L}`), never `L`.

Problem formulation (defined in `sec:bg-formulation`):

- `\Sigma_{\mathrm{DNA}}=\{\mathrm{A},\mathrm{C},\mathrm{G},\mathrm{T}\}`:
  strict DNA alphabet. Never write a sum as `\Sigma`; use `\sum`.
- `L`: window length of a dataset, fixed by domain
  (`sequence_length_by_domain` in `configs/evaluation_protocol_v4.yaml`):
  `L=81` for prokaryotes and `L=251` for eukaryotes.
- `\mathcal{X}_L=\Sigma_{\mathrm{DNA}}^{L}`: input space;
  `x_i=(x_{i1},\dots,x_{iL})\in\mathcal{X}_L`, generic position `t`
  (`x_{it}`).
- `\mathcal{Y}=\{0,1\}`: label space (`1`: promoter; `0`: non-promoter).
- `\mathcal{D}=\{(x_i,y_i)\}_{i=1}^{n}`: labeled dataset drawn from
  `p_{\text{data}}`.
- `f(\Phi(x);\boldsymbol{\theta})\in[0,1]`: positive-class score of model `f`
  with learned parameters `\boldsymbol{\theta}`.
- `\hat y=h(x)=\mathbf{1}[f(\Phi(x);\boldsymbol{\theta})\ge t^{\star}]`:
  classifier and binary decision; `t^{\star}` is the threshold (primary value
  `0.5`).

Data (Chapter 4): `s\in\mathcal{S}` source study; `d` dataset index
(`\mathcal{D}_{s,d}`, `\mathcal{P}_{s,d}`, `\mathcal{N}_{s,d}`,
`\mathcal{C}_{s,d}`); `p_{\text{data},s}` source distribution; raw sequence
`\tilde x_i`, raw size `\tilde n_s`; cropping `\operatorname{crop}_s`; filter
predicate `\operatorname{keep}`; stage counts `n^{+}_{c}`, `n^{-}_{c}`.

Features (Chapter 5): `k` k-mer length, `\mathcal{K}_k=\Sigma_{\mathrm{DNA}}^{k}`,
`L_k=L-k+1`, `u_{it}^{(k)}`; `\phi_j`, `\mathbf{z}_{ij}=\phi_j(x_i)`, `J`,
`\Phi`; nucleotide `\nu`, counts `N_\nu(x_i)`; local window width `\omega`;
`\rho^{(k)}` with `n_\rho` properties indexed by `q`; PseKNC highest tier
`\lambda`, lag `\delta`, correlations `\gamma_{i,\delta}^{(k)}` (Chen et al.
write `\theta_j`), weight `w`; `O_i^{(k)}`, `F_i^{(k)}`, `P_i^{(k)}`,
`Q_i^{(k,\lambda,w)}`; encoder `\operatorname{enc}_{\mathrm{BERT}}`, embedding
`\mathbf{e}_i\in\mathbb{R}^{d_{\mathrm{emb}}}`; fusion branches `\psi_j`.

Models (Chapter 6): capsule symbols of Sabour et al. (`\mathbf{u}_i`,
`\mathbf{W}_{ij}`, `\hat{\mathbf{u}}_{j\mid i}`, `b_{ij}`, `c_{ij}`,
`\mathbf{s}_j`, `\mathbf{v}_j`); these equations describe one input, so `i,j`
index capsules there and the section says so. Routing iterations
`n_{\mathrm{iter}}`; margin loss with `T_{y'}`, `m^{\pm}`, down-weight `\beta`;
reconstruction weight `\beta_{\mathrm{rec}}`; attention
`\mathbf{Q}_{\mathrm{att}},\mathbf{K}_{\mathrm{att}},\mathbf{V}_{\mathrm{att}}`,
`d_{\mathrm{key}}`, `n_{\mathrm{heads}}`.

Protocol and statistics (Chapters 7 and 8): experiment tuple
`(\mathcal{D},\Phi,f,\boldsymbol{\theta},\boldsymbol{\xi},E,r)` with
hyperparameter configuration `\boldsymbol{\xi}\in\Xi`; seed `r`; learning rate
`\epsilon`; `n_{\mathrm{batch}}`, `n_{\mathrm{epoch}}`; paired difference
`\Delta` (`\Delta_{d,r}`, `\Delta_d`); compared models `A`, `B` (italic;
nucleotides are upright); `n_{\mathrm{boot}}`, `n_{\mathrm{perm}}`; `\alpha`,
`p`; Wilcoxon `T`, Friedman `\chi^2_F`; `n_{\mathcal{D}}`, `n_{\mathrm{mod}}`;
upright `\mathrm{TP}`, `\mathrm{TN}`, `\mathrm{FP}`, `\mathrm{FN}`,
`\operatorname{MCC}`; calibration bins `\mathcal{B}_b`, `n_{\mathrm{bin}}`;
homology groups `\mathcal{G}`, `g`, Hamming distance `d_{\mathrm{H}}`;
attributions `\operatorname{IG}`, `\operatorname{SHAP}` (never `\phi`).

Retired symbols: score `s(x)`; `P` for the distribution; `z_i` for raw
sequences; `c_s`; `q` as filter; `k` as dataset index; `b` as nucleotide;
`h` as window width; `m` and `r` for physicochemical properties; `d` as PseKNC
lag; `\theta` for PseKNC correlations or hyperparameters; `g` for fusion
branches or the BERT encoder; `B_i`, `d_B`; `s` as seed; Sabour's `\lambda` and
`r`.

Deviations from Goodfellow et al.: examples are indexed by subscript (`x_i`,
not `x^{(i)}`), because parenthesised superscripts denote k-mer length; sets are
calligraphic (`\mathcal{X}`), following learning-theory usage; DNA sequences
are strings, not real vectors, and are not bold.

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
