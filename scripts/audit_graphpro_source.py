"""Write a machine-readable audit of the released GraphPro class files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capsprom.data.fasta_builders import GRAPHPRO_DATASET_NAMES
from capsprom.data.graphpro_reconstruction import audit_graphpro_pair
from capsprom.state import write_json_atomic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/GraphPro"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audits = [audit_graphpro_pair(args.raw_dir / folder).as_dict() for folder in GRAPHPRO_DATASET_NAMES]
    payload = {
        "schema_version": 1,
        "interpretation": "descriptive_only_released_labels_are_not_independently_verified",
        "datasets": audits,
    }
    write_json_atomic(args.output, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
