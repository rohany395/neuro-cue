"""Validation helpers for public Gradio API inputs."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
GRADIO_UPLOAD_ROOT = Path(os.environ.get("GRADIO_UPLOAD_ROOT", "/tmp/gradio")).resolve()
MAX_TEXT_CHARS = 5000
MAX_TIMESTEPS = 30
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def normalize_timestep_limit(value: int | str) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("n_timesteps must be a positive integer.") from exc

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, MAX_TIMESTEPS)


def normalize_text_input(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("Provide either text or video input.")

    normalized = (text or "").strip()
    if not normalized:
        raise ValueError("Provide either text or video input.")
    if len(normalized) > MAX_TEXT_CHARS:
        raise ValueError(f"Text input must be {MAX_TEXT_CHARS} characters or fewer.")
    return normalized


def _configured_space_host() -> str:
    raw_url = (
        os.environ.get("HF_SPACE_URL")
        or os.environ.get("SPACE_URL")
        or os.environ.get("VITE_SPACE_URL")
    )
    if not raw_url:
        space_id = os.environ.get("SPACE_ID", "")
        if "/" in space_id:
            owner, name = space_id.split("/", 1)
            return f"{owner}-{name}.hf.space".lower()
        raw_url = DEFAULT_SPACE_URL

    return (urlparse(raw_url).hostname or "").lower()


def _extract_upload_path_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Video file reference is invalid.")

    if (parsed.hostname or "").lower() != _configured_space_host():
        raise ValueError("Video file reference is invalid.")

    decoded_path = unquote(parsed.path)
    marker = "/file="
    marker_index = decoded_path.find(marker)
    if marker_index == -1:
        raise ValueError("Video file reference is invalid.")

    return decoded_path[marker_index + len(marker) :]


def _resolve_upload_path(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise ValueError("Video file reference is invalid.")
    if "\x00" in path:
        raise ValueError("Video file reference is invalid.")
    if urlparse(path).scheme:
        raise ValueError("Video file reference is invalid.")

    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError("Video file reference is invalid.")

    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, RuntimeError, OSError) as exc:
        raise ValueError("Video file reference is invalid.") from exc

    try:
        resolved.relative_to(GRADIO_UPLOAD_ROOT)
    except ValueError as exc:
        raise ValueError("Video file reference is invalid.") from exc

    return str(resolved)


def _get_dict_value(video: dict, key: str) -> str:
    value = video.get(key)
    return value if isinstance(value, str) else ""


def resolve_uploaded_video_path(video: object) -> tuple[str, str | None]:
    """Return a safe local upload path and original filename for a Gradio file ref."""
    orig_name = None

    if isinstance(video, dict):
        path = _get_dict_value(video, "path")
        url = _get_dict_value(video, "url")
        orig_name = _get_dict_value(video, "orig_name") or None

        if not path and not url:
            raise ValueError("Video file reference is invalid.")

        url_path = _extract_upload_path_from_url(url) if url else ""
        selected_path = path or url_path
        resolved_path = _resolve_upload_path(selected_path)

        if url_path:
            resolved_url_path = _resolve_upload_path(url_path)
            if resolved_path != resolved_url_path:
                raise ValueError("Video file reference is invalid.")

        return resolved_path, orig_name

    if isinstance(video, str):
        return _resolve_upload_path(video), orig_name

    name = getattr(video, "name", None)
    if isinstance(name, str):
        return _resolve_upload_path(name), orig_name

    raise ValueError("Unrecognized video input type.")


def video_extension_for(path: str, orig_name: str | None = None) -> str | None:
    lower_path = path.lower()
    if lower_path.endswith(VIDEO_EXTENSIONS):
        return None

    lower_name = (orig_name or "").lower()
    for ext in VIDEO_EXTENSIONS:
        if lower_name.endswith(ext):
            return ext

    return ".mp4"
