#!/usr/bin/env python3
"""Create strict-DNA cleaned copies of processed CapsProm CSV datasets."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from capsprom.data.dataset_builders import clean_processed_directory  # noqa: E402


def write_manifest(results, output_dir: Path) -> None:
    manifest = output_dir / "cleaning_manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "source_file",
            "cleaned_file",
            "rows_in",
            "rows_out",
            "removed_rows",
            "original_positive",
            "original_negative",
            "cleaned_positive",
            "cleaned_negative",
            "invalid_symbols",
        ])
        for result in results:
            writer.writerow([
                result.source.as_posix(),
                result.output.as_posix(),
                result.rows_in,
                result.rows_out,
                result.removed_rows,
                result.original_positive,
                result.original_negative,
                result.cleaned_positive,
                result.cleaned_negative,
                "".join(sorted(result.invalid_symbols)) or "-",
            ])

    changed = [result for result in results if result.removed_rows]
    readme = output_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Strict DNA Processed Datasets",
                "",
                "This directory contains cleaned copies of `data/processed/assembled_datasets/intra`.",
                "Original files are preserved unchanged. Cleaning removes only rows whose `sequence` contains characters outside `A`, `C`, `G`, and `T`.",
                "",
                "Filenames in this directory use updated `p` and `n` counts after row removal.",
                "",
                "## Summary",
                "",
                f"- Source CSV files: {len(results)}",
                f"- Cleaned CSV files: {len(results)}",
                f"- Files with removed rows: {len(changed)}",
                f"- Total removed rows: {sum(result.removed_rows for result in results)}",
                "",
                "See `cleaning_manifest.csv` for the source-to-cleaned mapping.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main(argv: list[str]) -> int:
    source_dir = Path(argv[1]) if len(argv) > 1 else Path("data/processed/assembled_datasets/intra")
    output_dir = Path(argv[2]) if len(argv) > 2 else Path("data/processed/assembled_datasets/intra_strict_dna")
    results = clean_processed_directory(source_dir, output_dir)
    write_manifest(results, output_dir)
    print(f"source_files={len(results)} cleaned_files={len(results)} removed_rows={sum(r.removed_rows for r in results)} output_dir={output_dir}")
    for result in results:
        if result.removed_rows:
            print(f"removed={result.removed_rows} source={result.source.name} cleaned={result.output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
