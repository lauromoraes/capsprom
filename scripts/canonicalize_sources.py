"""Build canonical, validated record tables from the acquired source files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capsprom.data.canonical_sources import canonicalize_sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/source_canonicalization_v1.yaml")
    )
    parser.add_argument("--collection", action="append", help="restrict to a collection_id")
    args = parser.parse_args()
    summary = canonicalize_sources(
        args.config,
        Path.cwd(),
        only_collections=set(args.collection) if args.collection else None,
    )
    print(json.dumps(summary, indent=2))
    if summary["failed_validation"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
