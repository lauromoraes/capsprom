"""Tracking-store path resolution shared by experiment runners."""

from pathlib import Path

from .config import ExperimentConfig


def resolve_tracking_uri(config: ExperimentConfig) -> str:
    raw = config.tracking.tracking_uri
    if raw.startswith("sqlite:///") and not raw.startswith("sqlite:////"):
        relative_path = Path(raw.removeprefix("sqlite:///"))
        database_path = (config.path.parent.parent / relative_path).resolve()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{database_path.as_posix()}"
    if "://" in raw or raw.startswith("file:"):
        return raw
    path = Path(raw)
    if not path.is_absolute():
        path = config.path.parent.parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve().as_uri()
