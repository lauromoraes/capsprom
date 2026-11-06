# CNNProm E. coli Panel Analysis

Exploratory, model-free description of the pilot panels (log R-076, findings
F-138 to F-141). No model was trained, no motif was extracted from a model, and
no test sequence was analysed.

**Superseded by `docs/reports/cnnprom_ecoli_panel_analysis_v3/` (R-079).** This
analysis used the training folds of grouped build v1. Build v2 changed most partitions, so its test records were largely
training rows here. Rerun the analysis on the v2 training folds before using it
for a decision.

To reproduce, from the repository root under WSL:

```bash
PYTHONPATH=.:src .venv/bin/python scripts/analyze_cnnprom_ecoli_panels.py
```

| Item | Location |
| --- | --- |
| Configuration | `configs/cnnprom_ecoli_panel_analysis_v2.yaml`, SHA-256 `df702eab…` |
| Script and features | `scripts/analyze_cnnprom_ecoli_panels.py`, `src/capsprom/eda/panel_analysis.py` |
| Figures, logo matrices, tables | `outputs/reports/cnnprom_ecoli_panel_analysis_v2/` (ignored by git) |
| Result manifest | `analysis_manifest.json`, SHA-256 `6932984e…` |
| Run log | `outputs/reports/_logs/cnnprom_ecoli_panel_analysis_v2.log` |

Version 1 of this analysis stays in `outputs/` as a record. Its t-SNE seed check
was empty: PCA initialization made all seeds identical. It is not used here.

## Main conclusions

1. **The native negatives are not a sample of the genome.** 97.2% of the training
   native negatives start in the first 200 kb of the 4,642 kb genome.
2. **They overlap each other across inner folds.** 3,070 window pairs overlap and
   1,663 of them fall in different inner folds. 2,277 overlap by less than 80%,
   which the homology grouping cannot see. This is a leakage risk for the native
   condition and should be resolved before training.
3. **The genomic panel removes the G+C shortcut, not the coding shortcut.** 85%
   of positives are noncoding, while 86% of genomic controls are coding.
4. **The promoter signal is visible in the genomic comparison.** Thirteen
   positions exceed the permutation limit, all around −35, −10, and the TSS.
5. **Projections mostly show G+C content.** PC1 correlates with G+C at about −0.96.
   Positives and genomic controls remain strongly mixed.

## Panels and partitions

A panel is one positive set paired with one negative definition.

- **Native negatives** are CNNProm source negatives, of source class
  `negative_opposite_strand_cds` (F-129).
- **Genomic controls** are same-strand NC_000913.3 windows with the G+C count of
  their positive, at least 100 nt from every known TSS (F-136).

| Analysis | Training folds | Test partition |
| --- | --- | --- |
| Record counts and homology group counts | Yes | Yes, counts only |
| Logos, distributions, pairing, context, consensus, diversity, projections | Yes | No |
| Identity check of the ledger against the native build | Yes | Yes, pass or stop only |

The code enforces this split: content analyses start after `training_records`,
and the script stops if a test row reaches them. The training contract
(`01049588…`) was written first, and its hash is pinned by the configuration.

**Table 1. Records and homology groups of the pilot.** Positives are reused:
838 positive sequences are in both panels, and rraBp1 is only in the native
panel (F-136). The 168 test positives are the same records in both panels.

| Panel | Partition | Positives | Groups | Negatives | Groups | Prevalence |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Native | Train | 671 | 638 | 2,399 | 1,721 | 0.219 |
| Native | Test | 168 | 159 | 601 | 458 | 0.218 |
| Genomic GC-matched | Train | 670 | 638 | 670 | 638 | 0.500 |
| Genomic GC-matched | Test | 168 | 159 | 168 | 159 | 0.500 |

All records are from *E. coli* K-12, source CNNProm. In the genomic panel each
control shares its positive's group. Counts for the other 18 native datasets and
the GraphPro v3 genomic and CDS panels are in `tables/dataset_panel_context_counts.csv`.
The GraphPro genomic ledgers have no partition column, so that table gives only
their pair counts.

## Sequence logos

![Sequence logos, zoomed scale](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig01_logos_zoomed.png)

**Figure 1. Dataset logos at a common 0 to 0.5 bit scale.** These logos come from
sequences, not from any model. Training folds only: 670 positives (one shifted
record excluded, as the contract requires), 2,399 native negatives, 670 genomic
controls. Heights are uncorrected Shannon information; the small-sample bias is
0.003 bits at n = 670 and 0.001 bits at n = 2,399. The TSS is marked only for
positives, because negatives have no TSS and their columns are window indices.
`fig01_logos_full_scale.png` shows the same logos at 0 to 2 bits.

Positives show −35 (TTG), −10 (TATAAT, peak 0.285 bits at −11), and an A/G at
the TSS. Native negatives are almost flat, with a mean of 0.005 bits per position.
Genomic controls have a mean of 0.027 bits; this flat level reflects their A+T
composition, not a positional signal. Matrices of counts, frequencies, and
information are in `matrices/`.

![Positional divergence](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig02_positional_divergence.png)

**Figure 2. Position-by-position total variation between positives and each negative
set.** The gray band is the 95th percentile of the maximum over positions under
500 label permutations. Training folds only.

Against genomic controls, 13 positions exceed the limit: −35, −34, −29, −14 to
−7, −1, and 0. Against native negatives, 70 of 81 positions exceed it, which
fits a broad composition difference rather than a local motif alone.

## Composition and pairing

![Distributions](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig03_distributions.png)

**Figure 3. Training counts and sequence-level distributions.** Every sequence is
81 nt, so length carries no signal. Means: window G+C 0.408 (positives), 0.532
(native), 0.408 (genomic); G+C of 500 nt flanks 0.493, 0.523, 0.454.

![Pairing diagnostics](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig04_pairing_diagnostics.png)

**Figure 4. Pairing diagnostics.** Left: all 670 training pairs have a G+C count
difference of 0. Middle: within-pair dinucleotide distance, median 0.225, against
0.250 for random re-pairing. Right: standardized mean difference by feature;
dotted lines mark ±0.1.

Matching works on its target and little beyond it. G+C is balanced, with a
standardized difference of −0.002 against −1.84 for native negatives. Seven of 20
features still exceed 0.1, the largest being GA (−0.24), lag-3 periodicity
(−0.23), and TA (+0.22). The two sides of a pair are only slightly more alike than
random pairs, and the controls' flanks are 3.8 G+C points poorer, so matching
tends to draw from A+T-rich regions.

## Genomic context

![Genomic context](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig05_genomic_context.png)

**Figure 5. Coding context and genome location of training windows.** A window is
coding when CDS annotation covers at least 50% of it. Strand is relative to the
window. Native negatives were placed by exact search; all 2,399 were found.

| Group | Noncoding | Same-strand CDS | Opposite-strand CDS |
| --- | ---: | ---: | ---: |
| Positives | 84.8% | 13.1% | 2.1% |
| Native negatives | 0.3% | 0.3% | 99.5% |
| Genomic controls | 13.7% | 43.0% | 43.3% |

![Native negative structure](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig10_native_negative_structure.png)

**Figure 6. Location and spacing of native negatives, training folds.** Left:
cumulative share along the genome. Right: distance between consecutive starts,
median 43 nt.

Native negatives are 97.2% below 200 kb and 99.3% below 300 kb, evenly split
between strands. They form 726 overlap components, the largest with 16 windows.
21 of them overlap a positive window. The same check across the train and test
partitions was not run, because the declared policy reads no test sequence.

## Consensus matches and diversity

![Consensus matches](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig06_consensus_matches.png)

**Figure 7. Fewest mismatches to textbook consensus elements, training folds.**
The search windows are fixed in the configuration before seeing results. They
measure sequence, not binding.

Within one mismatch of TATAAT: 35.3% of positives, 1.9% of native negatives, and
3.0% of genomic controls. For TTGACA: 12.5%, 2.8%, and 4.8%. Most positives
therefore have no near-consensus box, and some controls do.

![Diversity](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig07_diversity.png)

**Figure 8. Best ungapped identity on either strand, training folds.** This compares
windows at equal offset, so it does not detect shifted overlaps. Native negatives
look diverse here despite the overlaps in Figure 6.

No strand-invariant sequence is shared between the three groups. No control
overlaps a positive window, a native negative, or another control. 1.0% of
positives have a neighbour at 90% identity or more.

## Projections

![PCA](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig08_pca_common_space.png)

**Figure 9. PCA in one common space per representation.** Each column is one PCA
fitted once on all three groups together, 670 sequences per group with sampling
seed 20261106. Native negatives were subsampled so that they do not dominate the
axes. 4-mer and 3-mer frequencies use a Hellinger transform; one-hot keeps position.
Coordinates are comparable within a column only.

![t-SNE](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v2/figures/fig09_tsne_stability.png)

**Figure 10. t-SNE of the first 50 4-mer components.** One joint fit per panel, with
random starts for the seeds, perplexity 30 unless stated, and 1,000 iterations. The
last panel colours seed 13 by G+C.

PCA is the primary view because it is linear, its axes can be read, and all
groups share one fit. t-SNE is a neighbourhood check only. UMAP was not used, since
it is not installed and would add a dependency without answering a new question.

| Representation | PC1 variance | PC1–G+C correlation | Same-group 15-NN, 3 groups | Permutation 95% | Same-group 15-NN, positives vs genomic | Permutation 95% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4-mer | 4.5% | −0.96 | 0.503 | 0.339 | 0.539 | 0.507 |
| 3-mer | 10.4% | −0.97 | 0.494 | 0.338 | 0.532 | 0.506 |
| One-hot by position | 1.2% | −0.94 | 0.468 | 0.338 | 0.577 | 0.507 |

The native group separates along the G+C axis. Positives and genomic controls
overlap, and their neighbour agreement is only slightly above chance, most clearly
with one-hot input, which is the one representation that keeps position.

t-SNE orientation changes with the seed (median Procrustes disparity 0.39), so
its axes mean nothing. Neighbour agreement is stable across seeds at 0.509 to
0.515, and t-SNE keeps only about 21% of the 15 nearest neighbours of the
50-component space. Separation in these views is not evidence of predictive
performance or biological validity.

## Critical reading

**Observations** are the numbers above. They describe training folds and carry no
inference about the test partition.

**Hypotheses**, which this analysis cannot confirm:

- Native inner-validation scores may be inflated, because validation negatives
  share sequence with training negatives.
- A native-trained model may learn "not this coding region" or G+C content, which
  would predict many false positives elsewhere in the genome. H1 addresses this.
- A genomic-trained model may learn coding versus noncoding. Performance on the
  genomic panel would then partly reflect gene annotation, not promoter recognition.
- Some genomic controls may be real, unannotated promoters. The 3.0% near TATAAT
  is compatible with this but does not show it.

**Conclusions the evidence supports:**

- Native-panel specificity would describe about 200 kb of coding sequence, not the
  genome. The native condition is not a genome-background test.
- G+C matching succeeded, so a G+C-only model has no signal on the genomic panel.
- The genomic panel is a real but partial control. A good score on it does not show
  genomic promoter detection, which the contract already states.

**Limitations.** One organism and one assembly. The CDS call ignores RNA genes and
pseudogenes. Noncoding here is not a promoter-free label. R-070 and the 25-row
manual review had already seen pooled data including test rows, so "no test
sequence analysed" applies to this analysis, not to the project history. These
figures do not validate any control. Colours use the default validated categorical
palette; the palette validator could not be rerun because Node.js is not installed.

## Proposed changes to the training contract

The draft contract is unchanged. Everything here comes from training folds, so the
owner may adopt it without touching the test partition.

| Id | Proposal | Status |
| --- | --- | --- |
| P10 | Place native negatives on the genome and add genomic-overlap edges for them. The largest training component is 16 windows, so regrouping looks feasible. This needs a new grouped build, and partitions may change | Blocking, needs owner decision |
| P11 | Run the same overlap check across train and test as an identity-only integrity audit | Blocking, needs owner authorization |
| P12 | Report genomic-panel results also by control coding context, as a secondary stratum | Recommended |
| P13 | Consider a successor control policy with an intergenic stratum or coding-context matching, using training data only | For discussion |
| P14 | State in the thesis text that native specificity covers one genome region | Recommended |
