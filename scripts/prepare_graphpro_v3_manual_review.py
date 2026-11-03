"""Select the frozen manual-review sample of graphpro-reconstructed-v3 and write the review sheet.

The sheet lists, per sampled pair, the coordinates and sequences to check and
NCBI links to the reference intervals, with empty verdict columns (A–E of the
review contract).  It reads build outputs only and refuses to overwrite an
existing sheet, so the sample cannot change after review starts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import yaml

from capsprom.data.loading import sha256_file

OUTPUT = Path("docs/provenance/manual_review_graphpro_v3/review_sheet.csv")


def ncbi(accession: str, start0: int, end0: int, strand: str) -> str:
    link = f"https://www.ncbi.nlm.nih.gov/nuccore/{accession}?report=fasta&from={start0 + 1}&to={end0}"
    return link + ("&strand=2" if strand == "-" else "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/graphpro_v3_manual_review_v1.yaml"))
    args = parser.parse_args()
    if OUTPUT.exists():
        raise FileExistsError(f"{OUTPUT} exists; the review sample is frozen")
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    sampling = config["sampling"]
    rows = []
    for dataset in config["datasets"]:
        ledger = Path(dataset["ledger"])
        if sha256_file(ledger.with_name("build_manifest.json")) != dataset["manifest_sha256"]:
            raise ValueError(f"build manifest hash mismatch for {dataset['collection_id']}")
        pairs = list(csv.DictReader(ledger.open(encoding="utf-8")))
        partition = {r["record_id"]: r["partition"] for r in csv.DictReader(ledger.with_name("group_table.csv").open(encoding="utf-8"))}
        cds = {}
        if "cds_ledger" in dataset:
            cds = {r["pair_id"]: r for r in csv.DictReader(Path(dataset["cds_ledger"]).open(encoding="utf-8"))}

        def rank(pair: dict) -> str:
            material = sampling["key_material"].replace("<pair_id>", pair["pair_id"])
            return hashlib.sha256(material.encode()).hexdigest()

        chosen = []
        for strand in ("+", "-"):
            chosen += sorted((p for p in pairs if p["strand"] == strand), key=rank)[: sampling["strand_stratification"]["target_per_strand"]]
        if len(chosen) < sampling["pairs_per_dataset"]:
            rest = sorted((p for p in pairs if p not in chosen), key=rank)
            chosen += rest[: sampling["pairs_per_dataset"] - len(chosen)]
        for pair in sorted(chosen, key=rank):
            tss, strand, contig = int(pair["tss_zero_based"]), pair["strand"], pair["contig"]
            start, end = (tss - 60, tss + 21) if strand == "+" else (tss - 20, tss + 61)
            control = cds.get(pair["pair_id"])
            rows.append(
                {
                    "dataset": dataset["collection_id"],
                    "primary_source": dataset["primary_source"],
                    "pair_id": pair["pair_id"],
                    "partition": partition[pair["pair_id"]],
                    "tss_one_based": tss + 1,
                    "strand": strand,
                    "declared_classes": pair["tss_classes"],
                    "positive_sequence": pair["positive_sequence"],
                    "positive_ncbi": ncbi(contig, start, end, strand),
                    "control_start_one_based": int(pair["negative_start"]) + 1,
                    "control_end_one_based": int(pair["negative_end"]),
                    "control_sequence": pair["negative_sequence"],
                    "control_ncbi": ncbi(contig, int(pair["negative_start"]), int(pair["negative_end"]), strand),
                    "cds_control_start_one_based": int(control["genomic_start"]) + 1 if control else "",
                    "cds_control_strand": control["strand"] if control else "",
                    "cds_control_cds_id": control["cds_identifier"] if control else "",
                    "cds_control_sequence": control["sequence"] if control else "",
                    "cds_control_ncbi": ncbi(contig, int(control["genomic_start"]), int(control["genomic_start"]) + 81, control["strand"]) if control else "",
                    "A_positive_in_primary_table": "",
                    "B_positive_sequence": "",
                    "C_control_sequence_and_strand": "",
                    "D_control_tss_margin": "",
                    "E_cds_control": "" if control else "n/a",
                    "reviewer_notes": "",
                }
            )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(len(rows), "rows;", OUTPUT, sha256_file(OUTPUT))


if __name__ == "__main__":
    main()
