# Substitution Sensitivity Protocol

## Purpose and status

This specification defines a model-agnostic perturbation analysis that measures
how strongly each trained model depends on each region of the 81-bp input
window. It extends the random substitution method of Umarov and Solovyev
(2017) from CNNProm to every model compared in this thesis and adds
single-base in-silico mutagenesis (ISM) as a higher-resolution complement.

Status: design only. No implementation, state file, MLflow run, or result
exists. The versioned contract is `configs/substitution_sensitivity_v1.yaml`.

## Evidence level

Both analyses are prediction attributions (level 2 of
`specs/explainability_protocol.md`). Perturbed sequences lie outside the
training distribution, so a score drop shows that the model depends on a
region; it does not establish that the region is biologically functional. A
different profile between two models shows different dependence, not better or
worse performance. Biological correspondence requires the separate level-3
analysis.

## Source method

Umarov and Solovyev (2017, PLOS One 12(2):e0171410, section "Random
substitution method to discover positionally conserved functional elements")
replace a window of length `L` with a random sequence, evaluate the trained
model, and slide the window to build a per-position performance profile. Their
example uses `L = 6` and reports promoter sensitivity. The article does not
state the stride, the random distribution, the number of repetitions, or the
evaluated partition. The choices below fill those gaps and are therefore an
adaptation, not a reproduction.

The method targets elements that occupy approximately the same position in
every sequence. Elements with variable positions dilute in the average and are
not expected to form peaks.

## Coordinates

Every model receives the canonical 81-bp window. Index `i` in `[0, 80]` maps to
position `i - 60` relative to the TSS, so index 60 is the TSS and the window
covers -60..+20. No padding, circular wrapping, or genomic flank extension is
used.

## Window substitution (primary analysis)

For window length `L`, the start indices are `0..81-L` with stride 1 (76 starts
for `L = 6`). For each start, every evaluated sequence has bases
`[start, start + L)` replaced and all other bases kept unchanged. Each
repetition draws new bases.

- Primary window length: `L = 6`, as in the source method.
- Sensitivity window lengths: `L = 3` and `L = 12`.
- Primary replacement distribution: independent draws from the mononucleotide
  composition of the training partition of the same dataset and fold. This
  avoids confusing loss of a motif with an injected composition shift.
- Sensitivity replacement distribution: uniform (0.25 per base), as implied
  by the source method.
- Random draws are deterministic functions of dataset identifier, model seed,
  fold, window length, start, and repetition.

The primary profile is reported per window start. A per-base profile may also
be reported as the mean of all windows that contain the base. Base `i` is
covered by `min(i + 1, L, 81 - i)` windows, and this coverage is reported with
the per-base profile because edge bases average fewer windows.

Truncated edge windows are not used: replacing fewer bases mechanically
reduces the effect and would understate edge positions.

## Single-base in-silico mutagenesis (complement)

For each index `i` and each of the three alternative nucleotides, one base is
substituted and the sequence rescored. This yields 243 deterministic variants
per sequence and an `81 x 4` effect matrix per model, with zero at the
reference nucleotide. Positional summaries are the mean and the maximum
effect across the three alternatives.

ISM is computed separately for promoters and non-promoters. The promoter
matrix measures loss of score; the non-promoter matrix measures score gained
by single substitutions and shows whether a nucleotide-composition preference
(for example, A/T raising the score at every position) is class-independent.
Both matrices are descriptive and do not enter the predeclared contrasts.

ISM resolves which base and which nucleotide matter. It can understate
redundant or distributed elements that survive one substitution but not the
destruction of a whole window; window substitution covers that case. Neither
analysis replaces the other.

## Scoring and metrics

Each model is wrapped by a scorer that maps sequences to the model's own
promoter score through the complete prediction pipeline: one-hot tensors for
CapsProm and CNN models, k-mer recomputation for logistic regression and
XGBoost, DDS recomputation for the CDBProm adaptation, and tokenization for
contextual encoders. An unperturbed pass must reproduce stored predictions
exactly.

Scores are not on a common scale (capsule length is not a calibrated
probability), so the primary metric is relative:

```text
relative_drop(start) = (mean_score_original - mean_score_perturbed) / mean_score_original
```

computed over promoter sequences and averaged across repetitions. Secondary
metrics are the absolute score drop, the sensitivity drop at the fixed 0.5
threshold of `specs/statistical_evaluation_protocol.md`, and the mean score
change on non-promoter sequences (false-positive gain).

## Data separation and use

- Settings are frozen on inner-validation partitions only: each fold's model
  is evaluated on its own held-out validation partition.
- The number of repetitions `R` is the smallest value in the predeclared list
  whose Monte Carlo standard error of the primary metric is at or below the
  predeclared limit at every window start, pooled over inner folds. Nothing
  else may be tuned from these profiles; the regions and metrics below are
  fixed before any profile is computed.
- The confirmatory profile is computed once on the external test partition
  with frozen final models, after final fits are separately authorized.
- Profiles are not a model-selection criterion. MCC remains the only selection
  metric. Profiles may raise predeclared diagnostic flags (see below) that are
  reported, not acted upon, within an existing contract.

Using these profiles to choose hyperparameters, or training with window
substitution as augmentation, would remove their value as independent evidence
and would require a new versioned contract and an explicit project decision.

## Predeclared regions

Regions are fixed from the literature before any profile exists and are
approximate consensus locations, not dataset-specific annotations.

| Dataset group | Region | Coordinates (relative to TSS) |
|---|---|---|
| Prokaryotic (11 CDBProm, CNNProm E. coli and Bacillus) | sigma70-type -35 element | -36..-29 |
| Prokaryotic | sigma70-type -10 element | -13..-6 |
| Eukaryotic TATA (Mouse TATA, Arabidopsis TATA) | TATA box | -32..-23 |
| Eukaryotic non-TATA (Human, Mouse, Arabidopsis non-TATA) | Initiator | -3..+5 |

Known limitations, reported with every result:

- Several CDBProm organisms use sigma-factor families whose consensus differs
  from E. coli sigma70; the prokaryotic regions are approximations.
- The CDBProm TSS alignment is not uniform for every organism (only 53 of 200
  sampled H. pylori positives matched the dominant offset), which can flatten
  peaks independently of the model.

The regional summary of a profile is the mean primary metric over window
starts whose window overlaps the region by at least half of its length, and
over the dataset's predeclared regions.

## Diagnostic flags

The following are reported per dataset, model, and seed and never used for
selection:

- `flat_profile`: no window start exceeds the predeclared minimum relative
  drop, suggesting dependence on dispersed composition rather than local
  elements.
- `edge_dominant`: the maximum drop lies within the first or last `L` starts.

## Statistical analysis

All profiles are reported descriptively with across-seed intervals, peak
location and height, and overlap with the predeclared regions.

Inference is restricted to the regional summary and the predeclared contrasts:

1. primary: basic CapsProm versus the parameter- and stem-matched CNN without
   capsules;
2. secondary: basic CapsProm versus the CNNProm adaptation.

Within each dataset the ten seeds are paired; the cross-dataset test is the
two-sided Wilcoxon signed-rank test over the 18 confirmatory datasets, with
Holm correction across the two contrasts, following
`specs/statistical_evaluation_protocol.md`. ISM summaries are descriptive
only. Per-position tests are not performed.

## Artifacts

Each run persists, with dataset, configuration, and checkpoint hashes and the
MLflow run identifier:

- per-start, per-repetition scores and the aggregated window profile;
- the per-base profile with coverage counts;
- the ISM effect matrix and positional summaries;
- regional summaries and diagnostic flags;
- the random-draw seeds and replacement composition.

## Dependencies and gates

- The CNN matched to the CapsProm stem and parameter count does not yet exist;
  the primary contrast is blocked until its contract is frozen and trained
  under the same datasets, folds, seeds, selection rule, and budget.
- Inner-fold evaluation needs the per-fold best checkpoints. Their retention
  after the v4 resume-checkpoint pruning must be verified; classical inner-fold
  models may need refitting under unchanged hashes.
- External-test execution requires authorized and completed final fits.

## References

- Umarov, R. K. and Solovyev, V. V. (2017). Recognition of prokaryotic and
  eukaryotic promoters using convolutional deep learning neural networks.
  PLOS One 12(2):e0171410. <https://doi.org/10.1371/journal.pone.0171410>
- Harley, C. B. and Reynolds, R. P. (1987). Analysis of E. coli promoter
  sequences. Nucleic Acids Research 15(5):2343--2361.
  <https://doi.org/10.1093/nar/15.5.2343>
