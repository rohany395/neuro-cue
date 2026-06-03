"""Validation helpers for Gradio-uploaded video references."""

from pathlib import Path
from urllib.parse import unquote, urlparse


MAX_VIDEO_BYTES = 50 * 1024 * 1024
GRADIO_UPLOAD_ROOT = Path("/tmp/gradio").resolve()
DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def _configured_space_hostname() -> str:
    from os import environ

    space_url = environ.get("HF_SPACE_URL") or environ.get("VITE_SPACE_URL") or DEFAULT_SPACE_URL
    return (urlparse(space_url).hostname or "").lower()


def _extract_path_from_file_url(url: str) -> str:
    parsed = urlparse(url)
    if (parsed.hostname or "").lower() != _configured_space_hostname():
        raise ValueError("video_ref url must point to the configured Hugging Face Space.")

    path = unquote(parsed.path)
    if path.startswith("/file="):
        return path[len("/file="):]

    raise ValueError("video_ref url must point to a Hugging Face upload.")


def _validate_upload_path(path: str) -> Path:
    if not isinstance(path, str) or not path.strip() or "\0" in path:
        raise ValueError("video_ref path is invalid.")

    raw_path = Path(path)
    if not raw_path.is_absolute():
        raise ValueError("video_ref path must point to a Hugging Face upload.")

    try:
        resolved_path = raw_path.resolve(strict=True)
        resolved_path.relative_to(GRADIO_UPLOAD_ROOT)
    except (FileNotFoundError, RuntimeError, ValueError):
        raise ValueError("video_ref path must point to a Hugging Face upload.")

    if not resolved_path.is_file():
        raise ValueError("video_ref path must point to a file upload.")

    if resolved_path.stat().st_size > MAX_VIDEO_BYTES:
        max_mb = MAX_VIDEO_BYTES // (1024 * 1024)
        raise ValueError(f"Video must be {max_mb} MB or smaller.")

    return resolved_path


def validate_video_reference(video) -> tuple[str, str | None]:
    """Return a validated local upload path and original filename, if available."""
    if isinstance(video, dict):
        raw_path = video.get("path")
        raw_url = video.get("url")
        orig_name = video.get("orig_name")
    elif isinstance(video, str):
        raw_path = video
        raw_url = None
        orig_name = None
    elif hasattr(video, "name"):
        raw_path = video.name
        raw_url = None
        orig_name = getattr(video, "orig_name", None)
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}")

    if not raw_path and raw_url:
        raw_path = _extract_path_from_file_url(raw_url)
    elif raw_path and raw_url:
        url_path = _extract_path_from_file_url(raw_url)
        if _validate_upload_path(raw_path) != _validate_upload_path(url_path):
            raise ValueError("video_ref path and url do not reference the same upload.")

    validated_path = _validate_upload_path(raw_path)
    return str(validated_path), orig_name if isinstance(orig_name, str) else None
