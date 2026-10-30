"""Record provenance for the pinned acquisition, the legacy data tree, and legacy builds.

Records are written to a versioned directory under ``manifests/provenance/`` so
that they are reviewable in Git; bulky staging output stays under ignored
``data/interim/``.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

import yaml

from capsprom.data.acquisition import file_digests, load_acquisition_config
from capsprom.data.canonical_sources import load_canonicalization_config
from capsprom.data.provenance import (
    bhandari_history_record,
    classify_window_tss,
    inventory_legacy_tree,
    length_deviations,
    link_experiment_records,
    recreate_ucsc_ranges,
    replay_regenerated_v3,
    source_release_metadata,
    verify_label_csv_canonical,
)
from capsprom.state import write_json_atomic

ACQUISITION_CONFIG = Path("configs/source_acquisition_v1.yaml")
CANONICAL_CONFIG = Path("configs/source_canonicalization_v1.yaml")
RECORD_DIR = Path("manifests/provenance/source_acquisition_v1")
REPLAY_DIR = Path("data/interim/provenance_replay_regenerated_v3")
V3_FILTERING_MANIFEST = Path("data/processed/audits/real_negative_regenerated_v3/filtering_manifest.json")
BHANDARI_GENOMES = {"hg38": "hg38.2bit", "mm10": "mm10.2bit", "sacCer3": "sacCer3.2bit"}
BHANDARI_COLLECTIONS = ("bhandari-human", "bhandari-yeast", "bhandari-nominal-plant")
HISTORY_DIR = Path("data/acquired/bhandari_history_acquisition_v1/bhandari-github-history")
HISTORY_RECORD_DIR = Path("manifests/provenance/bhandari_history_acquisition_v1")
TAIR_DIR = Path("data/acquired/reference_acquisition_v6/ucsc-genark-tair10")
TAIR_ANNOTATION_DIR = Path("data/acquired/reference_acquisition_v8")


def _assembly_aliases() -> dict[str, str]:
    """Map Ensembl TAIR10 contig names to RefSeq accessions from the GCF_000001735.3 assembly report."""

    report = TAIR_ANNOTATION_DIR / "ncbi-tair10-gcf3/GCF_000001735.3_TAIR10_assembly_report.txt"
    aliases = {}
    for line in report.read_text(encoding="utf-8").splitlines():
        fields = line.split("	")
        if not line.startswith("#") and len(fields) > 6:
            aliases[fields[0]] = fields[6]
    aliases.update(Mt=aliases["MT"], Pt=aliases["Pltd"])
    return aliases


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "record",
        choices=[
            "snapshot",
            "source-metadata",
            "legacy-inventory",
            "replay-v3",
            "experiment-links",
            "length-deviations",
            "bhandari-recreation",
            "bhandari-history",
            "bhandari-history-canonical",
            "arabidopsis-tss",
        ],
    )
    args = parser.parse_args()

    acquisition = load_acquisition_config(ACQUISITION_CONFIG)
    canonical = load_canonicalization_config(CANONICAL_CONFIG)
    acquired_root = Path(acquisition["acquisition"]["root"])
    acquisition_manifest_path = acquired_root / "acquisition_manifest.json"
    canonical_manifest_path = Path(canonical["canonicalization"]["output_dir"]) / "canonical_manifest.json"

    if args.record == "snapshot":
        RECORD_DIR.mkdir(parents=True, exist_ok=True)
        for source in (acquisition_manifest_path, canonical_manifest_path):
            shutil.copyfile(source, RECORD_DIR / source.name)
        result: dict = {"copied": [acquisition_manifest_path.name, canonical_manifest_path.name]}
    elif args.record == "source-metadata":
        result = source_release_metadata(yaml.safe_load(ACQUISITION_CONFIG.read_text(encoding="utf-8")))
        write_json_atomic(RECORD_DIR / "source_release_metadata.json", result)
    elif args.record == "legacy-inventory":
        result = inventory_legacy_tree(
            Path("."),
            Path("data/raw"),
            acquired_root,
            _load_json(acquisition_manifest_path),
            canonical,
            _load_json(canonical_manifest_path),
        )
        write_json_atomic(RECORD_DIR / "legacy_raw_inventory.json", result)
        result = result["summary"]
    elif args.record == "experiment-links":
        result = link_experiment_records(
            sorted(Path("outputs").rglob("*.json")),
            V3_FILTERING_MANIFEST,
            _load_json(RECORD_DIR / "regenerated_v3_replay.json"),
        )
        write_json_atomic(RECORD_DIR / "experiment_dataset_links.json", result)
        result = {key: result[key] for key in ("record_count", "fully_linked_records")}
    elif args.record == "length-deviations":
        result = length_deviations(canonical_manifest_path.parent, _load_json(canonical_manifest_path))
        write_json_atomic(RECORD_DIR / "length_deviations.json", result)
        result = {key: result[key] for key in ("collection_count", "record_count")}
    elif args.record == "bhandari-recreation":
        canonical_dir = canonical_manifest_path.parent
        genomes = {name: acquired_root / "ucsc-genomes" / file for name, file in BHANDARI_GENOMES.items()}
        result = {
            collection: recreate_ucsc_ranges(canonical_dir / f"{collection}.csv.gz", genomes)
            for collection in BHANDARI_COLLECTIONS
        }
        write_json_atomic(RECORD_DIR / "bhandari_recreation.json", result)
        result = {
            collection: {key: value[key] for key in ("record_count", "identical_count")}
            for collection, value in result.items()
        }
    elif args.record == "arabidopsis-tss":
        annotations = {
            "genark_ncbiRefSeq_2025_06_09": TAIR_DIR / "GCF_000001735.4_TAIR10.1.ncbiRefSeq.gtf.gz",
            "ncbi_gcf4_gff_2023_06_16": TAIR_ANNOTATION_DIR / "ncbi-tair10-gcf4/GCF_000001735.4_TAIR10.1_genomic.gff.gz",
            "ncbi_gcf3_gff_2018_04_02": TAIR_ANNOTATION_DIR / "ncbi-tair10-gcf3/GCF_000001735.3_TAIR10_genomic.gff.gz",
            "ensembl_plants_31_tair10_2017_07_18": Path(
                "data/acquired/reference_acquisition_v9/ensembl-plants-31-athaliana/Arabidopsis_thaliana.TAIR10.31.gtf.gz"
            ),
        }
        summary, evidence = classify_window_tss(
            Path("data/canonical/bhandari_history_canonicalization_v1/bhandari-history-arabidopsis.csv.gz"),
            _load_json(Path("data/interim/bhandari_history/arabidopsis_loci.json")),
            annotations,
            aliases={"ensembl_plants_31_tair10_2017_07_18": _assembly_aliases()},
        )
        evidence_path = Path("data/interim/bhandari_history/arabidopsis_tss_evidence.csv")
        with evidence_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["record_id", "scope", "locus_count", *annotations])
            writer.writeheader()
            writer.writerows(evidence)
        summary["evidence_file"] = str(evidence_path)
        summary["evidence_sha256"] = file_digests(evidence_path)["sha256"]
        write_json_atomic(Path("manifests/provenance/bhandari_arabidopsis_tss_v1/tss_classification.json"), summary)
        result = {key: summary[key] for key in ("scope", "by_annotation", "exact_agreement_sets")}
    elif args.record == "bhandari-history-canonical":
        history_canonical = Path("data/canonical/bhandari_history_canonicalization_v1")
        drive_canonical = canonical_manifest_path.parent
        result = {
            collection: verify_label_csv_canonical(
                history_canonical / f"{collection}.csv.gz",
                HISTORY_DIR / name,
                f"bhandari-github-history/{name}",
                drive_canonical / f"{drive}.csv.gz",
            )
            for collection, name, drive in (
                ("bhandari-history-arabidopsis", "Promoter_ArabidopsisThaliana.csv", "bhandari-nominal-plant"),
                ("bhandari-history-human", "Promoter_Human.csv", "bhandari-human"),
                ("bhandari-history-yeast", "Promoter_Yeast.csv", "bhandari-yeast"),
            )
        }
        record_dir = Path("manifests/provenance/bhandari_history_canonicalization_v1")
        record_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(history_canonical / "canonical_manifest.json", record_dir / "canonical_manifest.json")
        write_json_atomic(record_dir / "canonical_verification.json", result)
    elif args.record == "bhandari-history":
        canonical_dir = canonical_manifest_path.parent
        history_files = {
            name: (HISTORY_DIR / name, canonical_dir / f"{collection}.csv.gz")
            for name, collection in (
                ("Promoter_ArabidopsisThaliana.csv", "bhandari-nominal-plant"),
                ("Promoter_Human.csv", "bhandari-human"),
                ("Promoter_Yeast.csv", "bhandari-yeast"),
            )
        }
        result = bhandari_history_record(
            history_files,
            HISTORY_DIR / "Promoter_ArabidopsisThaliana.csv",
            TAIR_DIR / "GCF_000001735.4.2bit",
            TAIR_DIR / "GCF_000001735.4_TAIR10.1.ncbiRefSeq.gtf.gz",
            Path("data/interim/bhandari_history/arabidopsis_loci.json"),
        )
        write_json_atomic(HISTORY_RECORD_DIR / "history_comparison.json", result)
        result = {key: result["arabidopsis_location"][key] for key in ("located_count", "unique_locus_count")}
    else:
        result = replay_regenerated_v3(
            canonical,
            acquired_root,
            REPLAY_DIR,
            V3_FILTERING_MANIFEST,
            Path("data/interim/fasta"),
            Path("data/processed/assembled_datasets/intra_regenerated_v3_strict_dna"),
        )
        write_json_atomic(RECORD_DIR / "regenerated_v3_replay.json", result)
        result = {key: result[key] for key in ("dataset_count", "all_datasets_match")}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
