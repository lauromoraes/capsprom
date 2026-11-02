# Dataset Eligibility for Experiments

This document explains when a dataset may be used in CapsProm experiments, the
criteria behind that decision, and the order in which the pipeline checks,
changes, or removes records. It summarizes rules that are defined elsewhere and
does not add new ones:

| Topic | Source of the rule |
| --- | --- |
| Exact-integrity rules and length exclusion | `specs/dataset_integrity_audit.md` |
| Source label semantics and the GraphPro decision | `docs/source_label_semantics_audit.md`, dataset eligibility manifest in `configs/` |
| Released and reconstructed data conditions | `specs/dataset_condition_policy.md` |
| Reconstruction of GraphPro | `specs/graphpro_dataset_reconstruction.md` |
| Similarity grouping across partitions | `specs/homology_grouping_protocol.md` |
| Dependence between datasets | dataset dependency manifest in `configs/`; `docs/dataset_dependency_audit.md` |
| External training resources | `docs/external_resource_leakage_finding.md` |

## 1. What "eligible" means

A dataset is **eligible** when it may enter **confirmatory** experiments. These
are the model comparisons and cross-dataset statistical tests that support the
thesis conclusions. Eligibility is decided per dataset (one train/test pair for
one source and organism), not per record.

Two other uses do not require eligibility:

- **Exploratory use.** Pipeline development, diagnostics and the study of a
  data problem. Results are kept as provenance and are never cited as
  biological evidence. The eight released GraphPro datasets are in this group.
- **Reproduction of a published baseline.** Running a study's own protocol on
  its own data, to compare with the number the study reported.

Eligibility always refers to one **data condition**
(`specs/dataset_condition_policy.md`):

| Condition | Data | Question it answers |
| --- | --- | --- |
| Released, filtered | The files distributed by the source study. Records may be removed by declared rules, but no sequence or label is changed. | What does the published benchmark support? |
| Reconstructed | Records rebuilt from verified references: genome assemblies, dated TSS annotations, primary coordinate tables, and a declared rule for building negatives. | What holds when the examples are rebuilt independently of the released files? |

A dataset eligible in one condition is not thereby eligible in the other. A
reconstructed dataset gets its own identity and is never pooled with the
released one.

**Current state.**

- **Released, filtered condition:** 18 datasets are eligible, 11 from CDBProm
  and 7 from CNNProm. The eight released GraphPro datasets are excluded.
- **Reconstructed condition:** no dataset is eligible. The six bacterial
  GraphPro reconstructions are candidates, and their model-training and
  confirmatory-use gates are closed.
- **Bhandari:** not covered by the eligibility decision. Its promoter-only
  source and synthetic negatives are handled under separate specifications.

**Gap.** The condition policy is a design: its condition labels and per-build
ledgers have not yet been applied to any build. The 18 eligible datasets come
from the earlier canonical build. In substance they are released data with
filtering, but they are not yet formally labelled with that condition.

## 2. Status of a dataset

| Status | Meaning |
| --- | --- |
| Eligible | Every criterion verified so far has passed. Criteria still open on an eligible dataset are listed in §3 and do not count as passed. |
| Excluded | A verified criterion failed. The dataset is kept unchanged for provenance. It may return only as a new reconstructed dataset with its own identity, never by repairing labels in place. |
| Pending | Evidence for at least one required criterion does not exist yet. A pending dataset is neither approved nor excluded. |

Two rules hold for every status:

- No label is ever changed on the basis of sequence content, strand, agreement
  with another study, or model output.
- Neither model performance nor test-set outcomes may influence eligibility.

## 3. Criteria

In the "Verification" column, **Done** means the check was run and its result
is recorded. **Defined, not applied** means the rule exists but has not been
run on the eligible build. **Pending** means the evidence does not exist yet.

### 3.1 Released, filtered condition

| Criterion | Justification | Verification | Consequence for use |
| --- | --- | --- | --- |
| **E1. Pair contract.** Exactly one train and one test file per dataset, both classes in both partitions, valid CSV, labels 0/1. | Without both classes in both partitions, training and evaluation are undefined. | **Done** for the 26 released pairs: all pass (integrity audit). | A failing pair is `invalid` and cannot be used. |
| **E2. DNA alphabet.** Sequences contain only A, C, G, T. | The encoders are defined for these four bases only. | **Done**: 8 records removed before splitting. | Removal of records (§4, step 7). |
| **E3. No cross-label collisions.** No identical sequence may carry both labels. | Identical inputs with opposite targets are irreducible label noise. Keeping one side would be an unsupported relabeling. | **Done**: 2,696 records removed, every occurrence on both sides. The audit finds zero conflicts in all 26 pairs. | Removal of records (§4, step 5). A dataset whose remaining labels are still doubtful is judged by E6. |
| **E4. No exact duplicates within a class.** | Duplicates weight some examples twice and could fall on both sides of the split. | **Done**: 1,060 records removed, keeping the first occurrence. The audit finds zero duplicates. | Removal of records (§4, step 6). |
| **E5. No exact train/test overlap.** | An identical sequence in train and test measures memorization, not generalization. | **Done**: zero overlap in all 26 pairs. | A pair with overlap is `train_test_overlap` and cannot be used. |
| **E6. Source label semantics.** For both classes, the source must document how the class was built, so that "positive" means promoter and "negative" means non-promoter. | Exact cleaning cannot show that a label has its intended biological meaning. | **Done.** CDBProm: the publication documents the curated promoter inputs and negatives sampled downstream of the promoters. CNNProm: the distributed documentation describes both classes. GraphPro fails (see the row below). | CDBProm and CNNProm are retained. GraphPro is **excluded**. |
| GraphPro detail for E6 | — | Five bacterial sets: the class is perfectly determined by the FASTA strand symbol. *E. coli*: 1,345 records appear identically in both classes. *B. amyloliquefaciens*: 535 negatives are CDBProm promoter windows. Human and mouse: no independent evidence on how the negatives were built; all records carry EPD promoter identifiers. | All eight are **excluded** from confirmatory use and kept as exploratory provenance. |
| **E7. Organism identity by accession.** The organism must be confirmed from accessions and record headers, not from file or folder names. | A wrong organism invalidates cross-dataset and cross-study comparisons. | **Done for GraphPro**: the `Cpne` folder was *C. pneumoniae*, previously mapped to *Clostridium phytofermentans*. **No recorded check** for the 18 eligible datasets. | GraphPro *C. pneumoniae*: corrected, but the dataset stays excluded (E6). Eligible datasets: open gap. |
| **E8. Length matches the declared window.** A record whose length differs from its source's declared length is excluded, never cropped or padded. | Its anchor (the TSS for promoters, the sampling rule for negatives) is then unknown. | **Defined, not applied.** The eligible build kept the most common length instead. Known deviations include 51 CDBProm negatives of 99 nt. | A future build must apply the rule. Until then, this criterion is open for the eligible datasets. |
| **E9. Documented crop anchor.** The crop index must come from the source or be verified against a reference. | An undocumented index may misplace the TSS in the window. | **Pending for CDBProm positives**: TSS index 500 is undocumented (F-018). CNNProm windows are native. | CDBProm stays eligible. Its comparability with published results is at most *qualified* until the index is verified. |
| **E10. No near-duplicate dependence across partitions.** Records that align above a threshold must stay in the same partition. | Shifted windows and repeat copies leak across an exact-identity split: up to 67% of test negatives in CNNProm Human non-TATA (F-084). | **Defined, not applied.** The current split groups only exact sequences. | Results on the current split may be optimistic for affected datasets (F-084 to F-088). Binding only after the evaluation protocol adopts the grouping. |
| **E11. Dependence between datasets.** Datasets sharing a source pool or many similar records form one dependency cluster. | Cross-dataset tests assume independent units. Dependent datasets counted twice inflate significance. | **Done**: exact overlap gives 14 clusters; alignment overlap gives 12 (F-114). | No records change. Results are aggregated per cluster before inference, and at least 10 clusters are required. The protocol in force still uses the exact-overlap clusters; the alignment rule is defined but not adopted. |
| **E12. External training resources.** A released, pretrained baseline must not have seen the test set. | A model trained on test records measures recall, not prediction. | **Done** for iPro-MP and GUE: up to 100% of the test positives in five bacterial sets (F-108, F-109). | Dataset eligibility is unchanged. Released weights of those baselines are not evaluated on the affected test sets; the baselines are trained from scratch on our partitions. |

### 3.2 Reconstructed condition

The criteria are those of the released condition plus the reinstatement
requirements of the eligibility manifest. Reinstatement is decided per
organism. The six bacterial GraphPro candidates are the only reconstructed
datasets so far.

| Criterion | Justification | Verification | Consequence for use |
| --- | --- | --- | --- |
| **R1. Source-supported class construction.** Positives come from verified TSS sources; negatives from a declared genomic rule. | Replaces the class semantics that the released files could not support (E6). | **Pending**: samples of the primary TSS sources and an independent manual review. Human and mouse also need dated EPD resolution. | Until it passes, the candidate cannot be used for training or confirmatory work. |
| **R2. Labels independent of strand.** | The released defect was class = strand. | Part of R1; **pending**. | As R1. |
| **R3. Organism verified by accession.** | As E7. | Recorded in the reconstruction contract; part of the pending manual review. | As R1. |
| **R4. New immutable build** with hashes, a filtering ledger, and a comparison with the released records. | Keeps the reconstructed data separate from, and traceable to, the released data. | **Done** for the six bacterial candidates: a clean second build reproduced every file byte for byte. | Required before any use. |
| **R5. Exact integrity repeated** (E1 to E5). | Same reasons as E1 to E5. | **Done** for the six bacterial candidates. | As E1 to E5. |
| **R6. Similarity-safe split.** Each positive and its control stay together. Pairs within Hamming distance 8, either orientation, form one group that is never split. | As E10. The reconstructed split applies this rule from the start. | **Done**: zero shared pairs or groups, zero exact or reverse-complement identities, and zero neighbours at distances 1 to 8 between train and test. | This gate is closed (passed). |
| **R7. Distribution diagnostics, cross-dataset dependence, licensing and archival.** | GC or length artefacts could separate the classes trivially; dependence and licensing affect inference and release. | **Pending**. | The candidates remain **pending**: neither eligible nor excluded. |

### 3.3 Differences between the two conditions

| Aspect | Released, filtered | Reconstructed |
| --- | --- | --- |
| Allowed changes | Removal of whole records by a declared rule; metadata corrections; deterministic transformations such as cropping. | New records from references, new labels, new negatives. |
| Source of label validity | The source study's documentation (E6). | Independent evidence: TSS sources, genome coordinates, the negative rule (R1). |
| Partition rule today | Exact-sequence groups. Similarity grouping is defined but not applied. | Similarity groups from the start (R6). |
| Comparability with published results | Possible with the study's own protocol, either direct or *qualified*. | Not comparable, by definition. |
| Identity | The released collection identifier. | A new identifier. Never pooled with released data. |

## 4. Processing stages in order

Each stage is either a **diagnostic** (records are measured; nothing is
changed, and a failure stops the pipeline or feeds a decision) or an
**intervention** (records are transformed or removed). The counts are for the
26 released pairs of the canonical build: 11 CDBProm, 7 CNNProm and 8 GraphPro.

| # | Stage | Type | Purpose | What is checked or changed | Rule | Effect on records |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | Acquisition | Diagnostic | Prove the files are the published ones. | Every file against its declared digests. | A digest mismatch deletes the file and fails the run. | None. |
| 2 | Canonicalization | Diagnostic and format conversion | One table format per collection, without changing content. | Per-class record counts against the release; sequence parity with the legacy files. | Every collection must pass, or the pipeline stops. | None removed. Sequences and labels unchanged. |
| 3 | Class mapping | Intervention (labelling) | Assign 1/0 to each record. | The label is taken from the source's class file or folder name. | Literal mapping only. Nothing is inferred from sequence or strand. | Each record gets the source's label. |
| 4 | Crop to the 81-nt window | Intervention (transformation) | Common input length: 60 nt upstream, the TSS, 20 nt downstream. | Sequence is cut at a source-specific TSS index and upper-cased. | Fixed index per source and length (for example 500 for CDBProm 1,001-nt positives; see E9). | Sequences shortened. Two CDBProm collisions are created by cropping. |
| 5 | Cross-label collision removal | Intervention (removal) | Remove contradictory inputs. | Sequences present in both classes. | Remove every occurrence from both classes. | −2,696 records (1,348 per class). |
| 6 | Within-class deduplication | Intervention (removal) | One copy per sequence. | Identical sequences within a class. | Keep the first occurrence. | −1,060 records (301 positive, 759 negative). |
| 7 | Strict-DNA filter | Intervention (removal) | Valid alphabet. | Characters other than A, C, G, T. | Remove the record. | −8 records (6 positive, 2 negative). |
| 8 | Train/test split | Intervention (assignment) | A fixed test partition. | Each class is shuffled with a seed derived from the dataset identity. | 20% of each class goes to test. Groups are exact sequences, which are unique after steps 5 and 6. | No removal. Final split: 143,946 train and 35,991 test records. |
| 9 | Integrity audit | Diagnostic | Confirm E1 to E5 on the written files. | Duplicates, label conflicts, train/test overlap, class presence. | Any finding makes the pair non-eligible. | None. Result: zero findings in all 26 pairs. |
| 10 | Source label semantics audit | Diagnostic, leading to a dataset decision | Check E6 and E7 against the raw sources. | Class construction, strand per class, identifiers, accessions. | Datasets without a supported meaning for both classes are excluded; labels are never repaired. | No records changed. Eight GraphPro datasets excluded as whole datasets. |
| 11 | Dependency clustering | Diagnostic, feeding inference | Check E11. | Shared sources and exact or alignment overlap between datasets. | Clusters are the units of statistical inference. | No records changed. |
| 12 | External resource audit | Diagnostic | Check E12 for pretrained baselines. | Alignment of each test set against each baseline's training data. | Released weights are not evaluated on affected test sets. | No records changed. |

Stages defined but not yet in the eligible build:

- **Length exclusion (E8).** Placed after canonicalization, before cropping. It
  removes whole records whose length differs from the declared one and lists
  every excluded record with its reason.
- **Similarity grouping (E10).** Placed between the strict-DNA filter and the
  split. It removes nothing: it only forces similar records into the same
  partition and the same inner fold.

The reconstructed condition replaces stages 2 to 4 with re-extraction from
references and a declared negative rule, and applies the similarity-safe split
(R6). Stages 5 to 9 are repeated on the new build.

## 5. Open gaps

| Gap | Affects | What would close it |
| --- | --- | --- |
| Condition labels and ledgers not yet applied to any build | All datasets | A build that follows the condition policy. |
| No recorded organism-by-accession check | 18 eligible datasets | An accession audit like the one done for GraphPro (E7). |
| Length rule not applied | CDBProm negatives (99 nt), others listed in the integrity spec | A build with length exclusion (E8). |
| CDBProm TSS index undocumented | 11 CDBProm datasets | Verification of the index against reference coordinates (E9). |
| Near-duplicate dependence across partitions | Mainly CNNProm Human and Mouse | Adoption of similarity grouping by the evaluation protocol (E10). |
| Reconstruction gates R1 and R7 | Six GraphPro candidates; GraphPro human and mouse | The pending audits in §3.2. |
| Bhandari outside this decision | Bhandari collections | An eligibility decision under its own specifications. |
