# GraphPro Candidate Distribution and Dependency Audit

## Scope

This release-gate audit covers six independently reconstructed bacterial
candidates and two exploratory released-data integrity views for Human and
Mouse. Distribution comparisons use the treated populations. The dependency
audit additionally includes all 18 datasets in the active CDBProm/CNNProm
confirmatory scope. No test outcome, model prediction, or effectiveness metric
is used.

## GC-distribution results

The table reports the positive-minus-negative difference in mean GC fraction,
the two-sample Kolmogorov--Smirnov statistic, its Holm-adjusted p-value across
the eight datasets, and the largest class-frequency total-variation distance at
one aligned position. Statistical detection is not equivalent to a large or
biologically meaningful effect, particularly at large sample sizes.

| Dataset | Mean GC difference | KS statistic | Holm-adjusted p | Maximum positional TV (position) |
| --- | ---: | ---: | ---: | ---: |
| BACILLUS | -0.0158 | 0.089 | 0.00122 | 0.182 (+3) |
| CJEJUNI_2 | -0.0157 | 0.115 | 1.55e-10 | 0.250 (-8) |
| CPNEUMONIAE | -0.0200 | 0.157 | 1.70e-5 | 0.284 (-35) |
| ECOLI | +0.0031 | 0.044 | 0.968 | 0.113 (-57) |
| LINTERROGANS | -0.0051 | 0.049 | 0.00470 | 0.226 (0) |
| RHODOBACTER_1 | -0.0078 | 0.058 | 2.01e-7 | 0.174 (+1) |
| Human released integrity view | +0.1096 | 0.298 | 3.27e-91 | 0.399 (+20 nominal) |
| Mouse released integrity view | +0.1038 | 0.328 | 2.16e-87 | 0.352 (+19 nominal) |

Every reconstructed bacterial positive--control pair respects the frozen
maximum absolute GC difference of four bases in 81 nt (0.04938). Mean absolute
pair differences range from 0.0254 to 0.0295. Nevertheless, five of six
bacterial aggregate class distributions remain detectably shifted, generally
toward slightly greater GC content in the sampled controls. The pair-level
constraint therefore passed exactly as specified, while the aggregate
distribution gate identifies residual structure that should be addressed by a
predeclared sensitivity condition rather than hidden.

Human and Mouse have much larger released-class differences, approximately
11.0 and 10.4 percentage points respectively. Because these identities are not
EPD-resolved reconstructions, this is evidence of a possible construction
shortcut, not evidence that either released class is biologically correct.
Their largest positional differences occur at the unverified terminal portion
of the nominal alignment.

## Cross-dataset dependencies

The dependency audit canonicalizes every sequence as the lexicographically
smaller forward or reverse-complement string. Across 26 identities it finds
nine overlapping pairs, five involving a GraphPro-derived candidate or
integrity view:

| Candidate/view | Related dataset | Same-label | Opposite-label | Interpretation |
| --- | --- | ---: | ---: | --- |
| reconstructed BACILLUS | CDBProm *B. amyloliquefaciens* | 2 | 0 | Shared positive lineage to verify |
| reconstructed CPNEUMONIAE | CDBProm *C. pneumoniae* | 404 | 0 | Strong source-pool dependence |
| reconstructed ECOLI | CNNProm E. coli | 0 | 6 | CNNProm negatives match reconstructed positives |
| Mouse integrity view | CNNProm mouse non-TATA | 0 | 1 | CNNProm positive matches released-view negative |
| Human integrity view | Mouse integrity view | 1 | 0 | Shared mammalian positive |

The six E. coli disagreements block that candidate's reinstatement until the
source lineage and label semantics of both resources are reviewed. The 404
Chlamydophila shared positives do not create an internal contradiction, but
they preclude treating the two datasets as independent experimental effects.
If reinstated, they must occupy the same dependency cluster. No observed exact
or reverse-complement cross-dataset overlap was found for CJEJUNI_2,
LINTERROGANS, or RHODOBACTER_1; exact non-overlap does not prove independence.

## Reproducibility and decision

The immutable audit contract is `configs/graphpro_candidate_audit_v1.yaml`.
Machine-readable outputs are stored under
`outputs/reports/graphpro_candidate_audit_v1/`, and the reviewed candidate
relationships are frozen in
`configs/graphpro_candidate_dependency_manifest_v1.yaml`. The audit performs
two-sided Mann--Whitney and Kolmogorov--Smirnov GC comparisons, corrects each
eight-test family with Holm's method, and records per-class quantiles and
pair-level GC differences.

This work does not change the active 18-dataset confirmatory manifest. It opens
no training gate and removes or relabels no candidate because of an external
disagreement. Remaining release work comprises primary-source sample review,
source/license archival, negative-control sensitivity design, manual sample
audit, and EPD/assembly resolution for Human and Mouse.
