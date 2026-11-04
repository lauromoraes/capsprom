# CDBProm and CNNProm Genomic-Control Feasibility (2026-11-04)

Updates `docs/control_coordinate_feasibility_inventory.md`, which predates
reference coordinate mapping v1 to v3. Source-only: no control was generated,
no partition changed, and no model output was read. Log R-061, findings F-127
to F-130.

## What a genomic control needs

Under `specs/graphpro_dataset_reconstruction.md` (negative-set rules) each
dataset needs: (a) the exact assembly; (b) a locus and strand per positive;
(c) the TSS position inside the window; (d) the **complete** primary TSS table
of the organism as the exclusion set (100 nt, both strands). Using only the
positives as exclusion repeats the *L. interrogans* v2 defect (F-116).

## Step 1: acceptance of mapping v3

`scripts/audit_mapping_acceptance.py` with
`configs/reference_coordinate_mapping_v3_acceptance_v1.yaml` reads the persisted
v3 tables; summary in
`manifests/provenance/reference_coordinate_mapping_v3/acceptance_v1.json`.

| Criterion | Result |
| --- | --- |
| 1 Coverage | every canonical record has one row; no duplicate record id, no orphan locus |
| 2 Consistency | 0 violations in 13 collections (`n_candidates` = locus rows; `verified` single; `ambiguous` ≥ 2) |
| 3 Round trip | enforced for every verified locus by the runner, which fails on mismatch (`coordinate_mapping.py`) |
| B1 declared coordinates | CNNProm *E. coli*: all 3,811 verified records match the F-098 rule (837 positives, strand agreeing in all; 2,974 negatives). Exploratory probe: all 1,000 CNNProm *B. subtilis* negatives equal plus-strand start + 60. CDBProm rows carry no coordinates, so B1 does not apply |
| B3 alignment fallback | 0 input records: v3 has no unmapped strict-DNA record |
| 7 R-011 comparison | cannot be made (F-093); **owner decision required** |
| 8 Manual sample audit | sheet frozen (83 rows, 2 per collection × status × label, lowest SHA-256 of `record_id`): `docs/provenance/manual_review_mapping_v3/review_sheet.csv`; **review pending** |

Mapping v3 can be accepted once criteria 7 and 8 are closed. Criteria 4 to 6
rest on the existing fixtures in `tests/test_exact_mapping.py` and
`tests/test_coordinate_mapping.py`.

## Step 2: TSS position and exclusion sources per dataset

| Dataset | (b) locus | (c) TSS in window | (d) complete TSS table | Status |
| --- | --- | --- | --- | --- |
| CNNProm *E. coli* | 3,811/3,839 | declared (F-098, B1 passed) | candidate: Thomason et al. 2015 dRNA-seq (14,868 TSS, MG1655, doi:10.1128/JB.02096-14) plus RegulonDB TSS sets; both on NC_000913.3, so a lift from NC_000913.2 is needed | **most feasible pilot** |
| CNNProm *B. subtilis* | 1,373/1,373 | positives: gene names only; negatives declared | candidate: Nicolas et al. 2012 (*Science* 335:1103; GEO GSE27219) | feasible after TSS verification of positives |
| CDBProm *C. pneumoniae* | 807/808 | offset inferred from the released matrix, not declared (F-018) | primary table already acquired for GraphPro v3 | feasible; shares cluster `cdbprom-chlamydophila` with GraphPro Cpne v3 |
| CDBProm *B. amyloliquefaciens*, *K. pneumoniae*, *S. coelicolor*, *Synechocystis* | ≥ 98% | as above | article references 24–28; not acquired | pending acquisition |
| CDBProm *C. glutamicum*, *H. pylori*, *M. tuberculosis*, *P. aeruginosa* | ≥ 98% (earlier strain sequences, F-096) | as above | listed as unpublished in the article; a published map would have to be found and lifted to the earlier sequence | weak |
| CDBProm *Anabaena*, *S. Typhimurium* | 0 verified (`assembly_conflicting`, F-104) | — | — | blocked by assembly decision |
| CNNProm Human/Mouse non-TATA, Mouse TATA, *Arabidopsis* TATA/non-TATA | not mapped | EPD identifiers unresolved | EPDnew would supply (d) | needs a dated EPD resolution first |

## Consequence for the native × genomic matrix

CNNProm native negatives are opposite-strand coding fragments
(`negative_opposite_strand_cds` in every bacterial record), so for CNNProm the
contrast native versus genomic is in effect coding versus genome background.
The realistic first set is CNNProm *E. coli*, then *B. subtilis* and CDBProm
*C. pneumoniae*. Three datasets in at most three dependency clusters keep the
matrix descriptive.

## Next actions (each a separate authorization)

1. Owner: decide criterion 7 and fill the manual sample sheet.
2. Acquire and hash the *E. coli* TSS tables; freeze an NC_000913.2 to
   NC_000913.3 coordinate lift; count non-overlapping free capacity (F-123
   lesson) before freezing a pilot contract.
3. Verify the CDBProm TSS offset per organism against its primary table.

## Update (log R-062)

- Criterion 7 is tested against the R-028 pilot (owner decision): reproduced
  within one record (F-131). Mapping v3 acceptance now waits only for the
  manual sample (criterion 8).
- *E. coli* exclusion set acquired: RegulonDB 14.0 union of 16 HT TSS datasets
  and PromoterSet, 34,800 TSS on NC_000913.3 (F-132). Positives were placed on
  NC_000913.3 by exact search, so no coordinate lift is needed; 834 of 837 lie
  on a RegulonDB TSS.
- Capacity: 22,174 disjoint free slots for 837 positives, none without a GC
  candidate (F-133). CNNProm *E. coli* is feasible as the genomic-control pilot.
