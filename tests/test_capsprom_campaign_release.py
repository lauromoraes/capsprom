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


def test_release_v4_opens_only_its_folds_and_follows_the_contract_seed_order() -> None:
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
    assert draft["release"]["status"] == "authorized_bounded_training_only_tranche"
    assert {name for name, open_ in draft["execution_gates"].items() if open_} == {
        "authorized_inner_folds_enabled"
    }


def test_releases_v3_to_v6_cover_each_contract_seed_once_in_order() -> None:
    root = Path(__file__).resolve().parents[1]
    contract = yaml.safe_load(
        (root / "configs/capsprom_basic_canonical_gpu_execution_v4.yaml").read_text()
    )
    released = []
    for version in (3, 4, 5, 6):
        release = yaml.safe_load(
            (root / f"configs/capsprom_campaign_release_v{version}.yaml").read_text()
        )
        scope = release["scope"]
        seeds = scope.get("seeds", [scope.get("seed")])
        assert scope["maximum_new_inner_fits"] == len(scope["folds"]) * len(seeds)
        assert release["scientific_boundaries"]["maximum_epochs"] == 50
        assert {name for name, open_ in release["execution_gates"].items() if open_} == {
            "authorized_inner_folds_enabled"
        }
        released += seeds
    assert released == contract["replication"]["seeds"]


def test_release_v7_opens_only_its_folds_and_keeps_the_v4_budget() -> None:
    root = Path(__file__).resolve().parents[1]
    contract = yaml.safe_load(
        (root / "configs/capsprom_basic_canonical_gpu_execution_v4.yaml").read_text()
    )
    previous = yaml.safe_load((root / "configs/capsprom_campaign_release_v6.yaml").read_text())
    draft = yaml.safe_load((root / "configs/capsprom_campaign_release_v7.yaml").read_text())

    assert draft["scope"]["dataset_id"] in contract["protocol"]["dataset_ids"]
    assert draft["scope"]["seeds"] == contract["replication"]["seeds"]
    assert draft["scope"]["maximum_new_inner_fits"] == 50
    assert draft["scientific_boundaries"] == previous["scientific_boundaries"]
    assert draft["release"]["status"] == "authorized_bounded_training_only_tranche"
    assert {name for name, open_ in draft["execution_gates"].items() if open_} == {
        "authorized_inner_folds_enabled"
    }


def test_tranche_runner_expands_seed_list_in_order(tmp_path, monkeypatch) -> None:
    import scripts.run_bounded_canonical_tranche as runner

    root = Path(__file__).resolve().parents[1]
    calls = []
    monkeypatch.setattr(runner.subprocess, "run", lambda command, check: calls.append(command))
    monkeypatch.setattr(
        runner.sys,
        "argv",
        [
            "runner",
            "--contract", "contract.yaml",
            "--release", str(root / "configs/capsprom_campaign_release_v6.yaml"),
            "--output-dir", str(tmp_path),
            "--exit-code-path", str(tmp_path / "job.exit"),
        ],
    )

    assert runner.main() == 0
    assert [(command[-2], command[-1]) for command in calls] == [
        (str(seed), str(fold))
        for seed in (71, 101, 137, 173, 211, 251, 293)
        for fold in range(5)
    ]
    assert (tmp_path / "job.exit").read_text() == "0\n"
