from __future__ import annotations

import os
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

MAX_TIMESTEPS = 30
UPLOAD_ROOT = Path(tempfile.gettempdir()) / "gradio"
DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def normalize_timestep_limit(value, max_timesteps: int = MAX_TIMESTEPS) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError):
        raise ValueError("n_timesteps must be a positive integer.") from None

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, max_timesteps)


def _configured_space_host() -> str:
    raw_url = (
        os.environ.get("HF_SPACE_URL")
        or os.environ.get("SPACE_URL")
        or DEFAULT_SPACE_URL
    )
    hostname = urlparse(raw_url).hostname
    if not hostname:
        raise ValueError("Configured Space URL must include a hostname.")
    return hostname.lower()


def _resolve_uploaded_path(path: str, upload_root: Path = UPLOAD_ROOT) -> Path:
    if not path or not Path(path).is_absolute():
        raise ValueError("Uploaded video path must be an absolute Gradio upload path.")

    upload_root_resolved = upload_root.resolve(strict=False)
    candidate = Path(path).resolve(strict=True)

    if candidate == upload_root_resolved or upload_root_resolved not in candidate.parents:
        raise ValueError("Uploaded video path must stay under Gradio's upload directory.")

    return candidate


def _path_from_file_url(url: str, expected_host: str | None = None) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Uploaded video URL must use https.")

    expected = (expected_host or _configured_space_host()).lower()
    if parsed.hostname is None or parsed.hostname.lower() != expected:
        raise ValueError("Uploaded video URL must point to the configured Hugging Face Space.")

    marker = "/file="
    if not parsed.path.startswith(marker):
        raise ValueError("Uploaded video URL must use the Gradio file route.")

    return unquote(parsed.path[len(marker):])


def resolve_uploaded_video_path(video, upload_root: Path = UPLOAD_ROOT) -> tuple[str, str | None]:
    if isinstance(video, dict):
        raw_path = video.get("path")
        raw_url = video.get("url")
        meta = video.get("meta") if isinstance(video.get("meta"), dict) else {}
        orig_name = video.get("orig_name") or meta.get("name")
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

    if not raw_path and raw_url:
        raw_path = _path_from_file_url(raw_url)

    resolved_path = _resolve_uploaded_path(str(raw_path or ""), upload_root)

    if raw_url:
        url_path = _resolve_uploaded_path(_path_from_file_url(raw_url), upload_root)
        if url_path != resolved_path:
            raise ValueError("Uploaded video path and URL do not reference the same file.")

    return str(resolved_path), orig_name


def ensure_video_extension(video_path: str, orig_name: str | None = None) -> str:
    if Path(video_path).suffix.lower() in VIDEO_EXTENSIONS:
        return video_path

    if orig_name and Path(orig_name).suffix.lower() in VIDEO_EXTENSIONS:
        suffix = Path(orig_name).suffix.lower()
    else:
        suffix = ".mp4"

    import shutil

    new_path = f"{video_path}{suffix}"
    shutil.copy(video_path, new_path)
    return new_path
