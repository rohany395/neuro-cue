import os
from pathlib import Path
from urllib.parse import unquote, urlparse


MAX_TIMESTEPS = 30
DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
UPLOAD_ROOT = Path(os.environ.get("GRADIO_UPLOAD_ROOT", "/tmp/gradio")).resolve()
ALLOWED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def normalize_timestep_limit(value) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("n_timesteps must be a positive integer.") from exc

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, MAX_TIMESTEPS)


def has_video_extension(path: str) -> bool:
    return path.lower().endswith(ALLOWED_VIDEO_EXTENSIONS)


def extension_from_name(name: str | None, default: str = ".mp4") -> str:
    if name and has_video_extension(name):
        return "." + name.rsplit(".", 1)[-1].lower()
    return default


def _space_hostname() -> str:
    return urlparse(os.environ.get("HF_SPACE_URL") or DEFAULT_SPACE_URL).hostname.lower()


def _validate_upload_path(path: str) -> str:
    if not path:
        raise ValueError("video_ref must include a path.")

    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError("video_ref path must be an absolute Gradio upload path.")

    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(UPLOAD_ROOT)
    except ValueError as exc:
        raise ValueError("video_ref path must be under the Gradio upload directory.") from exc

    return str(resolved)


def _path_from_space_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("video_ref url is invalid.")

    if parsed.hostname.lower() != _space_hostname():
        raise ValueError("video_ref url must point to the configured Hugging Face Space.")

    decoded_path = unquote(parsed.path)
    marker = "file="
    marker_index = decoded_path.find(marker)
    if marker_index == -1:
        raise ValueError("video_ref url must be a Gradio file URL.")

    return decoded_path[marker_index + len(marker):]


def resolve_uploaded_video_path(video) -> tuple[str, str | None]:
    if isinstance(video, dict):
        path = video.get("path")
        url = video.get("url")
        meta = video.get("meta")
        orig_name = video.get("orig_name") or (
            meta.get("name") if isinstance(meta, dict) else None
        )
    elif isinstance(video, str):
        path = video
        url = None
        orig_name = None
    elif hasattr(video, "name"):
        path = video.name
        url = None
        orig_name = getattr(video, "orig_name", None)
    else:
        raise ValueError(f"Unrecognized video input type: {type(video).__name__}")

    if not isinstance(path, str) and isinstance(url, str):
        path = _path_from_space_url(url)
    elif isinstance(url, str):
        url_path = _validate_upload_path(_path_from_space_url(url))
        path = _validate_upload_path(path)
        if path != url_path:
            raise ValueError("video_ref path and url do not refer to the same upload.")
        return path, orig_name if isinstance(orig_name, str) else None

    if not isinstance(path, str):
        raise ValueError("video_ref must include a path or url.")

    return _validate_upload_path(path), orig_name if isinstance(orig_name, str) else None
