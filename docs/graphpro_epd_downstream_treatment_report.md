# GraphPro EPD Downstream-Control Treatment

## Scope

This treatment applies only to the historical Human and Mouse control condition
located 1 kb downstream of an EPD TSS. It consumes the earlier exact-integrity
view, adds strand-invariant duplicate/collision handling, and excludes negative
windows whose interval plus the frozen 100-nt margin contains any TSS from the
union of the coding and non-coding EPDnew collections. It does not generate the
primary GC-matched control condition and does not enable model training.

The Mouse source files do not define a complete one-to-one positive--control
pairing: many EPD identifiers occur in only one class. The treatment therefore
removes only an invalid downstream control. It does not delete an independently
valid promoter merely to impose balance. Records sharing an EPD identifier are
retained as an indivisible group for future partitioning.

## Counts by stage

| Organism | Integrity-view positive | Integrity-view negative | RC removals positive | TSS removals negative | Final positive | Final negative |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Human | 2,331 | 2,334 | 1 | 73 | 2,330 | 2,261 |
| Mouse | 1,843 | 1,845 | 0 | 40 | 1,843 | 1,805 |

Of the 73 Human TSS exclusions, 21 controls directly contain another annotated
TSS and 52 are affected only by the 100-nt margin. For Mouse, the corresponding
counts are 11 and 29. The Human strand-invariant removal is one within-positive
reverse-complement duplicate. No reverse-complement collision occurs across
classes.

The final class-count differences are 69 Human records and 38 Mouse records.
No compensatory downsampling or synthetic balancing was applied. Such an action
would be a separate experimental choice rather than an integrity correction.

## Final integrity and grouping

Both treated populations have zero within-class strand-invariant duplicates,
zero cross-label exact/reverse-complement collisions, and zero remaining known
TSS-margin violations. Human has 2,254 EPD identifier groups shared between
classes, 76 positive-only groups, and seven negative-only groups. Mouse has
1,086 shared, 757 positive-only, and 719 negative-only groups. These identifiers
must be indivisible during any future split.

## Reproducibility

The immutable contract is
`configs/graphpro_epd_downstream_treatment_v1.yaml`. Run:

```bash
.venv/bin/python scripts/build_graphpro_epd_downstream_treatment.py \
  --config configs/graphpro_epd_downstream_treatment_v1.yaml \
  --output-dir data/interim/graphpro_epd_downstream_treated_v1
```

The builder validates every input hash, refuses overwrite, stages all outputs,
and publishes the directory atomically. A clean rebuild reproduced the FASTAs
and exclusion ledger byte for byte. The ledger records the source identifier,
EPD identifier, sequence hash, genomic interval, exact-overlap status, nearest
TSS distance, and implicated TSS identifiers for every removal.

## Remaining gates

This historical-control candidate still requires distribution and dependency
audits, followed by an EPD-identifier- and near-sequence-grouped split. The
completed distribution audit found persistent positive-minus-negative mean GC
differences of 0.1149 for Human and 0.1069 for Mouse, both with strong
distributional separation after Holm correction. TSS filtering therefore does
not remove the major compositional shortcut.

Exact strand-invariant dependency auditing found one shared positive between
the Human and Mouse candidates and one opposite-label identity between a Mouse
downstream control (`FP002834|Gm50063_1`) and a CNNProm Mouse non-TATA positive.
The latter match is reverse-complement oriented and blocks Mouse confirmatory
eligibility pending source resolution. It is not automatically deleted or
relabeled. Consequently, no grouped split is generated yet. Predictive results,
if eventually authorized, must be reported separately from the primary
GC-matched reconstruction, and the slight post-treatment imbalance must be
handled by a predeclared training policy rather than test-set inspection.

## Version-2 external-positive exclusion

The version-2 successor applies one additional predeclared control-suitability
rule to the immutable version-1 output. A downstream control is excluded when
its exact strand-invariant identity is labeled positive in the hash-bound active
comparison source. This rule removed only Mouse record
`FP002834|Gm50063_1` (version-1 negative index 952), whose sequence is the
reverse complement of a positive in `cnnprom-eukaryotic-Mouse_non_tata`.
CNNProm was not modified or relabeled, and the exclusion does not establish
which biological annotation is correct.

Mouse therefore changes from 1,843 positive and 1,805 negative records in v1
to 1,843 and 1,804 in v2; Human remains byte-identical at 2,330 and 2,261.
The incremental ledger records the identifier, sequence hash, external dataset,
external label, and match orientation. A clean rebuild reproduced both FASTAs
and the ledger byte for byte.

The repeated dependency audit contains no remaining opposite-label identity
between the v2 candidates and the 18-dataset confirmatory scope. One same-label
positive remains shared between Human and Mouse and must be grouped if both are
ever admitted. Distributional bias is essentially unchanged: the mean GC gaps
are 0.1149 for Human and 0.1070 for Mouse. Both v2 candidates therefore remain
exploratory, unsplit, and blocked from model training pending construction of
the primary GC-matched control condition.
