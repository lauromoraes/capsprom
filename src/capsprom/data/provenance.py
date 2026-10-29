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
