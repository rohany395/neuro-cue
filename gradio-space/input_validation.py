import os
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
GRADIO_UPLOAD_ROOT = Path(os.environ.get("GRADIO_UPLOAD_ROOT", "/tmp/gradio")).resolve()
MAX_TIMESTEPS = 30
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def normalize_timestep_limit(value, max_timesteps=MAX_TIMESTEPS):
    try:
        requested = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("n_timesteps must be a positive integer.") from exc

    if requested < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(requested, max_timesteps)


def _space_hostname(space_url=None):
    configured_url = space_url or os.environ.get("HF_SPACE_URL") or DEFAULT_SPACE_URL
    return urlparse(configured_url).hostname.lower()


def validate_space_file_url(url, space_url=None):
    parsed = urlparse(url)
    host = parsed.hostname.lower() if parsed.hostname else ""
    if parsed.scheme not in {"http", "https"} or host != _space_hostname(space_url):
        raise ValueError("video_ref url must point to the configured Hugging Face Space.")


def resolve_uploaded_video_path(video, upload_root=GRADIO_UPLOAD_ROOT, space_url=None):
    url = ""
    if isinstance(video, dict):
        url = video.get("url") or ""
        candidate = video.get("path") or ""
    elif isinstance(video, str):
        candidate = video
    elif hasattr(video, "name"):
        candidate = video.name
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}")

    if url:
        validate_space_file_url(url, space_url=space_url)

    if not candidate:
        raise ValueError("Uploaded video reference is missing a local path.")

    if "://" in candidate:
        raise ValueError("Uploaded video reference must use a local Gradio file path.")

    try:
        resolved = Path(candidate).resolve(strict=True)
    except OSError as exc:
        raise ValueError("Uploaded video file was not found.") from exc

    root = Path(upload_root).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Uploaded video path is outside the Gradio upload directory.") from exc

    if not resolved.is_file():
        raise ValueError("Uploaded video file was not found.")

    return str(resolved)
