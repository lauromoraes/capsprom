# CNNProm E. coli Pilot Training Contract

## Status and scope

Draft (2026-11-06, log R-079). The machine-readable contract is
`configs/cnnprom_ecoli_pilot_training_v2.yaml`. Version 1 was drafted before the
panel visual analysis. Version 2 changes only data pins, counts, partitions, and
open items after the regrouping of F-142. It authorizes no materialization,
training, final fit, or test access; every such gate is false.

The pilot compares training and test negative definitions for one dataset,
CNNProm *E. coli*, at 81 nt. Results are exploratory and never enter the
confirmatory scope.

## Panels

| Panel | Positives | Negatives | Meaning of the negatives |
| --- | --- | --- | --- |
| `native` | 671 train, 168 test | 2,400 train, 600 test | CNNProm source negatives, opposite-strand CDS windows (F-129) |
| `genomic_gc_matched` | 668 train, 168 test | 668 train, 168 test | One same-strand NC_000913.3 window per positive at equal G+C count, 100 nt or more from every known TSS (F-136) |

Both panels use the same positives, except for three removed from the genomic
panel: rraBp1, whose window is the reverse complement of argIp, and two whose
controls link to another partition (R-078). The 168 test positives are the same
records in both panels.

## Decisions

Each contract section separates three labels.

- **Established** decisions come from an approved source: the eligibility
  manifest v2, the negative-control design, evaluation protocol v4, the seed
  policy, the pilot contract, or the current CapsProm development candidate.
- **Proposed** decisions are drafted for this pilot and bind only after owner
  approval.
- **Pending** items block execution until closed.

| Topic | Established | Proposed | Pending |
| --- | --- | --- | --- |
| Question and hypotheses | Primary hypothesis; one panel's MCC is not enough | H1 to H3 and comparisons C1 to C3 | Owner approval |
| Conditions | Native and genomic conditions, panels never pooled | Keep native class balance as distributed | Multi-negative condition |
| Partitions | Homology groups, inherited partitions, seed 42 | Inherited fold manifests in the runner | None |
| Seeds | Ten run seeds, sampling 20261104, bootstrap 20260715 | Run all ten in the pilot | None |
| Models | CapsProm one-hot, GC-only reference | Fixed logistic and XGBoost, no search | GC-only config; group-aware classical runner |
| Budget | 50 epochs, patience 15, lower-median epoch, full refit | 120 CapsProm fits, bounded release | Execution contract per condition |
| Metrics | MCC per panel, secondary list, group bootstrap | Recall, specificity, MCC at prevalence 0.5 | Per-panel inference job |
| Tracking | MLflow parent and child runs, required artifacts | Tags, parameters, and metric prefixes | Hardware record in the runners |

## Leakage rules

1. Every record keeps the homology group of grouped build v2, which joins
   overlapping windows by unique genomic coordinates (F-142). A
   control takes the group and partition of its positive, and a pair is
   indivisible.
2. Inner folds come from the build's `train:k` labels. The runner's stratified
   `write_fold_manifest` ignores groups and is not used; a contract selects
   the inherited folds with `protocol.fold_manifest_root`.
3. Feature fitting, epoch selection, thresholds, and any calibration use
   training rows only. Test panels are read once, after final fits are frozen,
   by the gated inference job.
4. A dataset-level or panel-level test result never changes a contract, a
   control, or a model choice.

## Reading the panels together

The native test panel has prevalence 0.219 and the genomic one 0.500, so raw
MCC is not comparable across panels. For one fitted model the two panels share
all positives, so recall is identical and every difference comes from the
negatives and the prevalence. The contract reports recall, specificity per
panel, and MCC at prevalence 0.5 next to the raw per-panel MCC. These
across-panel summaries are descriptive and claim no record pairing.

With one dataset, no across-dataset test applies. Random genomic controls also
remain positive-unlabeled: absence from the TSS inventory does not prove
biological inactivity.

## Before training

The contract's `open_items` list what must close first. Three items block by
themselves.

- `configs/negative_control_evaluation_v1.yaml` still records no selected
  dataset and closed construction and training gates, so a successor is needed.
- Step 1 of the protocol's execution order, the GraphPro Human/Mouse manual
  source audit, has no recorded completion. The owner completes or waives it.
- The classical, GC-only, and per-panel inference paths do not exist yet.

Any change after approval creates a new contract version and state path.
