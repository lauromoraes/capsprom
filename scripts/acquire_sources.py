"""Plan or execute the pinned, hash-verified acquisition of upstream source files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from capsprom.data.acquisition import acquire_sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/source_acquisition_v1.yaml"))
    parser.add_argument("--execute", action="store_true", help="download; default only plans")
    parser.add_argument("--source", action="append", help="restrict to a source_id (repeatable)")
    args = parser.parse_args()
    settings = yaml.safe_load(args.config.read_text(encoding="utf-8"))["acquisition"]
    root = Path(settings["root"])
    summary = acquire_sources(
        args.config,
        root,
        root / "acquisition_manifest.json",
        execute=args.execute,
        only_sources=set(args.source) if args.source else None,
        command=[Path(sys.executable).name, *sys.argv],
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
