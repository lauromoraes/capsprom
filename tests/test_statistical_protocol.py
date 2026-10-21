from pathlib import Path

import yaml


def test_statistical_protocol_v2_prevents_pseudoreplication() -> None:
    root = Path(__file__).parents[1]
    protocol = yaml.safe_load(
        (root / "configs/evaluation_protocol_v2.yaml").read_text(encoding="utf-8")
    )

    assert protocol["protocol"]["version"] == "2.0.0"
    assert protocol["selection"]["folds"] == 5
    assert protocol["selection"]["statistical_replication_unit"] is False
    assert len(protocol["replication"]["stochastic_seeds"]) == 10
    assert protocol["replication"]["statistical_replication_unit"] is False
    assert protocol["comparison"]["dataset_level_effect"] == (
        "median_of_seed_paired_mcc_differences"
    )
    assert protocol["comparison"]["across_datasets"]["independent_unit"] == (
        "audited_dependency_cluster"
    )
    assert protocol["comparison"]["across_datasets"]["two_model_test"] == (
        "two_sided_wilcoxon_signed_rank"
    )
    assert protocol["comparison"]["across_datasets"]["multi_model_omnibus_test"] == (
        "friedman"
    )
    assert protocol["comparison"]["multiplicity"]["correction"] == "holm"
    assert all(value is False for value in protocol["execution_gates"].values())
