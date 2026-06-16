"""Validation helpers for public Gradio API inputs."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

MAX_TIMESTEPS = 30
UPLOAD_ROOT = Path("/tmp/gradio").resolve()
DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"


def normalize_timestep_limit(value, default: int = 10) -> int:
    """Clamp public API timestep requests to the payload size the app can serve."""
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError):
        n_timesteps = default

    return max(1, min(n_timesteps, MAX_TIMESTEPS))


def _configured_space_hostname() -> str:
    configured_url = os.environ.get("HF_SPACE_URL") or os.environ.get("SPACE_URL") or DEFAULT_SPACE_URL
    return (urlparse(configured_url).hostname or "").lower()


def _path_under_upload_root(path: str) -> str:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_relative_to(UPLOAD_ROOT):
        raise ValueError("Video upload path must be under the Gradio upload directory.")
    return str(resolved)


def _path_from_file_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Video upload URL must use http or https.")

    if (parsed.hostname or "").lower() != _configured_space_hostname():
        raise ValueError("Video upload URL must point to the configured Hugging Face Space.")

    file_path = unquote(parsed.path)
    prefix = "/file="
    if not file_path.startswith(prefix):
        raise ValueError("Video upload URL must reference a Gradio uploaded file.")

    return file_path[len(prefix):]


def resolve_uploaded_video_path(video) -> tuple[str, str | None]:
    """
    Resolve a Gradio uploaded video reference to a trusted local path.

    Public clients can call this API directly, so path and URL fields are
    treated as untrusted and must refer to Gradio's upload directory.
    """
    if isinstance(video, dict):
        path = video.get("path") if isinstance(video.get("path"), str) else None
        url = video.get("url") if isinstance(video.get("url"), str) else None
        orig_name = video.get("orig_name") if isinstance(video.get("orig_name"), str) else None
        meta_name = video.get("meta", {}).get("name") if isinstance(video.get("meta"), dict) else None
        orig_name = orig_name or (meta_name if isinstance(meta_name, str) else None)
    elif isinstance(video, str):
        path = video
        url = None
        orig_name = None
    elif hasattr(video, "name"):
        path = video.name
        url = None
        orig_name = None
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}")

    if url:
        url_path = _path_under_upload_root(_path_from_file_url(url))
        if path and _path_under_upload_root(path) != url_path:
            raise ValueError("Video upload path and URL do not reference the same file.")
        return url_path, orig_name

    if not path:
        raise ValueError("Video upload reference must include a path or URL.")

    return _path_under_upload_root(path), orig_name
