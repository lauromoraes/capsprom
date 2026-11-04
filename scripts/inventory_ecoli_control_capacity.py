"""CNNProm E. coli on NC_000913.3: place positives, build the RegulonDB TSS union, count control capacity."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml

from capsprom.data.control_capacity import excluded_intervals, free_runs, non_overlapping_slots
from capsprom.data.exact_mapping import find_exact, read_fasta, reverse_complement
from capsprom.state import write_json_atomic


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gc(seq: str) -> int:
    return sum(base in "GC" for base in seq)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/ecoli_control_capacity_v1.yaml"))
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))["inventory"]
    acq = yaml.safe_load(Path(cfg["acquisition_config"]).read_text(encoding="utf-8"))["acquisition"]
    root = Path(acq["root"])
    genome_path = Path(cfg["genome_fasta"])
    if _sha256(genome_path) != cfg["genome_fasta_sha256"]:
        raise SystemExit("genome hash mismatch")
    contigs = read_fasta(genome_path)
    contig = cfg["contig"]
    genome = contigs[contig]
    length = len(genome)
    radius, window, caliper = int(cfg["radius"]), int(cfg["window"]), int(cfg["gc_caliper"])

    tss: set[tuple[int, str]] = set()
    per_source: dict[str, int] = {}
    chromosomes: Counter[str] = Counter()
    for dataset in acq["ht_tss_datasets"]:
        ids, keys = set(), set()
        for page in sorted((root / "ht_tss" / dataset).glob("page_*.json")):
            for row in json.loads(page.read_bytes())["data"]["getAllTSSOfDataset"]:
                chromosomes[row["chromosome"]] += 1
                ids.add(row["_id"])
                if row["pos_1"] is not None and not 1 <= int(row["pos_1"]) <= length:
                    chromosomes["out_of_range"] += 1
                elif row["chromosome"] == contig and row["pos_1"] is not None:
                    keys.add((int(row["pos_1"]) - 1, row["strand"]))
        per_source[dataset] = len(keys)
        tss |= keys
    content = json.loads((root / "files" / "PromoterSet.json").read_bytes())["data"]["getDataOfFile"]["content"]
    promoter_keys, promoter_seq_check = set(), Counter()
    for line in content.splitlines()[1:]:
        cols = line.rstrip(" ").split("\t")
        if len(cols) < 6 or not cols[3].strip().isdigit():
            continue
        tss0, strand = int(cols[3]) - 1, "+" if cols[2] == "forward" else "-"
        promoter_keys.add((tss0, strand))
        seq = cols[5].strip().upper()
        if len(seq) == 81:
            if strand == "+":
                ref = genome[tss0 - 60 : tss0 + 21]
            else:
                ref = reverse_complement(genome[tss0 - 20 : tss0 + 61])
            promoter_seq_check["match" if ref == seq else "mismatch"] += 1
        else:
            promoter_seq_check["no_81nt_sequence"] += 1
    per_source["PromoterSet"] = len(promoter_keys)
    tss |= promoter_keys

    placed, positive_tss, positive_gc = Counter(), set(), []
    with gzip.open(cfg["mapping_records"], "rt", encoding="utf-8", newline="") as handle:
        records = [row for row in csv.DictReader(handle) if row["label"] == "1"]
    canonical = {}
    with gzip.open(cfg["canonical_table"], "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            canonical[row["record_id"]] = row["sequence"].upper()
    for record in records:
        loci = find_exact(canonical[record["record_id"]], {contig: genome})
        if len(loci) != 1:
            placed[f"loci_{min(len(loci), 2)}"] += 1
            continue
        locus = loci[0]
        tss0 = locus.start + 60 if locus.strand == "+" else locus.end - 61
        positive_tss.add((tss0, locus.strand))
        positive_gc.append(_gc(canonical[record["record_id"]]))
        placed["single_locus"] += 1
        placed["in_regulondb_union" if (tss0, locus.strand) in tss else "not_in_regulondb_union"] += 1
    exclusion = tss | positive_tss

    excluded = excluded_intervals({t for t, _ in exclusion}, radius, length)
    runs = free_runs(excluded, length)
    free_bp = sum(end - start for start, end in runs)
    slots = non_overlapping_slots(runs, window)
    window_gc = Counter()
    for start, end in runs:
        if end - start < window:
            continue
        gc = _gc(genome[start : start + window])
        window_gc[gc] += 1
        for pos in range(start + 1, end - window + 1):
            gc += (genome[pos + window - 1] in "GC") - (genome[pos - 1] in "GC")
            window_gc[gc] += 1
    no_candidate = sum(
        1 for g in positive_gc if not any(window_gc.get(v, 0) for v in range(g - caliper, g + caliper + 1))
    )
    summary = {
        "config_sha256": _sha256(args.config),
        "contig": contig, "contig_length": length, "radius": radius, "window": window,
        "tss_chromosomes": dict(chromosomes),
        "unique_tss_per_source": per_source,
        "union_unique_tss_position_strand": len(tss),
        "union_unique_tss_positions": len({t for t, _ in tss}),
        "promoterset_sequence_check": dict(promoter_seq_check),
        "positives": dict(placed),
        "exclusion_unique_positions": len({t for t, _ in exclusion}),
        "free_bp": free_bp, "free_fraction": round(free_bp / length, 4),
        "non_overlapping_slots": slots, "positives_needing_control": placed["single_locus"],
        "slots_per_positive": round(slots / max(1, placed["single_locus"]), 3),
        "free_candidate_windows_total": sum(window_gc.values()),
        "positives_without_gc_candidate": no_candidate,
        "median_gc_positive": sorted(positive_gc)[len(positive_gc) // 2] if positive_gc else None,
    }
    write_json_atomic(Path(cfg["summary_output"]), summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
