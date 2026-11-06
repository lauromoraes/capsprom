import csv
from pathlib import Path

import pytest
import yaml

from capsprom.canonical_neural import prepare_canonical_neural_plan, run_canonical_inner_fold_job
from capsprom.data.homology_grouping import GroupingRecord, place_unique_windows
from capsprom.data.loading import sha256_file
from capsprom.data.pilot_panels import (
    check_group_safety,
    genomic_records,
    native_records,
    training_records,
    write_condition,
)

DATASET = "fixture-source-organism"
PARTITIONS = [f"train:{fold}" for fold in range(5) for _ in range(2)] + ["test", "test"]


def _sequence(index: int, shift: int = 0) -> str:
    bases = "ACGT"
    return "".join(bases[((index + shift + 1) * (i + 3) + i * i) % 4] for i in range(81))


def _grouped() -> list[dict[str, str]]:
    return [
        {
            "record_id": f"r{index}-{label}",
            "sequence": _sequence(index, label * 7),
            "label": str(label),
            "group": str(index * 10 + label),
            "partition": partition,
        }
        for index, partition in enumerate(PARTITIONS)
        for label in (1, 0)
    ]


def _ledger(native) -> list[dict[str, str]]:
    return [
        {
            "record_id": f"source:{record.record_id}",
            "native_record_id": record.record_id,
            "positive_sequence": record.sequence,
            "negative_sequence": _sequence(int(record.group) + 40, 3),
            "group": record.group,
            "partition": record.partition,
        }
        for record in native
        if record.label == 1
    ]


def _protocol(path: Path, fold_manifest_root: str, tracking_uri: str) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump(
            {
                "protocol": {
                    "name": "fixture",
                    "status": "design_locked_test_execution_blocked",
                    "dataset_root": fold_manifest_root,
                    "fold_manifest_root": fold_manifest_root,
                    "dataset_ids": [DATASET],
                },
                "selection": {
                    "method": "five_fold_then_full_refit",
                    "folds": 5,
                    "fold_seed": 42,
                    "epoch_rule": "lower_median_fold_best_epoch",
                },
                "replication": {"seeds": [13]},
                "model": {
                    "name": "capsprom_basic",
                    "input": {"encoding": "one_hot", "k": 1, "sequence_length": 81, "channels": 4},
                    "architecture": {
                        "convolution_filters": 8,
                        "convolution_kernel": 9,
                        "primary_channels": 2,
                        "primary_dim": 4,
                        "primary_kernel": 9,
                        "primary_stride": 2,
                        "output_capsules": 2,
                        "output_dim": 4,
                        "routing_iterations": 1,
                        "routing_mode": "dynamic",
                        "routing_gradient_mode": "final_iteration",
                        "decoder_mode": "disabled",
                    },
                },
                "training": {
                    "runner_contract_version": 6,
                    "device": "cpu",
                    "batch_size": 4,
                    "optimizer": "adam",
                    "learning_rate": 0.0001,
                    "learning_rate_schedule": "fixed",
                    "maximum_epochs": 1,
                    "patience": 1,
                    "reconstruction_weight": 0.0,
                },
                "prediction": {"decision": "raw_score_argmax"},
                "tracking": {
                    "backend": "mlflow",
                    "tracking_uri": tracking_uri,
                    "experiment_name": "fixture-pilot",
                },
                "execution_gates": {
                    "external_test_enabled": False,
                    "require_dataset_hashes": True,
                    "require_fold_manifest_hashes": True,
                    "require_fixture_validation": True,
                },
            }
        ),
        encoding="utf-8",
    )


def test_control_inherits_positive_group_and_partition() -> None:
    native = native_records(_grouped())
    panel = genomic_records(_ledger(native), native)
    assert len(panel) == 24
    positives = {r.record_id: r for r in panel if r.label == 1}
    for control in (r for r in panel if r.label == 0):
        parent = positives[control.record_id.removesuffix("|genomic-control")]
        assert (control.group, control.partition) == (parent.group, parent.partition)
        assert control.negative_family == "genomic_gc_matched"


def test_ledger_that_moves_a_positive_is_refused() -> None:
    native = native_records(_grouped())
    ledger = _ledger(native)
    ledger[0]["partition"] = "test"
    with pytest.raises(ValueError, match="differs from the native build"):
        genomic_records(ledger, native)


def test_group_across_partitions_is_refused() -> None:
    rows = _grouped()
    rows[0]["group"] = rows[-1]["group"]
    with pytest.raises(ValueError, match="span partitions"):
        check_group_safety(native_records(rows))


def test_training_records_never_return_test_rows() -> None:
    assert all(r.partition != "test" for r in training_records(native_records(_grouped())))


def test_condition_files_keep_test_apart_and_are_immutable(tmp_path: Path) -> None:
    native = native_records(_grouped())
    names = write_condition(native, tmp_path / "native", "pilot.native")
    with (tmp_path / "native" / names["train"]).open(encoding="utf-8", newline="") as handle:
        train = list(csv.DictReader(handle))
    with (tmp_path / "native" / names["test"]).open(encoding="utf-8", newline="") as handle:
        test = list(csv.DictReader(handle))
    assert len(train) == 20 and len(test) == 4
    assert not {r["record_id"] for r in train} & {r["record_id"] for r in test}
    with pytest.raises(FileExistsError):
        write_condition(native, tmp_path / "native", "pilot.native")


def test_runner_uses_inherited_group_folds_and_runs_one_fold(tmp_path: Path) -> None:
    native = native_records(_grouped())
    root = tmp_path / "data" / "fixture"
    names = write_condition(genomic_records(_ledger(native), native), root, DATASET)
    config = tmp_path / "configs" / "protocol.yaml"
    _protocol(config, "data/fixture", f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}")
    output = tmp_path / "out"
    state = prepare_canonical_neural_plan(config, output)
    written = (output / state["datasets"][0]["fold_manifest"]).read_bytes()
    assert written == (root / names["fold_manifest"]).read_bytes()
    job = run_canonical_inner_fold_job(config, output, DATASET, 13, 0)
    assert job["status"] == "completed"


def test_runner_refuses_inherited_folds_that_miss_rows(tmp_path: Path) -> None:
    root = tmp_path / "data" / "fixture"
    names = write_condition(native_records(_grouped()), root, DATASET)
    manifest = root / names["fold_manifest"]
    lines = manifest.read_text(encoding="utf-8").splitlines(True)
    manifest.write_text("".join(lines[:-1]), encoding="utf-8")
    config = tmp_path / "configs" / "protocol.yaml"
    _protocol(config, "data/fixture", f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}")
    with pytest.raises(ValueError, match="cover the training rows"):
        prepare_canonical_neural_plan(config, tmp_path / "out")


def test_pilot_contract_keeps_training_blocked_and_pins_inherited_contracts() -> None:
    contract = yaml.safe_load(Path("configs/cnnprom_ecoli_pilot_training_v2.yaml").read_text(encoding="utf-8"))
    gates = contract["execution_gates"]
    assert not any(gates[name] for name in gates if name != "group_fold_integration_fixture_validated")
    assert contract["contract"]["confirmatory_use_enabled"] is False
    inherited = contract["inherits"]
    for key, path in inherited.items():
        # Restricted originals are absent from a clean clone.
        if f"{key}_sha256" in inherited and Path(path).exists():
            assert sha256_file(Path(path)) == inherited[f"{key}_sha256"]


def test_only_unique_windows_get_coordinates_on_either_strand() -> None:
    genome = "AAACCCGGGTTTACGTACGTGGGCCCAAA" + "TTGCA" + "CATCAT" + "TTTT" + "CATCAT"
    forward = GroupingRecord("forward", "GTACGTGG", 1, "forward")
    reverse = GroupingRecord("reverse", "TGCAA", 1, "reverse")
    repeated = GroupingRecord("repeated", "CATCAT", 1, "repeated")
    absent = GroupingRecord("absent", "GATTACA", 0, "absent")
    placed = {r.record_id: r for r in place_unique_windows([forward, reverse, repeated, absent], "c", genome)}
    assert genome[placed["forward"].start : placed["forward"].end] == "GTACGTGG"
    assert genome[placed["reverse"].start : placed["reverse"].end] == "TTGCA"
    assert placed["repeated"].contig is None and placed["absent"].contig is None
