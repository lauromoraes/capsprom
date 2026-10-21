#!/usr/bin/env python3
"""Create or verify a checksum manifest for an experiment artifact snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capsprom.remote_operations import (
    verify_artifact_snapshot,
    write_artifact_snapshot_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("root", type=Path)
    create.add_argument("manifest", type=Path)
    verify = subparsers.add_parser("verify")
    verify.add_argument("root", type=Path)
    verify.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.command == "create":
        report = write_artifact_snapshot_manifest(args.root, args.manifest)
    else:
        report = verify_artifact_snapshot(args.root, args.manifest)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.command == "verify" and not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
