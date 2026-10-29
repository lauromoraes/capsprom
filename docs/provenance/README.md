# Provenance Records

Where the evidence for the data's origin lives, and which documents depend on it.

| Need | Location |
| --- | --- |
| Rules (normative) | `specs/data_provenance_policy.md`, `specs/source_acquisition_protocol.md` |
| How to run, verify, recover | `docs/data_pipeline_operations.md` |
| Source contracts | `configs/source_acquisition_v1.yaml`, `configs/source_canonicalization_v1.yaml` |
| Machine records (committed) | `manifests/provenance/source_acquisition_v1/` |
| Machine records (authoritative, ignored) | `data/acquired/source_acquisition_v1/acquisition_manifest.json`, `data/canonical/source_canonicalization_v1/canonical_manifest.json`, run logs in `data/acquired/source_acquisition_v1/logs/` |
| Chronological log | `docs/provenance/research_log.md` |
| Facts, hypotheses, limitations | `docs/provenance/findings_register.md` |
| Lineage of experimental datasets | `docs/provenance/dataset_lineage.md` |
| Source and publication comparison | `docs/dataset_reconstruction_sources.md` |
| Acquisition v1 report | `docs/source_acquisition_v1_report.md` |
| Academic text | `docs/thesis/data_acquisition_provenance.tex` (input by chapter 4) |

## Committed records

`manifests/provenance/source_acquisition_v1/` contains:

- `acquisition_manifest.json`, `canonical_manifest.json`: snapshots of the
  authoritative manifests (`record_provenance.py snapshot`). Refresh them after
  every acquisition or canonicalization run, so that Git shows each change.
- `source_release_metadata.json`: upstream commit dates and HTTP headers, with
  `observed_at`.
- `legacy_raw_inventory.json`: SHA-256 and lineage status of every file in
  `data/raw/`; every legacy acquisition date is `unknown`.
- `regenerated_v3_replay.json`: byte comparison of the regenerated-v3 datasets
  rebuilt from the acquired files.

These are hash and metadata records, not data. No sequence is stored in them.
