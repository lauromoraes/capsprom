# GraphPro Primary-TSS Sample Audit

## Current state

The deterministic sample was materialized before any coordinate comparison.
Three primary supplements have now been acquired and hash-bound. Their 30
preselected rows all match the published one-based TSS position and strand
after the declared conversion from the zero-based, half-open BED point. The
exact Bacillus coordinate supplement is still unresolved. The nominal E. coli
subset has now been resolved, but it exposed an assembly error rather than
validating the MG1655 candidate. The five-source release gate therefore remains
closed and eligibility has not changed.

The five official Promotech BED files were downloaded from commit
`56251ad9b883ef831b4753fc623d5ec970fe65e0`. Their hashes exactly match
`configs/graphpro_source_registry_v1.yaml`. The frozen selector chose ten rows
per dataset, targeting five rows from each strand where available. The complete
50-row CSV has SHA-256
`751a9a757f0b0080dc9aa3778c3c94c87d057e6b74a49cacfe5754265d8c78f9`.

| Dataset | Promotech rows | Selected rows | Primary reference |
| --- | ---: | ---: | --- |
| *B. amyloliquefaciens* | 1,064 | 10 | PMID 26133043 |
| *C. jejuni* NCTC 11168 | 1,905 | 10 | PMID 23696746 |
| *C. pneumoniae* CWL029 | 530 | 10 | PMID 21989159 |
| *E. coli* MG1655 | 278 | 10 | PMID 27748404 |
| *L. interrogans* L495 | 2,865 | 10 | PMID 28154810 |

The ignored audit directory contains `selected_rows.csv` and
`audit_manifest.json`. Re-running the selector refuses to overwrite that
directory; a clean reproducibility run must use a different temporary output
path and compare hashes.

## Acceptance rule

Every sampled row must match the exact assembly version, strand, and TSS after
an explicitly documented source coordinate conversion. An unexplained one-base
offset is not accepted. A missing or ambiguous match fails the sampled dataset
and leaves it blocked; no row is relabeled or replaced.

Repeated records at one identical position and strand are annotation
multiplicity, not competing coordinate candidates. The ledger therefore keeps
both a binary coordinate-match count and the number and locations of source
records. This occurs where a TSS is associated with multiple annotations or
experimental conditions.

## Partial comparison results

| Dataset | Source table rows | Unique position/strand pairs | Sample matches | Result |
| --- | ---: | ---: | ---: | --- |
| *C. jejuni* NCTC 11168 | 2,466 | 1,905 | 10/10 | pass |
| *C. pneumoniae* CWL029 | 531 | 530 | 10/10 | pass |
| *L. interrogans* L495, 30/37 C | 56,135 | 45,562 | 10/10 | pass |
| *B. amyloliquefaciens* | -- | -- | 0/10 | blocked: exact supplement unavailable |
| Nominal *E. coli* MG1655 | 278 | 248 | 10/10 coordinates | fail: rows belong to pAA `NC_018666.1` |

The initial source contract is
`configs/graphpro_primary_tss_source_comparison_v1.yaml`; its v2 successor
records the E. coli identity failure. Generated, ignored
evidence is under
`outputs/reports/graphpro_primary_tss_source_comparison_v1/`: the row ledger,
summary, and hash manifest. The comparison is coordinate provenance evidence;
it does not validate labels, biological representativeness, or predictive
performance.

## Pending work

The E. coli source audit found exact ordered agreement for position, strand,
and locus in all 278 rows. All 278 published 51-nt windows match the pAA
reference, while none of the BED contig labels matches the required pAA
accession. Evidence is defined by
`configs/graphpro_ecoli_paa_source_audit_v1.yaml`. The nominal MG1655
reconstruction and every derivative are invalid; the source files themselves
remain preserved.

The remaining source task is to locate a coordinate-level Bacillus supplement
or document its unavailability through the publisher/author route. Separately,
the pAA source may be reconstructed only under a new identity and with fresh
controls, splits, dependencies, and hashes. No eligibility change or model run
is authorized yet.
