"""Map canonical records to reference assemblies under a versioned mapping config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capsprom.data.coordinate_mapping import run_mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/reference_coordinate_mapping_v1.yaml"))
    parser.add_argument("--collection", action="append", help="restrict to a collection_id")
    args = parser.parse_args()
    summary = run_mapping(args.config, Path.cwd(), only=set(args.collection) if args.collection else None)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
