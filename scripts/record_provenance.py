"""Record provenance for the pinned acquisition, the legacy data tree, and legacy builds.

Records are written to a versioned directory under ``manifests/provenance/`` so
that they are reviewable in Git; bulky staging output stays under ignored
``data/interim/``.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import yaml

from capsprom.data.acquisition import load_acquisition_config
from capsprom.data.canonical_sources import load_canonicalization_config
from capsprom.data.provenance import (
    inventory_legacy_tree,
    link_experiment_records,
    replay_regenerated_v3,
    source_release_metadata,
)
from capsprom.state import write_json_atomic

ACQUISITION_CONFIG = Path("configs/source_acquisition_v1.yaml")
CANONICAL_CONFIG = Path("configs/source_canonicalization_v1.yaml")
RECORD_DIR = Path("manifests/provenance/source_acquisition_v1")
REPLAY_DIR = Path("data/interim/provenance_replay_regenerated_v3")
V3_FILTERING_MANIFEST = Path("data/processed/audits/real_negative_regenerated_v3/filtering_manifest.json")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "record", choices=["snapshot", "source-metadata", "legacy-inventory", "replay-v3", "experiment-links"]
    )
    args = parser.parse_args()

    acquisition = load_acquisition_config(ACQUISITION_CONFIG)
    canonical = load_canonicalization_config(CANONICAL_CONFIG)
    acquired_root = Path(acquisition["acquisition"]["root"])
    acquisition_manifest_path = acquired_root / "acquisition_manifest.json"
    canonical_manifest_path = Path(canonical["canonicalization"]["output_dir"]) / "canonical_manifest.json"

    if args.record == "snapshot":
        RECORD_DIR.mkdir(parents=True, exist_ok=True)
        for source in (acquisition_manifest_path, canonical_manifest_path):
            shutil.copyfile(source, RECORD_DIR / source.name)
        result: dict = {"copied": [acquisition_manifest_path.name, canonical_manifest_path.name]}
    elif args.record == "source-metadata":
        result = source_release_metadata(yaml.safe_load(ACQUISITION_CONFIG.read_text(encoding="utf-8")))
        write_json_atomic(RECORD_DIR / "source_release_metadata.json", result)
    elif args.record == "legacy-inventory":
        result = inventory_legacy_tree(
            Path("."),
            Path("data/raw"),
            acquired_root,
            _load_json(acquisition_manifest_path),
            canonical,
            _load_json(canonical_manifest_path),
        )
        write_json_atomic(RECORD_DIR / "legacy_raw_inventory.json", result)
        result = result["summary"]
    elif args.record == "experiment-links":
        result = link_experiment_records(
            sorted(Path("outputs").rglob("*.json")),
            V3_FILTERING_MANIFEST,
            _load_json(RECORD_DIR / "regenerated_v3_replay.json"),
        )
        write_json_atomic(RECORD_DIR / "experiment_dataset_links.json", result)
        result = {key: result[key] for key in ("record_count", "fully_linked_records")}
    else:
        result = replay_regenerated_v3(
            canonical,
            acquired_root,
            REPLAY_DIR,
            V3_FILTERING_MANIFEST,
            Path("data/interim/fasta"),
            Path("data/processed/assembled_datasets/intra_regenerated_v3_strict_dna"),
        )
        write_json_atomic(RECORD_DIR / "regenerated_v3_replay.json", result)
        result = {key: result[key] for key in ("dataset_count", "all_datasets_match")}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
