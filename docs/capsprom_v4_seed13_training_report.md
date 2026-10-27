# CapsProm v4 Training-Only Seed-13 Report

## Scope

The first bounded release of the 18-dataset basic-CapsProm GPU v4 campaign ran
exactly five inner folds for
`cdbprom-prokaryotic-chlamydophila_pneumoniae` at seed 13. The release did not
authorize a final fit, external-test inference, embedding work, another seed,
or another dataset. The remote plan records `external_test_accessed: false`.

## Result

All five folds completed on their first attempt. Their best inner-validation
MCC values were 0.802377, 0.769882, 0.716264, 0.751923, and 0.747692. The mean
was 0.757628 with sample standard deviation 0.031603. Best epochs were 31, 41,
7, 30, and 25; the predeclared lower-median rule therefore selects epoch 30.

Fold 1 completed the 50-epoch maximum and selected epoch 41. This ceiling
contact is retained as a monitoring signal and does not authorize a post-outcome
change to the epoch budget. No fold collapsed to a single-class MCC of zero.

## Integrity

The persistent remote launcher wrote exit code zero. MLflow contains five
finished child runs and one intentionally open campaign parent. SQLite
`PRAGMA integrity_check` returned `ok`. A SHA-256 manifest covering 55 files was
written beside the persistent job log. No checkpoint was pruned.

A campaign-boundary snapshot was copied directly from `bioserver03` to
`bioserver04` at `/home/lauro/backups/capsprom/capsprom-v4-seed13/`. An rsync
checksum dry run reported no differences, the backup contains 55 files, and
its copied SQLite database independently returned integrity status `ok` with
the same five finished child runs and one open parent.

The remote checkout predates the locally implemented readiness command, so the
plan has not been mutated to `ready_for_final_fit`. The lower-median epoch above
was independently calculated read-only from the five completed plan entries.
Synchronizing and validating the readiness implementation is required before a
future final-fit release; final-fit and external-test gates remain closed.

## Review (2026-10-27, local and read-only)

The reported values are internally consistent: the fold MCCs average 0.757628,
and the sorted best epochs (7, 25, 30, 31, 41) give lower median 30. The
tranche stayed within release v3: five inner fits, no final fit, no external
test access, and no embedding job. No fold collapsed. One of five folds reached
the epoch ceiling, which is a monitoring signal only. The seed-13 mean is close
to the superseded 30-epoch v1/v2 line (0.756845 at seed 13, 0.744017 at seed
29). That comparison is descriptive and is not used for any selection.

The remaining blocker is operational: the readiness command is not yet on
`bioserver03`. The next unit is fixed by the deterministic scheduler
(`remote_operations.build_pending_fold_schedule`): the same dataset at seed 29,
folds 0-4. It is predeclared as the closed draft
`configs/capsprom_campaign_release_v4.yaml`, which the tranche runner refuses
to execute until an explicit authorization opens its inner-fold gate.
