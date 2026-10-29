import gzip
import hashlib
import json
import zipfile
from pathlib import Path

import pytest
import yaml

from capsprom.data.acquisition import (
    acquire_sources,
    file_digests,
    load_acquisition_config,
    resolve_github_tree,
)
from capsprom.data.canonical_sources import (
    build_collection_rows,
    canonicalize_sources,
    ipro_source_class,
    load_canonicalization_config,
    normalize_sequence,
    parse_fasta,
    write_canonical_csv_gz,
)


ROOT = Path(__file__).resolve().parents[1]
ACQUISITION = ROOT / "configs" / "source_acquisition_v1.yaml"
CANONICALIZATION = ROOT / "configs" / "source_canonicalization_v1.yaml"


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def test_file_digests_reproduce_git_blob_sha1(tmp_path: Path) -> None:
    path = tmp_path / "hello.txt"
    path.write_bytes(b"hello\n")

    digests = file_digests(path)

    assert digests["git_blob_sha1"] == "ce013625030ba8dba906f756967f9e9ca394464a"
    assert digests["size_bytes"] == 6


def test_real_acquisition_config_pins_every_github_commit() -> None:
    config = load_acquisition_config(ACQUISITION)
    ids = [source["source_id"] for source in config["sources"]]

    assert len(ids) == len(set(ids))
    assert {s["kind"] for s in config["sources"]} == {"github_tree", "url_list"}
    for source in config["sources"]:
        if source["kind"] == "github_tree":
            assert len(source["commit"]) == 40


def test_acquisition_config_rejects_branch_names(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "acquisition": {"name": "x", "root": "r"},
                "sources": [
                    {"source_id": "a", "kind": "github_tree", "repository": "o/r", "commit": "main",
                     "include": ["x"]}
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="40-hex"):
        load_acquisition_config(path)


def _tree(*paths: str) -> dict:
    return {
        "truncated": False,
        "tree": [{"path": p, "type": "blob", "sha": _git_blob(p.encode())} for p in paths]
        + [{"path": "Datasets", "type": "tree", "sha": "0" * 40}],
    }


def test_github_tree_resolution_filters_prefixes_and_quotes_urls() -> None:
    source = {
        "source_id": "repo",
        "repository": "owner/repo",
        "commit": "a" * 40,
        "include": ["Benchmark Dataset", "README.md"],
        "exclude": ["Benchmark Dataset/skip.txt"],
    }
    tree = _tree("Benchmark Dataset/Train/1.txt", "Benchmark Dataset/skip.txt", "README.md", "big.bin")

    files = resolve_github_tree(source, lambda url: tree)

    assert [f.path for f in files] == ["Benchmark Dataset/Train/1.txt", "README.md"]
    assert files[0].url.endswith(f"{'a' * 40}/Benchmark%20Dataset/Train/1.txt")
    assert files[0].expected == {"git_blob_sha1": _git_blob(b"Benchmark Dataset/Train/1.txt")}


def test_github_tree_resolution_rejects_unmatched_include_and_truncation() -> None:
    source = {"source_id": "repo", "repository": "o/r", "commit": "a" * 40, "include": ["missing"]}

    with pytest.raises(ValueError, match="matched no files"):
        resolve_github_tree(source, lambda url: _tree("README.md"))
    with pytest.raises(ValueError, match="truncated"):
        resolve_github_tree(source, lambda url: {"truncated": True, "tree": []})


def _write_url_config(path: Path, expected: dict | None = None) -> None:
    entry = {"path": "data/file.txt", "url": "https://example.test/file.txt"}
    if expected:
        entry["expected"] = expected
    path.write_text(
        yaml.safe_dump(
            {
                "acquisition": {"name": "test-acquisition", "root": "acquired"},
                "sources": [{"source_id": "site", "kind": "url_list", "files": [entry]}],
            }
        ),
        encoding="utf-8",
    )


def test_acquisition_is_resumable_and_records_digests(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    _write_url_config(config, {"md5": hashlib.md5(b"ACGT\n").hexdigest()})
    root, manifest = tmp_path / "acquired", tmp_path / "acquired" / "manifest.json"
    calls: list[str] = []

    def download(url: str, destination: Path, context: object) -> dict[str, str]:
        calls.append(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"ACGT\n")
        return {"last-modified": "Tue, 01 Jan 2019 00:00:00 GMT"}

    first = acquire_sources(
        config, root, manifest, execute=True, download=download, command=["acquire", "--execute"]
    )
    second = acquire_sources(config, root, manifest, execute=True, download=download)

    payload = json.loads(manifest.read_text())
    recorded = payload["files"]["site/data/file.txt"]
    assert first["downloaded"] == 1 and second["skipped_verified"] == 1
    assert calls == ["https://example.test/file.txt"]
    assert recorded["sha256"] == hashlib.sha256(b"ACGT\n").hexdigest()
    assert recorded["verified_against"] == ["md5"]
    assert recorded["response_headers"] == {"last-modified": "Tue, 01 Jan 2019 00:00:00 GMT"}
    assert recorded["acquired_at"].endswith("+00:00")
    runs = payload["runs"]
    assert [run["status"] for run in runs] == ["completed", "completed"]
    assert runs[0]["command"] == ["acquire", "--execute"]
    assert runs[1]["summary"]["skipped_verified"] == 1
    assert {"python", "code", "module_sha256"} <= set(runs[0]["tool"])


def test_acquisition_rejects_digest_mismatch_and_changed_config(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    _write_url_config(config, {"sha256": "0" * 64})
    root, manifest = tmp_path / "acquired", tmp_path / "acquired" / "manifest.json"

    def download(url: str, destination: Path, context: object) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"other")

    with pytest.raises(ValueError, match="digest mismatch"):
        acquire_sources(config, root, manifest, execute=True, download=download)
    assert not (root / "site" / "data" / "file.txt").exists()
    failed_run = json.loads(manifest.read_text())["runs"][-1]
    assert failed_run["status"] == "failed" and "digest mismatch" in failed_run["error"]

    _write_url_config(config)
    with pytest.raises(ValueError, match="different config"):
        acquire_sources(config, root, manifest, execute=False, download=download)


def test_fasta_parsing_joins_wrapped_lines_and_rejects_headerless_data() -> None:
    records = list(parse_fasta(">a desc\nAC GT\r\nnn\n\n>b\nA\n"))

    assert records == [("a desc", "ACGTnn"), ("b", "A")]
    with pytest.raises(ValueError, match="before the first FASTA header"):
        list(parse_fasta("ACGT\n>a\nA\n"))


def test_ipro_classes_and_normalization() -> None:
    assert ipro_source_class("Escherichia coli str K-12 substr. MG1655--7") == "positive"
    assert ipro_source_class("Escherichia coli str K-12 substr. MG1655 CDS--7") == "negative_cds"
    assert ipro_source_class("Acinetobacter baumannii ATCC 17978 Convergent--93") == "negative_intergenic"
    assert normalize_sequence(" acgN\n") == ("ACGN", True, "N")


def _write_fixture_repo(tmp_path: Path, legacy_negative: str = ">x\nAAAA\n") -> Path:
    acquired = tmp_path / "data" / "acquired"
    (acquired / "src").mkdir(parents=True)
    (acquired / "src" / "pos.fa").write_text(">p1\nACGT\n>p2\nACGT\n>p3\nAAAA\n>p4\nACN\n")
    with zipfile.ZipFile(acquired / "src" / "neg.zip", "w") as archive:
        archive.writestr("neg.txt", "AAAA\nGGGG\n")
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "raw" / "neg.fa").write_text(legacy_negative + ">y\nGGGG\n")
    manifest = {
        "files": {
            key: {"sha256": file_digests(acquired / key)["sha256"]} for key in ("src/pos.fa", "src/neg.zip")
        }
    }
    (acquired / "manifest.json").write_text(json.dumps(manifest))
    config = {
        "canonicalization": {
            "name": "test-canonicalization",
            "acquisition_manifest": "data/acquired/manifest.json",
            "acquired_root": "data/acquired",
            "output_dir": "data/canonical",
        },
        "collections": [
            {
                "collection_id": "toy",
                "source": "src",
                "domain": "prokaryotic",
                "organism": "Toy organism",
                "expected_length": 4,
                "publication_counts": {"positive": 5},
                "inputs": [
                    {"file": "src/pos.fa", "format": "fasta", "source_class": "positive", "label": 1,
                     "expected_records": 4, "tss_index": 2},
                    {"file": "src/neg.zip", "member": "neg.txt", "format": "lines",
                     "source_class": "negative", "label": 0, "expected_records": 2},
                ],
                "legacy_inputs": [{"path": "data/raw/neg.fa", "format": "fasta", "source_class": "negative"}],
            }
        ],
    }
    path = tmp_path / "canonical.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_collection_rows_flag_duplicates_collisions_and_lengths(tmp_path: Path) -> None:
    config = load_canonicalization_config(_write_fixture_repo(tmp_path))
    rows = build_collection_rows(config["collections"][0], tmp_path / "data" / "acquired")
    by_header = {(row["source_class"], row["record_index"]): row for row in rows}

    assert by_header[("positive", 1)]["duplicate_of"] == "toy:src/pos.fa:0000000"
    assert by_header[("positive", 2)]["cross_label_collision"] is True
    assert by_header[("negative", 0)]["cross_label_collision"] is True
    assert by_header[("positive", 3)]["length_matches_expected"] is False
    assert by_header[("positive", 3)]["strict_dna"] is False
    assert by_header[("positive", 0)]["tss_index"] == 2
    assert by_header[("negative", 1)]["tss_index"] is None
    assert by_header[("negative", 1)]["record_id"] == "toy:src/neg.zip!neg.txt:0000001"


def test_canonical_csv_gz_is_byte_reproducible(tmp_path: Path) -> None:
    config = load_canonicalization_config(_write_fixture_repo(tmp_path))
    rows = build_collection_rows(config["collections"][0], tmp_path / "data" / "acquired")

    write_canonical_csv_gz(rows, tmp_path / "a.csv.gz")
    write_canonical_csv_gz(rows, tmp_path / "b.csv.gz")

    assert (tmp_path / "a.csv.gz").read_bytes() == (tmp_path / "b.csv.gz").read_bytes()
    header = gzip.decompress((tmp_path / "a.csv.gz").read_bytes()).decode().splitlines()[0]
    assert header.startswith("record_id,collection_id,source,")


def test_canonicalization_validates_counts_and_legacy_parity(tmp_path: Path) -> None:
    config = _write_fixture_repo(tmp_path)

    first = canonicalize_sources(config, tmp_path)
    second = canonicalize_sources(config, tmp_path)

    manifest = json.loads((tmp_path / "data" / "canonical" / "canonical_manifest.json").read_text())
    report = manifest["collections"]["toy"]["validation"]
    assert first["built"] == 1 and second["skipped_unchanged"] == 1
    assert report["status"] == "pass"
    assert report["records_by_class"] == {"negative": 2, "positive": 4}
    assert report["publication_count_discrepancies"] == {"positive": {"publication": 5, "release": 4}}
    assert report["legacy_sequence_match"] == {"negative": True}


def test_canonicalization_fails_on_legacy_mismatch(tmp_path: Path) -> None:
    config = _write_fixture_repo(tmp_path, legacy_negative=">x\nCCCC\n")

    summary = canonicalize_sources(config, tmp_path)

    assert summary["failed_validation"] == ["toy"]


def test_real_canonical_config_reads_only_declared_acquisition_sources() -> None:
    acquisition = load_acquisition_config(ACQUISITION)
    canonical = load_canonicalization_config(CANONICALIZATION)
    source_ids = {source["source_id"] for source in acquisition["sources"]}

    assert canonical["canonicalization"]["acquisition_config"] == "configs/source_acquisition_v1.yaml"
    for collection in canonical["collections"]:
        for item in collection["inputs"]:
            assert item["file"].split("/", 1)[0] in source_ids
    ipro = [c for c in canonical["collections"] if c["source"] == "ipro-mp"]
    assert len(ipro) == 23
    plant = next(c for c in canonical["collections"] if c["collection_id"] == "bhandari-nominal-plant")
    assert plant["organism"] == ""
