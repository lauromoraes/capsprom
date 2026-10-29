# Legacy Data Archive Plan

Plan only: nothing has been archived or deleted. It applies when
`specs/sequence_window_policy.md` makes earlier processed data obsolete. Each
deletion needs the owner's confirmation, and is logged in
`docs/provenance/research_log.md`.

## What may be archived, and what stays

| Kind | Action | Reason |
| --- | --- | --- |
| Configs, specs, manifests, provenance records, reports in Git | **keep**; mark superseded configs in `configs/README.md` | immutable contracts; cited by hashes in the log, lineage, and thesis; a few KB each |
| Code of the 81 nt crop | **keep**, parameterize | the regenerated-v3 replay (`capsprom.data.provenance`) and all prokaryotic builds use it |
| `data/acquired/`, `data/canonical/` | **keep** | source of every new build |
| Processed datasets superseded by a newer accepted build | archive, then remove from disk | not in Git; reproducible from `acq-v1` (F-020) or kept only as provenance |
| `intra_regenerated_v3_strict_dna/` | **keep** until a v4 build is accepted | active confirmatory input; prokaryotic datasets stay valid |
| `data/raw/`, `data/interim/` | archive only after the legacy inventory no longer needs them | `prov/legacy_raw_inventory.json` and F-022 refer to their content |
| `mlruns/`, `mlflow.db`, `outputs/` | archive a copy; do not delete | they hold prokaryotic and 81 nt results that remain valid provenance; F-024 lists them as unscanned |

## Inventory at 2026-10-29

Sizes from `du -sh` on the working copy:

| Path | Size | Proposed action |
| --- | --- | --- |
| `data/processed/assembled_datasets/intra` | 147M | archive |
| `data/processed/assembled_datasets/intra_strict_dna` | 149M | archive |
| `data/processed/assembled_datasets/intra_regenerated_v1` | 16M | archive |
| `data/processed/assembled_datasets/intra_regenerated_v1_strict_dna` | 16M | archive |
| `data/processed/assembled_datasets/intra_regenerated_v2` | 15M | archive |
| `data/processed/assembled_datasets/intra_regenerated_v2_strict_dna` | 15M | archive |
| `data/processed/assembled_datasets/intra_regenerated_v3_strict_dna` | 15M | keep (active) |
| `data/processed/leakage_controlled` | 11M | keep (Bhandari shuffle control) |
| `data/processed/audits` | 452K | keep |
| `data/interim` | 630M | archive later |
| `data/raw` | 1.1G | archive later |
| `mlruns` + `mlflow.db` | 616M + 7M | archive copy, keep |
| `outputs/` | about 120M | archive copy, keep |

Archiving the six superseded processed directories frees about 358 MB.

## Procedure

1. Write `manifests/provenance/legacy_archive_v1/archive_manifest.json` with
   one row per file: relative path, size, and SHA-256.
2. Create one compressed archive per directory, outside the repository, and
   record each archive's SHA-256 and storage location in the manifest.
3. Restore each archive into a scratch directory and compare every file hash
   with the manifest.
4. Only then, and with the owner's confirmation, remove the originals.
5. Log the procedure, the location, and the hashes in a research-log entry, and
   update `docs/provenance/dataset_lineage.md`.
