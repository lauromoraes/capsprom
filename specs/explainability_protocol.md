# Model Explainability Protocol

## Purpose and evidence boundary

Explainability artifacts describe model behaviour; they are not, by themselves,
biological evidence. The protocol distinguishes three evidence levels:

1. **learned patterns**, such as subsequences that strongly activate a
   convolutional filter;
2. **prediction attributions**, such as base-level integrated gradients for a
   specified output and reference distribution; and
3. **biological correspondence**, which additionally requires a predeclared
   comparison with an external motif resource or independent biological
   evidence.

Weights, attention scores, routing coefficients, capsule norms, and embedding
coordinates must not be presented as biological explanations in isolation.

## Data separation and selection

Pattern discovery uses only training examples. During inner selection, each
fold's discovery set is its fold-training partition and its evaluation set is
the held-out validation partition. Thresholds, attribution baselines, filter
selection, motif-clustering settings, and database-matching rules are fixed
from training/validation analyses before external-test access. The final test
partition may quantify a frozen pattern's occurrence, attribution, or
association with predictions, but may not select the method or its settings.

Every artifact is scoped by dataset identifier, model name, configuration hash,
seed, fold, checkpoint hash, source partition, and sequence identifiers. Pattern
stability is evaluated by aligning motifs across folds and seeds and reporting
matched-pattern frequency, alignment similarity, positional displacement, and
uncertainty. Absence of a stable match is reported rather than suppressed.

## Architecture and representation matrix

| Model or representation | Primary method | Mapping to original DNA | Reproducible artifacts | Sequence logo |
|---|---|---|---|---|
| Logistic regression on k-mer/classical features | signed coefficients plus held-out permutation control | each k-mer is mapped to all exact occurrences; global GC/skew or PseKNC terms have no unique base coordinate | feature vocabulary, coefficients, occurrence coordinates, held-out score changes | yes for selected sequence k-mers after occurrence alignment; not for non-local descriptors |
| XGBoost on k-mer/classical features | gain/SHAP-style attribution with held-out permutation control | same occurrence map as logistic regression; overlapping k-mers distribute attribution to their covered bases under a recorded rule | tree/model hash, feature contributions, occurrence map, aggregation rule | yes for aligned selected k-mer occurrences; not from gain values alone |
| CNN control and one-hot CapsProm | first-layer activation maximization and base-level integrated gradients; in-silico mutagenesis as a robustness analysis | convolution index maps directly to the length-`K` input window; one-hot attribution maps directly to nucleotide and position | sequence IDs, coordinates, strand, activations/attributions, selected windows, PFM/PPM, logo, checkpoint hash | yes, from aligned high-activation windows or attribution-derived seqlets |
| Embedding-CapsProm with `k=1` | integrated gradients through the embedding lookup plus convolutional activation windows | token `j` maps to base `j`; attribution is projected to the observed token/base and never inferred from embedding geometry alone | token vocabulary, embedding/checkpoint hash, token and base attribution arrays, windows and matrices | yes, after mapping selected tokens back to bases |
| Embedding-CapsProm with overlapping `k>1` | token-level integrated gradients and occlusion; aggregate overlapping token contributions with a frozen sum or mean rule | token `j` maps to bases `[j,j+k)`; the overlap aggregation rule produces base-level scores | token spans, raw token scores, base aggregation rule and scores, selected windows | yes, only after deterministic reconstruction/alignment in base coordinates |
| Multi-head sequence plus global descriptors | per-branch attribution followed by an explicitly recorded fusion analysis | sequence-aligned heads map by their receptive fields; global heads remain global | branch inputs, branch attributions, fusion outputs, coordinate maps | only for sequence-aligned branches |
| Frozen contextual vectors | attribution of the trained projection to vector dimensions, plus token occlusion if the encoder can be rerun | pooled dimensions have no direct nucleotide coordinate; token occlusion provides the defensible positional map | encoder/tokenizer revisions, pooling rule, projection checkpoint, occlusion scores | only from token/base perturbation results, not pooled dimensions |
| Joint contextual encoder | integrated gradients or token occlusion through the fold-local encoder; attention is supplementary only | tokenizer offsets map tokens to all covered bases; overlaps use a frozen aggregation rule | encoder checkpoint, tokenizer offsets, baselines, token/base scores, selected seqlets | yes, from mapped base-level attribution seqlets |

Perturbation analyses are model-agnostic and apply to every row above, not
only to one-hot models: any model can rescore a sequence after substitution by
rerunning its complete prediction pipeline. Window substitution and single-base
in-silico mutagenesis for all compared models are governed by
`specs/substitution_sensitivity_protocol.md`. Within the CNN control and
one-hot CapsProm row, in-silico mutagenesis additionally serves as the
robustness check for gradient attributions.

CapsProm routing can be analysed by perturbing selected input regions and
measuring changes in class-capsule lengths and routing coefficients. This tests
a capsule-specific mechanism, but routing coefficients alone are not feature
attributions and do not establish biological relevance.

## Convolutional activation logos

For each first-layer filter, candidate windows are the original length-`K`
subsequences under its valid-convolution activations. Unless a versioned
configuration says otherwise, discovery considers promoter-labelled training
sequences, retains at most one maximum-activation window per sequence, uses a
training-derived activation threshold, and keeps the predeclared top number of
windows. Reverse-complement canonicalization is disabled for the current
single-orientation datasets; a later strand-invariant model must record which
strand supplied each window.

The implementation persists the complete candidate/selection table, including
stable sequence identifier, start and exclusive end, strand, filter, activation,
label, and selection rank. It also persists nucleotide counts (PFM),
probabilities (PPM, with the recorded pseudocount), information-content values,
and an SVG logo. This follows the activation-window interpretation used by
DeepBind while retaining the underlying windows needed to audit the logo.

Attribution-derived motif discovery is a separate analysis. Integrated
Gradients is the default architecture-agnostic attribution candidate because it
targets a specified model output and satisfies sensitivity and implementation
invariance under its stated assumptions. DeepLIFT is a planned robustness
method when all operations have validated propagation rules. TF-MoDISco may
cluster base-level high-importance seqlets after its parameters and attribution
baseline are frozen. The output remains a model-derived pattern until matched
against known motifs using a predeclared database, background, similarity
metric, multiple-testing correction, and species-appropriate interpretation.

## References

- Alipanahi, B. et al. (2015). *Predicting the sequence specificities of DNA-
  and RNA-binding proteins by deep learning*. Nature Biotechnology 33,
  831--838. <https://doi.org/10.1038/nbt.3300>
- Sundararajan, M., Taly, A., and Yan, Q. (2017). *Axiomatic Attribution for
  Deep Networks*. ICML, PMLR 70:3319--3328.
  <https://proceedings.mlr.press/v70/sundararajan17a.html>
- Shrikumar, A., Greenside, P., and Kundaje, A. (2017). *Learning Important
  Features Through Propagating Activation Differences*. ICML, PMLR
  70:3145--3153. <https://proceedings.mlr.press/v70/shrikumar17a.html>
- Shrikumar, A. et al. (2018). *Technical Note on Transcription Factor Motif
  Discovery from Importance Scores (TF-MoDISco) version 0.5.6.5*.
  <https://arxiv.org/abs/1811.00416>
