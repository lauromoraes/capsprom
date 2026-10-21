"""Audit exact sequence sharing across canonical dataset identities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capsprom.data.dependency import audit_cross_dataset_dependency
from capsprom.state import write_json_atomic


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = audit_cross_dataset_dependency(args.dataset_dir)
    write_json_atomic(args.output, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
