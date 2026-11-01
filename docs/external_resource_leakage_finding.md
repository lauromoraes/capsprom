# External Training Data and Pretrained Baselines: Cross-Study Leakage

Status: finding for thesis discussion (Chapter 9). Evidence is exploratory
(log R-032): one exact-substring audit and one MMseqs2 audit outside the
versioned pipeline. Findings F-106 to F-113; F-110 to F-113 are hypotheses.
Companion to `docs/cnnprom_overlap_leakage_finding.md`, which covers leakage
*inside* one benchmark. This document covers leakage *between* benchmarks and
into the released data and weights of baseline methods.

## 1. Summary

Promoter benchmarks are assembled from a few curated resources (RegulonDB,
DBTBS, EPDnew, primary TSS maps). Different studies therefore hold the same
promoters under different names, and a model trained on one study's data has
often seen another study's test set. We measured this for two resources that
baselines of this thesis ship with: iPro-MP's 23-species benchmark (train and
test, the data behind its released per-species weights), and the GUE promoter
sets used to fine-tune DNABERT-type models and EDEN.

Eligible regenerated-v3 test records with a neighbour in the external resource
(≥80% identity over ≥80% of the sequence, either strand; F-108, F-109):

| Test set | External resource | Positives | Negatives |
| --- | --- | ---: | ---: |
| CDBProm *Anabaena* sp. | iPro-MP | **503/503** (100%) | 49/502 (9.8%) |
| CDBProm *C. glutamicum* | iPro-MP | **112/112** (100%) | 8/114 (7.0%) |
| CDBProm *H. pylori* | iPro-MP | **119/141** (84.4%) | 8/142 (5.6%) |
| CNNProm *E. coli* | iPro-MP | **168/168** (100%) | 160/600 (26.7%) |
| CNNProm *B. subtilis* | iPro-MP | **75/75** (100%) | 2/200 (1.0%) |
| CDBProm S. Typhimurium | iPro-MP | 53/196 (27.0%) | 13/195 (6.7%) |
| CDBProm *K. pneumoniae* | iPro-MP | 41/266 (15.4%) | 15/265 (5.7%) |
| CNNProm Human non-TATA | GUE | **2,728/3,956** (69.0%) | 586/5,404 (10.8%) |
| CNNProm Mouse non-TATA | GUE | 677/3,253 (20.8%) | 15/4,959 (0.3%) |
| CNNProm Mouse TATA | GUE | 67/250 (26.8%) | 2/706 (0.3%) |

Three further CDBProm pairs have at most 12 affected records against iPro-MP.
The remaining pairs have none against either resource. Of the identical
records, 491 *Anabaena*, 105 *C. glutamicum*, 88 *H. pylori* and 132 *E. coli*
test positives occur verbatim in iPro-MP (F-106).

## 2. What the overlap is

- **Positive-side, not negative-side.** Inside CNNProm the leakage was almost
  entirely negative (F-084). Here it is almost entirely positive: in five
  bacterial sets every or nearly every test promoter is in iPro-MP. This fits
  a shared upstream source of curated promoters or TSS (F-110, hypothesis).
- **Same organism under another name.** The *Anabaena* hits come from iPro-MP
  species 13, *Nostoc* sp. PCC 7120, the strain also designated *Anabaena* sp.
  PCC 7120. Name-based matching of organisms across studies would miss it.
- **Close relatives.** S. Typhimurium and *K. pneumoniae* hits come mainly from
  iPro-MP *E. coli* K-12 and *Shigella flexneri*. Conserved enterobacterial
  promoters are a plausible cause (F-111, hypothesis).
- **Conservation, not shared records, for mouse.** GUE is human-only, so the
  mouse hits are cross-species sequence conservation of promoter regions
  (F-112, hypothesis). Conservation is a real biological signal, but it still
  makes a human-trained model's mouse test performance partly recall of human
  sequence.
- **Negatives.** The *E. coli* negative overlap (26.7%) is consistent with both
  studies sampling non-promoters from the same K-12 genome. It is not evidence
  of mislabelling.

## 3. Consequences

1. **Released weights cannot be evaluated on these test sets.** iPro-MP's
   per-species weights, and any DNABERT or EDEN checkpoint fine-tuned on GUE,
   have seen most positives of the affected sets (F-107). Their output there
   measures recall of training data.
2. **Pretraining and transfer.** The same applies to any use of these resources
   as pretraining, auxiliary or augmentation data for a model later tested on
   the affected sets.
3. **Published cross-study comparisons.** A study that reports a method trained
   on one benchmark and tested on another, or compares released models across
   benchmarks, inherits the overlap without needing their splits. The direction
   of the bias is the same as in the CNNProm finding: inflated sensitivity
   here, since the leak is on positives (F-113, hypothesis).
4. **Dataset independence.** The dependency manifest treats CDBProm and CNNProm
   datasets as separate sources. Shared promoters mean some cross-source pairs
   (*E. coli*, *B. subtilis*) may not be independent units for cross-dataset
   inference. This must be checked against `configs/dataset_dependency_manifest_v2.yaml`.
5. **What remains valid.** Training every baseline from scratch on the
   project's own training partition is unaffected. So is a fidelity check run
   on a method's own published split, since it never touches our test sets.
   Unsupervised DNABERT pretraining on the human genome is a separate exposure,
   not measured here.

## 4. Proposed methodology

The two findings together suggest an audit that existing benchmarks do not
perform: dependence must be checked not only within one dataset's train/test
split, but against every external resource a model has seen.

1. **External-resource register.** Before a baseline is used, list every
   dataset behind its pretraining, fine-tuning and released weights, with
   acquisition records and hashes.
2. **Cross-resource alignment audit.** Search each test set against each
   registered resource with the F-084 criterion. Report affected records per
   class. This extends `specs/homology_grouping_protocol.md` from one dataset
   to the union of resources.
3. **Exclusion or stratified reporting.** A released checkpoint is used on a
   test set only if the audit finds no material overlap. Otherwise, either
   train from scratch under the common protocol, or report the affected and
   unaffected test records separately.
4. **Organism identity by accession, not name.** Match organisms across
   studies by assembly or strain identifier, as done for *Nostoc*/*Anabaena*.
5. **Cross-source dependency clusters.** Feed shared-record evidence into the
   dataset dependency manifest so that cross-dataset tests do not count
   dependent datasets twice.

**Testable prediction.** If overlap inflates released-model performance, then
on the affected sets a released iPro-MP checkpoint scores higher on the
overlapping test positives than on the non-overlapping ones, and higher than
the same architecture trained from scratch on our training partition. Both
comparisons are exploratory and must not influence model selection.

## 5. Scope and limits

- 81-nt regenerated-v3 windows; other windows may change the counts.
- Identity ≥80% is a dependence criterion, not proof of a shared source record.
  The exact-identity counts (F-106) are the conservative figure.
- GUE was searched with query coverage only (`--cov-mode 2`), because its
  windows are 300 and 70 nt.
- DNABERT's genome pretraining, EDEN's own data beyond GUE, and CNNProm's
  Softberry server were not audited.
- The upstream source of the shared promoters (F-110) is not established.

## 6. References

- Ji, Y. et al. (2021). DNABERT: pre-trained bidirectional encoder
  representations from Transformers model for DNA-language in genome.
  *Bioinformatics* 37(15):2112–2120. doi:10.1093/bioinformatics/btab083
- Kapoor, S. and Narayanan, A. (2023). Leakage and the reproducibility crisis
  in machine-learning-based science. *Patterns* 4(9):100804.
  doi:10.1016/j.patter.2023.100804
- Su, W., Lyu, H., Lin, H. et al. (2025). iPro-MP. Study key `su2025ipro`
  in `configs/source_acquisition_v1.yaml`; not yet in `references.bib`.
- Zabihi et al. (2026). EDEN: multiscale expected density of nucleotide
  encoding for enhanced DNA sequence classification with hybrid deep learning.
  *BMC Bioinformatics* 27:40. doi:10.1186/s12859-026-06367-6
- Zhou, Z. et al. (2024). DNABERT-2: efficient foundation model and benchmark
  for multi-species genome. *ICLR 2024*. arXiv:2306.15006
