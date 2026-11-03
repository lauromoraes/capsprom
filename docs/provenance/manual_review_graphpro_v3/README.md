# Manual sample review of graphpro-reconstructed-v3

Eligibility gate 7 of `specs/graphpro_dataset_reconstruction.md` requires an
independent manual audit before a reconstructed organism is reinstated. The
sample is frozen by `configs/graphpro_v3_manual_review_v1.yaml` and written by
`scripts/prepare_graphpro_v3_manual_review.py`: 20 positive–control pairs per
organism (10 per strand, lowest SHA-256 rank of the pair id), 60 rows in
`review_sheet.csv`. The selection did not look at any check result.

## How to review

Check each row against the primary sources, not against the build outputs.
Fill each check column with `yes` or `no` (and `reviewer_notes` for every
`no`). `E_cds_control` is `n/a` for *L. interrogans*, which has no CDS panel.

| Column | What to check | Where |
| --- | --- | --- |
| `A_positive_in_primary_table` | `tss_one_based` and `strand` appear in the primary table, and the row's class set contains primary or secondary | The supplementary table named in `primary_source` (sorted by position) |
| `B_positive_sequence` | `positive_sequence` equals the sequence at `positive_ncbi` (the link already applies the strand) | NCBI nuccore FASTA link |
| `C_control_sequence_and_strand` | `control_sequence` equals the sequence at `control_ncbi`, on the same strand as the positive | NCBI nuccore FASTA link |
| `D_control_tss_margin` | No TSS of any class in the primary table lies within 100 nt of `control_start_one_based`..`control_end_one_based`, on either strand | Primary table, both temperature sheets for *L. interrogans* |
| `E_cds_control` | The CDS control lies inside the CDS `cds_control_cds_id`, on its sense strand, at least 60 nt from its start and stop | NCBI graphics or the RefSeq record of the assembly |

## Decision rule

A row passes when every applicable check is `yes`. An organism passes when all
20 of its rows pass. Any `no` keeps that organism blocked: the row is reported
in a new finding and nothing is relabeled. After the review, record the date
and the per-organism result in the research log; the filled sheet is committed
as the review record.
