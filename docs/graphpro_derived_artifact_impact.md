# GraphPro Derived-Artifact Impact Assessment

## Decision

The new Human and Mouse products are exploratory released-data integrity views,
not independently reconstructed datasets. They therefore receive the distinct
identity `graphpro-released-eukaryotic-integrity-v1`. They do not replace the
raw files, do not alter the active 18-dataset confirmatory scope, and do not
authorize model execution.

## Artifact status

| Artifact family | Status after this work | Required action |
| --- | --- | --- |
| Released GraphPro raw files | Preserved and authoritative for source audit | None |
| Canonical-v3 released GraphPro CSVs | Historical exploratory provenance | Do not reinterpret as reconstructed data |
| Historical GraphPro model runs | Valid only for their recorded released/canonical-v3 hashes | Do not reuse for new identities |
| Bacterial reconstructed v1 | Superseded integrity candidate; preserved | Use only for before-treatment audit |
| Bacterial reconstructed v2 | Superseded mixed candidate: nominal E. coli is invalid | Do not reuse its E. coli sequences, controls, split, distribution, or dependency results |
| Nominal reconstructed E. coli MG1655 | Invalid: pAA coordinates were applied to chromosome `NC_000913.3` | Preserve for audit only; reconstruct from `NC_018666.1` under a new identity |
| Bacterial reconstructed split v1 | Still valid; source data did not change | No regeneration required |
| Human/Mouse integrity v1 FASTAs | Exploratory integrity view; EPD identifiers resolved and sequences recreated | Preserve as the input provenance view; do not train from it |
| Human/Mouse downstream treated v1 | Historical +1 kb control candidate with TSS exclusions; distribution/dependency audit completed | Keep exploratory and unsplit; resolve the Mouse/CNNProm conflict and report separately from future GC-matched controls |
| Human/Mouse downstream treated v2 | Successor excluding the single Mouse control matching an active external positive | Current historical-control candidate; keep exploratory and unsplit because residual GC structure remains |
| Human/Mouse canonical-v3 splits | Not reusable for integrity-v1 or future reconstruction | Generate a new split only after reconstruction gates pass |
| Dataset-logo audit v1 | Superseded presentation artifact | Preserve; it overstates the eukaryotic nominal TSS label |
| Dataset-logo audit v2 | Current descriptive logo artifact | Use for the standalone report |
| Eligibility/dependency manifests | Confirmatory scope remains 18 CDBProm/CNNProm datasets | Create a new version only after per-organism reinstatement |

## Consequences

The Human and Mouse removal ledger closes only the exact-integrity bookkeeping
for the released files. The subsequent EPD audit resolves every source
identifier and coordinate, and exact assembly recreation confirms the historical
windowing rule, but neither result establishes biological non-promoter status for
the downstream controls. The treated candidates have no remaining exact
integrity or TSS-margin violations; nevertheless, strong residual GC structure
and a Mouse/CNNProm opposite-label identity keep them outside confirmatory use.
A future primary reconstruction will create GC-matched genomic controls, new
hashes, a new grouped split, and new dependency and eligibility manifests.
Existing released-data predictions cannot be migrated or pooled with that future
resource.

The E. coli source audit adds a distinct invalidation. All 278 ordered BED rows
match the pAA Supplementary Dataset S1 in position, strand, and locus, and all
278 published 51-nt windows match plasmid `NC_018666.1`. The BED nevertheless
labels every row `NC_000913.3`. Thus the nominal MG1655 positive windows are
sequences from unrelated chromosome coordinates, and their paired genomic
controls, grouped split, GC summaries, similarity components, cross-dataset
overlaps, and any predictions are not transferable. This is an assembly/source
identity failure, not a label collision that can be corrected by row removal.
