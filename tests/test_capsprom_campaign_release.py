from pathlib import Path

import yaml


def test_v4_campaign_release_is_bounded_and_excludes_graphpro() -> None:
    root = Path(__file__).resolve().parents[1]
    contract = yaml.safe_load(
        (root / "configs/capsprom_basic_canonical_gpu_execution_v4.yaml").read_text()
    )
    release = yaml.safe_load(
        (root / "configs/capsprom_campaign_release_v3.yaml").read_text()
    )

    dataset_ids = contract["protocol"]["dataset_ids"]
    assert len(dataset_ids) == 18
    assert all(not dataset_id.startswith("graphpro-") for dataset_id in dataset_ids)
    assert release["scope"]["dataset_id"] in dataset_ids
    assert release["scope"]["folds"] == [0, 1, 2, 3, 4]
    assert release["scope"]["maximum_new_inner_fits"] == 5
    assert contract["execution_gates"]["canonical_jobs_enabled"] is True
    assert contract["execution_gates"]["final_fits_enabled"] is False
    assert contract["execution_gates"]["external_test_enabled"] is False
    assert contract["execution_gates"]["embedding_jobs_enabled"] is False
    assert release["execution_gates"]["additional_inner_folds_enabled"] is False
