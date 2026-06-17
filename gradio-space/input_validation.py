import os
from pathlib import Path
from urllib.parse import unquote
from urllib.parse import urlparse


DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
MAX_TEXT_CHARS = 5000
MAX_TIMESTEPS = 30
GRADIO_UPLOAD_ROOT = Path("/tmp/gradio")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def normalize_timestep_limit(value: int | str | float) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError):
        raise ValueError("n_timesteps must be a positive integer.") from None

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, MAX_TIMESTEPS)


def validate_text_input(text: str) -> str:
    trimmed = (text or "").strip()
    if not trimmed:
        raise ValueError("Text input is required.")

    if len(trimmed) > MAX_TEXT_CHARS:
        raise ValueError(f"Text input must be {MAX_TEXT_CHARS} characters or fewer.")

    return trimmed


def configured_space_hostname(space_url: str | None = None) -> str:
    configured_url = (
        space_url
        or os.environ.get("HF_SPACE_URL")
        or os.environ.get("SPACE_URL")
        or DEFAULT_SPACE_URL
    )
    hostname = urlparse(configured_url).hostname
    if not hostname:
        raise ValueError("Configured Hugging Face Space URL is invalid.")
    return hostname.lower()


def _resolve_under_upload_root(path: str) -> Path:
    try:
        resolved = Path(path).resolve(strict=False)
        upload_root = GRADIO_UPLOAD_ROOT.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        raise ValueError("Invalid uploaded video path.") from None

    if not resolved.is_absolute():
        raise ValueError("Uploaded video path must be absolute.")

    try:
        resolved.relative_to(upload_root)
    except ValueError:
        raise ValueError("Uploaded video path is outside the Gradio upload directory.") from None

    return resolved


def _path_from_space_file_url(url: str, space_url: str | None) -> Path:
    parsed = urlparse(url)
    allowed_host = configured_space_hostname(space_url)
    if parsed.hostname is None or parsed.hostname.lower() != allowed_host:
        raise ValueError("Uploaded video URL must point to the configured Hugging Face Space.")

    file_prefix = "/file="
    if not parsed.path.startswith(file_prefix):
        raise ValueError("Uploaded video URL must reference a Gradio uploaded file.")

    return _resolve_under_upload_root(unquote(parsed.path[len(file_prefix):]))


def resolve_uploaded_video_path(video, space_url: str | None = None) -> tuple[str, str | None]:
    if isinstance(video, dict):
        path_value = video.get("path") or video.get("name")
        url_value = video.get("url")
        meta = video.get("meta")
        orig_name = video.get("orig_name") or (
            meta.get("name") if isinstance(meta, dict) else None
        )
    elif isinstance(video, str):
        path_value = video
        url_value = None
        orig_name = None
    elif hasattr(video, "name"):
        path_value = video.name
        url_value = None
        orig_name = getattr(video, "orig_name", None)
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}.")

    resolved_path = None
    if isinstance(path_value, str) and path_value:
        resolved_path = _resolve_under_upload_root(path_value)

    resolved_url_path = None
    if isinstance(url_value, str) and url_value:
        resolved_url_path = _path_from_space_file_url(url_value, space_url)

    if resolved_path is None and resolved_url_path is None:
        raise ValueError("Could not extract uploaded video path.")

    if (
        resolved_path is not None
        and resolved_url_path is not None
        and resolved_path != resolved_url_path
    ):
        raise ValueError("Uploaded video path and URL do not reference the same file.")

    return str(resolved_path or resolved_url_path), orig_name
