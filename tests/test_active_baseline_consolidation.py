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


def test_graphpro_resumption_keeps_training_and_confirmatory_gates_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    policy = yaml.safe_load(
        (root / "configs/graphpro_deferral_policy_v2.yaml").read_text(encoding="utf-8")
    )

    assert policy["policy"]["supersedes"] == "configs/graphpro_deferral_policy_v1.yaml"
    assert policy["policy"]["mutates_existing_graphpro_contracts"] is False
    assert policy["execution_gates"]["graphpro_training_enabled"] is False
    assert policy["execution_gates"]["graphpro_confirmatory_use_enabled"] is False
    assert policy["requirements"]["tss_exclusion_radius_nt"] == {
        "prokaryota": 100,
        "eukaryota": 250,
    }
    assert policy["scope"]["organisms"]["ecol"]["status"] == "excluded"


def test_graphpro_v3_contract_is_bound_to_hashed_sources_and_stays_blocked() -> None:
    root = Path(__file__).resolve().parents[1]
    contract = yaml.safe_load(
        (root / "configs/graphpro_reconstruction_v3.yaml").read_text(encoding="utf-8")
    )
    acquisition = yaml.safe_load(
        (root / contract["reference"]["acquisition"]).read_text(encoding="utf-8")
    )
    reference_ids = {source["source_id"] for source in acquisition["sources"]}

    assert all(value is False for value in contract["execution_gates"].values())
    assert contract["reconstruction"]["reuses_v2_sequences_controls_or_split"] is False
    assert contract["negative_policy"]["exclusion_set"] == "complete_primary_tss_table_all_classes"
    assert contract["negative_policy"]["exclusion_radius_nt"] == 100
    assert contract["grouping_and_split"]["protocol"] == "configs/homology_grouping_v1.yaml"
    assert {item["declared_positives"] for item in contract["organisms"]} == {855, 571, 5143}
    for organism in contract["organisms"]:
        assert organism["reference_source_id"] in reference_ids
        table = organism["primary_table"]
        path = root / table["path"]
        if path.exists():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == table["sha256"]


def test_dependency_manifest_v4_adds_graphpro_v3_candidates_without_changing_eligible_clusters() -> None:
    root = Path(__file__).resolve().parents[1]
    v3 = yaml.safe_load((root / "configs/dataset_dependency_manifest_v3.yaml").read_text(encoding="utf-8"))
    v4 = yaml.safe_load((root / "configs/dataset_dependency_manifest_v4.yaml").read_text(encoding="utf-8"))
    old = {d["dataset_id"]: d["dependency_cluster_id"] for d in v3["datasets"]}
    new = {d["dataset_id"]: d["dependency_cluster_id"] for d in v4["datasets"]}
    candidates = [d for d in v4["datasets"] if d.get("status") == "candidate_pending_eligibility"]

    assert {k: new[k] for k in old} == old
    assert len(new) == v4["manifest"]["dataset_count"] == 21
    assert len(set(new.values())) == v4["manifest"]["dependency_cluster_count"] == 14
    assert len(candidates) == v4["manifest"]["candidate_dataset_count"] == 3
    assert new["graphpro-reconstructed-v3-prokaryotic-chlamydophila_pneumoniae"] == "cdbprom-chlamydophila"
