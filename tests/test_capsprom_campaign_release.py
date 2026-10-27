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


def test_next_release_draft_is_closed_and_follows_the_contract_seed_order() -> None:
    root = Path(__file__).resolve().parents[1]
    contract = yaml.safe_load(
        (root / "configs/capsprom_basic_canonical_gpu_execution_v4.yaml").read_text()
    )
    previous = yaml.safe_load((root / "configs/capsprom_campaign_release_v3.yaml").read_text())
    draft = yaml.safe_load((root / "configs/capsprom_campaign_release_v4.yaml").read_text())

    seeds = contract["replication"]["seeds"]
    assert draft["scope"]["dataset_id"] == previous["scope"]["dataset_id"]
    assert draft["scope"]["seed"] == seeds[seeds.index(previous["scope"]["seed"]) + 1]
    assert draft["scope"]["folds"] == [0, 1, 2, 3, 4]
    assert draft["scope"]["maximum_new_inner_fits"] == 5
    assert draft["scientific_boundaries"] == previous["scientific_boundaries"]
    assert draft["release"]["status"] == "draft_pending_explicit_authorization"
    assert not any(draft["execution_gates"].values())
