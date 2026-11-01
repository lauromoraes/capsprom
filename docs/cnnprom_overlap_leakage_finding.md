# Overlapping Negatives in CNNProm and Train/Test Leakage

Status: finding for thesis discussion (Chapter 9). Evidence is exploratory
(log R-027): a single MMseqs2 audit outside the versioned pipeline. The
pipeline step that makes it reproducible is `specs/homology_grouping_protocol.md`.
Findings F-084 to F-089.

## 1. Summary

The CNNProm negative sets were built by drawing many fragments from a small
amount of DNA. Bacterial negatives are overlapping windows of the same genome
stretches (F-085); human non-TATA negatives are 27,731 fragments of 163 GenBank
clones covered about five times over (F-086). A random train/test split of
such files puts shifted copies of the same DNA on both sides. Exact-identity
deduplication, which our canonical build applies, and the Hamming audit of the
statistical protocol cannot see this, because a window shifted by a few
nucleotides differs at almost every position.

Measured on the regenerated-v3 build (F-084):

| Dataset | Test positives with a training neighbour | Test negatives with a training neighbour |
| --- | ---: | ---: |
| CNNProm Human non-TATA | 1.7% | **67.1%** |
| CNNProm *B. subtilis* | 2.7% | **40.5%** |
| CNNProm *E. coli* | 8.3% | **38.3%** |
| CNNProm Mouse non-TATA | 1.1% | **10.5%** |
| CNNProm Mouse TATA, *Arabidopsis* TATA/non-TATA | 0.1–1.2% | 0.7–3.8% |
| CDBProm, 11 organisms | 1.0–5.0% | 0.0–1.5% |

Neighbour: ≥80% identity over ≥80% of both 81-nt sequences, either strand.

## 2. What the overlap is

- **Same locus, shifted window.** In *E. coli* and *B. subtilis* the FASTA
  headers are start coordinates, and 77–78% of coordinate-adjacent negatives
  lie less than 81 nt apart and are exact shifted copies (F-085). In human,
  63.6% of test negatives share a clone with a training negative at identity
  1.00 (F-086). This leakage follows from how the negatives were made.
- **Repeats, not label noise.** 303 human test negatives also align to a
  training *positive*. None of these windows occurs verbatim in a positive.
  Their identity is around 85%, not 100%, and they spread over 57 clones and 61
  promoters (F-087). The likely cause is interspersed repeats, chiefly Alu,
  present both in gene bodies and in promoter windows (F-088; Hypothesis). This
  is a weaker form of dependence, a shared sequence family, not a mislabelled
  locus. An earlier conversational reading as "label noise" is withdrawn.
- **Asymmetry.** Leakage is almost entirely on the negative class. Positives
  come from curated databases (RegulonDB, DBTBS, EPDnew) with one window per
  promoter. Negatives were sampled with replacement in genomic position.

## 3. Consequences for published and project results

1. **Published CNNProm numbers.** Umarov and Solovyev (2017) report a 20% test
   set with no stated randomisation scheme and no redundancy or overlap
   removal (F-089). Their split is not released, so its contamination cannot
   be counted. However, F-085 and F-086 are properties of the files, not of our
   split. Any record-level random split reproduces them. The reported
   specificities (human non-TATA 0.98, *E. coli* 0.96, *B. subtilis* 0.95) and
   correlation coefficients are therefore expected to include a component of
   recognising previously seen DNA. The size of that component is unknown.
2. **Direction of the bias.** A model that memorises negative loci classifies
   their shifted copies correctly without learning what a non-promoter is.
   Specificity is inflated, and through it MCC, accuracy and ROC-AUC. The
   inflation should grow with model capacity, since convolutional and capsule
   networks memorise local k-mer content more readily than a linear k-mer
   model. This favours exactly the architectures the thesis proposes.
3. **Other studies.** Any later work that benchmarks on the CNNProm files with
   a random split, including CapsProm (Moraes et al., 2022), inherits the same
   dependence. That claim holds by construction. It does not need their splits.
4. **This project.** Development and exploratory runs on the regenerated-v3
   build carry the bias for the four affected CNNProm pairs. Under the
   project's own rules none of those runs is confirmatory, so no reported
   conclusion changes. Confirmatory runs must use the grouped partition of
   `specs/homology_grouping_protocol.md`.

## 4. Points for the thesis discussion

- **Contribution.** The finding identifies a construction property of a widely
  reused benchmark and shows how much exact deduplication leaves behind. It
  also supplies a reproducible correction: alignment-based connected-component
  grouping before partitioning (Teufel et al., 2023; Petti and Eddy, 2022).
  This applies to the broader concern about leakage in ML-based science
  (Kapoor and Narayanan, 2023).
- **Testable prediction.** If memorisation explains part of published
  performance, then:
  - specificity on CNNProm Human non-TATA, *E. coli* and *B. subtilis* falls
    under grouped partitioning;
  - CDBProm, at <2% overlap, barely changes;
  - the fall is larger for high-capacity models.

  Reporting grouped and record-level results side by side, as a predeclared
  sensitivity analysis, measures this directly and turns the finding into a
  result.
- **What not to claim.** The published CNNProm numbers cannot be called wrong,
  nor can a corrected value be put on them. Only the dependence in their data
  is established; its effect on their reported metrics is inferred.
- **Scope of the evidence.** The audit used 81-nt windows of the regenerated-v3
  build. Under `specs/sequence_window_policy.md` the eukaryotic window is
  251 nt, where five-fold fragment coverage implies even larger shared
  stretches. Overlaps shorter than 65 nt were not counted, so the reported
  shares are lower bounds.

## 5. References

- Kapoor, S. and Narayanan, A. (2023). Leakage and the reproducibility crisis
  in machine-learning-based science. *Patterns* 4(9):100804.
  doi:10.1016/j.patter.2023.100804
- Moraes, L. et al. (2022). CapsProm (see `references.bib`, `moraes2022capsprom`).
- Petti, S. and Eddy, S. R. (2022). Constructing benchmark test sets for
  biological sequence analysis using independent set algorithms. *PLoS
  Computational Biology* 18(3):e1009492. doi:10.1371/journal.pcbi.1009492
- Steinegger, M. and Söding, J. (2017). MMseqs2 enables sensitive protein
  sequence searching for the analysis of massive data sets. *Nature
  Biotechnology* 35(11):1026–1028. doi:10.1038/nbt.3988
- Teufel, F. et al. (2023). GraphPart: homology partitioning for biological
  sequence analysis. *NAR Genomics and Bioinformatics* 5(4):lqad088.
  doi:10.1093/nargab/lqad088
- Umarov, R. K. and Solovyev, V. V. (2017). Recognition of prokaryotic and
  eukaryotic promoters using convolutional deep learning neural networks.
  *PLOS ONE* 12(2):e0171410. doi:10.1371/journal.pone.0171410
