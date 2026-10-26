import hashlib
from pathlib import Path

import yaml

from scripts.consolidate_active_baselines import consolidate


def test_active_baseline_consolidation_excludes_graphpro() -> None:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "configs/active_baseline_consolidation_v1.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    for section, path_key, hash_key in (
        ("scope", "eligibility_manifest", "eligibility_manifest_sha256"),
        ("inputs", "completed_summary", "completed_summary_sha256"),
    ):
        path = root / config[section][path_key]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == config[section][hash_key]

    result = consolidate(config_path)

    assert result["dataset_count"] == 18
    assert result["included_sources"] == ["cdbprom", "cnnprom"]
    assert result["excluded_sources"] == ["graphpro"]
    assert all(not row["dataset"].startswith("graphpro-") for row in result["rows"])


def test_graphpro_deferral_keeps_every_execution_gate_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    policy = yaml.safe_load(
        (root / "configs/graphpro_deferral_policy_v1.yaml").read_text(encoding="utf-8")
    )

    assert policy["policy"]["mutates_existing_graphpro_contracts"] is False
    assert policy["scope"]["active_confirmatory_dataset_count"] == 18
    assert all(value is False for value in policy["execution_gates"].values())
