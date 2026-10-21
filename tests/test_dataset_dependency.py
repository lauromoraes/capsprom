import csv
import re
from pathlib import Path

import yaml

from capsprom.data.dependency import audit_cross_dataset_dependency


def _write(path: Path, rows: list[tuple[str, int]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sequence", "label"])
        writer.writerows(rows)


def test_cross_dataset_dependency_audit_counts_label_directions(tmp_path: Path) -> None:
    _write(tmp_path / "source-a-p-1-n-1-train.csv", [("AAAA", 0), ("CCCC", 1)])
    _write(tmp_path / "source-a-p-1-n-1-test.csv", [("GGGG", 0), ("TTTT", 1)])
    _write(tmp_path / "source-b-p-1-n-1-train.csv", [("AAAA", 1), ("CCCC", 1)])
    _write(tmp_path / "source-b-p-1-n-1-test.csv", [("ACGT", 0), ("TGCA", 1)])

    report = audit_cross_dataset_dependency(tmp_path)

    assert report["dataset_count"] == 2
    assert report["overlapping_pair_count"] == 1
    assert report["overlaps"] == [
        {
            "left_dataset_id": "source-a",
            "right_dataset_id": "source-b",
            "total": 2,
            "same_label_0": 0,
            "same_label_1": 1,
            "left_0_right_1": 1,
            "left_1_right_0": 0,
        }
    ]


def test_dependency_manifest_covers_the_canonical_contract() -> None:
    root = Path(__file__).parents[1]
    manifest = yaml.safe_load(
        (root / "configs/dataset_dependency_manifest_v1.yaml").read_text()
    )
    contract = yaml.safe_load(
        (root / "configs/capsprom_basic_canonical_gpu_execution_v2.yaml").read_text()
    )
    manifest_ids = [row["dataset_id"] for row in manifest["datasets"]]
    contract_ids = contract["protocol"]["dataset_ids"]
    file_ids = sorted(
        re.sub(r"-p-\d+-n-\d+-train$", "", path.stem)
        for path in (
            root / "data/processed/assembled_datasets/intra_regenerated_v3_strict_dna"
        ).glob("*-train.csv")
    )

    assert len(manifest_ids) == len(set(manifest_ids)) == 26
    assert sorted(manifest_ids) == sorted(contract_ids) == file_ids
    assert manifest["manifest"]["status"] == "provisional_requires_source_lineage_review"
    assert manifest["manifest"]["exact_overlap_audit"]["overlapping_pair_count"] == 8
    assert len(manifest["observed_exact_overlaps"]) == 8
    assert all(row["dependency_cluster_id"] for row in manifest["datasets"])


def test_fifty_epoch_contract_is_new_and_fully_blocked() -> None:
    root = Path(__file__).parents[1]
    contract = yaml.safe_load(
        (root / "configs/capsprom_basic_canonical_gpu_execution_v2.yaml").read_text()
    )
    policy = yaml.safe_load(
        (root / "configs/capsprom_future_campaign_release_policy_v2.yaml").read_text()
    )

    assert contract["training"]["maximum_epochs"] == 50
    assert contract["training"]["patience"] == 15
    assert contract["execution_gates"]["canonical_jobs_enabled"] is False
    assert contract["execution_gates"]["final_fits_enabled"] is False
    assert contract["execution_gates"]["external_test_enabled"] is False
    assert policy["scope"]["previous_30_epoch_folds_reusable"] is False
    assert policy["budget"]["restart_every_fold_from_epoch_one"] is True
    assert all(value is False for value in policy["execution_gates"].values())
