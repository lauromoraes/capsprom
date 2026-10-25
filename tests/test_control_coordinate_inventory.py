from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "configs" / "control_coordinate_feasibility_inventory_v1.yaml"


def _inventory() -> dict:
    return yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))


def test_coordinate_inventory_has_unique_declared_dataset_count() -> None:
    inventory = _inventory()
    datasets = inventory["datasets"]

    assert inventory["inventory"]["dataset_count"] == 29
    assert len(datasets) == 29
    assert len({row["dataset_id"] for row in datasets}) == len(datasets)
    assert {row["source_family"] for row in datasets} == {
        "bhandari",
        "cdbprom",
        "cnnprom",
        "graphpro_reconstructed",
    }


def test_coordinate_inventory_preserves_known_identity_conflict() -> None:
    datasets = {row["dataset_id"]: row for row in _inventory()["datasets"]}
    nominal_plant = datasets["bhandari-nominal-plant"]

    assert nominal_plant["observed_assembly"] == "mm10"
    assert nominal_plant["status"] == "insufficient_or_conflicting_identity"
    assert "resolve_plant_filename_vs_mouse_assembly_conflict" in nominal_plant["blockers"]


def test_inventory_completion_does_not_enable_execution() -> None:
    inventory = _inventory()
    gates = inventory["gates"]

    assert gates["inventory_complete"] is True
    assert gates["graphpro_bacterial_primary_row_sample_audit_complete"] is False
    assert gates["pilot_selection_enabled"] is False
    assert gates["control_construction_enabled"] is False
    assert inventory["pilot_candidates"]["currently_frozen"] is None
