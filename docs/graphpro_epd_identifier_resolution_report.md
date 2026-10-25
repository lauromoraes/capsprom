# GraphPro Human and Mouse EPD Identifier Resolution

## Scope and decision

This audit resolves identifiers only. It does not accept the released GraphPro
directory labels, reconstruct sequence windows, generate negative controls, or
enable model training. The frozen source is the November 2023 EPDnew FTP
snapshot archived as Zenodo DOI `10.5281/zenodo.10149386`. The four selected
BED files use GRCh38/hg38 for human and GRCm38/mm10 for mouse. Their local
copies are raw references, remain ignored by Git, and are verified against the
SHA-256 hashes in `configs/graphpro_epd_identifier_resolution_v1.yaml`.

EPD distributes these files under CC BY 4.0. The downloaded copyright notice
and its hash are recorded in the same contract.

## Results

| Organism | Released records per class | Shared identifiers across released classes | Union of identifiers | Resolved in EPDnewNC | Unresolved |
| --- | ---: | ---: | ---: | ---: | ---: |
| Human | 2,339 | 2,339 | 2,339 | 2,339 | 0 |
| Mouse | 1,846 | 1,116 | 2,576 | 2,576 | 0 |

The human identifier union equals the complete 2,339-record
`HsNC_EPDnew_001_hg38` collection. The mouse union is a 2,576-record subset of
the 3,077-record `MmNC_EPDnew_001_mm10` collection. One human identifier and
739 mouse identifiers also occur in the corresponding coding EPDnew BED files;
these alternative memberships are preserved in the row ledger, while the
non-coding collections remain primary because they resolve every identifier.

The class overlap is methodologically important. Every human EPD identifier is
attached to one sequence in each released class. In mouse, 1,116 identifiers
occur in both released classes and 730 occur only in each class. EPD membership
therefore identifies promoter/TSS candidates but cannot validate the released
negative label. The `FP` prefix and embedded header label are retained as
source metadata only.

A preliminary coordinate-convention check queried small hg38/mm10 intervals for
three human promoters (`PCAT1_1`, `FAM242E_1`, and `LINC00870_2`) and one mouse
promoter present in both released classes (`0610005C13Rik_1`). In both strand
orientations, every released positive was the 81-nt interval from -80 through
the TSS, while every paired released negative was the interval from +1000
through +1080 relative to the same TSS. A fifth mouse positive-only identifier
(`4930594M22Rik_1`) followed the same positive convention. This small audit is
strong evidence for a deterministic source construction rule, but it is not a
substitute for a complete, hash-bound recreation from local assembly files.

## Reproducibility

Run:

```bash
.venv/bin/python scripts/audit_graphpro_epd_identifiers.py \
  --config configs/graphpro_epd_identifier_resolution_v1.yaml \
  --output-dir outputs/reports/graphpro_epd_identifier_resolution_v1
```

The ignored output contains `identifier_resolution_ledger.csv`, one row per
released record with its EPD coordinate and alternative collection matches;
`identifier_resolution_summary.json`; and `audit_manifest.json` with the
configuration and output hashes. The writer refuses to overwrite an existing
audit directory and publishes the staged directory atomically.

## Remaining gates

Identifier resolution is complete, but Human and Mouse remain ineligible for
confirmatory use. The subsequent complete audit described in
`docs/graphpro_epd_sequence_recreation_report.md` recreated all 8,370 released
sequences from hash-verified hg38/mm10 assemblies. The next gate is a formal
TSS-proximity and integrity treatment of the historical downstream controls,
followed by a separate contract for the primary GC-matched controls. All
splits, dependency identities, and model results must then be regenerated for
the new dataset versions.
