# Manual sample review of the CNNProm E. coli genomic pilot

Gate `manual_sample_audit` of `configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml`
requires an independent manual audit before the panel can enter an
eligibility manifest. The sample is frozen by
`configs/cnnprom_ecoli_genomic_pilot_manual_review_v1.yaml` and written by
`scripts/prepare_cnnprom_ecoli_genomic_pilot_manual_review.py` from the build
with manifest SHA-256 `31fda2c7…`. `review_sheet.csv` has 25 rows:

- 5 `forced` rows, the contract's observed cases (rrsAp2 and gltIp1,
  multiple loci resolved; serWp and rplUp, near; araCp, shifted);
- 20 `random` rows, 10 per strand, with the lowest SHA-256 rank of the record id.

The selection did not look at any check result or model output.

## How to review

Check each row against the primary sources, not against the build outputs.
Fill each check column with `yes` or `no`, and write `reviewer_notes` for
every `no`. Coordinates are one-based on NC_000913.3.

| Column | What to check | Where |
| --- | --- | --- |
| `A_positive_tss_in_regulondb` | The RegulonDB promoter `regulondb_promoter_id` has the name in `promoter`, the strand in `strand`, and its TSS at `tss_one_based`. For `near` and `shifted` rows the RegulonDB TSS is instead `support_distance_nt` away (negative means upstream in transcription direction); for multi-locus rows the TSS matches the resolved locus | RegulonDB web: search the gene (the promoter name without its `p…` suffix) and open the promoter in the gene or operon page; or the acquired PromoterSet, `data/acquired/regulondb_tss_acquisition_v1/files/PromoterSet.json`, searched for the id |
| `B_positive_sequence` | `positive_sequence` equals the sequence at `positive_ncbi` (the link already applies the strand) | NCBI nuccore FASTA link |
| `C_control_sequence_and_strand` | `control_sequence` equals the sequence at `control_ncbi`, on the positive's strand, and has the same G+C count as `positive_sequence` | NCBI nuccore FASTA link |
| `D_control_tss_margin` | No RegulonDB TSS of any evidence lies within 100 nt of `control_start_one_based`..`control_end_one_based`, on either strand | RegulonDB genome browser around the control interval |

## Decision rule

A row passes when every check is `yes`. The panel passes when all 25 rows
pass. Any `no` keeps the panel blocked: the row is reported in a new finding
and nothing is relabeled. After the review, record the date and the result in
the research log; the filled sheet is committed as the review record.
