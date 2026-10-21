"""Synthetic compute-feasibility measurements for frozen neural contracts."""

from __future__ import annotations

import json
import platform
import random
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psutil
import torch
import yaml

from .canonical_neural import _canonical_training_config, _mapping
from .neural_training import encode_one_hot, run_training_only
from .state import write_json_atomic


def run_feasibility_suite(config_path: Path) -> dict[str, Any]:
    """Run each synthetic scenario in an isolated process and write one report."""

    config_path = config_path.resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    protocol = _mapping(raw, "protocol")
    if protocol.get("canonical_jobs_enabled") is not False:
        raise ValueError("feasibility requires canonical_jobs_enabled=false")
    if protocol.get("embedding_jobs_enabled") is not False:
        raise ValueError("feasibility requires embedding_jobs_enabled=false")
    fixtures = _mapping(raw, "fixtures")
    scenarios = _mapping(fixtures, "scenarios")
    reporting = _mapping(raw, "reporting")
    root = config_path.parent.parent
    output_path = root / str(reporting["output"])
    results = []
    for name, rows in scenarios.items():
        command = [
            sys.executable,
            "-m",
            "capsprom.feasibility",
            "--scenario",
            str(config_path),
            str(name),
            str(int(rows)),
        ]
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
        wall_seconds = time.perf_counter() - started
        if completed.returncode != 0:
            results.append(
                {
                    "scenario": name,
                    "rows": int(rows),
                    "status": "failed",
                    "wall_seconds": wall_seconds,
                    "error": completed.stderr.strip()[-2000:],
                }
            )
            continue
        result = json.loads(completed.stdout)
        result["subprocess_wall_seconds"] = wall_seconds
        results.append(result)
    limit = float(_mapping(raw, "limits")["maximum_wall_seconds_per_scenario"])
    completed_results = [item for item in results if item["status"] == "completed"]
    large_result = max(completed_results, key=lambda item: item["rows"], default=None)
    campaign_projection = None
    plan_path = root / "outputs" / "capsprom_basic_canonical_v1" / "plan_state.json"
    if large_result is not None and plan_path.is_file():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        total_training_rows = sum(int(item["train_rows"]) for item in plan["datasets"])
        seeds = int(plan["seed_count"])
        folds = int(plan["fold_count"])
        # Across K folds, training partitions contain K-1 complete-dataset equivalents;
        # the final refit adds one more, for K equivalents per seed and epoch.
        row_epochs = total_training_rows * seeds * folds
        seconds_per_row_epoch = large_result["training_seconds"] / large_result["rows"]
        maximum_epochs = int(_mapping(yaml.safe_load(
            (root / str(protocol["canonical_config"])).read_text(encoding="utf-8")
        ), "training")["maximum_epochs"])
        campaign_projection = {
            "method": "linear extrapolation from large synthetic scenario",
            "row_epochs_per_campaign_epoch": row_epochs,
            "hours_per_campaign_epoch": row_epochs * seconds_per_row_epoch / 3600,
            "maximum_epoch_hours": row_epochs * seconds_per_row_epoch * maximum_epochs / 3600,
            "excludes": [
                "validation, checkpoint and process-launch overhead",
                "retry overhead",
                "parallel-worker contention or acceleration",
                "early stopping before the maximum epoch",
            ],
        }
    report = {
        "protocol": protocol["name"],
        "config_path": config_path.relative_to(root).as_posix(),
        "scope": "frozen one-hot basic CapsProm only",
        "hardware": _hardware_metadata(),
        "criteria": {
            "maximum_wall_seconds_per_scenario": limit,
            "out_of_memory": "infeasible",
            "nonzero_exit": "infeasible",
        },
        "results": results,
        "campaign_projection": campaign_projection,
        "feasible": all(
            item["status"] == "completed" and item["subprocess_wall_seconds"] <= limit
            for item in results
        ),
        "limitations": [
            "synthetic labels and sequences cannot estimate predictive or biological validity",
            "one epoch estimates per-epoch cost but not early-stopping variability",
            "peak RSS is process-level and includes the Python and PyTorch runtimes",
            "CPU and GPU measurements are hardware- and software-version-specific",
        ],
        "canonical_jobs_started": 0,
        "embedding_jobs_started": 0,
    }
    write_json_atomic(output_path, report)
    return report


def run_scenario(config_path: Path, scenario: str, rows: int) -> dict[str, Any]:
    """Run one scenario; intended for process-isolated resource measurement."""

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    fixtures = _mapping(raw, "fixtures")
    training = _mapping(raw, "training")
    canonical_path = config_path.parent.parent / str(
        _mapping(raw, "protocol")["canonical_config"]
    )
    canonical = yaml.safe_load(canonical_path.read_text(encoding="utf-8"))
    seed = int(fixtures["random_seed"])
    rng = random.Random(seed + rows)
    preparation_started = time.perf_counter()
    sequences = [
        "".join(rng.choices("ACGT", k=int(fixtures["sequence_length"])))
        for _ in range(rows)
    ]
    labels = [index % 2 for index in range(rows)]
    # Materialize the exact real input dtype and shape as part of preparation.
    probe = encode_one_hot(sequences, int(fixtures["sequence_length"]))
    input_shape = list(probe.shape)
    input_dtype = str(probe.dtype)
    del probe
    preparation_seconds = time.perf_counter() - preparation_started
    output_dir = config_path.parent.parent / "outputs" / "feasibility" / scenario
    config = _canonical_training_config(canonical, seed, output_dir)
    config = type(config)(
        **{
            **config.__dict__,
            "maximum_epochs": int(training["epochs"]),
            "patience": int(training["epochs"]),
            "batch_size": int(training["batch_size"]),
            "validation_fraction": float(training["validation_fraction"]),
            "contract_version": 7,
            "device": str(training["device"]),
        }
    )
    if config.state_path.exists():
        config.state_path.unlink()
    latest_checkpoint = config.checkpoint_path.with_name(
        f"{config.checkpoint_path.stem}.latest{config.checkpoint_path.suffix}"
    )
    for checkpoint in (config.checkpoint_path, latest_checkpoint):
        checkpoint.unlink(missing_ok=True)
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        torch.cuda.reset_peak_memory_stats()
    training_started = time.perf_counter()
    run_training_only(sequences, labels, config)
    training_seconds = time.perf_counter() - training_started
    peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "scenario": scenario,
        "rows": rows,
        "status": "completed",
        "preparation_seconds": preparation_seconds,
        "training_seconds": training_seconds,
        "input_shape": input_shape,
        "input_dtype": input_dtype,
        "sequence_length": int(fixtures["sequence_length"]),
        "representation": fixtures["representation"],
        "batch_size": config.batch_size,
        "epochs": config.maximum_epochs,
        "device": "cuda" if config.device == "auto" and gpu_available else config.device,
        "peak_rss_bytes": int(peak_rss_kib * 1024),
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()) if gpu_available else None,
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()) if gpu_available else None,
    }


def _hardware_metadata() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "logical_cpu_count": psutil.cpu_count(logical=True),
        "physical_cpu_count": psutil.cpu_count(logical=False),
        "ram_total_bytes": int(memory.total),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "--scenario":
        raise SystemExit("usage: python -m capsprom.feasibility --scenario CONFIG NAME ROWS")
    print(json.dumps(run_scenario(Path(sys.argv[2]), sys.argv[3], int(sys.argv[4]))))
