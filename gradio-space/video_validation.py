"""Validation helpers for Gradio-uploaded video references."""

from pathlib import Path
from urllib.parse import urlparse


MAX_VIDEO_BYTES = 50 * 1024 * 1024
UPLOAD_ROOT = Path("/tmp/gradio")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


class VideoReferenceError(ValueError):
    """Raised when a client-supplied video reference is not a Gradio upload."""


def get_original_name(video) -> str | None:
    if isinstance(video, dict):
        orig_name = video.get("orig_name")
        if isinstance(orig_name, str):
            return orig_name

        meta = video.get("meta")
        if isinstance(meta, dict) and isinstance(meta.get("name"), str):
            return meta["name"]

    return None


def _extract_video_path(video) -> str:
    if isinstance(video, dict):
        video_path = video.get("path")
    elif isinstance(video, str):
        video_path = video
    elif hasattr(video, "name"):
        video_path = video.name
    else:
        raise VideoReferenceError(
            f"Unrecognized video input type: {type(video).__name__}"
        )

    if not isinstance(video_path, str) or not video_path.strip():
        raise VideoReferenceError("Video reference must include an uploaded file path.")

    return video_path.strip()


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme)


def normalize_uploaded_video_path(
    video,
    upload_root: Path | str = UPLOAD_ROOT,
    max_bytes: int = MAX_VIDEO_BYTES,
) -> str:
    """Return a real local path for a Gradio upload, or reject forged references."""

    video_path = _extract_video_path(video)
    if _looks_like_url(video_path):
        raise VideoReferenceError("Video reference path must be a local upload path.")

    candidate = Path(video_path)
    if not candidate.is_absolute():
        raise VideoReferenceError("Video reference path must be absolute.")

    root = Path(upload_root).resolve()
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise VideoReferenceError("Uploaded video file was not found.") from exc

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise VideoReferenceError("Video reference must point to a Gradio upload.") from exc

    if not resolved.is_file():
        raise VideoReferenceError("Video reference must point to a file.")

    if resolved.stat().st_size > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise VideoReferenceError(f"Video must be {max_mb} MB or smaller.")

    return str(resolved)
