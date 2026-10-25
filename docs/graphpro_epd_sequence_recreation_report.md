# GraphPro Human and Mouse Sequence Recreation Audit

## Decision

The released GraphPro Human and Mouse sequences are completely reproducible
from the frozen EPDnewNC coordinates and UCSC assemblies. This resolves their
source construction, but does not make the released negative windows equivalent
to the predeclared GC-matched genomic-control condition. They are retained as a
separate downstream-control condition until their remaining integrity and
dependency gates are completed.

## Frozen inputs

| Organism | EPD source | Assembly | twoBit size | Published MD5 |
| --- | --- | --- | ---: | --- |
| Human | HsNC EPDnew v001 | GRCh38/hg38 | 835,393,456 | `dcc3ea27079aa6dc3f9deccd7275e0f8` |
| Mouse | MmNC EPDnew v001 | GRCm38/mm10 | 714,784,109 | `fcfcc276799031793a513e2e9c07adad` |

The source-recreation contract also freezes every EPD BED and released
GraphPro file by SHA-256. The assemblies were acquired and checked on
`bioserver04`; they and all generated ledgers remain unversioned data artifacts.

## Recreated construction rule

For an EPD TSS at transcript-oriented coordinate zero, every released positive
is the 81-nt interval $[-80,1)$ and every released negative is the interval
$[1000,1081)$. Minus-strand intervals are reverse-complemented after extraction.
The class embedded in each header agrees with its released file, but is treated
as construction metadata rather than independent biological evidence.

| Organism | Class | Released records | Exact assembly recreations | Mismatches |
| --- | --- | ---: | ---: | ---: |
| Human | Positive | 2,339 | 2,339 | 0 |
| Human | Negative | 2,339 | 2,339 | 0 |
| Mouse | Positive | 1,846 | 1,846 | 0 |
| Mouse | Negative | 1,846 | 1,846 | 0 |

All 8,370 records therefore have exact sequence, coordinate, strand, assembly,
and EPD-identifier provenance. Two independent executions produced byte-equal
ledgers, summaries, and manifests.

## Interpretation of the negative class

The result rejects the hypothesis that the Human/Mouse problem was caused by a
later preprocessing error or arbitrary label corruption. The negative class is
a deterministic downstream region associated with an EPD TSS. Such a region
may be a useful constructed control, but EPD does not annotate it as a verified
non-promoter and the policy does not match GC content. This explains why exact
recreation and biological class validity remain separate gates.

The subsequent formal treatment operates after the earlier exact-integrity
stage. At that point, another annotated coding or non-coding TSS occurs within
the frozen 100-nt margin of 73 Human and 40 Mouse controls; 21 and 11 of these,
respectively, directly contain the other TSS. Every exclusion is recorded in a
row-level ledger.

## Reproducibility and remaining work

The implementation is `scripts/audit_graphpro_epd_sequence_recreation.py`,
using the dependency-free random-access reader in
`src/capsprom/data/twobit.py`. The ignored output directory contains one row per
released record, the aggregate summary, and the hash-bound audit manifest.

The separate downstream-control treatment is described in
`docs/graphpro_epd_downstream_treatment_report.md`. The predeclared GC-matched
genomic controls remain the primary reconstruction condition; the historical
+1 kb controls are a distinct reproduction or sensitivity condition. No model
execution is enabled by either audit.
