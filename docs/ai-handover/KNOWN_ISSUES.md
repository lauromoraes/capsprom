# Known Issues, Risks, and Gaps

## P0 scientific and preservation risks

- The campaign/consolidation state is preserved in `315f5cc`, and this handover is versioned separately. A migration must include both commits and any explicitly selected ignored artifacts.
- GraphPro labels/provenance are scientifically unsafe for confirmatory use. The pAA coordinate mapping invalidates derived MG1655 candidates and controls.
- External test access must remain closed. Any accidental access during selection would invalidate blind confirmatory claims.
- Versioned YAML with existing state must not be edited in place.

## P1 operational/scientific risks

- The basic CapsProm full 18-dataset campaign is not released. One successful dataset/seed tranche is insufficient to infer robustness or superiority.
- One completed fold hit the 50-epoch ceiling. Monitor future bounded tranches without adapting the budget from observed outcomes.
- `configs/evaluation_protocol_v3.yaml` is design-locked but confirmatory ranking remains disabled.
- The remote state was not directly checked during this audit. Registry/report evidence may lag unregistered activity.

## Documentation contradictions clarified

- `docs/processed_dataset_validation_summary.md` describes older `intra/` and legacy strict-DNA data; it must not be read as the active canonical-v3 validation result.
- `README.md` presents an early incremental structure and does not enumerate the now extensive implementation; `docs/roadmap.md` and `make status` are current.
- The earlier stale remote-policy v2 reference in `docs/development_environment.md` was corrected to active policy v3 in `315f5cc`.
- The earlier stale GPU-v3 next action was corrected in `315f5cc`; `make status` now requests review of the completed v4 tranche and predeclaration of the next bounded training-only release.
- XGBoost v2 status says a summary is available, but there is no `outputs/reports/xgboost_ten_seed_replication_v2/summary.json`; the documented summary is `docs/xgboost_ten_seed_replication.md` and the active consolidation JSON. Treat the status field as semantic availability, not that exact path.

## Unrecovered information

- Live remote process/session list and filesystem parity.
- External qualification-source availability at its Windows/OneDrive path.
- Whether all ignored output artifacts have an off-machine backup beyond the reported bioserver04 copy of the v4 boundary.
- Confirmation that the destination received both `315f5cc` and the handover commit, plus any separately transferred ignored artifacts.
