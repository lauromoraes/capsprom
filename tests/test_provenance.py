from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest

from capsprom.data.provenance import (
    inventory_legacy_tree,
    source_release_metadata,
    stage_legacy_inputs,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _acquired_tree(root: Path) -> dict:
    archive = root / "data/acquired/v1/site/bundle.zip"
    archive.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("pos.txt", "ACGT\n")
        handle.writestr("__MACOSX/._pos.txt", "junk")
    plain = root / "data/acquired/v1/site/neg.fa"
    plain.write_bytes(b">n\nTTTT\n")
    return {
        "acquisition": "v1",
        "config_sha256": "c" * 64,
        "files": {
            "site/bundle.zip": {"sha256": _sha(archive.read_bytes()), "size_bytes": 1},
            "site/neg.fa": {"sha256": _sha(plain.read_bytes()), "size_bytes": 1},
        },
    }


def test_legacy_inventory_classifies_files_and_never_infers_dates(tmp_path: Path) -> None:
    manifest = _acquired_tree(tmp_path)
    raw = tmp_path / "data/raw/Study"
    raw.mkdir(parents=True)
    (raw / "pos.txt").write_text("ACGT\n")  # same bytes as a zip member
    (raw / "neg.fa").write_text(">renamed\nTTTT\n")  # same sequence, other header
    (raw / "notes.txt").write_text("hand-written")
    genome = tmp_path / "data/raw/references/genome.fna"
    genome.parent.mkdir(parents=True)
    genome.write_text(">g\nACGT\n")
    (genome.parent / "manifest.json").write_text(
        f'{{"retrieved_utc": "2026-01-02T03:04:05+00:00", "files": {{"g": "{_sha(genome.read_bytes())}"}}}}'
    )
    canonical_config = {
        "collections": [
            {
                "collection_id": "study",
                "legacy_inputs": [
                    {"path": "data/raw/Study/neg.fa", "source_class": "negative"},
                ],
            }
        ]
    }
    canonical_manifest = {
        "config_sha256": "d" * 64,
        "collections": {"study": {"validation": {"legacy_sequence_match": {"negative": True}}}},
    }

    inventory = inventory_legacy_tree(
        tmp_path, Path("data/raw"), Path("data/acquired/v1"), manifest, canonical_config,
        canonical_manifest,
    )

    status = {item["path"]: item for item in inventory["files"]}
    assert status["data/raw/Study/pos.txt"]["byte_identical_to"] == ["site/bundle.zip!pos.txt"]
    assert status["data/raw/Study/neg.fa"]["status"] == "sequence_equivalent_to_acquisition"
    assert status["data/raw/Study/notes.txt"]["status"] == "not_reproduced_by_acquisition"
    assert all(
        status[path]["acquisition_date"]["status"] == "unknown"
        for path in ("data/raw/Study/pos.txt", "data/raw/Study/neg.fa", "data/raw/Study/notes.txt")
    )
    dated = status["data/raw/references/genome.fna"]["acquisition_date"]
    assert dated["status"] == "recorded" and dated["value"] == "2026-01-02T03:04:05+00:00"
    assert inventory["summary"]["Study"]["byte_identical_to_acquisition"] == 1


def test_source_release_metadata_separates_upstream_dates_from_acquisition() -> None:
    config = {
        "acquisition": {"name": "v1"},
        "sources": [
            {"source_id": "gh", "kind": "github_tree", "repository": "o/r", "commit": "a" * 40,
             "include": ["x"]},
            {"source_id": "site", "kind": "url_list", "release": 7,
             "files": [{"path": "f", "url": "https://example.test/f"}]},
        ],
    }
    commit = {
        "sha": "a" * 40,
        "html_url": "https://github.com/o/r/commit/" + "a" * 40,
        "commit": {"author": {"date": "2020-01-01T00:00:00Z"},
                   "committer": {"date": "2020-01-02T00:00:00Z"}},
    }
    record = source_release_metadata(
        config,
        fetch=lambda url: commit,
        head=lambda url, context: {"http_status": 200, "headers": {"last-modified": "x"}},
    )
    assert record["sources"]["gh"]["pinned_commit"]["committer_date"] == "2020-01-02T00:00:00Z"
    assert record["sources"]["site"]["declared"]["release"] == 7
    assert record["sources"]["site"]["files"]["f"]["headers"] == {"last-modified": "x"}
    assert "not acquisition dates" in record["interpretation"]


def test_stage_legacy_inputs_uses_contract_mapping(tmp_path: Path) -> None:
    _acquired_tree(tmp_path)
    acquired = tmp_path / "data/acquired/v1"
    config = {
        "collections": [
            {
                "collection_id": "study",
                "source": "study",
                "inputs": [
                    {"file": "site/bundle.zip", "member": "pos.txt", "source_class": "positive"},
                    {"file": "site/neg.fa", "source_class": "negative"},
                ],
                "legacy_inputs": [
                    {"path": "data/raw/Study/a_pos.txt", "source_class": "positive"},
                    {"path": "data/raw/Study/a_neg.fa", "source_class": "negative"},
                ],
            }
        ]
    }
    staged = stage_legacy_inputs(config, acquired, tmp_path / "stage", {"study"})
    assert (tmp_path / "stage/Study/a_pos.txt").read_text() == "ACGT\n"
    assert staged[0]["acquired_input"] == "site/bundle.zip!pos.txt"

    config["collections"][0]["inputs"].append({"file": "site/neg.fa", "source_class": "negative"})
    with pytest.raises(ValueError, match="ambiguous"):
        stage_legacy_inputs(config, acquired, tmp_path / "stage2", {"study"})


def test_experiment_links_accept_only_replayed_outputs(tmp_path: Path) -> None:
    from capsprom.data.provenance import link_experiment_records

    manifest = tmp_path / "filtering.json"
    manifest.write_text(
        '[{"study": "s", "organism_type": "o", "dataset": "d", '
        f'"train_output_sha256": "{"a" * 64}", "test_output_sha256": "{"b" * 64}"}}]'
    )
    replay = {
        "observed_at": "t",
        "datasets": [
            {"dataset": "s-o-d",
             "outputs_match": {"train_output_sha256": True, "test_output_sha256": False}}
        ],
    }
    run = tmp_path / "run.json"
    run.write_text(
        f'{{"train_dataset_sha256": "{"a" * 64}", "nested": [{{"test_sha256": "{"b" * 64}"}}]}}'
    )
    links = link_experiment_records([run], manifest, replay)
    assert links["records"][0]["replay_verified"] == ["s-o-d:train"]
    assert links["unlinked_dataset_hashes"] == ["b" * 64]
    assert links["fully_linked_records"] == 0
