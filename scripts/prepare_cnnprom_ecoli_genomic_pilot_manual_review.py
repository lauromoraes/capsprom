"""Select the frozen manual-review sample of the CNNProm E. coli genomic pilot and write the review sheet.

Mirrors scripts/prepare_graphpro_v3_manual_review.py: lowest SHA-256 rank per
strand, plus the contract's observed cases.  It reads build outputs only and
refuses to overwrite an existing sheet, so the sample cannot change after
review starts.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
from pathlib import Path

import yaml

from capsprom.data.loading import sha256_file
from prepare_graphpro_v3_manual_review import ncbi


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/cnnprom_ecoli_genomic_pilot_manual_review_v1.yaml"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    build, sampling = config["build"], config["sampling"]
    output = Path(build["output"])
    if output.exists():
        raise FileExistsError(f"{output} exists; the review sample is frozen")
    ledger = Path(build["ledger"])
    if sha256_file(ledger.with_name("build_manifest.json")) != build["manifest_sha256"]:
        raise ValueError("build manifest hash mismatch")
    pairs = {r["record_id"]: r for r in csv.DictReader(ledger.open(encoding="utf-8"))}
    with gzip.open(build["canonical_table"], "rt", encoding="utf-8", newline="") as handle:
        headers = {r["record_id"]: r["original_header"] for r in csv.DictReader(handle)}

    def rank(record_id: str) -> str:
        return hashlib.sha256(sampling["key_material"].replace("<record_id>", record_id).encode()).hexdigest()

    forced = [r for r in sampling["forced_records"]["records"] if r in pairs]
    pool = [r for r in pairs if r not in forced]
    chosen = []
    for strand in ("+", "-"):
        chosen += sorted((r for r in pool if pairs[r]["strand"] == strand), key=rank)[: sampling["strand_stratification"]["target_per_strand"]]
    rows = []
    for record_id in forced + sorted(chosen, key=rank):
        pair, contig = pairs[record_id], build["contig"]
        tss, strand = int(pair["tss_zero_based"]), pair["strand"]
        start, end = (tss - 60, tss + 21) if strand == "+" else (tss - 20, tss + 61)
        regulondb_id = headers[record_id].split("__", 1)[0]
        rows.append(
            {
                "sample": "forced" if record_id in forced else "random",
                "record_id": record_id,
                "promoter": pair["promoter"],
                "regulondb_promoter_id": regulondb_id,
                "partition": pair["partition"],
                "placement_status": pair["status"],
                "n_loci": pair["n_loci"],
                "tss_one_based": tss + 1,
                "strand": strand,
                "support_class": pair["support_class"],
                "support_distance_nt": pair["support_distance_nt"],
                "positive_sequence": pair["positive_sequence"],
                "positive_ncbi": ncbi(contig, start, end, strand),
                "control_start_one_based": int(pair["negative_start"]) + 1,
                "control_end_one_based": int(pair["negative_end"]),
                "control_sequence": pair["negative_sequence"],
                "control_ncbi": ncbi(contig, int(pair["negative_start"]), int(pair["negative_end"]), strand),
                "A_positive_tss_in_regulondb": "",
                "B_positive_sequence": "",
                "C_control_sequence_and_strand": "",
                "D_control_tss_margin": "",
                "reviewer_notes": "",
            }
        )
    assert len(rows) == len(forced) + 2 * sampling["strand_stratification"]["target_per_strand"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(len(rows), "rows;", output, sha256_file(output))


if __name__ == "__main__":
    main()
