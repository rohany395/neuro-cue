"""Validation helpers for public Gradio API inputs."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse


DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
UPLOAD_ROOT = Path(os.environ.get("GRADIO_TEMP_DIR", "/tmp/gradio")).resolve()
MAX_TEXT_CHARS = 5000
MAX_TIMESTEPS = 30
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def normalize_timestep_limit(value: object) -> int:
    """Return a bounded positive timestep count for response-size control."""
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError):
        raise ValueError("n_timesteps must be a positive integer.") from None

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, MAX_TIMESTEPS)


def validate_text_input(text: object) -> str:
    if not isinstance(text, str):
        raise ValueError("Text input must be a string.")

    trimmed = text.strip()
    if not trimmed:
        raise ValueError("Provide either text or video input.")

    if len(trimmed) > MAX_TEXT_CHARS:
        raise ValueError(f"Text input must be {MAX_TEXT_CHARS} characters or fewer.")

    return trimmed


def _configured_space_hostname() -> str:
    raw_url = os.environ.get("HF_SPACE_URL") or os.environ.get("SPACE_URL") or DEFAULT_SPACE_URL
    return urlparse(raw_url).hostname or urlparse(DEFAULT_SPACE_URL).hostname or ""


def _file_path_from_space_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("video_ref url must use http or https.")

    if parsed.hostname != _configured_space_hostname():
        raise ValueError("video_ref url must point to the configured Hugging Face Space.")

    marker = "/file="
    if marker not in parsed.path:
        raise ValueError("video_ref url must reference a Gradio uploaded file.")

    return unquote(parsed.path.split(marker, 1)[1])


def _path_under_upload_root(path_value: str) -> Path:
    if not path_value:
        raise ValueError("video_ref must include a path or url.")

    path = Path(path_value)
    if not path.is_absolute():
        raise ValueError("video_ref path must be an absolute Gradio upload path.")

    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(UPLOAD_ROOT)
    except ValueError:
        raise ValueError("video_ref path must be under the Gradio upload directory.") from None

    if not resolved.is_file():
        raise ValueError("video_ref file does not exist.")

    return resolved


def resolve_uploaded_video_path(video: object) -> tuple[str, str | None]:
    """Validate a Gradio video file reference and return a local path plus original name."""
    if isinstance(video, dict):
        raw_path = video.get("path")
        raw_url = video.get("url")
        orig_name = video.get("orig_name") or (video.get("meta") or {}).get("name")
    elif isinstance(video, str):
        raw_path = video
        raw_url = None
        orig_name = None
    elif hasattr(video, "name"):
        raw_path = video.name
        raw_url = None
        orig_name = None
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}")

    url_path = _file_path_from_space_url(raw_url) if isinstance(raw_url, str) and raw_url else None
    path_value = raw_path if isinstance(raw_path, str) and raw_path else url_path
    resolved = _path_under_upload_root(path_value)

    if url_path is not None:
        url_resolved = _path_under_upload_root(url_path)
        if url_resolved != resolved:
            raise ValueError("video_ref path and url do not reference the same file.")

    return str(resolved), orig_name if isinstance(orig_name, str) else None


def ensure_video_extension(video_path: str, orig_name: str | None = None) -> str:
    """TRIBE validates by extension; copy extensionless Gradio blobs to a safe suffixed path."""
    path = Path(video_path)
    if path.suffix.lower() in VIDEO_EXTENSIONS:
        return str(path)

    ext = ".mp4"
    if orig_name:
        orig_ext = Path(orig_name).suffix.lower()
        if orig_ext in VIDEO_EXTENSIONS:
            ext = orig_ext

    new_path = path.with_name(path.name + ext)
    if new_path != path:
        shutil.copyfile(path, new_path)
    return str(new_path)
