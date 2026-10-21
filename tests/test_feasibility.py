from pathlib import Path

import yaml

from capsprom.feasibility import run_scenario


def test_synthetic_feasibility_uses_real_input_shape_and_frozen_model(tmp_path: Path) -> None:
    project = tmp_path / "project"
    configs = project / "configs"
    configs.mkdir(parents=True)
    canonical = yaml.safe_load(
        (Path(__file__).parents[1] / "configs" / "capsprom_basic_canonical_v1.yaml").read_text()
    )
    canonical["model"]["architecture"].update(
        convolution_filters=8, primary_channels=2, primary_dim=4,
        output_dim=4, routing_iterations=1,
    )
    (configs / "canonical.yaml").write_text(yaml.safe_dump(canonical), encoding="utf-8")
    feasibility = {
        "protocol": {
            "name": "fixture", "canonical_config": "configs/canonical.yaml",
            "canonical_jobs_enabled": False, "embedding_jobs_enabled": False,
        },
        "fixtures": {
            "random_seed": 7, "sequence_length": 81, "alphabet": list("ACGT"),
            "representation": "one_hot_k1_float32", "class_balance": "alternating_binary",
            "scenarios": {"small": 20},
        },
        "training": {"epochs": 1, "batch_size": 4, "validation_fraction": 0.2, "device": "auto"},
        "limits": {"maximum_wall_seconds_per_scenario": 60},
        "reporting": {"output": "outputs/report.json"},
    }
    path = configs / "feasibility.yaml"
    path.write_text(yaml.safe_dump(feasibility), encoding="utf-8")

    result = run_scenario(path, "small", 20)

    assert result["status"] == "completed"
    assert result["input_shape"] == [20, 81, 4]
    assert result["input_dtype"] == "torch.float32"
    assert result["epochs"] == 1
    assert result["peak_rss_bytes"] > 0
