import os
from pathlib import Path
from urllib.parse import unquote, urlparse

MAX_TIMESTEPS = 30
UPLOAD_ROOT = Path(os.environ.get("GRADIO_TEMP_DIR", "/tmp/gradio")).resolve()
DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/"
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi")


def normalize_timestep_limit(value, max_timesteps: int = MAX_TIMESTEPS) -> int:
    try:
        n_timesteps = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("n_timesteps must be a positive integer.") from exc

    if n_timesteps < 1:
        raise ValueError("n_timesteps must be a positive integer.")

    return min(n_timesteps, max_timesteps)


def video_orig_name(video) -> str | None:
    if isinstance(video, dict):
        orig_name = video.get("orig_name")
        if isinstance(orig_name, str) and orig_name:
            return orig_name
        meta_name = video.get("meta", {}).get("name") if isinstance(video.get("meta"), dict) else None
        if isinstance(meta_name, str) and meta_name:
            return meta_name
    return None


def has_video_extension(path: str) -> bool:
    return path.lower().endswith(VIDEO_EXTENSIONS)


def extension_from_orig_name(orig_name: str | None) -> str:
    if orig_name and has_video_extension(orig_name):
        return "." + orig_name.rsplit(".", 1)[-1].lower()
    return ".mp4"


def resolve_uploaded_video_path(video, allowed_space_urls: list[str] | None = None) -> str:
    """Return a local Gradio upload path, rejecting arbitrary server paths/URLs."""
    path = _extract_video_path(video)
    url = _extract_video_url(video)

    url_path = _local_path_from_url(url, allowed_space_urls) if url else None
    local_path = _validate_upload_path(path) if path and not _looks_like_url(path) else None

    if path and _looks_like_url(path):
        path_url_path = _local_path_from_url(path, allowed_space_urls)
        if url_path is not None and path_url_path != url_path:
            raise ValueError("video path and url refer to different uploads.")
        url_path = path_url_path

    if local_path is not None and url_path is not None and local_path != url_path:
        raise ValueError("video path and url refer to different uploads.")

    resolved = local_path or url_path
    if resolved is None:
        raise ValueError("video must reference a Gradio upload.")

    return str(resolved)


def _extract_video_path(video) -> str:
    if isinstance(video, dict):
        value = video.get("path")
        return value if isinstance(value, str) else ""
    if isinstance(video, str):
        return video
    name = getattr(video, "name", "")
    return name if isinstance(name, str) else ""


def _extract_video_url(video) -> str:
    if isinstance(video, dict):
        value = video.get("url")
        return value if isinstance(value, str) else ""
    return ""


def _allowed_space_hosts(allowed_space_urls: list[str] | None) -> set[str]:
    urls = allowed_space_urls or [
        os.environ.get("HF_SPACE_URL", ""),
        os.environ.get("SPACE_URL", ""),
        DEFAULT_SPACE_URL,
    ]
    hosts = set()
    for url in urls:
        if not url:
            continue
        try:
            hosts.add(urlparse(url).hostname.lower())
        except AttributeError:
            continue
    return hosts


def _local_path_from_url(url: str, allowed_space_urls: list[str] | None) -> Path:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("video url is invalid.")

    if parsed.hostname.lower() not in _allowed_space_hosts(allowed_space_urls):
        raise ValueError("video url must point to the configured Hugging Face Space.")

    marker = "file="
    raw_path = unquote(parsed.path)
    if marker not in raw_path:
        raise ValueError("video url must reference a Gradio upload file.")

    upload_path = raw_path.split(marker, 1)[1]
    return _validate_upload_path(upload_path)


def _validate_upload_path(path: str) -> Path:
    resolved = Path(path).resolve(strict=False)
    try:
        resolved.relative_to(UPLOAD_ROOT)
    except ValueError as exc:
        raise ValueError("video path must reference a Gradio upload.") from exc
    return resolved


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
