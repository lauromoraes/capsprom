import json
import subprocess
import sys
from pathlib import Path


def test_equivalence_harness_detects_exact_cpu_resume(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    output = tmp_path / "equivalence"
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/validate_gpu_resume_equivalence.py"),
            "--output-dir",
            str(output),
            "--device",
            "cpu",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads((output / "equivalence_report.json").read_text(encoding="utf-8"))

    assert report["passed"] is True
    assert report["observed"]["predictions_exactly_equal"] is True
    assert (
        report["observed"]["history_metric_max_absolute_difference"]
        <= report["tolerances"]["history_metric_absolute"]
    )
    assert (
        report["observed"]["model_parameter_max_absolute_difference"]
        <= report["tolerances"]["model_parameter_absolute"]
    )
    assert report["canonical_jobs_started"] == 0
    assert report["embedding_jobs_started"] == 0
