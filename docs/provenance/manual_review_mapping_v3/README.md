# Manual sample audit of reference coordinate mapping v3

Criterion 8 of `specs/reference_coordinate_mapping_protocol.md`. The sheet was
drawn by `scripts/audit_mapping_acceptance.py` before inspection: two records
per collection, status, and label, lowest SHA-256 of `record_id` (83 rows,
SHA-256 `ad8942ca…`, log R-061).

For each row, fill:

- `check_locus_in_ncbi`: `yes`/`no`/`n/a` — the sequence at `contig_accession`
  `[start, end)` on `strand` (0-based half-open; reverse complement on `-`)
  in NCBI equals the record (`n/a` when the row has no single locus).
- `check_assembly_matches_source`: `yes`/`no` — the assembly is the one the
  source publication declares, or the documented substitute (F-096, F-098,
  F-103, F-104).
- `reviewer_notes`: free text for any `no`.

Do not edit the other columns.
