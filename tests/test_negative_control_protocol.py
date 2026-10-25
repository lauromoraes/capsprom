from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "configs" / "negative_control_evaluation_v1.yaml"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_negative_control_contract_remains_execution_blocked() -> None:
    contract = _contract()

    assert contract["protocol"]["status"] == "design_locked_execution_blocked"
    assert contract["protocol"]["modifies_active_confirmatory_scope"] is False
    assert contract["pilot_selection"]["selected_dataset"] is None
    assert contract["execution_gates"]["statistical_aggregation_fixture_validated"] is True
    assert contract["execution_gates"]["construction_enabled"] is False
    assert contract["execution_gates"]["split_generation_enabled"] is False
    assert contract["execution_gates"]["model_training_enabled"] is False
    assert contract["execution_gates"]["confirmatory_use_enabled"] is False


def test_negative_control_panels_are_not_pooled() -> None:
    contract = _contract()

    assert set(contract["conditions"]) == {
        "native",
        "genomic_gc_matched",
        "synthetic_shuffle",
        "cds_derived",
        "multi_negative",
    }
    assert contract["evaluation_matrix"]["concatenate_test_panels_for_one_mcc"] is False
    assert contract["statistics"]["across_panel_record_pairing_claimed"] is False


def test_multi_negative_weights_are_balanced_without_positive_duplication() -> None:
    condition = _contract()["conditions"]["multi_negative"]

    total_weight = (
        condition["positive_effective_weight"]
        + condition["negative_effective_weight"]
    )
    assert total_weight == 1.0
    assert condition["negative_family_weighting"] == "equal_across_available_families"
    assert condition["duplicate_positive_per_negative_family"] is False
