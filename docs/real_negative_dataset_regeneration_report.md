# Real-Negative Dataset Regeneration Report

> This report describes regenerated v1, which corrected append duplication but
> retained cross-label collisions. Regenerated v3 supersedes both v1 and v2 for
> experiments by removing collisions and same-label duplicates, filtering
> strict DNA, and assigning deterministic unique-sequence groups.
> See `docs/label_collision_filtering_report.md`.

## Purpose

This report evaluates the effect of replacing append mode with overwrite mode
in `data/crop_seqs.ipynb` and rebuilding the CDBProm, CNNProm, and GraphPro
datasets from the normalized pre-crop FASTA files. Regenerated artifacts are
stored separately from the legacy files under directories suffixed with
`regenerated_v1`.

## Root Cause

The legacy notebook opened every cropped FASTA with mode `a`. Re-executing the
cell appended the complete record collection to an existing output. The
resulting files contain exactly three copies of each promoter input and four
copies of each non-promoter input. The subsequent CSV construction preserved
those copies and split them at row level, placing identical copies in both
train and test.

The corrected notebook uses mode `w`. The reusable builder already used
overwrite semantics and is covered by an idempotence test that executes the
same crop twice and verifies that record counts do not grow.

## Before-and-After Audit

Table `tab:append-fix-effectiveness` compares the complete 26-pair audits. The
append correction removes the systematic 3x/4x replication and reduces test
rows participating in exact train/test overlap from 98.09% to 2.17%.

| Measure | Legacy append data | Regenerated overwrite data |
| --- | ---: | ---: |
| Training rows | 529,014 | 146,956 |
| Test rows | 132,272 | 36,737 |
| Internal duplicate rows | 379,046 | 1,614 |
| Shared unique sequences | 99,633 | 794 |
| Test rows in train/test overlap | 129,739 | 799 |
| Test rows in overlap (%) | 98.09 | 2.17 |
| Unique label conflicts | 1,348 | 1,348 |
| Strictly eligible pairs | 0 of 26 | 9 of 26 |

Table label: `tab:append-fix-effectiveness`.

By source, the remaining test-row overlap is 1.20% for CDBProm, 1.15% for
CNNProm, and 6.97% for GraphPro. The correction is therefore effective against
pipeline-introduced replication, but it does not remove natural duplicates,
crop-induced collisions, or source-level label conflicts.

## Eligible Pairs After Regeneration

The following nine pairs contain zero internal duplicates, zero label conflicts,
and zero exact train/test overlap under the regenerated row-level split:

- CDBProm: `bacillus_amyloliquefaciens`, `chlamydophila_pneumoniae`,
  `klebisiella_pneumoniae`, and `salmonella_typhimurium`;
- CNNProm: `Bacillus` and `Ecoli`;
- GraphPro: `bacillus_amyloliquefaciens`,
  `clostridium_phytofermentans`, and `rhodobacter_capsulatus`.

The v1 result established that all 1,348 unique label conflicts remain after the
append correction, confirming that they were not created by repeated file
writes. Regenerated v2 removes both labels for every ambiguous sequence before
splitting; its audit contains zero label conflicts and accepts 10 of 26 pairs.

## Reproduction

The active v3 dataset and its stage-level filtering manifests are reproduced
and audited with:

```bash
PYTHONPATH=src .venv/bin/python scripts/rebuild_real_negative_datasets.py
PYTHONPATH=src .venv/bin/python -m capsprom audit-datasets \
  data/processed/assembled_datasets/intra_regenerated_v3_strict_dna \
  data/processed/audits/real_negative_regenerated_v3
```

Its audit identifier is
`87371a88ca1c5456db340201de5c19558b1a5773cb441787ffffc0803b66d853`.

For historical reproduction of the append-only correction without collision
removal, the v1 audit command was:

```bash
PYTHONPATH=src .venv/bin/python -m capsprom audit-datasets \
  data/processed/assembled_datasets/intra_regenerated_v1_strict_dna \
  data/processed/audits/real_negative_regenerated_v1
```

The historical v1 audit identifier is
`6e86a8b6b2dca48b77404ba002583d8417d02727044f70167a8b1e0a98fac70b`.
