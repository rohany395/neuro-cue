"""Validation helpers for public prediction API inputs."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse


DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
DEFAULT_UPLOAD_ROOT = Path("/tmp/gradio")
MAX_TIMESTEPS = 30
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def normalize_timestep_limit(value, *, max_timesteps: int = MAX_TIMESTEPS) -> int:
    """Return a positive timestep count capped for public JSON responses."""
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("n_timesteps must be a positive integer.") from exc

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, max_timesteps)


def _configured_space_host(space_url: str | None = None) -> str:
    raw_url = space_url or os.environ.get("HF_SPACE_URL") or os.environ.get("SPACE_URL") or DEFAULT_SPACE_URL
    return urlparse(raw_url).hostname.lower()


def _upload_root(upload_root: str | Path | None = None) -> Path:
    return Path(upload_root or os.environ.get("GRADIO_TEMP_DIR") or DEFAULT_UPLOAD_ROOT).resolve()


def _validate_local_upload_path(path_value: str, upload_root: str | Path | None = None) -> str:
    if not path_value:
        raise ValueError("Video file reference is missing a path.")

    candidate = Path(path_value)
    if not candidate.is_absolute():
        raise ValueError("Video file path must be absolute.")

    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("Uploaded video file does not exist.") from exc

    root = _upload_root(upload_root)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Video file path must be under the Gradio upload directory.") from exc

    return str(resolved)


def _path_from_file_url(url_value: str, *, space_url: str | None = None) -> str:
    try:
        parsed = urlparse(url_value)
    except ValueError as exc:
        raise ValueError("Video file URL is invalid.") from exc

    expected_host = _configured_space_host(space_url)
    if parsed.hostname is None or parsed.hostname.lower() != expected_host:
        raise ValueError("Video file URL must point to the configured Hugging Face Space.")

    path = unquote(parsed.path)
    if not path.startswith("/file="):
        raise ValueError("Video file URL must use the Gradio /file= upload route.")

    return path[len("/file="):]


def get_original_filename(video) -> str | None:
    """Return the client filename from a Gradio file-like object or FileData dict."""
    if isinstance(video, dict):
        if isinstance(video.get("orig_name"), str):
            return video["orig_name"]
        meta = video.get("meta")
        if isinstance(meta, dict) and isinstance(meta.get("name"), str):
            return meta["name"]

    return None


def resolve_uploaded_video_path(
    video,
    *,
    upload_root: str | Path | None = None,
    space_url: str | None = None,
) -> str:
    """Resolve and validate a Gradio-uploaded video path.

    Public API callers can submit FileData dictionaries, so both local paths and
    URLs must resolve to existing files inside Gradio's upload directory.
    """
    path_value = None
    url_path = None

    if isinstance(video, dict):
        if isinstance(video.get("path"), str):
            path_value = video["path"]
        if isinstance(video.get("url"), str):
            url_path = _path_from_file_url(video["url"], space_url=space_url)
    elif isinstance(video, str):
        path_value = video
    elif hasattr(video, "name"):
        path_value = video.name
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}")

    if path_value is None and url_path is None:
        raise ValueError("Video input must include a path or URL.")

    resolved_path = (
        _validate_local_upload_path(path_value, upload_root)
        if path_value is not None
        else None
    )
    resolved_url_path = (
        _validate_local_upload_path(url_path, upload_root)
        if url_path is not None
        else None
    )

    if resolved_path and resolved_url_path and resolved_path != resolved_url_path:
        raise ValueError("Video path and URL refer to different uploaded files.")

    return resolved_path or resolved_url_path
