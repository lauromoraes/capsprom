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

## CNNProm Bacillus (release v8, 2026-10-27)

Release v8 (SHA-256 `025d4678…8747`) ran all 10 contract seeds for
`cnnprom-prokaryotic-Bacillus` (1,098 training rows), 50 folds. It started at
12:34:41Z and exited 0 at 12:47:44Z. Every fold completed on its first attempt.

| Seed | Mean MCC | SD | Selected epoch | Folds at 50 epochs |
| --- | --- | --- | --- | --- |
| 13 | 0.758007 | 0.036626 | 47 | 3/5 |
| 29 | 0.745790 | 0.022056 | 22 | 1/5 |
| 42 | 0.752993 | 0.029793 | 37 | 3/5 |
| 71 | 0.757858 | 0.034600 | 47 | 3/5 |
| 101 | 0.751190 | 0.020724 | 21 | 1/5 |
| 137 | 0.745311 | 0.024622 | 28 | 2/5 |
| 173 | 0.754068 | 0.030929 | 22 | 2/5 |
| 211 | 0.752483 | 0.029751 | 36 | 3/5 |
| 251 | 0.759319 | 0.031276 | 48 | 4/5 |
| 293 | 0.745047 | 0.035227 | 29 | 2/5 |

The mean of seed means is 0.752207, with SD 0.005389 and range
0.745047-0.759319. Twenty-four of 50 folds ran the full 50 epochs, and six had
their best epoch at 50. Ceiling contact is higher than on the two earlier
datasets (16/50 and 13/50). Under the user decision it is reported only.

After a readiness refresh, the plan has 150 completed inner folds and 30 units
`ready_for_final_fit`. `external_test_accessed` is false. All 18 data and
fold-manifest hashes match, SQLite is `ok`, and MLflow has 150 finished
children and one open parent. A 934-file manifest is in
`remote_jobs/bacillus-seeds13-293.sha256`. The backup at
`bioserver04:/home/lauro/backups/capsprom/capsprom-v4-bacillus-10-seeds` has
no checksum differences, verifies all 934 entries, and its SQLite copy is
`ok`. The v4 output tree on `bioserver03` is 3.0 GB after 150 folds, about
20 MB per fold, against 96 GB free. Final fits, external tests, and
embeddings remain closed.

## CDBProm Helicobacter pylori (release v9, 2026-10-27)

Release v9 (SHA-256 `55e6848d…cf7d`) ran all 10 contract seeds for
`cdbprom-prokaryotic-helicobacter_pylori` (1,130 training rows), 50 folds. It
started at 13:09:53Z and exited 0 at 13:23:49Z. Every fold completed on its
first attempt.

| Seed | Mean MCC | SD | Selected epoch | Folds at 50 epochs |
| --- | --- | --- | --- | --- |
| 13 | 0.880186 | 0.046812 | 48 | 3/5 |
| 29 | 0.894401 | 0.042201 | 44 | 3/5 |
| 42 | 0.894524 | 0.037024 | 48 | 3/5 |
| 71 | 0.889214 | 0.032882 | 46 | 5/5 |
| 101 | 0.894451 | 0.042128 | 38 | 3/5 |
| 137 | 0.887122 | 0.041331 | 49 | 3/5 |
| 173 | 0.885715 | 0.044335 | 39 | 4/5 |
| 211 | 0.891433 | 0.046492 | 43 | 3/5 |
| 251 | 0.906662 | 0.028698 | 44 | 4/5 |
| 293 | 0.904859 | 0.025781 | 50 | 5/5 |

The mean of seed means is 0.892857, with SD 0.008179 and range
0.880186-0.906662. Ceiling contact is the highest so far. Thirty-six of 50
folds ran the full 50 epochs, eight had their best epoch at 50, and selected
epochs range from 38 to 50. For seed 293 the selected epoch equals the budget.
The decision to keep the 50-epoch ceiling stands, and this is reported only.
It is still the strongest evidence so far that the budget limits training on
some datasets, and that matters for interpreting the campaign.

After a readiness refresh, the plan has 200 completed inner folds and 40 units
`ready_for_final_fit`. `external_test_accessed` is false. All 18 data and
fold-manifest hashes match, SQLite is `ok`, and MLflow has 200 finished
children and one open parent. A 1,236-file manifest is in
`remote_jobs/helicobacter-seeds13-293.sha256`. The backup at
`bioserver04:/home/lauro/backups/capsprom/capsprom-v4-helicobacter-10-seeds`
has no checksum differences, verifies all 1,236 entries, and its SQLite copy
is `ok`. The remote output tree is 4.0 GB, against 95 GB free on
`bioserver03` and 134 GB free on `bioserver04`.

## CDBProm Salmonella typhimurium (release v10, 2026-10-27)

Release v10 (SHA-256 `52cdfca2…ce1f`) ran all 10 contract seeds for
`cdbprom-prokaryotic-salmonella_typhimurium` (1,564 training rows), 50 folds.
It started at 13:30:51Z and exited 0 at 13:46:21Z. Every fold completed on its
first attempt.

| Seed | Mean MCC | SD | Selected epoch | Folds at 50 epochs |
| --- | --- | --- | --- | --- |
| 13 | 0.863814 | 0.022872 | 48 | 4/5 |
| 29 | 0.868024 | 0.030303 | 48 | 4/5 |
| 42 | 0.871568 | 0.037533 | 47 | 5/5 |
| 71 | 0.859075 | 0.029728 | 40 | 3/5 |
| 101 | 0.871448 | 0.037376 | 45 | 4/5 |
| 137 | 0.859936 | 0.022243 | 42 | 4/5 |
| 173 | 0.865187 | 0.032234 | 46 | 4/5 |
| 211 | 0.869090 | 0.029537 | 40 | 5/5 |
| 251 | 0.850733 | 0.026777 | 28 | 1/5 |
| 293 | 0.872487 | 0.030330 | 40 | 3/5 |

The mean of seed means is 0.865136, with SD 0.006930 and range
0.850733-0.872487. Thirty-seven of 50 folds ran the full 50 epochs, and seven
had their best epoch at 50. Selected epochs range from 28 to 48. This is
reported only; the ceiling is kept by decision.

After a readiness refresh, the plan has 250 completed inner folds and 50 units
`ready_for_final_fit`. `external_test_accessed` is false. All 18 data and
fold-manifest hashes match, SQLite is `ok`, and MLflow has 250 finished
children and one open parent. A 1,538-file manifest is in
`remote_jobs/salmonella-seeds13-293.sha256`. The backup at
`bioserver04:/home/lauro/backups/capsprom/capsprom-v4-salmonella-10-seeds`
has no checksum differences, verifies all 1,538 entries, and its SQLite copy
is `ok`.

Each backup so far has been a full, separate copy of the growing 5.0 GB output
tree. With 13 datasets left, that would need about 150 GB on `bioserver04`,
which has 131 GB free. From the next dataset on, each backup is written with
`rsync --link-dest` against the previous one. Unchanged files become hardlinks,
so each snapshot stays complete and independently verifiable while only new or
changed files use space.

## CDBProm Bacillus amyloliquefaciens (release v11, 2026-10-27)

Release v11 (SHA-256 `0a4684ab…6f48`) ran all 10 contract seeds for
`cdbprom-prokaryotic-bacillus_amyloliquefaciens` (1,692 training rows), 50
folds. It started at 14:02:38Z and exited 0 at 14:15:37Z. Every fold completed
on its first attempt.

| Seed | Mean MCC | SD | Selected epoch | Folds at 50 epochs |
| --- | --- | --- | --- | --- |
| 13 | 0.662557 | 0.025407 | 28 | 2/5 |
| 29 | 0.668430 | 0.024912 | 19 | 1/5 |
| 42 | 0.666398 | 0.034072 | 22 | 0/5 |
| 71 | 0.662129 | 0.029519 | 23 | 0/5 |
| 101 | 0.670244 | 0.031416 | 28 | 1/5 |
| 137 | 0.672325 | 0.038318 | 22 | 2/5 |
| 173 | 0.668551 | 0.044318 | 19 | 1/5 |
| 211 | 0.657077 | 0.035369 | 25 | 0/5 |
| 251 | 0.648549 | 0.028926 | 15 | 0/5 |
| 293 | 0.661980 | 0.041646 | 25 | 2/5 |

The mean of seed means is 0.663824, with SD 0.007074 and range
0.648549-0.672325. This is the lowest dataset mean so far. Ceiling contact is
low here: 9 of 50 folds reached 50 epochs, and one fold had its best epoch at
50. Selected epochs range from 15 to 28, so the budget is not binding on this
dataset.

After a readiness refresh, the plan has 300 completed inner folds and 60 units
`ready_for_final_fit`. `external_test_accessed` is false. All 18 data and
fold-manifest hashes match, SQLite is `ok`, and MLflow has 300 finished
children and one open parent. A 1,840-file manifest is in
`remote_jobs/amyloliquefaciens-seeds13-293.sha256`. The first hardlinked
backup, at
`bioserver04:/home/lauro/backups/capsprom/capsprom-v4-amyloliquefaciens-10-seeds`,
used 1,011 MB of new space instead of about 6 GB. It has no checksum
differences, verifies all 1,840 entries on its own, and its SQLite copy is
`ok`. `bioserver04` has 125 GB free.

## CDBProm Klebsiella pneumoniae (release v12, 2026-10-27)

Release v12 (SHA-256 `a5217a4b…514b`) ran all 10 contract seeds for
`cdbprom-prokaryotic-klebisiella_pneumoniae` (2,124 training rows), 50 folds.
The `klebisiella` spelling is the source identifier and is kept as is. The run
started at 14:26:19Z and exited 0 at 14:42:54Z. Every fold completed on its
first attempt.

| Seed | Mean MCC | SD | Selected epoch | Folds at 50 epochs |
| --- | --- | --- | --- | --- |
| 13 | 0.847811 | 0.009199 | 30 | 2/5 |
| 29 | 0.848505 | 0.011758 | 45 | 3/5 |
| 42 | 0.840365 | 0.020212 | 37 | 3/5 |
| 71 | 0.849743 | 0.016263 | 44 | 4/5 |
| 101 | 0.843860 | 0.005262 | 29 | 2/5 |
| 137 | 0.839233 | 0.010296 | 32 | 2/5 |
| 173 | 0.844132 | 0.010269 | 30 | 2/5 |
| 211 | 0.844233 | 0.012767 | 29 | 2/5 |
| 251 | 0.837930 | 0.008618 | 36 | 3/5 |
| 293 | 0.843473 | 0.017778 | 31 | 1/5 |

The mean of seed means is 0.843928, with SD 0.003957 and range
0.837930-0.849743. The fold-level SDs are the smallest so far. Twenty-four of
50 folds ran the full 50 epochs, and one had its best epoch at 50. Selected
epochs range from 29 to 45.

After a readiness refresh, the plan has 350 completed inner folds and 70 units
`ready_for_final_fit`. `external_test_accessed` is false. All 18 data and
fold-manifest hashes match, SQLite is `ok`, and MLflow has 350 finished
children and one open parent. A 2,142-file manifest is in
`remote_jobs/klebsiella-seeds13-293.sha256`. The hardlinked backup at
`bioserver04:/home/lauro/backups/capsprom/capsprom-v4-klebsiella-10-seeds`
used 1,013 MB of new space. It has no checksum differences, verifies all 2,142
entries, and its SQLite copy is `ok`. `bioserver04` has 124 GB free.

The plan has 50 completed inner folds, 10 units `ready_for_final_fit`, and
`external_test_accessed: false`. All 18 data and fold-manifest hashes match,
SQLite is `ok`, and MLflow has 50 finished children and one open parent. A
330-file manifest is in `remote_jobs/chlamydophila-seeds42-293.sha256`. The
backup at `bioserver04:/home/lauro/backups/capsprom/capsprom-v4-chlamydophila-10-seeds`
has no checksum differences, verifies all 330 entries, and its SQLite copy is
`ok`. Final fits, external tests, and embeddings remain closed.
