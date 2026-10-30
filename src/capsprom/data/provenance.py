"""Provenance records linking legacy files and derived datasets to a pinned acquisition.

Three records are produced, each stamped with when it was observed:

- the release metadata reported by each upstream source (commit dates, HTTP
  ``Last-Modified``), which is distinct from the date the project acquired it;
- an inventory of a legacy tree such as ``data/raw/`` that states, per file,
  whether its bytes or its sequences are reproduced by the pinned acquisition;
- a replay of a legacy dataset build from acquired files, compared byte for
  byte with the outputs that the experiments consumed.
"""

from __future__ import annotations

import bisect
import csv
import fnmatch
import gzip
import hashlib
import json
import re
import ssl
import subprocess
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from capsprom.data.acquisition import (
    RECORDED_HEADERS,
    USER_AGENT,
    fetch_json,
    file_digests,
    tls_context,
)
from capsprom.state import write_json_atomic

PROVENANCE_SCHEMA_VERSION = 1
UNKNOWN_ACQUISITION_DATE = {
    "value": None,
    "status": "unknown",
    "basis": "no acquisition record exists; file modification times are not accepted as evidence",
}
_MAX_GUNZIP_BYTES = 512 * 1024 * 1024
_HEX64 = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")

HeadFetcher = Callable[[str, "ssl.SSLContext | None"], dict[str, Any]]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def head_url(url: str, context: ssl.SSLContext | None = None) -> dict[str, Any]:
    """Return the recorded headers of a HEAD request, or the error it raised."""

    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60, context=context) as response:
            headers = {
                name: response.headers[name] for name in RECORDED_HEADERS if name in response.headers
            }
            return {"http_status": response.status, "headers": headers}
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        return {"error": repr(error)}


def source_release_metadata(
    acquisition_config: dict[str, Any],
    fetch: Callable[[str], Any] = fetch_json,
    head: HeadFetcher = head_url,
) -> dict[str, Any]:
    """Record what each source reports about its own version and update dates."""

    sources: dict[str, Any] = {}
    for source in acquisition_config["sources"]:
        declared = {
            key: value for key, value in source.items() if key not in {"files", "include", "exclude"}
        }
        entry: dict[str, Any] = {"declared": declared}
        if source["kind"] == "github_tree":
            commit = fetch(
                f"https://api.github.com/repos/{source['repository']}/commits/{source['commit']}"
            )
            entry["pinned_commit"] = {
                "sha": commit["sha"],
                "author_date": commit["commit"]["author"]["date"],
                "committer_date": commit["commit"]["committer"]["date"],
                "html_url": commit["html_url"],
            }
        else:
            entry["files"] = {
                item["path"]: head(item["url"], tls_context(item.get("tls_intermediate")))
                for item in source["files"]
            }
        sources[source["source_id"]] = entry
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "acquisition": acquisition_config["acquisition"]["name"],
        "observed_at": _now(),
        "interpretation": (
            "Commit dates and Last-Modified headers describe the upstream copy as reported by the "
            "source at observed_at. They are not acquisition dates; acquisition times are the "
            "acquired_at values in the acquisition manifest."
        ),
        "sources": sources,
    }


def acquired_content_index(acquired_root: Path, manifest: dict[str, Any]) -> dict[str, list[str]]:
    """Map the SHA-256 of every acquired file, zip member, and gzip payload to its origin."""

    index: dict[str, list[str]] = defaultdict(list)
    for key, record in sorted(manifest["files"].items()):
        index[record["sha256"]].append(key)
        path = acquired_root / key
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    if member.is_dir() or member.filename.startswith("__MACOSX/"):
                        continue
                    index[_sha256(archive.read(member))].append(f"{key}!{member.filename}")
        elif path.suffix == ".gz" and record["size_bytes"] <= _MAX_GUNZIP_BYTES:
            index[_sha256(gzip.decompress(path.read_bytes()))].append(f"{key}!gunzip")
    return dict(index)


def _sequence_equivalence(
    canonical_config: dict[str, Any], canonical_manifest: dict[str, Any]
) -> dict[str, list[dict[str, str]]]:
    """Map each legacy path to the collections whose validation reproduced its sequences."""

    equivalent: dict[str, list[dict[str, str]]] = defaultdict(list)
    collections = canonical_manifest["collections"]
    for collection in canonical_config["collections"]:
        cid = collection["collection_id"]
        matches = collections.get(cid, {}).get("validation", {}).get("legacy_sequence_match", {})
        for item in collection.get("legacy_inputs", []):
            # Inputs whose classes come from headers (ipro_fasta) declare no source_class.
            source_class = item.get("source_class")
            matched = matches.get(source_class) if source_class else matches and all(matches.values())
            if matched:
                equivalent[item["path"]].append(
                    {"collection_id": cid, "source_class": source_class or "all"}
                )
    return dict(equivalent)


def _dated_legacy_manifests(repo_root: Path, paths: list[Path]) -> dict[str, dict[str, str]]:
    """Read acquisition dates that a legacy ``manifest.json`` recorded for the files it hashes."""

    dated: dict[str, dict[str, str]] = {}
    for path in paths:
        if path.name != "manifest.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        when = payload.get("retrieved_utc") if isinstance(payload, dict) else None
        if not when:
            continue
        basis = f"retrieved_utc in {path.relative_to(repo_root).as_posix()} (untracked legacy record)"
        text = path.read_text(encoding="utf-8")
        for sha256 in set(_HEX64.findall(text)):
            dated[sha256] = {"value": when, "status": "recorded", "basis": basis}
    return dated


def _committed_hash_mentions(repo_root: Path, hashes: set[str]) -> dict[str, list[dict[str, str]]]:
    """Find committed project files that record a SHA-256, with the commit that first did so."""

    def git(*args: str) -> str:
        return subprocess.run(
            ("git", *args), cwd=repo_root, check=True, capture_output=True, text=True
        ).stdout

    try:
        tracked = git("ls-files", "configs", "docs", "specs").split()
    except (OSError, subprocess.CalledProcessError):
        return {}
    found: dict[str, list[dict[str, str]]] = defaultdict(list)
    for relative in tracked:
        try:
            text = (repo_root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for sha256 in set(_HEX64.findall(text)) & hashes:
            first = git("log", "--reverse", "--format=%H %cI", "-S", sha256, "--", relative).split()
            if len(first) >= 2:
                found[sha256].append(
                    {"path": relative, "first_commit": first[0], "first_commit_date": first[1]}
                )
    return dict(found)


def inventory_legacy_tree(
    repo_root: Path,
    legacy_root: Path,
    acquired_root: Path,
    acquisition_manifest: dict[str, Any],
    canonical_config: dict[str, Any],
    canonical_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Hash every legacy file and classify how far the pinned acquisition reproduces it."""

    index = acquired_content_index(repo_root / acquired_root, acquisition_manifest)
    equivalent = _sequence_equivalence(canonical_config, canonical_manifest)
    paths = sorted(p for p in (repo_root / legacy_root).rglob("*") if p.is_file())
    digests = {path: file_digests(path) for path in paths}
    retrieved = _dated_legacy_manifests(repo_root, paths)
    contracts = _committed_hash_mentions(repo_root, {d["sha256"] for d in digests.values()})
    files = []
    for path in paths:
        relative = path.relative_to(repo_root).as_posix()
        sha256 = digests[path]["sha256"]
        byte_matches = index.get(sha256, [])
        sequence_matches = equivalent.get(relative, [])
        if byte_matches:
            status = "byte_identical_to_acquisition"
        elif sequence_matches:
            status = "sequence_equivalent_to_acquisition"
        else:
            status = "not_reproduced_by_acquisition"
        mentions = contracts.get(sha256, [])
        if sha256 in retrieved:
            date = retrieved[sha256]
        elif mentions:
            first = min(mentions, key=lambda m: m["first_commit_date"])
            date = {
                "value": first["first_commit_date"],
                "status": "no_later_than",
                "basis": f"SHA-256 first committed in {first['path']} at {first['first_commit']}",
            }
        else:
            date = UNKNOWN_ACQUISITION_DATE
        files.append(
            {
                "path": relative,
                "group": path.relative_to(repo_root / legacy_root).parts[0],
                "size_bytes": digests[path]["size_bytes"],
                "sha256": sha256,
                "status": status,
                "byte_identical_to": byte_matches,
                "sequence_equivalent_to": sequence_matches,
                "recorded_by_committed_files": mentions,
                "acquisition_date": date,
            }
        )
    by_group: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in files:
        by_group[item["group"]][item["status"]] += 1
        by_group[item["group"]][f"date_{item['acquisition_date']['status']}"] += 1
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "legacy_root": legacy_root.as_posix(),
        "acquisition": acquisition_manifest["acquisition"],
        "acquisition_config_sha256": acquisition_manifest["config_sha256"],
        "canonical_config_sha256": canonical_manifest["config_sha256"],
        "observed_at": _now(),
        "summary": {group: dict(counts) for group, counts in sorted(by_group.items())},
        "files": files,
    }


def stage_legacy_inputs(
    canonical_config: dict[str, Any],
    acquired_root: Path,
    staging_root: Path,
    sources: set[str],
    legacy_prefix: str = "data/raw/",
) -> list[dict[str, str]]:
    """Write acquired inputs under their legacy file names so legacy builders can replay.

    Only collections with one acquired input per legacy class are staged; the
    mapping comes from the canonicalization contract, not from file names.
    """

    staged = []
    for collection in canonical_config["collections"]:
        if collection["source"] not in sources:
            continue
        inputs = {item["source_class"]: item for item in collection["inputs"]}
        if len(inputs) != len(collection["inputs"]):
            raise ValueError(f"{collection['collection_id']}: ambiguous class-to-input mapping")
        for legacy in collection.get("legacy_inputs", []):
            source_input = inputs[legacy["source_class"]]
            archive = acquired_root / source_input["file"]
            member = source_input.get("member")
            if member is not None:
                with zipfile.ZipFile(archive) as handle:
                    data = handle.read(member)
            else:
                data = archive.read_bytes()
            if not legacy["path"].startswith(legacy_prefix):
                raise ValueError(f"legacy path outside {legacy_prefix}: {legacy['path']}")
            destination = staging_root / legacy["path"][len(legacy_prefix):]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            staged.append(
                {
                    "legacy_path": legacy["path"],
                    "acquired_input": source_input["file"] + (f"!{member}" if member else ""),
                    "sha256": _sha256(data),
                }
            )
    return staged


# Dataset names that the legacy build used and the current builders spell differently.
# GraphPro's Cpne folder was first mislabelled as Clostridium; its records are
# Chlamydophila pneumoniae CWL029 (see capsprom.data.fasta_builders).
LEGACY_DATASET_ALIASES = {"clostridium_phytofermentans": "chlamydophila_pneumoniae"}


def _sha256_file(path: Path) -> str:
    return file_digests(path)["sha256"]


def replay_regenerated_v3(
    canonical_config: dict[str, Any],
    acquired_root: Path,
    staging_root: Path,
    reference_filtering_manifest: Path,
    reference_interim_fasta: Path,
    reference_strict_csv: Path,
) -> dict[str, Any]:
    """Rebuild the regenerated-v3 datasets from acquired files and compare them.

    The replay calls the same builders, crop windows, and seed as
    ``scripts/rebuild_real_negative_datasets.py``; per-dataset random streams make
    the outputs independent of which other datasets are present. Model-ready
    train/test CSVs must match byte for byte. Intermediate FASTA files are
    compared by record (identifier, description, sequence), because FASTA line
    wrapping is formatting, and their byte equality is reported separately.
    When the split differs, ``pooled_rows_match`` says whether train and test
    together still hold the same rows.
    """

    from capsprom.data.dataset_builders import (
        build_group_safe_intra_dataset_csvs_with_audit,
        crop_fasta_directory,
        group_promoter_pairs,
    )
    from capsprom.data.fasta_builders import (
        build_cdbprom_fastas,
        build_cnnprom_fastas,
        build_graphpro_fastas,
    )
    from capsprom.data.sequences import read_fasta

    for child in ("raw", "fasta", "cropped", "strict"):
        target = staging_root / child
        if target.exists() and any(target.iterdir()):
            raise ValueError(f"refusing to replay into a non-empty directory: {target}")
    raw, fasta = staging_root / "raw", staging_root / "fasta"
    staged = stage_legacy_inputs(
        canonical_config, acquired_root, raw, {"cdbprom", "cnnprom", "graphpro"}
    )
    fasta.mkdir(parents=True, exist_ok=True)
    build_cdbprom_fastas(raw / "CDBProm", fasta)
    build_cnnprom_fastas(raw / "CNNProm", fasta)
    build_graphpro_fastas(raw / "GraphPro", fasta)
    crop_fasta_directory(fasta, staging_root / "cropped")
    build = build_group_safe_intra_dataset_csvs_with_audit(
        staging_root / "cropped", staging_root / "strict", random_seed=42
    )
    pairs = group_promoter_pairs(sorted(fasta.glob("*.fa")))
    outputs = {result.output.name: result.output for result in build.outputs}

    reference = json.loads(reference_filtering_manifest.read_text(encoding="utf-8"))
    datasets = []
    for record in reference:
        legacy_name = record["dataset"]
        current_name = LEGACY_DATASET_ALIASES.get(legacy_name, legacy_name)
        key = (record["study"], record["organism_type"], current_name)
        prefix = f"{record['study']}-{record['organism_type']}-{current_name}-"
        legacy_prefix = f"{record['study']}-{record['organism_type']}-{legacy_name}-"
        outputs_match = {}
        replayed_rows: list[str] = []
        for split in ("train", "test"):
            names = [n for n in outputs if n.startswith(prefix) and n.endswith(f"-{split}.csv")]
            replayed = _sha256_file(outputs[names[0]]) if len(names) == 1 else None
            outputs_match[f"{split}_output_sha256"] = replayed == record[f"{split}_output_sha256"]
            if len(names) == 1:
                replayed_rows += outputs[names[0]].read_text(encoding="utf-8").splitlines()[1:]
        legacy_rows: list[str] = []
        for legacy_csv in sorted(reference_strict_csv.glob(f"{legacy_prefix}*.csv")):
            legacy_rows += legacy_csv.read_text(encoding="utf-8").splitlines()[1:]
        interim_records, interim_bytes = {}, {}
        for cls, field in (("p", "positive_source_sha256"), ("n", "negative_source_sha256")):
            if key not in pairs:
                interim_records[cls] = interim_bytes[cls] = False
                continue
            replayed_path = pairs[key][cls]
            legacy_path = reference_interim_fasta / replayed_path.name.replace(current_name, legacy_name)
            interim_bytes[cls] = _sha256_file(replayed_path) == record[field]
            interim_records[cls] = legacy_path.exists() and (
                _sha256_file(legacy_path) == record[field]
                and read_fasta(legacy_path) == read_fasta(replayed_path)
            )
        datasets.append(
            {
                "dataset": "-".join((record["study"], record["organism_type"], legacy_name)),
                "replayed_as": "-".join(key),
                "outputs_match": outputs_match,
                "interim_fasta_records_match": interim_records,
                "interim_fasta_bytes_match": interim_bytes,
                "pooled_rows_match": bool(legacy_rows) and sorted(legacy_rows) == sorted(replayed_rows),
                "all_match": all(outputs_match.values()) and all(interim_records.values()),
            }
        )
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "replay": "real-negative-regenerated-v3",
        "observed_at": _now(),
        "reference_filtering_manifest": reference_filtering_manifest.as_posix(),
        "reference_filtering_manifest_sha256": _sha256_file(reference_filtering_manifest),
        "staged_inputs": staged,
        "dataset_count": len(datasets),
        "all_datasets_match": all(item["all_match"] for item in datasets),
        "datasets": datasets,
    }



# Neural campaign states name the training CSV hash `train_sha256`.
_DATASET_HASH_KEYS = {"train_sha256", "test_sha256"}


def _dataset_hashes(payload: Any) -> set[str]:
    """Collect every dataset hash stored under a known key, at any depth."""

    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, str) and (
                key in _DATASET_HASH_KEYS or key.endswith("dataset_sha256")
            ):
                found.add(value)
            else:
                found |= _dataset_hashes(value)
    elif isinstance(payload, list):
        for value in payload:
            found |= _dataset_hashes(value)
    return found


def link_experiment_records(
    record_paths: list[Path],
    reference_filtering_manifest: Path,
    replay: dict[str, Any],
) -> dict[str, Any]:
    """Classify the dataset hashes that experiment records pinned against the replay.

    A hash is ``replay_verified`` when it is a regenerated-v3 output that the replay
    reproduced byte for byte from the acquisition.
    """

    reference = json.loads(reference_filtering_manifest.read_text(encoding="utf-8"))
    replayed = {item["dataset"]: item for item in replay["datasets"]}
    verified: dict[str, str] = {}
    for record in reference:
        dataset = "-".join((record["study"], record["organism_type"], record["dataset"]))
        for split in ("train", "test"):
            if replayed[dataset]["outputs_match"][f"{split}_output_sha256"]:
                verified[record[f"{split}_output_sha256"]] = f"{dataset}:{split}"
    records = []
    for path in sorted(record_paths):
        hashes = _dataset_hashes(json.loads(path.read_text(encoding="utf-8")))
        if not hashes:
            continue
        records.append(
            {
                "path": path.as_posix(),
                "dataset_hashes": len(hashes),
                "replay_verified": sorted(verified[h] for h in hashes if h in verified),
                "not_linked": sorted(h for h in hashes if h not in verified),
            }
        )
    unlinked = {h for item in records for h in item["not_linked"]}
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "observed_at": _now(),
        "replay_observed_at": replay["observed_at"],
        "record_count": len(records),
        "fully_linked_records": sum(1 for item in records if not item["not_linked"]),
        "unlinked_dataset_hashes": sorted(unlinked),
        "records": records,
    }


def length_deviations(canonical_dir: Path, canonical_manifest: dict[str, Any]) -> dict[str, Any]:
    """List every canonical record whose length differs from its declared release length.

    The record holds identifiers and lengths only, never sequences, so it can be
    committed and compared with the known-deviation table of the integrity spec.
    """

    collections: dict[str, dict[str, Any]] = {}
    total = 0
    for path in sorted(canonical_dir.glob("*.csv.gz")):
        collection_id = path.name.removesuffix(".csv.gz")
        by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["length_matches_expected"] == "false":
                    by_class[row["source_class"]].append(
                        {"record_id": row["record_id"], "length": int(row["length"])}
                    )
        if by_class:
            collections[collection_id] = {
                source_class: {"count": len(records), "records": records}
                for source_class, records in sorted(by_class.items())
            }
            total += sum(len(records) for records in by_class.values())
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "observed_at": _now(),
        "canonical_config_sha256": canonical_manifest.get("config_sha256"),
        "collection_count": len(collections),
        "record_count": total,
        "collections": collections,
    }


def spec_deviation_patterns(spec_text: str) -> list[str]:
    """Return the collection-ID patterns of the spec's known-deviation table."""

    section = spec_text.split("## Length exclusion", 1)[1].split("\n## ", 1)[0]
    patterns: list[str] = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[0].startswith("`"):
            patterns.extend(re.findall(r"`([^`]+)`", cells[0]))
    return patterns


def uncovered_deviations(record: dict[str, Any], patterns: list[str]) -> dict[str, list[str]]:
    """Compare a deviation record with the spec table in both directions."""

    collections = sorted(record["collections"])
    return {
        "missing_from_spec": [c for c in collections if not any(fnmatch.fnmatch(c, p) for p in patterns)],
        "stale_in_spec": [p for p in patterns if not any(fnmatch.fnmatch(c, p) for c in collections)],
    }


_UCSC_RANGE = re.compile(r"^(?P<assembly>[A-Za-z0-9]+)_.*\brange=(?P<chrom>[^:\s]+):(?P<start>\d+)-(?P<end>\d+)\b.*\bstrand=(?P<strand>[+-])")


def recreate_ucsc_ranges(canonical_path: Path, genomes: dict[str, Path]) -> dict[str, Any]:
    """Compare every record of a canonical table with its declared UCSC ``range``.

    Headers such as ``mm10_..._up_700_... range=chr1:a-b ... strand=-`` are read
    as 1-based closed intervals (F-041): ``[a - 1, b)`` is extracted from the
    named assembly and reverse-complemented on ``-``. The record lists the IDs of
    records that are not reproduced, never a sequence.
    """

    from capsprom.data.twobit import TwoBitGenome

    opened: dict[str, TwoBitGenome] = {}
    counts: dict[str, int] = defaultdict(int)
    failures: dict[str, list[str]] = defaultdict(list)
    by_assembly: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    try:
        with gzip.open(canonical_path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                counts["records"] += 1
                match = _UCSC_RANGE.match(row["original_header"])
                if match is None:
                    failures["unparsed_header"].append(row["record_id"])
                    continue
                assembly = match["assembly"]
                if assembly not in genomes:
                    failures["undeclared_assembly"].append(row["record_id"])
                    continue
                genome = opened.get(assembly) or opened.setdefault(assembly, TwoBitGenome(genomes[assembly]))
                if match["chrom"] not in genome.sequence_names:
                    failures["missing_contig"].append(row["record_id"])
                    continue
                start, end = int(match["start"]) - 1, int(match["end"])
                try:
                    recreated = genome.fetch(match["chrom"], start, end, reverse_complement=match["strand"] == "-")
                except ValueError:
                    failures["interval_outside_contig"].append(row["record_id"])
                    continue
                if recreated.upper() == row["sequence"].upper():
                    counts["identical"] += 1
                    by_assembly[assembly]["identical"] += 1
                else:
                    failures["sequence_differs"].append(row["record_id"])
                    by_assembly[assembly]["sequence_differs"] += 1
    finally:
        for genome in opened.values():
            genome.close()
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "observed_at": _now(),
        "canonical_table": canonical_path.name,
        "canonical_table_sha256": _sha256_file(canonical_path),
        "genomes": {name: {"path": str(path), "sha256": _sha256_file(path)} for name, path in sorted(genomes.items())},
        "convention": "ucsc_position_1closed",
        "record_count": counts["records"],
        "identical_count": counts["identical"],
        "by_assembly": {name: dict(values) for name, values in sorted(by_assembly.items())},
        "failures": {reason: {"count": len(ids), "record_ids": ids} for reason, ids in sorted(failures.items())},
    }


_REVERSE_COMPLEMENT = str.maketrans("ACGTN", "TGCAN")


def _anchor(sequence: str, size: int) -> tuple[int, str] | None:
    for offset in range(0, len(sequence) - size + 1, size):
        candidate = sequence[offset : offset + size]
        if set(candidate) <= set("ACGT"):
            return offset, candidate
    return None


def locate_exact_sequences(sequences: dict[str, str], genome_path: Path, anchor_size: int = 32) -> dict[str, Any]:
    """Find every exact, full-length occurrence of each sequence on either strand.

    Each sequence is reduced to its first ACGT-only ``anchor_size``-mer (on the
    forward sequence and on its reverse complement); one pass over the genome
    collects anchor positions, and every candidate is confirmed by comparing the
    whole sequence. Positions are 0-based starts of the forward-strand interval.
    """

    from capsprom.data.twobit import TwoBitGenome

    anchors: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    unanchored: list[str] = []
    for record_id, sequence in sequences.items():
        sequence = sequence.upper()
        for strand, oriented in (("+", sequence), ("-", sequence.translate(_REVERSE_COMPLEMENT)[::-1])):
            found = _anchor(oriented, anchor_size)
            if found is None:
                unanchored.append(record_id)
                break
            anchors[found[1]].append((record_id, strand, found[0]))
    hits: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with TwoBitGenome(genome_path) as genome:
        for name in genome.sequence_names:
            contig = genome.fetch(name, 0, genome.sequence_size(name)).upper()
            for position in range(len(contig) - anchor_size + 1):
                entries = anchors.get(contig[position : position + anchor_size])
                if not entries:
                    continue
                for record_id, strand, offset in entries:
                    sequence = sequences[record_id].upper()
                    start = position - offset
                    window = contig[start : start + len(sequence)] if start >= 0 else ""
                    if strand == "-":
                        window = window.translate(_REVERSE_COMPLEMENT)[::-1]
                    if window == sequence:
                        hits[record_id].append({"contig": name, "start": start, "strand": strand})
    located = {record_id: loci for record_id, loci in hits.items()}
    return {
        "genome_sha256": _sha256_file(genome_path),
        "anchor_size": anchor_size,
        "sequence_count": len(sequences),
        "located_count": len(located),
        "unique_locus_count": sum(1 for loci in located.values() if len(loci) == 1),
        "unanchored": sorted(set(unanchored)),
        "not_located": sorted(set(sequences) - set(located) - set(unanchored)),
        "loci": located,
    }


def _transcript_starts(gtf_path: Path) -> set[tuple[str, str, int]]:
    """Return ``(contig, strand, 1-based TSS)`` for every transcript of a GTF."""

    starts: set[tuple[str, str, int]] = set()
    with gzip.open(gtf_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            fields = line.split("\t")
            if len(fields) > 6 and fields[2] == "transcript":
                tss = int(fields[3]) if fields[6] == "+" else int(fields[4])
                starts.add((fields[0], fields[6], tss))
    return starts


def bhandari_history_record(
    history_files: dict[str, tuple[Path, Path]],
    arabidopsis_csv: Path,
    arabidopsis_genome: Path,
    arabidopsis_gtf: Path,
    loci_path: Path,
) -> dict[str, Any]:
    """Compare the pre-2021 Bhandari repository CSVs with the Drive release.

    ``history_files`` maps a CSV name to ``(csv_path, canonical_table)``. The
    *A. thaliana* CSV, which has no coordinates, is also located exactly in the
    *A. thaliana* genome, and the base at index 700 of each located window is
    compared with annotated transcript starts. Loci are written to the ignored
    ``loci_path``; the returned record holds counts and hashes only.
    """

    files: dict[str, Any] = {}
    for name, (csv_path, canonical_table) in sorted(history_files.items()):
        with csv_path.open(encoding="utf-8", newline="") as handle:
            rows = [(label, sequence.upper()) for label, sequence in csv.reader(handle)]
        with gzip.open(canonical_table, "rt", encoding="utf-8", newline="") as handle:
            released = [row["sequence"].upper() for row in csv.DictReader(handle)]
        history = [sequence for _, sequence in rows]
        lengths = defaultdict(int)
        for sequence in history:
            lengths[len(sequence)] += 1
        files[name] = {
            "sha256": _sha256_file(csv_path),
            "record_count": len(rows),
            "labels": sorted({label for label, _ in rows}),
            "length_1000_count": lengths[1000],
            "other_lengths": sorted(length for length in lengths if length != 1000),
            "unique_sequence_count": len(set(history)),
            "non_acgt_record_count": sum(1 for sequence in history if set(sequence) - set("ACGT")),
            "mean_gc": round(sum(s.count("G") + s.count("C") for s in history) / sum(map(len, history)), 4),
            "compared_with": canonical_table.name,
            "equal_multiset": sorted(history) == sorted(released),
            "shared_unique_sequences": len(set(history) & set(released)),
        }
    with arabidopsis_csv.open(encoding="utf-8", newline="") as handle:
        sequences = {f"{arabidopsis_csv.name}:{index}": row[1] for index, row in enumerate(csv.reader(handle))}
    located = locate_exact_sequences(sequences, arabidopsis_genome)
    starts = _transcript_starts(arabidopsis_gtf)
    tss_match = 0
    contigs: dict[str, int] = defaultdict(int)
    for record_id, loci in located["loci"].items():
        length = len(sequences[record_id])
        contigs[loci[0]["contig"]] += 1
        for locus in loci:
            if length != 1000:
                continue
            tss = locus["start"] + 701 if locus["strand"] == "+" else locus["start"] + length - 700
            if (locus["contig"], locus["strand"], tss) in starts:
                tss_match += 1
                break
    loci_path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(loci_path, located["loci"])
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "observed_at": _now(),
        "files": files,
        "arabidopsis_location": {
            "genome_sha256": located["genome_sha256"],
            "gtf_sha256": _sha256_file(arabidopsis_gtf),
            "anchor_size": located["anchor_size"],
            "sequence_count": located["sequence_count"],
            "located_count": located["located_count"],
            "unique_locus_count": located["unique_locus_count"],
            "first_locus_contigs": dict(sorted(contigs.items())),
            "unanchored_count": len(located["unanchored"]),
            "not_located_count": len(located["not_located"]),
            "not_located_record_ids": located["not_located"],
            "index_700_equals_transcript_start_count": tss_match,
            "loci_file": str(loci_path),
            "loci_sha256": _sha256_file(loci_path),
        },
    }


def verify_label_csv_canonical(
    canonical_table: Path, source_file: Path, source_key: str, comparison_table: Path | None = None
) -> dict[str, Any]:
    """Check that a canonical table built from a ``label,sequence`` file loses nothing.

    The rows, written back as ``label,sequence`` with the source's line ending,
    must reproduce the source file byte for byte; record IDs must be contiguous
    and stable; ``sequence_sha1`` must match. ``comparison_table`` (another
    release of the same study) is compared by sequence multiset and by order.
    """

    with gzip.open(canonical_table, "rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    collection_id = rows[0]["collection_id"] if rows else ""
    raw = source_file.read_bytes()
    newline = b"\r\n" if b"\r\n" in raw[:4096] else b"\n"
    rebuilt = b"".join(f"{row['original_header']},{row['sequence']}".encode() + newline for row in rows)
    expected_ids = [f"{collection_id}:{source_key}:{index:07d}" for index in range(len(rows))]
    sequences = [row["sequence"] for row in rows]
    lengths = defaultdict(int)
    for sequence in sequences:
        lengths[len(sequence)] += 1
    record: dict[str, Any] = {
        "canonical_table": canonical_table.name,
        "canonical_sha256": _sha256_file(canonical_table),
        "source_file": source_key,
        "source_sha256": _sha256(raw),
        "record_count": len(rows),
        "source_line_count": raw.count(newline),
        "rebuilt_equals_source_bytes": rebuilt == raw,
        "record_ids_contiguous": [row["record_id"] for row in rows] == expected_ids,
        "record_indexes_contiguous": [int(row["record_index"]) for row in rows] == list(range(len(rows))),
        "sequence_sha1_valid": all(
            hashlib.sha1(row["sequence"].encode()).hexdigest() == row["sequence_sha1"] for row in rows
        ),
        "case_normalized_records": sum(row["case_normalized"] == "true" for row in rows),
        "source_labels": sorted({row["original_header"] for row in rows}),
        "length_1000_records": lengths[1000],
        "other_lengths": {str(length): count for length, count in sorted(lengths.items()) if length != 1000},
        "non_strict_dna_records": sum(row["strict_dna"] != "true" for row in rows),
        "duplicate_records": sum(bool(row["duplicate_of"]) for row in rows),
        "unique_sequences": len(set(sequences)),
    }
    if comparison_table is not None:
        with gzip.open(comparison_table, "rt", encoding="utf-8", newline="") as handle:
            other = [row["sequence"] for row in csv.DictReader(handle)]
        record["comparison"] = {
            "table": comparison_table.name,
            "equal_multiset": sorted(sequences) == sorted(other),
            "equal_order": sequences == other,
            "shared_unique_sequences": len(set(sequences) & set(other)),
        }
    return record


TRANSCRIPT_FEATURES = frozenset(
    {"transcript", "mRNA", "lnc_RNA", "ncRNA", "tRNA", "rRNA", "snoRNA", "snRNA", "miRNA",
     "primary_transcript", "antisense_RNA"}
)
TSS_DISTANCE_BINS = ((0, 0, "exact"), (1, 10, "within_10"), (11, 100, "within_100"), (101, 500, "within_500"))


def transcript_intervals(
    path: Path, aliases: dict[str, str] | None = None
) -> dict[tuple[str, str], list[tuple[int, int]]]:
    """Return 1-based closed transcript intervals by ``(contig, strand)`` from a GTF or GFF3.

    ``aliases`` renames contigs (for example Ensembl ``1`` to RefSeq ``NC_003070.9``).
    """

    aliases = aliases or {}

    intervals: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            fields = line.split("\t")
            if len(fields) > 6 and fields[2] in TRANSCRIPT_FEATURES and fields[6] in "+-":
                intervals[(aliases.get(fields[0], fields[0]), fields[6])].append((int(fields[3]), int(fields[4])))
    return {key: sorted(set(values)) for key, values in intervals.items()}


def _nearest_tss(position: int, strand: str, starts: list[int]) -> int | None:
    """Signed distance, along transcription, from the window TSS to the nearest annotated TSS.

    Negative values mean the annotated TSS lies upstream of the window TSS.
    """

    if not starts:
        return None
    index = bisect.bisect_left(starts, position)
    nearest = min(
        (starts[i] for i in (index - 1, index) if 0 <= i < len(starts)), key=lambda start: abs(start - position)
    )
    return nearest - position if strand == "+" else position - nearest


def classify_window_tss(
    canonical_table: Path,
    loci: dict[str, list[dict[str, Any]]],
    annotations: dict[str, Path],
    window_tss: int = 700,
    aliases: dict[str, dict[str, str]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Classify, per record, the agreement of index ``window_tss`` with annotated transcript starts.

    A record is evaluated only if it has the declared length and an exact genome
    locus. Its window TSS is the 1-based genome position of index ``window_tss``
    on the locus strand: ``start + window_tss + 1`` on ``+`` and
    ``start + length - window_tss`` on ``-``, where ``start`` is the 0-based locus
    start. An annotated TSS is the 5' end of a transcript feature on the same
    contig and strand (GFF/GTF column 4 on ``+``, column 5 on ``-``). For records
    with several loci, the locus nearest an annotated TSS is used. Records are
    never judged incorrect here: the classes describe distance only.
    """

    starts = {}
    inside = {}
    for name, path in annotations.items():
        intervals = transcript_intervals(path, (aliases or {}).get(name))
        starts[name] = {
            key: sorted({start if key[1] == "+" else end for start, end in values}) for key, values in intervals.items()
        }
        inside[name] = intervals
    with gzip.open(canonical_table, "rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    evidence: list[dict[str, Any]] = []
    counts: dict[str, dict[str, int]] = {name: defaultdict(int) for name in annotations}
    signed: dict[str, dict[str, int]] = {name: defaultdict(int) for name in annotations}
    scope: dict[str, int] = defaultdict(int)
    for row in rows:
        record_loci = loci.get(f"{row['source_file'].rsplit('/', 1)[-1]}:{row['record_index']}", [])
        length = int(row["length"])
        entry: dict[str, Any] = {"record_id": row["record_id"], "locus_count": len(record_loci)}
        if not record_loci:
            entry["scope"] = "not_located"
        elif length != 1000:
            entry["scope"] = "not_full_length"
        else:
            entry["scope"] = "evaluated"
        scope[entry["scope"]] += 1
        for name in annotations:
            if entry["scope"] != "evaluated":
                entry[name] = ""
                continue
            best: tuple[int, int, str] | None = None
            for locus in record_loci:
                strand = locus["strand"]
                position = locus["start"] + window_tss + 1 if strand == "+" else locus["start"] + length - window_tss
                distance = _nearest_tss(position, strand, starts[name].get((locus["contig"], strand), []))
                if distance is not None and (best is None or abs(distance) < abs(best[0])):
                    best = (distance, position, f"{locus['contig']}:{strand}")
            if best is None:
                status = "no_transcript_on_strand"
            else:
                status = next((label for low, high, label in TSS_DISTANCE_BINS if low <= abs(best[0]) <= high), "")
                if not status:
                    contig, strand = best[2].split(":")
                    within = any(s <= best[1] <= e for s, e in inside[name].get((contig, strand), []))
                    status = "inside_transcript_far" if within else "outside_transcript_far"
                elif best[0]:
                    signed[name]["upstream" if best[0] < 0 else "downstream"] += 1
            entry[name] = status if best is None else f"{status}:{best[0]}"
            counts[name][status] += 1
        evidence.append(entry)
    agreement = defaultdict(int)
    for entry in evidence:
        if entry["scope"] == "evaluated":
            agreement["+".join(n for n in annotations if entry[n].startswith("exact")) or "none"] += 1
    summary = {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "observed_at": _now(),
        "canonical_table": canonical_table.name,
        "canonical_sha256": _sha256_file(canonical_table),
        "annotations": {name: {"path": str(path), "sha256": _sha256_file(path)} for name, path in annotations.items()},
        "window_tss_index": window_tss,
        "definition": "1-based TSS = locus start + 701 on '+', locus start + length - 700 on '-'; annotated TSS = "
        "5' end of a transcript feature on the same contig and strand; distance signed along transcription "
        "(negative = annotated TSS upstream)",
        "scope": dict(scope),
        "by_annotation": {name: dict(sorted(values.items())) for name, values in counts.items()},
        "near_miss_direction": {name: dict(values) for name, values in signed.items()},
        "exact_agreement_sets": dict(sorted(agreement.items())),
    }
    return summary, evidence
