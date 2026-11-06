# CNNProm E. coli Panel Analysis

Exploratory, model-free description of the pilot panels on grouped build v2 and
pilot build v2 (log R-079). No model was trained, no motif was extracted from a
model, and no test sequence was analysed here.

To reproduce, from the repository root under WSL:

```bash
PYTHONPATH=.:src .venv/bin/python scripts/analyze_cnnprom_ecoli_panels.py
```

| Item | Location |
| --- | --- |
| Configuration | `configs/cnnprom_ecoli_panel_analysis_v3.yaml`, SHA-256 `3fcbfb07…` |
| Script and features | `scripts/analyze_cnnprom_ecoli_panels.py`, `src/capsprom/eda/panel_analysis.py` |
| Figures, logo matrices, tables | `outputs/reports/cnnprom_ecoli_panel_analysis_v3/` (ignored by git) |
| Result manifest | `analysis_manifest.json`, SHA-256 `440e35c5…` |
| Run log | `outputs/reports/_logs/cnnprom_ecoli_panel_analysis_v3.log` |

Earlier versions stay in `outputs/` as records. Version 1 had an empty t-SNE seed
check, and version 2 read the training folds of the leaky partition (F-142).

## Main conclusions

1. **The leak found earlier is closed for uniquely placed records.** After
   regrouping, none of the 4,674 overlap edges between uniquely placed records
   crosses a partition. A small residual remains among repeat windows (below).
2. **The native negatives are not a sample of the genome.** 97.3% of the training
   native negatives start in the first 200 kb of the 4,642 kb genome.
3. **They carry much less independent information than their count suggests.**
   The 2,400 training native negatives form 551 homology groups, and the 600 test
   negatives form 125.
4. **The genomic panel removes the G+C shortcut, not the coding shortcut.** 86% of
   positives are noncoding, while 85% of genomic controls are coding.
5. **The promoter signal is visible in the genomic comparison.** Thirteen positions
   exceed the permutation limit, all around −35, −10, and the TSS.
6. **Projections mostly show G+C content.** PC1 correlates with G+C at about −0.96.
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
and the script stops if a test row reaches them. Regrouping and the gate audit did
read test sequences, for coordinates and for the audit's established descriptive
output. Because partitions were redrawn, most records of the new test partition
were training rows in analysis v2, and those aggregates were seen. No model output
exists, so no test outcome was seen.

**Table 1. Records and homology groups of the pilot.** Positives are reused: 836
positive sequences are in both panels, and 3 are only in the native panel. The 168
test positives are the same records in both panels.

| Panel | Partition | Positives | Groups | Negatives | Groups | Prevalence |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Native | Train | 671 | 560 | 2,400 | 551 | 0.219 |
| Native | Test | 168 | 147 | 600 | 125 | 0.219 |
| Genomic GC-matched | Train | 668 | 560 | 668 | 560 | 0.500 |
| Genomic GC-matched | Test | 168 | 147 | 168 | 147 | 0.500 |

All records are from *E. coli* K-12, source CNNProm. Group counts are per class, so
a mixed group counts once in each column. In the genomic panel each control shares
its positive's group. Counts for the other datasets are in
`tables/dataset_panel_context_counts.csv`, which still reads the native v1 builds
of those datasets and the GraphPro v3 panels.

## Sequence logos

![Sequence logos, zoomed scale](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig01_logos_zoomed.png)

**Figure 1. Dataset logos at a common 0 to 0.5 bit scale.** These logos come from
sequences, not from any model. Training folds only: 670 positives (one shifted
record excluded, as the contract requires), 2,400 native negatives, 668 genomic
controls. Heights are uncorrected Shannon information; the small-sample bias is
0.003 bits at n = 670 and 0.001 bits at n = 2,400. The TSS is marked only for
positives, because negatives have no TSS and their columns are window indices.
`fig01_logos_full_scale.png` shows the same logos at 0 to 2 bits.

Positives show −35 (TTG), −10 (TATAAT, peak 0.278 bits at −11), and an A/G at the
TSS. Native negatives are almost flat, with a mean of 0.005 bits per position.
Genomic controls have a mean of 0.029 bits; this flat level reflects their A+T
composition, not a positional signal. Matrices of counts, frequencies, and
information are in `matrices/`.

![Positional divergence](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig02_positional_divergence.png)

**Figure 2. Position-by-position total variation between positives and each negative
set.** The gray band is the 95th percentile of the maximum over positions under
500 label permutations. Training folds only.

Against genomic controls, 13 positions exceed the limit: −35, −34, −14 to −7, and
−2 to 0. Against native negatives, 71 of 81 positions exceed it, which fits a broad
composition difference rather than a local motif alone.

## Composition and pairing

![Distributions](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig03_distributions.png)

**Figure 3. Training counts and sequence-level distributions.** Every sequence is
81 nt, so length carries no signal. Means: window G+C 0.404 (positives), 0.532
(native), 0.405 (genomic); G+C of 500 nt flanks 0.493, 0.523, 0.452.

![Pairing diagnostics](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig04_pairing_diagnostics.png)

**Figure 4. Pairing diagnostics.** Left: all 668 training pairs have a G+C count
difference of 0. Middle: within-pair dinucleotide distance, median 0.238, against
0.262 for random re-pairing. Right: standardized mean difference by feature;
dotted lines mark ±0.1.

Matching works on its target and little beyond it. G+C is balanced, with a
standardized difference of −0.008 against −1.87 for native negatives. Ten of 20
features still exceed 0.1, the largest being lag-3 periodicity (−0.23), GA (−0.21),
and GT (+0.19). The two sides of a pair are only slightly more alike than random
pairs, and the controls' flanks are 4.0 G+C points poorer, so matching tends to
draw from A+T-rich regions.

## Genomic context

![Genomic context](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig05_genomic_context.png)

**Figure 5. Coding context and genome location of training windows.** A window is
coding when CDS annotation covers at least 50% of it. Strand is relative to the
window. Native negatives were placed by exact search; all 2,400 were found.

| Group | Noncoding | Same-strand CDS | Opposite-strand CDS |
| --- | ---: | ---: | ---: |
| Positives | 85.8% | 11.1% | 3.1% |
| Native negatives | 0.4% | 0.4% | 99.3% |
| Genomic controls | 14.8% | 41.5% | 43.7% |

![Native negative structure](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig10_native_negative_structure.png)

**Figure 6. Location and spacing of native negatives, training folds.** Left:
cumulative share along the genome. Right: distance between consecutive starts,
median 36 nt.

Native negatives are 97.3% below 200 kb and 99.3% below 300 kb. They form 539 overlap
components, the largest with 22 windows, and 14 overlap a positive window in
training. The script counts 20 overlapping pairs across inner folds. Each involves
a multi-locus record, which it places at the first match; the protocol gives these
records sequence edges only.

**Residual overlap.** A separate count over the whole build covered every locus of
the 28 multi-locus records. Among them, 9 pairs overlap at some locus across train
and test and 19 across inner folds, and one such record overlaps a uniquely placed
record in another fold. They are repeat windows and at most 0.7% of the records.

## Consensus matches and diversity

![Consensus matches](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig06_consensus_matches.png)

**Figure 7. Fewest mismatches to textbook consensus elements, training folds.**
The search windows were fixed in the configuration. They measure sequence, not
binding.

Within one mismatch of TATAAT: 34.6% of positives, 1.5% of native negatives, and
4.2% of genomic controls. For TTGACA: 12.8%, 2.6%, and 4.5%. Most positives
therefore have no near-consensus box, and some controls do.

![Diversity](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig07_diversity.png)

**Figure 8. Best ungapped identity on either strand, training folds.** This compares
windows at equal offset, so it does not detect shifted overlaps. Native negatives
look diverse here despite the overlaps in Figure 6.

No strand-invariant sequence is shared between the three groups. No control
overlaps a positive window, a native negative, or another control. 1.0% of positives
have a neighbour at 90% identity or more.

## Projections

![PCA](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig08_pca_common_space.png)

**Figure 9. PCA in one common space per representation.** Each column is one PCA
fitted once on all three groups together, 668 sequences per group with sampling
seed 20261106. Positives and native negatives were subsampled so that groups weigh
equally. 4-mer and 3-mer frequencies use a Hellinger transform; one-hot keeps
position. Coordinates are comparable within a column only.

![t-SNE](../../../outputs/reports/cnnprom_ecoli_panel_analysis_v3/figures/fig09_tsne_stability.png)

**Figure 10. t-SNE of the first 50 4-mer components.** One joint fit per panel, with
random starts for the seeds, perplexity 30 unless stated, and 1,000 iterations. The
last panel colours seed 13 by G+C.

PCA is the primary view because it is linear, its axes can be read, and all groups
share one fit. t-SNE is a neighbourhood check only. UMAP was not used, since it is
not installed and would add a dependency without answering a new question.

| Representation | PC1 variance | PC1–G+C correlation | Same-group 15-NN, 3 groups | Permutation 95% | Same-group 15-NN, positives vs genomic | Permutation 95% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4-mer | 4.5% | −0.96 | 0.506 | 0.339 | 0.538 | 0.507 |
| 3-mer | 10.4% | −0.97 | 0.498 | 0.338 | 0.531 | 0.506 |
| One-hot by position | 1.2% | −0.94 | 0.465 | 0.338 | 0.565 | 0.507 |

The native group separates along the G+C axis. Positives and genomic controls
overlap, and their neighbour agreement is only slightly above chance, most clearly
with one-hot input, the one representation that keeps position.

t-SNE orientation changes with the seed (median Procrustes disparity 0.45), so its
axes mean nothing. Three-group neighbour agreement is stable across seeds at 0.523
to 0.532, and t-SNE keeps only about 21% of the 15 nearest neighbours of the
50-component space. Separation in these views is not evidence of predictive
performance or biological validity.

## Critical reading

**Observations** are the numbers above. They describe training folds and carry no
inference about the test partition.

**Hypotheses**, which this analysis cannot confirm:

- A native-trained model may learn "not this coding region" or G+C content, which
  would predict many false positives elsewhere in the genome. H1 addresses this.
- A genomic-trained model may learn coding versus noncoding. Performance on the
  genomic panel would then partly reflect gene annotation, not promoter recognition.
- Some genomic controls may be real, unannotated promoters. The 4.2% near TATAAT is
  compatible with this but does not show it.

**Conclusions the evidence supports:**

- Native-panel specificity would describe about 200 kb of coding sequence, not the
  genome. The native condition is not a genome-background test.
- The native test panel has about 125 independent negative groups, so native
  specificity will be less precise than 600 records suggest.
- G+C matching succeeded, so a G+C-only model has no signal on the genomic panel.
- The genomic panel is a real but partial control. A good score on it does not show
  genomic promoter detection, which the contract already states.

**Limitations.** One organism and one assembly. The CDS call ignores RNA genes and
pseudogenes. Noncoding here is not a promoter-free label. The residual repeat
overlap above stays under the protocol's sequence-edge rule. Colours use the default
validated categorical palette; the palette validator could not be rerun because
Node.js is not installed. Other grouped datasets were not audited for overlap.

## Open proposals

| Id | Proposal | Status |
| --- | --- | --- |
| P10 | Join native negatives by genomic overlap | Done, build v2 (R-077) |
| P11 | Check overlap across train and test | Done during regrouping (F-142) |
| P12 | Report genomic-panel results also by control coding context, as a secondary stratum | Recommended, owner decision |
| P13 | Consider a successor control policy with an intergenic stratum or coding-context matching, using training data only | For discussion |
| P14 | State in the thesis text that native specificity covers one genome region | Recommended, owner decision |
| P15 | Decide whether multi-locus records should get overlap edges, which would change the homology protocol | Owner decision |
