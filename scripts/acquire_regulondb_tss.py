"""Acquire RegulonDB high-throughput TSS datasets and PromoterSet through GraphQL, byte for byte."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import yaml

from capsprom.state import write_json_atomic

TSS_FIELDS = "_id chromosome leftEndPosition rightEndPosition pos_1 strand datasetIds"
DATASET_FIELDS = "_id referenceGenome publications{pmid doi title} sourceSerie{series{sourceId}} sample{title}"
FILE_FIELDS = "fileName fileFormat version rdbVersion creationDate license citation columnsDetails content"


def _post(endpoint: str, query: str) -> bytes:
    request = urllib.request.Request(
        endpoint, data=json.dumps({"query": query}).encode("utf-8"),
        headers={"content-type": "application/json", "user-agent": "capsprom-acquisition"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        body = response.read()
    if "errors" in json.loads(body):
        raise RuntimeError(f"GraphQL error for {query[:80]}: {body[:300]!r}")
    return body


def _store(root: Path, name: str, query: str, body: bytes) -> dict:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return {"path": name, "query": query, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/regulondb_tss_acquisition_v1.yaml"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))["acquisition"]
    root, endpoint, size = Path(config["root"]), config["endpoint"], int(config["page_size"])
    started = datetime.now(UTC).isoformat(timespec="seconds")
    entries: list[dict] = []
    counts: dict[str, int] = {}
    for dataset in config["ht_tss_datasets"]:
        query = f'{{getDatasetByID(datasetID:"{dataset}"){{{DATASET_FIELDS}}}}}'
        entries.append(_store(root, f"ht_tss/{dataset}/metadata.json", query, _post(endpoint, query)))
        page, total = 0, 0
        while True:
            query = f'{{getAllTSSOfDataset(datasetId:"{dataset}",limit:{size},page:{page}){{{TSS_FIELDS}}}}}'
            body = _post(endpoint, query)
            rows = json.loads(body)["data"]["getAllTSSOfDataset"] or []
            if not rows:
                break
            entries.append(_store(root, f"ht_tss/{dataset}/page_{page:04d}.json", query, body))
            total += len(rows)
            page += 1
            if len(rows) < size:
                break
        counts[dataset] = total
    for name in config["files"]:
        query = f'{{getDataOfFile(fileName:"{name}"){{{FILE_FIELDS}}}}}'
        entries.append(_store(root, f"files/{name}.json", query, _post(endpoint, query)))
    manifest = {
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "endpoint": endpoint, "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "ht_tss_row_counts": counts, "files": entries,
    }
    write_json_atomic(Path(config["manifest"]), manifest)
    print(json.dumps({"ht_tss_row_counts": counts, "responses": len(entries)}, indent=2))


if __name__ == "__main__":
    main()
