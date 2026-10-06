"""Build the leakage-controlled Bhandari human promoter dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capsprom.data.leakage_controlled import build_bhandari_shuffled_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/raw/Bhandari_etal/Human_promoter.fa"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/leakage_controlled/bhandari_human_shuffle_v1"),
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = build_bhandari_shuffled_dataset(args.source, args.output_dir, seed=args.seed)
    print(json.dumps({key: str(value) for key, value in vars(result).items()}, indent=2))


if __name__ == "__main__":
    main()
