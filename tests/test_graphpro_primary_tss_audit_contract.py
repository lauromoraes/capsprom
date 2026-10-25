from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "graphpro_primary_tss_sample_audit_v1.yaml"


def test_primary_tss_sample_is_frozen_without_execution() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))

    assert contract["sampling"]["rows_per_dataset"] == 10
    assert contract["sampling"]["selection"] == "lowest_sha256_rank"
    assert contract["sampling"]["strand_stratification"]["enabled"] is True
    assert len(contract["datasets"]) == 5
    assert contract["coordinate_comparison"]["tolerate_unexplained_offset_nt"] == 0
    assert contract["execution_gates"]["sample_selection_enabled"] is True
    assert contract["execution_gates"]["coordinate_comparison_enabled"] is False
    assert contract["execution_gates"]["graphpro_manual_source_audit_complete"] is False
    assert contract["execution_gates"]["eligibility_update_enabled"] is False


def test_rhodobacter_alternative_is_not_substituted() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    excluded = contract["excluded_from_this_audit"][0]

    assert excluded["dataset_id"] == "graphpro-reconstructed-rhodobacter_capsulatus"
    assert excluded["later_resource"] == "GSE117537"
    assert excluded["later_resource_rows"] == 4045
    assert excluded["policy"] == "audit_separately_do_not_substitute"
