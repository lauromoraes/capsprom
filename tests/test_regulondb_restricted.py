import subprocess
from pathlib import Path

RESTRICTED = [
    "configs/cnnprom_ecoli_genomic_control_pilot_v1.yaml",
    "configs/cnnprom_ecoli_genomic_control_pilot_v2.yaml",
    "configs/cnnprom_ecoli_genomic_pilot_manual_review_v1.yaml",
    "manifests/provenance/cnnprom_ecoli_genomic_control_pilot_v1/placement_summary.json",
    "manifests/provenance/cnnprom_ecoli_genomic_control_pilot_v2/placement_summary.json",
    "docs/provenance/manual_review_ecoli_genomic_pilot/review_sheet.csv",
]


def test_restricted_files_are_ignored_and_public_copies_hold_no_row_level_values() -> None:
    tracked = subprocess.run(["git", "ls-files", "--", *RESTRICTED], capture_output=True, text=True, check=True).stdout
    assert tracked == ""
    for version in ("v1", "v2"):
        text = Path(f"configs/cnnprom_ecoli_genomic_control_pilot_{version}.public.yaml").read_text(encoding="utf-8")
        assert "nearest_union_tss_offset_nt" not in text
        summary = Path(
            f"manifests/provenance/cnnprom_ecoli_genomic_control_pilot_{version}/placement_summary.public.json"
        ).read_text(encoding="utf-8")
        assert "resolved_tss" not in summary and "support_distance_nt\": -" not in summary
