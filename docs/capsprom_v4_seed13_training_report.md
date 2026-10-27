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

## Readiness synchronization (2026-10-27, authorized, no training)

The `bioserver03` checkout had been synchronized by file copy (Git `c466e97`
plus local changes). A read-only diff showed that the inner-fold training path
was unchanged. `neural_training.py` only adds a test-only interruption hook
that is disabled by default. Both removed lines in `canonical_neural.py` are in
the final-fit path, which had never run. Before any change, the plan was copied
to `plan_state.pre-readiness-20261027.json` (SHA-256 `c09eeee7…c62d`) and
`src/` and `scripts/` were archived to `tmp/code-pre-readiness-20261027.tgz`.
Then `src/` and `scripts/` were copied without deletion. The v4 contract
(SHA-256 `e2c244d8…cdc2`) and release v3 were already identical to the local
copies and were not touched.

`refresh-neural-canonical-readiness` marked exactly one unit, Chlamydophila
seed 13, as `ready_for_final_fit` with selected epoch 30 from fold epochs 31,
41, 7, 30, and 25. A second run changed nothing. A diff of the plan before and
after shows that only that final-fit job changed; all 1,080 jobs remain. Before
and after the refresh, all 18 training-file and fold-manifest hashes matched the
plan on `bioserver03`. The local training files match the same hashes. SQLite
integrity was `ok`, and MLflow kept five finished children and one open parent.
`external_test_accessed` remains false. No training, final fit, or external
inference ran.

## Seed-29 tranche (release v4, 2026-10-27)

Release v4 (SHA-256 `4a618340…1a92`) ran Chlamydophila seed 29, folds 0-4, on
`bioserver03` under `nohup`/`setsid` (PID 538712). It started at 11:27:04Z and
exited with code 0 at 11:27:58Z. All five folds completed on their first
attempt.

| Fold | Best inner-validation MCC | Best epoch | Epochs run |
| --- | --- | --- | --- |
| 0 | 0.835629 | 42 | 50 |
| 1 | 0.737122 | 8 | 23 |
| 2 | 0.721327 | 23 | 38 |
| 3 | 0.751923 | 5 | 20 |
| 4 | 0.753255 | 47 | 50 |

The mean is 0.759851 with sample SD 0.044298. The lower-median rule gives epoch
23. Two folds (0 and 4) reached the 50-epoch ceiling. This is the second seed
with ceiling contact, and it remains a monitoring signal; the budget was not
changed. Across the two v4 seeds, the means are 0.757628 and 0.759851.

The plan now has 10 completed inner folds and `external_test_accessed: false`.
All 18 training-file and fold-manifest hashes still match. SQLite integrity is
`ok`, and MLflow has 10 finished children and one open parent. An 87-file
SHA-256 manifest is in `remote_jobs/seed29-folds0-4.sha256`. The boundary was
copied to `bioserver04:/home/lauro/backups/capsprom/capsprom-v4-seed29`. A
checksum dry run found no differences, all 87 manifest entries verify, and the
copied SQLite is `ok`. Seed 29 has not been marked `ready_for_final_fit`,
because release v4 did not include a readiness refresh. Final fits, external
tests, and embeddings remain closed.

## Remaining Chlamydophila seeds (releases v5 and v6, 2026-10-27)

Before launch, a readiness refresh marked seed 29 `ready_for_final_fit`
(epoch 23). Release v5 (seed 42) exited 0 after 57 s. Release v6 covered
seeds 71, 101, 137, 173, 211, 251, and 293 in schedule order, 35 folds, and
exited 0 after 6 min 56 s. For v6, `scripts/run_bounded_canonical_tranche.py`
was extended to accept a `seeds` list. It still accepts a single `seed`, and
the inner-fold command it calls is unchanged. Every fold completed on its first
attempt. A refresh after each release marked every seed `ready_for_final_fit`.

| Seed | Mean MCC | SD | Selected epoch | Folds at 50 epochs |
| --- | --- | --- | --- | --- |
| 13 | 0.757628 | 0.031603 | 30 | 1/5 |
| 29 | 0.759851 | 0.044298 | 23 | 2/5 |
| 42 | 0.732165 | 0.041744 | 9 | 1/5 |
| 71 | 0.744610 | 0.042871 | 39 | 4/5 |
| 101 | 0.752773 | 0.062173 | 32 | 2/5 |
| 137 | 0.765219 | 0.056676 | 33 | 2/5 |
| 173 | 0.758399 | 0.051162 | 18 | 0/5 |
| 211 | 0.757059 | 0.060750 | 32 | 1/5 |
| 251 | 0.743526 | 0.035332 | 8 | 1/5 |
| 293 | 0.756374 | 0.057575 | 31 | 2/5 |

Across the 10 seeds, the mean of seed means is 0.752760, with SD 0.009823 and
range 0.732165-0.765219. Selected epochs vary widely, from 8 to 39. Sixteen of
the 50 folds ran the full 50 epochs, and one of them (seed 293, fold 3) had its
best epoch at 50. This shows that the budget is often binding on this dataset.
The signal is recorded only; the budget cannot change within contract v4.
On 2026-10-27 the user decided to keep the 50-epoch ceiling for the whole v4
campaign. Ceiling contact is reported per dataset as a monitoring statistic.

## Corynebacterium glutamicum (release v7, 2026-10-27)

Release v7 (SHA-256 `0e2be325…6000`) ran all 10 contract seeds for
`cdbprom-prokaryotic-corynebacterium_glutamicum` (906 training rows), 50
folds. It started at 12:15:38Z and exited 0 at 12:26:52Z. Every fold completed
on its first attempt.

| Seed | Mean MCC | SD | Selected epoch | Folds at 50 epochs |
| --- | --- | --- | --- | --- |
| 13 | 0.761969 | 0.041699 | 25 | 2/5 |
| 29 | 0.771568 | 0.038252 | 31 | 2/5 |
| 42 | 0.779212 | 0.050193 | 31 | 0/5 |
| 71 | 0.769223 | 0.043918 | 26 | 0/5 |
| 101 | 0.777536 | 0.049313 | 27 | 1/5 |
| 137 | 0.777664 | 0.029166 | 33 | 2/5 |
| 173 | 0.772663 | 0.045638 | 31 | 1/5 |
| 211 | 0.769649 | 0.041636 | 34 | 2/5 |
| 251 | 0.761107 | 0.043030 | 26 | 0/5 |
| 293 | 0.767543 | 0.045412 | 43 | 3/5 |

The mean of seed means is 0.770813, with SD 0.006269 and range
0.761107-0.779212. Selected epochs range from 25 to 43. Thirteen of 50 folds
ran the full 50 epochs, and one (seed 137, fold 4) had its best epoch at 50.

After a readiness refresh, the plan has 100 completed inner folds and 20 units
`ready_for_final_fit`. `external_test_accessed` is false. All 18 data and
fold-manifest hashes match, SQLite is `ok`, and MLflow has 100 finished
children and one open parent. A 632-file manifest is in
`remote_jobs/corynebacterium-seeds13-293.sha256`. The backup at
`bioserver04:/home/lauro/backups/capsprom/capsprom-v4-corynebacterium-10-seeds`
has no checksum differences, verifies all 632 entries, and its SQLite copy is
`ok`. Final fits, external tests, and embeddings remain closed.

The plan has 50 completed inner folds, 10 units `ready_for_final_fit`, and
`external_test_accessed: false`. All 18 data and fold-manifest hashes match,
SQLite is `ok`, and MLflow has 50 finished children and one open parent. A
330-file manifest is in `remote_jobs/chlamydophila-seeds42-293.sha256`. The
backup at `bioserver04:/home/lauro/backups/capsprom/capsprom-v4-chlamydophila-10-seeds`
has no checksum differences, verifies all 330 entries, and its SQLite copy is
`ok`. Final fits, external tests, and embeddings remain closed.
