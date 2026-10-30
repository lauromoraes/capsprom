# Data Pipeline Operations

How to run, verify, recover, and reproduce the data pipeline from upstream
sources to canonical tables, and how to regenerate the provenance records. The
rules behind these steps are in `specs/data_provenance_policy.md` and
`specs/source_acquisition_protocol.md`.

## Architecture

```text
configs/source_acquisition_v1.yaml ──► scripts/acquire_sources.py ──► data/acquired/source_acquisition_v1/
                                         (capsprom.data.acquisition)     ├── <source_id>/<path>
                                                                         ├── acquisition_manifest.json
                                                                         └── logs/
configs/source_canonicalization_v1.yaml ► scripts/canonicalize_sources.py ► data/canonical/source_canonicalization_v1/
                                         (capsprom.data.canonical_sources) ├── <collection_id>.csv.gz
                                                                           └── canonical_manifest.json
scripts/record_provenance.py ──────────► manifests/provenance/source_acquisition_v1/   (committed)
 (capsprom.data.provenance)               ├── acquisition_manifest.json, canonical_manifest.json (snapshots)
                                          ├── source_release_metadata.json
                                          ├── legacy_raw_inventory.json
                                          └── regenerated_v3_replay.json
```

Large files stay under ignored `data/`. Only configs, code, documentation, and
the JSON records under `manifests/provenance/` are versioned.

## Environment

Commands run from the repository root with the project virtual environment
(`.venv`, Python 3.13). On this workstation the environment is a WSL venv:

```bash
wsl.exe -e sh -c 'cd /mnt/d/workspace/capsprom && PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py'
```

## Commands

| Step | Command | Writes |
| --- | --- | --- |
| Plan acquisition | `PYTHONPATH=src python scripts/acquire_sources.py` | nothing |
| Acquire or re-verify | `PYTHONPATH=src python scripts/acquire_sources.py --execute [--source ID]` | files, manifest, a `runs[]` entry |
| Canonicalize | `PYTHONPATH=src python scripts/canonicalize_sources.py [--collection ID]` | canonical tables and manifest |
| Snapshot manifests | `PYTHONPATH=src python scripts/record_provenance.py snapshot` | committed manifest copies |
| Upstream dates | `PYTHONPATH=src python scripts/record_provenance.py source-metadata` | `source_release_metadata.json` |
| Legacy inventory | `PYTHONPATH=src python scripts/record_provenance.py legacy-inventory` | `legacy_raw_inventory.json` |
| Legacy build replay | `PYTHONPATH=src python scripts/record_provenance.py replay-v3` | `regenerated_v3_replay.json`, staging under `data/interim/provenance_replay_regenerated_v3/` |
| Bhandari full recreation | `PYTHONPATH=src python scripts/record_provenance.py bhandari-recreation` | `bhandari_recreation.json` |
| Bhandari repository history | `PYTHONPATH=src python scripts/record_provenance.py bhandari-history` (needs `bhandari_history_acquisition_v1` and `reference_acquisition_v6`) | `manifests/provenance/bhandari_history_acquisition_v1/history_comparison.json`; loci in `data/interim/bhandari_history/` |
| Historical canonicalization (P-6) | `PYTHONPATH=src python scripts/canonicalize_sources.py --config configs/bhandari_history_canonicalization_v1.yaml`, then `scripts/record_provenance.py bhandari-history-canonical` | `data/canonical/bhandari_history_canonicalization_v1/`; `canonical_verification.json` |
| *A. thaliana* TSS classes | `PYTHONPATH=src python scripts/record_provenance.py arabidopsis-tss` (needs `reference_acquisition_v6`, `v8`, `v9` and the `bhandari-history` loci) | `tss_classification.json`; per-record evidence in `data/interim/bhandari_history/` |

Run long steps detached and logged so they survive a closed terminal, for example:

```bash
nohup env PYTHONPATH=src .venv/bin/python scripts/acquire_sources.py --execute > data/acquired/source_acquisition_v1/logs/run_$(date -u +%Y%m%dT%H%M%SZ).log 2>&1 &
```

## Validation

- **Acquisition:** each file must reproduce every declared digest (`sha256`,
  `md5`, Git blob SHA-1). Re-running `--execute` with nothing to download
  re-hashes every file and appends a `completed` run whose summary must show
  `skipped_verified` equal to `declared_files`.
- **Canonicalization:** every collection must be `pass` (exact per-class release
  counts and legacy sequence parity). The script exits 1 otherwise.
- **Replay:** `all_datasets_match` must be `true` before a legacy dataset is
  treated as derived from the reference collection.
- **Code:** `make check` after any code change.

## Failure recovery

| Symptom | Cause | Action |
| --- | --- | --- |
| Interrupted download or crash | network, power, terminal closed | Re-run the same command. Verified files are skipped; the partial `.part` file is discarded; the interrupted run stays in `runs[]` as `running` or `failed`. |
| `digest mismatch` | upstream changed or corrupted transfer | The file is deleted and the run is recorded as `failed`. Retry once; if it persists, the upstream changed: create a new acquisition version, do not edit the digest in v1. |
| `acquisition manifest belongs to a different config` | the config was edited after its manifest existed | Revert the config, or create `source_acquisition_v2.yaml` with a new root. |
| `CERTIFICATE_VERIFY_FAILED` | server omits an intermediate certificate | Pin the issuer's AIA certificate by SHA-256 as `tls_intermediate` in a new config version. Never disable verification. |
| Canonical input hash differs from acquisition manifest | acquired file altered | Re-run acquisition `--execute` to restore it from upstream, then canonicalize again. |
| Replay refuses to start | staging directory not empty | Remove `data/interim/provenance_replay_regenerated_v3/` (it is regenerable) and re-run. |
| GitHub API rate limit during `source-metadata` | unauthenticated API quota | Wait for the quota reset and re-run; the record is rewritten atomically. |

## Reproducing from scratch

1. Check out the commit that contains the configs.
2. Run acquisition with `--execute`. Every file must match its pinned digest;
   files without a declared digest (see the report) are checked against the
   committed manifest snapshot by SHA-256.
3. Run canonicalization; the output SHA-256 values must equal those in the
   committed `canonical_manifest.json` snapshot, because the tables are
   byte-reproducible.
4. Run `replay-v3` to confirm the legacy experimental datasets are still
   reproduced.
