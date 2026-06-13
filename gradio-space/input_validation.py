from __future__ import annotations

import os
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse

MAX_TEXT_CHARS = 5000
MAX_TIMESTEPS = 30
UPLOAD_ROOT = Path(os.environ.get("GRADIO_UPLOAD_ROOT", "/tmp/gradio")).resolve()
VALID_VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def normalize_timestep_limit(value: int | str, max_timesteps: int = MAX_TIMESTEPS) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("n_timesteps must be a positive integer.") from exc

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, max_timesteps)


def validate_text_input(text: str | None, max_chars: int = MAX_TEXT_CHARS) -> str:
    trimmed = (text or "").strip()
    if not trimmed:
        raise ValueError("Text input is required.")
    if len(trimmed) > max_chars:
        raise ValueError(f"Text input must be {max_chars} characters or fewer.")
    return trimmed


def _path_from_file_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        raise ValueError("video_ref url must be an uploaded Gradio file URL.")

    path = parsed.path
    if path.startswith("/file="):
        path = path[len("/file="):]
    elif path.startswith("file="):
        path = path[len("file="):]
    else:
        raise ValueError("video_ref url must reference an uploaded Gradio file.")

    return unquote(path)


def _resolve_under_upload_root(path: str | os.PathLike[str]) -> Path:
    if not path:
        raise ValueError("Uploaded video path is required.")

    try:
        resolved = Path(path).expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("Uploaded video file was not found.") from exc

    try:
        resolved.relative_to(UPLOAD_ROOT)
    except ValueError as exc:
        raise ValueError("Uploaded video path is not allowed.") from exc

    if not resolved.is_file():
        raise ValueError("Uploaded video path must be a file.")

    return resolved


def resolve_uploaded_video_path(video: object) -> tuple[str, str | None]:
    """Return a validated local Gradio upload path and original filename."""
    if not video:
        raise ValueError("Video input is required.")

    orig_name = None
    url_path = None

    if isinstance(video, dict):
        raw_path = video.get("path")
        raw_url = video.get("url")
        orig_name = video.get("orig_name")
        if not orig_name and isinstance(video.get("meta"), dict):
            orig_name = video["meta"].get("name")
        if raw_url:
            url_path = _path_from_file_url(str(raw_url))
        path = raw_path or url_path
    elif isinstance(video, str):
        path = video
    elif hasattr(video, "name"):
        path = video.name
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}")

    resolved = _resolve_under_upload_root(path)

    if url_path:
        url_resolved = _resolve_under_upload_root(url_path)
        if url_resolved != resolved:
            raise ValueError("video_ref path and url do not reference the same upload.")

    return str(resolved), str(orig_name) if orig_name else None


def ensure_video_extension(video_path: str, orig_name: str | None = None) -> str:
    resolved = _resolve_under_upload_root(video_path)
    if resolved.name.lower().endswith(VALID_VIDEO_EXTENSIONS):
        return str(resolved)

    suffix = Path(orig_name or "").suffix.lower()
    ext = suffix if suffix in VALID_VIDEO_EXTENSIONS else ".mp4"
    target = resolved.with_name(f"{resolved.name}{ext}")
    shutil.copy2(resolved, target)
    return str(_resolve_under_upload_root(target))
