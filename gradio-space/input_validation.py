"""Input validation helpers for public prediction APIs."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

MAX_TEXT_CHARS = 5000
MAX_TIMESTEPS = 30
DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
DEFAULT_UPLOAD_ROOT = Path("/tmp/gradio")
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def normalize_timestep_limit(value, max_timesteps: int = MAX_TIMESTEPS) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError):
        raise ValueError("n_timesteps must be a positive integer.") from None

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, max_timesteps)


def validate_text_input(text: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    trimmed = (text or "").strip()

    if not trimmed:
        raise ValueError("Text input is required.")

    if len(trimmed) > max_chars:
        raise ValueError(f"Text input must be {max_chars} characters or fewer.")

    return trimmed


def _configured_space_hosts() -> set[str]:
    urls = [
        os.environ.get("HF_SPACE_URL"),
        os.environ.get("SPACE_URL"),
        os.environ.get("GRADIO_SPACE_URL"),
    ]
    hosts: set[str] = set()
    for url in urls:
        if not url:
            continue
        try:
            host = urlparse(url).hostname
        except ValueError:
            continue
        if host:
            hosts.add(host.lower())

    if hosts:
        return hosts

    host = urlparse(DEFAULT_SPACE_URL).hostname
    if host:
        hosts.add(host.lower())
    return hosts


def _path_from_space_file_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except ValueError:
        raise ValueError("video_ref url is invalid.") from None

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("video_ref url is invalid.")

    if parsed.hostname.lower() not in _configured_space_hosts():
        raise ValueError("video_ref url must point to the configured Hugging Face Space.")

    path = unquote(parsed.path or "")
    marker = "/file="
    if marker not in path:
        raise ValueError("video_ref url must reference a Gradio uploaded file.")

    return path.split(marker, 1)[1]


def _normalize_ref_path(path: str) -> str:
    if path.startswith("file="):
        return path.removeprefix("file=")
    return path


def _resolve_upload_path(path: str, upload_root: Path) -> Path:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("video_ref must include a valid path.")

    normalized = _normalize_ref_path(path.strip())
    if normalized.startswith(("http://", "https://")):
        normalized = _path_from_space_file_url(normalized)

    candidate = Path(normalized)
    if not candidate.is_absolute():
        raise ValueError("video_ref path must be an absolute Gradio upload path.")

    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        raise ValueError("video_ref path does not exist.") from None

    root = upload_root.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError("video_ref path must stay inside the Gradio upload directory.") from None

    if not resolved.is_file():
        raise ValueError("video_ref path must reference an uploaded file.")

    return resolved


def _orig_name_from_ref(ref: dict) -> str | None:
    orig_name = ref.get("orig_name")
    if isinstance(orig_name, str):
        return orig_name

    meta = ref.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("name"), str):
        return meta["name"]

    return None


def resolve_uploaded_video_path(
    video,
    upload_root: Path = DEFAULT_UPLOAD_ROOT,
) -> tuple[str, str | None]:
    """Return a local Gradio upload path after validating the client file ref."""

    path = None
    url = None
    orig_name = None

    if isinstance(video, dict):
        path = video.get("path")
        url = video.get("url")
        orig_name = _orig_name_from_ref(video)
    elif isinstance(video, str):
        path = video
    elif hasattr(video, "name"):
        path = video.name
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}")

    if not path and not url:
        raise ValueError("video_ref must include path or url.")

    resolved_path = _resolve_upload_path(path, upload_root) if path else None
    resolved_url_path = (
        _resolve_upload_path(_path_from_space_file_url(url), upload_root) if url else None
    )

    if resolved_path and resolved_url_path and resolved_path != resolved_url_path:
        raise ValueError("video_ref path and url must reference the same upload.")

    resolved = resolved_path or resolved_url_path
    if resolved is None:
        raise ValueError("video_ref must include path or url.")

    return str(resolved), orig_name


def extension_for_video_path(path: str, orig_name: str | None = None) -> str:
    if Path(path).suffix.lower() in ALLOWED_VIDEO_EXTENSIONS:
        return ""

    if orig_name:
        suffix = Path(orig_name).suffix.lower()
        if suffix in ALLOWED_VIDEO_EXTENSIONS:
            return suffix

    return ".mp4"
