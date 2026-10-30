from __future__ import annotations

import gzip
import hashlib
import json
import struct
import zipfile
from pathlib import Path

import pytest

from capsprom.data.provenance import (
    classify_window_tss,
    inventory_legacy_tree,
    length_deviations,
    locate_exact_sequences,
    recreate_ucsc_ranges,
    source_release_metadata,
    spec_deviation_patterns,
    stage_legacy_inputs,
    uncovered_deviations,
    verify_label_csv_canonical,
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


def _write_canonical(path: Path, rows: list[tuple[str, str, int, str]]) -> None:
    header = "record_id,source_class,length,length_matches_expected\n"
    body = "".join(f"{rid},{cls},{length},{match}\n" for rid, cls, length, match in rows)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(header + body)


def test_length_deviations_lists_only_declared_mismatches(tmp_path: Path) -> None:
    _write_canonical(
        tmp_path / "a.csv.gz",
        [("a:1", "positive", 10, "true"), ("a:2", "positive", 9, "false"), ("a:3", "negative", 7, "false")],
    )
    _write_canonical(tmp_path / "b.csv.gz", [("b:1", "positive", 10, "true"), ("b:2", "positive", 4, "")])

    record = length_deviations(tmp_path, {"config_sha256": "e" * 64})

    assert record["record_count"] == 2
    assert list(record["collections"]) == ["a"]
    assert record["collections"]["a"]["positive"] == {"count": 1, "records": [{"record_id": "a:2", "length": 9}]}
    assert "sequence" not in json.dumps(record)


def test_spec_table_covers_generated_deviations_both_ways() -> None:
    spec = Path("specs/dataset_integrity_audit.md").read_text(encoding="utf-8")
    patterns = spec_deviation_patterns(spec)
    record = json.loads(
        Path("manifests/provenance/source_acquisition_v1/length_deviations.json").read_text(encoding="utf-8")
    )

    assert "bhandari-human" in patterns
    assert uncovered_deviations(record, patterns) == {"missing_from_spec": [], "stale_in_spec": []}


def test_uncovered_deviations_reports_gaps_in_both_directions() -> None:
    record = {"collections": {"x-1": {}, "y-1": {}}}

    assert uncovered_deviations(record, ["x-*", "z-1"]) == {"missing_from_spec": ["y-1"], "stale_in_spec": ["z-1"]}


def _write_twobit(path: Path, contigs: dict[str, str]) -> None:
    """Write an unmasked twoBit file without N blocks."""

    codes = {base: index for index, base in enumerate("TCAG")}
    index_size = sum(1 + len(name) + 4 for name in contigs)
    blobs, offset = [], 16 + index_size
    for sequence in contigs.values():
        packed = bytearray((len(sequence) + 3) // 4)
        for position, base in enumerate(sequence):
            packed[position // 4] |= codes[base] << (6 - 2 * (position % 4))
        blob = struct.pack(">IIII", len(sequence), 0, 0, 0) + bytes(packed)
        blobs.append((offset, blob))
        offset += len(blob)
    with path.open("wb") as handle:
        handle.write(struct.pack(">IIII", 0x1A412743, 0, len(contigs), 0))
        for (name, _), (blob_offset, _) in zip(contigs.items(), blobs, strict=True):
            handle.write(bytes([len(name)]) + name.encode("ascii") + struct.pack(">I", blob_offset))
        for _, blob in blobs:
            handle.write(blob)


def _write_headers(path: Path, rows: list[tuple[str, str, str]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        handle.write("record_id,original_header,sequence\n")
        handle.write("".join(f"{rid},{header},{sequence}\n" for rid, header, sequence in rows))


def test_recreate_ucsc_ranges_reads_one_based_closed_intervals(tmp_path: Path) -> None:
    genome = tmp_path / "g.2bit"
    _write_twobit(genome, {"chr1": "AACCGGTTAC"})
    table = tmp_path / "t.csv.gz"
    _write_headers(
        table,
        [
            ("t:0", "mm10_x range=chr1:3-6 5'pad=0 strand=+", "CCGG"),
            ("t:1", "mm10_x range=chr1:1-4 strand=-", "GGTT"),
            ("t:2", "mm10_x range=chr1:1-4 strand=+", "AAAA"),
            ("t:3", "hg38_x range=chr1:1-4 strand=+", "AACC"),
            ("t:4", "mm10_x range=chrZ:1-4 strand=+", "AACC"),
        ],
    )

    record = recreate_ucsc_ranges(table, {"mm10": genome})

    assert record["record_count"] == 5
    assert record["identical_count"] == 2
    assert record["failures"]["sequence_differs"]["record_ids"] == ["t:2"]
    assert record["failures"]["undeclared_assembly"]["record_ids"] == ["t:3"]
    assert record["failures"]["missing_contig"]["record_ids"] == ["t:4"]
    assert "CCGG" not in json.dumps(record)


def test_locate_exact_sequences_finds_both_strands_and_rejects_partial_matches(tmp_path: Path) -> None:
    genome = tmp_path / "g.2bit"
    _write_twobit(genome, {"c1": "TTTTACGTACCGGATTTT", "c2": "GGGGGG"})
    sequences = {"fwd": "ACGTACCGGA", "rev": "TCCGGTACGT", "partial": "ACGTACCGGC", "short": "AC"}

    record = locate_exact_sequences(sequences, genome, anchor_size=4)

    assert record["loci"]["fwd"] == [{"contig": "c1", "start": 4, "strand": "+"}]
    assert record["loci"]["rev"] == [{"contig": "c1", "start": 4, "strand": "-"}]
    assert record["not_located"] == ["partial"]
    assert record["unanchored"] == ["short"]


def test_verify_label_csv_canonical_rebuilds_source_bytes(tmp_path: Path) -> None:
    source = tmp_path / "p.csv"
    source.write_bytes(b"P,ACGT\r\nP,ACGT\r\nP,AANT\r\n")
    table = tmp_path / "c.csv.gz"
    with gzip.open(table, "wt", encoding="utf-8", newline="") as handle:
        handle.write("record_id,collection_id,record_index,original_header,sequence,sequence_sha1,"
                     "case_normalized,strict_dna,duplicate_of\n")
        for index, (sequence, strict, dup) in enumerate((("ACGT", "true", ""), ("ACGT", "true", "c:s:0000000"),
                                                         ("AANT", "false", ""))):
            sha = hashlib.sha1(sequence.encode()).hexdigest()
            handle.write(f"c:s:{index:07d},c,{index},P,{sequence},{sha},false,{strict},{dup}\n")

    record = verify_label_csv_canonical(table, source, "s")

    assert record["rebuilt_equals_source_bytes"] and record["record_ids_contiguous"]
    assert record["sequence_sha1_valid"]
    assert (record["duplicate_records"], record["non_strict_dna_records"], record["unique_sequences"]) == (1, 1, 2)


def test_classify_window_tss_uses_strand_specific_coordinates(tmp_path: Path) -> None:
    gtf = tmp_path / "a.gtf.gz"
    with gzip.open(gtf, "wt", encoding="utf-8") as handle:
        handle.write("c\tx\ttranscript\t708\t900\t.\t+\t.\tid\n")  # TSS 708 on +
        handle.write("c\tx\ttranscript\t100\t1295\t.\t-\t.\tid\n")  # TSS 1295 on -
    table = tmp_path / "t.csv.gz"
    with gzip.open(table, "wt", encoding="utf-8", newline="") as handle:
        handle.write("record_id,source_file,record_index,length\n")
        handle.write("r:0,f/p.csv,0,1000\nr:1,f/p.csv,1,1000\nr:2,f/p.csv,2,1000\nr:3,f/p.csv,3,9\n")
    loci = {
        "p.csv:0": [{"contig": "c", "start": 7, "strand": "+"}],  # index 700 -> 708: exact
        "p.csv:1": [{"contig": "c", "start": 995, "strand": "-"}],  # 995 + 1000 - 700 = 1295: exact
        "p.csv:3": [{"contig": "c", "start": 0, "strand": "+"}],
    }

    summary, evidence = classify_window_tss(table, loci, {"a": gtf})

    assert [row["a"] for row in evidence[:2]] == ["exact:0", "exact:0"]
    assert summary["scope"] == {"evaluated": 2, "not_located": 1, "not_full_length": 1}
