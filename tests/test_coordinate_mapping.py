import csv
import gzip
import hashlib
import json

import pytest
import yaml

from capsprom.data.coordinate_mapping import record_status, run_mapping
from capsprom.data.exact_mapping import reverse_complement

GENOME = "CCCC" + "ACGTTGCA" + "GGGG" + reverse_complement("TTTAAACC") + "AAAA" + "ACGTTGCA" + "CC"


def _canonical_row(index, sequence, collision="false"):
    return {
        "record_id": f"demo:file:{index:07d}", "collection_id": "demo", "organism": "Demo",
        "sequence": sequence, "sequence_sha1": hashlib.sha1(sequence.encode()).hexdigest(),
        "length": str(len(sequence)), "source_class": "positive", "label": "1",
        "original_header": f"h{index}", "cross_label_collision": collision,
    }


def _setup(tmp_path, evidence="declared"):
    canonical = tmp_path / "data/canonical/v1"
    canonical.mkdir(parents=True)
    rows = [_canonical_row(0, "TTTAAACC"), _canonical_row(1, "ACGTTGCA"), _canonical_row(2, "GATTACAG", "true"),
            _canonical_row(3, "ACGTNGCA")]
    with gzip.open(canonical / "demo.csv.gz", "wt", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256((canonical / "demo.csv.gz").read_bytes()).hexdigest()
    (canonical / "canonical_manifest.json").write_text(json.dumps({"collections": {"demo": {"output_sha256": digest}}}))
    acquired = tmp_path / "data/acquired/acq/src"
    acquired.mkdir(parents=True)
    with gzip.open(acquired / "G_genomic.fna.gz", "wt") as handle:
        handle.write(f">NC_1.1\n{GENOME}\n")
    reference = hashlib.sha256((acquired / "G_genomic.fna.gz").read_bytes()).hexdigest()
    (acquired.parent / "acquisition_manifest.json").write_text(
        json.dumps({"files": {"src/G_genomic.fna.gz": {"sha256": reference}}}))
    config = {
        "mapping": {"name": "demo-mapping", "canonical_root": "data/canonical/v1",
                    "canonical_manifest": "data/canonical/v1/canonical_manifest.json", "output_dir": "out"},
        "collections": [{"collection_id": "demo", "acquisition": "acq", "source_id": "src", "assembly": "GCF_1.1",
                         "assembly_evidence": evidence, "reference_file": "src/G_genomic.fna.gz"}],
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config))
    return path


def _read(path):
    with gzip.open(path, "rt", newline="") as handle:
        return list(csv.DictReader(handle))


def test_record_and_locus_tables(tmp_path):
    config = _setup(tmp_path)
    assert run_mapping(config, tmp_path) == {"built": ["demo"], "skipped": []}
    records = {row["record_id"][-1]: row for row in _read(tmp_path / "out/records/demo.csv.gz")}
    loci = _read(tmp_path / "out/loci/demo.csv.gz")
    assert records["0"]["status"] == "verified" and records["0"]["n_candidates"] == "1"
    assert records["1"]["status"] == "ambiguous" and records["1"]["n_candidates"] == "2"
    assert records["2"]["status"] == "unmapped" and records["2"]["status_reason"] == "no_candidate;label_conflict"
    assert records["3"]["status"] == "not_evaluated" and records["3"]["status_reason"] == "ambiguous_bases"
    minus = next(row for row in loci if row["record_id"].endswith("0"))
    assert (minus["start"], minus["end"], minus["strand"]) == ("16", "24", "-")
    assert len(loci) == 3


def test_rerun_skips_and_outputs_are_byte_identical(tmp_path):
    config = _setup(tmp_path)
    run_mapping(config, tmp_path)
    first = (tmp_path / "out/records/demo.csv.gz").read_bytes()
    assert run_mapping(config, tmp_path) == {"built": [], "skipped": ["demo"]}
    (tmp_path / "out/records/demo.csv.gz").unlink()
    assert run_mapping(config, tmp_path)["built"] == ["demo"]
    assert (tmp_path / "out/records/demo.csv.gz").read_bytes() == first
    manifest = json.loads((tmp_path / "out/mapping_manifest.json").read_text())
    assert len(manifest["runs"]) == 3


def test_inferred_assembly_makes_single_hit_inconsistent():
    assert record_status(1, "inferred", False) == ("inconsistent", ["assembly_mismatch"])
    assert record_status(1, "declared", False) == ("verified", [])
    assert record_status(1, "conflicting", True) == ("inconsistent", ["assembly_conflicting", "label_conflict"])


def test_failed_run_is_recorded(tmp_path):
    config = _setup(tmp_path)
    with gzip.open(tmp_path / "data/acquired/acq/src/G_genomic.fna.gz", "wt") as handle:
        handle.write(">NC_1.1\nACGT\n")
    with pytest.raises(ValueError, match="reference changed"):
        run_mapping(config, tmp_path)
    manifest = json.loads((tmp_path / "out/mapping_manifest.json").read_text())
    assert manifest["runs"][-1]["status"] == "failed"
