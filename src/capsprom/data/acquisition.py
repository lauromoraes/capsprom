"""Pinned, hash-verified, resumable acquisition of upstream source files."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from capsprom.state import write_json_atomic

ACQUISITION_SCHEMA_VERSION = 1
SUPPORTED_DIGESTS = ("sha256", "md5", "git_blob_sha1")
USER_AGENT = "capsprom-source-acquisition/1"
_CHUNK = 1024 * 1024

JsonFetcher = Callable[[str], Any]
Downloader = Callable[[str, Path, "ssl.SSLContext | None"], "dict[str, str] | None"]
# Response headers that describe the upstream copy; they are not acquisition dates.
RECORDED_HEADERS = ("last-modified", "etag", "content-length", "content-type")


@dataclass(frozen=True)
class AcquisitionFile:
    """One upstream file and the digests it must reproduce."""

    source_id: str
    path: str
    url: str
    expected: dict[str, str] = field(default_factory=dict)
    tls_intermediate: dict[str, str] | None = None

    @property
    def key(self) -> str:
        return f"{self.source_id}/{self.path}"


def load_acquisition_config(path: Path) -> dict[str, Any]:
    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if set(config) != {"acquisition", "sources"}:
        raise ValueError("acquisition config must contain exactly 'acquisition' and 'sources'")
    seen: set[str] = set()
    for source in config["sources"]:
        source_id = source["source_id"]
        if source_id in seen:
            raise ValueError(f"duplicate source_id: {source_id}")
        seen.add(source_id)
        kind = source["kind"]
        if kind == "github_tree":
            commit = str(source["commit"])
            if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
                raise ValueError(f"{source_id}: commit must be a full 40-hex SHA")
            if not source.get("include"):
                raise ValueError(f"{source_id}: github_tree requires a non-empty include list")
        elif kind == "url_list":
            for entry in source["files"]:
                unknown = set(entry.get("expected", {})) - set(SUPPORTED_DIGESTS)
                if unknown:
                    raise ValueError(f"{source_id}/{entry['path']}: unsupported digests {unknown}")
        else:
            raise ValueError(f"{source_id}: unsupported kind {kind!r}")
    return config


def file_digests(path: Path) -> dict[str, Any]:
    """Return size, SHA-256, MD5 and the Git blob SHA-1 of a file."""

    size = path.stat().st_size
    sha256, md5 = hashlib.sha256(), hashlib.md5()
    blob = hashlib.sha1(f"blob {size}\0".encode())
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            sha256.update(chunk)
            md5.update(chunk)
            blob.update(chunk)
    return {
        "size_bytes": size,
        "sha256": sha256.hexdigest(),
        "md5": md5.hexdigest(),
        "git_blob_sha1": blob.hexdigest(),
    }


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def fetch_json(url: str) -> Any:
    with urllib.request.urlopen(_request(url), timeout=60) as response:
        return json.load(response)


def tls_context(intermediate: dict[str, str] | None) -> ssl.SSLContext | None:
    """Trust the system roots plus one pinned intermediate for servers that omit it.

    Chain verification to a system root still applies; the intermediate is only
    accepted when its DER bytes reproduce the declared SHA-256.
    """

    if intermediate is None:
        return None
    with urllib.request.urlopen(_request(intermediate["url"]), timeout=60) as response:
        der = response.read()
    if hashlib.sha256(der).hexdigest() != intermediate["sha256"]:
        raise ValueError(f"TLS intermediate {intermediate['url']} does not match its pinned SHA-256")
    context = ssl.create_default_context()
    context.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(der))
    return context


def download_url(
    url: str, destination: Path, context: ssl.SSLContext | None = None
) -> dict[str, str]:
    """Stream a URL into a temporary sibling, atomically replace the destination, and
    return the recorded response headers."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".part", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            with urllib.request.urlopen(_request(url), timeout=300, context=context) as response:
                headers = {
                    name: response.headers[name] for name in RECORDED_HEADERS if name in response.headers
                }
                for chunk in iter(lambda: response.read(_CHUNK), b""):
                    handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return headers


def tool_provenance(repo_root: Path = Path(".")) -> dict[str, Any]:
    """Describe the code and interpreter that perform a run."""

    def git(*args: str) -> str:
        return subprocess.run(
            ("git", *args), cwd=repo_root, check=True, capture_output=True, text=True
        ).stdout.strip()

    try:
        code = {"commit": git("rev-parse", "HEAD"), "worktree_clean": not git("status", "--porcelain")}
    except (OSError, subprocess.CalledProcessError):
        code = {"commit": None, "worktree_clean": None}
    module = Path(__file__)
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "user_agent": USER_AGENT,
        "code": code,
        "module_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _included(path: str, include: list[str], exclude: list[str]) -> bool:
    def matches(prefix: str) -> bool:
        return path == prefix or path.startswith(prefix.rstrip("/") + "/")

    return any(matches(p) for p in include) and not any(matches(p) for p in exclude)


def resolve_github_tree(source: dict[str, Any], fetch: JsonFetcher = fetch_json) -> list[AcquisitionFile]:
    """Expand a pinned GitHub tree into files with their Git blob SHA-1 expectations."""

    repo, commit = source["repository"], source["commit"]
    tree = fetch(f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1")
    if tree.get("truncated"):
        raise ValueError(f"{source['source_id']}: GitHub tree listing is truncated")
    include, exclude = list(source["include"]), list(source.get("exclude", []))
    files = [
        AcquisitionFile(
            source_id=source["source_id"],
            path=item["path"],
            url=f"https://raw.githubusercontent.com/{repo}/{commit}/"
            + urllib.parse.quote(item["path"]),
            expected={"git_blob_sha1": item["sha"]},
        )
        for item in tree["tree"]
        if item["type"] == "blob" and _included(item["path"], include, exclude)
    ]
    for prefix in include:
        if not any(_included(f.path, [prefix], []) for f in files):
            raise ValueError(f"{source['source_id']}: include {prefix!r} matched no files")
    return sorted(files, key=lambda f: f.path)


def resolve_sources(
    config: dict[str, Any],
    manifest: dict[str, Any],
    fetch: JsonFetcher = fetch_json,
) -> list[AcquisitionFile]:
    """Resolve every declared file, reusing GitHub listings already frozen in the manifest."""

    resolved: list[AcquisitionFile] = []
    for source in config["sources"]:
        source_id = source["source_id"]
        if source["kind"] == "github_tree":
            frozen = manifest["resolved_listings"].get(source_id)
            if frozen is None:
                files = resolve_github_tree(source, fetch)
                manifest["resolved_listings"][source_id] = [
                    {"path": f.path, "url": f.url, "expected": f.expected} for f in files
                ]
            else:
                files = [AcquisitionFile(source_id=source_id, **entry) for entry in frozen]
        else:
            files = [
                AcquisitionFile(
                    source_id=source_id,
                    path=entry["path"],
                    url=entry["url"],
                    expected=dict(entry.get("expected", {})),
                    tls_intermediate=entry.get("tls_intermediate"),
                )
                for entry in source["files"]
            ]
        resolved.extend(files)
    keys = [f.key for f in resolved]
    if len(keys) != len(set(keys)):
        raise ValueError("resolved acquisition paths are not unique")
    return resolved


def _mismatches(expected: dict[str, str], observed: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        name: {"expected": value, "observed": observed[name]}
        for name, value in expected.items()
        if observed[name] != value.lower()
    }


def _new_manifest(config: dict[str, Any], config_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": ACQUISITION_SCHEMA_VERSION,
        "acquisition": config["acquisition"]["name"],
        "config_sha256": config_sha256,
        "resolved_listings": {},
        "files": {},
        "runs": [],
    }


def acquire_sources(
    config_path: Path,
    root: Path,
    manifest_path: Path,
    *,
    execute: bool,
    fetch: JsonFetcher = fetch_json,
    download: Downloader = download_url,
    only_sources: set[str] | None = None,
    command: list[str] | None = None,
) -> dict[str, Any]:
    """Plan or execute the acquisition; persist the manifest after every verified file.

    Every executed run, including a pure re-verification, is appended to the
    manifest's ``runs`` with its command, code version, and outcome.
    """

    config = load_acquisition_config(config_path)
    config_sha256 = hashlib.sha256(Path(config_path).read_bytes()).hexdigest()
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("config_sha256") != config_sha256:
            raise ValueError("acquisition manifest belongs to a different config; create a new version")
    else:
        manifest = _new_manifest(config, config_sha256)

    files = resolve_sources(config, manifest, fetch)
    if only_sources is not None:
        unknown = only_sources - {s["source_id"] for s in config["sources"]}
        if unknown:
            raise ValueError(f"unknown source ids: {sorted(unknown)}")
        files = [f for f in files if f.source_id in only_sources]
    summary = {"planned": 0, "skipped_verified": 0, "downloaded": 0}
    run: dict[str, Any] = {}
    if execute:
        run = {
            "started_at": _now(),
            "finished_at": None,
            "status": "running",
            "command": list(command) if command is not None else None,
            "only_sources": sorted(only_sources) if only_sources else None,
            "tool": tool_provenance(),
        }
        manifest.setdefault("runs", []).append(run)
        write_json_atomic(manifest_path, manifest)
    try:
        _acquire_files(files, root, manifest, manifest_path, execute, download, summary)
    except BaseException as error:
        if execute:
            run.update(status="failed", finished_at=_now(), error=repr(error), summary=dict(summary))
            write_json_atomic(manifest_path, manifest)
        raise
    summary["recorded_files"] = len(manifest["files"])
    summary["declared_files"] = len(files)
    if execute:
        run.update(status="completed", finished_at=_now(), summary=dict(summary))
        write_json_atomic(manifest_path, manifest)
    return summary


def _acquire_files(
    files: list[AcquisitionFile],
    root: Path,
    manifest: dict[str, Any],
    manifest_path: Path,
    execute: bool,
    download: Downloader,
    summary: dict[str, int],
) -> None:
    for item in files:
        destination = root / item.source_id / item.path
        recorded = manifest["files"].get(item.key)
        if recorded and destination.exists():
            if destination.stat().st_size == recorded["size_bytes"] and (
                file_digests(destination)["sha256"] == recorded["sha256"]
            ):
                summary["skipped_verified"] += 1
                continue
        summary["planned"] += 1
        if not execute:
            continue
        headers = download(item.url, destination, tls_context(item.tls_intermediate)) or {}
        observed = file_digests(destination)
        mismatches = _mismatches(item.expected, observed)
        if mismatches:
            destination.unlink()
            raise ValueError(f"{item.key}: digest mismatch {mismatches}")
        manifest["files"][item.key] = {
            "source_id": item.source_id,
            "path": item.path,
            "url": item.url,
            "expected": item.expected,
            "verified_against": sorted(item.expected),
            "acquired_at": _now(),
            "response_headers": headers,
            **observed,
        }
        write_json_atomic(manifest_path, manifest)
        summary["downloaded"] += 1
